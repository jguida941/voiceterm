"""Focused tests for event-backed implementer_completion_stall detection."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.event_projection import _detect_implementer_stall


def test_no_stall_when_status_has_no_markers() -> None:
    """No stall markers in claude_status/ack → not stalled."""
    assert _detect_implementer_stall(
        claude_status="Working on check_code_shape.py fix",
        claude_ack="acknowledged; instruction-rev: abc123",
        instruction="Fix the code_shape violation",
        poll_status="",
        reviewer_mode="active_dual_agent",
    ) is False


def test_stall_when_parked_on_promotion() -> None:
    """Stall markers present + no wait state in instruction → stalled."""
    assert _detect_implementer_stall(
        claude_status="waiting for codex review",
        claude_ack="acknowledged; instruction-rev: abc123",
        instruction="Fix the code_shape violation",
        poll_status="",
        reviewer_mode="active_dual_agent",
    ) is True


def test_not_stalled_when_instruction_has_wait_marker() -> None:
    """Stall markers present BUT instruction has hold-steady → NOT stalled."""
    assert _detect_implementer_stall(
        claude_status="waiting for codex review",
        claude_ack="acknowledged; instruction-rev: abc123",
        instruction="hold steady — Codex committing/pushing current tree",
        poll_status="",
        reviewer_mode="active_dual_agent",
    ) is False


def test_stall_when_reviewer_mode_inactive() -> None:
    """Stall markers + inactive reviewer → stalled."""
    assert _detect_implementer_stall(
        claude_status="waiting for codex review",
        claude_ack="acknowledged",
        instruction="Fix the bug",
        poll_status="",
        reviewer_mode="single_agent",
    ) is True


def test_not_stalled_with_promotion_pending_in_instruction() -> None:
    """Wait marker 'promotion pending' in instruction → NOT stalled."""
    assert _detect_implementer_stall(
        claude_status="continuing to poll",
        claude_ack="acknowledged",
        instruction="promotion pending — reviewer will promote next slice",
        poll_status="",
        reviewer_mode="active_dual_agent",
    ) is False


def test_stall_from_ack_text() -> None:
    """Stall markers in claude_ack (not just status) → stalled."""
    assert _detect_implementer_stall(
        claude_status="",
        claude_ack="instruction unchanged, continuing to poll",
        instruction="Implement the bridge-poll action",
        poll_status="",
        reviewer_mode="active_dual_agent",
    ) is True


def test_stall_from_no_change_continuing_status() -> None:
    """Low-information no-op polling text must count as a stall marker."""
    assert _detect_implementer_stall(
        claude_status="No change. Continuing.",
        claude_ack="acknowledged; instruction-rev: abc123",
        instruction="Implement the bridge-poll action",
        poll_status="",
        reviewer_mode="active_dual_agent",
    ) is True
