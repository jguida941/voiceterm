"""Gate plan-row commit-anchor closure on a terminal RoleReviewReceipt.

R316 Slice 4 (T2 wiring per R297-#175 FOURTH LEG):

A `PlanRowClosureReceipt` may not legitimately advance a `PlanRow` to
`closed_via_commit_anchor`/`applied` status without typed evidence that a
review role actually reviewed the work. This module surfaces that gate as a
pure-Python check so reducers and tests can compose it without reading the
in-memory role-review lifecycle ledger directly.

Per R313 A7 finding: `RoleReviewReceipt` was defined in
`runtime/role_review_lifecycle.py` but had zero command-layer consumers and was
therefore fire-and-forget. This gate is the first such consumer.

The gate accepts a sequence of `RoleReviewAssignmentLifecycle` rows (supplied
by callers from whichever store they own) and a `plan_row_id`. It returns the
typed evidence refs that should compose into the
`PlanRowClosureReceipt.composes_with` chain, or raises
`RoleReviewReceiptRequired` if no terminal review evidence is present.

Terminal-state semantics match `_TERMINAL_LIFECYCLE_STATES` (Slice 1):
- `status == "reviewed"` AND `receipt.verdict in {approved, changes_requested}`
  count as terminal closure proof.
- `status == "timed_out"` does NOT satisfy the gate (fallback authority is
  not a positive review verdict).
- Verdicts `blocked` / `informational` and status `assigned` are non-terminal
  and do not satisfy the gate.

A lifecycle row associates with a plan row when ANY of its `evidence_refs`
mentions the plan_row_id (exact or `plan_row:<id>` prefix), or the
assignment's `packet_id` already encodes the plan_row_id token. This mirrors
how plan rows compose with packet ids elsewhere in the typed substrate.
"""

from __future__ import annotations

from collections.abc import Iterable

from .ref_collections import unique_refs as _unique_refs
from .role_review_lifecycle import RoleReviewAssignmentLifecycle
from .value_coercion import coerce_string

_TERMINAL_REVIEW_VERDICTS = frozenset({"approved", "changes_requested"})


class RoleReviewReceiptRequired(Exception):
    """Raised when a plan-row closure lacks terminal RoleReviewReceipt evidence."""

    def __init__(self, plan_row_id: str, *, reason: str) -> None:
        super().__init__(
            f"plan_row_id={plan_row_id!r} requires terminal RoleReviewReceipt: {reason}"
        )
        self.plan_row_id = plan_row_id
        self.reason = reason


def lifecycle_covers_plan_row(
    lifecycle: RoleReviewAssignmentLifecycle,
    plan_row_id: str,
) -> bool:
    """Return True if `lifecycle` mentions `plan_row_id` in its evidence chain."""
    token = coerce_string(plan_row_id)
    if not token:
        return False
    candidates = (
        coerce_string(lifecycle.packet_id),
        *tuple(coerce_string(ref) for ref in lifecycle.evidence_refs),
    )
    plan_ref = f"plan_row:{token}"
    for candidate in candidates:
        if not candidate:
            continue
        if candidate == token or candidate == plan_ref:
            return True
        if token in candidate:
            return True
    return False


def is_terminal_review_lifecycle(
    lifecycle: RoleReviewAssignmentLifecycle,
) -> bool:
    """Return True for lifecycles with terminal-approved RoleReviewReceipt."""
    if lifecycle.status != "reviewed":
        return False
    receipt = lifecycle.receipt
    if receipt is None:
        return False
    return receipt.verdict in _TERMINAL_REVIEW_VERDICTS


def require_terminal_role_review_for_plan_row(
    plan_row_id: str,
    *,
    role_review_lifecycles: Iterable[RoleReviewAssignmentLifecycle],
) -> tuple[str, ...]:
    """Return composes_with refs for a plan-row commit-anchor closure.

    Raises RoleReviewReceiptRequired if no terminal RoleReviewReceipt covers
    `plan_row_id`. Returned refs are deduplicated typed pointers suitable for
    inclusion in `PlanRowClosureReceipt.composes_with` evidence.
    """
    row_id = coerce_string(plan_row_id)
    if not row_id:
        raise RoleReviewReceiptRequired("", reason="plan_row_id is required")

    lifecycles = tuple(role_review_lifecycles)
    if not lifecycles:
        raise RoleReviewReceiptRequired(
            row_id, reason="no role-review lifecycles supplied"
        )

    covering = tuple(
        lifecycle
        for lifecycle in lifecycles
        if lifecycle_covers_plan_row(lifecycle, row_id)
    )
    if not covering:
        raise RoleReviewReceiptRequired(
            row_id, reason="no role-review lifecycle covers plan_row"
        )

    terminal = tuple(
        lifecycle for lifecycle in covering if is_terminal_review_lifecycle(lifecycle)
    )
    if not terminal:
        raise RoleReviewReceiptRequired(
            row_id,
            reason=(
                "covering role-review lifecycles are non-terminal "
                "(no approved/changes_requested RoleReviewReceipt)"
            ),
        )

    refs: list[str] = []
    for lifecycle in terminal:
        refs.append(f"role_review_assignment:{lifecycle.assignment_id}")
        receipt = lifecycle.receipt
        if receipt is not None:
            refs.append(
                "role_review_receipt:"
                + ":".join(
                    (
                        receipt.packet_id,
                        receipt.role,
                        receipt.reviewer_actor,
                    )
                )
            )
            refs.append(f"role_review_verdict:{receipt.verdict}")
    return _unique_refs(refs)


__all__ = [
    "RoleReviewReceiptRequired",
    "is_terminal_review_lifecycle",
    "lifecycle_covers_plan_row",
    "require_terminal_role_review_for_plan_row",
]
