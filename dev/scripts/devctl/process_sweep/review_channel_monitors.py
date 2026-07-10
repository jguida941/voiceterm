"""Protection helpers for typed review-channel monitor processes."""

from __future__ import annotations

from typing import Any

REVIEW_CHANNEL_MONITOR_SCOPE = "repo_tooling"
REVIEW_CHANNEL_TRACE_MARKERS = (
    "dev/reports/review_channel/events/trace.ndjson",
    "dev/reports/review_channel/projections/latest/trace.ndjson",
)
REVIEW_CHANNEL_WATCH_MARKER = "review-channel --action watch"
REVIEW_CHANNEL_FOLLOW_MARKER = "--follow"


def _is_review_channel_monitor_command(command: str) -> bool:
    return any(marker in command for marker in REVIEW_CHANNEL_TRACE_MARKERS) or (
        REVIEW_CHANNEL_WATCH_MARKER in command
        and REVIEW_CHANNEL_FOLLOW_MARKER in command
    )


def review_channel_monitor_pids(rows: list[dict[str, Any]]) -> set[int]:
    """Return repo-tooling pids that are typed review-channel monitors."""
    seed_pids = {
        int(row["pid"])
        for row in rows
        if row.get("match_scope") == REVIEW_CHANNEL_MONITOR_SCOPE
        and _is_review_channel_monitor_command(str(row.get("command", "")))
    }
    if not seed_pids:
        return set()

    protected = set(seed_pids)
    changed = True
    while changed:
        changed = False
        for row in rows:
            pid = int(row.get("pid", 0) or 0)
            if pid in protected:
                continue
            if row.get("ppid") in protected:
                protected.add(pid)
                changed = True
    return protected


def review_channel_monitor_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return rows covered by review-channel monitor protection."""
    protected = review_channel_monitor_pids(rows)
    return [row for row in rows if row.get("pid") in protected]
