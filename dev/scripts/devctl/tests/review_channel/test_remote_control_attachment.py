from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.review_channel._attach_remote_control import (
    _build_attachment,
    _session_id_from_url,
    run_attach_remote_control_action,
)
from dev.scripts.devctl.review_channel.events import (
    post_packet,
    resolve_artifact_paths,
    transition_packet,
)
from dev.scripts.devctl.commands.review_channel_command.constants import (
    ReviewChannelAction,
)
from dev.scripts.devctl.commands.review_channel_command.helpers import _validate_args
from dev.scripts.devctl.review_channel.remote_control_attachment_artifact import (
    deactivate_remote_control_attachments,
    has_active_remote_control_attachment,
    load_remote_control_attachment,
    persist_remote_control_attachment,
    remote_control_attachment_path,
)
from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
)
from dev.scripts.devctl.review_channel.packet_contract import (
    PacketPostRequest,
    PacketTargetFields,
    PacketTransitionRequest,
)
from dev.scripts.devctl.tests.test_review_channel_context_refs import (
    _review_channel_text,
)
from dev.scripts.devctl.repo_packs import active_path_config


def _make_attach_args(**overrides: object) -> SimpleNamespace:
    """Build a minimal args namespace matching the attach-remote-control surface."""
    defaults: dict[str, object] = {
        "remote_provider": "claude",
        "remote_role": "operator",
        "attachment_status": "attached",
        "session_name": "",
        "remote_session_id": "",
        "session_url": "",
        "metadata_path": "",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


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


def test_build_attachment_defaults_remote_role_to_operator() -> None:
    attachment = _build_attachment(args=_make_attach_args(), existing=None)

    assert attachment.role == "operator"


def test_build_attachment_is_idempotent_for_same_session_url() -> None:
    """Re-attaching with the same session URL must reuse the existing id + timestamp."""
    args = _make_attach_args(
        session_name="VoiceTerm Bridge Loop",
        session_url="https://claude.ai/code/session_abc123",
    )

    first = _build_attachment(args=args, existing=None)
    second = _build_attachment(args=args, existing=first)

    assert second.attachment_id == first.attachment_id
    assert second.attached_at_utc == first.attached_at_utc
    # last_seen_utc should still refresh on every call even when identity matches.
    assert second.last_seen_utc >= first.last_seen_utc


def test_build_attachment_does_not_conflate_sessions_sharing_a_label() -> None:
    """Matching on session_name alone must NOT reuse a prior attachment id."""
    first_args = _make_attach_args(
        session_name="VoiceTerm Bridge Loop",
        session_url="https://claude.ai/code/session_first",
    )
    second_args = _make_attach_args(
        session_name="VoiceTerm Bridge Loop",
        session_url="https://claude.ai/code/session_second",
    )

    first = _build_attachment(args=first_args, existing=None)
    second = _build_attachment(args=second_args, existing=first)

    assert first.remote_session_id == "session_first"
    assert second.remote_session_id == "session_second"
    assert second.attachment_id != first.attachment_id


def test_has_active_predicate_is_false_for_detached_attachment(tmp_path: Path) -> None:
    """A persisted detached attachment must not register as active."""
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    detached = RemoteControlAttachmentState(
        provider="claude",
        role="implementer",
        attachment_id="remote-attach-detached",
        session_name="VoiceTerm Bridge Loop",
        remote_session_id="session_gone",
        session_url="https://claude.ai/code/session_gone",
        status="detached",
        attached_at_utc="2026-04-09T00:00:00Z",
        last_seen_utc="2026-04-09T00:00:01Z",
    )
    persist_remote_control_attachment(detached, output_root=status_dir)

    loaded = load_remote_control_attachment(
        output_root=status_dir, provider="claude"
    )
    assert loaded is not None
    assert loaded.status == "detached"
    assert has_active_remote_control_attachment(loaded) is False


def test_has_active_predicate_is_false_for_stale_attachment() -> None:
    attachment = RemoteControlAttachmentState(
        provider="claude",
        role="implementer",
        attachment_id="remote-attach-stale",
        session_name="VoiceTerm Bridge Loop",
        remote_session_id="session_stale",
        session_url="https://claude.ai/code/session_stale",
        status="stale",
    )

    assert has_active_remote_control_attachment(attachment) is False


def test_deactivate_remote_control_attachments_downgrades_all_providers(
    tmp_path: Path,
) -> None:
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    persist_remote_control_attachment(
        RemoteControlAttachmentState(
            provider="claude",
            role="implementer",
            attachment_id="remote-attach-claude",
            session_name="Claude bridge",
            remote_session_id="session_claude",
            session_url="https://claude.ai/code/session_claude",
            status="attached",
        ),
        output_root=status_dir,
    )
    persist_remote_control_attachment(
        RemoteControlAttachmentState(
            provider="codex",
            role="reviewer",
            attachment_id="remote-attach-codex",
            session_name="Codex bridge",
            remote_session_id="session_codex",
            session_url="https://chatgpt.com/codex/session_codex",
            status="unknown",
        ),
        output_root=status_dir,
    )

    updated_paths = deactivate_remote_control_attachments(output_root=status_dir)

    assert len(updated_paths) == 2
    assert {
        load_remote_control_attachment(output_root=status_dir, provider="claude").status,
        load_remote_control_attachment(output_root=status_dir, provider="codex").status,
    } == {"detached"}


def test_validate_args_requires_session_identity_when_attached() -> None:
    """Attached status without url or session id must raise a typed ValueError."""
    args = _make_attach_args(attachment_status="attached")
    with pytest.raises(ValueError, match="requires --session-url"):
        _validate_args(args, ReviewChannelAction.ATTACH_REMOTE_CONTROL)


def test_provider_parameterized_artifacts_do_not_clobber_each_other(
    tmp_path: Path,
) -> None:
    """Claude and codex attachments must coexist in the same sessions dir."""
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    claude_state = RemoteControlAttachmentState(
        provider="claude",
        role="implementer",
        attachment_id="remote-attach-claude",
        session_name="Claude bridge",
        remote_session_id="session_claude",
        session_url="https://claude.ai/code/session_claude",
        status="attached",
        attached_at_utc="2026-04-09T00:00:00Z",
        last_seen_utc="2026-04-09T00:00:01Z",
    )
    codex_state = RemoteControlAttachmentState(
        provider="codex",
        role="reviewer",
        attachment_id="remote-attach-codex",
        session_name="Codex bridge",
        remote_session_id="session_codex",
        session_url="https://chatgpt.com/codex/session_codex",
        status="attached",
        attached_at_utc="2026-04-09T00:00:02Z",
        last_seen_utc="2026-04-09T00:00:03Z",
    )

    claude_path = persist_remote_control_attachment(
        claude_state, output_root=status_dir
    )
    codex_path = persist_remote_control_attachment(
        codex_state, output_root=status_dir
    )

    assert claude_path == remote_control_attachment_path(
        output_root=status_dir, provider="claude"
    )
    assert codex_path == remote_control_attachment_path(
        output_root=status_dir, provider="codex"
    )
    assert claude_path != codex_path
    assert claude_path.is_file()
    assert codex_path.is_file()

    loaded_claude = load_remote_control_attachment(
        output_root=status_dir, provider="claude"
    )
    loaded_codex = load_remote_control_attachment(
        output_root=status_dir, provider="codex"
    )
    assert loaded_claude is not None and loaded_claude.provider == "claude"
    assert loaded_codex is not None and loaded_codex.provider == "codex"
    assert loaded_claude.remote_session_id == "session_claude"
    assert loaded_codex.remote_session_id == "session_codex"

    # Provider-agnostic scan should pick the most recently seen active record.
    scanned = load_remote_control_attachment(output_root=status_dir)
    assert scanned is not None
    assert scanned.provider == "codex"


def test_post_packet_refreshes_active_remote_control_attachment_last_seen(
    tmp_path: Path,
) -> None:
    review_channel_path = tmp_path / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    status_dir = tmp_path / active_path_config().review_status_dir_rel
    persist_remote_control_attachment(
        RemoteControlAttachmentState(
            provider="claude",
            role="operator",
            attachment_id="remote-attach-claude",
            session_name="Claude remote control",
            remote_session_id="session_claude",
            session_url="https://claude.ai/code/session_claude",
            status="attached",
            attached_at_utc="2026-04-09T00:00:00Z",
            last_seen_utc="2026-04-09T00:00:01Z",
        ),
        output_root=status_dir,
    )

    _, event = post_packet(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="claude",
            to_agent="codex",
            kind="instruction",
            summary="Remote-control heartbeat proof",
            body="Refresh the active remote attachment timestamp on post.",
        ),
    )

    attachment = load_remote_control_attachment(output_root=status_dir, provider="claude")

    assert attachment is not None
    assert attachment.last_seen_utc == event["timestamp_utc"]


