"""Process-sweep helpers for `devctl check`."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from ...process_sweep.core import expand_cleanup_target_rows, parse_etime_seconds


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
    protected_pids = _protected_registered_conductor_pids(
        rows=rows,
        repo_root=repo_root,
    )
    filtered_rows = [
        row for row in rows if int(row.get("pid", 0) or 0) not in protected_pids
    ]
    orphaned, active = split_orphans(filtered_rows)
    stale_active, _recent_active = split_stale(active)
    cleanup_targets = expand_cleanup_target_rows(
        filtered_rows,
        [*orphaned, *stale_active],
    )
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


SUPERVISED_CONDUCTOR_SCOPE = "review_channel_conductor"


def _session_is_cleanup_protected(session: object) -> bool:
    """Return True when a conductor session is runtime-live enough to protect.

    Host-process cleanup must key off runtime liveness, not only the broader
    governance/session freshness captured by ``session.live``. A conductor can
    remain script-running while ``session.live`` flips false because the
    prepared HEAD or instruction revision has drifted. When ``session_pid`` is
    missing, cleanup still needs enough typed identity to match the current
    wrapper by script path instead of silently protecting every conductor-like
    row.
    """
    if bool(getattr(session, "live", False)):
        return True
    return str(getattr(session, "script_probe_state", "")).strip().lower() == "running"


def _row_command_text(row: dict) -> str:
    return str(row.get("cmd") or row.get("command") or "").strip()


def _session_process_match_tokens(session: object) -> tuple[str, ...]:
    script_path = str(getattr(session, "script_path", "") or "").strip()
    if not script_path:
        return ()
    return (script_path,)


def _runtime_live_registered_conductor_sessions(
    *,
    repo_root: Path,
) -> tuple[object, ...]:
    from ...repo_packs import active_path_config
    from ...review_channel.session_probe import load_conductor_sessions

    status_dir = repo_root / active_path_config().review_status_dir_rel
    if not status_dir.exists():
        return ()

    sessions = load_conductor_sessions(session_output_root=status_dir)
    return tuple(
        session for session in sessions if _session_is_cleanup_protected(session)
    )


def _protected_registered_conductor_pids(
    *,
    rows: list[dict],
    repo_root: Path,
) -> set[int]:
    """Return runtime-live registered conductor pids plus descendants to exclude.

    Only PIDs recovered from the typed session registry
    (``load_conductor_sessions``) are protected. A running supervisor
    heartbeat is NOT sufficient on its own — unregistered detached
    wrappers must fall through to orphan/detached classification so
    invisible agents are surfaced instead of silently hidden (Q37). For
    registered sessions, runtime/script liveness is sufficient even when the
    broader launch authority has gone stale; host cleanup should not kill a
    still-running conductor just because prepared-head freshness drifted.
    """
    sessions = _runtime_live_registered_conductor_sessions(repo_root=repo_root)
    session_pids = {
        int(getattr(session, "session_pid", 0) or 0)
        for session in sessions
        if int(getattr(session, "session_pid", 0) or 0) > 0
    }
    if not session_pids:
        for session in sessions:
            tokens = _session_process_match_tokens(session)
            if not tokens:
                continue
            for row in rows:
                pid = int(row.get("pid", 0) or 0)
                if pid <= 0:
                    continue
                command = _row_command_text(row)
                if any(token in command for token in tokens):
                    session_pids.add(pid)

    if not session_pids:
        return set()
    descendants_by_parent: dict[int, list[int]] = {}
    for row in rows:
        pid = int(row.get("pid", 0) or 0)
        ppid = int(row.get("ppid", 0) or 0)
        if pid <= 0:
            continue
        descendants_by_parent.setdefault(ppid, []).append(pid)
    protected = set(session_pids)
    frontier = list(session_pids)
    while frontier:
        parent_pid = frontier.pop()
        for child_pid in descendants_by_parent.get(parent_pid, ()):
            if child_pid in protected:
                continue
            protected.add(child_pid)
            frontier.append(child_pid)
    return _include_registered_conductor_ancestors(rows=rows, protected=protected)


def _include_registered_conductor_ancestors(
    *,
    rows: list[dict],
    protected: set[int],
) -> set[int]:
    """Protect conductor wrapper ancestors of a typed-live conductor process."""
    rows_by_pid = {
        int(row.get("pid", 0) or 0): row
        for row in rows
        if int(row.get("pid", 0) or 0) > 0
    }
    expanded = set(protected)
    frontier = list(protected)
    while frontier:
        child_pid = frontier.pop()
        child_row = rows_by_pid.get(child_pid)
        if not child_row:
            continue
        parent_pid = int(child_row.get("ppid", 0) or 0)
        parent_row = rows_by_pid.get(parent_pid)
        if (
            parent_pid <= 0
            or parent_pid in expanded
            or not parent_row
            or parent_row.get("match_scope") != SUPERVISED_CONDUCTOR_SCOPE
        ):
            continue
        expanded.add(parent_pid)
        frontier.append(parent_pid)
    return expanded


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
