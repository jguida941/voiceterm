"""Helpers that keep event projection repairs out of the core projection file."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .core import DEFAULT_BRIDGE_REL
from .current_session_projection import (
    build_bridge_current_session,
    build_event_current_session,
)
from .handoff import extract_bridge_snapshot


@dataclass(frozen=True, slots=True)
class EventProjectionContext:
    """Stable inputs shared across event-backed projection passes."""

    repo_root: Path
    review_channel_path: Path
    projections_root: Path
    artifact_root: Path | None = None
    push_enforcement: dict[str, object] | None = None
    prior_review_state: Mapping[str, object] | None = None


def resolve_current_session(
    review_state: dict[str, object],
    *,
    context: EventProjectionContext,
    bridge_liveness: dict[str, object],
):
    """Prefer typed event state, but recover bridge instructions when focus is blank."""
    current_session = build_event_current_session(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
        prior_review_state=context.prior_review_state,
    )
    if current_session.current_instruction.strip() not in {"", "(missing)"}:
        return current_session
    if _event_session_has_packet_attention(current_session):
        return current_session
    try:
        bridge_snapshot = extract_bridge_snapshot(
            (context.repo_root / DEFAULT_BRIDGE_REL).read_text(encoding="utf-8")
        )
    except OSError:
        return current_session
    bridge_session = build_bridge_current_session(
        bridge_snapshot,
        bridge_liveness,
        prior_review_state=context.prior_review_state,
    )
    if bridge_session.current_instruction.strip() not in {"", "(missing)"}:
        return bridge_session
    return current_session


def _event_session_has_packet_attention(current_session) -> bool:
    open_findings = str(getattr(current_session, "open_findings", "") or "").strip().lower()
    return open_findings not in {"", "none"}
