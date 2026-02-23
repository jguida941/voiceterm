"""Reusable audit helpers for `devctl hygiene`.

Use these helpers when you need to add or change hygiene rules.
Keeping them separate from the command runner keeps the checks easier to read.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List

ALLOWED_ADR_STATUSES = {"Proposed", "Accepted", "Deprecated", "Superseded"}
ARCHIVE_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$")
ADR_INDEX_LINK_RE = re.compile(r"\[(\d{4})\]\(([^)]+)\)")
ADR_INDEX_ROW_RE = re.compile(r"\|\s*\[(\d{4})\]\([^)]+\)\s*\|[^|]*\|\s*([A-Za-z]+)\s*\|")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def extract_field(text: str, field: str) -> str:
    """Read `Field: value` metadata from markdown files."""
    match = re.search(rf"^{re.escape(field)}:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def audit_archive(repo_root: Path) -> Dict:
    """Check archive filenames and dates for policy mistakes."""
    archive_dir = repo_root / "dev/archive"
    files = sorted(path for path in archive_dir.glob("*.md") if path.name != "README.md")

    bad_filenames: List[str] = []
    invalid_dates: List[str] = []
    future_dates: List[str] = []
    errors: List[str] = []
    warnings: List[str] = []

    today = date.today()
    for path in files:
        name = path.name
        if not ARCHIVE_NAME_RE.match(name):
            bad_filenames.append(name)
            continue
        date_prefix = name[:10]
        try:
            entry_date = datetime.strptime(date_prefix, "%Y-%m-%d").date()
        except ValueError:
            invalid_dates.append(name)
            continue
        if entry_date > today:
            future_dates.append(name)

    if bad_filenames:
        errors.append(f"Archive files with invalid filename format: {', '.join(bad_filenames)}")
    if invalid_dates:
        errors.append(f"Archive files with invalid date prefix: {', '.join(invalid_dates)}")
    if future_dates:
        warnings.append(f"Archive files dated in the future: {', '.join(future_dates)}")

    return {
        "total_entries": len(files),
        "bad_filenames": bad_filenames,
        "invalid_dates": invalid_dates,
        "future_dates": future_dates,
        "errors": errors,
        "warnings": warnings,
    }


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
            index_status_mismatch.append(f"{adr_id} (file={status}, index={listed_status})")

    for match in ADR_INDEX_LINK_RE.finditer(index_text):
        path = match.group(2)
        if not path.endswith(".md"):
            continue
        target = (adr_dir / path).resolve()
        if not target.exists():
            broken_index_links.append(path)

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
        errors.append(f"ADR status mismatch between file and index: {', '.join(index_status_mismatch)}")
    if broken_index_links:
        errors.append(f"Broken ADR index links: {', '.join(sorted(set(broken_index_links)))}")

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
        "errors": errors,
        "warnings": warnings,
    }


def audit_scripts(repo_root: Path) -> Dict:
    """Check script inventory docs and cache-dir hygiene."""
    scripts_dir = repo_root / "dev/scripts"
    checks_dir = scripts_dir / "checks"
    readme_path = scripts_dir / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")

    top_level_scripts = sorted(
        path.name for path in scripts_dir.iterdir() if path.is_file() and path.name != "README.md"
    )
    undocumented = [name for name in top_level_scripts if name not in readme_text]
    check_scripts = sorted(
        str(path.relative_to(repo_root))
        for path in checks_dir.glob("check_*.py")
        if path.is_file()
    )
    undocumented_checks = [path for path in check_scripts if path not in readme_text]

    pycache_dirs = sorted(
        str(path.relative_to(repo_root))
        for path in scripts_dir.rglob("__pycache__")
        if path.is_dir()
    )

    errors: List[str] = []
    warnings: List[str] = []
    if undocumented:
        errors.append(
            "Top-level scripts not documented in dev/scripts/README.md: "
            + ", ".join(undocumented)
        )
    if undocumented_checks:
        errors.append(
            "Check scripts not documented in dev/scripts/README.md: "
            + ", ".join(undocumented_checks)
        )
    if pycache_dirs:
        warnings.append(f"Python cache directories present in repo tree: {', '.join(pycache_dirs)}")

    return {
        "top_level_scripts": top_level_scripts,
        "undocumented": undocumented,
        "check_scripts": check_scripts,
        "undocumented_checks": undocumented_checks,
        "pycache_dirs": pycache_dirs,
        "errors": errors,
        "warnings": warnings,
    }
