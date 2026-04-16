"""Public startup work-intake surface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .project_governance import ProjectGovernance
from .work_intake_continuity import build_continuity, confidence
from .work_intake_coordination import build_work_intake_coordination_state
from .work_intake_models import (
    IntakeRoutingState,
    PlanTargetRef,
    SessionPacingState,
    SessionContinuityState,
    WorkIntakeCoordinationState,
    WorkIntakeOwnershipState,
    WorkIntakePacket,
)
from .work_intake_plan_routing import PlanRoutingState
from .work_intake_phase_routing import build_plan_routing_state
from .work_intake_pacing import _PacingFocus, _PacingInputs, build_session_pacing_state
from .work_intake_ownership import build_work_intake_ownership_state
from .work_intake_routing import build_routing, scope_hints, warm_refs, writeback_sinks
from .work_intake_selection import (
    build_target_ref,
    load_review_state,
    promote_active_plan_entry,
    select_active_plan_entry,
)

if TYPE_CHECKING:
    from .startup_context import ReviewerGateState


@dataclass(frozen=True, slots=True)
class WorkIntakeStateInputs:
    review_state: object | None = None
    ownership: WorkIntakeOwnershipState | None = None
    coordination: WorkIntakeCoordinationState | None = None
    reviewer_gate: "ReviewerGateState | None" = None
    planning_snapshot: object | None = None
    graph_snapshot: object | None = None


def build_work_intake_packet(
    *,
    repo_root: Path,
    governance: ProjectGovernance,
    advisory_action: str,
    advisory_reason: str,
    state_inputs: WorkIntakeStateInputs | None = None,
) -> WorkIntakePacket:
    """Build the first typed startup intake packet from live repo state."""
    inputs = state_inputs or WorkIntakeStateInputs()
    resolved_review_state = inputs.review_state or load_review_state(
        repo_root,
        governance=governance,
    )
    active_entry = select_active_plan_entry(governance, resolved_review_state)
    routing = build_routing(
        repo_root,
        governance=governance,
        advisory_action=advisory_action,
    )
    continuity = build_continuity(active_entry, resolved_review_state)
    resolved_ownership = inputs.ownership or build_work_intake_ownership_state(
        repo_root=repo_root,
        review_state=resolved_review_state,
    )
    resolved_coordination = inputs.coordination or build_work_intake_coordination_state(
        governance=governance,
        review_state=resolved_review_state,
        ownership=resolved_ownership,
        reviewer_gate=inputs.reviewer_gate,
    )
    packet_confidence, fallback_reason = confidence(
        active_entry=active_entry,
        review_state=resolved_review_state,
        continuity=continuity,
    )
    target_ref = build_target_ref(
        repo_root,
        active_entry,
        reports_root=governance.path_roots.reports,
    )
    resolved_warm_refs = warm_refs(
        repo_root,
        governance=governance,
        active_entry=active_entry,
        routing=routing,
    )
    session_pacing = build_session_pacing_state(
        repo_root=repo_root,
        governance=governance,
        ownership=resolved_ownership,
        coordination=resolved_coordination,
        focus=_PacingFocus(
            active_target=target_ref,
            warm_refs=resolved_warm_refs,
        ),
        inputs=_PacingInputs(
            review_state=resolved_review_state,
            planning_snapshot=inputs.planning_snapshot,
            graph_snapshot=inputs.graph_snapshot,
        ),
    )
    promoted_entry = promote_active_plan_entry(
        governance,
        active_entry,
        focus_plan_path=session_pacing.focus_plan_path,
        live_finding_count=session_pacing.live_finding_count,
    )
    if promoted_entry is not active_entry:
        active_entry = promoted_entry
        continuity = build_continuity(active_entry, resolved_review_state)
        packet_confidence, fallback_reason = confidence(
            active_entry=active_entry,
            review_state=resolved_review_state,
            continuity=continuity,
        )
        target_ref = build_target_ref(
            repo_root,
            active_entry,
            reports_root=governance.path_roots.reports,
        )
        resolved_warm_refs = warm_refs(
            repo_root,
            governance=governance,
            active_entry=active_entry,
            routing=routing,
        )
        session_pacing = build_session_pacing_state(
            repo_root=repo_root,
            governance=governance,
            ownership=resolved_ownership,
            coordination=resolved_coordination,
            focus=_PacingFocus(
                active_target=target_ref,
                warm_refs=resolved_warm_refs,
            ),
            inputs=_PacingInputs(
                review_state=resolved_review_state,
                planning_snapshot=inputs.planning_snapshot,
                graph_snapshot=inputs.graph_snapshot,
            ),
        )
    plan_routing = build_plan_routing_state(
        repo_root=repo_root,
        active_target=target_ref,
        plan_path=session_pacing.focus_plan_path,
    )
    return WorkIntakePacket(
        advisory_action=advisory_action,
        advisory_reason=advisory_reason,
        active_target=target_ref,
        continuity=continuity,
        routing=routing,
        ownership=resolved_ownership,
        coordination=resolved_coordination,
        plan_routing=plan_routing,
        session_pacing=session_pacing,
        scope_hints=scope_hints(active_entry, resolved_review_state),
        warm_refs=resolved_warm_refs,
        writeback_sinks=writeback_sinks(governance, active_entry),
        confidence=packet_confidence,
        fallback_reason=fallback_reason,
    )


__all__ = [
    "IntakeRoutingState",
    "PlanRoutingState",
    "PlanTargetRef",
    "SessionPacingState",
    "SessionContinuityState",
    "WorkIntakeCoordinationState",
    "WorkIntakeStateInputs",
    "WorkIntakePacket",
    "build_work_intake_packet",
]
