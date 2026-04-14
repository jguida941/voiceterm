"""Parsers that normalize review-channel artifacts into typed runtime state."""

from __future__ import annotations

from collections.abc import Mapping

from ..platform.coordination_snapshot_models import coordination_snapshot_from_mapping
from .authority_snapshot import authority_snapshot_from_mapping
from .control_state import _int, _mapping, _string, _string_rows
from .remote_commit_pipeline_models import push_authorization_from_mapping
from .review_state_collaboration_parse import collaboration_state_from_payload
from .review_state_parser_rows import (
    canonicalize_current_instruction_state as _canonicalize_current_instruction_state,
    context_pack_refs_from_value as _context_pack_refs_from_value,
    current_session_state_from_payload as _current_session_state_from_payload,
    instruction_revision as _instruction_revision,
    packet_states_from_value as _packet_states_from_value,
    registry_agents_from_value as _registry_agents_from_value,
)
from .review_state_parse_support import (
    _bool,
    attention_projection_warning,
    attention_state_from_mapping,
    recovery_assessment_from_mapping,
    review_bridge_state_from_payload,
)
from .review_state_models import (
    AgentRegistryState,
    packet_inbox_from_mapping,
    ReviewQueueState,
    ReviewSessionState,
    ReviewState,
    review_candidate_from_mapping,
)
from .review_packet_inbox import build_packet_inbox_payload
from .review_state_commit_pipeline_parse import commit_pipeline_from_review_payload
from .reviewer_runtime_parser import reviewer_runtime_state_from_payload


def review_state_from_payload(payload: Mapping[str, object]) -> ReviewState | None:
    """Normalize review-state or full projection payloads into a shared contract."""
    envelope = _review_state_envelope(payload)
    if envelope is None:
        return None
    return _build_review_state(
        payload=payload,
        envelope=envelope,
    )


def _build_review_state(
    *,
    payload: Mapping[str, object],
    envelope: tuple[
        Mapping[str, object],
        Mapping[str, object],
        Mapping[str, object],
        Mapping[str, object],
        Mapping[str, object],
        list[str],
        tuple[str, ...],
    ],
) -> ReviewState:
    (
        review_payload,
        registry_payload,
        attention,
        recovery_assessment,
        bridge_liveness,
        warnings,
        errors,
    ) = envelope

    review = _mapping(review_payload.get("review"))
    queue = _mapping(review_payload.get("queue"))
    bridge = _mapping(review_payload.get("bridge"))
    commit_pipeline = commit_pipeline_from_review_payload(
        payload=payload,
        review_payload=review_payload,
    )
    current_session = _mapping(review_payload.get("current_session"))
    packet_inbox = _review_state_packet_inbox(
        payload=payload,
        review_payload=review_payload,
        attention=attention,
    )
    current_session_state = _current_session_state_from_payload(
        current_session=current_session,
        bridge=bridge,
    )
    bridge_state = review_bridge_state_from_payload(
        bridge=bridge,
        bridge_liveness=bridge_liveness,
    )
    registry_state = AgentRegistryState(
        timestamp=_string(registry_payload.get("timestamp"))
        or _string(registry_payload.get("updated_at")),
        agents=_registry_agents_from_value(registry_payload.get("agents")),
    )
    collaboration_state = collaboration_state_from_payload(
        collaboration=_mapping(review_payload.get("collaboration")),
        review=review,
        current_session=current_session_state,
        bridge=bridge_state,
        registry=registry_state,
    )
    assessment_state = recovery_assessment_from_mapping(recovery_assessment)
    attention_state = attention_state_from_mapping(
        attention,
        recovery_assessment=assessment_state,
    )
    warning = attention_projection_warning(
        raw_attention=attention,
        normalized_attention=attention_state,
        recovery_assessment=assessment_state,
    )
    if warning:
        warnings.append(warning)
    reviewer_runtime_state = reviewer_runtime_state_from_payload(
        reviewer_runtime=_mapping(review_payload.get("reviewer_runtime")),
        bridge=bridge,
        bridge_liveness=bridge_liveness,
        current_session=current_session_state,
        attention=attention,
        recovery_assessment=recovery_assessment,
    )
    review_candidate = review_candidate_from_mapping(
        review_payload.get("review_candidate")
    )
    push_authorization = (
        push_authorization_from_mapping(
            _mapping(review_payload.get("push_authorization"))
            or _mapping(payload.get("push_authorization"))
        )
        or commit_pipeline.push_authorization
    )
    coordination = (
        coordination_snapshot_from_mapping(review_payload.get("coordination"))
        or coordination_snapshot_from_mapping(payload.get("coordination"))
    )

    return ReviewState(
        schema_version=_int(payload.get("schema_version"))
        or _int(review_payload.get("schema_version"))
        or 1,
        contract_id="ReviewState",
        command=_string(payload.get("command"))
        or _string(review_payload.get("command"))
        or "review-channel",
        action=_string(payload.get("action")) or "status",
        timestamp=_string(payload.get("timestamp"))
        or _string(review_payload.get("timestamp")),
        ok=(
            _bool(payload.get("ok"))
            if "ok" in payload
            else _bool(review_payload.get("ok"))
            if "ok" in review_payload
            else not errors
        ),
        review=_review_session_state(review),
        queue=_review_queue_state(queue),
        current_session=current_session_state,
        packet_inbox=packet_inbox,
        collaboration=collaboration_state,
        bridge=bridge_state,
        attention=attention_state,
        recovery_assessment=assessment_state,
        packets=_packet_states_from_value(review_payload.get("packets")),
        registry=registry_state,
        review_candidate=review_candidate,
        push_authorization=push_authorization,
        reviewer_runtime=reviewer_runtime_state,
        commit_pipeline=commit_pipeline,
        coordination=coordination,
        authority_snapshot=(
            authority_snapshot_from_mapping(payload.get("authority_snapshot"))
            or authority_snapshot_from_mapping(
                review_payload.get("authority_snapshot")
            )
        ),
        warnings=tuple(warnings),
        errors=errors,
        snapshot_id=_string(payload.get("snapshot_id"))
        or _string(review_payload.get("snapshot_id"))
        or _string(_mapping(review_payload.get("commit_pipeline")).get("snapshot_id")),
    )


