"""Session-aware packet actor/target roster helpers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..runtime.role_profile import build_default_tandem_profile
from .session_probe import load_conductor_sessions


def default_packet_agent_ids() -> tuple[str, ...]:
    """Return the compatibility packet actor roster from the default tandem profile."""
    ordered: list[str] = []
    profile = build_default_tandem_profile()
    _append_agent_id(ordered, profile.reviewer.provider)
    for implementer in profile.implementers:
        _append_agent_id(ordered, implementer.provider)
    _append_agent_id(ordered, "cursor")
    _append_agent_id(ordered, profile.operator.provider)
    _append_agent_id(ordered, "system")
    return tuple(ordered)


def packet_agent_ids_from_review_state(
    review_state: Mapping[str, object] | None,
) -> tuple[str, ...]:
    """Return packet actor/target ids from the typed collaboration/runtime contract."""
    ordered = list(default_packet_agent_ids())
    if not isinstance(review_state, Mapping):
        return tuple(ordered)
    _append_registry_agent_ids(ordered, review_state.get("registry"))
    _append_collaboration_agent_ids(ordered, review_state.get("collaboration"))
    return tuple(ordered)


def packet_agent_ids_from_session_output(
    session_output_root: Path | None,
) -> tuple[str, ...]:
    """Return packet ids from repo-owned conductor session metadata alone."""
    ordered = list(default_packet_agent_ids())
    if session_output_root is None:
        return tuple(ordered)
    for record in load_conductor_sessions(session_output_root=session_output_root):
        _append_agent_id(ordered, record.provider)
        for lane in record.planned_lanes:
            if not isinstance(lane, Mapping):
                continue
            _append_agent_id(ordered, lane.get("agent_id"))
            _append_agent_id(ordered, lane.get("provider"))
    return tuple(ordered)


def _append_registry_agent_ids(
    ordered: list[str],
    registry: object,
) -> None:
    if not isinstance(registry, Mapping):
        return
    for row in registry.get("agents") or ():
        if not isinstance(row, Mapping):
            continue
        _append_agent_id(ordered, row.get("agent_id"))
        _append_agent_id(ordered, row.get("provider"))


def _append_collaboration_agent_ids(
    ordered: list[str],
    collaboration: object,
) -> None:
    if not isinstance(collaboration, Mapping):
        return
    for row in collaboration.get("role_assignments") or ():
        if not isinstance(row, Mapping):
            continue
        _append_agent_id(ordered, row.get("agent_id"))
        _append_agent_id(ordered, row.get("provider"))
    for row in collaboration.get("participants") or ():
        if not isinstance(row, Mapping):
            continue
        _append_agent_id(ordered, row.get("agent_id"))
        _append_agent_id(ordered, row.get("provider"))
    for row in collaboration.get("delegated_work") or ():
        if not isinstance(row, Mapping):
            continue
        _append_agent_id(ordered, row.get("agent_id"))
        _append_agent_id(ordered, row.get("provider"))


def _append_agent_id(ordered: list[str], value: object) -> None:
    text = str(value or "").strip()
    if text and text not in ordered:
        ordered.append(text)
