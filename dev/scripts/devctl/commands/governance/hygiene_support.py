"""Support helpers for the governed `devctl hygiene` command."""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Callable

from ...config import REPO_ROOT
from ...process_sweep.core import (
    DEFAULT_ORPHAN_MIN_AGE_SECONDS,
    DEFAULT_STALE_MIN_AGE_SECONDS,
    SECONDS_PER_DAY,
    format_process_rows,
    split_orphaned_processes,
    split_stale_processes,
)

ORPHAN_TEST_MIN_AGE_SECONDS = DEFAULT_ORPHAN_MIN_AGE_SECONDS
STALE_ACTIVE_TEST_MIN_AGE_SECONDS = DEFAULT_STALE_MIN_AGE_SECONDS
PROCESS_LINE_MAX_LEN = 180
PROCESS_REPORT_LIMIT = 8
SUPERVISED_CONDUCTOR_SCOPE = "review_channel_conductor"
MUTATION_BADGE_PATH = ".github/badges/mutation-score.json"
MUTATION_BADGE_MAX_AGE_DAYS = 14
README_REQUIRED_DIRS = ("dev/history", "dev/deferred", "dev/active", "dev/adr")


def _is_sandbox_ps_warning(message: str) -> bool:
    lowered = message.lower()
    return "unable to execute ps" in lowered and "operation not permitted" in lowered


def _format_process_rows(rows: list[dict]) -> str:
    return format_process_rows(
        rows,
        line_max_len=PROCESS_LINE_MAX_LEN,
        row_limit=PROCESS_REPORT_LIMIT,
    )


def _runtime_process_label(rows: list[dict]) -> str:
    scopes = {
        str(row.get("match_scope", "")).strip()
        for row in rows
        if row.get("match_scope")
    }
    return (
        "voiceterm test processes"
        if not scopes or scopes == {"voiceterm"}
        else "repo-related host processes"
    )


def _audit_runtime_processes(
    *,
    process_scanner: Callable[[], tuple[list[dict], list[str]]],
) -> dict:
    """Detect orphaned repo-related host processes and report active ones."""
    test_processes, scan_warnings = process_scanner()
    errors: list[str] = []
    warnings: list[str] = []

    ci_env = os.environ.get("CI", "").strip().lower()
    ci_mode = ci_env in {"1", "true", "yes"}
    for warning in scan_warnings:
        if _is_sandbox_ps_warning(warning):
            continue
        if ci_mode:
            errors.append(f"Runtime process sweep unavailable in CI: {warning}")
        else:
            warnings.append(warning)

    orphaned, active = split_orphaned_processes(
        test_processes,
        min_age_seconds=ORPHAN_TEST_MIN_AGE_SECONDS,
    )
    supervised_conductors = [
        row
        for row in active
        if row.get("match_scope") == SUPERVISED_CONDUCTOR_SCOPE
        and row.get("ppid") != 1
    ]
    supervised_conductor_pids = {row["pid"] for row in supervised_conductors}
    active = [row for row in active if row.get("pid") not in supervised_conductor_pids]
    stale_active, fresh_active = split_stale_processes(
        active,
        min_age_seconds=STALE_ACTIVE_TEST_MIN_AGE_SECONDS,
    )
    process_label = _runtime_process_label(test_processes)

    if orphaned:
        prefix = (
            "Orphaned voiceterm test processes detected. Stop leaked runners before continuing: "
            if process_label == "voiceterm test processes"
            else "Orphaned repo-related host processes detected (detached PPID=1). Stop leaked runners before continuing: "
        )
        errors.append(prefix + _format_process_rows(orphaned))

    if stale_active:
        prefix = (
            "Stale active voiceterm test processes detected. "
            if process_label == "voiceterm test processes"
            else "Stale active repo-related host processes detected. "
        )
        errors.append(
            prefix
            + f"Any process running >= {STALE_ACTIVE_TEST_MIN_AGE_SECONDS}s should be stopped: "
            + _format_process_rows(stale_active)
        )

    if fresh_active:
        prefix = (
            "Active voiceterm test processes detected: "
            if process_label == "voiceterm test processes"
            else "Active repo-related host processes detected during hygiene run: "
        )
        warnings.append(prefix + _format_process_rows(fresh_active))

    report: dict[str, object] = {}
    report["total_detected"] = len(test_processes)
    report["active_supervised_conductors"] = supervised_conductors
    report["orphaned"] = orphaned
    report["stale_active"] = stale_active
    report["active"] = fresh_active
    report["errors"] = errors
    report["warnings"] = warnings
    return report


def _fix_pycache_dirs(pycache_dirs: list[str]) -> dict:
    """Remove detected `__pycache__` dirs under repo-root-safe paths."""
    removed: list[str] = []
    failed: list[str] = []
    skipped: list[str] = []
    repo_root_resolved = REPO_ROOT.resolve()

    for relative_path in pycache_dirs:
        candidate = REPO_ROOT / relative_path
        if candidate.name != "__pycache__":
            skipped.append(f"{relative_path} (name is not __pycache__)")
            continue
        try:
            resolved = candidate.resolve()
        except OSError as exc:
            failed.append(f"{relative_path} (resolve failed: {exc})")
            continue
        try:
            resolved.relative_to(repo_root_resolved)
        except ValueError:
            failed.append(f"{relative_path} (outside repo root)")
            continue
        if not candidate.exists():
            skipped.append(f"{relative_path} (already absent)")
            continue
        if not candidate.is_dir():
            failed.append(f"{relative_path} (not a directory)")
            continue
        if candidate.is_symlink():
            failed.append(f"{relative_path} (symlink deletion is blocked)")
            continue
        try:
            shutil.rmtree(candidate)
        except OSError as exc:
            failed.append(f"{relative_path} ({exc})")
            continue
        removed.append(relative_path)

    report = {"requested": True}
    report["removed"] = removed
    report["failed"] = failed
    report["skipped"] = skipped
    return report


def _audit_mutation_badge() -> dict:
    """Warn if the mutation badge JSON is stale or missing."""
    errors: list[str] = []
    warnings: list[str] = []
    badge_path = REPO_ROOT / MUTATION_BADGE_PATH
    if not badge_path.exists():
        return {"errors": errors, "warnings": warnings}
    try:
        mtime = badge_path.stat().st_mtime
        age_days = (time.time() - mtime) / SECONDS_PER_DAY
        if age_days > MUTATION_BADGE_MAX_AGE_DAYS:
            warnings.append(
                f"Mutation badge is {age_days:.0f} days old "
                f"(threshold: {MUTATION_BADGE_MAX_AGE_DAYS} days). "
                "Re-run mutation testing to refresh."
            )
        data = json.loads(badge_path.read_text(encoding="utf-8"))
        if data.get("message", "").lower() == "stale":
            warnings.append("Mutation badge status is marked 'stale'.")
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"Unable to read mutation badge: {exc}")
    return {"errors": errors, "warnings": warnings}


def _audit_readme_presence() -> dict:
    """Warn if required dev directories are missing README files."""
    errors: list[str] = []
    warnings: list[str] = []
    for dir_path in README_REQUIRED_DIRS:
        full = REPO_ROOT / dir_path
        if not full.is_dir():
            continue
        readme = full / "README.md"
        if not readme.exists():
            warnings.append(f"{dir_path}/README.md is missing.")
    return {"errors": errors, "warnings": warnings}
