"""Shared support helpers for probe report rendering."""

from __future__ import annotations

import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .decision_packets import (
    ALLOWLIST_FILENAME,
    AllowlistEntry,
    DecisionPacket,
    FilteredFindings,
    build_design_decision_packet,
    build_design_decision_packets,
    filter_findings,
    load_allowlist,
)


def extract_source_snippet(
    file_path: str,
    symbol: str,
    repo_root: Path | None,
    *,
    context_lines: int = 3,
) -> str | None:
    """Extract a source code snippet around the named symbol."""
    if repo_root is None:
        return None
    full_path = repo_root / file_path
    if not full_path.exists():
        return None
    try:
        lines = full_path.read_text().splitlines()
    except OSError:
        return None

    target_line = next(
        (
            index
            for index, line in enumerate(lines)
            if f"def {symbol}(" in line or f"class {symbol}" in line or f"fn {symbol}(" in line
        ),
        None,
    )
    if target_line is None:
        return None

    start = max(0, target_line - context_lines)
    end = min(len(lines), target_line + context_lines + 10)
    snippet_lines = []
    for index in range(start, end):
        marker = ">>>" if index == target_line else "   "
        snippet_lines.append(f"{marker} {index + 1:4d} | {lines[index]}")

    lang = "rust" if file_path.endswith(".rs") else "python"
    return f"```{lang}\n" + "\n".join(snippet_lines) + "\n```"


def get_git_diff_for_file(file_path: str, repo_root: Path | None) -> str | None:
    """Get the git diff for a specific file."""
    if repo_root is None:
        return None
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--", file_path],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            check=False,
        )
    except OSError:
        return None
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


@dataclass
class AggregatedReport:
    """Aggregated multi-probe report data."""

    probe_results: list[dict[str, Any]] = field(default_factory=list)
    total_files_scanned: int = 0
    total_hints: int = 0
    hints_by_severity: dict[str, int] = field(default_factory=dict)
    hints_by_file: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


def aggregate_probe_results(reports: list[dict[str, Any]]) -> AggregatedReport:
    """Combine multiple probe JSON reports into a single view."""
    aggregated = AggregatedReport(probe_results=reports)
    severity_counts: dict[str, int] = defaultdict(int)
    file_hints: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for report in reports:
        aggregated.total_files_scanned += int(report.get("files_scanned", 0))
        for hint in report.get("risk_hints", []):
            aggregated.total_hints += 1
            severity = hint.get("severity", "medium")
            severity_counts[severity] += 1
            file_path = hint.get("file", "unknown")
            enriched_hint = {**hint, "probe": report.get("command", "unknown")}
            file_hints[file_path].append(enriched_hint)

    aggregated.hints_by_severity = dict(severity_counts)
    aggregated.hints_by_file = dict(file_hints)
    return aggregated
