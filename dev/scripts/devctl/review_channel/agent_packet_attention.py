"""Actor-scoped packet attention projection for agent-loop consumers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..runtime.reviewer_runtime_models import (
    PacketAttentionState,
    build_packet_attention_state,
)
from ..runtime.packet_absorption_resolution import (
    packet_has_effective_durable_binding,
    packet_requires_durable_binding,
)
from ..runtime.value_coercion import coerce_text as _text
from .active_packet_authority import current_active_packet_for_agent
from .agent_packet_attention_body import (
    packet_absorption_command,
    packet_body_open_command,
    packet_semantic_ingestion_command,
)
from .agent_packet_attention_priority import (
    best_attention_packet,
    best_body_open_packet,
    body_open_packets,
    latest_event_id as select_latest_event_id,
)
from .agent_packet_attention_scope import (
    active_packet_visible_to_route,
    pending_packets_for_scope,
)
from .agent_packet_focus import packet_by_id
from .agent_sync_readers import (
    agent_sync_pending_packet_count_from_row,
    agent_sync_row_for_actor,
)
from .packet_contract import normalize_packet_route_role
from .packet_loop_attention import (
    packet_absorption_required,
    packet_semantic_ingestion_required,
)


@dataclass(frozen=True, slots=True)
class _AttentionBuildInput:
    actor: str
    role: str
    session: str
    attention_packet: Mapping[str, object]
    pending_packets: tuple[Mapping[str, object], ...]
    fallback: Mapping[str, object]
    agent_sync: Mapping[str, object]
    packet_rows_authoritative: bool


def packet_attention_for_agent(
    review_state: Mapping[str, object],
    *,
    actor: str,
    role: str = "",
    session: str = "",
    fallback_attention: Mapping[str, object] | None = None,
) -> PacketAttentionState:
    """Return packet-attention state scoped to one requested actor."""
    actor_id = _text(actor)
    role_id = normalize_packet_route_role(role)
    session_id = _text(session)
    fallback = _matching_fallback_attention(
        fallback_attention,
        actor=actor_id,
        session=session_id,
    )
    if not actor_id:
        return _fallback_attention(session_id=session_id, fallback=fallback)

    packet_rows = _packet_rows(review_state)
    packet_rows_authoritative = isinstance(review_state.get("packets"), (list, tuple))
    pending_packets = pending_packets_for_scope(
        packet_rows,
        actor=actor_id,
        role=role_id,
        session=session_id,
    )
    active_packet = _active_packet_for_scope(
        review_state,
        actor=actor_id,
        role=role_id,
        session=session_id,
    )
    if not active_packet_visible_to_route(
        active_packet,
        actor=actor_id,
        role=role_id,
        session=session_id,
    ):
        active_packet = {}
    attention_packet = best_attention_packet(
        active_packet=active_packet,
        pending_packets=pending_packets,
    )
    return _build_attention(
        _AttentionBuildInput(
            actor=actor_id,
            role=role_id,
            session=session_id,
            attention_packet=attention_packet,
            pending_packets=pending_packets,
            fallback=fallback,
            agent_sync=agent_sync_row_for_actor(review_state, actor_id),
            packet_rows_authoritative=packet_rows_authoritative,
        )
    )


def _fallback_attention(
    *,
    session_id: str,
    fallback: Mapping[str, object],
) -> PacketAttentionState:
    absorption_required = bool(fallback.get("absorption_required"))
    semantic_ingestion_required = bool(fallback.get("semantic_ingestion_required"))
    body_open_required = bool(fallback.get("body_open_required")) and not (
        semantic_ingestion_required or absorption_required
    )
    return build_packet_attention_state(
        observation_actor_id="",
        observation_session_id=session_id,
        latest_inbox_event_id=_text(fallback.get("latest_inbox_event_id")),
        latest_attention_packet_id=_text(fallback.get("latest_attention_packet_id")),
        latest_attention_changed_at_utc=_text(
            fallback.get("latest_attention_changed_at_utc")
        ),
        last_observed_event_id=_text(fallback.get("last_observed_event_id")),
        last_observed_at_utc=_text(fallback.get("last_observed_at_utc")),
        pending_packet_count=int(fallback.get("pending_packet_count") or 0),
        unopened_body_packet_ids=tuple(
            _text(row)
            for row in (fallback.get("unopened_body_packet_ids") or ())
            if _text(row)
        ),
        body_open_packet_id=_text(fallback.get("body_open_packet_id")),
        body_open_command=_text(fallback.get("body_open_command"))
        if body_open_required
        else "",
        semantic_ingestion_required=semantic_ingestion_required,
        semantic_ingestion_packet_id=_text(
            fallback.get("semantic_ingestion_packet_id")
        ),
        semantic_ingestion_command=_text(fallback.get("semantic_ingestion_command"))
        if semantic_ingestion_required and not absorption_required
        else "",
        semantic_ingestion_reason=_text(fallback.get("semantic_ingestion_reason")),
        absorption_required=absorption_required,
        absorption_packet_id=_text(fallback.get("absorption_packet_id")),
        absorption_command=_text(fallback.get("absorption_command"))
        if absorption_required
        else "",
        absorption_reason=_text(fallback.get("absorption_reason")),
        superseded_packet_id=_text(fallback.get("superseded_packet_id")),
    )


def _active_packet_for_scope(
    review_state: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
) -> Mapping[str, object]:
    packet_id = current_active_packet_for_agent(
        review_state,
        actor,
        target_role=role,
        target_session_id=session,
    )
    return packet_by_id(review_state, packet_id)


def _build_attention(context: _AttentionBuildInput) -> PacketAttentionState:
    fallback = context.fallback
    attention_packet = context.attention_packet
    body_open_packet_rows = body_open_packets(
        context.pending_packets,
        actor=context.actor,
        role=context.role,
        session=context.session,
    )
    body_open_packet = best_body_open_packet(body_open_packet_rows)
    selected_packet = body_open_packet or attention_packet
    agent_sync = context.agent_sync
    last_observed = (
        _text(fallback.get("last_observed_event_id"))
        or _text(agent_sync.get("last_consumed_event_id_lower_bound"))
    )
    if context.packet_rows_authoritative:
        latest_inbox_event_id = _text(selected_packet.get("latest_event_id"))
        latest_attention_packet_id = _text(selected_packet.get("packet_id"))
        pending_packet_count = len(context.pending_packets)
        fallback_attention_changed_at = ""
        superseded_packet_id = ""
    else:
        latest_inbox_event_id = select_latest_event_id(
            _text(selected_packet.get("latest_event_id")),
            _text(fallback.get("latest_inbox_event_id")),
        )
        latest_attention_packet_id = _text(selected_packet.get("packet_id")) or _text(
            fallback.get("latest_attention_packet_id")
        )
        pending_packet_count = len(
            context.pending_packets
        ) or agent_sync_pending_packet_count_from_row(agent_sync)
        fallback_attention_changed_at = _text(
            fallback.get("latest_attention_changed_at_utc")
        )
        superseded_packet_id = _text(fallback.get("superseded_packet_id"))
    body_open_packet_id = _text(body_open_packet.get("packet_id"))
    unopened_body_packet_ids = tuple(
        _text(packet.get("packet_id"))
            for packet in body_open_packet_rows
        if _text(packet.get("packet_id"))
    )
    semantic_ingestion_required = bool(
        body_open_packet_id
        and packet_semantic_ingestion_required(
            body_open_packet,
            actor=context.actor,
            role=context.role,
            session=context.session,
        )
    )
    absorption_required = bool(
        body_open_packet_id
        and packet_absorption_required(
            body_open_packet,
            actor=context.actor,
            role=context.role,
            session=context.session,
        )
    )
    body_open_required = bool(
        body_open_packet_id
        and not semantic_ingestion_required
        and not absorption_required
    )
    body_open_command = (
        packet_body_open_command(
            packet_id=body_open_packet_id,
            actor=context.actor,
            role=context.role,
            session=context.session,
        )
        if body_open_required
        else ""
    )
    semantic_ingestion_command = (
        packet_semantic_ingestion_command(
            packet_id=body_open_packet_id,
            actor=context.actor,
            role=context.role,
            session=context.session,
            action_item_rows=_semantic_action_item_rows(body_open_packet),
        )
        if semantic_ingestion_required and not absorption_required
        else ""
    )
    absorption_command = (
        packet_absorption_command(
            packet_id=body_open_packet_id,
            actor=context.actor,
            role=context.role,
            session=context.session,
        )
        if absorption_required
        else ""
    )
    absorption_reason = (
        "packet_semantically_ingested_without_absorption"
        if absorption_required
        else ""
    )
    if (
        not context.packet_rows_authoritative
        and not body_open_packet_id
        and bool(fallback.get("body_open_required"))
    ):
        body_open_packet_id = _text(fallback.get("body_open_packet_id"))
        unopened_body_packet_ids = _fallback_unopened_body_packet_ids(
            fallback,
            body_open_packet_id=body_open_packet_id,
        )
        body_open_command = _text(fallback.get("body_open_command")) or (
            packet_body_open_command(
                packet_id=body_open_packet_id,
                actor=context.actor,
                role=context.role,
                session=context.session,
            )
        )
    return build_packet_attention_state(
        observation_actor_id=context.actor,
        observation_session_id=context.session,
        latest_inbox_event_id=latest_inbox_event_id,
        latest_attention_packet_id=latest_attention_packet_id,
        latest_attention_changed_at_utc=(
            _text(selected_packet.get("posted_at"))
            or _text(selected_packet.get("latest_event_at_utc"))
            or fallback_attention_changed_at
        ),
        last_observed_event_id=last_observed,
        last_observed_at_utc=_text(fallback.get("last_observed_at_utc")),
        pending_packet_count=pending_packet_count,
        unopened_body_packet_ids=(
            ()
            if semantic_ingestion_required or absorption_required
            else unopened_body_packet_ids
        ),
        body_open_packet_id=body_open_packet_id,
        body_open_command=body_open_command,
        semantic_ingestion_required=(
            semantic_ingestion_required and not absorption_required
        ),
        semantic_ingestion_packet_id=(
            body_open_packet_id
            if semantic_ingestion_required and not absorption_required
            else ""
        ),
        semantic_ingestion_command=semantic_ingestion_command,
        semantic_ingestion_reason=(
            "packet_body_observed_without_semantic_ingestion"
            if semantic_ingestion_required and not absorption_required
            else ""
        ),
        absorption_required=absorption_required,
        absorption_packet_id=body_open_packet_id if absorption_required else "",
        absorption_command=absorption_command,
        absorption_reason=absorption_reason,
        superseded_packet_id=superseded_packet_id,
    )


def _packet_rows(review_state: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    packets = review_state.get("packets")
    if not isinstance(packets, (list, tuple)):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, Mapping))


def _fallback_unopened_body_packet_ids(
    fallback: Mapping[str, object],
    *,
    body_open_packet_id: str,
) -> tuple[str, ...]:
    raw = fallback.get("unopened_body_packet_ids") or ()
    rows = tuple(_text(row) for row in raw if _text(row))
    if rows:
        return rows
    return (body_open_packet_id,) if body_open_packet_id else ()


def _matching_fallback_attention(
    fallback_attention: Mapping[str, object] | None,
    *,
    actor: str,
    session: str,
) -> Mapping[str, object]:
    fallback = fallback_attention if isinstance(fallback_attention, Mapping) else {}
    observed_actor = _text(fallback.get("observation_actor_id"))
    observed_session = _text(fallback.get("observation_session_id"))
    if observed_actor and actor and observed_actor != actor:
        return {}
    if observed_session and session and observed_session != session:
        return {}
    if actor and not observed_actor:
        return {}
    return fallback


__all__ = [
    "packet_attention_for_agent",
    "packet_body_open_command",
    "packet_semantic_ingestion_command",
    "packet_absorption_command",
]


def _semantic_action_item_rows(
    packet: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    packet_id = _text(packet.get("packet_id"))
    if not packet_id:
        return ()
    kind = _semantic_action_kind(packet)
    target_ref = _semantic_target_ref(packet, packet_id=packet_id)
    disposition = _semantic_action_disposition(packet)
    row = {
        "contract_id": "PacketSemanticActionItem",
        "schema_version": 1,
        "action_item_id": f"{packet_id}:{kind}",
        "kind": kind,
        "disposition": disposition,
        "target_ref": target_ref,
        "packet_ref": f"packet:{packet_id}",
        "reason": _semantic_action_reason(packet),
        "evidence_refs": [f"packet:{packet_id}#body_observed"],
    }
    slice_ref = _text(packet.get("target_ref")) or _text(packet.get("intake_ref"))
    if slice_ref:
        row["slice_ref"] = slice_ref
    if disposition == "deferred":
        row["next_slice_refs"] = _semantic_next_slice_refs(
            packet,
            packet_id=packet_id,
            target_ref=target_ref,
        )
    return (row,)


def _semantic_action_disposition(packet: Mapping[str, object]) -> str:
    if packet_has_effective_durable_binding(packet):
        return "accepted"
    if _packet_is_valid_action_request(packet):
        return "accepted"
    if packet_requires_durable_binding(packet):
        return "deferred"
    return "accepted"


def _semantic_action_kind(packet: Mapping[str, object]) -> str:
    requested = _text(packet.get("requested_action"))
    kind = _text(packet.get("kind"))
    if requested and requested != "review_only":
        return requested
    return kind or "packet"


def _packet_is_valid_action_request(packet: Mapping[str, object]) -> bool:
    return (
        _text(packet.get("kind")) == "action_request"
        and bool(_text(packet.get("requested_action")))
        and bool(_text(packet.get("target_kind")))
        and bool(_text(packet.get("target_ref")))
    )


def _semantic_target_ref(
    packet: Mapping[str, object],
    *,
    packet_id: str,
) -> str:
    target_ref = _text(packet.get("target_ref"))
    if target_ref:
        return target_ref
    target_kind = _text(packet.get("target_kind"))
    if target_kind:
        return f"{target_kind}:{packet_id}"
    return f"packet:{packet_id}"


def _semantic_action_reason(packet: Mapping[str, object]) -> str:
    summary = _text(packet.get("summary"))
    body = _text(packet.get("body"))
    if summary and body:
        return f"{summary}: {body[:180]}"
    return summary or body[:220] or "packet body parsed into typed semantic action row"


def _semantic_next_slice_refs(
    packet: Mapping[str, object],
    *,
    packet_id: str,
    target_ref: str,
) -> list[str]:
    refs: list[str] = []
    for value in (
        _text(packet.get("target_ref")),
        _text(packet.get("intake_ref")),
        target_ref,
        f"packet:{packet_id}",
    ):
        if value and value not in refs:
            refs.append(value)
    return refs or [f"packet:{packet_id}"]
