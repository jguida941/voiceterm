"""Reviewer-runtime payload normalization helpers."""

from __future__ import annotations

from collections.abc import Mapping

from .conductor_capability import authority_reviewer_mode, resolve_reviewer_mode
from .control_state import _mapping, _string
from .review_state_models import ReviewCurrentSessionState
from .review_state_parse_support import _bool
from .reviewer_gate_logic import (
    ReviewerRuntimeBlockInputs,
    reviewer_runtime_block_state,
)
from .reviewer_runtime_models import (
    AgentRuntimeClock,
    InboxObservationState,
    PacketAttentionState,
    RemoteControlAttachmentState,
    ReviewerAcceptanceState,
    ReviewerDutyProof,
    ReviewerRuntimeContract,
    remote_control_attachment_from_mapping,
)
from .reviewer_runtime_parser_state_rows import (
    bridge_last_poll_state,
    rollover_state,
    session_owner_state,
    typed_last_poll_state,
)
from .session_posture import build_session_posture, session_posture_from_mapping


def reviewer_runtime_state_from_payload(
    *,
    reviewer_runtime: Mapping[str, object],
    bridge: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    attention: Mapping[str, object],
    recovery_assessment: Mapping[str, object],
) -> ReviewerRuntimeContract:
    """Build the typed reviewer-runtime state from review-state payload fields."""
    attention_status = _diagnosis_status(
        recovery_assessment=recovery_assessment,
        attention=attention,
    )
    recovery_command = _decision_command(
        reviewer_runtime=reviewer_runtime,
        recovery_assessment=recovery_assessment,
        attention=attention,
    )
    if reviewer_runtime:
        return _typed_reviewer_runtime_state(
            reviewer_runtime=reviewer_runtime,
            bridge=bridge,
            bridge_liveness=bridge_liveness,
            current_session=current_session,
            attention_status=attention_status,
            recovery_command=recovery_command,
        )
    return _bridge_reviewer_runtime_state(
        bridge=bridge,
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        attention=attention,
        attention_status=attention_status,
        recovery_command=recovery_command,
    )


def _typed_reviewer_runtime_state(
    *,
    reviewer_runtime: Mapping[str, object],
    bridge: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    attention_status: str,
    recovery_command: str,
) -> ReviewerRuntimeContract:
    last_poll = _mapping(reviewer_runtime.get("last_poll"))
    rollover = _mapping(reviewer_runtime.get("rollover"))
    session_owner = _mapping(reviewer_runtime.get("session_owner"))
    review_acceptance = _mapping(reviewer_runtime.get("review_acceptance"))
    remote_control_attachment = remote_control_attachment_from_mapping(
        reviewer_runtime.get("remote_control_attachment")
    )
    session_posture = session_posture_from_mapping(
        reviewer_runtime.get("session_posture")
    )
    review_accepted = _bool(review_acceptance.get("review_accepted"))
    reviewer_mode = resolve_reviewer_mode(
        reviewer_runtime.get("reviewer_mode"),
        bridge.get("reviewer_mode"),
        bridge.get("effective_reviewer_mode"),
    )
    effective_reviewer_mode = resolve_reviewer_mode(
        reviewer_runtime.get("effective_reviewer_mode"),
        bridge.get("effective_reviewer_mode"),
        reviewer_runtime.get("reviewer_mode"),
        bridge.get("reviewer_mode"),
    )
    reviewer_mode = authority_reviewer_mode(
        reviewer_mode,
        effective_reviewer_mode,
    )
    stale_reason = _stale_reason(
        reviewer_runtime.get("stale_reason"), attention_status=attention_status
    )
    implementer_ack_current = _implementer_ack_current(
        reviewer_runtime=reviewer_runtime,
        bridge=bridge,
        current_session=current_session,
    )
    implementation_blocked, implementation_block_reason = _implementation_block_state(
        reviewer_runtime=reviewer_runtime,
        current_session=current_session,
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        implementer_ack_current=implementer_ack_current,
        attention_status=stale_reason,
    )
    return ReviewerRuntimeContract(
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        reviewer_freshness=(
            _string(reviewer_runtime.get("reviewer_freshness"))
            or _string(bridge.get("reviewer_freshness"))
            or _string(bridge_liveness.get("reviewer_freshness"))
            or "unknown"
        ),
        stale_reason=stale_reason,
        conductor_visibility=(
            _string(reviewer_runtime.get("conductor_visibility"))
            or _string(bridge_liveness.get("conductor_visibility"))
            or "unknown"
        ),
        implementer_ack_current=implementer_ack_current,
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
        last_poll=typed_last_poll_state(
            last_poll=last_poll,
            bridge=bridge,
            bridge_liveness=bridge_liveness,
        ),
        rollover=rollover_state(rollover),
        session_owner=session_owner_state(session_owner),
        recovery_action_allowed=(
            _string(reviewer_runtime.get("recovery_action_allowed")) or recovery_command
        ),
        review_acceptance=ReviewerAcceptanceState(
            current_verdict=_string(review_acceptance.get("current_verdict")),
            open_findings=_string(review_acceptance.get("open_findings"))
            or current_session.open_findings,
            review_accepted=review_accepted,
            reviewer_accepted_implementer_state_hash=_string(
                review_acceptance.get("reviewer_accepted_implementer_state_hash")
            ),
        ),
        publish_clear=(
            _bool(reviewer_runtime.get("publish_clear"))
            if "publish_clear" in reviewer_runtime
            else review_accepted
        ),
        remote_control_attachment=remote_control_attachment,
        session_posture=session_posture
        or build_session_posture(
            reviewer_mode=reviewer_mode,
            effective_reviewer_mode=effective_reviewer_mode,
            remote_control_attachment=remote_control_attachment,
        ),
        duty_proof=_duty_proof_from_mapping(reviewer_runtime.get("duty_proof")),
        inbox_observation=_inbox_observation_from_mapping(
            reviewer_runtime.get("inbox_observation")
        ),
        agent_runtime_clock=_agent_runtime_clock_from_mapping(
            reviewer_runtime.get("agent_runtime_clock")
        ),
        packet_attention=_packet_attention_from_mapping(
            reviewer_runtime.get("packet_attention")
        ),
    )


