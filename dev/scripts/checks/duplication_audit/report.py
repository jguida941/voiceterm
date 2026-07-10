"""Report parsing helpers for the duplication-audit script."""

from __future__ import annotations

import json
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import REPO_ROOT


def _path_for_report(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _load_report(path: Path) -> tuple[dict | None, str | None]:
    if not path.exists():
        return None, _missing_report_message(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return None, f"failed to parse jscpd report: {exc}"
    if not isinstance(payload, dict):
        return None, "jscpd report root must be a JSON object"
    return payload, None


def _extract_duplication_percent(payload: dict) -> float | None:
    stats = payload.get("statistics")
    if not isinstance(stats, dict):
        return None
    total = stats.get("total")
    if not isinstance(total, dict):
        return None
    percent = total.get("percentage")
    if isinstance(percent, (int, float)):
        return float(percent)
    return None


def _extract_duplicates_count(payload: dict) -> int | None:
    duplicates = payload.get("duplicates")
    if isinstance(duplicates, list):
        return len(duplicates)
    return None


def _missing_report_message(path: Path) -> str:
    return (
        f"missing report file: {_path_for_report(path)}; run with --run-jscpd "
        "(requires jscpd, install via `npm install -g jscpd`) or pass --report-path "
        "to an existing jscpd JSON report"
    )
