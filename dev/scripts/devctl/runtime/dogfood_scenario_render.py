"""Markdown renderers for dogfood scenario contracts."""

from __future__ import annotations

from .dogfood_scenario_models import DogfoodScenarioReport


def render_dogfood_scenario_markdown(report: DogfoodScenarioReport) -> str:
    """Render a scenario report as compact markdown."""
    lines = [
        f"## Dogfood Scenario: {report.scenario_id}",
        "",
        f"- state: {report.scenario_state}",
        f"- dogfood_status: {report.dogfood_status}",
        f"- fix_mode: {report.fix_mode}",
        f"- cadence_seconds: {report.cadence_seconds}",
        f"- loop_requested: {str(report.loop_requested).lower()}",
        f"- max_cycles: {report.max_cycles}",
        f"- summary: {report.summary}",
        "",
        "### Gates",
        "",
        "| Gate | Status | Blocking | Summary |",
        "|---|---|---:|---|",
    ]
    for gate in report.gates:
        lines.append(
            f"| `{gate.gate_id}` | `{gate.status}` | "
            f"{str(gate.blocking).lower()} | {gate.summary} |"
        )
    lines.extend(["", "### Lanes", ""])
    for lane in report.lanes:
        actions = ", ".join(lane.required_actions) or "none"
        lines.append(
            f"- `{lane.lane_id}` actor={lane.actor_id} role={lane.role} "
            f"mode={lane.mode} cadence={lane.cadence_seconds}s actions={actions}"
        )
    router = report.router
    lines.extend(["", "### Router", ""])
    lines.append(
        "- state="
        f"`{router.get('router_state', '')}` selected=`{router.get('selected_route_id', '')}` "
        f"routes={router.get('route_count', 0)} debt={router.get('governance_debt_count', 0)}"
    )
    lines.extend(["", "### Recommended Actions", ""])
    actions = report.recommended_actions or ("none",)
    lines.extend(f"- {action}" for action in actions)
    return "\n".join(lines)


__all__ = ["render_dogfood_scenario_markdown"]
