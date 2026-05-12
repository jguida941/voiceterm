"""Typed session termination policy and task-complete gate."""

from __future__ import annotations

import hashlib
import shlex
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from .anchor_scope import has_structured_anchor_scope
from .correlation_spine import (
    CorrelationContext,
    lineage_fields,
    merge_correlation_context,
)
from .packet_transport_expiry import packet_transport_expired
from .session_route_scope import normalize_route_role, packet_matches_session_route

SESSION_TERMINATION_POLICY_CONTRACT_ID = "SessionTerminationPolicy"
SESSION_TERMINATION_POLICY_SCHEMA_VERSION = 1
TASK_COMPLETE_DECISION_CONTRACT_ID = "TaskCompleteDecision"
TASK_COMPLETE_DECISION_SCHEMA_VERSION = 1
CONTINUATION_ANCHOR_MISSING_ERROR = "continuation_anchor_missing"
CONTINUATION_ANCHOR_BODY_UNOBSERVED_ERROR = "continuation_anchor_body_unobserved"
STOP_ANCHOR_BODY_UNOBSERVED_ERROR = "stop_anchor_body_unobserved"
PENDING_REVIEW_PACKET_ERROR = "pending_review_packet"
PENDING_REVIEW_PACKET_BODY_UNOBSERVED_ERROR = "pending_review_packet_body_unobserved"
PACKET_ATTENTION_PENDING_ERROR = "packet_attention_pending"
TASK_COMPLETE_BLOCKING_PACKET_KINDS = frozenset(
    {
        "action_request",
        "approval_request",
        "instruction",
    }
)

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

    def _decision(
        *,
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

    if policy.target_session_id and normalized_session != policy.target_session_id:
        return _decision(
            reason="policy_session_mismatch",
            policy_mode=policy.mode,
            target_session_id=policy.target_session_id,
        )
    if _expired(policy.expires_at_utc):
        return _decision(
            reason="policy_expired",
            policy_mode=policy.mode,
            target_session_id=policy.target_session_id,
        )

    rows = _packet_rows(packets)
    normalized_actor = _text(actor)
    normalized_role = normalize_route_role(actor_role)
    normalized_target_ref = _text(target_ref)

    stop_anchor = _active_stop_anchor(
        rows,
        session_id=normalized_session,
        actor=normalized_actor,
        actor_role=normalized_role,
        target_ref=normalized_target_ref,
    )
    if stop_anchor is not None:
        stop_anchor_id = _text(stop_anchor.get("packet_id"))
        if not _packet_body_observed_by_route(
            stop_anchor,
            actor=normalized_actor,
            actor_role=normalized_role,
            session_id=normalized_session,
        ):
            return _decision(
                source=stop_anchor,
                seed_kind="packet",
                seed_ref=stop_anchor_id,
                terminate=False,
                reason=STOP_ANCHOR_BODY_UNOBSERVED_ERROR,
                policy_mode=policy.mode,
                blocking_packet_id=stop_anchor_id,
                target_session_id=(
                    _text(stop_anchor.get("target_session_id"))
                    or policy.target_session_id
                ),
                next_command=_packet_body_show_command(
                    stop_anchor,
                    actor=actor,
                    actor_role=actor_role,
                    session_id=normalized_session,
                ),
                error_kind=STOP_ANCHOR_BODY_UNOBSERVED_ERROR,
                wake_required=True,
                pivot_required=True,
            )
        return _decision(
            source=stop_anchor,
            seed_kind="session",
            seed_ref=normalized_session,
            reason="operator_stop_anchor",
            policy_mode=policy.mode,
            target_session_id=policy.target_session_id,
        )

    attention = packet_attention if isinstance(packet_attention, Mapping) else {}
    if _packet_attention_blocks_task_complete(attention):
        attention_packet_id = _text(attention.get("latest_attention_packet_id"))
        return _decision(
            source=attention,
            seed_kind="packet",
            seed_ref=attention_packet_id,
            terminate=False,
            reason=PACKET_ATTENTION_PENDING_ERROR,
            policy_mode=policy.mode,
            blocking_packet_id=attention_packet_id,
            target_session_id=(
                _text(attention.get("observation_session_id"))
                or policy.target_session_id
            ),
            next_command=continuation_anchor_next_command(
                {},
                actor=actor,
            ),
            error_kind=PACKET_ATTENTION_PENDING_ERROR,
            pending_packet_count=_int(attention.get("pending_packet_count")),
            wake_required=_truthy(attention.get("wake_required")),
            pivot_required=_truthy(attention.get("pivot_required")),
        )

    pending_review = _active_pending_review_packet(
        rows,
        session_id=normalized_session,
        actor=normalized_actor,
        actor_role=normalized_role,
        target_ref=normalized_target_ref,
    )
    if pending_review is not None:
        pending_packet_id = _text(pending_review.get("packet_id"))
        if not _packet_body_observed_by_route(
            pending_review,
            actor=normalized_actor,
            actor_role=normalized_role,
            session_id=normalized_session,
        ):
            return _decision(
                source=pending_review,
                seed_kind="packet",
                seed_ref=pending_packet_id,
                terminate=False,
                reason=PENDING_REVIEW_PACKET_BODY_UNOBSERVED_ERROR,
                policy_mode=policy.mode,
                blocking_packet_id=pending_packet_id,
                target_session_id=policy.target_session_id,
                next_command=_packet_body_show_command(
                    pending_review,
                    actor=actor,
                    actor_role=actor_role,
                    session_id=normalized_session,
                ),
                error_kind=PENDING_REVIEW_PACKET_BODY_UNOBSERVED_ERROR,
                wake_required=True,
                pivot_required=True,
            )
        return _decision(
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
                actor=actor,
            ),
            error_kind=PENDING_REVIEW_PACKET_ERROR,
        )

    # MP377-CONTINUATION-ANCHOR-CONSOLIDATION-S1 (smell #058 fix):
    # Continuation_anchor enforcement applies in ALL policy modes, not just
    # `keep_awake_via_packets`. Previously `end_on_task_complete` mode skipped
    # the anchor check entirely (early-returned at this line), letting codex
    # sessions emit TASK_COMPLETE despite a live operator-authorized
    # continuation_anchor. Empirically confirmed 2026-05-11 when codex sessions
    # 019e1436 and 019e17fa-3745 both died at TASK_COMPLETE with live anchor
    # rev_pkt_3685. The anchor consultation now runs BEFORE the policy-mode
    # gate; only when no anchor exists does the policy-mode default decide
    # whether TASK_COMPLETE terminates the session.
    default_anchor = _active_continuation_anchor(
        rows,
        policy=policy,
        session_id=normalized_session,
        actor=normalized_actor,
        actor_role=normalized_role,
        target_ref=normalized_target_ref,
    )
    if default_anchor is not None:
        anchor_id = _text(default_anchor.get("packet_id"))
        if not _packet_body_observed_by_route(
            default_anchor,
            actor=normalized_actor,
            actor_role=normalized_role,
            session_id=normalized_session,
        ):
            return _decision(
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
                next_command=_packet_body_show_command(
                    default_anchor,
                    actor=actor,
                    actor_role=actor_role,
                    session_id=normalized_session,
                ),
                error_kind=CONTINUATION_ANCHOR_BODY_UNOBSERVED_ERROR,
                wake_required=True,
                pivot_required=True,
            )
        return _decision(
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
            next_command=continuation_anchor_next_command(default_anchor, actor=actor),
        )

    if policy.mode == SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE:
        return _decision(
            policy_mode=policy.mode,
            seed_kind="session",
            seed_ref=normalized_session,
        )

    return _decision(
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
    candidates = [
        packet
        for packet in packets
        if _text(packet.get("kind")) == CONTINUATION_ANCHOR_PACKET_KIND
        and _packet_is_active_anchor(packet)
        and _packet_matches_policy(
            packet,
            policy=policy,
            session_id=session_id,
            actor=actor,
            actor_role=actor_role,
            target_ref=target_ref,
        )
    ]
    if not candidates:
        return None
    return sorted(candidates, key=_packet_sort_key, reverse=True)[0]


def _active_pending_review_packet(
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
        if _packet_blocks_task_complete(packet)
        and _packet_is_active_anchor(packet)
        and packet_matches_session_route(
            packet,
            session_id=session_id,
            actor=actor,
            actor_role=actor_role,
            target_ref=target_ref,
        )
    ]
    return sorted(candidates, key=_packet_sort_key, reverse=True)[0] if candidates else None


def _packet_blocks_task_complete(packet: Mapping[str, object]) -> bool:
    kind = _text(packet.get("kind"))
    return kind.startswith("review_") or kind in TASK_COMPLETE_BLOCKING_PACKET_KINDS


def _packet_attention_blocks_task_complete(attention: Mapping[str, object]) -> bool:
    return (
        _int(attention.get("pending_packet_count")) > 0
        or _truthy(attention.get("wake_required"))
        or _truthy(attention.get("pivot_required"))
    )


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
        and _packet_is_active_anchor(packet)
        and _text(packet.get("lifecycle_current_state")) != "dismissed"
    ]
    return sorted(candidates, key=_packet_sort_key, reverse=True)[0] if candidates else None


