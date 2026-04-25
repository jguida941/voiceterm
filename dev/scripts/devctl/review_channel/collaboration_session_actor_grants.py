"""Capability-grant helpers for collaboration-session authority rows."""

from __future__ import annotations

from ..runtime.review_state_collaboration_models import CapabilityGrantState
from ..runtime.review_state_models import CollaborationParticipantState
from .collaboration_session_lane_owners import same_agent


def authority_grants(context: object) -> tuple[CapabilityGrantState, ...]:
    grants: list[CapabilityGrantState] = []
    inputs = context.inputs
    if same_agent(context.actor_id, inputs.mutation_owner):
        grants.extend(
            _grants(
                ("repo.stage", "repo.commit"),
                context,
                granted=context.live,
                source="mutation_owner",
                reason=(
                    "Live mutation owner controls repo mutation."
                    if context.live
                    else "Mutation owner is not live."
                ),
            )
        )
    if context.live and _is_remote_control(context.participant):
        grants.extend(
            _grants(
                ("repo.stage_handoff",),
                context,
                granted=True,
                source="remote_control_attachment",
                reason="Remote-control actor can receive sandbox/stage handoffs.",
            )
        )
    if same_agent(context.actor_id, inputs.verification_owner):
        grants.extend(
            _grants(
                ("review.checkpoint", "review.finding"),
                context,
                granted=context.live,
                source="verification_owner",
                reason="Live verification owner controls review/checkpoint output.",
            )
        )
    if context.role == "operator" or same_agent(context.actor_id, inputs.watcher_owner):
        grants.extend(
            _grants(
                ("approval.commit", "runtime.observe"),
                context,
                granted=context.live,
                source="operator_or_watcher",
                reason="Approval and observation do not imply repo mutation.",
            )
        )
    return tuple(grants)


def worktree_identity(participant: CollaborationParticipantState | None) -> str:
    if participant is None:
        return ""
    return participant.worktree or participant.workspace_root


def _grants(
    capabilities: tuple[str, ...],
    context: object,
    *,
    granted: bool,
    source: str,
    reason: str,
) -> tuple[CapabilityGrantState, ...]:
    return tuple(
        CapabilityGrantState(
            capability=capability,
            granted=granted,
            source=source,
            reason=reason,
            target_kind="runtime",
            target_ref=f"reviewer_mode:{context.inputs.reviewer_mode}",
            worktree_identity=worktree_identity(context.participant),
            issued_at_utc=context.inputs.timestamp,
        )
        for capability in capabilities
    )


def _is_remote_control(participant: CollaborationParticipantState | None) -> bool:
    if participant is None:
        return False
    return participant.capture_mode == "remote-control"
