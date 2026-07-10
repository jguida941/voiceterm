"""Tests for conversation and task board collaboration modules."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.operator_console.collaboration.conversation_state import (
    AGENT_DISPLAY_NAMES,
    AGENT_ROLES,
    ConversationMessage,
    ConversationSnapshot,
    build_conversation_snapshot,
    _body_preview,
    _parse_packet_to_message,
)
from app.operator_console.collaboration.task_board_state import (
    TaskBoardSnapshot,
    TaskTicket,
    build_task_board_snapshot,
    _column_for_status,
)


class TestConversationMessage(unittest.TestCase):
    def test_construction(self) -> None:
        msg = ConversationMessage(
            packet_id="pkt-001",
            from_agent="operator",
            to_agent="claude",
            kind="instruction",
            summary="Fix auth flow",
            body_preview="Fix the token refresh...",
            timestamp="2026-03-09T12:00:00Z",
            status="posted",
        )
        assert msg.packet_id == "pkt-001"
        assert msg.from_agent == "operator"
        assert msg.guard_passed is True


class TestBodyPreview(unittest.TestCase):
    def test_short_text_unchanged(self) -> None:
        assert _body_preview("hello world") == "hello world"

    def test_long_text_truncated(self) -> None:
        text = "a " * 200
        result = _body_preview(text, limit=20)
        assert len(result) <= 21
        assert result.endswith("\u2026")

    def test_whitespace_collapsed(self) -> None:
        assert _body_preview("hello   world\n\nfoo") == "hello world foo"


class TestParsePacket(unittest.TestCase):
    def test_valid_packet(self) -> None:
        packet = {
            "packet_id": "pkt-001",
            "from_agent": "codex",
            "to_agent": "operator",
            "kind": "finding",
            "summary": "Found 3 issues",
            "body": "Detailed review...",
            "posted_at": "2026-03-09T12:00:00Z",
            "status": "posted",
            "policy_hint": "review_only",
        }
        msg = _parse_packet_to_message(packet)
        assert msg is not None
        assert msg.packet_id == "pkt-001"
        assert msg.from_agent == "codex"
        assert msg.kind == "finding"

    def test_missing_packet_id_returns_none(self) -> None:
        assert _parse_packet_to_message({}) is None

    def test_defaults(self) -> None:
        msg = _parse_packet_to_message({"packet_id": "x"})
        assert msg is not None
        assert msg.from_agent == "system"
        assert msg.to_agent == "operator"
        assert msg.status == "posted"


class TestBuildConversationSnapshot(unittest.TestCase):
    def test_empty_returns_empty_snapshot(self) -> None:
        snap = build_conversation_snapshot()
        assert snap.messages == ()
        assert snap.last_refresh != ""

    def test_from_packets(self) -> None:
        packets = [
            {"packet_id": "b", "posted_at": "2026-03-09T12:01:00Z", "summary": "second"},
            {"packet_id": "a", "posted_at": "2026-03-09T12:00:00Z", "summary": "first"},
        ]
        snap = build_conversation_snapshot(history_packets=packets)
        assert len(snap.messages) == 2
        assert snap.messages[0].packet_id == "a"  # sorted by timestamp
        assert snap.messages[1].packet_id == "b"

    def test_from_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"packets": [{"packet_id": "x", "summary": "test"}]}, f)
            f.flush()
            snap = build_conversation_snapshot(review_state_path=Path(f.name))
        assert len(snap.messages) == 1

    def test_missing_file_returns_empty(self) -> None:
        snap = build_conversation_snapshot(
            review_state_path=Path("/nonexistent/path.json")
        )
        assert snap.messages == ()


class TestColumnForStatus(unittest.TestCase):
    def test_posted_is_pending(self) -> None:
        assert _column_for_status("posted") == "pending"

    def test_acked_is_in_progress(self) -> None:
        assert _column_for_status("acked") == "in_progress"

    def test_reviewed_is_review(self) -> None:
        assert _column_for_status("reviewed") == "review"

    def test_applied_is_done(self) -> None:
        assert _column_for_status("applied") == "done"

    def test_unknown_defaults_to_pending(self) -> None:
        assert _column_for_status("unknown_status") == "pending"


class TestTaskTicket(unittest.TestCase):
    def test_construction(self) -> None:
        ticket = TaskTicket(
            ticket_id="pkt-001",
            summary="Fix auth",
            assigned_agent="claude",
            status="in_progress",
            kind="instruction",
            last_updated="2026-03-09T12:00:00Z",
        )
        assert ticket.assigned_agent == "claude"
        assert ticket.packet_count == 1


class TestBuildTaskBoardSnapshot(unittest.TestCase):
    def test_empty_returns_empty_board(self) -> None:
        board = build_task_board_snapshot()
        assert board.pending == ()
        assert board.in_progress == ()
        assert board.review == ()
        assert board.done == ()

    def test_packets_bucketed_correctly(self) -> None:
        packets = [
            {"packet_id": "a", "status": "posted", "to_agent": "claude", "summary": "task 1"},
            {"packet_id": "b", "status": "acked", "to_agent": "codex", "summary": "task 2"},
            {"packet_id": "c", "status": "reviewed", "to_agent": "claude", "summary": "task 3"},
            {"packet_id": "d", "status": "applied", "to_agent": "cursor", "summary": "task 4"},
        ]
        board = build_task_board_snapshot(history_packets=packets)
        assert len(board.pending) == 1
        assert len(board.in_progress) == 1
        assert len(board.review) == 1
        assert len(board.done) == 1
        assert board.pending[0].ticket_id == "a"
        assert board.done[0].assigned_agent == "cursor"

    def test_skips_invalid_packets(self) -> None:
        packets = [
            {"packet_id": "a", "status": "posted"},
            {},  # no packet_id
            {"packet_id": "b", "status": "acked"},
        ]
        board = build_task_board_snapshot(history_packets=packets)
        assert len(board.pending) == 1
        assert len(board.in_progress) == 1


class TestAgentConstants(unittest.TestCase):
    def test_cursor_in_display_names(self) -> None:
        assert "cursor" in AGENT_DISPLAY_NAMES
        assert AGENT_DISPLAY_NAMES["cursor"] == "Cursor"

    def test_cursor_in_roles(self) -> None:
        assert AGENT_ROLES["cursor"] == "Editor"
