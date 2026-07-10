"""Violation projection helpers for governed push reports."""

from __future__ import annotations

import re
from typing import Any

from ...runtime.check_result_models import build_check_result


def _extract_preflight_violations(
    preflight_step: dict[str, Any] | None,
    timestamp: str,
) -> list[dict[str, Any]]:
    """Build typed ViolationRecord dicts from the preflight step result."""
    if not preflight_step:
        return []
    if preflight_step.get("returncode", 0) == 0:
        return []
    failure_output = str(preflight_step.get("failure_output") or "")
    per_check = _parse_per_check_failures(failure_output)
    if per_check:
        steps = _per_check_to_steps(per_check, preflight_step)
        result = build_check_result(
            steps=steps,
            timestamp=timestamp,
            command="push-preflight",
        )
        return [v.to_dict() for v in result.violations]
    step = dict(preflight_step)
    if "name" not in step:
        step["name"] = "push-preflight"
    result = build_check_result(
        steps=[step],
        timestamp=timestamp,
        command="push-preflight",
    )
    return [v.to_dict() for v in result.violations]


_CHECK_LINE_RE = re.compile(r"^\s*(PASS|FAIL|SKIP)\s+(\S+)(?:\s+--\s+(.*))?$")


def _parse_per_check_failures(
    failure_output: str,
) -> list[dict[str, str]]:
    """Extract individual failed check-router entries."""
    results: list[dict[str, str]] = []
    for line in failure_output.splitlines():
        match = _CHECK_LINE_RE.match(line)
        if not match:
            continue
        status, name, summary = match.group(1), match.group(2), match.group(3) or ""
        if status == "FAIL":
            results.append(dict(name=name, summary=summary.strip()))
    return results


def _per_check_to_steps(
    per_check: list[dict[str, str]],
    preflight_step: dict[str, Any],
) -> list[dict[str, Any]]:
    """Convert parsed per-check failures into check-result step dicts."""
    rc = preflight_step.get("returncode", 1)
    return [
        dict(
            name=entry["name"],
            cmd=preflight_step.get("cmd", []),
            returncode=rc,
            failure_output=entry["summary"],
            skipped=False,
        )
        for entry in per_check
    ]
