"""Peer packet attention windows for active agent sessions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from .value_coercion import coerce_int as _int
from .value_coercion import coerce_mapping as _mapping
from .value_coercion import coerce_text as _text


CONTRACT_ID = "AttentionWindowProjection"
MAX_PACKET_ROWS_PER_ACTOR = 3
_TERMINAL_STATUSES = frozenset({"applied", "dismissed", "expired"})
_TERMINAL_LIFECYCLES = frozenset(
    {"applied", "dismissed", "expired", "failed", "superseded", "archived"}
)
_BLOCKING_KINDS = frozenset({"action_request", "approval_request", "commit_approval"})
_AMBIENT_KINDS = frozenset({"finding", "question", "decision", "instruction", "system_notice"})


@dataclass(frozen=True, slots=True)
class PeerPacketRow:
    packet_id: str
    from_agent: str
    to_agent: str
    kind: str
    status: str
    lifecycle_current_state: str
    summary: str
    target_role: str
    target_session_id: str
    requested_action: str
    policy_hint: str
    urgency: str
    relevance_score: int
    relevance_reasons: tuple[str, ...]
    consume_state: str
    consume_required: bool
    mutation_blocking: bool
    show_command: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AttentionWindow:
    actor_id: str
    actor_role: str
    session_id: str
    latest_attention_packet_id: str
    blocking_consume_required: bool
    blocking_packet_ids: tuple[str, ...]
    peer_recent_packets: tuple[PeerPacketRow, ...]
    next_commands: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["blocking_packet_ids"] = list(self.blocking_packet_ids)
        payload["peer_recent_packets"] = [
            packet.to_dict() for packet in self.peer_recent_packets
        ]
        payload["next_commands"] = list(self.next_commands)
        return payload


@dataclass(frozen=True, slots=True)
class AttentionWindowProjection:
    contract_id: str
    schema_version: int
    source_contract: str
    source_latest_event_id: str
    windows: tuple[AttentionWindow, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_id": self.contract_id,
            "schema_version": self.schema_version,
            "source_contract": self.source_contract,
            "source_latest_event_id": self.source_latest_event_id,
            "windows": [window.to_dict() for window in self.windows],
        }


def build_attention_window_projection(
    review_state: Mapping[str, object],
    *,
    max_packets_per_actor: int = MAX_PACKET_ROWS_PER_ACTOR,
) -> AttentionWindowProjection:
    """Build bounded per-actor peer packet attention windows.

    Packets remain typed attention only. This projection decides what should be
    visible to the actor's next turn, and whether any visible packet is
    blocking enough to require consumption before mutation.
    """
    packets = _packet_rows(review_state)
    windows = tuple(
        window
        for row in _work_board_rows(review_state)
        if (window := _attention_window_for_row(
            row,
            packets=packets,
            max_packets=max_packets_per_actor,
        ))
        is not None
    )
    return AttentionWindowProjection(
        contract_id=CONTRACT_ID,
        schema_version=1,
        source_contract="ReviewState",
        source_latest_event_id=_source_latest_event_id(review_state),
        windows=windows,
    )


def _attention_window_for_row(
    row: Mapping[str, object],
    *,
    packets: tuple[Mapping[str, object], ...],
    max_packets: int,
) -> AttentionWindow | None:
    actor = _text(row.get("actor_id"))
    role = _normalize_role(row.get("role"))
    session = _text(row.get("session_id"))
    if not actor:
        return None

    candidates = [
        packet_row
        for packet in packets
        if (packet_row := _peer_packet_row(packet, actor=actor, role=role, session=session))
        is not None
    ]
    candidates.sort(
        key=lambda packet: (
            packet.consume_required,
            _event_rank(_packet_event_id(packet.packet_id, packets)),
            packet.relevance_score,
            packet.packet_id,
        ),
        reverse=True,
    )
    bounded = tuple(candidates[: max(0, max_packets)])
    blocking_packet_ids = tuple(
        packet.packet_id for packet in bounded if packet.mutation_blocking
    )
    return AttentionWindow(
        actor_id=actor,
        actor_role=role,
        session_id=session,
        latest_attention_packet_id=bounded[0].packet_id if bounded else "",
        blocking_consume_required=bool(blocking_packet_ids),
        blocking_packet_ids=blocking_packet_ids,
        peer_recent_packets=bounded,
        next_commands=tuple(
            packet.show_command for packet in bounded if packet.consume_required
        ),
    )


def _peer_packet_row(
    packet: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
) -> PeerPacketRow | None:
    if _terminal_packet(packet):
        return None
    reasons = _relevance_reasons(packet, actor=actor, role=role, session=session)
    if not reasons:
        return None
    packet_id = _text(packet.get("packet_id"))
    if not packet_id:
        return None
    kind = _text(packet.get("kind"))
    urgency = _packet_urgency(packet)
    consume_state = _consume_state(packet)
    consume_required = urgency == "blocking" and consume_state not in {
        "acked",
        "execution_started",
    }
    return PeerPacketRow(
        packet_id=packet_id,
        from_agent=_text(packet.get("from_agent")),
        to_agent=_text(packet.get("to_agent")),
        kind=kind,
        status=_text(packet.get("status")),
        lifecycle_current_state=_text(packet.get("lifecycle_current_state")),
        summary=_text(packet.get("summary")),
        target_role=_text(packet.get("target_role")),
        target_session_id=_text(packet.get("target_session_id")),
        requested_action=_text(packet.get("requested_action")),
        policy_hint=_text(packet.get("policy_hint")),
        urgency=urgency,
        relevance_score=_relevance_score(packet, reasons),
        relevance_reasons=tuple(reasons),
        consume_state=consume_state,
        consume_required=consume_required,
        mutation_blocking=consume_required,
        show_command=(
            "python3 dev/scripts/devctl.py review-channel --action show "
            f"--packet-id {packet_id} --terminal none --format md"
        ),
    )


def _relevance_reasons(
    packet: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
) -> list[str]:
    reasons: list[str] = []
    target_session = _text(packet.get("target_session_id"))
    if target_session and session and target_session != session:
        return reasons
    target_role = _normalize_role(packet.get("target_role"))
    if target_role and role and target_role != role:
        return reasons
    if _text(packet.get("to_agent")) == actor:
        reasons.append("to_actor")
    if target_role and role and target_role == role:
        reasons.append("target_role")
    if target_session and session and target_session == session:
        reasons.append("target_session")
    if reasons and _text(packet.get("from_agent")) not in {"", actor}:
        reasons.append("peer_authored")
    return reasons


def _relevance_score(packet: Mapping[str, object], reasons: Sequence[str]) -> int:
    score = 0
    weights = {
        "to_actor": 40,
        "target_session": 30,
        "target_role": 20,
        "peer_authored": 10,
    }
    for reason in reasons:
        score += weights.get(reason, 0)
    kind = _text(packet.get("kind"))
    if kind == "action_request":
        score += 30
    elif kind in {"finding", "approval_request", "commit_approval"}:
        score += 20
    elif kind in _AMBIENT_KINDS:
        score += 10
    if _summary_has_priority_marker(packet):
        score += 20
    return score


def _packet_urgency(packet: Mapping[str, object]) -> str:
    explicit = _text(packet.get("attention_urgency")).lower()
    if explicit == "auto":
        explicit = ""
    if explicit in {"blocking", "urgent", "ambient"}:
        return explicit
    explicit = _text(packet.get("urgency")).lower()
    if explicit in {"blocking", "urgent", "ambient"}:
        return explicit
    kind = _text(packet.get("kind"))
    if kind in _BLOCKING_KINDS:
        return "blocking"
    if _summary_has_priority_marker(packet):
        return "urgent"
    if kind in _AMBIENT_KINDS:
        return "ambient"
    return "ambient"


def _consume_state(packet: Mapping[str, object]) -> str:
    if _text(packet.get("execution_started_at_utc")):
        return "execution_started"
    if _text(packet.get("delivery_observed_at_utc")):
        return "observed"
    lifecycle = _text(packet.get("lifecycle_current_state"))
    if lifecycle == "delivery_pending":
        return "delivery_pending"
    return _text(packet.get("status")) or "unknown"


def _terminal_packet(packet: Mapping[str, object]) -> bool:
    return (
        _text(packet.get("status")) in _TERMINAL_STATUSES
        or _text(packet.get("lifecycle_current_state")) in _TERMINAL_LIFECYCLES
    )


def _summary_has_priority_marker(packet: Mapping[str, object]) -> bool:
    text = f"{_text(packet.get('summary'))} {_text(packet.get('body'))}".upper()
    return "P0" in text or "P1" in text or "BLOCKING" in text


def _work_board_rows(review_state: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows = _mapping(review_state.get("agent_work_board")).get("rows")
    if not isinstance(rows, list):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _packet_rows(review_state: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, Mapping))


def _source_latest_event_id(review_state: Mapping[str, object]) -> str:
    return (
        _text(_mapping(review_state.get("agent_sync")).get("source_latest_event_id"))
        or _text(review_state.get("event_index"))
        or _text(review_state.get("source_latest_event_id"))
    )


def _packet_event_id(
    packet_id: str,
    packets: tuple[Mapping[str, object], ...],
) -> str:
    for packet in packets:
        if _text(packet.get("packet_id")) == packet_id:
            return _text(packet.get("latest_event_id"))
    return ""


def _event_rank(value: str) -> int:
    if value.startswith("rev_evt_"):
        return _int(value.removeprefix("rev_evt_"))
    return 0


def _normalize_role(value: object) -> str:
    text = _text(value).lower().replace("-", "_")
    if text == "coder":
        return "implementer"
    if text == "approver":
        return "reviewer"
    return text


__all__ = [
    "AttentionWindow",
    "AttentionWindowProjection",
    "PeerPacketRow",
    "build_attention_window_projection",
]
