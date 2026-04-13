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
from .field_routes_planning import (
    check_finding_backlog_latest_rows_findings_priority_route,
    check_finding_backlog_open_findings_planning_ir_route,
    check_finding_backlog_open_rows_startup_quality_route,
    check_plan_phase_phase_id_startup_route,
    check_plan_task_task_id_startup_route,
)
from .field_routes_surface_state import (
    check_auto_mode_phase_session_resume_route,
    check_last_reviewed_sha_compact_route,
    check_push_eligible_dashboard_route,
    check_push_eligible_session_resume_route,
    check_top_blocker_dashboard_route,
    check_top_blocker_phone_route,
    check_top_blocker_session_resume_route,
)


FIELD_ROUTE_CHECKS: tuple[FieldRouteCheck, ...] = (
    check_finding_ai_instruction_ralph_route,
    check_finding_ai_instruction_autonomy_route,
    check_finding_ai_instruction_guard_run_route,
    check_decision_packet_mode_ralph_route,
    check_decision_packet_mode_autonomy_route,
    check_decision_packet_mode_guard_run_route,
    check_push_eligible_dashboard_route,
    check_push_eligible_session_resume_route,
    check_top_blocker_dashboard_route,
    check_top_blocker_session_resume_route,
    check_top_blocker_phone_route,
    check_plan_phase_phase_id_startup_route,
    check_plan_task_task_id_startup_route,
    check_finding_backlog_latest_rows_findings_priority_route,
    check_finding_backlog_open_findings_planning_ir_route,
    check_finding_backlog_open_rows_startup_quality_route,
    check_auto_mode_phase_session_resume_route,
    check_last_reviewed_sha_compact_route,
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
    ("ControlPlaneReadModel", "push_eligible"): (
        "dashboard",
        "session_resume",
    ),
    ("ControlPlaneReadModel", "top_blocker"): (
        "dashboard",
        "session_resume",
        "phone",
    ),
    ("AutoModeState", "phase"): (
        "session_resume",
    ),
    ("PlanPhase", "phase_id"): (
        "startup_plan_routing",
    ),
    ("PlanTask", "task_id"): (
        "startup_plan_routing",
    ),
    ("FindingBacklog", "latest_rows"): (
        "findings_priority",
    ),
    ("FindingBacklog", "open_findings"): (
        "planning_ir",
    ),
    ("FindingBacklog", "open_rows"): (
        "startup_quality_signals",
    ),
    ("SessionCachePacket", "last_reviewed_sha"): (
        "compact_projection",
    ),
}
