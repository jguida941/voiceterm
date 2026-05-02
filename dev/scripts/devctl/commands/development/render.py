"""Markdown rendering for ``devctl develop`` reports."""

from __future__ import annotations

from .models import DevelopmentLoopReport
from .render_collaboration import (
    orchestration_lines,
    peer_mind_lines,
    runtime_lines,
)


def render_markdown(report: DevelopmentLoopReport) -> str:
    """Render a human-scannable controller report."""
    payload = report.to_dict()
    topology = payload["topology"]
    scaling = topology["scaling"]
    lines = ["# devctl develop", ""]
    lines.extend(_header_lines(payload, topology, scaling))
    lines.extend(_next_slice_lines(payload["next_slice"]))
    lines.extend(_packet_attention_lines(payload["packet_attention"]))
    lines.extend(_lifecycle_lines(payload.get("lifecycle")))
    lines.extend(runtime_lines(payload.get("runtime")))
    lines.extend(peer_mind_lines(payload.get("peer_minds")))
    lines.extend(orchestration_lines(payload.get("orchestration")))
    lines.extend(_watcher_lease_lines(payload.get("watcher_lease")))
    lines.extend(_continuation_lines(payload.get("continuation")))
    lines.extend(_workstream_lines(topology["workstreams"]))
    lines.extend(_scaling_lines(scaling))
    lines.extend(_learning_lines(payload["learning"]))
    lines.extend(_packet_debt_lines(payload.get("packet_debt_remediation")))
    lines.extend(_discovery_lines(payload["discovery"]))
    _append_list(lines, "Blockers", payload["blockers"])
    _append_list(lines, "Warnings", payload["warnings"])
    _append_list(lines, "Required Checks", payload["required_checks"])
    _append_list(lines, "Next Commands", payload["next_commands"])
    return "\n".join(lines)


def _header_lines(payload: dict[str, object], topology, scaling) -> list[str]:
    return [
        f"- ok: {payload['ok']}",
        f"- action: {payload['action']}",
        f"- status: {payload['status']}",
        f"- controller_state: {payload['controller_state']}",
        f"- summary: {payload['summary']}",
        f"- next_step_command: {payload.get('next_step_command') or '(none)'}",
        f"- topology_id: {topology['topology_id']}",
        f"- default_worker_fanout: {topology['default_worker_fanout']}",
        f"- scaling_modes: {', '.join(scaling['mode_ids'])}",
    ]


def _next_slice_lines(next_slice) -> list[str]:
    return [
        "",
        "## Next Slice",
        "",
        f"- slice_id: {next_slice.get('slice_id') or '(none)'}",
        f"- title: {next_slice.get('title') or '(none)'}",
        f"- target_ref: {next_slice.get('target_ref') or '(none)'}",
        f"- status: {next_slice.get('status') or '(none)'}",
        f"- reason: {next_slice.get('reason') or '(none)'}",
    ]


def _packet_attention_lines(attention) -> list[str]:
    return [
        "",
        "## Packet Attention",
        "",
        f"- attention_required: {attention.get('attention_required')}",
        f"- attention_status: {attention.get('attention_status')}",
        f"- wake_reason: {attention.get('wake_reason') or '(none)'}",
        f"- latest_finding_packet_id: {attention.get('latest_finding_packet_id') or '(none)'}",
        "- pending_actionable_packet_ids: "
        f"{_list_text(attention.get('pending_actionable_packet_ids'))}",
        f"- durable_plan_row_id: {attention.get('durable_plan_row_id') or '(none)'}",
        f"- expired_unresolved_count: {attention.get('expired_unresolved_count')}",
        f"- required_command: {attention.get('required_command') or '(none)'}",
        f"- summary: {attention.get('summary') or '(none)'}",
    ]


def _workstream_lines(workstreams) -> list[str]:
    lines = ["", "## Workstreams", ""]
    for item in workstreams:
        lines.append(
            f"- {item['display_name']} ({item['workstream_id']}): "
            f"{item['mutation_policy']}"
        )
    return lines


def _lifecycle_lines(lifecycle) -> list[str]:
    if not isinstance(lifecycle, dict):
        return []
    lines = ["", "## Lifecycle", ""]
    lines.append(f"- action: {lifecycle.get('action')}")
    lines.append(f"- actor: {lifecycle.get('actor')}")
    lines.append(f"- slice_id: {lifecycle.get('slice_id') or '(none)'}")
    lines.append(f"- packet_id: {lifecycle.get('packet_id') or '(none)'}")
    lines.append(f"- state: {lifecycle.get('state')}")
    lines.append(f"- summary: {lifecycle.get('summary')}")
    steps = lifecycle.get("steps") if isinstance(lifecycle.get("steps"), list) else []
    for step in steps:
        if not isinstance(step, dict):
            continue
        command = f" | `{step.get('command')}`" if step.get("command") else ""
        lines.append(
            f"- {step.get('step_id')}: {step.get('state')} - "
            f"{step.get('purpose')}{command}"
        )
    return lines


