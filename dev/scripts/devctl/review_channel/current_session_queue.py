"""Queue-derived current-session instruction helpers."""

from __future__ import annotations

from collections.abc import Mapping

from .collaboration_provider import coding_provider_from_review_state
from .status_projection_helpers import clean_section


def queue_current_instruction(review_state: Mapping[str, object]) -> str:
    """Return the queue-selected instruction after role/target filtering."""
    queue = _mapping(review_state.get("queue"))
    source = _mapping(queue.get("derived_next_instruction_source"))
    derived = str(queue.get("derived_next_instruction") or "").strip()
    if not derived:
        return ""
    if _source_is_action_request(source):
        return derived
    target = str(source.get("to_agent") or "").strip().lower()
    if target and target != coding_provider_from_review_state(review_state):
        return ""
    return derived


def queue_instruction_is_priority_action_request(
    review_state: Mapping[str, object] | None,
    *,
    current_instruction: str = "",
) -> bool:
    """Return true when queue priority is an action_request instruction."""
    if not isinstance(review_state, Mapping):
        return False
    queue = _mapping(review_state.get("queue"))
    source = _mapping(queue.get("derived_next_instruction_source"))
    derived = str(queue.get("derived_next_instruction") or "").strip()
    if not derived:
        return False
    if current_instruction and clean_section(current_instruction) != clean_section(
        derived
    ):
        return False
    return _source_is_action_request(source)


def _source_is_action_request(source: Mapping[str, object]) -> bool:
    source_kind = str(
        source.get("packet_class")
        or source.get("kind")
        or source.get("selected_source_kind")
        or ""
    ).strip()
    if source_kind == "action_request":
        return True
    return (
        str(source.get("selection_policy") or "").strip()
        == "action_request_priority"
    )


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
