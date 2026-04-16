"""Focused tests for the reviewer-side bounded wait primitive."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands import review_channel as review_channel_command
from dev.scripts.devctl.commands.review_channel import status as review_channel_status_mod
from dev.scripts.devctl.commands.review_channel._reviewer_wait import (
    ReviewerWaitSnapshot,
    _accepted_hash_diverged,
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
    latest_pending_packet_id: str = "",
    latest_finding_packet_id: str = "",
    packet_inbox_available: bool = True,
    packet_attention_revision: str = "attn_rev_1",
    implementer_state_hash: str = "",
    reviewer_accepted_implementer_state_hash: str = "",
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
        latest_pending_packet_id=latest_pending_packet_id,
        latest_finding_packet_id=latest_finding_packet_id,
        packet_inbox_available=packet_inbox_available,
        packet_attention_revision=packet_attention_revision,
        implementer_state_hash=implementer_state_hash,
        reviewer_accepted_implementer_state_hash=reviewer_accepted_implementer_state_hash,
    )


def _write_review_state(
    root: Path,
    *,
    current_session: dict[str, object] | None = None,
    packet_inbox: dict[str, object] | None = None,
) -> Path:
    payload = {
        "current_session": current_session
        or {
            "implementer_ack_revision": "rev1",
            "implementer_ack_state": "current",
            "implementer_status": "Working.",
        },
        "packet_inbox": packet_inbox
        or {
            "attention_revision": "attn_rev_1",
            "agents": [
                {
                    "agent": "codex",
                    "current_instruction_packet_id": "",
                    "latest_finding_packet_id": "",
                    "pending_actionable_packet_ids": [],
                    "expired_unresolved_packet_ids": [],
                    "attention_status": "none",
                    "wake_reason": "",
                    "required_command": "",
                    "attention_revision": "codex_attn_rev_1",
                    "delivery_state": "idle",
                }
            ],
        },
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
    packet_inbox: dict[str, object] | None = None,
    claude_ack_revision: str = "rev1",
    claude_ack_current: bool = True,
    reviewer_accepted_implementer_state_hash: str = "",
) -> dict[str, object]:
    review_state_path = _write_review_state(
        root,
        current_session=current_session,
        packet_inbox=packet_inbox,
    )
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
        "reviewer_runtime": {
            "review_acceptance": {
                "reviewer_accepted_implementer_state_hash": reviewer_accepted_implementer_state_hash,
            },
        },
        "attention": {"status": attention_status},
        "packet_inbox": json.loads(review_state_path.read_text(encoding="utf-8"))["packet_inbox"],
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

    def test_pending_packet_is_ready(self):
        snap = _snapshot(latest_pending_packet_id="rev_pkt_123")
        self.assertTrue(_implementer_update_ready(snap))


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

    def test_pending_packet_changed(self):
        baseline = _snapshot(latest_pending_packet_id="")
        current = _snapshot(latest_pending_packet_id="rev_pkt_456")
        self.assertTrue(_implementer_changed(baseline, current))

    def test_no_change(self):
        baseline = _snapshot()
        current = _snapshot()
        self.assertFalse(_implementer_changed(baseline, current))


class TestAcceptedHashDiverged(unittest.TestCase):
    """Verify _accepted_hash_diverged detects semantic implementer state changes."""

    def test_diverged_when_hashes_differ(self):
        snap = _snapshot(
            implementer_state_hash="hash_new",
            reviewer_accepted_implementer_state_hash="hash_old",
        )
        self.assertTrue(_accepted_hash_diverged(snap))

    def test_not_diverged_when_hashes_match(self):
        snap = _snapshot(
            implementer_state_hash="hash_same",
            reviewer_accepted_implementer_state_hash="hash_same",
        )
        self.assertFalse(_accepted_hash_diverged(snap))

    def test_not_diverged_when_implementer_hash_missing(self):
        snap = _snapshot(
            implementer_state_hash="",
            reviewer_accepted_implementer_state_hash="hash_old",
        )
        self.assertFalse(_accepted_hash_diverged(snap))

    def test_not_diverged_when_accepted_hash_missing(self):
        """Gracefully skips when Slice 2 state is absent."""
        snap = _snapshot(
            implementer_state_hash="hash_new",
            reviewer_accepted_implementer_state_hash="",
        )
        self.assertFalse(_accepted_hash_diverged(snap))

    def test_not_diverged_when_both_missing(self):
        snap = _snapshot(
            implementer_state_hash="",
            reviewer_accepted_implementer_state_hash="",
        )
        self.assertFalse(_accepted_hash_diverged(snap))


class TestImplementerUpdateReadyWithAcceptedHash(unittest.TestCase):
    """Verify _implementer_update_ready considers the accepted-hash signal."""

    def test_ready_on_hash_divergence_even_when_tree_hashes_match(self):
        """Semantic state divergence triggers ready even with same worktree hash."""
        snap = _snapshot(
            worktree_hash="aaa",
            reviewed_hash="aaa",
            implementer_state_hash="hash_new",
            reviewer_accepted_implementer_state_hash="hash_old",
        )
        self.assertTrue(_implementer_update_ready(snap))

    def test_not_ready_when_both_hashes_match(self):
        snap = _snapshot(
            worktree_hash="aaa",
            reviewed_hash="aaa",
            implementer_state_hash="hash_same",
            reviewer_accepted_implementer_state_hash="hash_same",
        )
        self.assertFalse(_implementer_update_ready(snap))

    def test_not_ready_when_accepted_hash_absent(self):
        """Gracefully no-op when Slice 2 hasn't landed yet."""
        snap = _snapshot(
            worktree_hash="aaa",
            reviewed_hash="aaa",
            implementer_state_hash="hash_new",
            reviewer_accepted_implementer_state_hash="",
        )
        self.assertFalse(_implementer_update_ready(snap))


