"""Tests for automation heartbeat suppression in reviewer follow loops."""

from __future__ import annotations

from pathlib import Path
import unittest

from dev.scripts.devctl.review_channel.reviewer_follow_heartbeat_guard import (
    maybe_refresh_automation_reviewer_heartbeat,
)
from dev.scripts.devctl.review_channel.reviewer_state_support import (
    EnsureHeartbeatResult,
)


class ReviewerFollowHeartbeatGuardTests(unittest.TestCase):
    def test_ensure_follow_does_not_call_bridge_writer(self) -> None:
        def forbidden_writer(**_kwargs) -> EnsureHeartbeatResult:
            raise AssertionError("ensure-follow automation rewrote bridge.md")

        result = maybe_refresh_automation_reviewer_heartbeat(
            repo_root=Path("/tmp/missing-repo"),
            bridge_path=Path("/tmp/missing-repo/bridge.md"),
            reason="ensure-follow",
            requested_reviewer_mode="active_dual_agent",
            ensure_reviewer_heartbeat_fn=forbidden_writer,
        )

        self.assertFalse(result.refreshed)
        self.assertTrue(result.suppressed)
        self.assertEqual(result.reviewer_mode, "active_dual_agent")
        self.assertIsNone(result.state_write)

    def test_reviewer_follow_does_not_call_bridge_writer(self) -> None:
        def forbidden_writer(**_kwargs) -> EnsureHeartbeatResult:
            raise AssertionError("automation follow heartbeat rewrote bridge.md")

        result = maybe_refresh_automation_reviewer_heartbeat(
            repo_root=Path("/tmp/missing-repo"),
            bridge_path=Path("/tmp/missing-repo/bridge.md"),
            reason="reviewer-follow",
            requested_reviewer_mode="active_dual_agent",
            ensure_reviewer_heartbeat_fn=forbidden_writer,
        )

        self.assertFalse(result.refreshed)
        self.assertTrue(result.suppressed)
        self.assertEqual(result.reviewer_mode, "active_dual_agent")
        self.assertIsNone(result.state_write)

    def test_non_automation_heartbeat_still_calls_bridge_writer(self) -> None:
        calls: list[str] = []

        def writer(**kwargs) -> EnsureHeartbeatResult:
            calls.append(str(kwargs["reason"]))
            return EnsureHeartbeatResult(
                refreshed=True,
                reviewer_mode="tools_only",
                reason=str(kwargs["reason"]),
                state_write=None,
                error=None,
            )

        result = maybe_refresh_automation_reviewer_heartbeat(
            repo_root=Path("/tmp/repo"),
            bridge_path=Path("/tmp/repo/bridge.md"),
            reason="manual-review",
            requested_reviewer_mode="tools_only",
            ensure_reviewer_heartbeat_fn=writer,
        )

        self.assertTrue(result.refreshed)
        self.assertFalse(result.suppressed)
        self.assertEqual(calls, ["manual-review"])


if __name__ == "__main__":
    unittest.main()
