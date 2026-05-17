"""Archive governance checks used by `devctl hygiene`."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List

ARCHIVE_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$")


def audit_archive(repo_root: Path) -> Dict:
    """Check archive filenames and dates for policy mistakes."""
    archive_dir = repo_root / "dev/archive"
    files = sorted(
        path for path in archive_dir.glob("*.md") if path.name != "README.md"
    )

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
        errors.append(
            f"Archive files with invalid filename format: {', '.join(bad_filenames)}"
        )
    if invalid_dates:
        errors.append(
            f"Archive files with invalid date prefix: {', '.join(invalid_dates)}"
        )
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