def _packet_is_active_anchor(packet: Mapping[str, object]) -> bool:
    if packet_transport_expired(packet):
        return False
    status = _text(packet.get("status"))
    lifecycle = _text(packet.get("lifecycle_current_state"))
    if status in {"applied", "archived", "dismissed", "expired"}:
        return False
    return lifecycle not in {"applied", "archived", "dismissed", "expired"}


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


def _packet_body_observed_by_route(
    packet: Mapping[str, object],
    *,
    actor: str,
    actor_role: str,
    session_id: str,
) -> bool:
    body = _text(packet.get("body"))
    if not body:
        return True
    if not actor:
        return False
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if _body_observation_row_matches(
        packet,
        actor=actor,
        actor_role=actor_role,
        session_id=session_id,
        body_digest=digest,
        allow_event_session_fallback=False,
    ):
        return True
    events = packet.get("body_observation_events")
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
        return False
    return any(
        isinstance(event, Mapping)
        and _body_observation_row_matches(
            event,
            actor=actor,
            actor_role=actor_role,
            session_id=session_id,
            body_digest=digest,
            allow_event_session_fallback=True,
        )
        for event in events
    )


def _body_observation_row_matches(
    row: Mapping[str, object],
    *,
    actor: str,
    actor_role: str,
    session_id: str,
    body_digest: str,
    allow_event_session_fallback: bool,
) -> bool:
    if _text(row.get("body_observed_by")) != actor:
        return False
    if _text(row.get("body_digest")) != body_digest:
        return False
    if actor_role:
        observed_role = _text(row.get("body_observed_role"))
        if allow_event_session_fallback and not observed_role:
            observed_role = _text(row.get("target_role"))
        if normalize_route_role(observed_role) != actor_role:
            return False
    if session_id:
        observed_session = _text(row.get("body_observed_session_id"))
        if allow_event_session_fallback and not observed_session:
            observed_session = _text(
                row.get("target_session_id") or row.get("session_id")
            )
        if observed_session != session_id:
            return False
    return True


