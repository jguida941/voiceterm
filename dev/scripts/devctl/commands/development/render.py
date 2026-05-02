"""Markdown rendering for ``devctl develop`` reports."""

from __future__ import annotations

from .models import DevelopmentLoopReport


def render_markdown(report: DevelopmentLoopReport) -> str:
    """Render a human-scannable controller report."""
    payload = report.to_dict()
    topology = payload["topology"]
    scaling = topology["scaling"]
    lines = ["# devctl develop", ""]
    lines.extend(_header_lines(payload, topology, scaling))
    lines.extend(_next_slice_lines(payload["next_slice"]))
    lines.extend(_workstream_lines(topology["workstreams"]))
    lines.extend(_scaling_lines(scaling))
    lines.extend(_learning_lines(payload["learning"]))
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


def _workstream_lines(workstreams) -> list[str]:
    lines = ["", "## Workstreams", ""]
    for item in workstreams:
        lines.append(
            f"- {item['display_name']} ({item['workstream_id']}): "
            f"{item['mutation_policy']}"
        )
    return lines


def _scaling_lines(scaling) -> list[str]:
    lines = ["", "## Scaling", ""]
    lines.append(f"- pressure_inputs: {', '.join(scaling['pressure_inputs'])}")
    lines.append(f"- route_outputs: {', '.join(scaling['route_outputs'])}")
    for gate in scaling["safety_gates"]:
        lines.append(f"- safety_gate: {gate}")
    return lines


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


__all__ = ["render_markdown"]
