"""Digest helpers for Operator Console snapshot redraw decisions."""

from __future__ import annotations

import hashlib

from ..core.models import AgentLaneData, OperatorConsoleSnapshot


def snapshot_digest(snapshot: OperatorConsoleSnapshot) -> str:
    """Return a digest that changes when visible snapshot state changes."""
    lane_signatures: list[str] = []
    for lane in _present_lanes(snapshot):
        lane_signatures.append(
            "|".join(
                [
                    lane.provider_name,
                    lane.lane_title,
                    lane.role_label,
                    lane.status_hint,
                    lane.state_label,
                    lane.risk_label or "",
                    lane.confidence_label or "",
                    ";".join(f"{key}={value}" for key, value in lane.rows),
                    lane.raw_text,
                ]
            )
        )
    payload = "\n".join(
        [
            snapshot.codex_panel_text,
            snapshot.claude_panel_text,
            snapshot.operator_panel_text,
            snapshot.raw_bridge_text,
            snapshot.last_codex_poll or "",
            snapshot.last_worktree_hash or "",
            snapshot.review_state_path or "",
            "|".join(snapshot.warnings),
            "|".join(approval.packet_id for approval in snapshot.pending_approvals),
            "|".join(lane_signatures),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _present_lanes(snapshot: OperatorConsoleSnapshot) -> list[AgentLaneData]:
    return [
        lane
        for lane in (
            snapshot.codex_lane,
            snapshot.operator_lane,
            snapshot.claude_lane,
            snapshot.cursor_lane,
        )
        if lane is not None
    ]