def _scaling_lines(scaling) -> list[str]:
    lines = ["", "## Scaling", ""]
    lines.append(f"- pressure_inputs: {', '.join(scaling['pressure_inputs'])}")
    lines.append(f"- route_outputs: {', '.join(scaling['route_outputs'])}")
    for gate in scaling["safety_gates"]:
        lines.append(f"- safety_gate: {gate}")
    return lines


def _watcher_lease_lines(watcher) -> list[str]:
    if not isinstance(watcher, dict):
        return []
    return [
        "",
        "## Watcher Lease",
        "",
        f"- lease_id: {watcher.get('lease_id') or '(none)'}",
        f"- watcher_id: {watcher.get('watcher_id') or '(none)'}",
        f"- watched_actor: {watcher.get('watched_actor') or '(none)'}",
        f"- watched_surfaces: {_list_text(watcher.get('watched_surfaces'))}",
        f"- status: {watcher.get('status') or '(none)'}",
        f"- last_seen_event_id: {watcher.get('last_seen_event_id') or '(none)'}",
        f"- stale_after_seconds: {watcher.get('stale_after_seconds')}",
        f"- stale_seconds: {watcher.get('stale_seconds')}",
        f"- next_report_command: {watcher.get('next_report_command') or '(none)'}",
        f"- summary: {watcher.get('summary') or '(none)'}",
    ]


def _continuation_lines(continuation) -> list[str]:
    if not isinstance(continuation, dict):
        return []
    return [
        "",
        "## Continuation",
        "",
        f"- continuation_required: {continuation.get('continuation_required')}",
        f"- status: {continuation.get('status') or '(none)'}",
        f"- final_response_allowed: {continuation.get('final_response_allowed')}",
        f"- do_not_stop_here: {not bool(continuation.get('final_response_allowed'))}",
        f"- reasons: {_list_text(continuation.get('reasons'))}",
        f"- next_required_command: {continuation.get('next_required_command') or '(none)'}",
        f"- stop_policy: {continuation.get('stop_policy') or '(none)'}",
        f"- summary: {continuation.get('summary') or '(none)'}",
    ]


def _learning_lines(learning) -> list[str]:
    return [
        "",
        "## Learning",
        "",
        f"- open_findings: {learning['open_findings']}",
        f"- promotion_candidates: {learning['promotion_candidates']}",
        f"- queued_promotion_candidates: {learning['queued_promotion_candidates']}",
        f"- smartness_inputs: {', '.join(learning['smartness_inputs'])}",
    ]


def _packet_debt_lines(report) -> list[str]:
    if not isinstance(report, dict):
        return []
    rows = report.get("rows") if isinstance(report.get("rows"), list) else []
    lines = ["", "## Packet Debt Remediation", ""]
    lines.append(f"- debt_count: {report.get('debt_count', 0)}")
    if report.get("total_debt_count") is not None:
        lines.append(f"- total_debt_count: {report.get('total_debt_count', 0)}")
    if report.get("omitted_debt_count") is not None:
        lines.append(f"- omitted_debt_count: {report.get('omitted_debt_count', 0)}")
    lines.append(f"- write_enabled: {report.get('write_enabled', False)}")
    lines.append(f"- action_counts: {_counts_text(report.get('action_counts'))}")
    for row in rows[:10]:
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- {row.get('packet_id')}: {row.get('recommended_action')} "
            f"({row.get('reason')}; target {row.get('target_ref') or '(none)'})"
        )
    return lines


def _discovery_lines(discovery) -> list[str]:
    return [
        "",
        "## Discovery",
        "",
        f"- commands: {discovery['commands']}",
        f"- guards: {discovery['guards']}",
        f"- probes: {discovery['probes']}",
        f"- surfaces: {discovery['surfaces']}",
        f"- coverage_targets: {', '.join(discovery['coverage_targets'])}",
    ]


def _append_list(lines: list[str], title: str, values: list[str]) -> None:
    if not values:
        return
    lines.extend(("", f"## {title}", ""))
    for value in values:
        lines.append(f"- {value}")


def _counts_text(value) -> str:
    if not isinstance(value, dict) or not value:
        return "(none)"
    return ", ".join(f"{key}={count}" for key, count in value.items())


def _list_text(value) -> str:
    if not isinstance(value, list) or not value:
        return "(none)"
    return ", ".join(str(item) for item in value)


__all__ = ["render_markdown"]
