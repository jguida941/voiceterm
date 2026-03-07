"""ADR governance checks used by `devctl hygiene`."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .hygiene_audits_adrs_backlog import analyze_adr_id_governance
from .hygiene_audits_adrs_metadata import (
    ADR_INDEX_LINK_RE,
    ADR_INDEX_ROW_RE,
    ALLOWED_ADR_STATUSES,
    ISO_DATE_RE,
    extract_field,
)


def audit_adrs(repo_root: Path) -> Dict:
    """Check ADR metadata and ADR index consistency."""
    adr_dir = repo_root / "dev/adr"
    index_path = adr_dir / "README.md"
    adr_files = sorted(path for path in adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md"))
    tracked_adrs = [path for path in adr_files if path.name != "0000-template.md"]

    errors: List[str] = []
    warnings: List[str] = []
    missing_status: List[str] = []
    invalid_status: List[str] = []
    missing_date: List[str] = []
    invalid_date: List[str] = []
    superseded_missing_link: List[str] = []
    index_missing: List[str] = []
    index_status_mismatch: List[str] = []
    broken_index_links: List[str] = []

    status_by_id: Dict[str, str] = {}
    for path in tracked_adrs:
        text = path.read_text(encoding="utf-8")
        adr_id = path.name[:4]

        status = extract_field(text, "Status")
        date_value = extract_field(text, "Date")
        superseded_by = extract_field(text, "Superseded-by")

        if not status:
            missing_status.append(path.name)
        elif status not in ALLOWED_ADR_STATUSES:
            invalid_status.append(f"{path.name} ({status})")
        else:
            status_by_id[adr_id] = status

        if not date_value:
            missing_date.append(path.name)
        elif not ISO_DATE_RE.match(date_value):
            invalid_date.append(f"{path.name} ({date_value})")

        if status == "Superseded" and not superseded_by:
            superseded_missing_link.append(path.name)
        if superseded_by and status != "Superseded":
            warnings.append(f"{path.name} defines Superseded-by but status is {status}")

    index_text = index_path.read_text(encoding="utf-8")
    linked_ids = {match.group(1) for match in ADR_INDEX_LINK_RE.finditer(index_text)}

    for path in tracked_adrs:
        adr_id = path.name[:4]
        if adr_id not in linked_ids:
            index_missing.append(path.name)

    index_row_status: Dict[str, str] = {}
    for match in ADR_INDEX_ROW_RE.finditer(index_text):
        index_row_status[match.group(1)] = match.group(2)

    for adr_id, status in status_by_id.items():
        listed_status = index_row_status.get(adr_id)
        if listed_status and listed_status != status:
            index_status_mismatch.append(
                f"{adr_id} (file={status}, index={listed_status})"
            )

    for match in ADR_INDEX_LINK_RE.finditer(index_text):
        path = match.group(2)
        if not path.endswith(".md"):
            continue
        target = (adr_dir / path).resolve()
        if not target.exists():
            broken_index_links.append(path)

    tracking = analyze_adr_id_governance(
        tracked_ids_int=sorted(int(path.name[:4]) for path in tracked_adrs),
        index_text=index_text,
        repo_root=repo_root,
        errors=errors,
        warnings=warnings,
    )

    if missing_status:
        errors.append(f"ADRs missing Status: {', '.join(missing_status)}")
    if invalid_status:
        errors.append(f"ADRs with invalid Status value: {', '.join(invalid_status)}")
    if missing_date:
        errors.append(f"ADRs missing Date: {', '.join(missing_date)}")
    if invalid_date:
        errors.append(f"ADRs with invalid Date format: {', '.join(invalid_date)}")
    if superseded_missing_link:
        errors.append(
            "Superseded ADRs missing Superseded-by metadata: "
            + ", ".join(superseded_missing_link)
        )
    if index_missing:
        errors.append(f"ADRs missing from ADR index: {', '.join(index_missing)}")
    if index_status_mismatch:
        errors.append(
            f"ADR status mismatch between file and index: {', '.join(index_status_mismatch)}"
        )
    if broken_index_links:
        errors.append(
            f"Broken ADR index links: {', '.join(sorted(set(broken_index_links)))}"
        )

    return {
        "total_adrs": len(tracked_adrs),
        "missing_status": missing_status,
        "invalid_status": invalid_status,
        "missing_date": missing_date,
        "invalid_date": invalid_date,
        "superseded_missing_link": superseded_missing_link,
        "index_missing": index_missing,
        "index_status_mismatch": index_status_mismatch,
        "broken_index_links": sorted(set(broken_index_links)),
        "missing_sequence_ids": [
            f"{value:04d}" for value in tracking["missing_sequence_ids"]
        ],
        "retired_ids": [f"{value:04d}" for value in tracking["retired_ids"]],
        "reserved_ids": [f"{value:04d}" for value in tracking["reserved_ids"]],
        "unexplained_gap_ids": [
            f"{value:04d}" for value in tracking["unexplained_gap_ids"]
        ],
        "stale_governed_ids": [
            f"{value:04d}" for value in tracking["stale_governed_ids"]
        ],
        "backlog_master_ids": [
            f"{value:04d}" for value in tracking["backlog_master_ids"]
        ],
        "backlog_autonomy_ids": [
            f"{value:04d}" for value in tracking["backlog_autonomy_ids"]
        ],
        "backlog_missing_reserved_ids": [
            f"{value:04d}" for value in tracking["backlog_missing_reserved_ids"]
        ],
        "backlog_existing_ids": [
            f"{value:04d}" for value in tracking["backlog_existing_ids"]
        ],
        "reserved_not_backlog_ids": [
            f"{value:04d}" for value in tracking["reserved_not_backlog_ids"]
        ],
        "backlog_scope_mismatch": tracking["backlog_scope_mismatch"],
        "next_pointer_value": (
            f"{tracking['next_pointer_value']:04d}"
            if tracking["next_pointer_value"] is not None
            else None
        ),
        "next_pointer_expected": (
            f"{tracking['next_pointer_expected']:04d}"
            if tracking["next_pointer_expected"] is not None
            else None
        ),
        "stale_reference_violations": tracking["stale_reference_violations"],
        "errors": errors,
        "warnings": warnings,
    }