def _duty_proof_from_mapping(value: object) -> ReviewerDutyProof:
    """Per rev_pkt_2475 + rev_pkt_2498: deserialize typed reviewer-duty proof
    from disk projection so the contract round-trips faithfully through
    the projection-rebuild path. Empty/missing → safe default."""
    payload = _mapping(value)
    if not payload:
        return ReviewerDutyProof()
    return ReviewerDutyProof(
        reviewer_actor_id=_string(payload.get("reviewer_actor_id")),
        reviewer_session_id=_string(payload.get("reviewer_session_id")),
        last_packet_event_id=_string(payload.get("last_packet_event_id")),
        last_packet_observed_at_utc=_string(payload.get("last_packet_observed_at_utc")),
        pending_packet_count=int(payload.get("pending_packet_count") or 0),
        current_head_sha=_string(payload.get("current_head_sha")),
        staged_tree_hash=_string(payload.get("staged_tree_hash")),
        worktree_hash=_string(payload.get("worktree_hash")),
        changed_path_count=int(payload.get("changed_path_count") or 0),
        reviewed_diff_hash=_string(payload.get("reviewed_diff_hash")),
        reviewed_diff_base=_string(payload.get("reviewed_diff_base")),
        reviewed_path_count=int(payload.get("reviewed_path_count") or 0),
        last_diff_review_at_utc=_string(payload.get("last_diff_review_at_utc")),
        semantic_review_source=_string(payload.get("semantic_review_source")),
        semantic_review_claimed=_bool(payload.get("semantic_review_claimed")),
        review_conflict_class=_string(payload.get("review_conflict_class")),
        review_conflict_reasons=tuple(
            _string(row)
            for row in (payload.get("review_conflict_reasons") or ())
            if _string(row)
        ),
        state=_string(payload.get("state")) or "unknown",
        stale_reasons=tuple(_string(row) for row in (payload.get("stale_reasons") or ()) if _string(row)),
    )


