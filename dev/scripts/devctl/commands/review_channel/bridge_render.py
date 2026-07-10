"""Bridge-report rendering helpers for `devctl review-channel`."""

from __future__ import annotations

import json
from ...review_channel.attach_auth_render import append_attach_auth_policy_markdown
from ...review_channel.doctor_markdown import append_doctor_markdown
from ...review_channel.projection_markdown import append_push_markdown
from .bridge_wait_render import append_wait_state_markdown
from .bridge_success_report import BridgeSuccessReportRequest, build_bridge_success_report
from .bridge_render_sections import (
    _append_handoff_bundle,
    _append_promotion,
    _append_attention,
    _append_service_identity,
    _append_bridge_heartbeat_refresh,
    _append_reviewer_state_write,
    _append_bridge_render,
    _append_sessions,
)
from .status_readiness import append_runtime_readiness_markdown
from .cli_health_probe import append_cli_health_probe_markdown


def render_bridge_md(
    report: dict,
    *,
    bridge_liveness_keys: tuple[str, ...],
) -> str:
    """Render a markdown summary for bridge-backed review-channel actions."""
    lines = ["# devctl review-channel", ""]
    lines.append(f"- ok: {report['ok']}")
    append_top_level_error_lines(lines, report)
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
    lines.append(f"- typed_state_written: {report.get('typed_state_written', False)}")
    lines.append(f"- process_alive: {report.get('process_alive', False)}")
    lines.append(f"- bridge_attached: {report.get('bridge_attached', False)}")
    lines.append(f"- handoff_ack_required: {report.get('handoff_ack_required', False)}")
    lines.append(
        "- codex_requested_worker_budget: "
        f"{report.get('codex_requested_worker_budget', 0)}"
    )
    lines.append(
        "- claude_requested_worker_budget: "
        f"{report.get('claude_requested_worker_budget', 0)}"
    )
    runtime_counts = report.get("runtime_counts")
    if isinstance(runtime_counts, dict):
        lines.append(
            f"- active_conductor_count: {runtime_counts.get('active_conductor_count', 0)}"
        )
        lines.append(
            f"- live_participant_count: {runtime_counts.get('live_participant_count', 0)}"
        )
        lines.append(
            f"- running_daemon_count: {runtime_counts.get('running_daemon_count', 0)}"
        )
        lines.append(
            f"- delegated_work_total: {runtime_counts.get('delegated_work_total', 0)}"
        )
        lines.append(
            "- requested_worker_budget_total: "
            f"{runtime_counts.get('requested_worker_budget_total', 0)}"
        )
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
    append_runtime_readiness_markdown(lines, report)
    append_cli_health_probe_markdown(lines, report.get("cli_health_probe"))
    append_common_report_sections(lines, report)
    _append_handoff_bundle(lines, report.get("handoff_bundle"))
    _append_promotion(lines, report.get("promotion"))
    _append_attention(lines, report.get("attention"))
    append_doctor_markdown(lines, report.get("doctor"))
    bridge_liveness = report.get("bridge_liveness")
    push_enforcement = (
        bridge_liveness.get("push_enforcement")
        if isinstance(bridge_liveness, dict)
        else None
    )
    append_push_markdown(lines, push_enforcement, report.get("push_decision"))
    append_wait_state_markdown(lines, report.get("wait_state"))
    _append_service_identity(lines, report.get("service_identity"))
    append_attach_auth_policy_markdown(lines, report.get("attach_auth_policy"))
    _append_bridge_heartbeat_refresh(lines, report.get("bridge_heartbeat_refresh"))
    _append_reviewer_state_write(lines, report.get("reviewer_state_write"))
    _append_bridge_render(lines, report.get("bridge_render"))
    _append_sessions(lines, report.get("sessions"))
    return "\n".join(lines)


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
        commit_pipeline_path = projection_paths.get("commit_pipeline_path")
        if commit_pipeline_path:
            lines.append(f"- commit_pipeline_path: {commit_pipeline_path}")


def append_top_level_error_lines(lines: list[str], report: dict) -> None:
    for error in report.get("errors") or []:
        lines.append(f"- error: {error}")
