"""Process-sweep helpers for `devctl check`."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from ..process_sweep import parse_etime_seconds


def parse_etime_seconds_for_compat(raw: str) -> int | None:
    """Compatibility wrapper retained for legacy tests."""
    return parse_etime_seconds(raw)


def cleanup_orphaned_voiceterm_test_binaries(
    step_name: str,
    dry_run: bool,
    *,
    repo_root: Path,
    scanner: Callable[[], tuple[list[dict], list[str]]],
    split_orphans: Callable[[list[dict]], tuple[list[dict], list[dict]]],
    split_stale: Callable[[list[dict]], tuple[list[dict], list[dict]]],
    killer: Callable[[list[dict]], tuple[list[int], list[str]]],
) -> dict:
    """Clean up detached/stale test binaries so local runs stay stable over time."""
    start = time.time()
    if dry_run:
        return {
            "name": step_name,
            "cmd": ["internal", "process-sweep", "--dry-run"],
            "cwd": str(repo_root),
            "returncode": 0,
            "duration_s": 0.0,
            "skipped": True,
            "warnings": [],
            "killed_pids": [],
            "detected_orphans": 0,
            "detected_stale_active": 0,
        }

    rows, warnings = scanner()
    orphaned, active = split_orphans(rows)
    stale_active, _recent_active = split_stale(active)
    cleanup_targets = [*orphaned, *stale_active]
    killed_pids, kill_warnings = killer(cleanup_targets)

    for warning in warnings:
        print(f"[{step_name}] warning: {warning}")
    if orphaned:
        print(f"[{step_name}] detected {len(orphaned)} orphaned voiceterm test binaries")
    if stale_active:
        print(
            f"[{step_name}] detected {len(stale_active)} stale active voiceterm test binaries"
        )
    if killed_pids:
        print(f"[{step_name}] killed {len(killed_pids)} orphaned/stale voiceterm test binaries")
    for warning in kill_warnings:
        print(f"[{step_name}] warning: {warning}")

    return {
        "name": step_name,
        "cmd": ["internal", "process-sweep", "--kill-orphans-or-stale"],
        "cwd": str(repo_root),
        "returncode": 0,
        "duration_s": round(time.time() - start, 2),
        "skipped": False,
        "warnings": warnings + kill_warnings,
        "killed_pids": killed_pids,
        "detected_orphans": len(orphaned),
        "detected_stale_active": len(stale_active),
    }