def _inbox_observation_from_mapping(value: object) -> InboxObservationState:
    """Per rev_pkt_2486 projection-rebuild gap fix: deserialize typed inbox
    observation from disk so reviewer_mode renderers don't see default-empty
    after every refresh. Empty/missing → safe default."""
    payload = _mapping(value)
    if not payload:
        return InboxObservationState()
    return InboxObservationState(
        actor_id=_string(payload.get("actor_id")),
        session_id=_string(payload.get("session_id")),
        last_inbox_event_id=_string(payload.get("last_inbox_event_id")),
        last_inbox_event_at_utc=_string(payload.get("last_inbox_event_at_utc")),
        last_inbox_observed_event_id=_string(payload.get("last_inbox_observed_event_id")),
        last_inbox_observed_at_utc=_string(payload.get("last_inbox_observed_at_utc")),
        pending_packet_count=int(payload.get("pending_packet_count") or 0),
        superseded_packet_id=_string(payload.get("superseded_packet_id")),
        pivot_required=_bool(payload.get("pivot_required")),
        pivot_reasons=tuple(_string(row) for row in (payload.get("pivot_reasons") or ()) if _string(row)),
    )


def _agent_runtime_clock_from_mapping(value: object) -> AgentRuntimeClock:
    """Per rev_pkt_2498 (1) projection round-trip: deserialize typed shared
    runtime clock from disk so all agents continue to read the same
    source_latest_event_id after a projection rebuild."""
    payload = _mapping(value)
    if not payload:
        return AgentRuntimeClock()
    return AgentRuntimeClock(
        source_latest_event_id=_string(payload.get("source_latest_event_id")),
        source_latest_event_at_utc=_string(payload.get("source_latest_event_at_utc")),
        cadence_seconds=int(payload.get("cadence_seconds") or 0),
        last_published_at_utc=_string(payload.get("last_published_at_utc")),
        snapshot_id=_string(payload.get("snapshot_id")),
    )


def _packet_attention_from_mapping(value: object) -> PacketAttentionState:
    """Per rev_pkt_2498 (2,4) projection-rebuild gap fix: deserialize typed
    per-actor_session attention contract from disk so the commit gate's
    typed-state path can read populated wake_required / pivot_required
    fields after a projection rebuild instead of seeing all-defaults that
    silently let the env-fallback fire."""
    payload = _mapping(value)
    if not payload:
        return PacketAttentionState()
    return PacketAttentionState(
        observation_actor_id=_string(payload.get("observation_actor_id")),
        observation_session_id=_string(payload.get("observation_session_id")),
        latest_inbox_event_id=_string(payload.get("latest_inbox_event_id")),
        latest_attention_packet_id=_string(payload.get("latest_attention_packet_id")),
        latest_attention_changed_at_utc=_string(payload.get("latest_attention_changed_at_utc")),
        last_observed_event_id=_string(payload.get("last_observed_event_id")),
        last_observed_at_utc=_string(payload.get("last_observed_at_utc")),
        pending_packet_count=int(payload.get("pending_packet_count") or 0),
        unopened_body_packet_count=int(payload.get("unopened_body_packet_count") or 0),
        unopened_body_packet_ids=tuple(
            _string(row)
            for row in (payload.get("unopened_body_packet_ids") or ())
            if _string(row)
        ),
        body_open_required=_bool(payload.get("body_open_required")),
        body_open_packet_id=_string(payload.get("body_open_packet_id")),
        body_open_command=_string(payload.get("body_open_command")),
        semantic_ingestion_required=_bool(payload.get("semantic_ingestion_required")),
        semantic_ingestion_packet_id=_string(payload.get("semantic_ingestion_packet_id")),
        semantic_ingestion_command=_string(payload.get("semantic_ingestion_command")),
        semantic_ingestion_reason=_string(payload.get("semantic_ingestion_reason")),
        superseded_packet_id=_string(payload.get("superseded_packet_id")),
        pivot_required=_bool(payload.get("pivot_required")),
        wake_required=_bool(payload.get("wake_required")),
        stale_reason=_string(payload.get("stale_reason")),
        pivot_reasons=tuple(_string(row) for row in (payload.get("pivot_reasons") or ()) if _string(row)),
    )


