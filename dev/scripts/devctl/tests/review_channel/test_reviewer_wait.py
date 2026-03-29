"""Focused tests for the reviewer-side bounded wait primitive."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands import review_channel as review_channel_command
from dev.scripts.devctl.commands.review_channel._reviewer_wait import (
    ReviewerWaitSnapshot,
    _implementer_changed,
    _implementer_update_ready,
    _reviewer_loop_unhealthy,
    run_reviewer_wait_action,
)
from dev.scripts.devctl.commands.review_channel._wait_shared import WaitDeps
from dev.scripts.devctl.commands.review_channel_command import (
    ReviewChannelAction,
    RuntimePaths,
    _coerce_action,
    _validate_args,
)
from dev.scripts.devctl.review_channel.parser import REVIEW_ACTION_CHOICES


def _snapshot(
    *,
    exit_code: int = 0,
    worktree_hash: str = "aaa",
    reviewed_hash: str = "aaa",
    implementer_ack_revision: str = "rev1",
    implementer_ack_state: str = "current",
    implementer_status_excerpt: str = "Working.",
    attention_status: str = "reviewed_hash_stale",
    attention_summary: str = "",
    attention_recommended_action: str = "",
    reviewer_mode: str = "active_dual_agent",
    report: dict | None = None,
) -> ReviewerWaitSnapshot:
    return ReviewerWaitSnapshot(
        report=report or {},
        exit_code=exit_code,
        worktree_hash=worktree_hash,
        reviewed_hash=reviewed_hash,
        implementer_ack_revision=implementer_ack_revision,
        implementer_ack_state=implementer_ack_state,
        implementer_status_excerpt=implementer_status_excerpt,
        attention_status=attention_status,
        attention_summary=attention_summary,
        attention_recommended_action=attention_recommended_action,
        reviewer_mode=reviewer_mode,
    )


def _write_review_state(
    root: Path,
    *,
    current_session: dict[str, object] | None = None,
) -> Path:
    payload = {
        "current_session": current_session
        or {
            "implementer_ack_revision": "rev1",
            "implementer_ack_state": "current",
            "implementer_status": "Working.",
        }
    }
    path = root / "review_state.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _status_report(
    root: Path,
    *,
    current_hash: str = "aaa",
    reviewed_hash: str = "aaa",
    reviewer_mode: str = "active_dual_agent",
    attention_status: str = "healthy",
    current_session: dict[str, object] | None = None,
    claude_ack_revision: str = "rev1",
    claude_ack_current: bool = True,
) -> dict[str, object]:
    review_state_path = _write_review_state(root, current_session=current_session)
    return {
        "reviewer_worker": {
            "current_hash": current_hash,
            "reviewed_hash": reviewed_hash,
            "reviewer_mode": reviewer_mode,
            "review_needed": current_hash != reviewed_hash,
        },
        "bridge_liveness": {
            "reviewer_mode": reviewer_mode,
            "claude_ack_revision": claude_ack_revision,
            "claude_ack_current": claude_ack_current,
            "claude_ack_present": True,
        },
        "projection_paths": {
            "review_state_path": str(review_state_path),
            "compact_path": str(review_state_path),
        },
        "attention": {"status": attention_status},
        "warnings": [],
        "errors": [],
    }


class TestImplementerUpdateReady(unittest.TestCase):
    """Verify _implementer_update_ready detects worktree vs reviewed hash divergence."""

    def test_same_hash_not_ready(self):
        snap = _snapshot(worktree_hash="abc", reviewed_hash="abc")
        self.assertFalse(_implementer_update_ready(snap))

    def test_different_hash_ready(self):
        snap = _snapshot(worktree_hash="abc", reviewed_hash="def")
        self.assertTrue(_implementer_update_ready(snap))

    def test_empty_hash_not_ready(self):
        snap = _snapshot(worktree_hash="", reviewed_hash="")
        self.assertFalse(_implementer_update_ready(snap))


class TestImplementerChanged(unittest.TestCase):
    """Verify _implementer_changed detects meaningful state transitions."""

    def test_worktree_hash_changed(self):
        baseline = _snapshot(worktree_hash="aaa")
        current = _snapshot(worktree_hash="bbb")
        self.assertTrue(_implementer_changed(baseline, current))

    def test_ack_revision_changed(self):
        baseline = _snapshot(implementer_ack_revision="rev1")
        current = _snapshot(implementer_ack_revision="rev2")
        self.assertTrue(_implementer_changed(baseline, current))

    def test_ack_state_changed(self):
        baseline = _snapshot(implementer_ack_state="stale")
        current = _snapshot(implementer_ack_state="current")
        self.assertTrue(_implementer_changed(baseline, current))

    def test_status_excerpt_changed(self):
        baseline = _snapshot(implementer_status_excerpt="Working.")
        current = _snapshot(implementer_status_excerpt="Done.")
        self.assertTrue(_implementer_changed(baseline, current))

    def test_no_change(self):
        baseline = _snapshot()
        current = _snapshot()
        self.assertFalse(_implementer_changed(baseline, current))


class TestReviewerLoopUnhealthy(unittest.TestCase):
    """Verify _reviewer_loop_unhealthy exits on bad states."""

    def test_nonzero_exit_unhealthy(self):
        snap = _snapshot(exit_code=1)
        self.assertTrue(_reviewer_loop_unhealthy(snap))

    def test_inactive_mode_unhealthy(self):
        snap = _snapshot(reviewer_mode="single_agent")
        self.assertTrue(_reviewer_loop_unhealthy(snap))

    def test_healthy_active_mode(self):
        snap = _snapshot(reviewer_mode="active_dual_agent", exit_code=0)
        self.assertFalse(_reviewer_loop_unhealthy(snap))

    def test_publisher_missing_unhealthy(self):
        snap = _snapshot(attention_status="publisher_missing")
        self.assertTrue(_reviewer_loop_unhealthy(snap))

    def test_checkpoint_required_unhealthy(self):
        snap = _snapshot(attention_status="checkpoint_required")
        self.assertTrue(_reviewer_loop_unhealthy(snap))


class TestReviewerWaitSurface(unittest.TestCase):
    """Verify the reviewer-wait action is wired into the public command surface."""

    def test_parser_exposes_reviewer_wait(self):
        self.assertIn("reviewer-wait", REVIEW_ACTION_CHOICES)

    def test_coerce_action_supports_reviewer_wait(self):
        self.assertIs(_coerce_action("reviewer-wait"), ReviewChannelAction.REVIEWER_WAIT)

    def test_validate_args_rejects_follow(self):
        args = SimpleNamespace(
            action="reviewer-wait",
            follow=True,
            rollover_threshold_pct=50,
            limit=20,
            await_ack_seconds=0,
            max_follow_snapshots=0,
            follow_interval_seconds=1,
            stale_minutes=30,
            expires_in_minutes=30,
            start_publisher_if_missing=False,
            format="json",
        )
        with self.assertRaisesRegex(
            ValueError,
            "review-channel reviewer-wait does not support --follow.",
        ):
            _validate_args(args)

    def test_dispatch_routes_to_reviewer_wait(self):
        with TemporaryDirectory() as tmp:
            bridge = Path(tmp) / "bridge.md"
            bridge.write_text("# bridge\n", encoding="utf-8")
            args = SimpleNamespace(action="reviewer-wait")
            paths = RuntimePaths(bridge_path=bridge)
            expected = ({"ok": True}, 0)
            with patch.object(
                review_channel_command,
                "_run_reviewer_wait_action",
                return_value=expected,
            ) as mocked:
                result = review_channel_command._dispatch_action(
                    args=args,
                    action=ReviewChannelAction.REVIEWER_WAIT,
                    repo_root=Path(tmp),
                    paths=paths,
                )
            self.assertEqual(result, expected)
            mocked.assert_called_once()


class TestReviewerWaitLoop(unittest.TestCase):
    """Integration test for the reviewer wait loop."""

    def _make_args(self, **overrides):
        defaults = {
            "action": "reviewer-wait",
            "timeout_minutes": 0,
            "follow_interval_seconds": 1,
            "format": "json",
        }
        defaults.update(overrides)
        return SimpleNamespace(**defaults)

    def _make_deps(self, reports):
        """Build deps that cycle through a list of (report, exit_code) tuples."""
        call_count = [0]
        mono_time = [0.0]

        def run_status(*, args, repo_root, paths):
            idx = min(call_count[0], len(reports) - 1)
            call_count[0] += 1
            return reports[idx]

        def read_bridge(path):
            return ""

        def monotonic():
            return mono_time[0]

        def sleep(seconds):
            mono_time[0] += seconds

        return WaitDeps(
            run_status_action_fn=run_status,
            read_bridge_text_fn=read_bridge,
            monotonic_fn=monotonic,
            sleep_fn=sleep,
        )

    def _make_paths(self, tmp_path):
        bridge = tmp_path / "bridge.md"
        bridge.write_text("# bridge")
        return RuntimePaths(bridge_path=bridge)

    def test_exits_immediately_when_implementer_already_changed(self):
        """If worktree hash differs from reviewed hash, exit immediately."""
        with TemporaryDirectory() as tmp:
            args = self._make_args()
            paths = self._make_paths(Path(tmp))
            report = _status_report(
                Path(tmp),
                current_hash="new_worktree",
                reviewed_hash="old_reviewed",
                attention_status="reviewed_hash_stale",
            )
            deps = self._make_deps([(report, 0)])

            result, exit_code = run_reviewer_wait_action(
                args=args,
                repo_root=Path(tmp),
                paths=paths,
                deps=deps,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                result["wait_state"]["stop_reason"],
                "implementer_update_ready",
            )
            self.assertTrue(result["wait_state"]["implementer_update_observed"])
            self.assertEqual(result["wait_attention_status"], "reviewed_hash_stale")
            self.assertIn("Review the current diff", result["warnings"][0])

    def test_exits_on_unhealthy_reviewer(self):
        """If reviewer mode is inactive, exit with error."""
        with TemporaryDirectory() as tmp:
            args = self._make_args()
            paths = self._make_paths(Path(tmp))
            report = _status_report(
                Path(tmp),
                reviewer_mode="single_agent",
                attention_status="inactive",
            )
            deps = self._make_deps([(report, 0)])

            result, exit_code = run_reviewer_wait_action(
                args=args,
                repo_root=Path(tmp),
                paths=paths,
                deps=deps,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(
                result["wait_state"]["stop_reason"],
                "reviewer_loop_unhealthy",
            )
            self.assertEqual(result["wait_attention_status"], "inactive")
            self.assertIn("review loop is unhealthy", result["errors"][0])

    def test_exits_when_typed_ack_revision_changes(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            args = self._make_args()
            paths = self._make_paths(tmp_path)
            baseline_root = tmp_path / "baseline"
            baseline_root.mkdir()
            current_root = tmp_path / "current"
            current_root.mkdir()
            baseline = _status_report(
                baseline_root,
                current_session={
                    "implementer_ack_revision": "rev1",
                    "implementer_ack_state": "stale",
                    "implementer_status": "Working.",
                },
            )
            current = _status_report(
                current_root,
                current_session={
                    "implementer_ack_revision": "rev2",
                    "implementer_ack_state": "current",
                    "implementer_status": "Working.",
                },
                claude_ack_revision="rev2",
            )
            deps = self._make_deps([(baseline, 0), (current, 0)])

            result, exit_code = run_reviewer_wait_action(
                args=args,
                repo_root=tmp_path,
                paths=paths,
                deps=deps,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                result["wait_state"]["stop_reason"],
                "implementer_update_observed",
            )
            self.assertEqual(
                result["wait_state"]["current_implementer_ack_revision"],
                "rev2",
            )
            self.assertEqual(result["wait_attention_status"], "healthy")
            self.assertIn("Re-read the worktree diff", result["warnings"][0])

    def test_times_out_when_no_change(self):
        """If nothing changes, should time out."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            args = self._make_args(timeout_minutes=0)
            args.follow_interval_seconds = 1
            paths = self._make_paths(tmp_path)
            report = _status_report(tmp_path, attention_status="healthy")
            deps = self._make_deps([(report, 0)] * 5)

            import dev.scripts.devctl.commands.review_channel._reviewer_wait as rw
            original_timeout = rw.DEFAULT_REVIEWER_WAIT_TIMEOUT_SECONDS
            rw.DEFAULT_REVIEWER_WAIT_TIMEOUT_SECONDS = 3
            try:
                result, exit_code = run_reviewer_wait_action(
                    args=args,
                    repo_root=tmp_path,
                    paths=paths,
                    deps=deps,
                )
            finally:
                rw.DEFAULT_REVIEWER_WAIT_TIMEOUT_SECONDS = original_timeout

            self.assertEqual(exit_code, 1)
            self.assertEqual(result["wait_state"]["stop_reason"], "timed_out")
            self.assertGreater(result["wait_state"]["polls_observed"], 0)
            self.assertEqual(result["wait_attention_status"], "healthy")
            self.assertIn("Timed out waiting", result["errors"][0])

    def test_timeout_surfaces_stale_ack_reason(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            args = self._make_args(timeout_minutes=0)
            args.follow_interval_seconds = 1
            paths = self._make_paths(tmp_path)
            report = _status_report(
                tmp_path,
                attention_status="claude_ack_stale",
                current_session={
                    "implementer_ack_revision": "rev2",
                    "implementer_ack_state": "stale",
                    "implementer_status": "Waiting.",
                },
                claude_ack_revision="rev1",
                claude_ack_current=False,
            )
            deps = self._make_deps([(report, 0)] * 5)

            import dev.scripts.devctl.commands.review_channel._reviewer_wait as rw

            original_timeout = rw.DEFAULT_REVIEWER_WAIT_TIMEOUT_SECONDS
            rw.DEFAULT_REVIEWER_WAIT_TIMEOUT_SECONDS = 3
            try:
                result, exit_code = run_reviewer_wait_action(
                    args=args,
                    repo_root=tmp_path,
                    paths=paths,
                    deps=deps,
                )
            finally:
                rw.DEFAULT_REVIEWER_WAIT_TIMEOUT_SECONDS = original_timeout

            self.assertEqual(exit_code, 1)
            self.assertEqual(result["wait_attention_status"], "claude_ack_stale")
            self.assertIn("Claude ACK remained stale", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
