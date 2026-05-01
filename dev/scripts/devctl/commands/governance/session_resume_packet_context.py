"""Build SessionCachePacket from resolved session-resume context."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...runtime.control_plane_read_model import ControlPlaneReadModel
from .session_resume_cache_packet_builder import (
    SessionCachePacketBuildContext,
    SessionCachePacketFields,
    build_session_cache_packet,
)
from .session_resume_continuation import build_agent_session_continuation_for_resume
from .session_resume_context_values import replace_context_values
from .session_resume_packet import SessionCachePacket

if TYPE_CHECKING:
    from ...runtime.review_state_models import ReviewState


@dataclass(frozen=True)
class ResolvedPacketBuildContext:
    repo_root: Path
    role: str
    model: ControlPlaneReadModel
    head_sha: str
    typed_review_state: "ReviewState | None"
    authority_snapshot: object
    packet_inbox: object
    resolved_context: dict[str, Any]


def build_packet_from_resolved_context(
    context: ResolvedPacketBuildContext | None = None,
    **values: object,
) -> SessionCachePacket:
    """Build a session packet from a resolved context.

    When both ``context`` and keyword values are supplied, keyword values
    override the context. Unknown keyword fields fail closed before packet
    construction.
    """
    context = replace_context_values(
        context,
        values,
        context_type=ResolvedPacketBuildContext,
        label="session packet",
    )
    resolved_context = context.resolved_context
    changed_paths = resolved_context.get("changed_paths")
    continuation = build_agent_session_continuation_for_resume(
        repo_root=context.repo_root,
        role=context.role,
        branch=context.model.branch,
        authority_snapshot=context.authority_snapshot,
        packet_inbox=context.packet_inbox,
        typed_review_state=context.typed_review_state,
        current_instruction=str(resolved_context["current_instruction"]),
        blockers=str(resolved_context["blockers"]),
        changed_paths=changed_paths if isinstance(changed_paths, list) else None,
    )
    return build_session_cache_packet(
        model=context.model,
        build_context=SessionCachePacketBuildContext(
            role=context.role,
            head_sha=context.head_sha,
            typed_review_state=context.typed_review_state,
            coordination=resolved_context["coordination"],
            authority_snapshot=context.authority_snapshot,
            review_candidate=resolved_context["review_candidate"],
            attention_payload=resolved_context["attention_payload"],
            packet_inbox=context.packet_inbox,
            connectivity_registry=resolved_context["connectivity_registry"],
            runtime_spine_closure=dict(
                resolved_context.get("runtime_spine_closure") or {}
            ),
            packet_continuity_index=dict(
                resolved_context.get("packet_continuity_index") or {}
            ),
            packet_carry_forward_debt=tuple(
                resolved_context.get("packet_carry_forward_debt") or ()
            ),
            continuity_attention=dict(
                resolved_context.get("continuity_attention") or {}
            ),
            key_surfaces=resolved_context["key_surfaces"],
            agent_session_continuation=continuation,
            fields=packet_fields_from_context(resolved_context),
        ),
    )


def packet_fields_from_context(context: dict[str, Any]) -> SessionCachePacketFields:
    return SessionCachePacketFields(
        ack_state=str(context["ack_state"]),
        blockers=str(context["blockers"]),
        current_instruction=str(context["current_instruction"]),
        guard_bundle=str(context["guard_bundle"]),
        head_at_push_time=str(context["head_at_push_time"]),
        instruction_revision=str(context["instruction_revision"]),
        key_rules=tuple(context["key_rules"]),
        last_reviewed_sha=str(context["last_reviewed_sha"]),
        next_cmd=str(context["next_cmd"]),
        observation_status=str(context["obs_status"]),
        open_findings=str(context["open_findings"]),
        review_state_mtime=float(context["rs_mtime"]),
        top_blocker=str(context["top_blocker"]),
        visible_next_cmd=str(context["visible_next_cmd"]),
    )


__all__ = [
    "ResolvedPacketBuildContext",
    "build_packet_from_resolved_context",
    "packet_fields_from_context",
]
