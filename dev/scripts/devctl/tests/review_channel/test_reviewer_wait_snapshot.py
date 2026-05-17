"""Tests for reviewer wait snapshots using typed reviewer providers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel._reviewer_wait_snapshot import (
    capture_reviewer_snapshot,
)
from dev.scripts.devctl.commands.review_channel._wait_shared import WaitDeps


def test_capture_reviewer_snapshot_uses_typed_reviewer_provider() -> None:
    report = {
        "collaboration": {
            "review_agent": "cursor",
            "role_assignments": (),
        },
        "reviewer_worker": {
            "current_hash": "tree-current",
            "reviewed_hash": "tree-reviewed",
        },
        "bridge_liveness": {
            "effective_reviewer_mode": "active_dual_agent",
        },
        "current_session": {
            "implementer_ack_revision": "rev-123",
            "implementer_ack_state": "current",
            "implementer_status": "ready",
            "implementer_state_hash": "impl-hash",
        },
        "attention": {
            "status": "review_needed",
            "summary": "Cursor reviewer has work",
            "recommended_action": "open_inbox",
        },
        "reviewer_runtime": {
            "review_acceptance": {
                "reviewer_accepted_implementer_state_hash": "accepted-hash",
            }
        },
        "packet_inbox": {
            "attention_revision": "attn-123",
            "agents": [
                {
                    "agent": "cursor",
                    "current_instruction_packet_id": "rev_pkt_cursor_instruction",
                    "latest_finding_packet_id": "rev_pkt_cursor_finding",
                    "pending_actionable_packet_ids": [
                        "rev_pkt_cursor_instruction",
                    ],
                    "expired_unresolved_packet_ids": [],
                    "attention_status": "wake_required",
                    "wake_reason": "instruction_pending",
                    "required_command": "python3 dev/scripts/devctl.py review-channel --action inbox",
                    "delivery_state": "notified",
                },
                {
                    "agent": "codex",
                    "current_instruction_packet_id": "",
                    "latest_finding_packet_id": "",
                    "pending_actionable_packet_ids": [],
                    "expired_unresolved_packet_ids": [],
                    "attention_status": "none",
                    "wake_reason": "",
                    "required_command": "",
                    "delivery_state": "",
                },
            ],
        },
    }
    deps = WaitDeps(
        run_status_action_fn=lambda **kwargs: (report, 0),
        read_bridge_text_fn=lambda **kwargs: "",
        monotonic_fn=lambda: 0.0,
        sleep_fn=lambda _seconds: None,
    )

    snapshot = capture_reviewer_snapshot(
        args=SimpleNamespace(),
        repo_root=Path("."),
        paths=SimpleNamespace(),
        deps=deps,
    )

    assert snapshot.latest_pending_packet_id == "rev_pkt_cursor_instruction"
    assert snapshot.latest_finding_packet_id == "rev_pkt_cursor_finding"
