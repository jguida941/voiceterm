"""Public startup work-intake surface."""

from __future__ import annotations

from pathlib import Path

from .project_governance import ProjectGovernance
from .work_intake_continuity import build_continuity, confidence
from .work_intake_models import (
    IntakeRoutingState,
    PlanTargetRef,
    SessionContinuityState,
    WorkIntakePacket,
)
from .work_intake_routing import build_routing, scope_hints, warm_refs, writeback_sinks
from .work_intake_selection import build_target_ref, load_review_state, select_active_plan_entry


def build_work_intake_packet(
    *,
    repo_root: Path,
    governance: ProjectGovernance,
    advisory_action: str,
    advisory_reason: str,
) -> WorkIntakePacket:
    """Build the first typed startup intake packet from live repo state."""
    review_state = load_review_state(repo_root)
    active_entry = select_active_plan_entry(governance, review_state)
    routing = build_routing(
        repo_root,
        governance=governance,
        advisory_action=advisory_action,
    )
    continuity = build_continuity(active_entry, review_state)
    packet_confidence, fallback_reason = confidence(
        active_entry=active_entry,
        review_state=review_state,
        continuity=continuity,
    )
    return WorkIntakePacket(
        advisory_action=advisory_action,
        advisory_reason=advisory_reason,
        active_target=build_target_ref(repo_root, active_entry),
        continuity=continuity,
        routing=routing,
        scope_hints=scope_hints(active_entry, review_state),
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
    "WorkIntakePacket",
    "build_work_intake_packet",
]