def test_transition_packet_refreshes_remote_attachment_and_action_receipt(
    tmp_path: Path,
) -> None:
    """Transition side effects must keep their imports wired end to end."""
    review_channel_path = tmp_path / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    status_dir = tmp_path / active_path_config().review_status_dir_rel
    persist_remote_control_attachment(
        RemoteControlAttachmentState(
            provider="claude",
            role="operator",
            attachment_id="remote-attach-claude-transition",
            session_name="Claude remote control",
            remote_session_id="session_claude_transition",
            session_url="https://claude.ai/code/session_claude_transition",
            status="attached",
            attached_at_utc="2026-04-09T00:00:00Z",
            last_seen_utc="2026-04-09T00:00:01Z",
        ),
        output_root=status_dir,
    )
    _, event = post_packet(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="codex",
            to_agent="claude",
            kind="action_request",
            summary="Run focused bridge check",
            body="python3 dev/scripts/checks/check_review_channel_bridge.py",
            requested_action="run_check",
            policy_hint="review_only",
            target=PacketTargetFields.from_values(
                target_kind="runtime",
                target_ref="guard:check_review_channel_bridge",
                target_revision="tree-123",
            ),
        ),
    )

    refreshed, apply_event = transition_packet(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(event["packet_id"]),
            actor="claude",
        ),
    )
    attachment = load_remote_control_attachment(output_root=status_dir, provider="claude")
    applied_packet = next(
        packet
        for packet in refreshed.review_state["packets"]
        if packet["packet_id"] == event["packet_id"]
    )

    assert attachment is not None
    assert attachment.last_seen_utc == apply_event["timestamp_utc"]
    assert applied_packet["execution_started_at_utc"] == apply_event["timestamp_utc"]
    assert applied_packet["execution_started_by"] == "claude"


def test_session_id_from_url_strips_query_and_fragment() -> None:
    """Session ids must survive query strings and fragments after the tail."""
    assert (
        _session_id_from_url("https://claude.ai/code/session_abc?foo=1")
        == "session_abc"
    )
    assert (
        _session_id_from_url("https://claude.ai/code/session_xyz#top")
        == "session_xyz"
    )
    assert (
        _session_id_from_url("https://claude.ai/code/session_trailing/")
        == "session_trailing"
    )
    assert _session_id_from_url("https://example.com/other/path") == ""
    assert _session_id_from_url("") == ""
