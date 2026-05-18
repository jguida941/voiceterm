"""Source readers for AgentLoopDecision."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..review_channel.agent_packet_focus import (
    AgentPacketFocus,
    packet_by_id,
    packet_focus_for_agent,
)
from ..review_channel.packet_contract import (
    normalize_packet_route_role,
    packet_route_matches_scope,
)
from ..review_channel.packet_loop_attention import packet_requires_runtime_attention
from .agent_loop_operator_override import (
    AgentLoopOperatorOverride,
)
from .review_packet_inbox_liveness import is_live_pending
from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping as _mapping,
    coerce_text as _text,
)


@dataclass(frozen=True, slots=True)
class AgentLoopContext:
    review_state: Mapping[str, object]
    dashboard: Mapping[str, object]
    actor: str
    role: str
    session: str
    master_plan: Mapping[str, object]
    clock: Mapping[str, object]
    attention: Mapping[str, object]
    authority: Mapping[str, object]
    action_routing: Mapping[str, object]
    allowed_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    granted_capabilities: tuple[str, ...]
    operator_override: AgentLoopOperatorOverride
    may_mutate: bool
    top_blocker: str
    next_action: str
    next_command: str
    current_instruction_revision: str
    loop_intent: str
    requested_plan_ref: str
    requested_packet_id: str


PacketState = AgentPacketFocus


def build_agent_loop_context(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    actor_id: object,
    actor_role: object = "",
    session_id: object = "",
    loop_intent: object = "",
    requested_plan_ref: object = "",
    requested_packet_id: object = "",
    master_plan: object = None,
    operator_override_requested: object = False,
    operator_override_reason: object = "",
    operator_override_scope: object = "edit-only",
    operator_override_by: object = "operator",
) -> AgentLoopContext:
    from .agent_loop_context_builder import (
        AgentLoopContextBuildInput,
        build_agent_loop_context_impl,
    )

    return build_agent_loop_context_impl(
        AgentLoopContextBuildInput(
            review_state=review_state,
            dashboard=dashboard,
            actor_id=actor_id,
            actor_role=actor_role,
            session_id=session_id,
            loop_intent=loop_intent,
            requested_plan_ref=requested_plan_ref,
            requested_packet_id=requested_packet_id,
            master_plan=master_plan,
            operator_override_requested=operator_override_requested,
            operator_override_reason=operator_override_reason,
            operator_override_scope=operator_override_scope,
            operator_override_by=operator_override_by,
        )
    )


def resolve_packet_state(ctx: AgentLoopContext) -> PacketState:
    focus = packet_focus_for_agent(
        ctx.review_state,
        actor=ctx.actor,
        role=ctx.role,
        session=ctx.session,
        attention=ctx.attention,
    )
    if ctx.requested_packet_id:
        return _requested_packet_focus(ctx, fallback=focus)
    return focus


def _requested_packet_focus(
    ctx: AgentLoopContext,
    *,
    fallback: PacketState,
) -> PacketState:
    packet_id = _text(ctx.requested_packet_id)
    packet = packet_by_id(ctx.review_state, packet_id)
    if not _requested_packet_can_focus(ctx, packet):
        return AgentPacketFocus()
    return AgentPacketFocus(
        active_packet_id=packet_id,
        attention_packet_id=packet_id,
        executing_packet_id=fallback.executing_packet_id,
        active_packet=packet,
        attention_packet=packet,
        executing_packet=fallback.executing_packet,
        source_contracts=fallback.source_contracts,
    )


def _requested_packet_can_focus(
    ctx: AgentLoopContext,
    packet: Mapping[str, object],
) -> bool:
    if not packet:
        return False
    if not is_live_pending(packet):
        return False
    if not packet_route_matches_scope(
        packet,
        target_role=ctx.role,
        target_session_id=ctx.session,
    ):
        return False
    return packet_requires_runtime_attention(
        packet,
        actor=ctx.actor,
        role=ctx.role,
        session=ctx.session,
    )


def blocker_active(ctx: AgentLoopContext) -> bool:
    return bool(ctx.top_blocker and ctx.top_blocker not in {"n/a", "none"})


def attention_requires_pivot(ctx: AgentLoopContext, packets: PacketState) -> bool:
    if not ctx.attention:
        return False
    if (
        ctx.requested_packet_id
        and not packets.active_packet_id
        and not packets.attention_packet_id
    ):
        return False
    if coerce_bool(ctx.attention.get("body_open_required")):
        return True
    if coerce_bool(ctx.attention.get("semantic_ingestion_required")):
        return True
    if coerce_bool(ctx.attention.get("absorption_required")):
        return True
    if (
        packets.active_packet_id
        and packets.active_packet_id == packets.attention_packet_id
        and _text(latest_session_outcome(ctx).get("outcome")) != "completed_handoff"
    ):
        return False
    pending_packet_count = coerce_int(ctx.attention.get("pending_packet_count"))
    has_attention = bool(
        packets.attention_packet_id
        or _text(ctx.attention.get("latest_attention_packet_id"))
        or pending_packet_count > 0
    )
    return has_attention and (
        coerce_bool(ctx.attention.get("wake_required"))
        or coerce_bool(ctx.attention.get("pivot_required"))
        or pending_packet_count > 0
    )


def latest_session_outcome(ctx: AgentLoopContext) -> Mapping[str, object]:
    candidates = [
        row for row in session_outcome_rows(ctx)
        if outcome_matches_scope(
            row,
            actor=ctx.actor,
            role=ctx.role,
            session=ctx.session,
        )
    ]
    return candidates[-1] if candidates else {}


def session_identity_required(ctx: AgentLoopContext) -> bool:
    if ctx.session or ctx.role not in {"implementer", "coder"}:
        return False
    rows = _mapping(ctx.review_state.get("agent_work_board")).get("rows")
    if not isinstance(rows, list):
        return False
    matching = [
        row for row in rows
        if isinstance(row, Mapping)
        and _text(row.get("actor_id")) == ctx.actor
        and normalize_packet_route_role(row.get("role")) in {"implementer", "coder"}
    ]
    return len(matching) > 1


def role_is_observer(role: str) -> bool:
    return role in {"dashboard", "observer", "operator"}


def normalize_loop_intent(value: object) -> str:
    text = _text(value).lower().replace("_", "-")
    if text in {"", "auto"}:
        return "auto"
    if text in {"wake", "wake-once"}:
        return "wake"
    if text in {"iterate", "iteration", "loop"}:
        return "iterate"
    if text in {"plan", "plan-target"}:
        return "plan"
    if text in {"packet", "packet-target"}:
        return "packet"
    if text in {"full-plan", "full_plan", "autonomous-plan"}:
        return "full-plan"
    return "auto"


def current_instruction_revision(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
) -> str:
    return (
        _text(_mapping(review_state.get("current_session")).get(
            "current_instruction_revision"
        ))
        or _text(_mapping(dashboard.get("ack_freshness")).get(
            "current_instruction_revision"
        ))
    )


def scoped_packet_attention(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    actor: str,
    session: str,
) -> Mapping[str, object]:
    attention = _mapping(_mapping(review_state.get("reviewer_runtime")).get(
        "packet_attention"
    )) or _mapping(dashboard.get("packet_attention"))
    observed_actor = _text(attention.get("observation_actor_id"))
    observed_session = _text(attention.get("observation_session_id"))
    if observed_actor and actor and observed_actor != actor:
        return {}
    if observed_session and session and observed_session != session:
        return {}
    return attention


def session_outcome_rows(ctx: AgentLoopContext) -> tuple[Mapping[str, object], ...]:
    rows: list[Mapping[str, object]] = []
    raw_collab = _mapping(ctx.review_state.get("collaboration")).get("session_outcomes")
    raw_latest = _mapping(ctx.dashboard.get("session_outcomes")).get("latest")
    if isinstance(raw_collab, list):
        rows.extend(row for row in raw_collab if isinstance(row, Mapping))
    if isinstance(raw_latest, list):
        rows.extend(row for row in raw_latest if isinstance(row, Mapping))
    return tuple(rows)


def outcome_matches_scope(
    row: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
) -> bool:
    actor_key = actor.lower()
    if actor_key not in {
        _text(row.get("session_actor_id")).lower(),
        _text(row.get("provider")).lower(),
    }:
        return False
    row_role = normalize_packet_route_role(row.get("session_actor_role"))
    if role and row_role and row_role != role:
        return False
    if session:
        return session in {
            _text(row.get("session_id")),
            _text(row.get("session_name")),
            _text(row.get("prepared_session_token")),
        }
    return True
