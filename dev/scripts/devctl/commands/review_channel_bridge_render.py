"""Bridge-report rendering helpers for `devctl review-channel`."""

from __future__ import annotations

import json

from ..approval_mode import normalize_approval_mode
from ..review_channel.core import REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE
from ..review_channel.handoff import handoff_bundle_to_dict
from ..review_channel.heartbeat import bridge_heartbeat_refresh_to_dict
from ..review_channel.promotion import promotion_candidate_to_dict
from ..review_channel.state import projection_paths_to_dict
from ..time_utils import utc_timestamp


def render_bridge_md(
    report: dict,
    *,
    bridge_liveness_keys: tuple[str, ...],
) -> str:
    """Render a markdown summary for bridge-backed review-channel actions."""
    lines = ["# devctl review-channel", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- action: {report.get('action')}")
    lines.append(f"- execution_mode: {report.get('execution_mode')}")
    lines.append(f"- terminal: {report.get('terminal')}")
    lines.append(
        f"- terminal_profile_requested: {report.get('terminal_profile_requested')}"
    )
    lines.append(
        f"- terminal_profile_applied: {report.get('terminal_profile_applied') or 'none'}"
    )
    lines.append(f"- approval_mode: {report.get('approval_mode')}")
    lines.append(f"- dangerous: {report.get('dangerous', False)}")
    lines.append(f"- rollover_threshold_pct: {report.get('rollover_threshold_pct')}")
    lines.append(f"- rollover_trigger: {report.get('rollover_trigger') or 'n/a'}")
    lines.append(f"- await_ack_seconds: {report.get('await_ack_seconds')}")
    lines.append(f"- bridge_active: {report.get('bridge_active', False)}")
    lines.append(f"- launched: {report.get('launched', False)}")
    lines.append(f"- handoff_ack_required: {report.get('handoff_ack_required', False)}")
    lines.append(f"- codex_lane_count: {report.get('codex_lane_count', 0)}")
    lines.append(f"- claude_lane_count: {report.get('claude_lane_count', 0)}")
    lines.append(f"- codex_workers_requested: {report.get('codex_workers_requested', 0)}")
    lines.append(f"- claude_workers_requested: {report.get('claude_workers_requested', 0)}")
    lines.append(f"- retirement_note: {report.get('retirement_note')}")
    _append_bridge_liveness_lines(
        lines,
        report.get("bridge_liveness"),
        bridge_liveness_keys=bridge_liveness_keys,
    )
    if report.get("handoff_ack_observed") is not None:
        lines.append(
            "- handoff_ack_observed: "
            f"{json.dumps(report['handoff_ack_observed'], sort_keys=True)}"
        )
    append_common_report_sections(lines, report)
    _append_handoff_bundle(lines, report.get("handoff_bundle"))
    _append_promotion(lines, report.get("promotion"))
    _append_bridge_heartbeat_refresh(lines, report.get("bridge_heartbeat_refresh"))
    _append_sessions(lines, report.get("sessions"))
    return "\n".join(lines)


def build_bridge_success_report(
    *,
    args,
    bridge_liveness: dict[str, object],
    codex_lanes: list,
    claude_lanes: list,
    terminal_profile_applied: str | None,
    warnings: list[str],
    sessions: list[dict[str, object]],
    handoff_bundle,
    projection_paths,
    launched: bool,
    handoff_ack_required: bool,
    handoff_ack_observed: dict[str, bool] | None,
    promotion=None,
    bridge_heartbeat_refresh=None,
    execution_mode_override: str | None = None,
) -> tuple[dict, int]:
    """Assemble the bridge-action success report dict."""
    report_ok = str(bridge_liveness.get("overall_state") or "unknown") == "fresh"
    report = {
        "command": "review-channel",
        "timestamp": utc_timestamp(),
        "action": args.action,
        "ok": report_ok,
        "exit_ok": True,
        "exit_code": 0,
        "execution_mode": execution_mode_override
        or (
            "markdown-bridge"
            if args.execution_mode in ("auto", "markdown-bridge")
            else args.execution_mode
        ),
        "terminal": args.terminal,
        "terminal_profile_requested": args.terminal_profile,
        "terminal_profile_applied": terminal_profile_applied,
        "approval_mode": normalize_approval_mode(
            getattr(args, "approval_mode", None),
            dangerous=bool(args.dangerous),
        ),
        "dangerous": bool(args.dangerous),
        "rollover_threshold_pct": args.rollover_threshold_pct,
        "rollover_trigger": (
            args.rollover_trigger if args.action == "rollover" else None
        ),
        "await_ack_seconds": args.await_ack_seconds,
        "bridge_active": True,
        "launched": launched,
        "handoff_ack_required": handoff_ack_required,
        "handoff_ack_observed": handoff_ack_observed,
        "codex_lane_count": len(codex_lanes),
        "claude_lane_count": len(claude_lanes),
        "codex_workers_requested": args.codex_workers,
        "claude_workers_requested": args.claude_workers,
        "retirement_note": REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
        "warnings": warnings,
        "errors": [],
        "sessions": sessions,
        "handoff_bundle": handoff_bundle_to_dict(handoff_bundle),
        "bridge_liveness": bridge_liveness,
        "projection_paths": projection_paths_to_dict(projection_paths),
        "promotion": promotion_candidate_to_dict(promotion),
        "bridge_heartbeat_refresh": bridge_heartbeat_refresh_to_dict(
            bridge_heartbeat_refresh
        ),
    }
    if bridge_heartbeat_refresh is not None:
        report["warnings"].append(
            "Auto-refreshed the markdown-bridge reviewer heartbeat before "
            f"{args.action} so the live launch contract could proceed."
        )
    if handoff_ack_required and handoff_ack_observed is not None:
        missing = [
            provider
            for provider, observed in handoff_ack_observed.items()
            if not observed
        ]
        if missing:
            report["ok"] = False
            report["exit_ok"] = False
            report["exit_code"] = 1
            report["errors"].append(
                "Timed out waiting for fresh-conductor rollover ACK lines "
                f"from: {', '.join(missing)}"
            )
            return report, 1
    return report, 0


def _append_bridge_liveness_lines(
    lines: list[str],
    bridge_liveness: object,
    *,
    bridge_liveness_keys: tuple[str, ...],
) -> None:
    if not isinstance(bridge_liveness, dict):
        return
    label_overrides = {"overall_state": "bridge_state"}
    for key in bridge_liveness_keys:
        if key == "last_reviewed_scope_present":
            continue
        label = label_overrides.get(key, key)
        value = bridge_liveness.get(key)
        if key == "last_codex_poll_utc" and not value:
            value = "n/a"
        lines.append(f"- {label}: {value}")


def append_common_report_sections(lines: list[str], report: dict) -> None:
    if report.get("warnings"):
        lines.append("")
        lines.append("## Warnings")
        for warning in report["warnings"]:
            lines.append(f"- {warning}")
    if report.get("errors"):
        lines.append("")
        lines.append("## Errors")
        for error in report["errors"]:
            lines.append(f"- {error}")
    if report.get("artifact_paths"):
        artifact_paths = report["artifact_paths"]
        lines.append("")
        lines.append("## Artifacts")
        lines.append(f"- artifact_root: {artifact_paths['artifact_root']}")
        lines.append(f"- event_log_path: {artifact_paths['event_log_path']}")
        lines.append(f"- state_path: {artifact_paths['state_path']}")
        lines.append(f"- projections_root: {artifact_paths['projections_root']}")
    if report.get("projection_paths"):
        projection_paths = report["projection_paths"]
        lines.append("")
        lines.append("## Projections")
        lines.append(f"- root_dir: {projection_paths['root_dir']}")
        lines.append(f"- review_state_path: {projection_paths['review_state_path']}")
        lines.append(f"- compact_path: {projection_paths['compact_path']}")
        lines.append(f"- full_path: {projection_paths['full_path']}")
        lines.append(f"- actions_path: {projection_paths['actions_path']}")
        lines.append(f"- trace_path: {projection_paths['trace_path']}")
        lines.append(
            f"- latest_markdown_path: {projection_paths['latest_markdown_path']}"
        )
        lines.append(
            f"- agent_registry_path: {projection_paths['agent_registry_path']}"
        )


def _append_handoff_bundle(lines: list[str], handoff_bundle: object) -> None:
    if not isinstance(handoff_bundle, dict):
        return
    lines.append("")
    lines.append("## Handoff Bundle")
    lines.append(f"- bundle_dir: {handoff_bundle['bundle_dir']}")
    lines.append(f"- markdown_path: {handoff_bundle['markdown_path']}")
    lines.append(f"- json_path: {handoff_bundle['json_path']}")
    lines.append(f"- generated_at: {handoff_bundle['generated_at']}")
    lines.append(f"- rollover_id: {handoff_bundle['rollover_id']}")
    lines.append(f"- trigger: {handoff_bundle['trigger']}")
    lines.append(f"- threshold_pct: {handoff_bundle['threshold_pct']}")


def _append_promotion(lines: list[str], promotion: object) -> None:
    if not isinstance(promotion, dict):
        return
    lines.append("")
    lines.append("## Promotion")
    lines.append(f"- instruction: {promotion.get('instruction')}")
    lines.append(f"- source_path: {promotion.get('source_path')}")
    if promotion.get("phase_heading"):
        lines.append(f"- phase_heading: {promotion.get('phase_heading')}")
    lines.append(f"- checklist_item: {promotion.get('checklist_item')}")


def _append_bridge_heartbeat_refresh(lines: list[str], refresh: object) -> None:
    if not isinstance(refresh, dict):
        return
    lines.append("")
    lines.append("## Bridge Heartbeat Refresh")
    lines.append(f"- bridge_path: {refresh.get('bridge_path')}")
    lines.append(f"- reason: {refresh.get('reason')}")
    lines.append(f"- last_codex_poll_utc: {refresh.get('last_codex_poll_utc')}")
    lines.append(f"- last_codex_poll_local: {refresh.get('last_codex_poll_local')}")
    lines.append(f"- last_worktree_hash: {refresh.get('last_worktree_hash')}")


def _append_sessions(lines: list[str], sessions: object) -> None:
    if not isinstance(sessions, list) or not sessions:
        return
    lines.append("")
    lines.append("## Sessions")
    for session in sessions:
        lines.append(f"### {session['session_name']}")
        lines.append(f"- provider: {session['provider']}")
        lines.append(f"- worker_budget: {session['worker_budget']}")
        lines.append(f"- lane_count: {session['lane_count']}")
        lines.append(f"- script_path: {session['script_path']}")
        lines.append(f"- launch_command: {session['launch_command']}")
        for lane in session["lanes"]:
            lines.append(
                f"- lane: {lane['agent_id']} | {lane['lane']} | "
                f"{lane['worktree']} | {lane['branch']}"
            )
