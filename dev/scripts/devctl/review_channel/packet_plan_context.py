"""Derive non-authoritative plan context for review-channel packets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

from ..runtime.packet_plan_context import (
    packet_plan_context_from_plan_id,
    packet_plan_context_from_work_intake,
)
from .event_store import DEFAULT_REVIEW_CHANNEL_PLAN_ID
from .packet_contract import PacketPostRequest, PacketTargetFields
from .packet_target_validation import (
    RUNTIME_ACTION_REQUEST_ACTIONS,
    RUNTIME_TARGET_PACKET_KINDS,
)


def enrich_packet_request_plan_context(
    *,
    repo_root: Path,
    review_state_payload: Mapping[str, object] | None,
    request: PacketPostRequest,
) -> PacketPostRequest:
    """Attach current WorkIntake plan context when a post omitted it.

    The context is intentionally non-authoritative: it lets agents and startup
    surfaces keep packet scope tied to the selected plan target, while only
    plan-targeted ``apply`` transitions can mutate typed master-plan authority.
    """
    if _request_disallows_plan_context(request):
        return request

    context = _derive_packet_plan_context(
        repo_root=repo_root,
        review_state_payload=review_state_payload,
        fallback_plan_id=request.plan_id,
    )
    if not context.has_values():
        return request

    target = request.target
    next_target = PacketTargetFields.from_values(
        target_kind=target.target_kind,
        target_ref=target.target_ref,
        target_revision=target.target_revision,
        anchor_refs=target.anchor_refs or context.anchor_refs,
        intake_ref=target.intake_ref or context.intake_ref,
        mutation_op=target.mutation_op,
        target_role=target.target_role,
        target_session_id=target.target_session_id,
        anchor_scope=target.anchor_scope,
        requested_session_visibility=target.requested_session_visibility,
    )
    next_plan_id = request.plan_id
    if _default_or_missing_plan_id(next_plan_id) and context.plan_id:
        next_plan_id = context.plan_id

    if next_target == target and next_plan_id == request.plan_id:
        return request
    return replace(request, plan_id=next_plan_id, target=next_target)


def _derive_packet_plan_context(
    *,
    repo_root: Path,
    review_state_payload: Mapping[str, object] | None,
    fallback_plan_id: str,
) -> PacketPlanContext:
    try:
        payload = _work_intake_context_payload(
            repo_root=repo_root,
            review_state_payload=review_state_payload,
        )
    except (ImportError, OSError, RuntimeError, ValueError):
        payload = {}
    context = packet_plan_context_from_work_intake(
        payload,
        fallback_plan_id=fallback_plan_id,
    )
    if context.has_values():
        return context
    return packet_plan_context_from_plan_id(fallback_plan_id)


def _work_intake_context_payload(
    *,
    repo_root: Path,
    review_state_payload: Mapping[str, object] | None,
) -> dict[str, object]:
    from ..governance.draft import scan_repo_governance
    from ..runtime.review_state_parser import review_state_from_payload
    from ..runtime.work_intake import WorkIntakeStateInputs, build_work_intake_packet

    governance = scan_repo_governance(repo_root)
    review_state = (
        review_state_from_payload(review_state_payload)
        if isinstance(review_state_payload, Mapping)
        else None
    )
    packet = build_work_intake_packet(
        repo_root=repo_root,
        governance=governance,
        advisory_action="review_channel_post",
        advisory_reason="packet_plan_context",
        state_inputs=WorkIntakeStateInputs(review_state=review_state),
    )
    return packet.to_dict()


def _request_disallows_plan_context(request: PacketPostRequest) -> bool:
    if request.kind in RUNTIME_TARGET_PACKET_KINDS:
        return True
    if (
        request.kind == "action_request"
        and request.requested_action in RUNTIME_ACTION_REQUEST_ACTIONS
    ):
        return True
    target = request.target
    return bool(
        target.target_kind
        or target.target_ref
        or target.target_revision
        or target.mutation_op
    )


def _default_or_missing_plan_id(value: object) -> bool:
    text = str(value or "").strip()
    return not text or text == DEFAULT_REVIEW_CHANNEL_PLAN_ID


__all__ = [
    "enrich_packet_request_plan_context",
]
