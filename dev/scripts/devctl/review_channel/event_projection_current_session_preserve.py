"""Preserve current-session context across event projection refreshes."""

from __future__ import annotations

from collections.abc import Mapping

from .current_session_support import compute_implementer_state_hash


def preserve_current_session_context_from_prior(
    review_state: dict[str, object],
    prior: Mapping[str, object],
) -> tuple[dict[str, object], bool]:
    """Preserve typed current-session context through the approved writer path."""
    prior_session = prior.get("current_session")
    current_session = review_state.get("current_session")
    if not isinstance(prior_session, Mapping) or not isinstance(
        current_session, Mapping
    ):
        return review_state, False
    current = dict(current_session)
    for field in _PRESERVED_CURRENT_SESSION_FIELDS:
        prior_value = str(prior_session.get(field) or "").strip()
        if not prior_value or prior_value == "(missing)":
            continue
        if not _current_session_context_missing(current.get(field), field):
            continue
        current[field] = prior_value
    if current == current_session:
        return review_state, False
    current["implementer_state_hash"] = compute_implementer_state_hash(
        implementer_status=str(current.get("implementer_status") or ""),
        implementer_ack=str(current.get("implementer_ack") or ""),
    )
    updated = dict(review_state)
    updated.update({"current_session": current})
    return updated, True


def _current_session_context_missing(value: object, field: str) -> bool:
    text = str(value or "").strip()
    normalized = text.lower().lstrip("-").strip().rstrip(".")
    if field == "open_findings":
        return normalized in {"", "none"}
    if field == "last_reviewed_scope":
        return normalized in {"", "missing"}
    return normalized in _MISSING_STATUS_VALUES


_PRESERVED_CURRENT_SESSION_FIELDS = (
    "implementer_status",
    "open_findings",
    "last_reviewed_scope",
)

_MISSING_STATUS_VALUES = (
    "",
    "inactive",
    "missing",
    "status unavailable",
    "waiting_for_ack",
)


__all__ = ["preserve_current_session_context_from_prior"]
