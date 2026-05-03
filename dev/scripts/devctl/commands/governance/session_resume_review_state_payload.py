"""Resolve the typed review-state payload used by session-resume."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...runtime.review_state_locator import load_current_review_state
from ...runtime.review_state_parser import review_state_from_payload

if TYPE_CHECKING:
    from ...runtime.project_governance import ProjectGovernance
    from ...runtime.review_state_models import ReviewState


def resolve_typed_review_state_payload(
    *,
    repo_root: Path,
    governance: "ProjectGovernance | None",
    review_state: "ReviewState | None",
    sources: dict[str, Any],
) -> tuple["ReviewState | None", dict[str, object]]:
    review_state_payload = (
        sources.get("review_state")
        if isinstance(sources.get("review_state"), dict)
        else {}
    )
    typed_review_state = review_state or review_state_from_payload(review_state_payload)
    if review_state is not None or _review_state_has_packets(typed_review_state):
        return typed_review_state, review_state_payload
    loaded_review_state = load_current_review_state(
        repo_root,
        governance=governance,
        prefer_cached_projection=True,
    )
    if not _review_state_has_packets(loaded_review_state):
        return typed_review_state, review_state_payload
    payload = _review_state_payload_dict(loaded_review_state)
    return loaded_review_state, payload or review_state_payload


def _review_state_has_packets(review_state: object | None) -> bool:
    if review_state is None:
        return False
    packets = getattr(review_state, "packets", None)
    if packets:
        return True
    payload = _review_state_payload_dict(review_state)
    return bool(payload.get("packets"))


def _review_state_payload_dict(review_state: object | None) -> dict[str, object]:
    to_dict = getattr(review_state, "to_dict", None)
    if not callable(to_dict):
        return {}
    payload = to_dict()
    return payload if isinstance(payload, dict) else {}
