"""Deterministic doc-authority scanner for governed markdown documents."""

from __future__ import annotations

from pathlib import Path

from ..time_utils import utc_timestamp
from .doc_authority_metadata import parse_metadata_header
from .doc_authority_models import (
    BUDGET_LIMITS,
    PLAN_DOC_CLASSES,
    REQUIRED_SECTIONS,
    ROLE_TO_DOC_CLASS,
    DocRecord,
    DocRegistryReport,
    GovernedDocLayout,
)
from .doc_authority_rules import (
    check_budget,
    classify_doc,
    parse_index_registry,
)
from .doc_authority_support import (
    detect_authority_overlaps,
    detect_consolidation_candidates,
    scan_governed_docs,
)


def build_doc_authority_report(
    repo_root: Path,
    *,
    policy_path: str | Path | None = None,
) -> DocRegistryReport:
    """Orchestrate scan, overlap detection, and report assembly."""
    records = scan_governed_docs(repo_root, policy_path=policy_path)
    by_class: dict[str, int] = {}
    by_lifecycle: dict[str, int] = {}
    total_lines = 0

    for record in records:
        by_class[record.doc_class] = by_class.get(record.doc_class, 0) + 1
        by_lifecycle[record.lifecycle] = by_lifecycle.get(record.lifecycle, 0) + 1
        total_lines += record.line_count

    managed_records = [record for record in records if record.registry_managed]
    registered_count = sum(1 for record in managed_records if record.in_index)
    missing_count = len(managed_records) - registered_count
    non_index_governed = len(records) - len(managed_records)
    coverage = (registered_count / len(managed_records)) if managed_records else 0.0

    budget_violations = _budget_violations(records)
    return DocRegistryReport(
        command="doc-authority",
        timestamp_utc=utc_timestamp(),
        repo_root=str(repo_root),
        total_governed_docs=len(records),
        total_lines=total_lines,
        by_class=by_class,
        by_lifecycle=by_lifecycle,
        registry_coverage=round(coverage, 3),
        registry_counts={
            "managed_active_docs": len(managed_records),
            "registered_active_docs": registered_count,
            "missing_active_docs": missing_count,
            "non_index_governed_docs": non_index_governed,
        },
        budget_violations=budget_violations,
        authority_overlaps=detect_authority_overlaps(records),
        consolidation_candidates=detect_consolidation_candidates(records),
        records=records,
    )


def _budget_violations(records: list[DocRecord]) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    for record in records:
        if record.budget_status not in {"warning", "exceeded"}:
            continue
        violations.append(
            {
                "path": record.path,
                "status": record.budget_status,
                "lines": record.line_count,
                "limit": record.budget_limit,
            }
        )
    return violations


def render_doc_authority_md(report: DocRegistryReport) -> str:
    """Render a human-readable markdown summary of the doc-authority report."""
    managed_active = report.registry_counts.get("managed_active_docs", 0)
    registered_active = report.registry_counts.get("registered_active_docs", 0)
    lines = [
        "# doc-authority",
        "",
        f"Scanned {report.total_governed_docs} governed docs, {report.total_lines} total lines.",
        "",
        "## Summary",
        "",
        (
            f"- Registry coverage: {report.registry_coverage:.1%} "
            f"({registered_active}/{managed_active} active docs registered)"
        ),
        f"- Non-index governed docs: {report.registry_counts.get('non_index_governed_docs', 0)}",
        f"- Budget violations: {len(report.budget_violations)}",
        f"- Authority overlaps: {len(report.authority_overlaps)}",
        f"- Consolidation candidates: {len(report.consolidation_candidates)}",
        "",
        "## By Class",
        "",
    ]
    for doc_class, count in sorted(report.by_class.items()):
        lines.append(f"- {doc_class}: {count}")

    lines.extend(["", "## By Lifecycle", ""])
    for lifecycle, count in sorted(report.by_lifecycle.items()):
        lines.append(f"- {lifecycle}: {count}")

    lines.extend(_render_budget_violations(report.budget_violations))
    lines.extend(_render_authority_overlaps(report.authority_overlaps))
    lines.extend(_render_consolidation_candidates(report.consolidation_candidates))
    lines.extend(_render_registry_table(report.records))
    return "\n".join(lines)


def _render_budget_violations(
    violations: list[dict[str, object]],
) -> list[str]:
    if not violations:
        return []
    lines = ["", "## Budget Violations", ""]
    for violation in violations:
        lines.append(
            f"- `{violation['path']}`: {violation['status']} "
            f"({violation['lines']} lines, limit {violation['limit']})"
        )
    return lines


def _render_authority_overlaps(
    overlaps: list[dict[str, object]],
) -> list[str]:
    if not overlaps:
        return []
    lines = ["", "## Authority Overlaps", ""]
    for overlap in overlaps:
        docs = ", ".join(f"`{path}`" for path in overlap["docs"])
        lines.append(f"- {overlap['mp']}: {docs}")
    return lines


def _render_consolidation_candidates(
    candidates: list[dict[str, object]],
) -> list[str]:
    if not candidates:
        return []
    lines = ["", "## Consolidation Candidates", ""]
    for candidate in candidates:
        signals = "; ".join(candidate["signals"])
        lines.append(f"- `{candidate['path']}`: {signals}")
    return lines


def _render_registry_table(records: list[DocRecord]) -> list[str]:
    lines = ["", "## Doc Registry", ""]
    lines.append("| Path | Class | Lifecycle | Lines | Budget | Managed | Registered |")
    lines.append("|---|---|---|---|---|---|---|")
    for record in records:
        lines.append(
            f"| `{record.path}` | {record.doc_class} | {record.lifecycle} "
            f"| {record.line_count} | {record.budget_status} | "
            f"{'yes' if record.registry_managed else 'no'} | "
            f"{'yes' if record.in_index else 'no'} |"
        )
    return lines


__all__ = [
    "BUDGET_LIMITS",
    "PLAN_DOC_CLASSES",
    "REQUIRED_SECTIONS",
    "ROLE_TO_DOC_CLASS",
    "DocRecord",
    "DocRegistryReport",
    "GovernedDocLayout",
    "build_doc_authority_report",
    "check_budget",
    "classify_doc",
    "detect_authority_overlaps",
    "detect_consolidation_candidates",
    "parse_index_registry",
    "parse_metadata_header",
    "render_doc_authority_md",
]
