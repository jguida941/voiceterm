"""Focused tests for review-channel follow-controller helpers."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from dev.scripts.devctl.review_channel import follow_stream as review_channel_follow_stream
from dev.scripts.devctl.review_channel.follow_controller import (
    EnsureFollowDeps,
    _build_ensure_follow_tick,
)
from dev.scripts.devctl.review_channel.reviewer_state_support import (
    EnsureHeartbeatResult,
)
from dev.scripts.devctl.runtime.monitor_snapshot_contracts import MonitorSnapshotPaths


class FollowControllerTests(unittest.TestCase):
    def test_ensure_follow_tick_writes_monitor_snapshot_bundle(self) -> None:
        calls: list[tuple[Path, Path]] = []
        deps = EnsureFollowDeps(
            ensure_reviewer_heartbeat_fn=lambda **_kw: None,
            reviewer_state_write_to_dict_fn=lambda _sw: None,
            run_status_action_fn=lambda **_kw: (
                {
                    "command": "review-channel",
                    "action": "status",
                    "bridge_liveness": {"reviewer_mode": "single_agent"},
                },
                0,
            ),
            attach_reviewer_worker_fn=lambda *_a, **_kw: None,
            ensure_reviewer_supervisor_running_fn=None,
            emit_follow_ndjson_frame_fn=lambda *_a, **_kw: 0,
            reset_follow_output_fn=lambda _o: None,
            build_follow_completion_report_fn=lambda **_kw: {},
            build_follow_output_error_report_fn=lambda **_kw: {},
            write_publisher_heartbeat_fn=lambda *_a, **_kw: Path("/tmp/publisher.json"),
            read_publisher_state_fn=lambda _status_dir: {"running": True},
            write_monitor_snapshot_fn=lambda **kwargs: _record_monitor_snapshot(
                kwargs,
                calls,
            ),
            utc_timestamp_fn=lambda: "2026-04-10T18:10:00Z",
            sleep_fn=lambda _s: None,
            operator_interaction_mode="remote_control",
        )
        args = SimpleNamespace()
        repo_root = Path("/tmp/repo")
        status_dir = repo_root / "dev/review_status"
        ensure_result = EnsureHeartbeatResult(
            refreshed=False,
            reviewer_mode="single_agent",
            reason="ensure-follow",
            state_write=None,
            error=None,
        )

        with (
            patch(
                "dev.scripts.devctl.review_channel.follow_controller.maybe_refresh_automation_reviewer_heartbeat",
                return_value=ensure_result,
            ),
            patch(
                "dev.scripts.devctl.review_channel.follow_controller.compute_review_range",
                return_value=None,
            ),
        ):
            tick = _build_ensure_follow_tick(
                args=args,
                repo_root=repo_root,
                paths={
                    "bridge_path": repo_root / "bridge.md",
                    "status_dir": status_dir,
                },
                deps=deps,
            )

        self.assertEqual(tick.exit_code, 0)
        self.assertIn("monitor_snapshot", tick.report)
        self.assertEqual(
            tick.report["monitor_snapshot"]["json_path"],
            str(status_dir / "monitor_snapshot.json"),
        )
        self.assertEqual(calls, [(repo_root, status_dir)])

    def test_ensure_follow_tick_report_serializes_monitor_snapshot_paths(self) -> None:
        deps = EnsureFollowDeps(
            ensure_reviewer_heartbeat_fn=lambda **_kw: None,
            reviewer_state_write_to_dict_fn=lambda _sw: None,
            run_status_action_fn=lambda **_kw: (
                {
                    "command": "review-channel",
                    "action": "status",
                    "bridge_liveness": {"reviewer_mode": "single_agent"},
                },
                0,
            ),
            attach_reviewer_worker_fn=lambda *_a, **_kw: None,
            ensure_reviewer_supervisor_running_fn=None,
            emit_follow_ndjson_frame_fn=lambda *_a, **_kw: 0,
            reset_follow_output_fn=lambda _o: None,
            build_follow_completion_report_fn=lambda **_kw: {},
            build_follow_output_error_report_fn=lambda **_kw: {},
            write_publisher_heartbeat_fn=lambda *_a, **_kw: Path("/tmp/publisher.json"),
            read_publisher_state_fn=lambda _status_dir: {"running": True},
            write_monitor_snapshot_fn=lambda **_kwargs: MonitorSnapshotPaths(
                root_dir="/tmp/repo/dev/review_status",
                json_path="/tmp/repo/dev/review_status/monitor_snapshot.json",
                markdown_path="/tmp/repo/dev/review_status/monitor_snapshot.md",
            ),
            utc_timestamp_fn=lambda: "2026-04-10T18:10:00Z",
            sleep_fn=lambda _s: None,
            operator_interaction_mode="remote_control",
        )

        with (
            patch(
                "dev.scripts.devctl.review_channel.follow_controller.maybe_refresh_automation_reviewer_heartbeat",
                return_value=EnsureHeartbeatResult(
                    refreshed=False,
                    reviewer_mode="single_agent",
                    reason="ensure-follow",
                    state_write=None,
                    error=None,
                ),
            ),
            patch(
                "dev.scripts.devctl.review_channel.follow_controller.compute_review_range",
                return_value=None,
            ),
        ):
            tick = _build_ensure_follow_tick(
                args=SimpleNamespace(),
                repo_root=Path("/tmp/repo"),
                paths={
                    "bridge_path": Path("/tmp/repo/bridge.md"),
                    "status_dir": Path("/tmp/repo/dev/review_status"),
                },
                deps=deps,
            )

        emitted: list[str] = []

        def fake_emit_output(
            content: str,
            *,
            output_path: str | None,
            pipe_command: str | None,
            pipe_args: list[str] | None,
            announce_output_path: bool = True,
            writer=None,
            stdout_content: str | None = None,
            piper=None,
            additional_outputs=None,
        ) -> int:
            emitted.append(content)
            return 0

        with patch.object(
            review_channel_follow_stream,
            "emit_output",
            side_effect=fake_emit_output,
        ):
            rc = review_channel_follow_stream.emit_follow_ndjson_frame(
                tick.report,
                args=SimpleNamespace(output=None, pipe_command=None, pipe_args=None),
            )

        self.assertEqual(rc, 0)
        payload = json.loads(emitted[0])
        self.assertEqual(
            payload["monitor_snapshot"]["json_path"],
            "/tmp/repo/dev/review_status/monitor_snapshot.json",
        )

    def test_spawn_follow_publisher_uses_explicit_interval_when_present(self) -> None:
        from dev.scripts.devctl.commands.review_channel._publisher import (
            spawn_follow_publisher,
        )

        args = SimpleNamespace(
            operator_interaction_mode="remote_control",
            follow_interval_seconds=180,
            follow_inactivity_timeout_seconds=0,
        )
        with patch(
            "dev.scripts.devctl.commands.review_channel._publisher.subprocess.Popen"
        ) as popen:
            popen.return_value = SimpleNamespace(pid=42)
            started, _pid, _log_path = spawn_follow_publisher(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={
                    "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
                    "bridge_path": Path("/tmp/repo/bridge.md"),
                    "status_dir": Path("/tmp/repo/dev/review_status"),
                },
            )

        command = popen.call_args.args[0]
        idx = command.index("--follow-interval-seconds")
        self.assertTrue(started)
        self.assertEqual(command[idx + 1], "180")

    def test_ensure_follow_tick_reloads_status_after_reviewer_wake(self) -> None:
        reports = [
            (
                {
                    "command": "review-channel",
                    "action": "status",
                    "bridge_liveness": {"reviewer_mode": "single_agent"},
                },
                0,
            ),
            (
                {
                    "command": "review-channel",
                    "action": "status",
                    "bridge_liveness": {"reviewer_mode": "single_agent"},
                    "packet_inbox": {"agents": []},
                },
                0,
            ),
        ]
        deps = EnsureFollowDeps(
            ensure_reviewer_heartbeat_fn=lambda **_kw: None,
            reviewer_state_write_to_dict_fn=lambda _sw: None,
            run_status_action_fn=lambda **_kw: reports.pop(0),
            attach_reviewer_worker_fn=lambda *_a, **_kw: None,
            ensure_reviewer_supervisor_running_fn=None,
            emit_follow_ndjson_frame_fn=lambda *_a, **_kw: 0,
            reset_follow_output_fn=lambda _o: None,
            build_follow_completion_report_fn=lambda **_kw: {},
            build_follow_output_error_report_fn=lambda **_kw: {},
            write_publisher_heartbeat_fn=lambda *_a, **_kw: Path("/tmp/publisher.json"),
            read_publisher_state_fn=lambda _status_dir: {"running": True},
            write_monitor_snapshot_fn=None,
            utc_timestamp_fn=lambda: "2026-04-10T18:10:00Z",
            sleep_fn=lambda _s: None,
            operator_interaction_mode="remote_control",
        )

        with (
            patch(
                "dev.scripts.devctl.review_channel.follow_controller.maybe_refresh_automation_reviewer_heartbeat",
                return_value=EnsureHeartbeatResult(
                    refreshed=False,
                    reviewer_mode="single_agent",
                    reason="ensure-follow",
                    state_write=None,
                    error=None,
                ),
            ),
            patch(
                "dev.scripts.devctl.review_channel.follow_controller.compute_review_range",
                return_value=None,
            ),
            patch(
                "dev.scripts.devctl.review_channel.follow_controller.maybe_wake_waiting_reviewer_conductor",
                return_value={"attempted": True, "woke": True, "packet_id": "pkt-1"},
            ),
        ):
            tick = _build_ensure_follow_tick(
                args=SimpleNamespace(),
                repo_root=Path("/tmp/repo"),
                paths={
                    "bridge_path": Path("/tmp/repo/bridge.md"),
                    "status_dir": Path("/tmp/repo/dev/review_status"),
                },
                deps=deps,
            )

        self.assertEqual(tick.exit_code, 0)
        self.assertEqual(tick.report["reviewer_wake"]["packet_id"], "pkt-1")
        self.assertIn("packet_inbox", tick.report)


def _record_monitor_snapshot(
    kwargs: dict[str, object],
    calls: list[tuple[Path, Path]],
) -> dict[str, str]:
    repo_root = kwargs["repo_root"]
    status_dir = kwargs["review_status_dir"]
    assert isinstance(repo_root, Path)
    assert isinstance(status_dir, Path)
    calls.append((repo_root, status_dir))
    return {
        "json_path": str(status_dir / "monitor_snapshot.json"),
        "markdown_path": str(status_dir / "monitor_snapshot.md"),
    }


if __name__ == "__main__":
    unittest.main()
