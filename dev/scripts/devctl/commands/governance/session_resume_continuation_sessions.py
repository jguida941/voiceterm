"""Collaboration-session lookup helpers for session-resume continuation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...runtime.review_state_models import ReviewState


def session_ref_for_agent(
    *,
    typed_review_state: "ReviewState | None",
    agent_id: str,
    role: str,
) -> str:
    if typed_review_state is None:
        return ""
    collaboration = getattr(typed_review_state, "collaboration", None)
    participants = getattr(collaboration, "participants", ()) or ()
    agent_key = str(agent_id or "").strip().lower()
    role_key = str(role or "").strip().lower()
    for participant in participants:
        if not _participant_matches(participant, agent_key=agent_key, role_key=role_key):
            continue
        return (
            _participant_text(participant, "metadata_path")
            or _participant_text(participant, "log_path")
            or _participant_text(participant, "session_name")
        )
    return ""


def _participant_matches(
    participant: object,
    *,
    agent_key: str,
    role_key: str,
) -> bool:
    values = {
        _participant_text(participant, "agent_id").lower(),
        _participant_text(participant, "provider").lower(),
        _participant_text(participant, "role").lower(),
    }
    return bool((agent_key and agent_key in values) or (role_key and role_key in values))


def _participant_text(participant: object, attr: str) -> str:
    return str(getattr(participant, attr, "") or "").strip()


__all__ = ["session_ref_for_agent"]
