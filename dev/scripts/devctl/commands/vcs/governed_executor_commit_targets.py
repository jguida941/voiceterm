"""Commit handoff target selection for governed VCS commands."""

from __future__ import annotations

from ...review_channel.publication_ownership import resolve_publication_owner
from ...runtime.conductor_capability import build_conductor_capability_state
from ...runtime.review_state_models import ReviewState
from ...runtime.reviewer_runtime_models import has_active_remote_control_attachment
from .governed_executor_actor_authority import (
    _collaboration_mapping,
    coding_agent_can_receive_stage_handoff,
    commit_authority_target,
    provider_has_live_role,
)


def resolve_commit_stage_target(review_state: ReviewState | None) -> str:
    """Pick the remote-control lane that can receive a pre-pipeline handoff.

    Stage handoffs only make sense when a remote-control executor lane is
    attached: the typical trigger is a sandbox-blocked ``.git/index.lock``
    that the local lane cannot resolve, so handing the request back to the
    same local lane would just re-emit the same block. Returns an empty
    string (fail-closed) when no remote-control attachment is active so
    callers can decide whether to defer or surface the block to the
    operator instead of self-routing.

    Attachments default to ``role="operator"``. The attached provider is
    normally the writable operator lane, but when the attached provider is
    the reviewer-bound agent and a separate implementer is bound, the
    stage handoff must route to the implementer to avoid recirculating
    back to the blocked reviewer queue.
    """
    if review_state is None:
        return ""
    attachment = getattr(
        getattr(review_state, "reviewer_runtime", None),
        "remote_control_attachment",
        None,
    )
    if not has_active_remote_control_attachment(attachment):
        return ""
    provider = str(getattr(attachment, "provider", "") or "").strip().lower()
    if provider:
        # The deeper invariant: whenever the attachment provider is the
        # typed reviewer-bound agent and a separate coding agent is bound,
        # route the stage handoff to the implementer to avoid recirculating
        # back to the blocked reviewer queue. This holds regardless of the
        # attachment role label (`operator`, `reviewer`, etc.) — the live
        # session payload uses `role="reviewer"` for the codex attachment
        # while keeping claude as the coding agent, and the reroute must
        # fire there too.
        collaboration = getattr(review_state, "collaboration", None)
        coding_agent = (
            str(getattr(collaboration, "coding_agent", "") or "").strip().lower()
        )
        review_agent = (
            str(getattr(collaboration, "review_agent", "") or "").strip().lower()
        )
        if (
            coding_agent
            and review_agent
            and provider == review_agent
            and coding_agent != review_agent
            and coding_agent_can_receive_stage_handoff(
                review_state, provider=coding_agent
            )
        ):
            return coding_agent
    return provider


def resolve_commit_execution_target(review_state: ReviewState | None) -> str:
    """Pick the writable provider lane for a typed commit handoff."""
    if review_state is None:
        return ""
    authority_target = commit_authority_target(review_state)
    if authority_target:
        return authority_target
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
    # v4.55.3 (rev_pkt_4778/4780): when typed collaboration is available,
    # build the capability from typed `role_assignments` rather than
    # trusting the (potentially legacy/projection-built) bridge
    # capability. A bridge capability with `may_edit_repo=True` from a
    # compatibility projection must not bypass the typed gate. The
    # bridge fallback only applies when no typed collaboration is
    # supplied (back-compat for callers/test fixtures without typed
    # role_assignments).
    typed_collaboration = _collaboration_mapping(review_state)
    if typed_collaboration is not None and implementer_provider:
        implementer_capability = build_conductor_capability_state(
            provider=implementer_provider,
            reviewer_mode=reviewer_mode,
            role="implementer",
            collaboration=typed_collaboration,
        )
    else:
        implementer_capability = review_state.bridge.implementer_capability or (
            build_conductor_capability_state(
                provider=implementer_provider,
                reviewer_mode=reviewer_mode,
                role="implementer",
                collaboration=typed_collaboration,
            )
            if implementer_provider
            else None
        )
    if (
        implementer_provider
        and implementer_capability
        and implementer_capability.may_edit_repo
        and provider_has_live_role(
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
    # v4.55.3 (rev_pkt_4780): same typed-over-bridge precedence for the
    # reviewer capability — typed `role_assignments` decide authority,
    # not bridge projections.
    if typed_collaboration is not None and reviewer_provider:
        reviewer_capability = build_conductor_capability_state(
            provider=reviewer_provider,
            reviewer_mode=reviewer_mode,
            role="reviewer",
            collaboration=typed_collaboration,
        )
    else:
        reviewer_capability = review_state.bridge.reviewer_capability or (
            build_conductor_capability_state(
                provider=reviewer_provider,
                reviewer_mode=reviewer_mode,
                role="reviewer",
                collaboration=typed_collaboration,
            )
            if reviewer_provider
            else None
        )
    if (
        reviewer_provider
        and reviewer_capability
        and reviewer_capability.may_edit_repo
        and provider_has_live_role(
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
    if target_role and not provider_has_live_role(
        review_state,
        provider=target_provider,
        role=target_role,
    ):
        return ""
    return target_provider


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
        if (
            str(getattr(participant, "capture_mode", "") or "").strip().lower()
            == "remote-control"
        ):
            return "remote_control"
    return "local_terminal"
