"""Parsers that normalize review-channel artifacts into typed runtime state."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .control_state import _int, _mapping, _string, _string_rows
from .review_state_models import (
    AgentRegistryEntryState,
    AgentRegistryState,
    ContextPackRefState,
    ReviewAttentionState,
    ReviewBridgeState,
    ReviewCurrentSessionState,
    ReviewPacketState,
    ReviewQueueState,
    ReviewSessionState,
    ReviewState,
)
from .review_state_semantics import is_pending_implementer_state


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def review_state_from_payload(payload: Mapping[str, object]) -> ReviewState | None:
    """Normalize review-state or full projection payloads into a shared contract."""
    review_payload = _mapping(payload.get("review_state"))
    if not review_payload and any(
        key in payload for key in ("review", "queue", "bridge", "packets", "agents")
    ):
        review_payload = payload
    if not review_payload:
        return None

    registry_payload = _mapping(payload.get("agent_registry")) or _mapping(
        review_payload.get("agent_registry")
    )
    attention = _mapping(payload.get("attention")) or _mapping(
        review_payload.get("attention")
    )
    bridge_liveness = _mapping(payload.get("bridge_liveness")) or _mapping(
        review_payload.get("bridge_liveness")
    )
    warnings = _string_rows(payload.get("warnings")) or _string_rows(
        review_payload.get("warnings")
    )
    errors = _string_rows(payload.get("errors")) or _string_rows(
        review_payload.get("errors")
    )

    review = _mapping(review_payload.get("review"))
    queue = _mapping(review_payload.get("queue"))
    bridge = _mapping(review_payload.get("bridge"))
    current_session = _mapping(review_payload.get("current_session"))

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
        review=ReviewSessionState(
            plan_id=_string(review.get("plan_id")),
            controller_run_id=_string(review.get("controller_run_id")),
            session_id=_string(review.get("session_id")) or "markdown-bridge",
            surface_mode=_string(review.get("surface_mode")) or "markdown-bridge",
            active_lane=_string(review.get("active_lane")) or "review",
            refresh_seq=_int(review.get("refresh_seq")),
            bridge_path=_string(review.get("bridge_path")),
            review_channel_path=_string(review.get("review_channel_path")),
        ),
        queue=ReviewQueueState(
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
        ),
        current_session=_current_session_state_from_payload(
            current_session=current_session,
            bridge=bridge,
        ),
        bridge=ReviewBridgeState(
            overall_state=_string(bridge_liveness.get("overall_state")) or "unknown",
            codex_poll_state=_string(bridge_liveness.get("codex_poll_state"))
            or "unknown",
            reviewer_freshness=_string(bridge_liveness.get("reviewer_freshness"))
            or "unknown",
            reviewer_mode=_string(bridge.get("reviewer_mode")) or "single_agent",
            last_codex_poll_utc=_string(bridge.get("last_codex_poll_utc")),
            last_codex_poll_age_seconds=_int(
                bridge_liveness.get("last_codex_poll_age_seconds")
            ),
            last_worktree_hash=_string(bridge.get("last_worktree_hash")),
            current_instruction=_string(bridge.get("current_instruction")),
            open_findings=_string(bridge.get("open_findings")),
            claude_status=_string(bridge.get("claude_status")),
            claude_ack=_string(bridge.get("claude_ack")),
            claude_ack_current=_bool(bridge.get("claude_ack_current")),
            current_instruction_revision=_string(
                bridge.get("current_instruction_revision")
            ),
            claude_ack_revision=_string(bridge.get("claude_ack_revision")),
            last_reviewed_scope=_string(bridge.get("last_reviewed_scope")),
            reviewed_hash_current=(
                _bool(bridge.get("reviewed_hash_current"))
                if "reviewed_hash_current" in bridge
                else None
            ),
            review_needed=(
                _bool(bridge.get("review_needed"))
                if "review_needed" in bridge
                else None
            ),
            review_accepted=_bool(bridge.get("review_accepted")),
            implementer_completion_stall=bool(bridge.get("implementer_completion_stall")),
            publisher_running=bool(bridge.get("publisher_running")),
        ),
        attention=_attention_state_from_mapping(attention),
        packets=_packet_states_from_value(review_payload.get("packets")),
        registry=AgentRegistryState(
            timestamp=_string(registry_payload.get("timestamp"))
            or _string(registry_payload.get("updated_at")),
            agents=_registry_agents_from_value(registry_payload.get("agents")),
        ),
        warnings=warnings,
        errors=errors,
    )


def _current_session_state_from_payload(
    *,
    current_session: Mapping[str, object],
    bridge: Mapping[str, object],
) -> ReviewCurrentSessionState:
    if current_session:
        return ReviewCurrentSessionState(
            current_instruction=_string(current_session.get("current_instruction")),
            current_instruction_revision=_string(
                current_session.get("current_instruction_revision")
            ),
            implementer_status=_string(current_session.get("implementer_status")),
            implementer_ack=_string(current_session.get("implementer_ack")),
            implementer_ack_revision=_string(
                current_session.get("implementer_ack_revision")
            ),
            implementer_ack_state=_string(
                current_session.get("implementer_ack_state")
            )
            or "unknown",
            implementer_session_state=_string(
                current_session.get("implementer_session_state")
            ),
            implementer_session_hint=_string(
                current_session.get("implementer_session_hint")
            ),
            open_findings=_string(current_session.get("open_findings")),
            last_reviewed_scope=_string(current_session.get("last_reviewed_scope")),
        )

    implementer_ack = _string(bridge.get("claude_ack"))
    return ReviewCurrentSessionState(
        current_instruction=_string(bridge.get("current_instruction")),
        current_instruction_revision=_string(bridge.get("current_instruction_revision")),
        implementer_status=_string(bridge.get("claude_status")),
        implementer_ack=implementer_ack,
        implementer_ack_revision=_string(bridge.get("claude_ack_revision")),
        implementer_ack_state=_bridge_ack_state(bridge, implementer_ack),
        implementer_session_state="",
        implementer_session_hint="",
        open_findings=_string(bridge.get("open_findings")),
        last_reviewed_scope=_string(bridge.get("last_reviewed_scope")),
    )


def _bridge_ack_state(bridge: Mapping[str, object], implementer_ack: str) -> str:
    if is_pending_implementer_state(
        implementer_status=_string(bridge.get("claude_status")),
        implementer_ack=implementer_ack,
    ):
        return "pending"
    if not implementer_ack:
        return "missing"
    if _bool(bridge.get("claude_ack_current")):
        return "current"
    return "stale"


def _attention_state_from_mapping(
    mapping: Mapping[str, object],
) -> ReviewAttentionState | None:
    if not mapping:
        return None
    return ReviewAttentionState(
        status=_string(mapping.get("status")) or "unknown",
        owner=_string(mapping.get("owner")) or "system",
        summary=_string(mapping.get("summary")),
        recommended_action=_string(mapping.get("recommended_action")),
        recommended_command=_string(mapping.get("recommended_command")),
    )


def _packet_states_from_value(value: object) -> tuple[ReviewPacketState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    packets: list[ReviewPacketState] = []
    for row in value:
        mapping = _mapping(row)
        packet_id = _string(mapping.get("packet_id"))
        if not packet_id:
            continue
        try:
            confidence = float(mapping.get("confidence"))
        except (TypeError, ValueError):
            confidence = 0.0
        packets.append(
            ReviewPacketState(
                packet_id=packet_id,
                kind=_string(mapping.get("kind")) or "system_notice",
                from_agent=_string(mapping.get("from_agent")) or "system",
                to_agent=_string(mapping.get("to_agent")) or "operator",
                summary=_string(mapping.get("summary")),
                body=_string(mapping.get("body")),
                status=_string(mapping.get("status")) or "posted",
                policy_hint=_string(mapping.get("policy_hint")),
                requested_action=_string(mapping.get("requested_action")),
                approval_required=_bool(mapping.get("approval_required")),
                posted_at=(
                    _string(mapping.get("posted_at"))
                    or _string(mapping.get("timestamp_utc"))
                    or _string(mapping.get("acked_at_utc"))
                    or _string(mapping.get("applied_at_utc"))
                    or _string(mapping.get("_sort_timestamp"))
                ),
                evidence_refs=_string_rows(mapping.get("evidence_refs")),
                context_pack_refs=_context_pack_refs_from_value(
                    mapping.get("context_pack_refs")
                ),
                trace_id=_string(mapping.get("trace_id")),
                latest_event_id=_string(mapping.get("latest_event_id")),
                confidence=confidence,
                guidance_refs=_string_rows(mapping.get("guidance_refs")),
                target_kind=_string(mapping.get("target_kind")),
                target_ref=_string(mapping.get("target_ref")),
                target_revision=_string(mapping.get("target_revision")),
                anchor_refs=_string_rows(mapping.get("anchor_refs")),
                intake_ref=_string(mapping.get("intake_ref")),
                mutation_op=_string(mapping.get("mutation_op")),
                acked_by=_string(mapping.get("acked_by")),
                acked_at_utc=_string(mapping.get("acked_at_utc")),
                applied_at_utc=_string(mapping.get("applied_at_utc")),
                expires_at_utc=_string(mapping.get("expires_at_utc")),
            )
        )
    return tuple(packets)


def _context_pack_refs_from_value(value: object) -> tuple[ContextPackRefState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    refs: list[ContextPackRefState] = []
    for row in value:
        mapping = _mapping(row)
        pack_kind = _string(mapping.get("pack_kind"))
        pack_ref = _string(mapping.get("pack_ref"))
        if not pack_kind or not pack_ref:
            continue
        refs.append(
            ContextPackRefState(
                pack_kind=pack_kind,
                pack_ref=pack_ref,
                adapter_profile=_string(mapping.get("adapter_profile")),
                generated_at_utc=_string(mapping.get("generated_at_utc")),
            )
        )
    return tuple(refs)


def _registry_agents_from_value(
    value: object,
) -> tuple[AgentRegistryEntryState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    agents: list[AgentRegistryEntryState] = []
    for row in value:
        mapping = _mapping(row)
        agent_id = _string(mapping.get("agent_id"))
        if not agent_id:
            continue
        agents.append(
            AgentRegistryEntryState(
                agent_id=agent_id,
                provider=_string(mapping.get("provider")),
                display_name=_string(mapping.get("display_name")) or agent_id,
                lane=_string(mapping.get("lane")),
                lane_title=_string(mapping.get("lane_title")),
                current_job=_string(mapping.get("current_job")),
                job_state=_string(mapping.get("job_state")) or "unknown",
                waiting_on=_string(mapping.get("waiting_on")),
                last_packet_seen=_string(mapping.get("last_packet_seen")),
                last_packet_applied=_string(mapping.get("last_packet_applied")),
                script_profile=_string(mapping.get("script_profile")),
                mp_scope=_string(mapping.get("mp_scope")),
                worktree=_string(mapping.get("worktree")),
                branch=_string(mapping.get("branch")),
                updated_at=_string(mapping.get("updated_at")),
            )
        )
    return tuple(agents)
