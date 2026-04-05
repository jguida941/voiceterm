"""Provider-resolution helpers shared by review-channel runtime builders."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_state_models import CollaborationSessionState


def collaboration_provider(
    collaboration: CollaborationSessionState | Mapping[str, object] | None,
    *,
    role_id: str,
    default: str,
) -> str:
    """Return the provider assigned to one collaboration role."""
    if collaboration is None:
        return default
    assignments = (
        collaboration.get("role_assignments")
        if isinstance(collaboration, Mapping)
        else collaboration.role_assignments
    )
    for assignment in assignments or ():
        if isinstance(assignment, Mapping):
            assignment_role_id = str(assignment.get("role_id") or "")
            provider = str(assignment.get("provider") or "")
        else:
            assignment_role_id = assignment.role_id
            provider = assignment.provider
        if assignment_role_id == role_id and provider:
            return provider
    return default


def coding_provider_from_report(report: Mapping[str, object]) -> str:
    """Return the implementer provider from a review-channel report payload."""
    collaboration = report.get("collaboration")
    provider = collaboration_provider(
        collaboration if isinstance(collaboration, Mapping) else None,
        role_id="coding_agent",
        default="",
    )
    if provider:
        return provider
    bridge_liveness = report.get("bridge_liveness")
    if isinstance(bridge_liveness, Mapping):
        capability = bridge_liveness.get("implementer_capability")
        if isinstance(capability, Mapping):
            provider = str(capability.get("provider") or "").strip().lower()
            if provider:
                return provider
    return "claude"
