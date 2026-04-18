"""Runtime-count extraction for observed startup control topology."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from .control_topology_bridge_counts import (
    active_conductor_count,
    boolish,
    bridge_role_counts,
)
from .runtime_count_roles import participant_role_provider_ids
from .runtime_count_roles import provider_has_only_non_tandem_presence


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
    role_assignments = _rows(collaboration.get("role_assignments"))
    live_participants = [row for row in participants if boolish(row.get("live"))]
    role_counts = bridge_role_counts(bridge_liveness)
    typed_role_totals = _live_role_totals(
        role_assignments=role_assignments,
        live_participants=live_participants,
    )
    if participants:
        live_reviewer_total = typed_role_totals["live_reviewer_total"]
        live_implementer_total = typed_role_totals["live_implementer_total"]
        live_participant_total = len(live_participants)
    else:
        live_reviewer_total = typed_role_totals["live_reviewer_total"]
        live_implementer_total = typed_role_totals["live_implementer_total"]
        if not typed_role_totals["derived_from_typed_roles"]:
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


def _live_role_totals(
    *,
    role_assignments: list[Mapping[str, object]],
    live_participants: list[Mapping[str, object]],
) -> dict[str, int | bool]:
    reviewer_ids: list[str] = []
    implementer_ids: list[str] = []
    for row in role_assignments:
        if not boolish(row.get("live")):
            continue
        provider = _text(row.get("provider") or row.get("agent_id"))
        if not provider:
            continue
        if provider_has_only_non_tandem_presence(
            live_participants,
            provider,
            text_fn=_text,
        ):
            continue
        role_id = _text(row.get("role_id"))
        if role_id == "review_agent" and provider not in reviewer_ids:
            reviewer_ids.append(provider)
        elif role_id == "coding_agent" and provider not in implementer_ids:
            implementer_ids.append(provider)
    if not reviewer_ids:
        reviewer_ids.extend(
            participant_role_provider_ids(
                live_participants,
                "reviewer",
                text_fn=_text,
            )
        )
    if not implementer_ids:
        implementer_ids.extend(
            participant_role_provider_ids(
                live_participants,
                "implementer",
                text_fn=_text,
            )
        )
    return {
        "live_reviewer_total": len(reviewer_ids),
        "live_implementer_total": len(implementer_ids),
        "derived_from_typed_roles": bool(role_assignments),
    }
def _text(value: object) -> str:
    return str(value or "").strip().lower()