def _review_state_packet_inbox(
    *,
    payload: Mapping[str, object],
    review_payload: Mapping[str, object],
    attention: Mapping[str, object],
):
    packet_inbox = _mapping(payload.get("packet_inbox")) or _mapping(
        review_payload.get("packet_inbox")
    )
    return (
        packet_inbox_from_mapping(packet_inbox)
        or packet_inbox_from_mapping(
            build_packet_inbox_payload(
                review_payload.get("packets"),
                attention=attention,
            )
        )
        or packet_inbox_from_mapping({"attention_revision": "", "agents": []})
    )


def _review_session_state(review: Mapping[str, object]) -> ReviewSessionState:
    return ReviewSessionState(
        plan_id=_string(review.get("plan_id")),
        controller_run_id=_string(review.get("controller_run_id")),
        session_id=_string(review.get("session_id")) or "markdown-bridge",
        surface_mode=_string(review.get("surface_mode")) or "markdown-bridge",
        active_lane=_string(review.get("active_lane")) or "review",
        refresh_seq=_int(review.get("refresh_seq")),
        bridge_path=_string(review.get("bridge_path")),
        review_channel_path=_string(review.get("review_channel_path")),
    )


def _review_queue_state(queue: Mapping[str, object]) -> ReviewQueueState:
    return ReviewQueueState(
        pending_total=_int(queue.get("pending_total")),
        pending_codex=_int(queue.get("pending_codex")),
        pending_claude=_int(queue.get("pending_claude")),
        pending_cursor=_int(queue.get("pending_cursor")),
        pending_operator=_int(queue.get("pending_operator")),
        stale_packet_count=_int(queue.get("stale_packet_count")),
        derived_next_instruction=_string(queue.get("derived_next_instruction")),
        derived_next_instruction_source=dict(
            _mapping(queue.get("derived_next_instruction_source"))
        ),
    )


def _review_state_envelope(
    payload: Mapping[str, object],
) -> tuple[
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
    list[str],
    tuple[str, ...],
] | None:
    review_payload = _mapping(payload.get("review_state"))
    if not review_payload and any(
        key in payload for key in ("review", "queue", "bridge", "packets", "agents")
    ):
        review_payload = payload
    if not review_payload:
        return None
    registry_payload = (
        _mapping(payload.get("agent_registry"))
        or _mapping(payload.get("registry"))
        or _mapping(review_payload.get("agent_registry"))
        or _mapping(review_payload.get("registry"))
    )
    attention = _mapping(payload.get("attention")) or _mapping(
        review_payload.get("attention")
    )
    recovery_assessment = _mapping(payload.get("recovery_assessment")) or _mapping(
        review_payload.get("recovery_assessment")
    )
    bridge_liveness = _mapping(payload.get("bridge_liveness")) or _mapping(
        review_payload.get("bridge_liveness")
    )
    warnings = list(
        _string_rows(payload.get("warnings"))
        or _string_rows(review_payload.get("warnings"))
    )
    errors = _string_rows(payload.get("errors")) or _string_rows(
        review_payload.get("errors")
    )
    return (
        review_payload,
        registry_payload,
        attention,
        recovery_assessment,
        bridge_liveness,
        warnings,
        errors,
    )
