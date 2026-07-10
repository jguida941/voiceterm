from __future__ import annotations

from dev.scripts.devctl.runtime.collaboration_packet_kinds import (
    PEER_HEARTBEAT_PACKET_KIND,
    PEER_OFFLINE_PACKET_KIND,
)
from dev.scripts.devctl.runtime.peer_heartbeat import resolve_peer_heartbeat


def test_peer_heartbeat_within_explicit_expiry_is_alive() -> None:
    evidence = resolve_peer_heartbeat(
        {
            "packets": [
                _packet(
                    packet_id="rev_pkt_heartbeat",
                    kind=PEER_HEARTBEAT_PACKET_KIND,
                    from_agent="claude",
                    to_agent="codex",
                    target_session_id="codex-s1",
                    posted_at="2026-05-11T22:30:00Z",
                    expires_at_utc="2026-05-11T22:35:00Z",
                )
            ]
        },
        actor="codex",
        session_id="codex-s1",
        peer_actor="claude",
        now_utc="2026-05-11T22:34:00Z",
    )

    assert evidence.status == "alive"
    assert evidence.peer_offline is False
    assert evidence.heartbeat_packet_id == "rev_pkt_heartbeat"
    assert evidence.expires_at_utc == "2026-05-11T22:35:00Z"


def test_peer_heartbeat_ttl_expiry_surfaces_peer_offline() -> None:
    evidence = resolve_peer_heartbeat(
        {
            "packets": [
                _packet(
                    packet_id="rev_pkt_heartbeat",
                    kind=PEER_HEARTBEAT_PACKET_KIND,
                    from_agent="claude",
                    to_agent="codex",
                    target_session_id="codex-s1",
                    posted_at="2026-05-11T22:30:00Z",
                )
            ]
        },
        actor="codex",
        session_id="codex-s1",
        peer_actor="claude",
        now_utc="2026-05-11T22:36:00Z",
        ttl_seconds=300,
    )

    assert evidence.status == "expired"
    assert evidence.peer_offline is True
    assert evidence.expires_at_utc == "2026-05-11T22:35:00Z"


def test_peer_offline_packet_wins_over_unexpired_heartbeat() -> None:
    evidence = resolve_peer_heartbeat(
        {
            "packets": [
                _packet(
                    packet_id="rev_pkt_heartbeat",
                    kind=PEER_HEARTBEAT_PACKET_KIND,
                    from_agent="claude",
                    to_agent="codex",
                    target_session_id="codex-s1",
                    posted_at="2026-05-11T22:30:00Z",
                    expires_at_utc="2026-05-11T22:40:00Z",
                    latest_event_id="rev_evt_10",
                ),
                _packet(
                    packet_id="rev_pkt_offline",
                    kind=PEER_OFFLINE_PACKET_KIND,
                    from_agent="codex",
                    to_agent="claude",
                    anchor_refs=["packet:rev_pkt_heartbeat"],
                    latest_event_id="rev_evt_11",
                ),
            ]
        },
        actor="codex",
        session_id="codex-s1",
        peer_actor="claude",
        now_utc="2026-05-11T22:31:00Z",
    )

    assert evidence.status == "peer_offline"
    assert evidence.peer_offline is True
    assert evidence.peer_offline_packet_id == "rev_pkt_offline"


def test_peer_heartbeat_session_mismatch_requires_offline_evidence() -> None:
    evidence = resolve_peer_heartbeat(
        {
            "packets": [
                _packet(
                    packet_id="rev_pkt_heartbeat",
                    kind=PEER_HEARTBEAT_PACKET_KIND,
                    from_agent="claude",
                    to_agent="codex",
                    target_session_id="codex-old",
                    posted_at="2026-05-11T22:30:00Z",
                    expires_at_utc="2026-05-11T22:40:00Z",
                )
            ]
        },
        actor="codex",
        session_id="codex-new",
        peer_actor="claude",
        now_utc="2026-05-11T22:31:00Z",
    )

    assert evidence.status == "session_mismatch"
    assert evidence.peer_offline is True
    assert evidence.peer_session_id == "codex-old"


def test_missing_peer_heartbeat_is_peer_offline() -> None:
    evidence = resolve_peer_heartbeat(
        {"packets": []},
        actor="codex",
        session_id="codex-s1",
        peer_actor="claude",
        now_utc="2026-05-11T22:31:00Z",
    )

    assert evidence.status == "missing"
    assert evidence.peer_offline is True


def _packet(
    *,
    packet_id: str,
    kind: str,
    from_agent: str,
    to_agent: str,
    target_session_id: str = "",
    posted_at: str = "2026-05-11T22:30:00Z",
    expires_at_utc: str = "",
    anchor_refs: list[str] | None = None,
    latest_event_id: str = "rev_evt_1",
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "kind": kind,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "target_session_id": target_session_id,
        "posted_at": posted_at,
        "expires_at_utc": expires_at_utc,
        "anchor_refs": anchor_refs or [],
        "latest_event_id": latest_event_id,
        "status": "pending",
        "lifecycle_current_state": "pending",
    }
