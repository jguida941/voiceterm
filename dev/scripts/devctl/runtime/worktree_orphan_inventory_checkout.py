"""Checkout row/source builders for worktree-orphan inventory scans."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import NamedTuple

from .checkout_inventory_contracts import (
    CheckoutInventoryClassification,
    CheckoutInventoryRow,
)
from .worktree_orphan_inventory_git import CheckoutProbe
from .worktree_orphan_snapshot import OrphanSource, OrphanSourceClassification


class CheckoutDebt(NamedTuple):
    dirty_count: int
    untracked_count: int
    unpublished_commit_shas: tuple[str, ...]
    has_debt: bool
    governed_auto_sync: bool
    load_bearing: bool
    state: str
    status: str
    notes: tuple[str, ...]


class CheckoutSourceIdentity(NamedTuple):
    source_id: str
    source_kind: str
    source_ref: str


def source_for_checkout(
    *,
    identity: CheckoutSourceIdentity,
    probe: CheckoutProbe,
    compatibility_paths: tuple[str, ...],
    metadata: Mapping[str, object],
    include_clean: bool = False,
) -> OrphanSource | None:
    debt = checkout_debt(probe, compatibility_paths)
    if not debt.has_debt and not include_clean:
        return None

    return OrphanSource(
        source_id=identity.source_id,
        source_kind=identity.source_kind,
        source_ref=identity.source_ref,
        path=str(probe.path),
        repo_identity=probe.repo_identity,
        branch=probe.branch,
        head_sha=probe.head_sha,
        dirty_path_count=debt.dirty_count,
        untracked_path_count=debt.untracked_count,
        unpublished_commit_shas=debt.unpublished_commit_shas,
        status=debt.status,
        classification=source_classification(debt),
        evidence_refs=("git status --porcelain=v1", "git rev-list"),
        metadata=dict(metadata),
    )


def checkout_debt(
    probe: CheckoutProbe,
    compatibility_paths: tuple[str, ...],
) -> CheckoutDebt:
    dirty_count = len(probe.dirty_paths)
    untracked_count = len(probe.untracked_paths)
    unpublished = probe.unpublished_commit_shas
    has_debt = dirty_count > 0 or untracked_count > 0 or bool(unpublished)

    governed_auto_sync = only_compatibility_projection_paths(
        (*probe.dirty_paths, *probe.untracked_paths),
        compatibility_paths,
    )
    load_bearing = has_debt and not governed_auto_sync

    return CheckoutDebt(
        dirty_count=dirty_count,
        untracked_count=untracked_count,
        unpublished_commit_shas=unpublished,
        has_debt=has_debt,
        governed_auto_sync=governed_auto_sync,
        load_bearing=load_bearing,
        state=checkout_source_state(
            has_debt=has_debt,
            governed_auto_sync=governed_auto_sync,
        ),
        status="unresolved" if load_bearing else "classified",
        notes=checkout_source_notes(governed_auto_sync),
    )


def source_classification(debt: CheckoutDebt) -> OrphanSourceClassification:
    return OrphanSourceClassification(
        state=debt.state,
        known_governed_auto_sync=debt.governed_auto_sync,
        load_bearing=debt.load_bearing,
        governance_owner="worktree_inventory",
        risk="unpublished_or_dirty_work" if debt.load_bearing else "classified",
        notes=debt.notes,
    )


def checkout_source_state(*, has_debt: bool, governed_auto_sync: bool) -> str:
    if governed_auto_sync:
        return "known_governed_auto_sync"
    if has_debt:
        return "unresolved"
    return "clean_unmanaged_shadow"


def checkout_source_notes(governed_auto_sync: bool) -> tuple[str, ...]:
    if governed_auto_sync:
        return ("only governed compatibility projection paths are dirty",)
    return ()


def inventory_row(
    *,
    row_id: str,
    state: str,
    probe: CheckoutProbe,
    source_refs: tuple[str, ...],
    classification: CheckoutInventoryClassification,
) -> CheckoutInventoryRow:
    return CheckoutInventoryRow(
        row_id=row_id,
        state=state,
        checkout_path=str(probe.path),
        checkout_fingerprint=probe.checkout_fingerprint,
        repo_identity=probe.repo_identity,
        origin_url=probe.origin_url,
        branch=probe.branch,
        head_sha=probe.head_sha,
        git_dir=probe.git_dir,
        source_refs=source_refs,
        classification=classification,
    )


def checkout_classification(
    *,
    probe: CheckoutProbe,
    compatibility_paths: tuple[str, ...],
    ownership: str,
) -> CheckoutInventoryClassification:
    paths = (*probe.dirty_paths, *probe.untracked_paths)
    governed_auto_sync = only_compatibility_projection_paths(paths, compatibility_paths)
    evidence_refs = compatibility_paths if governed_auto_sync else ()

    return CheckoutInventoryClassification(
        known_governed_auto_sync=governed_auto_sync,
        ownership=ownership,
        reason=checkout_classification_reason(governed_auto_sync),
        evidence_refs=evidence_refs,
    )


def checkout_classification_reason(governed_auto_sync: bool) -> str:
    if governed_auto_sync:
        return "only governed compatibility projection paths are dirty"
    return ""


def row_with_source_refs(
    row: CheckoutInventoryRow,
    refs: tuple[str, ...],
) -> CheckoutInventoryRow:
    return CheckoutInventoryRow(
        row_id=row.row_id,
        state=row.state,
        checkout_path=row.checkout_path,
        checkout_fingerprint=row.checkout_fingerprint,
        repo_identity=row.repo_identity,
        origin_url=row.origin_url,
        branch=row.branch,
        head_sha=row.head_sha,
        git_dir=row.git_dir,
        ledger_header_ref=row.ledger_header_ref,
        source_refs=refs,
        classification=row.classification,
    )


def only_compatibility_projection_paths(
    paths: Iterable[str],
    compatibility_paths: tuple[str, ...],
) -> bool:
    path_set = {path for path in paths if path}
    if not path_set:
        return False

    return path_set.issubset(set(compatibility_paths))


__all__ = [
    "CheckoutSourceIdentity",
    "checkout_classification",
    "inventory_row",
    "row_with_source_refs",
    "source_for_checkout",
]
