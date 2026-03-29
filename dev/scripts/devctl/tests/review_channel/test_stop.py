from __future__ import annotations

import signal
from types import SimpleNamespace
from pathlib import Path

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.review_channel._publisher import (
    REVIEWER_SUPERVISOR_FOLLOW_ARGS,
)
from dev.scripts.devctl.commands.review_channel._stop import (
    StopActionDeps,
    run_stop_action,
)
from dev.scripts.devctl.commands.review_channel_command.constants import (
    PUBLISHER_FOLLOW_COMMAND_ARGS,
)
from dev.scripts.devctl.review_channel.lifecycle_state import (
    PublisherHeartbeat,
    ReviewerSupervisorHeartbeat,
    write_publisher_heartbeat,
    write_reviewer_supervisor_heartbeat,
)


def test_cli_accepts_stop_action_and_args() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "review-channel",
            "--action",
            "stop",
            "--daemon-kind",
            "reviewer_supervisor",
            "--stop-grace-seconds",
            "2.5",
        ]
    )

    assert args.action == "stop"
    assert args.daemon_kind == "reviewer_supervisor"
    assert args.stop_grace_seconds == 2.5


def test_detached_follow_commands_disable_inactivity_timeout() -> None:
    assert PUBLISHER_FOLLOW_COMMAND_ARGS[-2:] == (
        "--follow-inactivity-timeout-seconds",
        "0",
    )
    assert REVIEWER_SUPERVISOR_FOLLOW_ARGS[-2:] == [
        "--follow-inactivity-timeout-seconds",
        "0",
    ]


def test_run_stop_action_stops_reviewer_supervisor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    pid_alive = {"value": True}
    monkeypatch.setattr(
        "dev.scripts.devctl.review_channel.lifecycle_state._pid_is_alive",
        lambda _pid: pid_alive["value"],
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.review_channel.lifecycle_state._heartbeat_age_seconds",
        lambda _timestamp: 0.0,
    )
    write_reviewer_supervisor_heartbeat(
        status_dir,
        ReviewerSupervisorHeartbeat(
            pid=4242,
            started_at_utc="2026-03-25T12:00:00Z",
            last_heartbeat_utc="2026-03-25T12:00:00Z",
            snapshots_emitted=3,
            reviewer_mode="active_dual_agent",
        ),
    )

    def kill_fn(pid: int, sig: int) -> None:
        assert pid == 4242
        assert sig == signal.SIGINT
        pid_alive["value"] = False
        write_reviewer_supervisor_heartbeat(
            status_dir,
            ReviewerSupervisorHeartbeat(
                pid=pid,
                started_at_utc="2026-03-25T12:00:00Z",
                last_heartbeat_utc="2026-03-25T12:00:05Z",
                snapshots_emitted=3,
                reviewer_mode="active_dual_agent",
                stop_reason="manual_stop",
                stopped_at_utc="2026-03-25T12:00:05Z",
            ),
        )

    report, exit_code = run_stop_action(
        args=SimpleNamespace(daemon_kind="reviewer_supervisor", stop_grace_seconds=1.0),
        repo_root=tmp_path,
        paths={"status_dir": status_dir},
        deps=StopActionDeps(
            kill_fn=kill_fn,
            monotonic_fn=lambda: 0.0,
            sleep_fn=lambda _seconds: None,
        ),
    )

    assert exit_code == 0
    assert report["ok"] is True
    assert report["stopped_daemons"] == ["reviewer_supervisor"]
    result = report["results"][0]
    assert result["reason"] == "manual_stop"
    assert result["state"]["stop_reason"] == "manual_stop"


def test_run_stop_action_is_idempotent_when_daemon_is_not_running(tmp_path: Path) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    write_publisher_heartbeat(
        status_dir,
        PublisherHeartbeat(
            pid=5151,
            started_at_utc="2026-03-25T12:00:00Z",
            last_heartbeat_utc="2026-03-25T12:00:05Z",
            snapshots_emitted=2,
            reviewer_mode="active_dual_agent",
            stop_reason="manual_stop",
            stopped_at_utc="2026-03-25T12:00:05Z",
        ),
    )

    report, exit_code = run_stop_action(
        args=SimpleNamespace(daemon_kind="publisher", stop_grace_seconds=1.0),
        repo_root=tmp_path,
        paths={"status_dir": status_dir},
    )

    assert exit_code == 0
    assert report["ok"] is True
    result = report["results"][0]
    assert result["reason"] == "not_running"
    assert result["attempted"] is False
