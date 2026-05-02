"""Tests for persisted launcher-discipline bypass receipts."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands.review_channel._recover import (
    _maybe_launch_recover_sessions,
)
from dev.scripts.devctl.commands.review_channel.bridge_handler import (
    _maybe_enforce_terminal_app_launch_discipline,
)
from dev.scripts.devctl.commands.review_channel.bridge_launch_control import (
    LaunchSessionRequest,
    launch_sessions_if_requested,
)
from dev.scripts.devctl.review_channel.event_store import (
    ReviewChannelArtifactPaths,
    load_events,
)
from dev.scripts.devctl.review_channel.recover_support import RecoverLaunchInput


def _artifact_paths(tmp_path: Path) -> ReviewChannelArtifactPaths:
    artifact_root = tmp_path / "review_channel"
    return ReviewChannelArtifactPaths(
        artifact_root=str(artifact_root),
        event_log_path=str(artifact_root / "events" / "trace.ndjson"),
        state_path=str(artifact_root / "state" / "latest.json"),
        projections_root=str(artifact_root / "projections" / "latest"),
    )


def _bypass_events(paths: ReviewChannelArtifactPaths) -> list[dict[str, object]]:
    return [
        event
        for event in load_events(Path(paths.event_log_path))
        if event.get("event_type") == "launcher_discipline_bypassed"
    ]


def _bridge_file(tmp_path: Path) -> Path:
    bridge_path = tmp_path / "bridge.md"
    bridge_path.write_text(
        "\n".join(
            [
                "# Bridge",
                "",
                "- Last Codex poll: `2026-05-02T12:00:00Z`",
                "- Reviewer mode: `single_agent`",
                "",
                "## Poll Status",
                "",
                "fresh",
            ]
        ),
        encoding="utf-8",
    )
    return bridge_path


def test_launch_control_persists_bypass_receipt_once(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)
    args = SimpleNamespace(
        action="launch",
        terminal="none",
        dry_run=False,
        await_ack_seconds=0,
        bypass_reason="operator accepted dev-only launch bypass",
    )
    request = LaunchSessionRequest(
        args=args,
        sessions=[{"launch_command": "/bin/true"}],
        bridge_path=_bridge_file(tmp_path),
        handoff_bundle=None,
        terminal_profile_applied=None,
        repo_root=tmp_path,
        interaction_mode="local_terminal",
        artifact_paths=paths,
    )

    with patch(
        "dev.scripts.devctl.commands.review_channel.bridge_launch_control._launch_sessions_headless",
        return_value=True,
    ):
        launch_sessions_if_requested(request)
        launch_sessions_if_requested(request)

    events = _bypass_events(paths)
    assert len(events) == 1
    event = events[0]
    assert event["bypass_reason"] == "operator accepted dev-only launch bypass"
    assert event["terminal_arg"] == "none"
    assert event["interaction_mode"] == "local_terminal"
    assert event["bypassed_verdicts"] == [
        {
            "denial_reason": "headless_launch_in_local_mode",
            "operator_message": (
                "Refusing headless Codex launch (`--terminal none`) because"
                " typed interaction_mode is `local_terminal`, not"
                " `remote_control`. Headless Codex CLI silently hangs on"
                " auth/permission prompts and the publisher daemon then fakes"
                " aliveness. Use `--terminal terminal-app` (visible local"
                " launch) per CLAUDE.md Bootstrap."
            ),
            "bypass_reason": "operator accepted dev-only launch bypass",
            "terminal_arg": "none",
            "interaction_mode": "local_terminal",
        }
    ]


def test_bridge_handler_terminal_app_bypass_is_audited_once(
    tmp_path: Path,
) -> None:
    paths = _artifact_paths(tmp_path)
    args = SimpleNamespace(
        action="launch",
        terminal="terminal-app",
        operator_interaction_mode="remote_control",
        bypass_reason="operator accepted visible-launch bypass",
    )

    with patch(
        "dev.scripts.devctl.commands.review_channel.bridge_handler.resolve_launch_interaction_mode",
        return_value="remote_control",
    ):
        _maybe_enforce_terminal_app_launch_discipline(
            args=args,
            repo_root=tmp_path,
            artifact_paths=paths,
        )
        _maybe_enforce_terminal_app_launch_discipline(
            args=args,
            repo_root=tmp_path,
            artifact_paths=paths,
        )

    events = _bypass_events(paths)
    assert len(events) == 1
    assert events[0]["terminal_arg"] == "terminal-app"
    assert events[0]["interaction_mode"] == "remote_control"
    assert events[0]["bypassed_verdicts"][0]["denial_reason"] == (
        "visible_launch_in_remote_control"
    )


def test_recover_launch_persists_bypass_receipt_once(tmp_path: Path) -> None:
    paths = _artifact_paths(tmp_path)
    args = SimpleNamespace(
        terminal="none",
        dry_run=False,
        await_ack_seconds=0,
        bypass_reason="operator accepted recover bypass",
    )
    launch_input = RecoverLaunchInput(
        args=args,
        repo_root=tmp_path,
        bridge_path=tmp_path / "bridge.md",
        current_instruction_revision="rev-1",
        sessions=[{"launch_command": "/bin/true"}],
        terminal_profile_applied=None,
        interaction_mode="local_terminal",
        artifact_paths=paths,
    )

    with patch(
        "dev.scripts.devctl.commands.review_channel._recover._launch_sessions_headless",
        return_value=True,
    ):
        _maybe_launch_recover_sessions(launch_input)
        _maybe_launch_recover_sessions(launch_input)

    events = _bypass_events(paths)
    assert len(events) == 1
    assert events[0]["terminal_arg"] == "none"
    assert events[0]["interaction_mode"] == "local_terminal"
    assert events[0]["bypassed_verdicts"][0]["denial_reason"] == (
        "headless_launch_in_local_mode"
    )
