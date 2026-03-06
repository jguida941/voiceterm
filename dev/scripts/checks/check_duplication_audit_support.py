"""Support helpers for duplication audit reporting and fallback scanning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable


def derive_status(
    *,
    errors: list[str],
    warnings: list[str],
    blocked_by_tooling: bool,
    duplication_percent: float | None,
    max_duplication_percent: float,
    report_age_hours: float | None,
    max_age_hours: float,
    report_exists: bool,
) -> str:
    if blocked_by_tooling:
        return "blocked_by_tooling"
    if not report_exists and any("missing report file" in error for error in errors):
        return "missing_report"
    if (
        duplication_percent is not None
        and duplication_percent > max_duplication_percent
        and any("duplication percent exceeds threshold" in error for error in errors)
    ):
        return "duplication_threshold_exceeded"
    if (
        report_age_hours is not None
        and report_age_hours > max_age_hours
        and any("jscpd report is stale" in error for error in errors)
    ):
        return "stale_report"
    if errors:
        return "error"
    if warnings:
        return "ok_with_warnings"
    return "ok"


def render_markdown(report: dict) -> str:
    lines = [
        "# check_duplication_audit",
        "",
        f"- ok: {report['ok']}",
        f"- status: {report['status']}",
        f"- blocked_by_tooling: {report['blocked_by_tooling']}",
        f"- source_root: {report['source_root']}",
        f"- report_path: {report['report_path']}",
        f"- run_jscpd: {report['run_jscpd']}",
        f"- run_python_fallback: {report['run_python_fallback']}",
        f"- allow_missing_tool: {report['allow_missing_tool']}",
        f"- jscpd_status: {report['jscpd_status']}",
        f"- report_exists: {report['report_exists']}",
        (
            "- report_age_hours: null"
            if report["report_age_hours"] is None
            else f"- report_age_hours: {report['report_age_hours']:.2f}"
        ),
        f"- max_age_hours: {report['max_age_hours']:.2f}",
        (
            "- duplication_percent: null"
            if report["duplication_percent"] is None
            else f"- duplication_percent: {report['duplication_percent']:.2f}"
        ),
        f"- max_duplication_percent: {report['max_duplication_percent']:.2f}",
        (
            "- duplicates_count: null"
            if report["duplicates_count"] is None
            else f"- duplicates_count: {report['duplicates_count']}"
        ),
    ]
    if report["errors"]:
        lines.append("- errors:")
        lines.extend(f"  - {entry}" for entry in report["errors"])
    if report["warnings"]:
        lines.append("- warnings:")
        lines.extend(f"  - {entry}" for entry in report["warnings"])
    if not report["errors"]:
        lines.append("- errors: none")
    if not report["warnings"]:
        lines.append("- warnings: none")
    return "\n".join(lines)


def run_python_fallback(
    *,
    source_root: Path,
    report_path: Path,
    min_lines: int,
    path_for_report: Callable[[Path], str],
) -> tuple[bool, str | None, str]:
    try:
        payload = _build_fallback_payload(source_root=source_root, min_lines=min_lines)
    except (OSError, ValueError) as exc:
        return False, f"python fallback failed: {exc}", "python_fallback_failed"

    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        return (
            False,
            f"python fallback failed to write report at {path_for_report(report_path)}: {exc}",
            "python_fallback_failed",
        )
    return True, None, "python_fallback"


def _build_fallback_payload(*, source_root: Path, min_lines: int) -> dict:
    if min_lines <= 0:
        raise ValueError("min_lines must be greater than zero")
    if not source_root.exists():
        raise ValueError(f"source root does not exist: {source_root}")

    file_records: list[tuple[Path, list[str]]] = []
    total_lines = 0
    for file_path in sorted(source_root.rglob("*")):
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        file_records.append((file_path, lines))
        total_lines += len(lines)

    window_map: dict[tuple[str, ...], list[tuple[int, int]]] = {}
    for file_idx, (_path, lines) in enumerate(file_records):
        if len(lines) < min_lines:
            continue
        for start in range(0, len(lines) - min_lines + 1):
            window = tuple(lines[start : start + min_lines])
            if not any(fragment.strip() for fragment in window):
                continue
            window_map.setdefault(window, []).append((file_idx, start))

    duplicate_entries: list[dict] = []
    duplicated_line_refs: set[tuple[int, int]] = set()
    for window, hits in window_map.items():
        if len(hits) < 2:
            continue
        anchor_file_idx, anchor_start = hits[0]
        anchor_file_path, _ = file_records[anchor_file_idx]
        for other_file_idx, other_start in hits[1:]:
            other_file_path, _ = file_records[other_file_idx]
            duplicate_entries.append(
                {
                    "format": "python_fallback",
                    "fragment": "\n".join(window),
                    "firstFile": {"name": anchor_file_path.as_posix(), "start": anchor_start + 1},
                    "secondFile": {"name": other_file_path.as_posix(), "start": other_start + 1},
                    "lines": min_lines,
                    "tokens": min_lines,
                }
            )
            for offset in range(min_lines):
                duplicated_line_refs.add((anchor_file_idx, anchor_start + offset))
                duplicated_line_refs.add((other_file_idx, other_start + offset))

    duplicated_lines = len(duplicated_line_refs)
    duplication_percent = 0.0
    if total_lines > 0:
        duplication_percent = (duplicated_lines / total_lines) * 100.0

    return {
        "statistics": {
            "total": {
                "lines": total_lines,
                "duplicatedLines": duplicated_lines,
                "percentage": duplication_percent,
            }
        },
        "duplicates": duplicate_entries,
        "meta": {
            "generatedBy": "check_duplication_audit.py python fallback",
            "sourceRoot": source_root.as_posix(),
            "minLines": min_lines,
        },
    }

