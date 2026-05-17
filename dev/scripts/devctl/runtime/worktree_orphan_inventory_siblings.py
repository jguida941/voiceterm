"""Bounded same-parent sibling clone inventory sources."""

from __future__ import annotations

from pathlib import Path

from .checkout_inventory_contracts import CheckoutInventoryRow
from .worktree_orphan_inventory_checkout import (
    CheckoutSourceIdentity,
    checkout_classification,
    inventory_row,
    row_with_source_refs,
    source_for_checkout,
)
from .worktree_orphan_inventory_git import (
    CheckoutProbe,
    looks_like_git_checkout,
    probe_checkout,
    same_parent_candidates,
)
from .worktree_orphan_snapshot import OrphanSource


def scan_bounded_sibling_clones(
    repo_root: Path,
    *,
    primary_probe: CheckoutProbe,
    seen_paths: set[Path],
    compatibility_paths: tuple[str, ...],
) -> tuple[tuple[OrphanSource, ...], tuple[CheckoutInventoryRow, ...]]:
    sources: list[OrphanSource] = []
    rows: list[CheckoutInventoryRow] = []

    for index, candidate in enumerate(same_parent_candidates(repo_root.parent, repo_root.name)):
        resolved = candidate.resolve(strict=False)
        if skip_sibling_candidate(resolved, seen_paths):
            continue

        probe = probe_checkout(resolved)
        if not same_origin_clone(probe, primary_probe):
            continue

        source, row = sibling_inventory_items(
            index=index,
            candidate=candidate,
            repo_name=repo_root.name,
            probe=probe,
            compatibility_paths=compatibility_paths,
        )
        refs = (source.source_ref,) if source is not None else ()
        if source is not None:
            sources.append(source)
        rows.append(row_with_source_refs(row, refs))

    return tuple(sources), tuple(rows)


def skip_sibling_candidate(resolved: Path, seen_paths: set[Path]) -> bool:
    return resolved in seen_paths or not looks_like_git_checkout(resolved)


def same_origin_clone(probe: CheckoutProbe, primary_probe: CheckoutProbe) -> bool:
    return bool(probe.repo_identity and probe.origin_url == primary_probe.origin_url)


def sibling_inventory_items(
    *,
    index: int,
    candidate: Path,
    repo_name: str,
    probe: CheckoutProbe,
    compatibility_paths: tuple[str, ...],
) -> tuple[OrphanSource | None, CheckoutInventoryRow]:
    source = sibling_source(
        index=index,
        candidate=candidate,
        repo_name=repo_name,
        probe=probe,
        compatibility_paths=compatibility_paths,
    )
    row = sibling_row(probe=probe, index=index, compatibility_paths=compatibility_paths)

    return source, row


def sibling_source(
    *,
    index: int,
    candidate: Path,
    repo_name: str,
    probe: CheckoutProbe,
    compatibility_paths: tuple[str, ...],
) -> OrphanSource | None:
    return source_for_checkout(
        identity=CheckoutSourceIdentity(
            source_id=f"source-sibling-checkout-{index}",
            source_kind=sibling_source_kind(candidate, repo_name),
            source_ref=f"sibling-checkout:{probe.checkout_fingerprint}",
        ),
        probe=probe,
        compatibility_paths=compatibility_paths,
        include_clean=True,
        metadata={"inventory_source": "bounded_same_parent_sibling"},
    )


def sibling_source_kind(candidate: Path, repo_name: str) -> str:
    if candidate.name.startswith(f"{repo_name}-wt-"):
        return "worker_root_orphan"
    return "unregistered_sibling_clone"


def sibling_row(
    *,
    probe: CheckoutProbe,
    index: int,
    compatibility_paths: tuple[str, ...],
) -> CheckoutInventoryRow:
    return inventory_row(
        row_id=f"row-sibling-checkout-{index}",
        state="unmanaged_shadow",
        probe=probe,
        source_refs=(),
        classification=checkout_classification(
            probe=probe,
            compatibility_paths=compatibility_paths,
            ownership="bounded_sibling_clone",
        ),
    )


__all__ = ["scan_bounded_sibling_clones"]
