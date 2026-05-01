"""Plan 4.1 dogfood scenario reducer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .dogfood_models import DogfoodReport
from .dogfood_scenario_models import (
    DEFAULT_TESTER_CADENCE_SECONDS,
    PLAN41_TANDEM_SCENARIO_ID,
    VALID_DOGFOOD_FIX_MODES,
    DogfoodScenarioReport,
)
from .dogfood_scenario_plan41_extract import compact_router, pending_packet_count
from .dogfood_scenario_plan41_support import (
    dogfood_backlog_gate,
    dogfood_status_for_state,
    fanout_gate,
    packet_gate,
    recommended_actions,
    router_gate,
    scenario_lanes,
    scenario_state,
    scenario_summary,
    startup_gate,
    tester_cadence_gate,
)


def build_plan41_tandem_scenario(
    *,
    dashboard: Mapping[str, Any],
    dogfood_report: DogfoodReport,
    fix_mode: str = "observe",
    cadence_seconds: int = DEFAULT_TESTER_CADENCE_SECONDS,
    max_cycles: int = 1,
    loop_requested: bool = False,
) -> DogfoodScenarioReport:
    """Build the Plan 4.1 tandem self-improvement scenario report."""
    normalized_fix_mode = fix_mode if fix_mode in VALID_DOGFOOD_FIX_MODES else "observe"
    safe_cadence = max(DEFAULT_TESTER_CADENCE_SECONDS, int(cadence_seconds or 0))
    safe_max_cycles = max(1, int(max_cycles or 1))
    review_state = _mapping(dashboard.get("_review_state"))
    control_plane = _mapping(dashboard.get("control_plane"))
    coordination = _mapping(control_plane.get("coordination")) or _mapping(dashboard.get("coordination"))
    router = _mapping(review_state.get("agent_dispatch_router")) or _mapping(dashboard.get("agent_dispatch_router"))
    pending_packets = pending_packet_count(dashboard, review_state)
    gates = (
        startup_gate(control_plane),
        router_gate(router),
        packet_gate(pending_packets),
        tester_cadence_gate(dashboard),
        fanout_gate(coordination, normalized_fix_mode),
        dogfood_backlog_gate(dogfood_report),
    )
    blocking_gates = tuple(gate for gate in gates if gate.blocking)
    state = scenario_state(
        gates=blocking_gates,
        router_state=_text(router.get("router_state")),
        fix_mode=normalized_fix_mode,
    )
    return DogfoodScenarioReport(
        scenario_id=PLAN41_TANDEM_SCENARIO_ID,
        generated_from="DashboardSnapshot+DogfoodReport",
        fix_mode=normalized_fix_mode,
        loop_requested=bool(loop_requested),
        max_cycles=safe_max_cycles,
        cadence_seconds=safe_cadence,
        scenario_state=state,
        dogfood_status=dogfood_status_for_state(state),
        summary=scenario_summary(
            scenario_state=state,
            blocking_gates=blocking_gates,
            pending_packets=pending_packets,
            router=router,
        ),
        gates=gates,
        lanes=scenario_lanes(
            dashboard=dashboard,
            cadence_seconds=safe_cadence,
            fix_mode=normalized_fix_mode,
        ),
        router=compact_router(router),
        recommended_actions=recommended_actions(
            gates=blocking_gates,
            pending_packets=pending_packets,
            router=router,
            fix_mode=normalized_fix_mode,
        ),
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value).strip() if value is not None else ""


__all__ = ["build_plan41_tandem_scenario"]
