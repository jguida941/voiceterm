"""Regression tests for the typed remote-control lifecycle command."""

from __future__ import annotations

import json
import shlex
from datetime import datetime, timezone
from pathlib import Path

from dev.scripts.devctl.cli_parser import entrypoint as cli
from dev.scripts.devctl.commands.remote_control import command as remote_control
from dev.scripts.devctl.runtime.remote_control_attachment_status import (
    remote_attachment_active,
)
from dev.scripts.devctl.runtime.remote_control_invocation_receipt import (
    REMOTE_CONTROL_INVOCATION_STATE_CHANGES,
)
from dev.scripts.devctl.runtime.remote_control_slash_adapters import (
    build_remote_control_slash_adapter_catalog,
)
from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
)
from dev.scripts.devctl.runtime.session_posture_interaction import (
    resolve_interaction_mode,
)


def _epoch_ms(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)


def _now_epoch_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def test_remote_control_enter_writes_active_attachment(
    tmp_path: Path,
    capsys,
) -> None:
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--role",
            "operator",
            "--session-name",
            "Phone Session",
            "--session-url",
            "https://claude.ai/code/session_test",
            "--launcher-source",
            "slash",
            "--entrypoint",
            "/project:typed-remote-control",
            "--heartbeat-ttl-seconds",
            "60",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    artifact = tmp_path / "sessions" / "claude-remote-control.json"
    stored = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["operator_interaction_mode"] == "remote_control"
    assert stored["status"] == "attached"
    assert stored["launcher_source"] == "slash"
    assert stored["entrypoint"] == "/project:typed-remote-control"
    assert stored["heartbeat_ttl_seconds"] == 60


