"""Tests for packet loop-attention policy."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.packet_loop_attention import (
    packet_requires_loop_attention,
)


def test_review_accepted_lifecycle_does_not_create_loop_attention() -> None:
    assert not packet_requires_loop_attention(
        {
            "kind": "review_accepted",
            "to_agent": "codex",
            "status": "pending",
            "lifecycle_current_state": "review_accepted",
            "requested_action": "review_only",
            "policy_hint": "review_only",
        }
    )


def test_pending_task_progress_still_creates_loop_attention() -> None:
    assert packet_requires_loop_attention(
        {
            "kind": "task_progress",
            "to_agent": "codex",
            "status": "pending",
            "lifecycle_current_state": "task_progress",
            "requested_action": "review_only",
            "policy_hint": "review_only",
        }
    )
