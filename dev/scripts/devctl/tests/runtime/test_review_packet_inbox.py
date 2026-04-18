from __future__ import annotations

from dev.scripts.devctl.runtime.review_packet_inbox import (
    packet_inbox_from_review_state,
    summarize_packet_attention_open_findings,
)


def test_packet_inbox_drops_persisted_expired_ids_when_live_packets_are_gone() -> None:
    review_state = {
        "packets": [],
        "packet_inbox": {
            "attention_revision": "persisted-rev",
            "agents": [
                {
                    "agent": "codex",
                    "current_instruction_packet_id": "",
                    "latest_finding_packet_id": "rev_pkt_0649",
                    "pending_actionable_packet_ids": [],
                    "expired_unresolved_packet_ids": ["rev_pkt_0649"],
                    "attention_status": "review_needed",
                    "wake_reason": "expired_unresolved_packet",
                    "required_command": "python3 dev/scripts/devctl.py review-channel --action inbox --target codex --status pending --terminal none --format md",
                    "attention_revision": "codex-attention-rev",
                    "delivery_state": "unseen",
                }
            ],
        },
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    codex = packet_inbox.for_agent("codex")
    assert codex is not None
    assert codex.latest_finding_packet_id == ""
    assert codex.expired_unresolved_packet_ids == ()
    assert codex.attention_status == "none"
    assert codex.wake_reason == ""


def test_open_findings_summary_does_not_revive_evicted_expired_packets() -> None:
    review_state = {
        "packets": [],
        "queue": {
            "pending_total": 0,
            "stale_packet_count": 0,
        },
        "packet_inbox": {
            "attention_revision": "persisted-rev",
            "agents": [
                {
                    "agent": "codex",
                    "current_instruction_packet_id": "",
                    "latest_finding_packet_id": "rev_pkt_0649",
                    "pending_actionable_packet_ids": [],
                    "expired_unresolved_packet_ids": ["rev_pkt_0649"],
                    "attention_status": "review_needed",
                    "wake_reason": "expired_unresolved_packet",
                    "required_command": "python3 dev/scripts/devctl.py review-channel --action inbox --target codex --status pending --terminal none --format md",
                    "attention_revision": "codex-attention-rev",
                    "delivery_state": "unseen",
                }
            ],
        },
    }

    summary = summarize_packet_attention_open_findings(
        review_state,
        fallback="none",
        agent="codex",
    )

    assert summary == "none"


def test_packet_inbox_indexes_current_instruction_by_target_agent() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_cursor_1",
                "status": "pending",
                "summary": "Cursor owns the active instruction",
                "body": "Cursor owns the active instruction",
                "kind": "instruction",
                "from_agent": "codex",
                "to_agent": "cursor",
                "requested_action": "continue",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    cursor = packet_inbox.for_agent("cursor")
    codex = packet_inbox.for_agent("codex")
    assert cursor is not None
    assert codex is not None
    assert cursor.current_instruction_packet_id == "rev_pkt_cursor_1"
    assert codex.current_instruction_packet_id == ""
