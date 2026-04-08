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
    SessionContinuityState,
    WorkIntakeCoordinationState,
    WorkIntakeOwnershipState,
    WorkIntakePacket,
)
from .work_intake_ownership import build_work_intake_ownership_state
from .work_intake_routing import build_routing, scope_hints, warm_refs, writeback_sinks
from .work_intake_selection import build_target_ref, load_review_state, select_active_plan_entry

if TYPE_CHECKING:
    from .startup_context import ReviewerGateState


@dataclass(frozen=True, slots=True)
class WorkIntakeStateInputs:
    review_state: object | None = None
    ownership: WorkIntakeOwnershipState | None = None
    coordination: WorkIntakeCoordinationState | None = None
    reviewer_gate: "ReviewerGateState | None" = None


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
    return WorkIntakePacket(
        advisory_action=advisory_action,
        advisory_reason=advisory_reason,
        active_target=build_target_ref(repo_root, active_entry),
        continuity=continuity,
        routing=routing,
        ownership=resolved_ownership,
        coordination=resolved_coordination,
        scope_hints=scope_hints(active_entry, resolved_review_state),
        warm_refs=warm_refs(
            repo_root,
            governance=governance,
            active_entry=active_entry,
            routing=routing,
        ),
        writeback_sinks=writeback_sinks(governance, active_entry),
        confidence=packet_confidence,
        fallback_reason=fallback_reason,
    )


__all__ = [
    "IntakeRoutingState",
    "PlanTargetRef",
    "SessionContinuityState",
    "WorkIntakeCoordinationState",
    "WorkIntakeStateInputs",
    "WorkIntakePacket",
    "build_work_intake_packet",
]
