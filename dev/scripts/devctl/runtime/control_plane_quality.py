"""Quality-gate resolution for the control-plane read model."""

from __future__ import annotations

from typing import Any

from .value_coercion import coerce_string


def resolve_quality(
    push_report: dict[str, Any] | None,
    *,
    current_head: str = "",
) -> dict[str, Any]:
    """Derive guard-ok and check details from the current-head push report."""
    if push_report is None:
        return {"last_guard_ok": True, "check_details": ()}
    if _push_report_is_stale(push_report, current_head=current_head):
        return {"last_guard_ok": True, "check_details": ()}
    preflight = push_report.get("preflight_step", {}) or {}
    rc = preflight.get("returncode", -1)
    guard_ok = rc == 0 if isinstance(rc, int) else True
    details: list[dict[str, str]] = []
    if not guard_ok:
        violations = push_report.get("violations")
        if isinstance(violations, list):
            for violation in violations[:10]:
                if isinstance(violation, dict):
                    details.append({
                        "check": (
                            coerce_string(violation.get("step_name"))
                            or "unknown"
                        ),
                        "status": "FAIL",
                        "violation": coerce_string(violation.get("summary")),
                    })
    return {"last_guard_ok": guard_ok, "check_details": tuple(details)}


def _push_report_is_stale(
    push_report: dict[str, Any],
    *,
    current_head: str,
) -> bool:
    report_head = coerce_string(push_report.get("head_commit"))
    current = coerce_string(current_head)
    if not report_head or not current:
        return False
    return not (
        report_head == current
        or report_head.startswith(current)
        or current.startswith(report_head)
    )
