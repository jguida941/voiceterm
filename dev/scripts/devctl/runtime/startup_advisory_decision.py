"""Typed startup advisory-decision routing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .startup_advisory_push_support import (
    checkpoint_progress_decision,
    steady_state_decision,
)
from .decision_explainability import rejected_rule_trace, rule_match_evidence
from .project_governance_contract import (
    delivery_mode_requires_push,
    normalize_delivery_mode,
)
from .startup_advisory_support import (
    StartupAdvisoryDecision,
    _decision,
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
    delivery_mode = normalize_delivery_mode(
        getattr(getattr(governance, "bridge_config", None), "delivery_mode", "")
    )
    if push is not None:
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
        if push is not None:
            result = detached_publication_decision(push, gate)
            if result is not None:
                return result
    if not delivery_mode_requires_push(delivery_mode):
        return _decision(
            "continue_editing",
            f"delivery_mode:{delivery_mode}",
            (
                "Startup is running in a delivery mode that does not require "
                "governed git publication."
            ),
            (
                rule_match_evidence(
                    "startup_advisory.non_push_delivery_mode",
                    "The repo governance bridge config selects a non-push delivery mode.",
                    f"delivery_mode={delivery_mode}",
                ),
            ),
            (
                rejected_rule_trace(
                    "startup_advisory.push_allowed",
                    "Move straight to the governed push path.",
                    "The active delivery mode does not require git publication.",
                ),
            ),
        )
    if gate.bridge_active and not gate.review_accepted:
        return pending_review_decision(
            bridge_active=gate.bridge_active,
            review_accepted=gate.review_accepted,
            worktree_clean=bool(getattr(push, "worktree_clean", True)),
        )
    if push is None:
        return _decision(
            "continue_editing",
            "push_enforcement_unavailable",
            "Startup has no push-enforcement contract, so no push action is selected.",
            (
                rule_match_evidence(
                    "startup_advisory.push_enforcement_unavailable",
                    "ProjectGovernance did not provide push_enforcement.",
                    f"delivery_mode={delivery_mode}",
                ),
            ),
            (),
        )
    return steady_state_decision(push, gate)


__all__ = ["StartupAdvisoryDecision", "derive_advisory_decision"]
