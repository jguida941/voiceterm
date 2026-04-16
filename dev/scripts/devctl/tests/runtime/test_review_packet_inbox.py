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
