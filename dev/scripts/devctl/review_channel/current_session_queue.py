"""Queue-derived current-session instruction helpers."""

from __future__ import annotations

from collections.abc import Mapping

from .collaboration_provider import (
    coding_provider_from_review_state,
    reviewer_provider_from_review_state,
)
from .status_projection_helpers import clean_section

_ROLE_ALIAS_PAIRS = (
    ("coder", "implementer"),
    ("coding", "implementer"),
    ("implementation", "implementer"),
    ("implementer", "implementer"),
    ("review", "reviewer"),
    ("reviewer", "reviewer"),
    ("dashboard", "dashboard"),
    ("observer", "dashboard"),
    ("operator", "operator"),
)
_ROLE_ALIASES = dict(_ROLE_ALIAS_PAIRS)


def queue_current_instruction(review_state: Mapping[str, object]) -> str:
    """Return the queue-selected instruction after role/target filtering."""
    queue = _mapping(review_state.get("queue"))
    source = _mapping(queue.get("derived_next_instruction_source"))
    derived = str(queue.get("derived_next_instruction") or "").strip()
    if not derived:
        return ""
    target = str(source.get("to_agent") or "").strip().lower()
    target_role = _normalize_role(source.get("target_role"))
    if _source_is_action_request(source):
        return derived if _source_targets_current_session(
            target=target,
            target_role=target_role,
            coding_provider=coding_provider_from_review_state(review_state),
            reviewer_provider=reviewer_provider_from_review_state(review_state),
        ) else ""
    if (
        target
        and target != coding_provider_from_review_state(review_state)
        and target_role != "dashboard"
    ):
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
    if current_instruction and not _same_instruction(
        current_instruction,
        derived,
    ):
        return False
    if not _source_is_action_request(source):
        return False
    return _source_targets_current_session(
        target=str(source.get("to_agent") or "").strip().lower(),
        target_role=_normalize_role(source.get("target_role")),
        coding_provider=coding_provider_from_review_state(review_state),
        reviewer_provider=reviewer_provider_from_review_state(review_state),
    )


def queue_instruction_is_dashboard_route(
    review_state: Mapping[str, object] | None,
    *,
    current_instruction: str = "",
) -> bool:
    """Return true when the selected queue instruction targets a dashboard lane."""
    if not isinstance(review_state, Mapping):
        return False
    queue = _mapping(review_state.get("queue"))
    source = _mapping(queue.get("derived_next_instruction_source"))
    derived = str(queue.get("derived_next_instruction") or "").strip()
    if not derived:
        return False
    if current_instruction and not _same_instruction(
        current_instruction,
        derived,
    ):
        return False
    return _normalize_role(source.get("target_role")) == "dashboard"


def queue_instruction_preserves_packet_truth_clear(
    review_state: Mapping[str, object] | None,
    *,
    current_instruction: str = "",
) -> bool:
    return queue_instruction_is_priority_action_request(
        review_state,
        current_instruction=current_instruction,
    ) or queue_instruction_is_dashboard_route(
        review_state,
        current_instruction=current_instruction,
    )


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


def _source_targets_current_session(
    *,
    target: str,
    target_role: str,
    coding_provider: str,
    reviewer_provider: str,
) -> bool:
    if target_role == "dashboard":
        return True
    if target_role == "reviewer":
        return False
    if target_role == "implementer":
        return True
    if target:
        return target != reviewer_provider and target in {
            coding_provider,
            "claude",
            "cursor",
        }
    return True


def _normalize_role(value: object) -> str:
    role = str(value or "").strip()
    if not role:
        return ""
    key = role.lower().replace("-", "_").replace(" ", "_")
    return _ROLE_ALIASES.get(key, key)


def _same_instruction(left: str, right: str) -> bool:
    left_clean = clean_section(left)
    right_clean = clean_section(right)
    if left_clean == right_clean:
        return True
    return _without_markdown_bullets(left_clean) == _without_markdown_bullets(
        right_clean
    )


def _without_markdown_bullets(text: str) -> str:
    lines = []
    for line in clean_section(text).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        lines.append(stripped)
    return "\n".join(lines)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
