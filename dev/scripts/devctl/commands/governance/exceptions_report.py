"""Report helpers for governed exception commands."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ...time_utils import utc_timestamp


def base_report(action: str, **paths: Path) -> dict[str, object]:
    payload: dict[str, object] = {
        "command": "exceptions",
        "action": action,
        "ok": True,
        "timestamp": utc_timestamp(),
    }
    for key, path in paths.items():
        payload[key] = str(path)
    return payload


def render_markdown(report: Mapping[str, object]) -> str:
    action = report.get("action") or ""
    lines = ["# devctl exceptions", "", f"- action: `{action}`"]
    lines.append(f"- ok: `{str(report.get('ok', False)).lower()}`")
    if report.get("store_path"):
        lines.append(f"- store_path: `{report.get('store_path')}`")
    if report.get("validate_path"):
        lines.append(f"- validate_path: `{report.get('validate_path')}`")
    if action == "pending":
        lines.append(f"- pending_count: `{report.get('pending_count', 0)}`")
        _append_pending_rows(lines, report.get("lifecycles"))
    else:
        lines.append(f"- validated_count: `{report.get('validated_count', 0)}`")
    errors = report.get("errors")
    if isinstance(errors, list) and errors:
        lines.extend(["", "## Errors"])
        lines.extend(f"- {error}" for error in errors)
    return "\n".join(lines) + "\n"


def _append_pending_rows(lines: list[str], lifecycles: object) -> None:
    if not isinstance(lifecycles, list) or not lifecycles:
        return
    lines.extend(["", "## Pending"])
    for row in lifecycles:
        if isinstance(row, Mapping):
            lines.append(
                f"- `{row.get('lifecycle_id', '')}` "
                f"status=`{row.get('status', '')}`"
            )


__all__ = ["base_report", "render_markdown"]
