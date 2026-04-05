"""Shared utility functions for the dashboard module family.

These utilities are used by both ``dashboard.py`` (the command entry point) and
``dashboard_builders.py`` (the section builders).  Extracted to break a circular
import between the two.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..repo_packs import active_path_config


def _paths() -> dict[str, str]:
    """Derive artifact paths from the active repo-pack path config.

    Paths that already exist in RepoPathConfig are resolved from it. Paths
    that are dashboard-specific and not yet migrated to RepoPathConfig are
    kept as local constants with a migration note.
    """
    cfg = active_path_config()
    status_dir = cfg.review_status_dir_rel

    return {
        "compact_json": f"{status_dir}/compact.json",
        "full_json": f"{status_dir}/full.json",
        "review_state_json": cfg.review_state_json_rel,
        "push_json": cfg.push_report_rel,
        # TODO: migrate receipt_json to RepoPathConfig
        "receipt_json": "dev/reports/startup/latest/receipt.json",
        "agents_json": f"{status_dir}/registry/agents.json",
        # TODO: migrate pipeline_json to RepoPathConfig
        "pipeline_json": f"{status_dir}/commit_pipeline.json",
        # TODO: migrate publisher_hb to RepoPathConfig
        "publisher_hb": f"{status_dir}/publisher_heartbeat.json",
        # TODO: migrate supervisor_hb to RepoPathConfig
        "supervisor_hb": f"{status_dir}/reviewer_supervisor_heartbeat.json",
        "events_jsonl": cfg.audit_event_log_rel,
        "bridge_md": cfg.bridge_rel,
        "master_plan": cfg.active_master_plan_doc_rel,
        "governance_review_json": f"{cfg.governance_review_summary_root_rel}/review_summary.json",
        "probe_summary_json": f"{cfg.probe_report_output_root_rel}/latest/summary.json",
        "data_science_json": cfg.watchdog_summary_rel,
        # TODO: migrate conductor session paths to RepoPathConfig
        "codex_conductor_session": f"{status_dir}/sessions/codex-conductor.json",
        "claude_conductor_session": f"{status_dir}/sessions/claude-conductor.json",
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    """Read a JSON artifact, returning None on any failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _age_seconds(utc_stamp: str) -> int | None:
    """Compute seconds elapsed since a UTC ISO-8601 timestamp, or None."""
    if not utc_stamp or utc_stamp == "n/a":
        return None
    try:
        ts = datetime.fromisoformat(utc_stamp.replace("Z", "+00:00"))
        return max(0, int((datetime.now(timezone.utc) - ts).total_seconds()))
    except (ValueError, TypeError):
        return None


def _format_age(seconds: int | None) -> str:
    """Human-readable short age string: '42s ago', '12m ago', '3h ago'."""
    if seconds is None:
        return "--"
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    return f"{seconds // 3600}h ago"


def _format_duration(seconds: int | None) -> str:
    """Human-readable short duration without 'ago': '42s', '45m', '2h 15m'."""
    if seconds is None:
        return "--"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    if mins:
        return f"{hours}h {mins}m"
    return f"{hours}h"


def _tail_lines(path: Path, count: int = 10) -> list[str]:
    """Read the last *count* lines of a file without loading the entire file.

    Uses a seek-from-end strategy to handle large JSONL logs efficiently.
    Returns an empty list on any IO failure.
    """
    try:
        size = path.stat().st_size
    except OSError:
        return []
    if size == 0:
        return []
    chunk_size = min(size, count * 2048)
    try:
        with open(path, "rb") as fh:
            fh.seek(max(0, size - chunk_size))
            raw = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    return lines[-count:]


def _extract_time_from_iso(ts: str) -> str:
    """Pull HH:MM:SS from an ISO-8601 timestamp string."""
    if not ts:
        return "--:--:--"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return "--:--:--"
