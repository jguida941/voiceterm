"""Peer heartbeat TTL evidence over review-channel packets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

UTC = timezone.utc

from .collaboration_packet_kinds import (
    PEER_HEARTBEAT_PACKET_KIND,
    PEER_OFFLINE_PACKET_KIND,
)
from .value_coercion import coerce_int as _int
from .value_coercion import coerce_mapping as _mapping
from .value_coercion import coerce_string as _text


CONTRACT_ID = "PeerHeartbeatEvidence"
SCHEMA_VERSION = 1
DEFAULT_PEER_HEARTBEAT_TTL_SECONDS = 300
_RESOLVED_STATUSES = frozenset({"applied", "dismissed", "expired", "archived"})


@dataclass(frozen=True, slots=True)
class PeerHeartbeatEvidence:
    contract_id: str = CONTRACT_ID
    schema_version: int = SCHEMA_VERSION
    actor_id: str = ""
    actor_session_id: str = ""
    peer_actor_id: str = ""
    peer_session_id: str = ""
    heartbeat_packet_id: str = ""
    peer_offline_packet_id: str = ""
    heartbeat_observed_at_utc: str = ""
    expires_at_utc: str = ""
    ttl_seconds: int = DEFAULT_PEER_HEARTBEAT_TTL_SECONDS
    status: str = "missing"
    peer_offline: bool = True
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def resolve_peer_heartbeat(
    review_state: Mapping[str, object],
    *,
    actor: str,
    session_id: str,
    peer_actor: str,
    now_utc: str = "",
    ttl_seconds: int = DEFAULT_PEER_HEARTBEAT_TTL_SECONDS,
) -> PeerHeartbeatEvidence:
    """Resolve current peer heartbeat state for an actor/peer pair."""
    actor_id = _text(actor)
    peer_id = _text(peer_actor)
    session = _text(session_id)
    ttl = max(0, _int(ttl_seconds) or DEFAULT_PEER_HEARTBEAT_TTL_SECONDS)
    base = {
        "actor_id": actor_id,
        "actor_session_id": session,
        "peer_actor_id": peer_id,
        "ttl_seconds": ttl,
    }
    if not actor_id or not peer_id or not session:
        return PeerHeartbeatEvidence(
            **base,
            status="missing_scope",
            peer_offline=True,
            summary="actor, peer_actor, and session_id are required",
        )

    heartbeat = _latest_packet(
        review_state,
        kind=PEER_HEARTBEAT_PACKET_KIND,
        from_agent=peer_id,
        to_agent=actor_id,
    )
    if not heartbeat:
        return PeerHeartbeatEvidence(
            **base,
            status="missing",
            peer_offline=True,
            summary="peer heartbeat packet missing",
        )

    heartbeat_packet_id = _text(heartbeat.get("packet_id"))
    peer_session_id = _heartbeat_peer_session_id(heartbeat)
    observed_at = _heartbeat_observed_at(heartbeat)
    expires_at = _heartbeat_expires_at(heartbeat, observed_at=observed_at, ttl_seconds=ttl)
    offline_packet = _latest_offline_packet(
        review_state,
        actor=actor_id,
        peer_actor=peer_id,
        heartbeat_packet_id=heartbeat_packet_id,
    )
    if offline_packet:
        return PeerHeartbeatEvidence(
            **base,
            peer_session_id=peer_session_id,
            heartbeat_packet_id=heartbeat_packet_id,
            peer_offline_packet_id=_text(offline_packet.get("packet_id")),
            heartbeat_observed_at_utc=observed_at,
            expires_at_utc=expires_at,
            status="peer_offline",
            peer_offline=True,
            summary="peer_offline packet recorded for latest heartbeat",
        )
    if peer_session_id and peer_session_id != session:
        return PeerHeartbeatEvidence(
            **base,
            peer_session_id=peer_session_id,
            heartbeat_packet_id=heartbeat_packet_id,
            heartbeat_observed_at_utc=observed_at,
            expires_at_utc=expires_at,
            status="session_mismatch",
            peer_offline=True,
            summary=(
                "peer_heartbeat targets "
                f"{peer_session_id} but live session is {session}"
            ),
        )
    if _expired(expires_at, now_utc=now_utc):
        return PeerHeartbeatEvidence(
            **base,
            peer_session_id=peer_session_id,
            heartbeat_packet_id=heartbeat_packet_id,
            heartbeat_observed_at_utc=observed_at,
            expires_at_utc=expires_at,
            status="expired",
            peer_offline=True,
            summary="peer heartbeat TTL expired",
        )
    return PeerHeartbeatEvidence(
        **base,
        peer_session_id=peer_session_id,
        heartbeat_packet_id=heartbeat_packet_id,
        heartbeat_observed_at_utc=observed_at,
        expires_at_utc=expires_at,
        status="alive",
        peer_offline=False,
        summary="peer heartbeat is within TTL",
    )


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


def _latest_offline_packet(
    review_state: Mapping[str, object],
    *,
    actor: str,
    peer_actor: str,
    heartbeat_packet_id: str,
) -> Mapping[str, object]:
    anchor = f"packet:{heartbeat_packet_id}" if heartbeat_packet_id else ""
    candidates = [
        packet
        for packet in _packet_rows(review_state)
        if _text(packet.get("kind")) == PEER_OFFLINE_PACKET_KIND
        and {actor, peer_actor} == {_text(packet.get("from_agent")), _text(packet.get("to_agent"))}
        and (not anchor or anchor in _anchor_refs(packet))
        and not _packet_resolved(packet)
    ]
    return _latest_by_event_id(candidates)


def _packet_rows(review_state: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows = review_state.get("packets")
    if not isinstance(rows, (list, tuple)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


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


def _heartbeat_peer_session_id(packet: Mapping[str, object]) -> str:
    metadata = _mapping(packet.get("metadata"))
    return (
        _text(packet.get("target_session_id"))
        or _text(metadata.get("peer_session_id"))
        or _text(metadata.get("target_session_id"))
    )


def _heartbeat_observed_at(packet: Mapping[str, object]) -> str:
    return _text(packet.get("posted_at")) or _text(packet.get("timestamp_utc"))


def _heartbeat_expires_at(
    packet: Mapping[str, object],
    *,
    observed_at: str,
    ttl_seconds: int,
) -> str:
    explicit = _text(packet.get("expires_at_utc"))
    if explicit:
        return explicit
    observed = _parse_utc(observed_at)
    if observed is None:
        return ""
    return _format_utc(observed + timedelta(seconds=ttl_seconds))


def _expired(expires_at: str, *, now_utc: str) -> bool:
    expiry = _parse_utc(expires_at)
    now = _parse_utc(now_utc) or datetime.now(UTC)
    if expiry is None:
        return False
    return expiry <= now


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


def _parse_utc(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = [
    "CONTRACT_ID",
    "DEFAULT_PEER_HEARTBEAT_TTL_SECONDS",
    "PeerHeartbeatEvidence",
    "resolve_peer_heartbeat",
]
