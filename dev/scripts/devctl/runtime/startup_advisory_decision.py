"""Typed startup advisory-decision routing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .startup_advisory_push_support import (
    checkpoint_progress_decision,
    steady_state_decision,
)
from .startup_advisory_support import (
    StartupAdvisoryDecision,
    blocked_loop_decision,
    concurrent_writer_decision,
    coordination_conflict_decision,
    detached_publication_decision,
    pending_review_decision,
)
from .startup_push_decision import _is_detached_publication_only

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .startup_context import ReviewerGateState
    from .work_intake_models import (
        WorkIntakeCoordinationState,
        WorkIntakeOwnershipState,
    )


def derive_advisory_decision(
    governance: "ProjectGovernance",
    gate: "ReviewerGateState",
    ownership: "WorkIntakeOwnershipState | None" = None,
    coordination: "WorkIntakeCoordinationState | None" = None,
) -> StartupAdvisoryDecision:
    """Derive the advisory action from push enforcement and reviewer state."""
    push = governance.push_enforcement
    decision = checkpoint_progress_decision(push)
    if decision is not None:
        return decision
    if ownership is not None and ownership.concurrent_writer_detected:
        return concurrent_writer_decision(ownership)
    if coordination is not None and coordination.concurrent_writer_conflict_detected:
        return coordination_conflict_decision(coordination)
    if gate.implementation_blocked and not gate.review_gate_allows_push:
        # Manual reviewer approval can publish a clean branch, but cannot
        # authorize more coding.  Skip the blocked-loop route for detached
        # patterns so publication checks can still proceed.
        if not _is_detached_publication_only(gate.implementation_block_reason):
            return blocked_loop_decision(gate)
        result = detached_publication_decision(push, gate)
        if result is not None:
            return result
    if gate.bridge_active and not gate.review_accepted:
        return pending_review_decision(
            bridge_active=gate.bridge_active,
            review_accepted=gate.review_accepted,
            worktree_clean=push.worktree_clean,
        )
    return steady_state_decision(push, gate)


__all__ = ["StartupAdvisoryDecision", "derive_advisory_decision"]
