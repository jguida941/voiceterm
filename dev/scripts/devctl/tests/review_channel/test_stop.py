from __future__ import annotations

import signal
from types import SimpleNamespace
from pathlib import Path

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.review_channel._publisher import (
    REVIEWER_SUPERVISOR_FOLLOW_ARGS,
)
from dev.scripts.devctl.commands.review_channel._reviewer_supervisor_autostart import (
    ensure_reviewer_supervisor_running,
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


def test_reviewer_supervisor_auto_start_respects_manual_stop(
    tmp_path: Path,
) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    write_reviewer_supervisor_heartbeat(
        status_dir,
        ReviewerSupervisorHeartbeat(
            pid=4242,
            started_at_utc="2026-03-25T12:00:00Z",
            last_heartbeat_utc="2026-03-25T12:00:05Z",
            snapshots_emitted=3,
            reviewer_mode="active_dual_agent",
            stop_reason="manual_stop",
            stopped_at_utc="2026-03-25T12:00:05Z",
        ),
    )

    report = ensure_reviewer_supervisor_running(
        args=SimpleNamespace(follow=False, reviewer_mode="active_dual_agent"),
        repo_root=tmp_path,
        paths={"status_dir": status_dir},
    )

    assert report == {
        "attempted": False,
        "started": False,
        "reason": "non_restartable_stop_reason",
        "stop_reason": "manual_stop",
    }


def test_reviewer_supervisor_auto_start_allows_manual_stop_when_recovery_is_typed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    write_reviewer_supervisor_heartbeat(
        status_dir,
        ReviewerSupervisorHeartbeat(
            pid=4242,
            started_at_utc="2026-03-25T12:00:00Z",
            last_heartbeat_utc="2026-03-25T12:00:05Z",
            snapshots_emitted=3,
            reviewer_mode="active_dual_agent",
            stop_reason="manual_stop",
            stopped_at_utc="2026-03-25T12:00:05Z",
        ),
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel._reviewer_supervisor_autostart._resolve_supervisor_interaction_mode",
        lambda **_kwargs: "remote_control",
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel._reviewer_supervisor_autostart.spawn_reviewer_supervisor",
        lambda **_kwargs: (True, 4321, "/tmp/reviewer_supervisor_follow.log"),
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel._reviewer_supervisor_autostart.verify_reviewer_supervisor_start",
        lambda **_kwargs: "started",
    )

    report = ensure_reviewer_supervisor_running(
        args=SimpleNamespace(follow=False, reviewer_mode="active_dual_agent"),
        repo_root=tmp_path,
        paths={"status_dir": status_dir},
        allow_manual_stop_recovery=True,
        sleep_seconds=0.0,
    )

    assert report == {
        "attempted": True,
        "started": True,
        "pid": 4321,
        "log_path": "/tmp/reviewer_supervisor_follow.log",
        "start_status": "started",
    }


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


def test_run_stop_action_escalates_to_sigkill_after_grace_timeout(
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
    write_publisher_heartbeat(
        status_dir,
        PublisherHeartbeat(
            pid=5151,
            started_at_utc="2026-03-25T12:00:00Z",
            last_heartbeat_utc="2026-03-25T12:00:05Z",
            snapshots_emitted=2,
            reviewer_mode="active_dual_agent",
        ),
    )

    clock = {"now": 0.0}
    signals: list[int] = []

    def monotonic_fn() -> float:
        return clock["now"]

    def sleep_fn(seconds: float) -> None:
        clock["now"] += seconds

    def kill_fn(pid: int, sig: int) -> None:
        assert pid == 5151
        signals.append(sig)
        if sig == signal.SIGKILL:
            pid_alive["value"] = False
            write_publisher_heartbeat(
                status_dir,
                PublisherHeartbeat(
                    pid=pid,
                    started_at_utc="2026-03-25T12:00:00Z",
                    last_heartbeat_utc="2026-03-25T12:00:08Z",
                    snapshots_emitted=2,
                    reviewer_mode="active_dual_agent",
                    stop_reason="forced_stop",
                    stopped_at_utc="2026-03-25T12:00:08Z",
                ),
            )

    report, exit_code = run_stop_action(
        args=SimpleNamespace(daemon_kind="publisher", stop_grace_seconds=3.0),
        repo_root=tmp_path,
        paths={"status_dir": status_dir},
        deps=StopActionDeps(
            kill_fn=kill_fn,
            monotonic_fn=monotonic_fn,
            sleep_fn=sleep_fn,
        ),
    )

    assert exit_code == 0
    assert report["ok"] is True
    assert signals == [signal.SIGINT, signal.SIGTERM, signal.SIGKILL]
    result = report["results"][0]
    assert result["signal"] == "SIGKILL"
    assert result["reason"] == "forced_stop"
    assert result["stopped"] is True
