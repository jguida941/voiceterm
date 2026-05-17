"""Report projection helpers for VCS ActionResult payloads."""

from __future__ import annotations


def action_result_report_fields(result: object) -> dict[str, object]:
    """Project ActionResult-like objects into the commit report shape."""
    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
    else:
        payload = {
            "action_id": str(getattr(result, "action_id", "") or ""),
            "ok": bool(getattr(result, "ok", False)),
            "status": str(getattr(result, "status", "") or ""),
            "reason": str(getattr(result, "reason", "") or ""),
            "warnings": list(getattr(result, "warnings", ()) or ()),
        }
    reason_chain = tuple(getattr(result, "reason_chain", ()) or ())
    errors = tuple(getattr(result, "errors", ()) or ())
    return {
        "action_result": payload,
        "reason_chain": list(reason_chain),
        "remediation": str(getattr(result, "remediation", "") or ""),
        "auto_executable": bool(getattr(result, "auto_executable", False)),
        "errors": [dict(item) for item in errors if isinstance(item, dict)],
    }
