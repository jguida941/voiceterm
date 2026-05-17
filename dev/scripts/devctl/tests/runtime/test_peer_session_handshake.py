from __future__ import annotations

from dev.scripts.devctl.runtime.collaboration_packet_kinds import (
    PEER_SESSION_HANDSHAKE_PACKET_KIND,
    SESSION_RESYNC_PACKET_KIND,
)
from dev.scripts.devctl.runtime.peer_session_handshake import (
    resolve_peer_session_handshake,
)


def test_peer_session_handshake_matches_live_session() -> None:
    evidence = resolve_peer_session_handshake(
        {
            "packets": [
                _packet(
                    packet_id="rev_pkt_handshake",
                    kind=PEER_SESSION_HANDSHAKE_PACKET_KIND,
                    from_agent="claude",
                    to_agent="codex",
                    target_session_id="codex-s1",
                )
            ]
        },
        actor="codex",
        session_id="codex-s1",
        peer_actor="claude",
    )

    assert evidence.status == "matched"
    assert evidence.session_resync_required is False
    assert evidence.handshake_packet_id == "rev_pkt_handshake"


def test_peer_session_handshake_mismatch_requires_session_resync() -> None:
    evidence = resolve_peer_session_handshake(
        {
            "packets": [
                _packet(
                    packet_id="rev_pkt_handshake",
                    kind=PEER_SESSION_HANDSHAKE_PACKET_KIND,
                    from_agent="claude",
                    to_agent="codex",
                    target_session_id="codex-old",
                )
            ]
        },
        actor="codex",
        session_id="codex-new",
        peer_actor="claude",
    )

    assert evidence.status == "mismatch"
    assert evidence.session_resync_required is True
    assert evidence.peer_session_id == "codex-old"


def test_session_resync_packet_satisfies_handshake_mismatch() -> None:
    evidence = resolve_peer_session_handshake(
        {
            "packets": [
                _packet(
                    packet_id="rev_pkt_handshake",
                    kind=PEER_SESSION_HANDSHAKE_PACKET_KIND,
                    from_agent="claude",
                    to_agent="codex",
                    target_session_id="codex-old",
                    latest_event_id="rev_evt_10",
                ),
                _packet(
                    packet_id="rev_pkt_resync",
                    kind=SESSION_RESYNC_PACKET_KIND,
                    from_agent="codex",
                    to_agent="claude",
                    anchor_refs=["packet:rev_pkt_handshake"],
                    latest_event_id="rev_evt_11",
                ),
            ]
        },
        actor="codex",
        session_id="codex-new",
        peer_actor="claude",
    )

    assert evidence.status == "resynced"
    assert evidence.session_resync_required is False
    assert evidence.session_resync_packet_id == "rev_pkt_resync"


def test_missing_peer_session_handshake_requires_resync_evidence() -> None:
    evidence = resolve_peer_session_handshake(
        {"packets": []},
        actor="codex",
        session_id="codex-s1",
        peer_actor="claude",
    )

    assert evidence.status == "missing"
    assert evidence.session_resync_required is True


def _packet(
    *,
    packet_id: str,
    kind: str,
    from_agent: str,
    to_agent: str,
    target_session_id: str = "",
    anchor_refs: list[str] | None = None,
    latest_event_id: str = "rev_evt_1",
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "kind": kind,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "target_session_id": target_session_id,
        "anchor_refs": anchor_refs or [],
        "latest_event_id": latest_event_id,
        "status": "pending",
        "lifecycle_current_state": "pending",
    }
