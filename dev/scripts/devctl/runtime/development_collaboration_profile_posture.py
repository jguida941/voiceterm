"""Session posture readers for collaboration profiles."""

from __future__ import annotations

from collections.abc import Mapping

from .review_state_collaboration_models import CollaborationSessionState
from .session_posture import SessionPosture, session_posture_from_mapping


def session_posture_from_review_state(
    review_state: Mapping[str, object],
) -> SessionPosture | None:
    runtime = mapping(review_state.get("reviewer_runtime"))
    posture = session_posture_from_mapping(
        runtime.get("session_posture") or review_state.get("session_posture")
    )
    return posture if session_posture_has_evidence(posture) else None


def session_posture_from_collaboration(
    state: CollaborationSessionState | None,
) -> SessionPosture | None:
    if state is None:
        return None
    posture = state.session_posture
    return posture if session_posture_has_evidence(posture) else None


def session_posture_has_evidence(posture: SessionPosture | None) -> bool:
    return posture is not None and (
        bool(posture.actors) or posture.interaction_mode != "unresolved"
    )


def mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