def _bridge_reviewer_runtime_state(
    *,
    bridge: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    attention: Mapping[str, object],
    attention_status: str,
    recovery_command: str,
) -> ReviewerRuntimeContract:
    reviewer_mode = resolve_reviewer_mode(
        bridge.get("reviewer_mode"),
        bridge.get("effective_reviewer_mode"),
    )
    effective_reviewer_mode = resolve_reviewer_mode(
        bridge.get("effective_reviewer_mode"),
        bridge.get("reviewer_mode"),
    )
    reviewer_mode = authority_reviewer_mode(
        reviewer_mode,
        effective_reviewer_mode,
    )
    implementer_ack_current = _implementer_ack_current(
        reviewer_runtime={},
        bridge=bridge,
        current_session=current_session,
    )
    implementation_blocked, implementation_block_reason = _implementation_block_state(
        reviewer_runtime={},
        current_session=current_session,
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        implementer_ack_current=implementer_ack_current,
        attention_status=_stale_reason("", attention_status=attention_status),
    )
    review_accepted = _bool(bridge.get("review_accepted"))
    return ReviewerRuntimeContract(
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        reviewer_freshness=_string(bridge.get("reviewer_freshness"))
        or _string(bridge_liveness.get("reviewer_freshness"))
        or "unknown",
        stale_reason=_stale_reason("", attention_status=attention_status),
        conductor_visibility=_string(bridge_liveness.get("conductor_visibility"))
        or "unknown",
        implementer_ack_current=implementer_ack_current,
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
        last_poll=bridge_last_poll_state(
            bridge=bridge,
            bridge_liveness=bridge_liveness,
        ),
        recovery_action_allowed=recovery_command
        or _string(attention.get("recommended_command")),
        review_acceptance=ReviewerAcceptanceState(
            current_verdict="",
            open_findings=current_session.open_findings
            or "- reviewer state unavailable.",
            review_accepted=review_accepted,
            reviewer_accepted_implementer_state_hash="",
        ),
        publish_clear=review_accepted,
        session_posture=build_session_posture(
            reviewer_mode=reviewer_mode,
            effective_reviewer_mode=effective_reviewer_mode,
        ),
    )


def _stale_reason(value: object, *, attention_status: str) -> str:
    stale_reason = _string(value)
    if stale_reason or attention_status in {"", "healthy"}:
        return stale_reason
    return attention_status


def _diagnosis_status(
    *,
    recovery_assessment: Mapping[str, object],
    attention: Mapping[str, object],
) -> str:
    diagnosis = _mapping(recovery_assessment.get("diagnosis"))
    return _string(diagnosis.get("status")) or _string(attention.get("status"))


def _decision_command(
    *,
    reviewer_runtime: Mapping[str, object],
    recovery_assessment: Mapping[str, object],
    attention: Mapping[str, object],
) -> str:
    if reviewer_runtime:
        command = _string(reviewer_runtime.get("recovery_action_allowed"))
        if command:
            return command
    decision = _mapping(recovery_assessment.get("decision"))
    return _string(decision.get("command")) or _string(
        attention.get("recommended_command")
    )


def _implementation_block_state(
    *,
    reviewer_runtime: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    reviewer_mode: str,
    effective_reviewer_mode: str,
    implementer_ack_current: bool,
    attention_status: str,
) -> tuple[bool, str]:
    derived_blocked, derived_block_reason = reviewer_runtime_block_state(
        ReviewerRuntimeBlockInputs(
            reviewer_mode=reviewer_mode,
            effective_reviewer_mode=effective_reviewer_mode,
            implementer_ack_current=implementer_ack_current,
            attention_status=attention_status,
            current_instruction=current_session.current_instruction,
            implementer_status=current_session.implementer_status,
            implementer_ack=current_session.implementer_ack,
            implementer_ack_state=current_session.implementer_ack_state,
        )
    )
    implementation_blocked = (
        _bool(reviewer_runtime.get("implementation_blocked"))
        if "implementation_blocked" in reviewer_runtime
        else derived_blocked
    )
    implementation_block_reason = (
        _string(reviewer_runtime.get("implementation_block_reason"))
        if "implementation_block_reason" in reviewer_runtime
        else derived_block_reason
    )
    if implementation_blocked and not implementation_block_reason:
        return True, derived_block_reason
    if not implementation_blocked:
        return False, ""
    return True, implementation_block_reason


def _implementer_ack_current(
    *,
    reviewer_runtime: Mapping[str, object],
    bridge: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
) -> bool:
    if "implementer_ack_current" in reviewer_runtime:
        return _bool(reviewer_runtime.get("implementer_ack_current"))
    ack_state = current_session.implementer_ack_state
    if ack_state in {"current", "stale", "pending"}:
        return ack_state == "current"
    return _bool(bridge.get("claude_ack_current"))
