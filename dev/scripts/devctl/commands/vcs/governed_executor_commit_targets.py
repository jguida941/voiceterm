"""Commit handoff target selection for governed VCS commands."""

from __future__ import annotations

from ...review_channel.publication_ownership import resolve_publication_owner
from ...runtime.conductor_capability import build_conductor_capability_state
from ...runtime.review_state_models import ReviewState
from ...runtime.reviewer_runtime_models import has_active_remote_control_attachment


def resolve_commit_stage_target(review_state: ReviewState | None) -> str:
    """Pick the remote-control lane that can receive a pre-pipeline handoff."""
    if review_state is None:
        return ""
    attachment = getattr(
        getattr(review_state, "reviewer_runtime", None),
        "remote_control_attachment",
        None,
    )
    if not has_active_remote_control_attachment(attachment):
        return resolve_commit_execution_target(review_state)
    provider = str(getattr(attachment, "provider", "") or "").strip().lower()
    return provider or resolve_commit_execution_target(review_state)


def resolve_commit_execution_target(review_state: ReviewState | None) -> str:
    """Pick the writable provider lane for a typed commit handoff."""
    if review_state is None:
        return ""
    reviewer_mode = (
        review_state.bridge.effective_reviewer_mode
        or review_state.collaboration.reviewer_mode
        or review_state.bridge.reviewer_mode
        or "single_agent"
    )
    implementer_provider = _provider_for_role(
        review_state,
        role_id="coding_agent",
        fallback_provider=review_state.collaboration.coding_agent,
        fallback_role="implementer",
    )
    implementer_capability = review_state.bridge.implementer_capability or (
        build_conductor_capability_state(
            provider=implementer_provider,
            reviewer_mode=reviewer_mode,
            role="implementer",
        )
        if implementer_provider
        else None
    )
    if (
        implementer_provider
        and implementer_capability
        and implementer_capability.may_edit_repo
        and _provider_has_live_role(
            review_state,
            provider=implementer_provider,
            role="implementer",
        )
    ):
        return implementer_provider

    reviewer_provider = _provider_for_role(
        review_state,
        role_id="review_agent",
        fallback_provider=review_state.collaboration.review_agent,
        fallback_role="reviewer",
    )
    reviewer_capability = review_state.bridge.reviewer_capability or (
        build_conductor_capability_state(
            provider=reviewer_provider,
            reviewer_mode=reviewer_mode,
            role="reviewer",
        )
        if reviewer_provider
        else None
    )
    if (
        reviewer_provider
        and reviewer_capability
        and reviewer_capability.may_edit_repo
        and _provider_has_live_role(
            review_state,
            provider=reviewer_provider,
            role="reviewer",
        )
    ):
        return reviewer_provider
    return _publication_owned_target(
        review_state,
        reviewer_provider=reviewer_provider,
        implementer_provider=implementer_provider,
    )


def _provider_for_role(
    review_state: ReviewState,
    *,
    role_id: str,
    fallback_provider: str,
    fallback_role: str,
) -> str:
    for assignment in review_state.collaboration.role_assignments:
        if assignment.role_id != role_id:
            continue
        provider = str(assignment.provider or assignment.agent_id).strip().lower()
        if provider:
            return provider
    provider = str(fallback_provider or "").strip().lower()
    if provider:
        return provider
    if fallback_role == "implementer":
        capability = review_state.bridge.implementer_capability
    else:
        capability = review_state.bridge.reviewer_capability
    if capability is not None:
        provider = str(capability.provider or "").strip().lower()
        if provider:
            return provider
    return ""


def _publication_owned_target(
    review_state: ReviewState,
    *,
    reviewer_provider: str,
    implementer_provider: str,
) -> str:
    interaction_mode = _commit_execution_interaction_mode(review_state)
    if interaction_mode != "remote_control":
        return ""
    collaboration = getattr(review_state, "collaboration", None)
    topology = str(getattr(collaboration, "topology_mode", "") or "").strip()
    decision = resolve_publication_owner(
        interaction_mode=interaction_mode,
        topology=topology,
        reviewer_provider=reviewer_provider,
        implementer_provider=implementer_provider,
    )
    target_provider = str(decision.owner_provider or "").strip().lower()
    if not target_provider:
        return ""
    target_role = ""
    if str(decision.owner or "").strip().lower() == "implementer":
        target_role = "implementer"
    elif str(decision.owner or "").strip().lower() == "reviewer":
        target_role = "reviewer"
    if target_role and not _provider_has_live_role(
        review_state,
        provider=target_provider,
        role=target_role,
    ):
        return ""
    return target_provider


def _provider_has_live_role(
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
        participant_provider = str(
            getattr(participant, "provider", "")
            or getattr(participant, "agent_id", "")
            or ""
        ).strip().lower()
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
    return True


def _provider_live_role_assignment_status(
    collaboration: object,
    *,
    provider: str,
    role: str,
) -> str:
    role_ids = ("coding_agent",) if role == "implementer" else ("review_agent", "lead_agent")
    saw_live_provider_assignment = False
    for assignment in tuple(getattr(collaboration, "role_assignments", ()) or ()):
        assignment_provider = str(
            getattr(assignment, "provider", "")
            or getattr(assignment, "agent_id", "")
            or ""
        ).strip().lower()
        if assignment_provider != provider or not bool(getattr(assignment, "live", False)):
            continue
        saw_live_provider_assignment = True
        if str(getattr(assignment, "role_id", "") or "").strip().lower() in role_ids:
            return "matching"
    if saw_live_provider_assignment:
        return "other"
    return "unknown"


def _commit_execution_interaction_mode(review_state: ReviewState) -> str:
    reviewer_runtime = getattr(review_state, "reviewer_runtime", None)
    attachment = getattr(reviewer_runtime, "remote_control_attachment", None)
    if has_active_remote_control_attachment(attachment):
        return "remote_control"

    collaboration = getattr(review_state, "collaboration", None)
    restart = getattr(collaboration, "restart", None)
    if str(getattr(restart, "source", "") or "").strip() == "remote_control_attachment":
        return "remote_control"

    participants = tuple(getattr(collaboration, "participants", ()) or ())
    for participant in participants:
        if str(getattr(participant, "capture_mode", "") or "").strip().lower() == "remote-control":
            return "remote_control"
    return "local_terminal"
