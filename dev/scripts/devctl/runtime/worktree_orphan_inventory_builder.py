"""Build report-only worktree-orphan inventory reports."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import NamedTuple

from ..config import REPO_ROOT
from .checkout_inventory_contracts import CheckoutInventory, CheckoutInventoryRow
from .worktree_orphan_inventory_checkout import (
    CheckoutSourceIdentity,
    checkout_classification,
    inventory_row,
    source_for_checkout,
)
from .worktree_orphan_inventory_git import CheckoutProbe, probe_checkout
from .worktree_orphan_inventory_planned import scan_planned_lanes
from .worktree_orphan_inventory_registered import scan_registered_worktrees
from .worktree_orphan_inventory_report import OrphanInventoryReport
from .worktree_orphan_inventory_siblings import scan_bounded_sibling_clones
from .worktree_orphan_inventory_stashes import scan_stashes
from .worktree_orphan_inventory_support import (
    compatibility_projection_paths,
    inventory_stats,
    load_review_state,
    normalize_review_state,
    stable_id,
    utc_now,
)
from .worktree_orphan_snapshot import OrphanSource

DEFAULT_SCAN_SCOPE = "bounded_local"


class InventoryContext(NamedTuple):
    root: Path
    generated_at_utc: str
    scan_scope: str
    compatibility_paths: tuple[str, ...]
    primary_probe: CheckoutProbe
    review_state: Mapping[str, object]


class InventoryCollector:
    """Mutable accumulator for one report-only inventory scan."""

    def __init__(self, context: InventoryContext) -> None:
        self.context = context
        self.rows: list[CheckoutInventoryRow] = []
        self.sources: list[OrphanSource] = []
        self.warnings: list[str] = list(context.primary_probe.errors)
        self.seen_paths: set[Path] = set()
        self.seen_source_refs: set[str] = set()

    def collect(self) -> None:
        self.add_current_checkout()
        self.add_registered_worktrees()
        self.add_planned_lanes()
        self.add_bounded_sibling_clones()
        self.add_stashes()

    def add_current_checkout(self) -> None:
        source = source_for_checkout(
            identity=CheckoutSourceIdentity(
                source_id="source-current-checkout",
                source_kind="current_checkout",
                source_ref=(
                    "current-checkout:"
                    f"{self.context.primary_probe.checkout_fingerprint}"
                ),
            ),
            probe=self.context.primary_probe,
            compatibility_paths=self.context.compatibility_paths,
            metadata={"inventory_source": "current_checkout"},
        )
        source_refs = self.add_source(source)

        self.rows.append(
            inventory_row(
                row_id="row-current-checkout",
                state="managed",
                probe=self.context.primary_probe,
                source_refs=source_refs,
                classification=checkout_classification(
                    probe=self.context.primary_probe,
                    compatibility_paths=self.context.compatibility_paths,
                    ownership="primary_checkout",
                ),
            )
        )
        self.seen_paths.add(self.context.primary_probe.path)

    def add_registered_worktrees(self) -> None:
        sources, rows, paths = scan_registered_worktrees(
            self.context.root,
            primary_probe=self.context.primary_probe,
            compatibility_paths=self.context.compatibility_paths,
        )

        self.add_sources(sources)
        self.rows.extend(rows)
        self.seen_paths.update(paths)

    def add_planned_lanes(self) -> None:
        sources = scan_planned_lanes(
            self.context.root,
            state=self.context.review_state,
        )

        self.add_sources(sources)

    def add_bounded_sibling_clones(self) -> None:
        sources, rows = scan_bounded_sibling_clones(
            self.context.root,
            primary_probe=self.context.primary_probe,
            seen_paths=self.seen_paths,
            compatibility_paths=self.context.compatibility_paths,
        )

        self.add_sources(sources)
        self.rows.extend(rows)

    def add_stashes(self) -> None:
        startup_scan = self.context.scan_scope == "startup_context"
        sources, warnings = scan_stashes(
            self.context.root,
            include_file_paths=not startup_scan,
            max_stashes=8 if startup_scan else 0,
        )

        self.add_sources(sources)
        self.warnings.extend(warnings)

    def add_sources(self, additions: Iterable[OrphanSource]) -> None:
        for source in additions:
            self.add_source(source)

    def add_source(self, source: OrphanSource | None) -> tuple[str, ...]:
        if source is None or source.source_ref in self.seen_source_refs:
            return ()

        self.sources.append(source)
        self.seen_source_refs.add(source.source_ref)
        return (source.source_ref,)


def build_orphan_inventory_report(
    *,
    repo_root: Path = REPO_ROOT,
    review_state: Mapping[str, object] | None = None,
    scan_scope: str = DEFAULT_SCAN_SCOPE,
    generated_at_utc: str | None = None,
) -> OrphanInventoryReport:
    """Build a bounded, read-only orphan inventory report."""
    context = inventory_context(
        repo_root=repo_root,
        review_state=review_state,
        scan_scope=scan_scope,
        generated_at_utc=generated_at_utc,
    )
    collector = InventoryCollector(context)
    collector.collect()

    return inventory_report(context, collector)


def inventory_context(
    *,
    repo_root: Path,
    review_state: Mapping[str, object] | None,
    scan_scope: str,
    generated_at_utc: str | None,
) -> InventoryContext:
    root = repo_root.resolve(strict=False)
    review_payload = load_review_state(root) if review_state is None else review_state

    return InventoryContext(
        root=root,
        generated_at_utc=generated_at_utc or utc_now(),
        scan_scope=scan_scope,
        compatibility_paths=compatibility_projection_paths(root),
        primary_probe=probe_checkout(root),
        review_state=normalize_review_state(review_payload),
    )


def inventory_report(
    context: InventoryContext,
    collector: InventoryCollector,
) -> OrphanInventoryReport:
    return OrphanInventoryReport(
        report_id=stable_id(
            "orphan-inventory",
            context.root,
            context.generated_at_utc,
        ),
        generated_at_utc=context.generated_at_utc,
        scan_scope=context.scan_scope,
        primary_repo_identity=context.primary_probe.repo_identity,
        checkout_inventory=checkout_inventory(context, collector.rows),
        sources=tuple(sorted(collector.sources, key=lambda item: item.source_id)),
        stats=inventory_stats(collector.sources),
        warnings=tuple(collector.warnings),
    )


def checkout_inventory(
    context: InventoryContext,
    rows: list[CheckoutInventoryRow],
) -> CheckoutInventory:
    return CheckoutInventory(
        inventory_id=stable_id(
            "checkout-inventory",
            context.root,
            context.generated_at_utc,
        ),
        generated_at_utc=context.generated_at_utc,
        inventory_scope=context.scan_scope,
        filesystem_scan_ref=f"filesystem_scan:{context.scan_scope}",
        ledger_headers_ref="ledger_headers:not_loaded",
        rows=tuple(rows),
    )


__all__ = ["DEFAULT_SCAN_SCOPE", "build_orphan_inventory_report"]
