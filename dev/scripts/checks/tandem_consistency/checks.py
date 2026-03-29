"""Backward-compatible tandem-consistency check facade."""

from __future__ import annotations

from .implementer_checks import (
    check_implementer_ack_freshness,
    check_implementer_completion_stall,
)
from .operator_checks import check_plan_alignment, check_promotion_state
from .reviewer_checks import (
    check_reviewed_hash_honesty,
    check_reviewer_freshness,
    compute_non_audit_worktree_hash,
)
from .system_checks import check_launch_truth

__all__ = [
    "compute_non_audit_worktree_hash",
    "check_implementer_ack_freshness",
    "check_implementer_completion_stall",
    "check_launch_truth",
    "check_plan_alignment",
    "check_promotion_state",
    "check_reviewed_hash_honesty",
    "check_reviewer_freshness",
]
