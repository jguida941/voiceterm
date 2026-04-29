"""Session-resume cache packet construction helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ...platform.coordination_snapshot_models import CoordinationSnapshot
from ...runtime.agent_session_continuation_models import AgentSessionContinuationState
from ...runtime.authority_snapshot import AuthoritySnapshot
from ...runtime.control_plane_read_model import ControlPlaneReadModel
from ...runtime.review_state_models import PacketInboxState, ReviewCandidateRecord
from ...runtime.packet_intent_anchor import packet_intent_anchors_from_packets
from ...runtime.surface_provenance import surface_provenance_from_object
from ...time_utils import utc_timestamp
from .session_resume_packet import SessionCachePacket

if TYPE_CHECKING:
    from ...runtime.review_state_models import ReviewState


@dataclass(frozen=True, slots=True)
class SessionCachePacketFields:
    ack_state: str
    blockers: str
    current_instruction: str
    guard_bundle: str
    head_at_push_time: str
    instruction_revision: str
    key_rules: tuple[str, ...]
    last_reviewed_sha: str
    next_cmd: str
    observation_status: str
    open_findings: str
    review_state_mtime: float
    top_blocker: str
    visible_next_cmd: str


@dataclass(frozen=True, slots=True)
class SessionCachePacketBuildContext:
    role: str
    head_sha: str
    typed_review_state: "ReviewState | None"
    coordination: CoordinationSnapshot | None
    authority_snapshot: AuthoritySnapshot | None
    review_candidate: ReviewCandidateRecord | None
    attention_payload: dict[str, Any]
    packet_inbox: PacketInboxState | None
    connectivity_registry: dict[str, object]
    key_surfaces: tuple[str, ...]
    agent_session_continuation: AgentSessionContinuationState | None
    fields: SessionCachePacketFields


def build_session_cache_packet(
    *,
    model: ControlPlaneReadModel,
    build_context: SessionCachePacketBuildContext,
) -> SessionCachePacket:
    fields = build_context.fields
    typed_review_state = build_context.typed_review_state
    snapshot_id = (
        getattr(typed_review_state, "snapshot_id", "")
        if typed_review_state is not None
        else ""
    )
    zref = (
        getattr(typed_review_state, "zref", "")
        if typed_review_state is not None
        else ""
    )
    provenance = (
        surface_provenance_from_object(typed_review_state)
        if typed_review_state is not None
        else None
    )
    visible_next_cmd = fields.visible_next_cmd
    next_cmd = fields.next_cmd
    return SessionCachePacket(
        generated_at_utc=utc_timestamp(),
        role=build_context.role,
        branch=model.branch,
        head_sha=build_context.head_sha,
        snapshot_id=snapshot_id,
        zref=zref,
        advisory_action=model.next_action,
        advisory_reason=fields.top_blocker,
        blockers=fields.blockers,
        interaction_mode=model.operator_interaction_mode,
        current_instruction=fields.current_instruction,
        instruction_revision=fields.instruction_revision,
        ack_state=fields.ack_state,
        open_findings=fields.open_findings,
        last_guard_ok=model.last_guard_ok,
        last_reviewed_sha=fields.last_reviewed_sha,
        review_state_mtime=fields.review_state_mtime,
        done_summary=next_cmd,
        next_action=visible_next_cmd,
        key_rules=fields.key_rules,
        head_at_push_time=fields.head_at_push_time,
        operator_interaction_mode=model.operator_interaction_mode,
        resolved_phase=model.resolved_phase,
        next_guard_bundle=fields.guard_bundle,
        next_recommended_command=visible_next_cmd,
        reviewer_observation_status=fields.observation_status,
        review_candidate=build_context.review_candidate,
        remote_control_attachment=getattr(model, "remote_control_attachment", None),
        session_posture=getattr(model, "session_posture", None),
        coordination=build_context.coordination,
        authority_snapshot=build_context.authority_snapshot,
        attention_status=_str_field(build_context.attention_payload, "status")
        or model.attention_status,
        attention_summary=_str_field(build_context.attention_payload, "summary")
        or model.attention_summary,
        attention_revision=(
            build_context.packet_inbox.attention_revision
            if build_context.packet_inbox is not None
            else ""
        ),
        packet_inbox=build_context.packet_inbox,
        packet_intent_anchors=packet_intent_anchors_from_packets(
            getattr(typed_review_state, "packets", ()) if typed_review_state else ()
        ),
        connectivity_registry=build_context.connectivity_registry,
        key_surfaces=build_context.key_surfaces,
        agent_session_continuation=build_context.agent_session_continuation,
        provenance=provenance,
    )


def _str_field(mapping: dict[str, Any], key: str) -> str:
    return str((mapping or {}).get(key) or "").strip()
