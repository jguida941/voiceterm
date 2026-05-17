"""Registered git-worktree inventory sources."""

from __future__ import annotations

from pathlib import Path

from .checkout_inventory_contracts import CheckoutInventoryRow
from .worktree_orphan_inventory_checkout import (
    CheckoutSourceIdentity,
    checkout_classification,
    inventory_row,
    source_for_checkout,
)
from .worktree_orphan_inventory_git import CheckoutProbe, probe_checkout
from .worktree_orphan_inventory_worktrees import (
    WorktreeRecord,
    git_worktree_records,
    is_temp_path,
)
from .worktree_orphan_snapshot import OrphanSource, OrphanSourceClassification


def scan_registered_worktrees(
    repo_root: Path,
    *,
    primary_probe: CheckoutProbe,
    compatibility_paths: tuple[str, ...],
) -> tuple[tuple[OrphanSource, ...], tuple[CheckoutInventoryRow, ...], set[Path]]:
    sources: list[OrphanSource] = []
    rows: list[CheckoutInventoryRow] = []
    seen_paths: set[Path] = set()

    for index, record in enumerate(git_worktree_records(repo_root)):
        resolved = record.path.resolve(strict=False)
        seen_paths.add(resolved)
        if resolved == primary_probe.path:
            continue

        if record.prunable or not resolved.exists():
            sources.append(prunable_worktree_source(index, record, resolved))
            continue

        source, row = registered_worktree_items(
            index=index,
            resolved=resolved,
            compatibility_paths=compatibility_paths,
        )
        if source is not None:
            sources.append(source)
        rows.append(row)

    return tuple(sources), tuple(rows), seen_paths


def prunable_worktree_source(
    index: int,
    record: WorktreeRecord,
    resolved: Path,
) -> OrphanSource:
    source_kind = (
        "prunable_ci_worktree_orphan"
        if is_temp_path(resolved)
        else "prunable_or_missing_worktree"
    )
    classification = OrphanSourceClassification(
        state="prunable",
        load_bearing=False,
        governance_owner="git_worktree_list",
        risk="cleanup_candidate",
        notes=(record.reason or "registered worktree is prunable",),
    )

    return OrphanSource(
        source_id=f"source-worktree-prunable-{index}",
        source_kind=source_kind,
        source_ref=f"git-worktree:{resolved}",
        path=str(resolved),
        branch=record.branch,
        head_sha=record.head_sha,
        status="classified",
        classification=classification,
        evidence_refs=("git worktree list --porcelain",),
        metadata={
            "prunable": True,
            "bare": record.bare,
            "detached": record.detached,
        },
    )


def registered_worktree_items(
    *,
    index: int,
    resolved: Path,
    compatibility_paths: tuple[str, ...],
) -> tuple[OrphanSource | None, CheckoutInventoryRow]:
    probe = probe_checkout(resolved)
    source = registered_worktree_source(index, probe, compatibility_paths)
    refs = (source.source_ref,) if source is not None else ()

    return source, registered_worktree_row(
        index=index,
        probe=probe,
        compatibility_paths=compatibility_paths,
        source_refs=refs,
    )


def registered_worktree_source(
    index: int,
    probe: CheckoutProbe,
    compatibility_paths: tuple[str, ...],
) -> OrphanSource | None:
    return source_for_checkout(
        identity=CheckoutSourceIdentity(
            source_id=f"source-registered-worktree-{index}",
            source_kind="registered_git_worktree",
            source_ref=f"git-worktree:{probe.checkout_fingerprint}",
        ),
        probe=probe,
        compatibility_paths=compatibility_paths,
        metadata={"inventory_source": "git_worktree_list"},
    )


def registered_worktree_row(
    *,
    index: int,
    probe: CheckoutProbe,
    compatibility_paths: tuple[str, ...],
    source_refs: tuple[str, ...],
) -> CheckoutInventoryRow:
    return inventory_row(
        row_id=f"row-registered-worktree-{index}",
        state="managed",
        probe=probe,
        source_refs=source_refs,
        classification=checkout_classification(
            probe=probe,
            compatibility_paths=compatibility_paths,
            ownership="registered_git_worktree",
        ),
    )


__all__ = ["scan_registered_worktrees"]
