"""Runtime-count extraction for observed startup control topology."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from .control_topology_bridge_counts import (
    active_conductor_count,
    boolish,
    bridge_role_counts,
)


def startup_runtime_counts(
    review_state: object | None,
    *,
    bridge_liveness: Mapping[str, object],
) -> dict[str, int]:
    """Return startup-scoped runtime counts without importing review-channel CLI code."""
    if review_state is None:
        return {}
    collaboration = _object_mapping(getattr(review_state, "collaboration", None))
    participants = _rows(collaboration.get("participants"))
    live_participants = [row for row in participants if boolish(row.get("live"))]
    role_counts = bridge_role_counts(bridge_liveness)
    if participants:
        live_reviewer_total = sum(
            1 for row in live_participants if _text(row.get("role")) == "reviewer"
        )
        live_implementer_total = sum(
            1 for row in live_participants if _text(row.get("role")) == "implementer"
        )
        live_participant_total = len(live_participants)
    else:
        live_reviewer_total = role_counts["live_reviewer_total"]
        live_implementer_total = role_counts["live_implementer_total"]
        live_participant_total = role_counts["live_participants_total"]
    counts: dict[str, int] = {}
    counts["participants_total"] = len(participants)
    counts["live_participants_total"] = live_participant_total
    counts["live_reviewer_total"] = live_reviewer_total
    counts["live_implementer_total"] = live_implementer_total
    counts["active_conductor_count"] = active_conductor_count(
        bridge=bridge_liveness,
        live_participants=live_participants,
    )
    counts["live_participant_count"] = live_participant_total
    counts["live_reviewer_count"] = live_reviewer_total
    counts["live_implementer_count"] = live_implementer_total
    return counts


def startup_bridge_liveness(review_state: object | None) -> dict[str, object]:
    """Return bridge liveness from the typed startup review-state object."""
    if review_state is None:
        return {}
    return dict(_object_mapping(getattr(review_state, "bridge", None)))


def _object_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    try:
        mapped = asdict(value)
    except TypeError:
        return {}
    return mapped if isinstance(mapped, Mapping) else {}


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _text(value: object) -> str:
    return str(value or "").strip().lower()
