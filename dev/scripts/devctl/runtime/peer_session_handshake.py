"""Typed peer session handshake evidence over review-channel packets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from .collaboration_packet_kinds import (
    PEER_SESSION_HANDSHAKE_PACKET_KIND,
    SESSION_RESYNC_PACKET_KIND,
)
from .value_coercion import coerce_mapping as _mapping
from .value_coercion import coerce_text as _text


CONTRACT_ID = "PeerSessionHandshakeEvidence"
_RESOLVED_STATUSES = frozenset({"applied", "dismissed", "expired", "archived"})


@dataclass(frozen=True, slots=True)
class PeerSessionHandshakeEvidence:
    contract_id: str = CONTRACT_ID
    schema_version: int = 1
    actor_id: str = ""
    actor_session_id: str = ""
    peer_actor_id: str = ""
    peer_session_id: str = ""
    handshake_packet_id: str = ""
    session_resync_packet_id: str = ""
    status: str = "missing"
    session_resync_required: bool = False
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def resolve_peer_session_handshake(
    review_state: Mapping[str, object],
    *,
    actor: str,
    session_id: str,
    peer_actor: str,
) -> PeerSessionHandshakeEvidence:
    """Resolve peer session handshake state for one actor/peer pair."""
    actor_id = _text(actor)
    peer_id = _text(peer_actor)
    session = _text(session_id)
    base = {
        "actor_id": actor_id,
        "actor_session_id": session,
        "peer_actor_id": peer_id,
    }
    if not actor_id or not peer_id or not session:
        return PeerSessionHandshakeEvidence(
            **base,
            status="missing_scope",
            session_resync_required=True,
            summary="actor, peer_actor, and session_id are required",
        )

    handshake = _latest_packet(
        review_state,
        kind=PEER_SESSION_HANDSHAKE_PACKET_KIND,
        from_agent=peer_id,
        to_agent=actor_id,
    )
    if not handshake:
        return PeerSessionHandshakeEvidence(
            **base,
            status="missing",
            session_resync_required=True,
            summary="peer_session_handshake packet missing",
        )

    handshake_packet_id = _text(handshake.get("packet_id"))
    peer_session_id = _handshake_peer_session_id(handshake)
    if peer_session_id != session:
        resync_packet = _latest_resync_packet(
            review_state,
            actor=actor_id,
            peer_actor=peer_id,
            handshake_packet_id=handshake_packet_id,
        )
        if resync_packet:
            return PeerSessionHandshakeEvidence(
                **base,
                peer_session_id=peer_session_id,
                handshake_packet_id=handshake_packet_id,
                session_resync_packet_id=_text(resync_packet.get("packet_id")),
                status="resynced",
                session_resync_required=False,
                summary="session mismatch has session_resync evidence",
            )
        return PeerSessionHandshakeEvidence(
            **base,
            peer_session_id=peer_session_id,
            handshake_packet_id=handshake_packet_id,
            status="mismatch",
            session_resync_required=True,
            summary=(
                "peer_session_handshake targets "
                f"{peer_session_id or 'unknown'} but live session is {session}"
            ),
        )

    return PeerSessionHandshakeEvidence(
        **base,
        peer_session_id=peer_session_id,
        handshake_packet_id=handshake_packet_id,
        status="matched",
        session_resync_required=False,
        summary="peer_session_handshake matches live session",
    )


def _latest_resync_packet(
    review_state: Mapping[str, object],
    *,
    actor: str,
    peer_actor: str,
    handshake_packet_id: str,
) -> Mapping[str, object]:
    anchor = f"packet:{handshake_packet_id}" if handshake_packet_id else ""
    candidates = [
        packet
        for packet in _packet_rows(review_state)
        if _text(packet.get("kind")) == SESSION_RESYNC_PACKET_KIND
        and {actor, peer_actor} == {_text(packet.get("from_agent")), _text(packet.get("to_agent"))}
        and (not anchor or anchor in _anchor_refs(packet))
        and not _packet_resolved(packet)
    ]
    return _latest_by_event_id(candidates)


def _latest_packet(
    review_state: Mapping[str, object],
    *,
    kind: str,
    from_agent: str,
    to_agent: str,
) -> Mapping[str, object]:
    candidates = [
        packet
        for packet in _packet_rows(review_state)
        if _text(packet.get("kind")) == kind
        and _text(packet.get("from_agent")) == from_agent
        and _text(packet.get("to_agent")) == to_agent
        and not _packet_resolved(packet)
    ]
    return _latest_by_event_id(candidates)


def _latest_by_event_id(
    packets: list[Mapping[str, object]],
) -> Mapping[str, object]:
    if not packets:
        return {}
    return sorted(
        packets,
        key=lambda packet: (
            _event_rank(_text(packet.get("latest_event_id"))),
            _text(packet.get("posted_at")),
            _text(packet.get("packet_id")),
        ),
    )[-1]


def _packet_rows(review_state: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows = review_state.get("packets")
    if not isinstance(rows, (list, tuple)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _handshake_peer_session_id(packet: Mapping[str, object]) -> str:
    metadata = _mapping(packet.get("metadata"))
    return (
        _text(packet.get("target_session_id"))
        or _text(metadata.get("peer_session_id"))
        or _text(metadata.get("target_session_id"))
    )


def _anchor_refs(packet: Mapping[str, object]) -> tuple[str, ...]:
    refs = packet.get("anchor_refs")
    if not isinstance(refs, (list, tuple)):
        return ()
    return tuple(_text(ref) for ref in refs if _text(ref))


def _packet_resolved(packet: Mapping[str, object]) -> bool:
    status = _text(packet.get("status"))
    lifecycle = _text(packet.get("lifecycle_current_state"))
    return status in _RESOLVED_STATUSES or lifecycle in _RESOLVED_STATUSES


def _event_rank(event_id: str) -> int:
    if not event_id.startswith("rev_evt_"):
        return -1
    try:
        return int(event_id.removeprefix("rev_evt_"))
    except ValueError:
        return -1


__all__ = [
    "CONTRACT_ID",
    "PeerSessionHandshakeEvidence",
    "resolve_peer_session_handshake",
]
