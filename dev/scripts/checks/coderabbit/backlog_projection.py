"""Bounded backlog projections shared by CodeRabbit loop consumers."""

from __future__ import annotations

from typing import Any

MAX_BACKLOG_REPORT_ITEMS = 6


def project_backlog_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a bounded structured backlog slice for downstream consumers."""
    projected: list[dict[str, Any]] = []
    for item in items[:MAX_BACKLOG_REPORT_ITEMS]:
        row: dict[str, Any] = {}
        for key in (
            "summary",
            "severity",
            "category",
            "path",
            "file",
            "file_path",
            "line",
            "end_line",
            "module",
            "target",
            "symbol",
            "check_id",
        ):
            value = item.get(key)
            if value in (None, "", []):
                continue
            row[key] = value
        if row:
            projected.append(row)
    return projected
