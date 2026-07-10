"""Actor-authority helpers for governed VCS target selection."""

from __future__ import annotations

from ...runtime.conductor_capability import build_conductor_capability_state
from ...runtime.review_state_collaboration_models import (
    ActorAuthorityState,
    actor_authority_for_capability,
)
from ...runtime.review_state_models import ReviewState


def commit_authority_target(review_state: ReviewState) -> str:
    """Return the live mutation owner when repo.commit is explicitly granted."""
    collaboration = getattr(review_state, "collaboration", None)
    mutation_owner = str(getattr(collaboration, "mutation_owner", "") or "").strip()
    authority = target_authority(
        review_state,
        capability="repo.commit",
        provider=mutation_owner,
    )
    if authority is None:
        return ""
    if not authority_has_live_role(
        review_state,
        authority=authority,
        expected_role="implementer",
    ):
        return ""
    return str(authority.provider or authority.actor_id).strip().lower()


def coding_agent_can_receive_stage_handoff(
    review_state: ReviewState,
    *,
    provider: str,
) -> bool:
    """Verify the coding-agent reroute target is live and writable."""
    authority = target_authority(
        review_state,
        capability="repo.stage",
        provider=provider,
        alternate_capabilities=("repo.stage_handoff",),
    )
    if authority is not None and authority_has_live_role(
        review_state,
        authority=authority,
        expected_role="implementer",
    ):
        return True
    reviewer_mode = (
        review_state.bridge.effective_reviewer_mode
        or review_state.collaboration.reviewer_mode
        or review_state.bridge.reviewer_mode
        or "single_agent"
    )
    capability = build_conductor_capability_state(
        provider=provider,
        reviewer_mode=reviewer_mode,
        role="implementer",
    )
    if capability is None or not getattr(capability, "may_edit_repo", False):
        return False
    return provider_has_live_role(
        review_state,
        provider=provider,
        role="implementer",
    )


def target_authority(
    review_state: ReviewState,
    *,
    capability: str,
    provider: str,
    alternate_capabilities: tuple[str, ...] = (),
) -> ActorAuthorityState | None:
    collaboration = getattr(review_state, "collaboration", None)
    authorities = tuple(getattr(collaboration, "actor_authorities", ()) or ())
    if not authorities:
        return None
    return actor_authority_for_capability(
        authorities,
        capability,
        preferred_actor=provider,
        alternate_capabilities=alternate_capabilities,
    )


def authority_has_live_role(
    review_state: ReviewState,
    *,
    authority: ActorAuthorityState,
    expected_role: str,
) -> bool:
    role = str(authority.role or "").strip().lower()
    if role not in {"implementer", "reviewer"}:
        return False
    normalized_expected = str(expected_role or "").strip().lower()
    if normalized_expected == "implementer" and role != "implementer":
        return False
    provider = str(authority.provider or authority.actor_id or "").strip().lower()
    if not provider:
        return False
    return provider_has_live_role(
        review_state,
        provider=provider,
        role=role,
    )


def provider_has_live_role(
    review_state: ReviewState,
    *,
    provider: str,
    role: str,
) -> bool:
    normalized_provider = str(provider or "").strip().lower()
    normalized_role = str(role or "").strip().lower()
    if not normalized_provider or normalized_role not in {"implementer", "reviewer"}:
        return False
    collaboration = getattr(review_state, "collaboration", None)
    participants = tuple(getattr(collaboration, "participants", ()) or ())
    saw_live_provider_participant = False
    for participant in participants:
        participant_provider = (
            str(
                getattr(participant, "provider", "")
                or getattr(participant, "agent_id", "")
                or ""
            )
            .strip()
            .lower()
        )
        if participant_provider != normalized_provider or not bool(
            getattr(participant, "live", False)
        ):
            continue
        saw_live_provider_participant = True
        participant_role = str(getattr(participant, "role", "") or "").strip().lower()
        if participant_role == normalized_role:
            return True
    if saw_live_provider_participant:
        return False
    assignment_status = _provider_live_role_assignment_status(
        collaboration,
        provider=normalized_provider,
        role=normalized_role,
    )
    if assignment_status == "matching":
        return True
    if assignment_status == "other":
        return False
    # Fail closed when no live participant or live role-assignment proves
    # the lane is reachable.
    return False


def _provider_live_role_assignment_status(
    collaboration: object,
    *,
    provider: str,
    role: str,
) -> str:
    role_ids = (
        ("coding_agent",) if role == "implementer" else ("review_agent", "lead_agent")
    )
    saw_live_provider_assignment = False
    for assignment in tuple(getattr(collaboration, "role_assignments", ()) or ()):
        assignment_provider = (
            str(
                getattr(assignment, "provider", "")
                or getattr(assignment, "agent_id", "")
                or ""
            )
            .strip()
            .lower()
        )
        if assignment_provider != provider or not bool(
            getattr(assignment, "live", False)
        ):
            continue
        saw_live_provider_assignment = True
        if str(getattr(assignment, "role_id", "") or "").strip().lower() in role_ids:
            return "matching"
    if saw_live_provider_assignment:
        return "other"
    return "unknown"
