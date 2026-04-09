from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.review_channel._attach_remote_control import (
    run_attach_remote_control_action,
)


def test_cli_accepts_attach_remote_control_action() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "review-channel",
            "--action",
            "attach-remote-control",
            "--session-url",
            "https://claude.ai/code/session_abc123",
        ]
    )

    assert args.action == "attach-remote-control"
    assert args.remote_provider == "claude"
    assert args.attachment_status == "attached"


def test_attach_remote_control_action_writes_artifact_and_derives_session_id(
    tmp_path: Path,
) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    parser = build_parser()
    args = parser.parse_args(
        [
            "review-channel",
            "--action",
            "attach-remote-control",
            "--session-name",
            "VoiceTerm Bridge Loop",
            "--session-url",
            "https://claude.ai/code/session_abc123",
            "--terminal",
            "none",
            "--format",
            "json",
        ]
    )

    report, exit_code = run_attach_remote_control_action(
        args=args,
        repo_root=tmp_path,
        paths={"status_dir": status_dir},
    )

    assert exit_code == 0
    assert report["ok"] is True
    attachment = report["attachment"]
    assert attachment["remote_session_id"] == "session_abc123"
    artifact_path = status_dir / "sessions" / "claude-remote-control.json"
    assert artifact_path.is_file()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["status"] == "attached"
    assert payload["session_url"] == "https://claude.ai/code/session_abc123"


def test_attach_remote_control_action_allows_unknown_status_without_url(
    tmp_path: Path,
) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    parser = build_parser()
    args = parser.parse_args(
        [
            "review-channel",
            "--action",
            "attach-remote-control",
            "--session-name",
            "VoiceTerm Bridge Loop",
            "--attachment-status",
            "unknown",
            "--terminal",
            "none",
            "--format",
            "json",
        ]
    )

    report, exit_code = run_attach_remote_control_action(
        args=args,
        repo_root=tmp_path,
        paths={"status_dir": status_dir},
    )

    assert exit_code == 0
    assert report["attachment"]["status"] == "unknown"
