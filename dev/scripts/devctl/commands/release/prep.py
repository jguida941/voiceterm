"""Release metadata preparation helpers for `devctl ship`/`devctl release`."""

from __future__ import annotations

from datetime import date

from ...config import REPO_ROOT
from .prep_updates import RELEASE_METADATA_UPDATERS


def prepare_release_metadata(
    version: str,
    *,
    release_date: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Apply release version metadata updates across canonical files."""
    resolved_date = release_date or date.today().isoformat()
    changed_files: list[str] = []
    unchanged_files: list[str] = []

    for rel_path, updater in RELEASE_METADATA_UPDATERS:
        absolute = REPO_ROOT / rel_path
        if not absolute.exists():
            raise RuntimeError(f"missing release metadata file: {rel_path}")

        before = absolute.read_text(encoding="utf-8")
        after = updater(before, version, resolved_date)
        if after == before:
            unchanged_files.append(rel_path)
            continue

        changed_files.append(rel_path)
        if not dry_run:
            absolute.write_text(after, encoding="utf-8")

    return {
        "version": version,
        "release_date": resolved_date,
        "changed_files": changed_files,
        "unchanged_files": unchanged_files,
        "dry_run": dry_run,
    }
