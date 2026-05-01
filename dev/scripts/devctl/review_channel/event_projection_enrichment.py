"""Helpers that keep event projection repairs out of the core projection file."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .current_session_projection import (
    build_event_current_session,
)


@dataclass(frozen=True, slots=True)
class EventProjectionContext:
    """Stable inputs shared across event-backed projection passes."""

    repo_root: Path
    review_channel_path: Path
    projections_root: Path
    artifact_root: Path | None = None
    push_enforcement: dict[str, object] | None = None
    prior_review_state: Mapping[str, object] | None = None
    # Per rev_pkt_2546/2550 (Plan 4.1 Scope 1): the reduced event log must be
    # threaded into projection passes so reviewer-runtime / packet-attention /
    # runtime-clock derivations can consume the typed event source instead of
    # rebuilding from bridge-markdown projections.
    events: tuple[dict[str, object], ...] = ()


def resolve_current_session(
    review_state: dict[str, object],
    *,
    context: EventProjectionContext,
    bridge_liveness: dict[str, object],
):
    """Resolve current-session authority from typed event state only."""
    return build_event_current_session(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
        prior_review_state=context.prior_review_state,
    )
