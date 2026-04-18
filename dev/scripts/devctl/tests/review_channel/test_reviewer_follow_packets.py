"""Tests for reviewer-follow packet projection provider routing."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.review_channel.reviewer_follow_packets import (
    attach_reviewer_packets,
)


def test_attach_reviewer_packets_uses_typed_reviewer_provider() -> None:
    report = {
        "packet_inbox": {
            "attention_revision": "rev-1",
            "agents": [
                {
                    "agent": "cursor",
                    "attention_status": "review_needed",
                    "wake_reason": "finding_pending",
                    "pending_actionable_packet_ids": ["rev_pkt_cursor"],
                    "latest_finding_packet_id": "rev_pkt_cursor_finding",
                    "current_instruction_packet_id": "rev_pkt_cursor_instruction",
                },
                {
                    "agent": "codex",
                    "attention_status": "healthy",
                    "wake_reason": "",
                    "pending_actionable_packet_ids": [],
                    "latest_finding_packet_id": "rev_pkt_codex_finding",
                    "current_instruction_packet_id": "",
                },
            ],
        },
        "packets": [
            {
                "packet_id": "rev_pkt_cursor_finding",
                "kind": "finding",
                "from_agent": "claude",
                "summary": "Cursor reviewer finding",
                "posted_at": "2026-04-18T01:00:00Z",
            },
            {
                "packet_id": "rev_pkt_cursor_instruction",
                "kind": "instruction",
                "from_agent": "claude",
                "summary": "Cursor reviewer instruction",
                "posted_at": "2026-04-18T01:01:00Z",
            },
            {
                "packet_id": "rev_pkt_codex_finding",
                "kind": "finding",
                "from_agent": "claude",
                "summary": "Codex reviewer finding",
                "posted_at": "2026-04-18T01:02:00Z",
            },
        ],
    }
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            review_agent="cursor",
            role_assignments=(),
        )
    )

    with patch(
        "dev.scripts.devctl.review_channel.reviewer_follow_packets.load_current_review_state",
        return_value=review_state,
    ):
        attach_reviewer_packets(report=report, repo_root=Path("."))

    projection = report["reviewer_packets"]
    assert projection["pending_total"] == 1
    assert projection["latest_packet_id"] == "rev_pkt_cursor_finding"
    assert projection["actionable_packet_id"] == "rev_pkt_cursor_instruction"
