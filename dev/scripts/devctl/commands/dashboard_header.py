"""Top-level header projection for DashboardSnapshot JSON consumers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def _coerce_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


@dataclass(frozen=True, slots=True)
class DashboardHeaderProjection:
    """Compact top-level dashboard header for JSON consumers."""

    status: str
    owner: str
    next_action: str
    top_blocker: str
    pending_count: int
    pending_findings_count: int
    next_actor: str
    next_command: str
    pending_action_requests: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def project_dashboard_header_fields(
    *,
    summary: dict[str, Any],
    now: dict[str, Any],
    coordination: dict[str, Any],
    control_plane: Any = None,
) -> dict[str, Any]:
    """Expose a compact top-level dashboard header for JSON consumers."""
    pending_count = max(
        _coerce_int(coordination.get("pending_count")),
        _coerce_int(coordination.get("pending_packets")),
        _coerce_int(getattr(control_plane, "pending_action_requests", 0)),
    )
    top_blocker = (
        str(summary.get("primary_blocker") or "").strip()
        or str(now.get("top_blocker") or "none").strip()
        or "none"
    )
    next_command = str(
        getattr(control_plane, "next_command", "")
        or summary.get("next_command_hint")
        or ""
    ).strip()
    return DashboardHeaderProjection(
        status=str(summary.get("overall_state") or "unknown"),
        owner=str(now.get("owner") or "n/a"),
        next_action=str(now.get("next_action") or "n/a"),
        top_blocker=top_blocker,
        pending_count=pending_count,
        pending_findings_count=_coerce_int(coordination.get("pending_findings_count")),
        next_actor=str(summary.get("next_actor") or "n/a"),
        next_command=next_command,
        pending_action_requests=_coerce_int(
            getattr(control_plane, "pending_action_requests", 0)
        ),
    ).to_dict()