def _packet_body_show_command(
    packet: Mapping[str, object],
    *,
    actor: str,
    actor_role: str,
    session_id: str,
) -> str:
    packet_id = _text(packet.get("packet_id"))
    target_actor = _text(actor) or _text(packet.get("to_agent"))
    if not packet_id:
        return ""
    parts = [
        "python3",
        "dev/scripts/devctl.py",
        "review-channel",
        "--action",
        "show",
        "--packet-id",
        packet_id,
    ]
    if target_actor:
        parts.extend(("--actor", target_actor))
    parts.extend(("--terminal", "none", "--format", "md"))
    if actor_role:
        parts.extend(("--target-role", actor_role))
    if session_id:
        parts.extend(("--target-session-id", session_id))
    return " ".join(shlex.quote(part) for part in parts)


def _packet_rows(packets: Sequence[object] | object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, Mapping))


def _packet_sort_key(packet: Mapping[str, object]) -> tuple[str, str, str]:
    return (
        _text(packet.get("posted_at")),
        _text(packet.get("latest_event_id")),
        _text(packet.get("packet_id")),
    )


def _expired(value: str) -> bool:
    stamp = _parse_utc(value)
    return stamp is not None and stamp <= datetime.now(timezone.utc)


def _parse_utc(value: object) -> datetime | None:
    text = _text(value)
    if not text:
        return None
    try:
        stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value).lower() in {"1", "true", "yes", "on"}


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
