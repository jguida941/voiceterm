"""Idris-style typestate gate over governed exception rows for campaign mutation_allowed.

Composes the GovernedTransitionTypeChecker into the read-only campaign report so
that ``mutation_allowed`` requires every closed/closure-bearing lifecycle row to
typecheck via ``IdempotentReemit`` re-emit semantics. A pending_count of zero is
no longer sufficient evidence: closed rows must carry a typed closure proof that
matches the lifecycle and resolves its composed refs against an evidence index.

This is the campaign-layer consumer of the typechecker, mirroring the proven
type-5 pattern in
``dev/scripts/devctl/runtime/raw_git_bypass_lifecycle_closure.py``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ...config import REPO_ROOT
from ...runtime.governed_exception_lifecycle import GovernedExceptionLifecycle
from ...runtime.governed_exception_store import (
    DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL,
    load_governed_exception_lifecycles_with_errors,
)
from ...runtime.governed_transition_typechecker import (
    IDEMPOTENT_REEMIT_EVENT,
    GovernedTransitionError,
    GovernedTransitionInput,
    check_governed_exception_transition,
)

_TYPECHECKED_CLOSED_STATUSES: frozenset[str] = frozenset(
    {"closed", "closed_via_commit_anchor", "closed_via_bypass_expiry"}
)


@dataclass(frozen=True, slots=True)
class TypeCheckerVerdict:
    """Composite verdict over every governed exception row inspected."""

    allows_mutation: bool
    rows_scanned: int
    rows_typechecked: int
    blocking_errors: tuple[GovernedTransitionError, ...]
    summary: str


def campaign_typechecker_verdict(
    exception_store_path: Path | None,
) -> TypeCheckerVerdict:
    """Run GovernedTransitionTypeChecker against closed lifecycle rows.

    For each lifecycle whose status is ``closed`` / ``closed_via_commit_anchor``
    / ``closed_via_bypass_expiry``, simulate an ``IdempotentReemit`` transition
    from the row to itself. The typechecker then enforces that the row carries a
    matching closure proof and that any composed refs resolve. A row that fails
    typecheck blocks campaign mutation_allowed.
    """
    store_path = exception_store_path or (
        REPO_ROOT / DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL
    )
    load_result = load_governed_exception_lifecycles_with_errors(store_path)
    if load_result.errors:
        return TypeCheckerVerdict(
            allows_mutation=False,
            rows_scanned=0,
            rows_typechecked=0,
            blocking_errors=(),
            summary=f"typechecker_skipped_store_error count={len(load_result.errors)}",
        )

    evidence_index = _evidence_index_for(load_result.lifecycles)
    blocking: list[GovernedTransitionError] = []
    typechecked = 0
    for lifecycle in load_result.lifecycles:
        if lifecycle.status not in _TYPECHECKED_CLOSED_STATUSES:
            continue
        typechecked += 1
        result = check_governed_exception_transition(
            GovernedTransitionInput(
                before=lifecycle,
                after=lifecycle,
                event_kind=IDEMPOTENT_REEMIT_EVENT,
                evidence_index=evidence_index,
                closure_proof=lifecycle.closure_proof,
            )
        )
        if not result.ok:
            blocking.extend(result.errors)

    rows_scanned = len(load_result.lifecycles)
    allows_mutation = not blocking
    summary = (
        f"typecheck=ok rows={rows_scanned} closed_checked={typechecked}"
        if allows_mutation
        else (
            f"typecheck=blocked rows={rows_scanned} "
            f"closed_checked={typechecked} errors={len(blocking)}"
        )
    )
    return TypeCheckerVerdict(
        allows_mutation=allows_mutation,
        rows_scanned=rows_scanned,
        rows_typechecked=typechecked,
        blocking_errors=tuple(blocking),
        summary=summary,
    )


def _evidence_index_for(
    lifecycles: tuple[GovernedExceptionLifecycle, ...],
) -> Mapping[str, object]:
    """Build an evidence index from authority/worktree-safety refs on the rows.

    A closed row's composed refs typecheck against whatever evidence the
    lifecycle ledger itself already publishes. This keeps the campaign gate
    purely read-only: it cannot manufacture proof that the store does not
    already carry.
    """
    index: dict[str, object] = {}
    for lifecycle in lifecycles:
        for ref in lifecycle.authority_evidence_refs:
            if ref:
                index[ref] = {"source": "authority_evidence_refs"}
        for ref in lifecycle.worktree_safety_evidence_refs:
            if ref:
                index[ref] = {"source": "worktree_safety_evidence_refs"}
        for ref in lifecycle.projection_refs:
            if ref:
                index[ref] = {"source": "projection_refs"}
        if lifecycle.planned_finding_ingest_ref:
            index[lifecycle.planned_finding_ingest_ref] = {
                "source": "planned_finding_ingest_ref"
            }
    return index


__all__ = [
    "TypeCheckerVerdict",
    "campaign_typechecker_verdict",
]