def test_remote_control_exit_detaches_attachment(
    tmp_path: Path,
    capsys,
) -> None:
    enter_args = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )
    assert remote_control.run(enter_args) == 0
    capsys.readouterr()

    exit_args = cli.build_parser().parse_args(
        [
            "remote-control",
            "exit",
            "--provider",
            "claude",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(exit_args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    stored = json.loads(
        (tmp_path / "sessions" / "claude-remote-control.json").read_text(
            encoding="utf-8",
        )
    )
    assert payload["operator_interaction_mode"] == "local_terminal"
    assert stored["status"] == "detached"


def test_enter_without_identity_and_no_existing_falls_closed_to_evidence_missing(
    tmp_path: Path,
    capsys,
) -> None:
    """Per rev_pkt_2996 #1 + rev_pkt_3001 + rev_pkt_3003 #3: a direct
    CLI invocation that lacks both ``--remote-session-id`` and
    ``--session-url`` AND has no live identity-bound prior attachment
    must NOT promote operator_interaction_mode to remote_control. The
    only valid outcome is status=evidence_missing, attachment_active
    =False, mode=local_terminal, plus an explicit warning so audit
    trails see the fail-closed result.
    """
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "local_terminal"
    assert payload["attachment_active"] is False
    assert payload["state_change"] == "evidence_missing"
    assert (payload.get("attachment") or {}).get("status") == "evidence_missing"
    warnings = payload.get("warnings") or []
    assert any(
        "lacks current session identity" in str(warning) for warning in warnings
    ), f"expected fail-closed warning; got {warnings!r}"


def test_classify_claimed_source_kind_is_self_attested_not_proof() -> None:
    """Per rev_pkt_3021 P1 #5 + rev_pkt_3025 P0-2: receipts record what
    the caller CLAIMS about the invocation source for audit narrative.
    The classifier reads only user-supplied CLI flags, so it is
    SELF-ATTESTED, not proof of physical slash execution.

    Authority decisions (mode promotion, refresh of identity-bound
    attachments) MUST NOT rely on this value. Identity-bound attachment
    evidence + TTL is the only authority gate today; non-user-controllable
    proof belongs in ``proven_source_kind``.
    """
    from dev.scripts.devctl.runtime.remote_control_invocation_receipt import (
        REMOTE_CONTROL_INVOCATION_SOURCE_KINDS,
        classify_claimed_source_kind,
    )

    assert (
        classify_claimed_source_kind(
            entrypoint="/project:typed-remote-control",
            launcher_source="claude_project_slash",
        )
        == "claude_project_slash"
    )
    assert (
        classify_claimed_source_kind(
            entrypoint="/project:typed-remote-control",
            launcher_source="",
        )
        == "direct_cli"
    ), "project entrypoint alone does not claim a trusted source"
    assert (
        classify_claimed_source_kind(
            entrypoint="",
            launcher_source="claude_project_slash",
        )
        == "direct_cli"
    ), (
        "rev_pkt_3007 Q3 conjunction rule: launcher_source alone is not "
        "even a claim; both entrypoint and launcher_source must agree."
    )
    assert (
        classify_claimed_source_kind(
            entrypoint="",
            launcher_source="",
            invocation_origin="claude_project_slash",
        )
        == "claude_project_slash"
    ), "explicit invocation_origin overrides classification when caller is authoritative"
    assert (
        classify_claimed_source_kind(
            entrypoint="",
            launcher_source="",
            invocation_origin="claude_builtin_slash",
        )
        == "claude_builtin_slash"
    )
    assert (
        classify_claimed_source_kind(entrypoint="", launcher_source="")
        == "unspecified"
    )
    assert (
        classify_claimed_source_kind(
            entrypoint="/some-arbitrary-string",
            launcher_source="custom-tool",
        )
        == "direct_cli"
    )
    for value in (
        "claude_builtin_slash",
        "claude_project_slash",
        "codex_project_slash",
        "direct_cli",
        "review_channel_attach",
        "unspecified",
    ):
        assert value in REMOTE_CONTROL_INVOCATION_SOURCE_KINDS


def test_direct_cli_spoofing_trusted_flags_does_not_grant_authority(
    tmp_path: Path,
    capsys,
) -> None:
    """Per rev_pkt_3025 P0-2 + P0-3: a direct CLI passing the exact
    flags from .claude/commands/typed-remote-control.md (entrypoint +
    launcher_source) MUST NOT receive trusted/proven authority. The
    receipt's ``claimed_source_kind`` may say ``claude_project_slash``
    for audit narrative, but ``proven_source_kind`` stays
    ``unspecified`` until non-user-controllable evidence lands, and the
    attachment must remain fail-closed (no identity flag passed) so
    operator_interaction_mode does NOT promote.
    """
    from dev.scripts.devctl.runtime.remote_control_invocation_receipt import (
        DEFAULT_REMOTE_CONTROL_INVOCATION_REL,
        receipt_from_mapping,
    )

    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--entrypoint",
            "/project:typed-remote-control",
            "--launcher-source",
            "claude_project_slash",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )
    rc = remote_control.run(args)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "local_terminal", (
        "rev_pkt_3025 P0-2: spoofed slash flags must not promote"
    )
    assert payload["attachment_active"] is False
    assert payload["state_change"] == "evidence_missing"

    receipt_path = tmp_path / DEFAULT_REMOTE_CONTROL_INVOCATION_REL
    last_line = receipt_path.read_text(encoding="utf-8").strip().splitlines()[-1]
    receipt = receipt_from_mapping(json.loads(last_line))
    assert receipt.claimed_source_kind == "claude_project_slash", (
        "claimed source narrative is recorded for audit"
    )
    assert receipt.proven_source_kind == "unspecified", (
        "rev_pkt_3025 P0-2: no non-user-controllable proof exists yet"
    )
    assert receipt.invocation_origin == "direct_cli", (
        "rev_pkt_3027: invocation_origin must NOT mirror the spoofable "
        "claimed_source_kind. When proven_source_kind=unspecified, the "
        "field defaults to direct_cli so the receipt does not surface "
        "claude_project_slash under an authoritative-sounding name."
    )


def test_source_proof_accepts_fresh_typed_slash_metadata(tmp_path: Path) -> None:
    from dev.scripts.devctl.commands.remote_control._source_proof import (
        resolve_lifecycle_source_proof_from_projection,
    )

    session_id = "test-claude-session-0001"
    session_path = tmp_path / f"{session_id}.jsonl"
    session_path.write_text(
        json.dumps(
            {
                "type": "system",
                "subtype": "local_command",
                "content": (
                    "<command-name>/typed-remote-control</command-name>\n"
                    "<command-message>typed-remote-control</command-message>"
                ),
                "timestamp": "2026-05-04T23:20:00Z",
                "sessionId": session_id,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    proof = resolve_lifecycle_source_proof_from_projection(
        projection={"session_id": session_id, "session_path": str(session_path)},
        command_entrypoint="/project:typed-remote-control",
        launcher_source="claude_project_slash",
        now_utc="2026-05-04T23:20:30Z",
    )

    assert proof.proven_source_kind == "claude_project_slash"
    assert proof.remote_session_id == ""
    assert proof.provider_session_id == f"claude-code:{session_id}"
    assert proof.proof_channel == "claude_agent_mind_attribution"


def test_source_proof_rejects_stale_typed_slash_metadata(tmp_path: Path) -> None:
    from dev.scripts.devctl.commands.remote_control._source_proof import (
        resolve_lifecycle_source_proof_from_projection,
    )

    session_id = "test-claude-session-0001"
    session_path = tmp_path / f"{session_id}.jsonl"
    session_path.write_text(
        json.dumps(
            {
                "type": "system",
                "subtype": "local_command",
                "content": "<command-name>/typed-remote-control</command-name>",
                "timestamp": "2026-05-04T23:10:00Z",
                "sessionId": session_id,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    proof = resolve_lifecycle_source_proof_from_projection(
        projection={"session_id": session_id, "session_path": str(session_path)},
        command_entrypoint="/project:typed-remote-control",
        launcher_source="claude_project_slash",
        now_utc="2026-05-04T23:20:30Z",
    )

    assert proof.proven_source_kind == "unspecified"
    assert proof.remote_session_id == ""


def test_typed_slash_source_proof_without_physical_confirmation_does_not_promote(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from dev.scripts.devctl.commands.remote_control._source_proof import (
        RemoteControlSourceProof,
    )

    monkeypatch.setattr(
        remote_control,
        "resolve_lifecycle_source_proof",
        lambda *args, **kwargs: RemoteControlSourceProof(
            proven_source_kind="claude_project_slash",
            provider_session_id="claude-code:session_test",
            proof_channel="claude_agent_mind_attribution",
            proof_source="/tmp/session.jsonl",
            proof_observed_at_utc="2026-05-04T23:20:00Z",
        ),
    )
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--entrypoint",
            "/project:typed-remote-control",
            "--launcher-source",
            "claude_project_slash",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "local_terminal"
    assert payload["attachment_active"] is False
    assert payload["state_change"] == "evidence_missing"
    assert payload["source_proof"]["proven_source_kind"] == "claude_project_slash"
    assert payload["source_proof"]["provider_session_id"] == "claude-code:session_test"
    attachment = payload["attachment"]
    assert attachment["status"] == "evidence_missing"
    assert attachment["remote_session_id"] == ""
    assert attachment["physical_remote_control_confirmed"] is False


def test_typed_slash_physical_confirmation_flag_without_identity_does_not_promote(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from dev.scripts.devctl.commands.remote_control._source_proof import (
        RemoteControlSourceProof,
    )

    monkeypatch.setattr(
        remote_control,
        "resolve_lifecycle_source_proof",
        lambda *args, **kwargs: RemoteControlSourceProof(
            proven_source_kind="claude_project_slash",
            provider_session_id="claude-code:session_test",
            proof_channel="claude_agent_mind_attribution",
            proof_source="/tmp/session.jsonl",
            proof_observed_at_utc="2026-05-04T23:20:00Z",
        ),
    )
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--entrypoint",
            "/project:typed-remote-control",
            "--launcher-source",
            "claude_project_slash",
            "--physical-remote-control-confirmed",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "local_terminal"
    assert payload["attachment_active"] is False
    assert payload["state_change"] == "evidence_missing"
    attachment = payload["attachment"]
    assert attachment["status"] == "evidence_missing"
    assert attachment["remote_session_id"] == ""
    assert attachment["physical_remote_control_confirmed"] is False


def test_typed_slash_builtin_remote_control_proof_promotes_mode(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from dev.scripts.devctl.commands.remote_control._source_proof import (
        RemoteControlSourceProof,
    )

    monkeypatch.setattr(
        remote_control,
        "resolve_lifecycle_source_proof",
        lambda *args, **kwargs: RemoteControlSourceProof(
            proven_source_kind="claude_project_slash",
            session_url="https://claude.ai/code/session_real",
            provider_session_id="claude-code:session_test",
            proof_channel="claude_agent_mind_remote_control_bridge_status",
            proof_source="/tmp/session.jsonl",
            proof_observed_at_utc="2026-05-04T23:20:00Z",
        ),
    )
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--entrypoint",
            "/project:typed-remote-control",
            "--launcher-source",
            "claude_project_slash",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "remote_control"
    assert payload["attachment_active"] is True
    assert payload["source_proof"]["session_url"] == "https://claude.ai/code/session_real"
    attachment = payload["attachment"]
    assert attachment["status"] == "attached"
    assert attachment["session_url"] == "https://claude.ai/code/session_real"
    assert attachment["remote_session_id"] == "session_real"


def test_builtin_remote_control_hook_promotes_from_transcript_url(
    tmp_path: Path,
    capsys,
) -> None:
    from dev.scripts.devctl.runtime.remote_control_invocation_receipt import (
        DEFAULT_REMOTE_CONTROL_INVOCATION_REL,
        receipt_from_mapping,
    )
    from dev.scripts.devctl.time_utils import utc_timestamp

    session_id = "test-claude-session-0001"
    session_path = tmp_path / f"{session_id}.jsonl"
    timestamp = utc_timestamp()
    session_path.write_text(
        "\n".join(
            json.dumps(event)
            for event in (
                {
                    "type": "system",
                    "subtype": "local_command",
                    "content": "<command-name>/remote-control</command-name>",
                    "timestamp": timestamp,
                    "sessionId": session_id,
                },
                {
                    "type": "system",
                    "subtype": "bridge_status",
                    "content": (
                        "/remote-control is active. Code in CLI or at "
                        "https://claude.ai/code/session_hook"
                    ),
                    "url": "https://claude.ai/code/session_hook",
                    "timestamp": timestamp,
                    "sessionId": session_id,
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )
    hook_input = tmp_path / "hook.json"
    hook_input.write_text(
        json.dumps(
            {
                "hook_event_name": "UserPromptSubmit",
                "prompt": "/remote-control",
                "session_id": session_id,
                "transcript_path": str(session_path),
                "cwd": str(Path(__file__).resolve().parents[5]),
            }
        ),
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "hook",
            "--provider",
            "claude",
            "--hook-input-file",
            str(hook_input),
            "--hook-poll-seconds",
            "0",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "remote_control"
    assert payload["attachment_active"] is True
    assert payload["source_proof"]["proven_source_kind"] == "claude_builtin_slash"
    assert payload["hook"]["hook_prompt_action"] == "enter"
    attachment = payload["attachment"]
    assert attachment["status"] == "attached"
    assert attachment["entrypoint"] == "claude_builtin_remote_control"
    assert attachment["launcher_source"] == "claude_builtin_slash"
    assert attachment["session_url"] == "https://claude.ai/code/session_hook"
    assert attachment["remote_session_id"] == "session_hook"
    assert attachment["physical_remote_control_confirmed"] is True
    assert attachment["physical_confirmation_method"] == "claude_hook_transcript"
    assert attachment["source_hook_event_name"] == "UserPromptSubmit"
    assert attachment["source_hook_prompt"] == "/remote-control"
    assert attachment["source_hook_session_id"] == session_id
    assert attachment["source_hook_transcript_path"] == str(session_path)
    assert attachment["source_hook_dedupe_key"]
    assert attachment["source_proof_channel"] == "claude_hook"

    receipt_path = tmp_path / DEFAULT_REMOTE_CONTROL_INVOCATION_REL
    last_line = receipt_path.read_text(encoding="utf-8").strip().splitlines()[-1]
    receipt = receipt_from_mapping(json.loads(last_line))
    assert receipt.proven_source_kind == "claude_builtin_slash"
    assert receipt.invocation_origin == "claude_builtin_slash"
    assert receipt.proof_channel == "claude_hook"
    assert receipt.physical_confirmation_method == "claude_hook_transcript"
    assert receipt.hook_event_name == "UserPromptSubmit"
    assert receipt.hook_prompt == "/remote-control"
    assert receipt.hook_session_id == session_id
    assert receipt.hook_transcript_path == str(session_path)
    assert receipt.hook_dedupe_key == attachment["source_hook_dedupe_key"]


def test_builtin_remote_control_hook_promotes_from_live_session_state(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from dev.scripts.devctl.commands.remote_control import _session_state_proof

    session_id = "test-claude-session-0001"
    session_path = tmp_path / f"{session_id}.jsonl"
    session_path.write_text("", encoding="utf-8")
    session_state_root = tmp_path / "claude-sessions"
    session_state_root.mkdir()
    (session_state_root / "33330.json").write_text(
        json.dumps(
            {
                "pid": 33330,
                "sessionId": session_id,
                "cwd": str(Path(__file__).resolve().parents[5]),
                "status": "idle",
                "updatedAt": _now_epoch_ms(),
                "bridgeSessionId": "session_state",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        _session_state_proof,
        "CLAUDE_SESSION_STATE_ROOT",
        session_state_root,
    )
    monkeypatch.setattr(_session_state_proof, "_pid_alive", lambda _pid: True)
    hook_input = tmp_path / "hook.json"
    hook_input.write_text(
        json.dumps(
            {
                "hook_event_name": "UserPromptExpansion",
                "prompt": "/remote-control",
                "command_name": "remote-control",
                "session_id": session_id,
                "transcript_path": str(session_path),
                "cwd": str(Path(__file__).resolve().parents[5]),
            }
        ),
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "hook",
            "--provider",
            "claude",
            "--hook-input-file",
            str(hook_input),
            "--hook-poll-seconds",
            "0",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "remote_control"
    assert payload["attachment_active"] is True
    assert payload["source_proof"]["proof_channel"] == "claude_session_state"
    attachment = payload["attachment"]
    assert attachment["status"] == "attached"
    assert attachment["session_url"] == "https://claude.ai/code/session_state"
    assert attachment["remote_session_id"] == "session_state"
    assert attachment["physical_remote_control_confirmed"] is True
    assert attachment["physical_confirmation_method"] == "claude_session_state_bridge"


def test_user_prompt_expansion_hook_promotes_and_dedupes_submit(
    tmp_path: Path,
    capsys,
) -> None:
    from dev.scripts.devctl.runtime.remote_control_invocation_receipt import (
        DEFAULT_REMOTE_CONTROL_INVOCATION_REL,
    )
    from dev.scripts.devctl.time_utils import utc_timestamp

    session_id = "test-claude-session-0001"
    session_path = tmp_path / f"{session_id}.jsonl"
    timestamp = utc_timestamp()
    session_path.write_text(
        "\n".join(
            json.dumps(event)
            for event in (
                {
                    "type": "system",
                    "subtype": "local_command",
                    "content": "<command-name>/remote-control</command-name>",
                    "timestamp": timestamp,
                    "sessionId": session_id,
                },
                {
                    "type": "system",
                    "subtype": "bridge_status",
                    "content": (
                        "/remote-control is active. Code in CLI or at "
                        "https://claude.ai/code/session_hook"
                    ),
                    "url": "https://claude.ai/code/session_hook",
                    "timestamp": timestamp,
                    "sessionId": session_id,
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )

    def run_hook(payload: dict[str, object]) -> dict[str, object]:
        hook_input = tmp_path / f"{payload['hook_event_name']}.json"
        hook_input.write_text(json.dumps(payload), encoding="utf-8")
        args = cli.build_parser().parse_args(
            [
                "remote-control",
                "hook",
                "--provider",
                "claude",
                "--hook-input-file",
                str(hook_input),
                "--hook-poll-seconds",
                "0",
                "--status-dir",
                str(tmp_path),
                "--format",
                "json",
            ]
        )
        assert remote_control.run(args) == 0
        return json.loads(capsys.readouterr().out)

    first = run_hook(
        {
            "hook_event_name": "UserPromptExpansion",
            "prompt": "/remote-control",
            "command_name": "remote-control",
            "command_source": "builtin",
            "session_id": session_id,
            "transcript_path": str(session_path),
        }
    )
    second = run_hook(
        {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "/remote-control",
            "session_id": session_id,
            "transcript_path": str(session_path),
        }
    )

    assert first["hook"]["hook_event_name"] == "UserPromptExpansion"
    assert first["attachment"]["source_hook_command_name"] == "remote-control"
    assert second["hook"]["deduped"] is True
    assert second["state_change"] == "no_op"
    receipt_lines = (tmp_path / DEFAULT_REMOTE_CONTROL_INVOCATION_REL).read_text(
        encoding="utf-8"
    ).strip().splitlines()
    assert len(receipt_lines) == 1


def test_hook_ignores_non_remote_control_prompt_without_writing_attachment(
    tmp_path: Path,
    capsys,
) -> None:
    hook_input = tmp_path / "hook.json"
    hook_input.write_text(
        json.dumps(
            {
                "hook_event_name": "UserPromptSubmit",
                "prompt": "please keep coding",
                "session_id": "session_test",
                "transcript_path": str(tmp_path / "session_test.jsonl"),
            }
        ),
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "hook",
            "--provider",
            "claude",
            "--hook-input-file",
            str(hook_input),
            "--hook-poll-seconds",
            "0",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["hook_prompt_action"] == "ignore"
    assert payload["hook_prompt_matched"] is False
    assert not (tmp_path / "sessions" / "claude-remote-control.json").exists()


def test_exit_resets_stale_physical_confirmation_flag(
    tmp_path: Path,
    capsys,
) -> None:
    from dev.scripts.devctl.runtime.remote_control_invocation_receipt import (
        DEFAULT_REMOTE_CONTROL_INVOCATION_REL,
        receipt_from_mapping,
    )

    enter = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--session-url",
            "https://claude.ai/code/session_active",
            "--physical-remote-control-confirmed",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )
    assert remote_control.run(enter) == 0
    enter_payload = json.loads(capsys.readouterr().out)
    enter_attachment = enter_payload["attachment"]
    assert enter_payload["operator_interaction_mode"] == "remote_control"
    assert enter_attachment["physical_remote_control_confirmed"] is False
    assert enter_attachment["physical_confirmation_method"] == "operator_assertion"
    receipt_path = tmp_path / DEFAULT_REMOTE_CONTROL_INVOCATION_REL
    first_line = receipt_path.read_text(encoding="utf-8").strip().splitlines()[-1]
    first_receipt = receipt_from_mapping(json.loads(first_line))
    assert first_receipt.physical_confirmation_method == "operator_assertion"

    exit_args = cli.build_parser().parse_args(
        [
            "remote-control",
            "exit",
            "--provider",
            "claude",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(exit_args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    attachment = payload["attachment"]
    assert attachment["status"] == "detached"
    assert attachment["physical_remote_control_confirmed"] is False
    assert attachment["physical_confirmation_method"] == "none"


def test_typed_slash_with_real_session_url_promotes_mode(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from dev.scripts.devctl.commands.remote_control._source_proof import (
        RemoteControlSourceProof,
    )

    monkeypatch.setattr(
        remote_control,
        "resolve_lifecycle_source_proof",
        lambda *args, **kwargs: RemoteControlSourceProof(
            proven_source_kind="unspecified",
        ),
    )
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--entrypoint",
            "/project:typed-remote-control",
            "--launcher-source",
            "claude_project_slash",
            "--session-url",
            "https://claude.ai/code/session_real",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "remote_control"
    assert payload["attachment_active"] is True
    attachment = payload["attachment"]
    assert attachment["status"] == "attached"
    assert attachment["remote_session_id"] == "session_real"
    assert attachment["session_url"] == "https://claude.ai/code/session_real"


def test_direct_cli_physical_confirmation_flag_does_not_promote(
    tmp_path: Path,
    capsys,
) -> None:
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--entrypoint",
            "/project:typed-remote-control",
            "--launcher-source",
            "claude_project_slash",
            "--physical-remote-control-confirmed",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "local_terminal"
    assert payload["attachment_active"] is False
    assert payload["state_change"] == "evidence_missing"


def test_direct_cli_identityless_heartbeat_does_not_refresh_active_attachment(
    tmp_path: Path,
    capsys,
) -> None:
    first = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--session-url",
            "https://claude.ai/code/session_active",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )
    assert remote_control.run(first) == 0
    capsys.readouterr()

    heartbeat = cli.build_parser().parse_args(
        [
            "remote-control",
            "heartbeat",
            "--provider",
            "claude",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )
    assert remote_control.run(heartbeat) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "local_terminal"
    assert payload["attachment_active"] is False
    assert payload["state_change"] == "evidence_missing"
    assert payload["attachment"]["status"] == "evidence_missing"
    assert payload["attachment"]["remote_session_id"] == ""


def test_trusted_provider_heartbeat_refreshes_existing_physical_identity(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from dev.scripts.devctl.commands.remote_control._source_proof import (
        RemoteControlSourceProof,
    )

    first = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--session-url",
            "https://claude.ai/code/session_active",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )
    assert remote_control.run(first) == 0
    capsys.readouterr()
    monkeypatch.setattr(
        remote_control,
        "resolve_lifecycle_source_proof",
        lambda *args, **kwargs: RemoteControlSourceProof(
            proven_source_kind="claude_builtin_slash",
            provider_session_id="claude-code:session_test",
            proof_channel="claude_session_state",
            proof_source="/tmp/33330.json",
            proof_observed_at_utc="2026-05-04T23:31:08Z",
        ),
    )
    heartbeat = cli.build_parser().parse_args(
        [
            "remote-control",
            "heartbeat",
            "--provider",
            "claude",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    assert remote_control.run(heartbeat) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "remote_control"
    assert payload["attachment_active"] is True
    assert payload["state_change"] in {"no_op", "heartbeat_refreshed"}
    assert payload["attachment"]["status"] == "attached"
    assert payload["attachment"]["remote_session_id"] == "session_active"
    assert payload["attachment"]["session_url"] == "https://claude.ai/code/session_active"


def test_status_reconciles_live_session_state_bridge(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from dev.scripts.devctl.commands.remote_control import _runtime_io

    session_state_root = tmp_path / "claude-sessions"
    session_state_root.mkdir()
    (session_state_root / "33330.json").write_text(
        json.dumps(
            {
                "pid": 33330,
                "sessionId": "test-claude-session-0001",
                "cwd": str(Path(__file__).resolve().parents[5]),
                "status": "idle",
                "updatedAt": _now_epoch_ms(),
                "bridgeSessionId": "session_state",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        _runtime_io._session_state_proof,
        "CLAUDE_SESSION_STATE_ROOT",
        session_state_root,
    )
    monkeypatch.setattr(
        _runtime_io._session_state_proof,
        "_pid_alive",
        lambda _pid: True,
    )
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "status",
            "--provider",
            "claude",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "remote_control"
    assert payload["attachment_active"] is True
    assert payload["attachment"]["remote_session_id"] == "session_state"
    assert payload["attachment"]["session_url"] == "https://claude.ai/code/session_state"
    assert payload["attachment"]["physical_confirmation_method"] == (
        "claude_session_state_bridge"
    )
    assert payload["attachment"]["source_proof_channel"] == "claude_session_state"


def test_status_clears_session_state_attachment_when_bridge_id_disappears(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from dev.scripts.devctl.commands.remote_control import _runtime_io

    session_state_root = tmp_path / "claude-sessions"
    session_state_root.mkdir()
    state_path = session_state_root / "33330.json"
    state_payload = {
        "pid": 33330,
        "sessionId": "test-claude-session-0001",
        "cwd": str(Path(__file__).resolve().parents[5]),
        "status": "idle",
        "updatedAt": _now_epoch_ms(),
        "bridgeSessionId": "session_state",
    }
    state_path.write_text(json.dumps(state_payload), encoding="utf-8")
    monkeypatch.setattr(
        _runtime_io._session_state_proof,
        "CLAUDE_SESSION_STATE_ROOT",
        session_state_root,
    )
    monkeypatch.setattr(
        _runtime_io._session_state_proof,
        "_pid_alive",
        lambda _pid: True,
    )
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "status",
            "--provider",
            "claude",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )
    assert remote_control.run(args) == 0
    capsys.readouterr()
    state_payload["bridgeSessionId"] = None
    state_payload["updatedAt"] = _now_epoch_ms()
    state_path.write_text(json.dumps(state_payload), encoding="utf-8")

    assert remote_control.run(args) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["operator_interaction_mode"] == "local_terminal"
    assert payload["attachment_active"] is False
    assert payload["attachment"]["status"] == "evidence_missing"
    assert payload["attachment"]["physical_confirmation_method"] == "none"


def test_stale_remote_attachment_does_not_promote_mode() -> None:
    stale = RemoteControlAttachmentState(
        provider="claude",
        attachment_id="remote-attach-stale",
        status="attached",
        attached_at_utc="2026-05-04T00:00:00Z",
        last_seen_utc="2026-05-04T00:00:00Z",
        heartbeat_ttl_seconds=1,
    )

    assert remote_attachment_active(stale) is False
    assert (
        resolve_interaction_mode(
            "remote_control",
            remote_control_attachment=stale,
            effective_reviewer_mode="single_agent",
        )
        == "single_agent"
    )


def test_synthetic_claude_code_session_id_does_not_promote_mode() -> None:
    synthetic = RemoteControlAttachmentState(
        provider="claude",
        attachment_id="remote-attach-synthetic",
        status="attached",
        remote_session_id="claude-code:session_test",
        attached_at_utc="2026-05-04T00:00:00Z",
        last_seen_utc="2026-05-04T00:00:00Z",
        heartbeat_ttl_seconds=-1,
    )

    assert remote_attachment_active(synthetic) is False


def test_start_without_provider_launch_api_fails_closed(
    tmp_path: Path,
    capsys,
) -> None:
    args = cli.build_parser().parse_args(
        [
            "remote-control",
            "start",
            "--provider",
            "claude",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )

    rc = remote_control.run(args)

    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["operator_interaction_mode"] == "local_terminal"
    assert payload["attachment_active"] is False
    assert payload["state_change"] == "evidence_missing"
    assert "built-in slash command" in payload["errors"][0]


def test_remote_control_slash_catalog_keeps_only_typed_recovery_adapter() -> None:
    rows = build_remote_control_slash_adapter_catalog()
    commands = {row.slash_command: row.backend_command for row in rows}

    # `/project:typed-remote-control` is the only project-facing slash. The
    # retired `/project:remote-control` and `/project:bridge-loop` aliases
    # must not be generated because they confuse Claude built-in dispatch.
    assert set(commands) == {
        "/project:typed-remote-control",
    }
    canonical_rows = [row for row in rows if not row.compatibility_alias]
    alias_rows = [row for row in rows if row.compatibility_alias]
    assert {row.slash_command for row in canonical_rows} == {
        "/project:typed-remote-control",
    }
    assert alias_rows == []
    assert all("devctl.py remote-control enter" in command for command in commands.values())
    for command in commands.values():
        parsed = cli.build_parser().parse_args(shlex.split(command)[2:])
        assert parsed.command == "remote-control"
        assert parsed.action == "enter"


def test_claude_remote_control_slash_files_are_thin_adapters() -> None:
    """Only the canonical typed recovery slash should be installed.

    The .claude command file must:
    - declare YAML frontmatter (description + allowed-tools) so Claude's
      slash menu surfaces them with an active label;
    - delegate to ``devctl remote-control enter`` (no embedded policy);
    - carry the "thin adapter" disclaimer so future edits don't accrete
      lifecycle policy into the slash file itself.

    Per rev_pkt_2996 finding #7: the canonical entrypoint
    ``/project:typed-remote-control`` must be referenced in the
    canonical file and not just left to the catalog/adapter layer.
    """
    root = Path(__file__).resolve().parents[5]
    typed_text = (
        root / ".claude" / "commands" / "typed-remote-control.md"
    ).read_text(encoding="utf-8")

    assert not (root / ".claude" / "commands" / "remote-control.md").exists()
    assert not (root / ".claude" / "commands" / "bridge-loop.md").exists()
    assert typed_text.startswith("---\n"), typed_text[:80]
    assert "description:" in typed_text.split("---", 2)[1]
    assert "allowed-tools:" in typed_text.split("---", 2)[1]
    assert "This file is only an adapter." in typed_text
    assert "devctl.py remote-control enter --provider claude" in typed_text

    assert (
        "--entrypoint /project:typed-remote-control" in typed_text
    ), "canonical file must reference its own entrypoint"
    assert "/project:remote-control" not in typed_text
    assert "/project:bridge-loop" not in typed_text


def test_claude_settings_json_wires_remote_control_hooks() -> None:
    root = Path(__file__).resolve().parents[5]
    payload = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    hooks = payload["hooks"]

    expansion_hook = hooks["UserPromptExpansion"][0]["hooks"][0]
    assert hooks["UserPromptExpansion"][0]["matcher"] == "remote-control"
    assert hooks["UserPromptExpansion"][1]["matcher"] == "rc"
    assert expansion_hook["type"] == "command"
    assert expansion_hook["async"] is True
    assert "remote-control hook --provider claude" in expansion_hook["command"]
    assert "claude_builtin_remote_control" in expansion_hook["command"]
    assert "claude_builtin_slash" in expansion_hook["command"]

    prompt_hook = hooks["UserPromptSubmit"][0]["hooks"][0]
    assert prompt_hook["type"] == "command"
    assert prompt_hook["async"] is True
    assert "remote-control hook --provider claude" in prompt_hook["command"]
    assert "claude_builtin_remote_control" in prompt_hook["command"]
    assert "claude_builtin_slash" in prompt_hook["command"]

    end_hook = hooks["SessionEnd"][0]["hooks"][0]
    assert end_hook["type"] == "command"
    assert "remote-control exit --provider claude" in end_hook["command"]
    assert "claude_session_end" in end_hook["command"]


def _emitted_state_change(
    capsys, args_list: list[str], expected: str
) -> None:
    """Drive one lifecycle invocation and assert state_change is in the closed enum.

    Per rev_pkt_3007 Q4: every emitted state_change value MUST be a member
    of REMOTE_CONTROL_INVOCATION_STATE_CHANGES so receipt readers can
    replay the closed lifecycle vocabulary without inferring loose strings.
    """
    args = cli.build_parser().parse_args(args_list)
    rc = remote_control.run(args)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    state_change = payload.get("state_change")
    assert state_change in REMOTE_CONTROL_INVOCATION_STATE_CHANGES, (
        f"state_change={state_change!r} not in closed enum "
        f"{REMOTE_CONTROL_INVOCATION_STATE_CHANGES}"
    )
    assert state_change == expected, (
        f"expected state_change={expected!r}, got {state_change!r}"
    )


def test_state_change_dry_run_preview_is_in_closed_enum(
    tmp_path: Path,
    capsys,
) -> None:
    """Per rev_pkt_3007 Q4: dry-run emits ``preview`` as a typed value."""
    _emitted_state_change(
        capsys,
        [
            "remote-control",
            "start",
            "--provider",
            "claude",
            "--dry-run",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ],
        expected="preview",
    )


def test_state_change_first_identity_bound_enter_is_created(
    tmp_path: Path,
    capsys,
) -> None:
    """Per rev_pkt_3007 Q4 + rev_pkt_3023 P1/P0 #4: the first
    identity-bound enter (no prior attachment) classifies as ``created``,
    NOT ``heartbeat_refreshed``. The previous test pinned the wrong
    behavior; the classifier now correctly distinguishes first-create
    from heartbeat-refresh based on observable before/after fields.
    """
    _emitted_state_change(
        capsys,
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--session-name",
            "Phone Session",
            "--session-url",
            "https://claude.ai/code/session_test",
            "--launcher-source",
            "slash",
            "--entrypoint",
            "/project:typed-remote-control",
            "--heartbeat-ttl-seconds",
            "60",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ],
        expected="created",
    )


def test_state_change_subsequent_enter_is_heartbeat_refreshed(
    tmp_path: Path,
    capsys,
) -> None:
    """Companion to ``..._first_identity_bound_enter_is_created``: a
    second enter against the SAME identity-bound attachment must
    classify as ``heartbeat_refreshed`` (or ``no_op`` when nothing
    changed). This proves the classifier distinguishes the lifecycle
    transitions per rev_pkt_3023 P1/P0 #4.
    """
    base_args = [
        "remote-control",
        "enter",
        "--provider",
        "claude",
        "--session-name",
        "Phone Session",
        "--session-url",
        "https://claude.ai/code/session_test",
        "--launcher-source",
        "slash",
        "--entrypoint",
        "/project:typed-remote-control",
        "--heartbeat-ttl-seconds",
        "60",
        "--status-dir",
        str(tmp_path),
        "--format",
        "json",
    ]
    first = cli.build_parser().parse_args(base_args)
    assert remote_control.run(first) == 0
    capsys.readouterr()

    second = cli.build_parser().parse_args(base_args)
    assert remote_control.run(second) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["state_change"] in {"heartbeat_refreshed", "no_op"}
    assert payload["state_change"] in REMOTE_CONTROL_INVOCATION_STATE_CHANGES


def test_state_change_evidence_missing_is_in_closed_enum(
    tmp_path: Path,
    capsys,
) -> None:
    """Per rev_pkt_3007 Q4: identity-less enter fails closed to ``evidence_missing``."""
    _emitted_state_change(
        capsys,
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ],
        expected="evidence_missing",
    )


def test_state_change_exit_already_detached_is_in_closed_enum(
    tmp_path: Path,
    capsys,
) -> None:
    """Per rev_pkt_3007 Q4: exit with no existing attachment emits ``already_detached``."""
    _emitted_state_change(
        capsys,
        [
            "remote-control",
            "exit",
            "--provider",
            "claude",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ],
        expected="already_detached",
    )


def test_state_change_exit_with_existing_detached_is_in_closed_enum(
    tmp_path: Path,
    capsys,
) -> None:
    """Per rev_pkt_3007 Q4: exit on a live attachment emits ``detached``."""
    enter_args = cli.build_parser().parse_args(
        [
            "remote-control",
            "enter",
            "--provider",
            "claude",
            "--session-name",
            "Phone Session",
            "--session-url",
            "https://claude.ai/code/session_test",
            "--launcher-source",
            "slash",
            "--entrypoint",
            "/project:typed-remote-control",
            "--heartbeat-ttl-seconds",
            "60",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ]
    )
    assert remote_control.run(enter_args) == 0
    capsys.readouterr()

    _emitted_state_change(
        capsys,
        [
            "remote-control",
            "exit",
            "--provider",
            "claude",
            "--status-dir",
            str(tmp_path),
            "--format",
            "json",
        ],
        expected="detached",
    )
