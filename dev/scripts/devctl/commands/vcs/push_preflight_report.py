"""Push preflight report artifact helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PUSH_PREFLIGHT_CHECK_ROUTER_REPORT = (
    "dev/reports/push/latest_check_router_preflight.json"
)
PREFLIGHT_FAILURE_SUMMARY_LIMIT = 20


def annotate_preflight_step(
    preflight_step: dict[str, Any] | None,
    *,
    report_path: Path,
) -> None:
    """Attach the bounded check-router report pointer and failure summary."""
    if not preflight_step:
        return
    preflight_step["report_path"] = PUSH_PREFLIGHT_CHECK_ROUTER_REPORT
    if int(preflight_step.get("returncode") or 0) == 0:
        return
    summary = _load_preflight_failure_summary(report_path)
    if summary:
        preflight_step["failure_output"] = summary


def _load_preflight_failure_summary(report_path: Path) -> str:
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return ""
    if not isinstance(payload, dict):
        return ""
    failed = [
        _preflight_failure_line(step)
        for step in _preflight_report_steps(payload)
        if int(step.get("returncode") or 0) != 0
    ]
    failed = [line for line in failed if line]
    if not failed and not bool(payload.get("ok")):
        failed.append("FAIL check-router -- see preflight report artifact")
    if len(failed) > PREFLIGHT_FAILURE_SUMMARY_LIMIT:
        remaining = len(failed) - PREFLIGHT_FAILURE_SUMMARY_LIMIT
        failed = [
            *failed[:PREFLIGHT_FAILURE_SUMMARY_LIMIT],
            f"FAIL additional-checks -- {remaining} more failure(s) in report artifact",
        ]
    return "\n".join(failed)


def _preflight_report_steps(payload: dict[str, Any]) -> list[dict[str, Any]]:
    steps = payload.get("steps")
    if not isinstance(steps, list):
        return []
    return [step for step in steps if isinstance(step, dict)]


def _preflight_failure_line(step: dict[str, Any]) -> str:
    name = str(step.get("source") or step.get("name") or "check-router").strip()
    detail = _first_nonblank_line(
        step.get("failure_output"),
        step.get("error"),
        step.get("router_command"),
    )
    return f"FAIL {name} -- {detail}" if detail else f"FAIL {name}"


def _first_nonblank_line(*values: object) -> str:
    for value in values:
        for line in str(value or "").splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
    return ""


__all__ = [
    "PUSH_PREFLIGHT_CHECK_ROUTER_REPORT",
    "annotate_preflight_step",
]
