"""Report rendering for the contract-connectivity guard."""

from __future__ import annotations

from .models import ContractConnectivityReport
from .support import build_report as build_connectivity_report


def build_report(
    *,
    repo_root,
    absolute: bool = False,
    since_ref: str | None = None,
    head_ref: str = "HEAD",
) -> ContractConnectivityReport:
    """Proxy the typed support-layer builder."""
    return build_connectivity_report(
        repo_root=repo_root,
        absolute=absolute,
        since_ref=since_ref,
        head_ref=head_ref,
    )


def render_md(report: ContractConnectivityReport) -> str:
    lines = ["# check_contract_connectivity", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- mode: {report.mode}")
    lines.append(f"- contracts_scanned: {report.contracts_scanned}")
    lines.append(f"- importer_modules_scanned: {report.importer_modules_scanned}")
    if report.since_ref:
        lines.append(f"- since_ref: {report.since_ref}")
    lines.append(f"- head_ref: {report.head_ref}")
    lines.append(f"- orphaned_contracts: {len(report.orphaned_contracts)}")
    lines.append(f"- duplicate_contracts: {len(report.duplicate_contracts)}")
    lines.append(f"- stranded_consumers: {len(report.stranded_consumers)}")
    lines.append(f"- new_orphaned_contracts: {len(report.new_orphaned_contracts)}")
    lines.append(f"- new_duplicate_contracts: {len(report.new_duplicate_contracts)}")
    lines.append(f"- new_stranded_consumers: {len(report.new_stranded_consumers)}")

    lines.extend(("", "## Layer Counts", ""))
    for row in report.layer_counts:
        lines.append(f"- {row.layer}: {row.contract_count}")

    _append_orphans(lines, title="Orphaned Contracts", items=report.orphaned_contracts)
    _append_duplicates(lines, title="Duplicate Contracts", items=report.duplicate_contracts)
    _append_stranded(lines, title="Stranded Consumers", items=report.stranded_consumers)

    if report.mode != "absolute":
        _append_orphans(
            lines,
            title="New Orphaned Contracts",
            items=report.new_orphaned_contracts,
        )
        _append_duplicates(
            lines,
            title="New Duplicate Contracts",
            items=report.new_duplicate_contracts,
        )
        _append_stranded(
            lines,
            title="New Stranded Consumers",
            items=report.new_stranded_consumers,
        )
    return "\n".join(lines)


def _append_orphans(lines: list[str], *, title: str, items) -> None:
    if not items:
        return
    lines.extend(("", f"## {title}", ""))
    for item in items:
        detail = (
            f"- `{item.contract_name}` in `{item.module_path}` "
            f"(layer `{item.layer}`; scope `{item.consumer_scope}`; "
            f"fields: {', '.join(item.field_names) or 'none'})"
        )
        if item.importer_paths:
            detail += f"; internal importers: {', '.join(item.importer_paths)}"
        lines.append(detail)


def _append_duplicates(lines: list[str], *, title: str, items) -> None:
    if not items:
        return
    lines.extend(("", f"## {title}", ""))
    for item in items:
        lines.append(
            f"- `{item.left_contract_name}` ↔ `{item.right_contract_name}` "
            f"({item.overlap_ratio:.2f}; shared: {', '.join(item.shared_fields)})"
        )


def _append_stranded(lines: list[str], *, title: str, items) -> None:
    if not items:
        return
    lines.extend(("", f"## {title}", ""))
    for item in items:
        lines.append(
            f"- `{item.consumer_path}` rebuilds `{item.contract_name}` "
            f"({item.overlap_ratio:.2f}; raw keys: {', '.join(item.shared_raw_keys)})"
        )
