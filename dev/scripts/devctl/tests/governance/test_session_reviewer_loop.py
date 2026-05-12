"""Tests for typed reviewer-agent routing in the session reviewer loop."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands.governance.session_reviewer_loop import (
    _has_pending_work,
    _run_ensure_tick,
)


def test_has_pending_work_uses_typed_reviewer_provider() -> None:
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            review_agent="cursor",
            role_assignments=(),
        )
    )

    with (
        patch(
            "dev.scripts.devctl.commands.governance.session_reviewer_loop.load_current_review_state",
            return_value=review_state,
        ),
        patch(
            "dev.scripts.devctl.commands.governance.session_reviewer_loop.load_pending_reviewer_packets",
            return_value=({"packet_id": "rev_pkt_cursor"},),
        ) as mock_pending,
        patch(
            "dev.scripts.devctl.commands.governance.session_reviewer_loop._has_reviewer_relevant_changes",
            return_value=False,
        ),
    ):
        assert _has_pending_work(Path("/tmp/repo")) is True

    mock_pending.assert_called_once_with(
        Path("/tmp/repo"),
        reviewer_agent="cursor",
    )


def test_ensure_tick_uses_snapshot_bound_follow_without_inactivity_timeout() -> None:
    with patch(
        "dev.scripts.devctl.commands.governance.session_reviewer_loop.subprocess.run"
    ) as run_mock:
        _run_ensure_tick(Path("/tmp/repo"), 30)

    command = run_mock.call_args.args[0]
    assert "--max-follow-snapshots" in command
    assert command[command.index("--max-follow-snapshots") + 1] == "1"
    assert "--follow-inactivity-timeout-seconds" in command
    assert command[command.index("--follow-inactivity-timeout-seconds") + 1] == "0"
