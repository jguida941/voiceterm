"""Collaboration timeline synthesis for the Operator Console workflow view."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from dev.scripts.devctl.repo_packs import VOICETERM_PATH_CONFIG

from ..state.core.models import AgentLaneData, OperatorConsoleSnapshot
from ..state.core.value_coercion import safe_text

_ROLLOVER_ROOT_REL = Path(VOICETERM_PATH_CONFIG.rollover_root_rel)
_MAX_ROLLOVER_EVENTS = 3
_EVENT_DETAIL_LIMIT = 3


@dataclass(frozen=True)
class TimelineEvent:
    """One display-ready event in the operator timeline."""

    actor: str
    status_level: str
    title: str
    detail: str
    source: str


def build_timeline_from_snapshot(
    snapshot: OperatorConsoleSnapshot,
    *,
    repo_root: Path | None = None,
) -> tuple[TimelineEvent, ...]:
    """Build newest-first timeline events from snapshot and rollover artifacts."""
    events: list[TimelineEvent] = []
    _append_lane_event(events, lane=snapshot.codex_lane)
    _append_lane_event(events, lane=snapshot.claude_lane)
    _append_lane_event(events, lane=snapshot.operator_lane)
    _append_approval_event(events, approvals=len(snapshot.pending_approvals))
    _append_warning_events(events, snapshot.warnings)
    _append_bridge_marker_events(
        events,
        last_codex_poll=snapshot.last_codex_poll,
        last_worktree_hash=snapshot.last_worktree_hash,
    )
    if repo_root is not None:
        events.extend(_rollover_events(repo_root))
    return tuple(events)


def _append_lane_event(events: list[TimelineEvent], *, lane: AgentLaneData | None) -> None:
    if lane is None:
        return
    detail_parts: list[str] = []
    for key, value in lane.rows:
        cleaned = " ".join(value.split())
        if not cleaned or cleaned in {"(missing)", "(unknown)", "(none)"}:
            continue
        if key == "Approvals" and cleaned == "0":
            continue
        detail_parts.append(f"{key}: {cleaned}")
        if len(detail_parts) >= _EVENT_DETAIL_LIMIT:
            break
    detail = " | ".join(detail_parts) or "No additional lane details."
    events.append(
        TimelineEvent(
            actor=lane.provider_name.lower(),
            status_level=lane.status_hint,
            title=f"{lane.provider_name} lane: {lane.state_label}",
            detail=detail,
            source="bridge snapshot",
        )
    )


def _append_approval_event(events: list[TimelineEvent], *, approvals: int) -> None:
    if approvals <= 0:
        events.append(
            TimelineEvent(
                actor="operator",
                status_level="active",
                title="Approval queue is clear",
                detail="No pending operator approvals.",
                source="review state",
            )
        )
        return
    events.append(
        TimelineEvent(
            actor="operator",
            status_level="warning",
            title=f"Pending approvals: {approvals}",
            detail="Operator action is required before the next gated transition.",
            source="review state",
        )
    )


def _append_warning_events(events: list[TimelineEvent], warnings: tuple[str, ...]) -> None:
    for warning in warnings[:_EVENT_DETAIL_LIMIT]:
        events.append(
            TimelineEvent(
                actor="system",
                status_level="warning",
                title="Snapshot warning",
                detail=" ".join(warning.split()),
                source="snapshot diagnostics",
            )
        )


def _append_bridge_marker_events(
    events: list[TimelineEvent],
    *,
    last_codex_poll: str | None,
    last_worktree_hash: str | None,
) -> None:
    if last_codex_poll:
        events.append(
            TimelineEvent(
                actor="codex",
                status_level="active",
                title="Reviewer heartbeat observed",
                detail=f"Last Codex poll: {last_codex_poll}",
                source="bridge metadata",
            )
        )
    if last_worktree_hash:
        events.append(
            TimelineEvent(
                actor="system",
                status_level="idle",
                title="Reviewed worktree anchor",
                detail=f"Last non-audit worktree hash: {last_worktree_hash}",
                source="bridge metadata",
            )
        )


def _rollover_events(repo_root: Path) -> tuple[TimelineEvent, ...]:
    rollover_root = repo_root / _ROLLOVER_ROOT_REL
    if not rollover_root.exists():
        return ()
    events: list[TimelineEvent] = []
    directories = sorted(
        (child for child in rollover_root.iterdir() if child.is_dir()),
        reverse=True,
    )
    for directory in directories[:_MAX_ROLLOVER_EVENTS]:
        payload = _load_handoff_json(directory / "handoff.json")
        if payload is None:
            continue
        resume_state = payload.get("resume_state")
        if not isinstance(resume_state, dict):
            continue
        next_action = safe_text(resume_state.get("next_action")) or "(missing)"
        current_step = safe_text(resume_state.get("current_atomic_step")) or "(missing)"
        reviewed_hash = safe_text(resume_state.get("reviewed_worktree_hash")) or "(missing)"
        created_at = safe_text(payload.get("created_at")) or directory.name
        events.append(
            TimelineEvent(
                actor="system",
                status_level="warning",
                title=f"Rollover handoff: {created_at}",
                detail=(
                    f"next_action: {next_action} | "
                    f"atomic_step: {current_step} | "
                    f"worktree: {reviewed_hash}"
                ),
                source="rollover handoff",
            )
        )
    return tuple(events)


def _load_handoff_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload
