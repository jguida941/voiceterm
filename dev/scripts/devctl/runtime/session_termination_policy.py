"""Typed session termination policy and task-complete gate."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from .anchor_scope import has_structured_anchor_scope
from .correlation_spine import (
    CorrelationContext,
    lineage_fields,
    merge_correlation_context,
)
from .session_termination_anchor_release import slice_counted_anchor_status
from .session_termination_attention import (
    packet_attention_blocks_task_complete,
    truthy,
)
from .session_termination_body import (
    packet_body_observed_by_route,
    packet_body_show_command,
)
from .session_termination_pending import (
    active_pending_review_packet,
    packet_is_active_anchor,
    packet_sort_key,
)
from .session_termination_time import expired
from .session_route_scope import normalize_route_role, packet_matches_session_route

SESSION_TERMINATION_POLICY_CONTRACT_ID = "SessionTerminationPolicy"
SESSION_TERMINATION_POLICY_SCHEMA_VERSION = 1
TASK_COMPLETE_DECISION_CONTRACT_ID = "TaskCompleteDecision"
TASK_COMPLETE_DECISION_SCHEMA_VERSION = 1
CONTINUATION_ANCHOR_MISSING_ERROR = "continuation_anchor_missing"
CONTINUATION_ANCHOR_BODY_UNOBSERVED_ERROR = "continuation_anchor_body_unobserved"
CONTINUATION_ANCHOR_SLICE_COUNTED_PENDING_ERROR = (
    "continuation_anchor_slice_counted_pending"
)
CONTINUATION_ANCHOR_SLICE_COUNTED_INVALID_ERROR = (
    "continuation_anchor_slice_counted_invalid"
)
STOP_ANCHOR_BODY_UNOBSERVED_ERROR = "stop_anchor_body_unobserved"
PENDING_REVIEW_PACKET_ERROR = "pending_review_packet"
PENDING_REVIEW_PACKET_BODY_UNOBSERVED_ERROR = "pending_review_packet_body_unobserved"
PACKET_ATTENTION_PENDING_ERROR = "packet_attention_pending"
SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE = "end_on_task_complete"
SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS = "keep_awake_via_packets"
SESSION_TERMINATION_MODE_END_WHEN_ANCHOR_DRAINED = "session_end_when_anchor_drained"
SESSION_TERMINATION_MODES = frozenset(
    {
        SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE,
        SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
        SESSION_TERMINATION_MODE_END_WHEN_ANCHOR_DRAINED,
    }
)

CONTINUATION_ANCHOR_PACKET_KIND = "continuation_anchor"
STOP_ANCHOR_PACKET_KIND = "stop_anchor"
SESSION_TERMINATION_PACKET_KINDS = frozenset(
    {
        CONTINUATION_ANCHOR_PACKET_KIND,
        STOP_ANCHOR_PACKET_KIND,
    }
)


@dataclass(frozen=True, slots=True)
class SessionTerminationPolicy:
    """Machine-readable policy for an agent session's TASK_COMPLETE boundary."""

    schema_version: int = SESSION_TERMINATION_POLICY_SCHEMA_VERSION
    contract_id: str = SESSION_TERMINATION_POLICY_CONTRACT_ID
    mode: str = SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE
    set_by: str = ""
    set_at_utc: str = ""
    anchor_packet_id: str = ""
    target_session_id: str = ""
    expires_at_utc: str = ""

    @property
    def keeps_awake(self) -> bool:
        return self.mode in {
            SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
            SESSION_TERMINATION_MODE_END_WHEN_ANCHOR_DRAINED,
        }

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TaskCompleteDecision:
    """Decision for whether TASK_COMPLETE ends or continues the session."""

    schema_version: int = TASK_COMPLETE_DECISION_SCHEMA_VERSION
    contract_id: str = TASK_COMPLETE_DECISION_CONTRACT_ID
    terminate: bool = True
    reason: str = "policy_default"
    policy_mode: str = SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE
    anchor_packet_id: str = ""
    blocking_packet_id: str = ""
    target_session_id: str = ""
    next_command: str = ""
    error_kind: str = ""
    pending_packet_count: int = 0
    wake_required: bool = False
    pivot_required: bool = False
    correlation_id: str = ""
    causation_id: str = ""
    run_id: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @property
    def continuation_anchor_missing(self) -> bool:
        return self.error_kind == CONTINUATION_ANCHOR_MISSING_ERROR

    @property
    def pending_review_packet(self) -> bool:
        return self.error_kind == PENDING_REVIEW_PACKET_ERROR

    @property
    def packet_attention_pending(self) -> bool:
        return self.error_kind == PACKET_ATTENTION_PENDING_ERROR


@dataclass(frozen=True, slots=True)
class SessionTerminationRoute:
    session_id: str
    actor: str
    actor_role: str
    target_ref: str
    raw_actor: str
    raw_actor_role: str


def session_termination_policy_from_mapping(
    value: object,
) -> SessionTerminationPolicy:
    """Deserialize policy state, falling back to the fail-closed default."""
    if not isinstance(value, Mapping):
        return SessionTerminationPolicy()
    mode = _text(value.get("mode"))
    if mode not in SESSION_TERMINATION_MODES:
        mode = SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE
    return SessionTerminationPolicy(
        schema_version=_int(value.get("schema_version"))
        or SESSION_TERMINATION_POLICY_SCHEMA_VERSION,
        contract_id=(
            _text(value.get("contract_id"))
            or SESSION_TERMINATION_POLICY_CONTRACT_ID
        ),
        mode=mode,
        set_by=_text(value.get("set_by")),
        set_at_utc=_text(value.get("set_at_utc")),
        anchor_packet_id=_text(value.get("anchor_packet_id")),
        target_session_id=_text(value.get("target_session_id")),
        expires_at_utc=_text(value.get("expires_at_utc")),
    )


def session_termination_policy_from_review_state(
    review_state: Mapping[str, object] | None,
) -> SessionTerminationPolicy:
    """Read policy from review-state payloads without trusting prose fields."""
    if not isinstance(review_state, Mapping):
        return SessionTerminationPolicy()
    policy = session_termination_policy_from_mapping(
        review_state.get("session_termination_policy")
    )
    if policy.mode != SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE:
        return policy
    runtime = review_state.get("reviewer_runtime")
    if isinstance(runtime, Mapping):
        return session_termination_policy_from_mapping(
            runtime.get("session_termination_policy")
        )
    return policy


def task_complete_decision(
    *,
    session_id: str,
    packets: Sequence[object] | object,
    policy: SessionTerminationPolicy,
    actor: str = "",
    actor_role: str = "",
    target_ref: str = "",
    packet_attention: Mapping[str, object] | None = None,
    correlation_id: str = "",
    causation_id: str = "",
    run_id: str = "",
) -> TaskCompleteDecision:
    """Return the typed TASK_COMPLETE decision for one session boundary."""
    normalized_session = _text(session_id)
    base_context = CorrelationContext(
        correlation_id=_text(correlation_id),
        causation_id=_text(causation_id),
        run_id=_text(run_id),
    )
    if policy.target_session_id and normalized_session != policy.target_session_id:
        return _task_decision(
            base_context=base_context,
            reason="policy_session_mismatch",
            policy_mode=policy.mode,
            target_session_id=policy.target_session_id,
        )
    if expired(policy.expires_at_utc):
        return _task_decision(
            base_context=base_context,
            reason="policy_expired",
            policy_mode=policy.mode,
            target_session_id=policy.target_session_id,
        )
    rows = _packet_rows(packets)
    normalized_actor = _text(actor)
    normalized_role = normalize_route_role(actor_role)
    normalized_target_ref = _text(target_ref)
    route = SessionTerminationRoute(
        session_id=normalized_session,
        actor=normalized_actor,
        actor_role=normalized_role,
        target_ref=normalized_target_ref,
        raw_actor=actor,
        raw_actor_role=actor_role,
    )
    stop_decision = _stop_anchor_task_decision(
        rows=rows,
        policy=policy,
        route=route,
        base_context=base_context,
    )
    if stop_decision is not None:
        return stop_decision
    attention = packet_attention if isinstance(packet_attention, Mapping) else {}
    attention_decision = _packet_attention_task_decision(
        attention=attention,
        policy=policy,
        actor=actor,
        base_context=base_context,
    )
    if attention_decision is not None:
        return attention_decision
    pending_decision = _pending_review_task_decision(
        rows=rows,
        policy=policy,
        route=route,
        base_context=base_context,
    )
    if pending_decision is not None:
        return pending_decision
    anchor_decision = _continuation_anchor_task_decision(
        rows=rows,
        policy=policy,
        route=route,
        base_context=base_context,
    )
    if anchor_decision is not None:
        return anchor_decision
    if policy.mode == SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE:
        return _task_decision(
            base_context=base_context,
            policy_mode=policy.mode,
            seed_kind="session",
            seed_ref=normalized_session,
        )
    return _task_decision(
        base_context=base_context,
        seed_kind="session",
        seed_ref=normalized_session,
        terminate=False,
        reason=CONTINUATION_ANCHOR_MISSING_ERROR,
        policy_mode=policy.mode,
        target_session_id=policy.target_session_id,
        next_command=continuation_anchor_next_command(
            {},
            actor=actor,
        ),
        error_kind=CONTINUATION_ANCHOR_MISSING_ERROR,
    )


def _task_decision(
    *,
    base_context: CorrelationContext,
    source: Mapping[str, object] | None = None,
    seed_kind: str = "",
    seed_ref: str = "",
    **kwargs: object,
) -> TaskCompleteDecision:
    context = merge_correlation_context(
        source,
        lineage_fields(base_context),
        seed_kind=seed_kind,
        seed_ref=seed_ref,
    )
    return TaskCompleteDecision(
        **kwargs,
        correlation_id=context.correlation_id,
        causation_id=context.causation_id,
        run_id=context.run_id,
    )


def _stop_anchor_task_decision(
    *,
    rows: tuple[Mapping[str, object], ...],
    policy: SessionTerminationPolicy,
    route: SessionTerminationRoute,
    base_context: CorrelationContext,
) -> TaskCompleteDecision | None:
    stop_anchor = _active_stop_anchor(
        rows,
        session_id=route.session_id,
        actor=route.actor,
        actor_role=route.actor_role,
        target_ref=route.target_ref,
    )
    if stop_anchor is None:
        return None
    stop_anchor_id = _text(stop_anchor.get("packet_id"))
    if not packet_body_observed_by_route(
        stop_anchor,
        actor=route.actor,
        actor_role=route.actor_role,
        session_id=route.session_id,
    ):
        return _task_decision(
            base_context=base_context,
            source=stop_anchor,
            seed_kind="packet",
            seed_ref=stop_anchor_id,
            terminate=False,
            reason=STOP_ANCHOR_BODY_UNOBSERVED_ERROR,
            policy_mode=policy.mode,
            blocking_packet_id=stop_anchor_id,
            target_session_id=(
                _text(stop_anchor.get("target_session_id")) or policy.target_session_id
            ),
            next_command=packet_body_show_command(
                stop_anchor,
                actor=route.raw_actor,
                actor_role=route.raw_actor_role,
                session_id=route.session_id,
            ),
            error_kind=STOP_ANCHOR_BODY_UNOBSERVED_ERROR,
            wake_required=True,
            pivot_required=True,
        )
    return _task_decision(
        base_context=base_context,
        source=stop_anchor,
        seed_kind="session",
        seed_ref=route.session_id,
        reason="operator_stop_anchor",
        policy_mode=policy.mode,
        target_session_id=policy.target_session_id,
    )


def _packet_attention_task_decision(
    *,
    attention: Mapping[str, object],
    policy: SessionTerminationPolicy,
    actor: str,
    base_context: CorrelationContext,
) -> TaskCompleteDecision | None:
    if not packet_attention_blocks_task_complete(attention):
        return None
    attention_packet_id = _text(attention.get("latest_attention_packet_id"))
    return _task_decision(
        base_context=base_context,
        source=attention,
        seed_kind="packet",
        seed_ref=attention_packet_id,
        terminate=False,
        reason=PACKET_ATTENTION_PENDING_ERROR,
        policy_mode=policy.mode,
        blocking_packet_id=attention_packet_id,
        target_session_id=(
            _text(attention.get("observation_session_id")) or policy.target_session_id
        ),
        next_command=continuation_anchor_next_command({}, actor=actor),
        error_kind=PACKET_ATTENTION_PENDING_ERROR,
        pending_packet_count=_int(attention.get("pending_packet_count")),
        wake_required=truthy(attention.get("wake_required")),
        pivot_required=truthy(attention.get("pivot_required")),
    )


def _pending_review_task_decision(
    *,
    rows: tuple[Mapping[str, object], ...],
    policy: SessionTerminationPolicy,
    route: SessionTerminationRoute,
    base_context: CorrelationContext,
) -> TaskCompleteDecision | None:
    pending_review = active_pending_review_packet(
        rows,
        session_id=route.session_id,
        actor=route.actor,
        actor_role=route.actor_role,
        target_ref=route.target_ref,
    )
    if pending_review is None:
        return None
    pending_packet_id = _text(pending_review.get("packet_id"))
    if not packet_body_observed_by_route(
        pending_review,
        actor=route.actor,
        actor_role=route.actor_role,
        session_id=route.session_id,
    ):
        return _task_decision(
            base_context=base_context,
            source=pending_review,
            seed_kind="packet",
            seed_ref=pending_packet_id,
            terminate=False,
            reason=PENDING_REVIEW_PACKET_BODY_UNOBSERVED_ERROR,
            policy_mode=policy.mode,
            blocking_packet_id=pending_packet_id,
            target_session_id=policy.target_session_id,
            next_command=packet_body_show_command(
                pending_review,
                actor=route.raw_actor,
                actor_role=route.raw_actor_role,
                session_id=route.session_id,
            ),
            error_kind=PENDING_REVIEW_PACKET_BODY_UNOBSERVED_ERROR,
            wake_required=True,
            pivot_required=True,
        )
    return _task_decision(
        base_context=base_context,
        source=pending_review,
        seed_kind="packet",
        seed_ref=pending_packet_id,
        terminate=False,
        reason=PENDING_REVIEW_PACKET_ERROR,
        policy_mode=policy.mode,
        blocking_packet_id=pending_packet_id,
        target_session_id=policy.target_session_id,
        next_command=continuation_anchor_next_command(
            pending_review,
            actor=route.raw_actor,
        ),
        error_kind=PENDING_REVIEW_PACKET_ERROR,
    )


def _slice_counted_continuation_anchor_decision(
    *,
    anchor: Mapping[str, object],
    rows: tuple[Mapping[str, object], ...],
    policy: SessionTerminationPolicy,
    base_context: CorrelationContext,
) -> TaskCompleteDecision | None:
    """SLICE-Z bug #9 fix: keep session alive when slice-counted anchor pending.

    Per codex rev_pkt_4517: continuation_anchor packets can opt into
    ``release_mode=commit_count`` (or ``slice_counted``) with a
    ``release_commit_count=N`` threshold. The session must continue while
    distinct typed commit evidence since the anchor's posted_at remains below
    ``N``, and only release once N is reached.

    This helper is called only after the anchor has passed normal route scope
    and body-observation checks. Fail-closed: invalid release metadata =
    continue (do not auto-terminate).
    """
    status = slice_counted_anchor_status(anchor, rows)
    if not status.configured:
        return None
    anchor_id = _text(anchor.get("packet_id"))
    if status.invalid:
        return _task_decision(
            base_context=base_context,
            policy_mode=policy.mode,
            seed_kind="continuation_anchor",
            seed_ref=anchor_id,
            terminate=False,
            reason=CONTINUATION_ANCHOR_SLICE_COUNTED_INVALID_ERROR,
            error_kind=CONTINUATION_ANCHOR_SLICE_COUNTED_INVALID_ERROR,
        )
    if status.released:
        return _task_decision(
            base_context=base_context,
            source=anchor,
            seed_kind="packet",
            seed_ref=anchor_id,
            reason="continuation_anchor_slice_counted_released",
            policy_mode=policy.mode,
            anchor_packet_id=anchor_id,
            target_session_id=(
                _text(anchor.get("target_session_id")) or policy.target_session_id
            ),
        )
    return _task_decision(
        base_context=base_context,
        policy_mode=policy.mode,
        seed_kind="continuation_anchor",
        seed_ref=anchor_id,
        terminate=False,
        reason=CONTINUATION_ANCHOR_SLICE_COUNTED_PENDING_ERROR,
        error_kind=CONTINUATION_ANCHOR_SLICE_COUNTED_PENDING_ERROR,
    )


def _continuation_anchor_task_decision(
    *,
    rows: tuple[Mapping[str, object], ...],
    policy: SessionTerminationPolicy,
    route: SessionTerminationRoute,
    base_context: CorrelationContext,
) -> TaskCompleteDecision | None:
    released_decision: TaskCompleteDecision | None = None
    for default_anchor in _active_continuation_anchor_candidates(
        rows,
        policy=policy,
        session_id=route.session_id,
        actor=route.actor,
        actor_role=route.actor_role,
        target_ref=route.target_ref,
    ):
        anchor_id = _text(default_anchor.get("packet_id"))
        if not packet_body_observed_by_route(
            default_anchor,
            actor=route.actor,
            actor_role=route.actor_role,
            session_id=route.session_id,
        ):
            return _task_decision(
                base_context=base_context,
                source=default_anchor,
                seed_kind="packet",
                seed_ref=anchor_id,
                terminate=False,
                reason=CONTINUATION_ANCHOR_BODY_UNOBSERVED_ERROR,
                policy_mode=policy.mode,
                anchor_packet_id=anchor_id,
                blocking_packet_id=anchor_id,
                target_session_id=(
                    _text(default_anchor.get("target_session_id"))
                    or policy.target_session_id
                ),
                next_command=packet_body_show_command(
                    default_anchor,
                    actor=route.raw_actor,
                    actor_role=route.raw_actor_role,
                    session_id=route.session_id,
                ),
                error_kind=CONTINUATION_ANCHOR_BODY_UNOBSERVED_ERROR,
                wake_required=True,
                pivot_required=True,
            )
        slice_counted_decision = _slice_counted_continuation_anchor_decision(
            anchor=default_anchor,
            rows=rows,
            policy=policy,
            base_context=base_context,
        )
        if slice_counted_decision is not None:
            if slice_counted_decision.terminate:
                released_decision = slice_counted_decision
                continue
            return slice_counted_decision
        return _task_decision(
            base_context=base_context,
            source=default_anchor,
            seed_kind="packet",
            seed_ref=anchor_id,
            terminate=False,
            reason="continuation_anchor_active",
            policy_mode=policy.mode,
            anchor_packet_id=anchor_id,
            target_session_id=(
                _text(default_anchor.get("target_session_id"))
                or policy.target_session_id
            ),
            next_command=continuation_anchor_next_command(
                default_anchor,
                actor=route.raw_actor,
            ),
        )
    if (
        released_decision is not None
        and policy.mode != SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE
    ):
        return released_decision
    return None


def continuation_anchor_next_command(
    anchor: Mapping[str, object],
    *,
    actor: str = "",
) -> str:
    """Return the bounded next command for an active continuation anchor."""
    target_actor = _text(actor) or _text(anchor.get("to_agent"))
    if not target_actor:
        return ""
    return f"python3 dev/scripts/devctl.py develop next --actor {target_actor} --format md"


def _active_continuation_anchor(
    packets: Sequence[Mapping[str, object]],
    *,
    policy: SessionTerminationPolicy,
    session_id: str,
    actor: str,
    actor_role: str,
    target_ref: str,
) -> Mapping[str, object] | None:
    candidates = _active_continuation_anchor_candidates(
        packets,
        policy=policy,
        session_id=session_id,
        actor=actor,
        actor_role=actor_role,
        target_ref=target_ref,
    )
    return candidates[0] if candidates else None


def _active_continuation_anchor_candidates(
    packets: Sequence[Mapping[str, object]],
    *,
    policy: SessionTerminationPolicy,
    session_id: str,
    actor: str,
    actor_role: str,
    target_ref: str,
) -> tuple[Mapping[str, object], ...]:
    candidates = [
        packet
        for packet in packets
        if _text(packet.get("kind")) == CONTINUATION_ANCHOR_PACKET_KIND
        and packet_is_active_anchor(packet)
        and _packet_matches_policy(
            packet,
            policy=policy,
            session_id=session_id,
            actor=actor,
            actor_role=actor_role,
            target_ref=target_ref,
        )
    ]
    return tuple(sorted(candidates, key=packet_sort_key, reverse=True))


def _active_stop_anchor(
    packets: Sequence[Mapping[str, object]],
    *,
    session_id: str,
    actor: str,
    actor_role: str,
    target_ref: str,
) -> Mapping[str, object] | None:
    candidates = [
        packet
        for packet in packets
        if _text(packet.get("kind")) == STOP_ANCHOR_PACKET_KIND
        and has_structured_anchor_scope(packet)
        and packet_matches_session_route(
            packet,
            session_id=session_id,
            actor=actor,
            actor_role=actor_role,
            target_ref=target_ref,
        )
        and packet_is_active_anchor(packet)
        and _text(packet.get("lifecycle_current_state")) != "dismissed"
    ]
    return sorted(candidates, key=packet_sort_key, reverse=True)[0] if candidates else None


def _packet_matches_policy(
    packet: Mapping[str, object],
    *,
    policy: SessionTerminationPolicy,
    session_id: str,
    actor: str,
    actor_role: str,
    target_ref: str,
) -> bool:
    if policy.anchor_packet_id and _text(packet.get("packet_id")) != policy.anchor_packet_id:
        return False
    return packet_matches_session_route(
        packet,
        session_id=session_id,
        actor=actor,
        actor_role=actor_role,
        target_ref=target_ref,
    )


def _packet_rows(packets: Sequence[object] | object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, Mapping))


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "CONTINUATION_ANCHOR_PACKET_KIND",
    "CONTINUATION_ANCHOR_BODY_UNOBSERVED_ERROR",
    "CONTINUATION_ANCHOR_MISSING_ERROR",
    "PACKET_ATTENTION_PENDING_ERROR",
    "PENDING_REVIEW_PACKET_ERROR",
    "SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE",
    "SESSION_TERMINATION_MODE_END_WHEN_ANCHOR_DRAINED",
    "SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS",
    "SESSION_TERMINATION_MODES",
    "SESSION_TERMINATION_PACKET_KINDS",
    "SESSION_TERMINATION_POLICY_CONTRACT_ID",
    "SESSION_TERMINATION_POLICY_SCHEMA_VERSION",
    "STOP_ANCHOR_PACKET_KIND",
    "TASK_COMPLETE_DECISION_CONTRACT_ID",
    "TASK_COMPLETE_DECISION_SCHEMA_VERSION",
    "SessionTerminationPolicy",
    "TaskCompleteDecision",
    "continuation_anchor_next_command",
    "session_termination_policy_from_mapping",
    "session_termination_policy_from_review_state",
    "task_complete_decision",
]