class TestImplementerChangedWithAcceptedHash(unittest.TestCase):
    """Verify _implementer_changed considers the accepted-hash signal."""

    def test_changed_on_hash_divergence_even_when_everything_else_matches(self):
        baseline = _snapshot()
        current = _snapshot(
            implementer_state_hash="hash_new",
            reviewer_accepted_implementer_state_hash="hash_old",
        )
        self.assertTrue(_implementer_changed(baseline, current))

    def test_not_changed_when_accepted_hash_absent(self):
        baseline = _snapshot()
        current = _snapshot(
            implementer_state_hash="hash_new",
            reviewer_accepted_implementer_state_hash="",
        )
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
        self.assertIn("doctor", REVIEW_ACTION_CHOICES)

    def test_coerce_action_supports_reviewer_wait(self):
        self.assertIs(_coerce_action("reviewer-wait"), ReviewChannelAction.REVIEWER_WAIT)
        self.assertIs(_coerce_action("doctor"), ReviewChannelAction.DOCTOR)

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

    def test_dispatch_routes_to_doctor(self):
        with TemporaryDirectory() as tmp:
            bridge = Path(tmp) / "bridge.md"
            bridge.write_text("# bridge\n", encoding="utf-8")
            args = SimpleNamespace(action="doctor")
            paths = RuntimePaths(bridge_path=bridge)
            expected = ({"ok": True}, 0)
            with patch.object(
                review_channel_command,
                "_run_doctor_action",
                return_value=expected,
            ) as mocked:
                result = review_channel_command._dispatch_action(
                    args=args,
                    action=ReviewChannelAction.DOCTOR,
                    repo_root=Path(tmp),
                    paths=paths,
                )
            self.assertEqual(result, expected)
            mocked.assert_called_once()

    def test_doctor_action_reduces_status_to_readiness_surface(self):
        status_report = {
            "command": "review-channel",
            "timestamp": "2026-04-03T00:00:00Z",
            "action": "status",
            "ok": True,
            "exit_ok": True,
            "execution_mode": "markdown-bridge",
            "terminal": "none",
            "warnings": [],
            "errors": [],
            "doctor": {
                "status": "healthy",
                "publisher_running": True,
                "publisher_last_heartbeat_utc": "2026-04-03T00:00:10Z",
                "publisher_stop_reason": "",
                "reviewer_supervisor_running": False,
                "reviewer_supervisor_last_heartbeat_utc": "2026-04-03T00:00:05Z",
                "reviewer_supervisor_stop_reason": "manual_stop",
                "pipeline_state": "push_blocked",
                "blocked_reason": "pipeline_unavailable",
            },
            "reviewer_runtime": {"publish_clear": True},
            "commit_pipeline": {"state": "push_blocked"},
            "projection_paths": {"review_state_path": "/tmp/review_state.json"},
            "publisher": {"running": True},
            "reviewer_supervisor": {"running": False},
        }
        args = SimpleNamespace(action="doctor")

        with patch.object(
            review_channel_status_mod,
            "_run_status_action",
            return_value=(status_report, 0),
        ):
            report, exit_code = review_channel_status_mod._run_doctor_action(
                args=args,
                repo_root=Path("."),
                paths=RuntimePaths(),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["action"], "doctor")
        self.assertEqual(report["doctor"]["status"], "healthy")
        self.assertTrue(report["doctor"]["publisher_running"])
        self.assertEqual(
            report["doctor"]["reviewer_supervisor_stop_reason"],
            "manual_stop",
        )
        self.assertEqual(
            report["doctor"]["blocked_reason"],
            "pipeline_unavailable",
        )
        self.assertEqual(report["commit_pipeline"]["state"], "push_blocked")


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

    def _make_deps(self, reports, *, pending_packets=None):
        """Build deps that cycle through a list of (report, exit_code) tuples."""
        call_count = [0]
        packet_call_count = [0]
        mono_time = [0.0]
        packet_rows = pending_packets or [[]]

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

        def load_pending_packets(repo_root, paths):
            idx = min(packet_call_count[0], len(packet_rows) - 1)
            packet_call_count[0] += 1
            return packet_rows[idx]

        return WaitDeps(
            run_status_action_fn=run_status,
            read_bridge_text_fn=read_bridge,
            monotonic_fn=monotonic,
            sleep_fn=sleep,
            pending_packets_fn=load_pending_packets,
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

    def test_exits_immediately_when_codex_packet_already_pending(self):
        with TemporaryDirectory() as tmp:
            args = self._make_args()
            paths = self._make_paths(Path(tmp))
            report = _status_report(
                Path(tmp),
                current_hash="same_hash",
                reviewed_hash="same_hash",
                attention_status="healthy",
                packet_inbox={
                    "attention_revision": "attn_rev_1",
                    "agents": [
                        {
                            "agent": "codex",
                            "current_instruction_packet_id": "rev_pkt_9000",
                            "latest_finding_packet_id": "",
                            "pending_actionable_packet_ids": ["rev_pkt_9000"],
                            "expired_unresolved_packet_ids": [],
                            "attention_status": "wake_required",
                            "wake_reason": "instruction_pending",
                            "required_command": "python3 dev/scripts/devctl.py review-channel --action inbox --target codex --status pending --terminal none --format md",
                            "attention_revision": "codex_attn_rev_1",
                            "delivery_state": "unseen",
                        }
                    ],
                },
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
            self.assertEqual(
                result["wait_state"]["current_pending_packet_id"],
                "rev_pkt_9000",
            )
            self.assertIn("typed packet", result["warnings"][0])

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

    def test_exits_when_new_codex_packet_arrives_mid_poll(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            args = self._make_args()
            paths = self._make_paths(tmp_path)
            baseline = _status_report(
                tmp_path,
                current_hash="same_hash",
                reviewed_hash="same_hash",
                attention_status="healthy",
            )
            current = _status_report(
                tmp_path,
                current_hash="same_hash",
                reviewed_hash="same_hash",
                attention_status="healthy",
                packet_inbox={
                    "attention_revision": "attn_rev_2",
                    "agents": [
                        {
                            "agent": "codex",
                            "current_instruction_packet_id": "rev_pkt_9001",
                            "latest_finding_packet_id": "",
                            "pending_actionable_packet_ids": ["rev_pkt_9001"],
                            "expired_unresolved_packet_ids": [],
                            "attention_status": "wake_required",
                            "wake_reason": "instruction_pending",
                            "required_command": "python3 dev/scripts/devctl.py review-channel --action inbox --target codex --status pending --terminal none --format md",
                            "attention_revision": "codex_attn_rev_2",
                            "delivery_state": "unseen",
                        }
                    ],
                },
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
                result["wait_state"]["current_pending_packet_id"],
                "rev_pkt_9001",
            )
            self.assertIn("pending packet arrived", result["warnings"][0])

    def test_exits_immediately_when_codex_finding_already_pending(self):
        with TemporaryDirectory() as tmp:
            args = self._make_args()
            paths = self._make_paths(Path(tmp))
            report = _status_report(
                Path(tmp),
                current_hash="same_hash",
                reviewed_hash="same_hash",
                attention_status="healthy",
                packet_inbox={
                    "attention_revision": "attn_rev_3",
                    "agents": [
                        {
                            "agent": "codex",
                            "current_instruction_packet_id": "",
                            "latest_finding_packet_id": "rev_pkt_find_1",
                            "pending_actionable_packet_ids": [],
                            "expired_unresolved_packet_ids": [],
                            "attention_status": "review_needed",
                            "wake_reason": "finding_pending",
                            "required_command": "python3 dev/scripts/devctl.py review-channel --action inbox --target codex --status pending --terminal none --format md",
                            "attention_revision": "codex_attn_rev_3",
                            "delivery_state": "unseen",
                        }
                    ],
                },
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
            self.assertEqual(
                result["wait_state"]["current_finding_packet_id"],
                "rev_pkt_find_1",
            )
            self.assertIn("finding is already queued", result["warnings"][0])

    def test_missing_packet_inbox_fails_closed(self):
        with TemporaryDirectory() as tmp:
            args = self._make_args()
            paths = self._make_paths(Path(tmp))
            report = _status_report(
                Path(tmp),
                attention_status="healthy",
                packet_inbox={"attention_revision": "", "agents": []},
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
            self.assertIn("typed packet-inbox state is missing", result["errors"][0])

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

    def test_exits_immediately_on_accepted_hash_divergence(self):
        """If implementer-state-hash diverges from accepted baseline, exit immediately."""
        with TemporaryDirectory() as tmp:
            args = self._make_args()
            paths = self._make_paths(Path(tmp))
            report = _status_report(
                Path(tmp),
                current_hash="aaa",
                reviewed_hash="aaa",
                attention_status="healthy",
                current_session={
                    "implementer_ack_revision": "rev1",
                    "implementer_ack_state": "current",
                    "implementer_status": "Working on slice 3.",
                    "implementer_state_hash": "hash_after_new_work",
                },
                reviewer_accepted_implementer_state_hash="hash_at_last_review",
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
            self.assertTrue(result["wait_state"]["accepted_hash_diverged"])
            self.assertEqual(
                result["wait_state"]["current_implementer_state_hash"],
                "hash_after_new_work",
            )
            self.assertEqual(
                result["wait_state"]["reviewer_accepted_implementer_state_hash"],
                "hash_at_last_review",
            )

    def test_no_exit_when_accepted_hash_absent(self):
        """Gracefully skips hash comparison when Slice 2 state is absent."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            args = self._make_args(timeout_minutes=0)
            args.follow_interval_seconds = 1
            paths = self._make_paths(tmp_path)
            report = _status_report(
                tmp_path,
                attention_status="healthy",
                current_session={
                    "implementer_ack_revision": "rev1",
                    "implementer_ack_state": "current",
                    "implementer_status": "Working.",
                    "implementer_state_hash": "hash_new_work",
                },
                reviewer_accepted_implementer_state_hash="",
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
            self.assertEqual(result["wait_state"]["stop_reason"], "timed_out")
            self.assertFalse(result["wait_state"]["accepted_hash_diverged"])

    def test_loop_detects_hash_divergence_mid_poll(self):
        """Loop should wake when hash diverges between baseline and poll snapshot."""
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
                    "implementer_ack_state": "current",
                    "implementer_status": "Working.",
                    "implementer_state_hash": "hash_accepted",
                },
                reviewer_accepted_implementer_state_hash="hash_accepted",
            )
            current = _status_report(
                current_root,
                current_session={
                    "implementer_ack_revision": "rev1",
                    "implementer_ack_state": "current",
                    "implementer_status": "Working.",
                    "implementer_state_hash": "hash_diverged",
                },
                reviewer_accepted_implementer_state_hash="hash_accepted",
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
            self.assertTrue(result["wait_state"]["accepted_hash_diverged"])

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
