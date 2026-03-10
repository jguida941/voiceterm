"""Cross-language quality backlog collector for `devctl report`."""

from __future__ import annotations

from typing import Any

from .collect import collect_absolute_checks, collect_source_inventory
from .models import ABSOLUTE_CHECKS
from .priorities import build_priorities
from ..time_utils import utc_timestamp


def collect_quality_backlog(
    *,
    top_n: int = 40,
    include_tests: bool = False,
) -> dict[str, Any]:
    """Collect a prioritized cross-language quality backlog."""
    inventory = collect_source_inventory(include_tests=include_tests)
    check_data = collect_absolute_checks()
    checks = check_data["checks"]
    priorities, severity_counts = build_priorities(
        inventory_rows=inventory["rows"],
        checks=checks,
        top_n=max(0, top_n),
    )
    guard_failures = sum(
        1
        for row in checks.values()
        if isinstance(row, dict) and not bool(row.get("ok", False))
    )
    summary = dict(
        ranked_paths=len(priorities),
        guard_failures=guard_failures,
        critical_paths=severity_counts["critical"],
        high_paths=severity_counts["high"],
        medium_paths=severity_counts["medium"],
        low_paths=severity_counts["low"],
        source_files_scanned=len(inventory["rows_json"]),
    )
    pressure_rows = inventory["rows_json"][: min(max(10, top_n), 100)]
    return dict(
        timestamp=utc_timestamp(),
        ok=guard_failures == 0 and severity_counts["critical"] == 0,
        summary=summary,
        scope=dict(
            absolute_checks=[check.key for check in ABSOLUTE_CHECKS],
            includes_tests=include_tests,
        ),
        inventory=dict(
            language_totals=inventory["language_totals"],
            top_file_pressure=pressure_rows,
        ),
        priorities=priorities,
        checks=checks,
        warnings=check_data["warnings"],
        errors=check_data["errors"],
    )


def render_quality_backlog_markdown(backlog: dict[str, Any]) -> list[str]:
    """Render markdown section lines for the quality backlog payload."""
    if not isinstance(backlog, dict):
        return []
    summary = backlog.get("summary", {})
    priorities = backlog.get("priorities", [])
    lines = ["## Quality Backlog", ""]
    lines.append(f"- ok: {bool(backlog.get('ok', False))}")
    lines.append(f"- source_files_scanned: {summary.get('source_files_scanned', 0)}")
    lines.append(f"- guard_failures: {summary.get('guard_failures', 0)}")
    lines.append(
        "- severities: "
        f"critical={summary.get('critical_paths', 0)}, "
        f"high={summary.get('high_paths', 0)}, "
        f"medium={summary.get('medium_paths', 0)}, "
        f"low={summary.get('low_paths', 0)}"
    )
    lines.append(f"- ranked_paths: {summary.get('ranked_paths', 0)}")
    if not isinstance(priorities, list) or not priorities:
        lines.append("- priorities: none")
        return lines
    lines.append("")
    lines.append("### Top Priority Paths")
    for row in priorities[:10]:
        if not isinstance(row, dict):
            continue
        path = row.get("path", "unknown")
        score = row.get("score", 0)
        severity = row.get("severity", "unknown")
        signals = row.get("signals", [])
        signal_text = ", ".join(signals[:4]) if isinstance(signals, list) else ""
        lines.append(f"- [{severity}] `{path}` score={score} signals={signal_text}")
    return lines
