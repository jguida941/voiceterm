"""Process-sweep helpers for `devctl check`."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from ..process_sweep import expand_cleanup_target_rows, parse_etime_seconds


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
    """Clean up detached/stale repo-related processes so local runs stay stable."""
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
    cleanup_targets = expand_cleanup_target_rows(rows, [*orphaned, *stale_active])
    killed_pids, kill_warnings = killer(cleanup_targets)

    for warning in warnings:
        print(f"[{step_name}] warning: {warning}")
    if orphaned:
        print(f"[{step_name}] detected {len(orphaned)} orphaned repo-related processes")
    if stale_active:
        print(
            f"[{step_name}] detected {len(stale_active)} stale active repo-related processes"
        )
    if killed_pids:
        print(
            f"[{step_name}] killed {len(killed_pids)} orphaned/stale repo-related processes"
        )
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


def cleanup_host_processes(
    step_name: str,
    dry_run: bool,
    *,
    repo_root: Path,
    cleanup_report_builder: Callable[..., dict],
) -> dict:
    """Run host-side cleanup + strict verify as one `check` step."""
    start = time.time()
    report = cleanup_report_builder(dry_run=dry_run, verify=True)

    if report["dry_run"]:
        return {
            "name": step_name,
            "cmd": ["internal", "host-process-cleanup", "--verify", "--dry-run"],
            "cwd": str(repo_root),
            "returncode": 0,
            "duration_s": 0.0,
            "skipped": True,
            "warnings": [],
            "errors": [],
            "killed_pids": [],
            "detected_orphans": 0,
            "detected_stale_active": 0,
            "verify_ok": True,
        }

    if report["orphaned_count_pre"]:
        print(f"[{step_name}] detected {report['orphaned_count_pre']} orphaned repo-related host processes")
    if report["stale_active_count_pre"]:
        print(
            f"[{step_name}] detected {report['stale_active_count_pre']} stale active repo-related host processes"
        )
    if report["killed_pids"]:
        print(
            f"[{step_name}] killed {len(report['killed_pids'])} orphaned/stale repo-related host processes"
        )
    for warning in report["warnings"]:
        print(f"[{step_name}] warning: {warning}")
    for error in report["errors"]:
        print(f"[{step_name}] error: {error}")

    return {
        "name": step_name,
        "cmd": ["internal", "host-process-cleanup", "--verify"],
        "cwd": str(repo_root),
        "returncode": 0 if report["ok"] else 1,
        "duration_s": round(time.time() - start, 2),
        "skipped": False,
        "warnings": list(report["warnings"]),
        "errors": list(report["errors"]),
        "killed_pids": list(report["killed_pids"]),
        "detected_orphans": report["orphaned_count_pre"],
        "detected_stale_active": report["stale_active_count_pre"],
        "verify_ok": report["verify_ok"],
    }
