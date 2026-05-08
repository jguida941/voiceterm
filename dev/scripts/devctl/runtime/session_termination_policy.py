"""Typed session termination policy and task-complete gate."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

SESSION_TERMINATION_POLICY_CONTRACT_ID = "SessionTerminationPolicy"
SESSION_TERMINATION_POLICY_SCHEMA_VERSION = 1
TASK_COMPLETE_DECISION_CONTRACT_ID = "TaskCompleteDecision"
TASK_COMPLETE_DECISION_SCHEMA_VERSION = 1

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
    target_session_id: str = ""
    next_command: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


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
) -> TaskCompleteDecision:
    """Return the typed TASK_COMPLETE decision for one session boundary."""
    normalized_session = _text(session_id)
    if policy.mode == SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE:
        return TaskCompleteDecision(policy_mode=policy.mode)
    if policy.target_session_id and normalized_session != policy.target_session_id:
        return TaskCompleteDecision(
            reason="policy_session_mismatch",
            policy_mode=policy.mode,
            target_session_id=policy.target_session_id,
        )
    if _expired(policy.expires_at_utc):
        return TaskCompleteDecision(
            reason="policy_expired",
            policy_mode=policy.mode,
            target_session_id=policy.target_session_id,
        )

    rows = _packet_rows(packets)
    if _active_stop_anchor(rows, session_id=normalized_session) is not None:
        return TaskCompleteDecision(
            reason="operator_stop_anchor",
            policy_mode=policy.mode,
            target_session_id=policy.target_session_id,
        )

    anchor = _active_continuation_anchor(
        rows,
        policy=policy,
        session_id=normalized_session,
    )
    if anchor is None:
        return TaskCompleteDecision(
            reason="no_active_anchor",
            policy_mode=policy.mode,
            target_session_id=policy.target_session_id,
        )
    anchor_id = _text(anchor.get("packet_id"))
    return TaskCompleteDecision(
        terminate=False,
        reason="continuation_anchor_active",
        policy_mode=policy.mode,
        anchor_packet_id=anchor_id,
        target_session_id=(
            _text(anchor.get("target_session_id")) or policy.target_session_id
        ),
        next_command=continuation_anchor_next_command(anchor, actor=actor),
    )


def continuation_anchor_next_command(
    anchor: Mapping[str, object],
    *,
    actor: str = "",
) -> str:
    """Return the bounded next command for an active continuation anchor."""
    target_actor = _text(actor) or _text(anchor.get("to_agent")) or "codex"
    return f"python3 dev/scripts/devctl.py develop next --actor {target_actor} --format md"


def _active_continuation_anchor(
    packets: Sequence[Mapping[str, object]],
    *,
    policy: SessionTerminationPolicy,
    session_id: str,
) -> Mapping[str, object] | None:
    candidates = [
        packet
        for packet in packets
        if _text(packet.get("kind")) == CONTINUATION_ANCHOR_PACKET_KIND
        and _packet_is_active_anchor(packet)
        and _packet_matches_policy(packet, policy=policy, session_id=session_id)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=_packet_sort_key, reverse=True)[0]


def _active_stop_anchor(
    packets: Sequence[Mapping[str, object]],
    *,
    session_id: str,
) -> Mapping[str, object] | None:
    candidates = [
        packet
        for packet in packets
        if _text(packet.get("kind")) == STOP_ANCHOR_PACKET_KIND
        and _packet_matches_session(packet, session_id=session_id)
        and not _expired(_text(packet.get("expires_at_utc")))
        and _text(packet.get("lifecycle_current_state")) != "dismissed"
    ]
    return sorted(candidates, key=_packet_sort_key, reverse=True)[0] if candidates else None


def _packet_is_active_anchor(packet: Mapping[str, object]) -> bool:
    if _expired(_text(packet.get("expires_at_utc"))):
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
) -> bool:
    if policy.anchor_packet_id and _text(packet.get("packet_id")) != policy.anchor_packet_id:
        return False
    return _packet_matches_session(packet, session_id=session_id)


def _packet_matches_session(
    packet: Mapping[str, object],
    *,
    session_id: str,
) -> bool:
    target_session = _text(packet.get("target_session_id"))
    return not target_session or not session_id or target_session == session_id


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


__all__ = [
    "CONTINUATION_ANCHOR_PACKET_KIND",
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
