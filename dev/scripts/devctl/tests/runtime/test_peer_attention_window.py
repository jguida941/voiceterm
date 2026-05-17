from __future__ import annotations

from dev.scripts.devctl.runtime.peer_attention_window import (
    build_attention_window_projection,
)


def test_attention_window_keeps_blocking_packet_separate_from_ambient_finding() -> None:
    projection = build_attention_window_projection(
        {
            "agent_sync": {"source_latest_event_id": "rev_evt_20"},
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "codex",
                        "role": "implementer",
                        "session_id": "codex-session",
                    }
                ]
            },
            "packets": [
                _packet(
                    packet_id="rev_pkt_1",
                    kind="finding",
                    summary="P1 review note for the active slice",
                    latest_event_id="rev_evt_10",
                ),
                _packet(
                    packet_id="rev_pkt_2",
                    kind="action_request",
                    summary="Checkpoint handoff requires review",
                    requested_action="checkpoint_publication_handoff",
                    latest_event_id="rev_evt_11",
                ),
            ],
        },
    )

    payload = projection.to_dict()
    window = payload["windows"][0]
    rows = window["peer_recent_packets"]
    assert window["actor_id"] == "codex"
    assert window["blocking_consume_required"] is True
    assert window["blocking_packet_ids"] == ["rev_pkt_2"]
    assert rows[0]["packet_id"] == "rev_pkt_2"
    assert rows[0]["urgency"] == "blocking"
    assert rows[0]["mutation_blocking"] is True
    assert rows[1]["packet_id"] == "rev_pkt_1"
    assert rows[1]["urgency"] == "urgent"
    assert rows[1]["mutation_blocking"] is False


def test_attention_window_does_not_leak_exact_session_packet_to_peer_session() -> None:
    projection = build_attention_window_projection(
        {
            "agent_work_board": {
                "rows": [
                    {"actor_id": "claude", "role": "reviewer", "session_id": "s1"},
                    {"actor_id": "claude", "role": "reviewer", "session_id": "s2"},
                ]
            },
            "packets": [
                _packet(
                    packet_id="rev_pkt_session",
                    to_agent="claude",
                    target_role="reviewer",
                    target_session_id="s1",
                    latest_event_id="rev_evt_30",
                )
            ],
        },
    )

    windows = projection.to_dict()["windows"]
    by_session = {window["session_id"]: window for window in windows}
    assert by_session["s1"]["latest_attention_packet_id"] == "rev_pkt_session"
    assert by_session["s2"]["latest_attention_packet_id"] == ""
    assert by_session["s2"]["peer_recent_packets"] == []


def test_attention_window_omits_terminal_packets() -> None:
    projection = build_attention_window_projection(
        {
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "codex",
                        "role": "implementer",
                        "session_id": "codex-session",
                    }
                ]
            },
            "packets": [
                _packet(
                    packet_id="rev_pkt_done",
                    lifecycle_current_state="applied",
                    latest_event_id="rev_evt_40",
                )
            ],
        },
    )

    window = projection.to_dict()["windows"][0]
    assert window["latest_attention_packet_id"] == ""
    assert window["blocking_consume_required"] is False
    assert window["blocking_packet_ids"] == []
    assert window["peer_recent_packets"] == []


def test_attention_window_does_not_let_consumed_action_request_mask_new_peer_packet() -> None:
    projection = build_attention_window_projection(
        {
            "agent_work_board": {
                "rows": [
                    {
                        "actor_id": "codex",
                        "role": "implementer",
                        "session_id": "codex-session",
                    }
                ]
            },
            "packets": [
                _packet(
                    packet_id="rev_pkt_old",
                    kind="action_request",
                    status="acked",
                    lifecycle_current_state="in_progress",
                    latest_event_id="rev_evt_10",
                ),
                _packet(
                    packet_id="rev_pkt_new",
                    kind="finding",
                    summary="Reviewer note for this exact session",
                    latest_event_id="rev_evt_99",
                ),
            ],
        },
    )

    window = projection.to_dict()["windows"][0]
    rows = window["peer_recent_packets"]
    assert window["latest_attention_packet_id"] == "rev_pkt_new"
    assert window["blocking_consume_required"] is False
    assert window["blocking_packet_ids"] == []
    assert rows[0]["packet_id"] == "rev_pkt_new"
    assert rows[1]["packet_id"] == "rev_pkt_old"
    assert rows[1]["consume_state"] == "acked"
    assert rows[1]["mutation_blocking"] is False


def _packet(
    *,
    packet_id: str,
    kind: str = "action_request",
    to_agent: str = "codex",
    from_agent: str = "claude",
    target_role: str = "implementer",
    target_session_id: str = "codex-session",
    status: str = "pending",
    lifecycle_current_state: str = "delivery_pending",
    summary: str = "Packet summary",
    requested_action: str = "",
    latest_event_id: str = "rev_evt_1",
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "kind": kind,
        "status": status,
        "lifecycle_current_state": lifecycle_current_state,
        "summary": summary,
        "target_role": target_role,
        "target_session_id": target_session_id,
        "requested_action": requested_action,
        "latest_event_id": latest_event_id,
    }
