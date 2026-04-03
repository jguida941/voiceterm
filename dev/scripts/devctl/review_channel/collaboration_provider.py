"""Provider-resolution helpers shared by review-channel runtime builders."""

from __future__ import annotations

from ..runtime.review_state_models import CollaborationSessionState


def collaboration_provider(
    collaboration: CollaborationSessionState | None,
    *,
    role_id: str,
    default: str,
) -> str:
    """Return the provider assigned to one collaboration role."""
    if collaboration is None:
        return default
    for assignment in collaboration.role_assignments:
        if assignment.role_id == role_id and assignment.provider:
            return assignment.provider
    return default
