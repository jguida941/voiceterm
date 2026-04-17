"""Row-level helpers for review-state parser normalization."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from hashlib import sha256

from .control_state import _mapping, _string, _string_rows
from .review_state_semantics import (
    is_missing_instruction,
    normalize_instruction_markdown,
)
from .review_state_models import (
    AgentRegistryEntryState,
    ContextPackRefState,
    ReviewCurrentSessionState,
    ReviewPacketState,
)
from .review_state_parse_support import _bool, bridge_ack_state


def current_session_state_from_payload(
    *,
    current_session: Mapping[str, object],
    bridge: Mapping[str, object],
) -> ReviewCurrentSessionState:
    if current_session:
        current_instruction, current_instruction_revision = (
            canonicalize_current_instruction_state(
                _string(current_session.get("current_instruction")),
                _string(current_session.get("current_instruction_revision")),
            )
        )
        return ReviewCurrentSessionState(
            current_instruction=current_instruction,
            current_instruction_revision=current_instruction_revision,
            implementer_status=_string(current_session.get("implementer_status")),
            implementer_ack=_string(current_session.get("implementer_ack")),
            implementer_ack_revision=_string(
                current_session.get("implementer_ack_revision")
            ),
            implementer_ack_state=_string(
                current_session.get("implementer_ack_state")
            )
            or "unknown",
            implementer_state_hash=_string(
                current_session.get("implementer_state_hash")
            ),
            implementer_session_state=_string(
                current_session.get("implementer_session_state")
            ),
            implementer_session_hint=_string(
                current_session.get("implementer_session_hint")
            ),
            open_findings=_string(current_session.get("open_findings")),
            last_reviewed_scope=_string(current_session.get("last_reviewed_scope")),
        )
    return ReviewCurrentSessionState(
        current_instruction="",
        current_instruction_revision="",
        implementer_status="",
        implementer_ack="",
        implementer_ack_revision="",
        implementer_ack_state="missing",
        implementer_state_hash="",
        implementer_session_state="",
        implementer_session_hint="",
        open_findings="",
        last_reviewed_scope="",
    )


def canonicalize_current_instruction_state(
    current_instruction: str,
    current_instruction_revision: str,
) -> tuple[str, str]:
    canonical_instruction = canonical_instruction_markdown(current_instruction)
    if is_missing_instruction(canonical_instruction):
        return canonical_instruction, ""
    revision = _string(current_instruction_revision)
    if canonical_instruction != current_instruction:
        raw_revision = instruction_revision(current_instruction)
        if not revision or revision == raw_revision:
            revision = instruction_revision(canonical_instruction)
    elif not revision and canonical_instruction:
        revision = instruction_revision(canonical_instruction)
    return canonical_instruction, revision


def canonical_instruction_markdown(current_instruction: str) -> str:
    return normalize_instruction_markdown(_string(current_instruction))


def instruction_revision(text: str) -> str:
    normalized = _string(text).strip()
    if is_missing_instruction(normalized):
        return ""
    return sha256(normalized.encode("utf-8")).hexdigest()[:12]


def packet_states_from_value(value: object) -> tuple[ReviewPacketState, ...]:
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
                context_pack_refs=context_pack_refs_from_value(
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
                pipeline_generation=_string(mapping.get("pipeline_generation")),
                staged_snapshot_hash=_string(mapping.get("staged_snapshot_hash")),
                guard_results_summary=_string(mapping.get("guard_results_summary")),
                acked_by=_string(mapping.get("acked_by")),
                acked_at_utc=_string(mapping.get("acked_at_utc")),
                applied_at_utc=_string(mapping.get("applied_at_utc")),
                delivery_emitted_at_utc=_string(
                    mapping.get("delivery_emitted_at_utc")
                ),
                delivery_observed_at_utc=_string(
                    mapping.get("delivery_observed_at_utc")
                ),
                delivery_observed_by=_string(mapping.get("delivery_observed_by")),
                execution_started_at_utc=_string(
                    mapping.get("execution_started_at_utc")
                ),
                execution_started_by=_string(mapping.get("execution_started_by")),
                expires_at_utc=_string(mapping.get("expires_at_utc")),
            )
        )
    return tuple(packets)


def context_pack_refs_from_value(value: object) -> tuple[ContextPackRefState, ...]:
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


def registry_agents_from_value(
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
