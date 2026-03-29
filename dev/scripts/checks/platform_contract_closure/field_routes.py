"""Field-route closure proofs for platform contract enforcement.

Keep this module as the stable compatibility surface while the route families
live in smaller submodules.
"""

from __future__ import annotations

from collections.abc import Callable

FieldRouteCheck = Callable[[], tuple[dict[str, object], dict[str, object] | None]]
from .field_routes_decision_packet import (
    check_decision_packet_mode_autonomy_route,
    check_decision_packet_mode_guard_run_route,
    check_decision_packet_mode_ralph_route,
)
from .field_routes_finding import (
    check_finding_ai_instruction_autonomy_route,
    check_finding_ai_instruction_guard_run_route,
    check_finding_ai_instruction_ralph_route,
)


FIELD_ROUTE_CHECKS: tuple[FieldRouteCheck, ...] = (
    check_finding_ai_instruction_ralph_route,
    check_finding_ai_instruction_autonomy_route,
    check_finding_ai_instruction_guard_run_route,
    check_decision_packet_mode_ralph_route,
    check_decision_packet_mode_autonomy_route,
    check_decision_packet_mode_guard_run_route,
)

FIELD_ROUTE_FAMILY_REGISTRY: dict[tuple[str, str], tuple[str, ...]] = {
    ("Finding", "ai_instruction"): (
        "ralph_prompt",
        "autonomy_loop_packet",
        "guard_run_report",
    ),
    ("DecisionPacket", "decision_mode"): (
        "ralph_prompt",
        "autonomy_loop_packet",
        "guard_run_report",
    ),
}
