"""`devctl review-channel` command implementation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..common import emit_output
from ..config import REPO_ROOT
from ..review_channel import (
    REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
    build_bridge_guard_report,
    build_launch_sessions,
    ensure_launcher_prereqs,
    filter_provider_lanes,
    launch_terminal_sessions,
    list_terminal_profiles,
    resolve_terminal_profile_name,
    summarize_bridge_guard_failures,
)
from ..review_channel_events import (
    artifact_paths_to_dict,
    event_state_exists,
    filter_history_events,
    filter_inbox_packets,
    load_or_refresh_event_bundle,
    post_packet,
    refresh_event_bundle,
    resolve_artifact_paths,
    transition_packet,
)
from ..review_channel_handoff import (
    BRIDGE_LIVENESS_KEYS,
    bridge_liveness_to_dict,
    extract_bridge_snapshot,
    handoff_bundle_to_dict,
    summarize_bridge_liveness,
    validate_launch_bridge_state,
    wait_for_rollover_ack,
    write_handoff_bundle,
)
from ..review_channel_state import projection_paths_to_dict, refresh_status_snapshot
from ..time_utils import utc_timestamp

BRIDGE_ACTIONS = {"launch", "rollover"}
EVENT_ACTIONS = {"post", "watch", "inbox", "ack", "dismiss", "apply", "history"}


def _error_report(args, message: str, *, exit_code: int) -> tuple[dict, int]:
    report = {
        "command": "review-channel",
        "timestamp": utc_timestamp(),
        "action": getattr(args, "action", None),
        "ok": False,
        "exit_ok": False,
        "exit_code": exit_code,
        "execution_mode": getattr(args, "execution_mode", "auto"),
        "terminal": getattr(args, "terminal", "terminal-app"),
        "terminal_profile_requested": getattr(args, "terminal_profile", None),
        "terminal_profile_applied": None,
        "dangerous": bool(getattr(args, "dangerous", False)),
        "rollover_threshold_pct": getattr(args, "rollover_threshold_pct", None),
        "rollover_trigger": getattr(args, "rollover_trigger", None),
        "await_ack_seconds": getattr(args, "await_ack_seconds", None),
        "retirement_note": REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
        "errors": [message],
        "warnings": [],
        "sessions": [],
        "handoff_bundle": None,
        "handoff_ack_required": False,
        "handoff_ack_observed": None,
        "bridge_liveness": None,
        "projection_paths": None,
        "artifact_paths": None,
        "packet": None,
        "packets": [],
        "history": [],
    }
    return report, exit_code


def _render_bridge_md(report: dict) -> str:
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
    _append_bridge_liveness_lines(lines, report.get("bridge_liveness"))
    if report.get("handoff_ack_observed") is not None:
        lines.append(
            "- handoff_ack_observed: "
            f"{json.dumps(report['handoff_ack_observed'], sort_keys=True)}"
        )
    _append_common_report_sections(lines, report)
    if report.get("handoff_bundle"):
        handoff_bundle = report["handoff_bundle"]
        lines.append("")
        lines.append("## Handoff Bundle")
        lines.append(f"- bundle_dir: {handoff_bundle['bundle_dir']}")
        lines.append(f"- markdown_path: {handoff_bundle['markdown_path']}")
        lines.append(f"- json_path: {handoff_bundle['json_path']}")
        lines.append(f"- generated_at: {handoff_bundle['generated_at']}")
        lines.append(f"- rollover_id: {handoff_bundle['rollover_id']}")
        lines.append(f"- trigger: {handoff_bundle['trigger']}")
        lines.append(f"- threshold_pct: {handoff_bundle['threshold_pct']}")
    if report.get("sessions"):
        lines.append("")
        lines.append("## Sessions")
        for session in report["sessions"]:
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
    return "\n".join(lines)


def _render_event_md(report: dict) -> str:
    lines = ["# devctl review-channel", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- action: {report.get('action')}")
    lines.append(f"- execution_mode: {report.get('execution_mode')}")
    queue = report.get("queue") or {}
    lines.append(f"- pending_total: {queue.get('pending_total', 0)}")
    lines.append(f"- stale_packet_count: {queue.get('stale_packet_count', 0)}")
    if report.get("target"):
        lines.append(f"- target: {report.get('target')}")
    if report.get("status_filter"):
        lines.append(f"- status_filter: {report.get('status_filter')}")
    if report.get("limit") is not None:
        lines.append(f"- limit: {report.get('limit')}")
    _append_common_report_sections(lines, report)
    packet = report.get("packet")
    if isinstance(packet, dict):
        lines.append("")
        lines.append("## Packet")
        lines.append(f"- packet_id: {packet.get('packet_id')}")
        lines.append(f"- trace_id: {packet.get('trace_id')}")
        lines.append(f"- route: {packet.get('from_agent')} -> {packet.get('to_agent')}")
        lines.append(f"- status: {packet.get('status')}")
        lines.append(f"- summary: {packet.get('summary')}")
    packets = report.get("packets")
    if isinstance(packets, list) and packets:
        lines.append("")
        lines.append("## Packets")
        for packet_row in packets:
            if not isinstance(packet_row, dict):
                continue
            lines.append(
                f"- {packet_row.get('packet_id')}: {packet_row.get('status')} | "
                f"{packet_row.get('from_agent')} -> {packet_row.get('to_agent')} | "
                f"{packet_row.get('summary')}"
            )
    history = report.get("history")
    if isinstance(history, list) and history:
        lines.append("")
        lines.append("## History")
        for event in history:
            if not isinstance(event, dict):
                continue
            lines.append(
                f"- {event.get('event_id')}: {event.get('event_type')} | "
                f"{event.get('packet_id')} | {event.get('timestamp_utc')}"
            )
    return "\n".join(lines)


def _append_common_report_sections(lines: list[str], report: dict) -> None:
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


def _render_report(report: dict) -> str:
    if report.get("report_mode") == "event-backed":
        return _render_event_md(report)
    return _render_bridge_md(report)


def _append_bridge_liveness_lines(
    lines: list[str],
    bridge_liveness: object,
) -> None:
    if not isinstance(bridge_liveness, dict):
        return
    label_overrides = {"overall_state": "bridge_state"}
    for key in BRIDGE_LIVENESS_KEYS:
        if key == "last_reviewed_scope_present":
            continue
        label = label_overrides.get(key, key)
        value = bridge_liveness.get(key)
        if key == "last_codex_poll_utc" and not value:
            value = "n/a"
        lines.append(f"- {label}: {value}")


def _validate_args(args) -> None:
    rollover_threshold_pct = getattr(args, "rollover_threshold_pct", 50)
    await_ack_seconds = getattr(args, "await_ack_seconds", 0)
    limit = getattr(args, "limit", 20)
    stale_minutes = getattr(args, "stale_minutes", 30)
    expires_in_minutes = getattr(args, "expires_in_minutes", 30)
    if rollover_threshold_pct <= 0 or rollover_threshold_pct > 100:
        raise ValueError("--rollover-threshold-pct must be between 1 and 100.")
    if await_ack_seconds < 0:
        raise ValueError("--await-ack-seconds must be zero or greater.")
    if args.action == "rollover" and await_ack_seconds <= 0:
        raise ValueError(
            "--await-ack-seconds must be greater than zero for rollover so "
            "fresh-session ACK stays fail-closed."
        )
    if args.action == "post":
        if not getattr(args, "from_agent", None):
            raise ValueError("--from-agent is required for review-channel post.")
        if not getattr(args, "to_agent", None):
            raise ValueError("--to-agent is required for review-channel post.")
        if not getattr(args, "kind", None):
            raise ValueError("--kind is required for review-channel post.")
        if not getattr(args, "summary", None):
            raise ValueError("--summary is required for review-channel post.")
        if bool(getattr(args, "body", None)) == bool(getattr(args, "body_file", None)):
            raise ValueError(
                "Review-channel post requires exactly one of --body or --body-file."
            )
    if args.action in {"ack", "dismiss", "apply"}:
        if not getattr(args, "packet_id", None):
            raise ValueError(f"--packet-id is required for review-channel {args.action}.")
        if not getattr(args, "actor", None):
            raise ValueError(f"--actor is required for review-channel {args.action}.")
    if args.action in {"inbox", "watch", "history"} and limit <= 0:
        raise ValueError("--limit must be greater than zero.")
    if stale_minutes <= 0:
        raise ValueError("--stale-minutes must be greater than zero.")
    if expires_in_minutes <= 0:
        raise ValueError("--expires-in-minutes must be greater than zero.")


def _resolve_runtime_paths(args, repo_root: Path) -> dict[str, object]:
    script_dir = None
    if getattr(args, "script_dir", None):
        script_dir = (repo_root / args.script_dir).resolve()
    artifact_paths = resolve_artifact_paths(
        repo_root=repo_root,
        artifact_root_rel=getattr(args, "artifact_root", None),
        state_json_rel=getattr(args, "state_json", None),
        projections_dir_rel=getattr(args, "emit_projections", None),
    )
    return {
        "review_channel_path": (repo_root / args.review_channel_path).resolve(),
        "bridge_path": (repo_root / args.bridge_path).resolve(),
        "rollover_dir": (repo_root / args.rollover_dir).resolve(),
        "status_dir": (repo_root / args.status_dir).resolve(),
        "script_dir": script_dir,
        "artifact_paths": artifact_paths,
    }


def _bridge_launch_state(
    *,
    args,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
) -> tuple[list, dict[str, object], dict[str, object], list, list]:
    _, lanes = ensure_launcher_prereqs(
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        execution_mode=args.execution_mode,
    )
    bridge_snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
    bridge_liveness_state = summarize_bridge_liveness(bridge_snapshot)
    if args.action in BRIDGE_ACTIONS:
        bridge_guard_report = build_bridge_guard_report(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
        )
        if not bridge_guard_report.get("ok", False):
            raise ValueError(
                "Fresh conductor bootstrap requires a green review-channel "
                "bridge guard before launch: "
                + summarize_bridge_guard_failures(bridge_guard_report)
            )
        launch_state_errors = validate_launch_bridge_state(
            bridge_snapshot,
            liveness=bridge_liveness_state,
        )
        if launch_state_errors:
            raise ValueError(
                "Fresh conductor bootstrap requires a live bridge "
                "contract before launch: "
                + "; ".join(launch_state_errors)
            )
    bridge_liveness = bridge_liveness_to_dict(bridge_liveness_state)
    codex_lanes = filter_provider_lanes(lanes, provider="codex")
    claude_lanes = filter_provider_lanes(lanes, provider="claude")
    return lanes, bridge_liveness, bridge_liveness_state, codex_lanes, claude_lanes


def _resolve_terminal_launch_state(
    args,
    *,
    codex_lanes: list,
    claude_lanes: list,
) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    available_profiles = (
        list_terminal_profiles() if args.terminal == "terminal-app" else []
    )
    terminal_profile_applied = resolve_terminal_profile_name(
        args.terminal_profile,
        available_profiles=available_profiles,
    )
    if args.codex_workers > len(codex_lanes):
        warnings.append(
            "Requested Codex worker budget exceeds the current lane table; "
            f"using {len(codex_lanes)} advertised Codex lanes."
        )
    if args.claude_workers > len(claude_lanes):
        warnings.append(
            "Requested Claude worker budget exceeds the current lane table; "
            f"using {len(claude_lanes)} advertised Claude lanes."
        )
    if (
        args.terminal == "terminal-app"
        and args.terminal_profile == "auto-dark"
        and terminal_profile_applied is None
    ):
        warnings.append(
            "No known dark Terminal.app profile was found; live launch will "
            "fall back to the current Terminal default."
        )
    if (
        args.terminal == "terminal-app"
        and args.terminal_profile not in {"auto-dark", "default", "system", "none"}
        and available_profiles
        and terminal_profile_applied not in available_profiles
    ):
        warnings.append(
            f"Requested Terminal profile `{args.terminal_profile}` was not "
            "found; live launch will fall back to the current Terminal default."
        )
        terminal_profile_applied = None
    return terminal_profile_applied, warnings


def _prepare_rollover_bundle(
    *,
    args,
    repo_root: Path,
    bridge_path: Path,
    review_channel_path: Path,
    rollover_dir: Path,
    lanes: list,
) -> tuple[object | None, list[str]]:
    if args.action != "rollover":
        return None, []
    handoff_bundle = write_handoff_bundle(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=rollover_dir,
        trigger=args.rollover_trigger,
        threshold_pct=args.rollover_threshold_pct,
        lane_assignments=[
            {
                "agent_id": lane.agent_id,
                "provider": lane.provider,
                "lane": lane.lane,
                "worktree": lane.worktree,
                "branch": lane.branch,
                "mp_scope": lane.mp_scope,
            }
            for lane in lanes
        ],
    )
    return handoff_bundle, [
        "Planned rollover created a repo-visible handoff bundle. "
        "Fresh sessions should acknowledge it before the old sessions exit."
    ]


def _launch_sessions_if_requested(
    *,
    args,
    sessions: list[dict[str, object]],
    bridge_path: Path,
    handoff_bundle,
    terminal_profile_applied: str | None,
) -> tuple[bool, bool, dict[str, bool] | None]:
    launched = False
    handoff_ack_required = False
    handoff_ack_observed = None
    if (
        args.action in BRIDGE_ACTIONS
        and args.terminal == "terminal-app"
        and not args.dry_run
    ):
        launch_terminal_sessions(sessions, terminal_profile=terminal_profile_applied)
        launched = True
        if (
            args.action == "rollover"
            and handoff_bundle is not None
            and args.await_ack_seconds > 0
        ):
            handoff_ack_required = True
            handoff_ack_observed = wait_for_rollover_ack(
                bridge_path=bridge_path,
                rollover_id=handoff_bundle.rollover_id,
                timeout_seconds=args.await_ack_seconds,
            )
    return launched, handoff_ack_required, handoff_ack_observed


def _build_bridge_success_report(
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
) -> tuple[dict, int]:
    report_ok = str(bridge_liveness.get("overall_state") or "unknown") == "fresh"
    report = {
        "command": "review-channel",
        "timestamp": utc_timestamp(),
        "action": args.action,
        "ok": report_ok,
        "exit_ok": True,
        "exit_code": 0,
        "execution_mode": (
            "markdown-bridge"
            if args.execution_mode in ("auto", "markdown-bridge")
            else args.execution_mode
        ),
        "terminal": args.terminal,
        "terminal_profile_requested": args.terminal_profile,
        "terminal_profile_applied": terminal_profile_applied,
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
    }
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


def _load_post_body(args) -> str:
    body = getattr(args, "body", None)
    body_file = getattr(args, "body_file", None)
    if body:
        return str(body)
    assert body_file is not None
    return Path(body_file).read_text(encoding="utf-8")


def _build_event_report(
    *,
    args,
    bundle,
    packet: dict[str, object] | None = None,
    event: dict[str, object] | None = None,
    packets: list[dict[str, object]] | None = None,
    history: list[dict[str, object]] | None = None,
    warnings: list[str] | None = None,
) -> tuple[dict, int]:
    report_warnings = list(bundle.review_state.get("warnings", []))
    report_warnings.extend(warnings or [])
    report_errors = list(bundle.review_state.get("errors", []))
    report = {
        "command": "review-channel",
        "timestamp": utc_timestamp(),
        "action": args.action,
        "report_mode": "event-backed",
        "ok": not report_errors,
        "exit_ok": not report_errors,
        "exit_code": 0 if not report_errors else 1,
        "execution_mode": "event-backed",
        "terminal": "none",
        "terminal_profile_requested": getattr(args, "terminal_profile", None),
        "terminal_profile_applied": None,
        "dangerous": False,
        "warnings": report_warnings,
        "errors": report_errors,
        "sessions": [],
        "handoff_bundle": None,
        "handoff_ack_required": False,
        "handoff_ack_observed": None,
        "bridge_liveness": None,
        "projection_paths": projection_paths_to_dict(bundle.projection_paths),
        "artifact_paths": artifact_paths_to_dict(bundle.artifact_paths),
        "queue": bundle.review_state.get("queue", {}),
        "packet": packet,
        "packets": packets or [],
        "history": history or [],
        "event": event,
        "target": getattr(args, "target", None),
        "status_filter": getattr(args, "status", None),
        "limit": getattr(args, "limit", None),
    }
    return report, report["exit_code"]


def _run_event_action(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
) -> tuple[dict, int]:
    review_channel_path = paths["review_channel_path"]
    artifact_paths = paths["artifact_paths"]
    assert isinstance(review_channel_path, Path)
    if args.action == "post":
        bundle, event = post_packet(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            from_agent=args.from_agent,
            to_agent=args.to_agent,
            kind=args.kind,
            summary=args.summary,
            body=_load_post_body(args),
            evidence_refs=list(args.evidence_ref or []),
            confidence=float(args.confidence),
            requested_action=args.requested_action,
            policy_hint=args.policy_hint,
            approval_required=bool(args.approval_required),
            packet_id=getattr(args, "packet_id", None),
            trace_id=getattr(args, "trace_id", None),
            session_id=args.session_id,
            plan_id=args.plan_id,
            controller_run_id=getattr(args, "controller_run_id", None),
            expires_in_minutes=args.expires_in_minutes,
        )
        packet = next(
            (
                packet_row
                for packet_row in bundle.review_state.get("packets", [])
                if isinstance(packet_row, dict)
                and packet_row.get("packet_id") == event.get("packet_id")
            ),
            None,
        )
        return _build_event_report(args=args, bundle=bundle, packet=packet, event=event)
    if args.action in {"ack", "dismiss", "apply"}:
        bundle, event = transition_packet(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            action=args.action,
            packet_id=args.packet_id,
            actor=args.actor,
            session_id=args.session_id,
            plan_id=args.plan_id,
            controller_run_id=getattr(args, "controller_run_id", None),
        )
        packet = next(
            (
                packet_row
                for packet_row in bundle.review_state.get("packets", [])
                if isinstance(packet_row, dict)
                and packet_row.get("packet_id") == args.packet_id
            ),
            None,
        )
        return _build_event_report(args=args, bundle=bundle, packet=packet, event=event)
    bundle = load_or_refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    if args.action == "status":
        bundle = refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
        return _build_event_report(args=args, bundle=bundle)
    if args.action == "inbox":
        packets = filter_inbox_packets(
            bundle.review_state,
            target=getattr(args, "target", None),
            status=getattr(args, "status", None),
            limit=args.limit,
        )
        return _build_event_report(args=args, bundle=bundle, packets=packets)
    if args.action == "watch":
        packets = filter_inbox_packets(
            bundle.review_state,
            target=getattr(args, "target", None),
            status=getattr(args, "status", None) or "pending",
            limit=args.limit,
        )
        warnings = []
        if getattr(args, "follow", False):
            warnings.append(
                "Follow mode is accepted but this CLI slice emits one refreshed "
                "snapshot per invocation."
            )
        return _build_event_report(
            args=args,
            bundle=bundle,
            packets=packets,
            warnings=warnings,
        )
    if args.action == "history":
        history = filter_history_events(
            bundle.events,
            trace_id=getattr(args, "trace_id", None),
            limit=args.limit,
        )
        return _build_event_report(args=args, bundle=bundle, history=history)
    raise ValueError(f"Unsupported event-backed review-channel action: {args.action}")


def _run_bridge_action(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
) -> tuple[dict, int]:
    review_channel_path = paths["review_channel_path"]
    bridge_path = paths["bridge_path"]
    rollover_dir = paths["rollover_dir"]
    status_dir = paths["status_dir"]
    script_dir = paths["script_dir"]
    assert isinstance(review_channel_path, Path)
    assert isinstance(bridge_path, Path)
    assert isinstance(rollover_dir, Path)
    assert isinstance(status_dir, Path)

    lanes, bridge_liveness, _liveness_state, codex_lanes, claude_lanes = (
        _bridge_launch_state(
            args=args,
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
        )
    )
    terminal_profile_applied, warnings = _resolve_terminal_launch_state(
        args,
        codex_lanes=codex_lanes,
        claude_lanes=claude_lanes,
    )
    handoff_bundle, handoff_warnings = _prepare_rollover_bundle(
        args=args,
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        rollover_dir=rollover_dir,
        lanes=lanes,
    )
    warnings.extend(handoff_warnings)
    status_snapshot = refresh_status_snapshot(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=status_dir,
        execution_mode=args.execution_mode,
        warnings=warnings,
        errors=[],
    )
    warnings = status_snapshot.warnings
    sessions: list[dict[str, object]] = []
    if args.action in BRIDGE_ACTIONS:
        sessions = build_launch_sessions(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
            codex_lanes=codex_lanes,
            claude_lanes=claude_lanes,
            codex_workers=min(args.codex_workers, len(codex_lanes)),
            claude_workers=min(args.claude_workers, len(claude_lanes)),
            dangerous=bool(args.dangerous),
            rollover_threshold_pct=args.rollover_threshold_pct,
            await_ack_seconds=args.await_ack_seconds,
            bridge_liveness=bridge_liveness,
            handoff_bundle=handoff_bundle_to_dict(handoff_bundle),
            script_dir=script_dir if isinstance(script_dir, Path) else None,
            session_output_root=status_dir,
        )
    launched, handoff_ack_required, handoff_ack_observed = _launch_sessions_if_requested(
        args=args,
        sessions=sessions,
        bridge_path=bridge_path,
        handoff_bundle=handoff_bundle,
        terminal_profile_applied=terminal_profile_applied,
    )
    return _build_bridge_success_report(
        args=args,
        bridge_liveness=bridge_liveness,
        codex_lanes=codex_lanes,
        claude_lanes=claude_lanes,
        terminal_profile_applied=terminal_profile_applied,
        warnings=warnings,
        sessions=sessions,
        handoff_bundle=handoff_bundle,
        projection_paths=status_snapshot.projection_paths,
        launched=launched,
        handoff_ack_required=handoff_ack_required,
        handoff_ack_observed=handoff_ack_observed,
    )


def run(args) -> int:
    """Run one review-channel action."""
    repo_root = REPO_ROOT.resolve()
    try:
        _validate_args(args)
        paths = _resolve_runtime_paths(args, repo_root)
        artifact_paths = paths["artifact_paths"]
        use_event_path = args.action in EVENT_ACTIONS or (
            args.action == "status" and event_state_exists(artifact_paths)
        )
        if use_event_path:
            report, exit_code = _run_event_action(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
        elif args.action in BRIDGE_ACTIONS or args.action == "status":
            report, exit_code = _run_bridge_action(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
        else:
            report, exit_code = _error_report(
                args,
                f"Unsupported review-channel action: {args.action}",
                exit_code=2,
            )
    except ValueError as exc:
        report, exit_code = _error_report(args, str(exc), exit_code=1)
    except subprocess.CalledProcessError as exc:
        report, exit_code = _error_report(
            args,
            f"launcher subprocess failed: {exc}",
            exit_code=1,
        )
    except OSError as exc:
        report, exit_code = _error_report(args, str(exc), exit_code=1)

    output = json.dumps(report, indent=2) if args.format == "json" else _render_report(report)
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
    )
    if pipe_rc != 0:
        return pipe_rc
    return exit_code
