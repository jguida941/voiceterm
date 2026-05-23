"""Provider-resolution helpers shared by review-channel runtime builders."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_state_models import CollaborationSessionState
from ..runtime.role_profile import normalize_role_id, role_capability_classes


_DEPRECATED_ROLE_REPLACEMENTS = {
    "lead_agent": "orchestrator",
    "review_agent": "architecture_review",
    "coding_agent": "implementation",
    "operator_agent": "operator",
}


def collaboration_provider(
    collaboration: CollaborationSessionState | Mapping[str, object] | None,
    *,
    role_id: str,
    default: str,
) -> str:
    """Return the provider assigned to one collaboration role."""
    if collaboration is None:
        return default
    normalized_role_id = _normalize_role_id(role_id)
    direct_provider = _direct_role_provider(collaboration, role_id=normalized_role_id)
    if direct_provider:
        return direct_provider
    assignments = (
        collaboration.get("role_assignments")
        if isinstance(collaboration, Mapping)
        else getattr(collaboration, "role_assignments", ())
    )
    for assignment in assignments or ():
        if isinstance(assignment, Mapping):
            assignment_role_id = str(assignment.get("role_id") or "")
            provider = _normalized_provider(assignment.get("provider"))
        else:
            assignment_role_id = assignment.role_id
            provider = _normalized_provider(assignment.provider)
        if _normalize_role_id(assignment_role_id) == normalized_role_id and provider:
            return provider
    return default


def collaboration_provider_for_capability(
    collaboration: CollaborationSessionState | Mapping[str, object] | None,
    *,
    capability_classes: set[str],
    default: str = "",
) -> str:
    """Return the first provider assigned to a role with the requested capability."""
    if collaboration is None:
        return default
    assignments = (
        collaboration.get("role_assignments")
        if isinstance(collaboration, Mapping)
        else getattr(collaboration, "role_assignments", ())
    )
    for assignment in assignments or ():
        if isinstance(assignment, Mapping):
            assignment_role_id = _normalize_role_id(assignment.get("role_id"))
            provider = _normalized_provider(assignment.get("provider"))
        else:
            assignment_role_id = _normalize_role_id(assignment.role_id)
            provider = _normalized_provider(assignment.provider)
        if provider and set(role_capability_classes(assignment_role_id)) & capability_classes:
            return provider
    participants = (
        collaboration.get("participants")
        if isinstance(collaboration, Mapping)
        else getattr(collaboration, "participants", ())
    )
    for participant in participants or ():
        if isinstance(participant, Mapping):
            role_id = _normalize_role_id(participant.get("role"))
            provider = _normalized_provider(participant.get("provider"))
        else:
            role_id = _normalize_role_id(participant.role)
            provider = _normalized_provider(participant.provider)
        if provider and set(role_capability_classes(role_id)) & capability_classes:
            return provider
    return default


def coding_provider_from_review_state(
    review_state: object | Mapping[str, object] | None,
) -> str:
    """Return the coding-agent provider from one review-state payload."""
    return _role_provider_from_review_state(
        review_state,
        role_id="implementation",
        default="",
    )


def reviewer_provider_from_review_state(
    review_state: object | Mapping[str, object] | None,
) -> str:
    """Return the reviewer provider from one review-state payload."""
    return _role_provider_from_review_state(
        review_state,
        role_id="architecture_review",
        default="",
    )


def coding_provider_from_report(report: Mapping[str, object]) -> str:
    """Return the implementer provider from a review-channel report payload."""
    collaboration = report.get("collaboration")
    provider = collaboration_provider(
        collaboration if isinstance(collaboration, Mapping) else None,
        role_id="implementation",
        default="",
    )
    bridge_liveness = report.get("bridge_liveness")
    if isinstance(bridge_liveness, Mapping):
        capability = bridge_liveness.get("implementer_capability")
        if isinstance(capability, Mapping):
            provider = _normalized_provider(capability.get("provider"))
            if provider:
                return provider
    return provider


def _role_provider_from_review_state(
    review_state: object | Mapping[str, object] | None,
    *,
    role_id: str,
    default: str,
) -> str:
    collaboration = None
    if isinstance(review_state, Mapping):
        collaboration = review_state.get("collaboration")
    elif review_state is not None:
        collaboration = getattr(review_state, "collaboration", None)
    return collaboration_provider(
        collaboration if isinstance(collaboration, Mapping) or collaboration is None else collaboration,
        role_id=role_id,
        default=default,
    )


def _direct_role_provider(
    collaboration: CollaborationSessionState | Mapping[str, object],
    *,
    role_id: str,
) -> str:
    field_name = role_id
    if isinstance(collaboration, Mapping):
        return _normalized_provider(collaboration.get(field_name))
    return _normalized_provider(getattr(collaboration, field_name, ""))


def _normalize_role_id(value: object) -> str:
    role_id = normalize_role_id(value)
    return _DEPRECATED_ROLE_REPLACEMENTS.get(role_id, role_id)


def _normalized_provider(value: object) -> str:
    return str(value or "").strip().lower()
