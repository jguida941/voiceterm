"""Top-level report builder for contract-connectivity analysis."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.checks.check_bootstrap import REPO_ROOT
from dev.scripts.checks.rust_guard_common import GuardContext

from .bidirectional import (
    bidirectional_reference_findings,
    bidirectional_reference_key,
)
from .findings import (
    duplicate_contracts,
    duplicate_key,
    layer_counts,
    new_findings,
    orphan_key,
    orphaned_contracts,
    stranded_consumers,
    stranded_key,
)
from .inventory import analyze_source
from .models import ContractConnectivityReport
from .planned_debt import load_planned_debt_coverage


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    absolute: bool = False,
    since_ref: str | None = None,
    head_ref: str = "HEAD",
) -> ContractConnectivityReport:
    """Analyze contract connectivity and return one typed report."""
    guard = GuardContext(repo_root)
    if absolute and since_ref:
        raise ValueError("--absolute cannot be combined with --since-ref/--head-ref")
    if since_ref:
        guard.validate_ref(since_ref)
        guard.validate_ref(head_ref)

    current_ref = None if not since_ref else head_ref
    current = analyze_source(repo_root=repo_root, guard=guard, ref=current_ref)
    baseline = None if absolute else analyze_source(
        repo_root=repo_root,
        guard=guard,
        ref=since_ref or "HEAD",
    )

    current_duplicates = duplicate_contracts(current.contracts)
    current_orphans = orphaned_contracts(
        current,
        duplicate_findings=current_duplicates,
    )
    current_stranded = stranded_consumers(current)
    current_bidirectional = bidirectional_reference_findings(
        current,
        duplicate_findings=current_duplicates,
    )

    baseline_duplicates = () if baseline is None else duplicate_contracts(
        baseline.contracts
    )
    baseline_orphans = () if baseline is None else orphaned_contracts(
        baseline,
        duplicate_findings=baseline_duplicates,
    )
    baseline_stranded = () if baseline is None else stranded_consumers(baseline)
    baseline_bidirectional = (
        ()
        if baseline is None
        else bidirectional_reference_findings(
            baseline,
            duplicate_findings=baseline_duplicates,
        )
    )

    new_orphans = new_findings(current_orphans, baseline_orphans, orphan_key)
    new_duplicates = new_findings(
        current_duplicates,
        baseline_duplicates,
        duplicate_key,
    )
    new_stranded = new_findings(
        current_stranded,
        baseline_stranded,
        stranded_key,
    )
    new_bidirectional = new_findings(
        current_bidirectional,
        baseline_bidirectional,
        bidirectional_reference_key,
    )
    new_debt_count = (
        len(new_orphans)
        + len(new_duplicates)
        + len(new_stranded)
        + len(new_bidirectional)
    )
    planned_debt = (
        load_planned_debt_coverage(repo_root)
        if not absolute and new_debt_count
        else None
    )
    planned_debt_row_ids = () if planned_debt is None else planned_debt.row_ids
    debt_is_planned = bool(planned_debt_row_ids)
    unplanned_orphans = () if debt_is_planned else new_orphans
    unplanned_duplicates = () if debt_is_planned else new_duplicates
    unplanned_stranded = () if debt_is_planned else new_stranded
    unplanned_bidirectional = () if debt_is_planned else new_bidirectional

    if absolute:
        ok = not (
            current_orphans
            or current_duplicates
            or current_stranded
            or current_bidirectional
        )
        mode = "absolute"
    elif since_ref:
        ok = not (
            unplanned_orphans
            or unplanned_duplicates
            or unplanned_stranded
            or unplanned_bidirectional
        )
        mode = "commit-range"
    else:
        ok = not (
            unplanned_orphans
            or unplanned_duplicates
            or unplanned_stranded
            or unplanned_bidirectional
        )
        mode = "working-tree"

    return ContractConnectivityReport(
        mode=mode,
        since_ref="" if absolute or since_ref is None else since_ref,
        head_ref=head_ref,
        ok=ok,
        contracts_scanned=len(current.contracts),
        importer_modules_scanned=len(current.parsed_modules),
        layer_counts=layer_counts(current.contracts),
        orphaned_contracts=tuple(current_orphans),
        duplicate_contracts=tuple(current_duplicates),
        stranded_consumers=tuple(current_stranded),
        bidirectional_reference_findings=tuple(current_bidirectional),
        new_orphaned_contracts=tuple(new_orphans),
        new_duplicate_contracts=tuple(new_duplicates),
        new_stranded_consumers=tuple(new_stranded),
        new_bidirectional_reference_findings=tuple(new_bidirectional),
        unplanned_new_orphaned_contracts=tuple(unplanned_orphans),
        unplanned_new_duplicate_contracts=tuple(unplanned_duplicates),
        unplanned_new_stranded_consumers=tuple(unplanned_stranded),
        unplanned_new_bidirectional_reference_findings=tuple(
            unplanned_bidirectional
        ),
        planned_debt_row_ids=planned_debt_row_ids,
        planned_debt_count=new_debt_count if debt_is_planned else 0,
        baseline_orphaned_count=len(baseline_orphans),
        baseline_duplicate_count=len(baseline_duplicates),
        baseline_stranded_count=len(baseline_stranded),
        baseline_bidirectional_reference_count=len(baseline_bidirectional),
    )
