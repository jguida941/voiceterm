"""Cached repo analytics collected for Operator Console snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
import time

try:
    from dev.scripts.devctl.collect import (
        collect_ci_runs,
        collect_git_status,
        collect_mutation_summary,
    )
    from dev.scripts.devctl.config import REPO_ROOT as DEVCTL_REPO_ROOT
except ImportError:  # pragma: no cover - repo import path should exist in-app
    collect_ci_runs = None
    collect_git_status = None
    collect_mutation_summary = None
    DEVCTL_REPO_ROOT = None

_CACHE_TTL_SECONDS = 90.0
_CACHE_LOCK = Lock()
_CACHE: dict[str, tuple[float, "RepoAnalyticsSnapshot"]] = {}


@dataclass(frozen=True)
class RepoAnalyticsSnapshot:
    """Cached repo-derived analytics used by dashboard surfaces."""

    branch: str | None
    changed_files: int
    added_files: int
    modified_files: int
    deleted_files: int
    renamed_files: int
    untracked_files: int
    conflicted_files: int
    top_paths: tuple[str, ...]
    changelog_updated: bool
    master_plan_updated: bool
    mutation_score_pct: float | None
    mutation_age_hours: float | None
    mutation_note: str | None
    ci_runs_total: int | None
    ci_success_runs: int
    ci_failed_runs: int
    ci_pending_runs: int
    ci_note: str | None
    collection_note: str | None = None


def collect_repo_analytics(repo_root: Path) -> RepoAnalyticsSnapshot:
    """Return cached repo analytics for the current repository."""
    if not repo_root.exists():
        return _unavailable_snapshot("repo root is unavailable")
    if DEVCTL_REPO_ROOT is None:
        return _unavailable_snapshot("repo analytics helpers are unavailable")
    if repo_root.resolve() != Path(DEVCTL_REPO_ROOT).resolve():
        return _unavailable_snapshot(
            "repo analytics are only wired for the current codex-voice repo root"
        )

    cache_key = str(repo_root.resolve())
    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None and now - cached[0] < _CACHE_TTL_SECONDS:
            return cached[1]

    snapshot = _collect_uncached()
    with _CACHE_LOCK:
        _CACHE[cache_key] = (now, snapshot)
    return snapshot


def _collect_uncached() -> RepoAnalyticsSnapshot:
    if collect_git_status is None or collect_mutation_summary is None:
        return _unavailable_snapshot("repo analytics helpers are unavailable")

    git_info = collect_git_status()
    changes = git_info.get("changes", []) if isinstance(git_info, dict) else []
    if not isinstance(changes, list):
        changes = []
    status_counts = {
        "added": 0,
        "modified": 0,
        "deleted": 0,
        "renamed": 0,
        "untracked": 0,
        "conflicted": 0,
    }
    top_paths: list[str] = []
    for change in changes:
        if not isinstance(change, dict):
            continue
        status = str(change.get("status") or "")
        path = str(change.get("path") or "").strip()
        bucket = _classify_change_status(status)
        status_counts[bucket] += 1
        if path and path not in top_paths and len(top_paths) < 6:
            top_paths.append(path)

    mutation_info = collect_mutation_summary()
    mutation_results = (
        mutation_info.get("results", {}) if isinstance(mutation_info, dict) else {}
    )
    mutation_score_pct = _float_or_none(mutation_results.get("score"))
    mutation_age_hours = _float_or_none(mutation_results.get("outcomes_age_hours"))
    mutation_note = _first_text(
        mutation_info.get("warning") if isinstance(mutation_info, dict) else None,
        mutation_info.get("error") if isinstance(mutation_info, dict) else None,
    )

    ci_runs_total = None
    ci_success_runs = 0
    ci_failed_runs = 0
    ci_pending_runs = 0
    ci_note = None
    if collect_ci_runs is not None:
        ci_info = collect_ci_runs(limit=5)
        runs = ci_info.get("runs", []) if isinstance(ci_info, dict) else []
        if isinstance(runs, list):
            ci_runs_total = len(runs)
            for run in runs:
                if not isinstance(run, dict):
                    continue
                conclusion = str(run.get("conclusion") or "").strip().lower()
                status = str(run.get("status") or "").strip().lower()
                if conclusion == "success":
                    ci_success_runs += 1
                elif conclusion in {
                    "failure",
                    "cancelled",
                    "timed_out",
                    "startup_failure",
                    "action_required",
                }:
                    ci_failed_runs += 1
                else:
                    if status in {"queued", "in_progress", "requested", "waiting"} or not conclusion:
                        ci_pending_runs += 1
        ci_note = _first_text(
            ci_info.get("warning") if isinstance(ci_info, dict) else None,
            ci_info.get("error") if isinstance(ci_info, dict) else None,
        )

    return RepoAnalyticsSnapshot(
        branch=_safe_text(git_info.get("branch")) if isinstance(git_info, dict) else None,
        changed_files=len(changes),
        added_files=status_counts["added"],
        modified_files=status_counts["modified"],
        deleted_files=status_counts["deleted"],
        renamed_files=status_counts["renamed"],
        untracked_files=status_counts["untracked"],
        conflicted_files=status_counts["conflicted"],
        top_paths=tuple(top_paths),
        changelog_updated=bool(git_info.get("changelog_updated")) if isinstance(git_info, dict) else False,
        master_plan_updated=bool(git_info.get("master_plan_updated")) if isinstance(git_info, dict) else False,
        mutation_score_pct=mutation_score_pct,
        mutation_age_hours=mutation_age_hours,
        mutation_note=mutation_note,
        ci_runs_total=ci_runs_total,
        ci_success_runs=ci_success_runs,
        ci_failed_runs=ci_failed_runs,
        ci_pending_runs=ci_pending_runs,
        ci_note=ci_note,
    )


def _unavailable_snapshot(note: str) -> RepoAnalyticsSnapshot:
    return RepoAnalyticsSnapshot(
        branch=None,
        changed_files=0,
        added_files=0,
        modified_files=0,
        deleted_files=0,
        renamed_files=0,
        untracked_files=0,
        conflicted_files=0,
        top_paths=(),
        changelog_updated=False,
        master_plan_updated=False,
        mutation_score_pct=None,
        mutation_age_hours=None,
        mutation_note=None,
        ci_runs_total=None,
        ci_success_runs=0,
        ci_failed_runs=0,
        ci_pending_runs=0,
        ci_note=None,
        collection_note=note,
    )


def _classify_change_status(status: str) -> str:
    trimmed = status.strip().upper()
    if trimmed == "??":
        return "untracked"
    if "U" in trimmed or trimmed == "AA":
        return "conflicted"
    if "R" in trimmed:
        return "renamed"
    if "D" in trimmed:
        return "deleted"
    if "A" in trimmed:
        return "added"
    return "modified"


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _safe_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _first_text(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
