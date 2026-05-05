"""Tests for non-flag remote-control source proof."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from dev.scripts.devctl.commands.remote_control import _source_proof
from dev.scripts.devctl.commands.remote_control import _session_state_proof


SESSION_ID = "test-claude-session-0001"
CLAUDE_ENV = {
    "CLAUDECODE": "1",
    "AI_AGENT": "claude-code/2.1.126/agent",
    "CLAUDE_CODE_ENTRYPOINT": "cli",
}


def _base_args(**overrides: object) -> SimpleNamespace:
    values = {
        "provider": "claude",
        "entrypoint": "/project:typed-remote-control",
        "launcher_source": "claude_project_slash",
        "remote_session_id": "",
        "session_url": "",
        "status_dir": "",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _write_session(path: Path, *events: dict[str, object]) -> None:
    path.write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )


def _epoch_ms(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)


def _write_session_state(root: Path, name: str, payload: dict[str, object]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_live_session_state_bridge_session_id_proves_active_remote_control(
    tmp_path: Path,
) -> None:
    root = tmp_path / "sessions"
    state_path = _write_session_state(
        root,
        "33330.json",
        {
            "pid": 33330,
            "sessionId": SESSION_ID,
            "cwd": str(tmp_path),
            "status": "idle",
            "updatedAt": _epoch_ms("2026-05-04T23:31:08Z"),
            "bridgeSessionId": "session_live",
        },
    )

    proof = _session_state_proof.resolve_live_session_state_bridge_proof(
        session_id=SESSION_ID,
        now_utc="2026-05-04T23:31:10Z",
        expected_cwd=str(tmp_path),
        max_age_seconds=300,
        session_state_root=root,
        pid_checker=lambda _pid: True,
    )

    assert proof is not None
    assert proof.path == state_path
    assert proof.bridge_session_id == "session_live"
    assert proof.session_url == "https://claude.ai/code/session_live"
    assert proof.updated_at_utc == "2026-05-04T23:31:08Z"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("bridgeSessionId", None),
        ("bridgeSessionId", ""),
        ("bridgeSessionId", "not-a-bridge-session"),
        ("sessionId", "other-session"),
        ("cwd", "/tmp/other-project"),
        ("status", "terminated"),
    ],
)
def test_live_session_state_bridge_proof_fails_closed_for_invalid_state(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    root = tmp_path / "sessions"
    payload = {
        "pid": 33330,
        "sessionId": SESSION_ID,
        "cwd": str(tmp_path),
        "status": "idle",
        "updatedAt": _epoch_ms("2026-05-04T23:31:08Z"),
        "bridgeSessionId": "session_live",
    }
    payload[field] = value
    _write_session_state(root, "33330.json", payload)

    proof = _session_state_proof.resolve_live_session_state_bridge_proof(
        session_id=SESSION_ID,
        now_utc="2026-05-04T23:31:10Z",
        expected_cwd=str(tmp_path),
        max_age_seconds=300,
        session_state_root=root,
        pid_checker=lambda _pid: True,
    )

    assert proof is None


def test_live_session_state_bridge_proof_rejects_stale_updated_at(
    tmp_path: Path,
) -> None:
    root = tmp_path / "sessions"
    _write_session_state(
        root,
        "33330.json",
        {
            "pid": 33330,
            "sessionId": SESSION_ID,
            "cwd": str(tmp_path),
            "status": "idle",
            "updatedAt": _epoch_ms("2026-05-04T23:00:00Z"),
            "bridgeSessionId": "session_live",
        },
    )

    proof = _session_state_proof.resolve_live_session_state_bridge_proof(
        session_id=SESSION_ID,
        now_utc="2026-05-04T23:31:10Z",
        expected_cwd=str(tmp_path),
        max_age_seconds=300,
        session_state_root=root,
        pid_checker=lambda _pid: True,
    )

    assert proof is None


def test_attribution_skill_event_alone_proves_typed_slash(tmp_path: Path) -> None:
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(
        session_path,
        {
            "timestamp": "2026-05-04T23:33:42Z",
            "attributionSkill": "typed-remote-control",
            "message": {"content": [{"type": "text", "text": "slash invoked"}]},
        },
    )

    proof = _source_proof.resolve_lifecycle_source_proof_from_projection(
        projection={"session_id": SESSION_ID, "session_path": str(session_path)},
        command_entrypoint="/project:typed-remote-control",
        launcher_source="claude_project_slash",
        now_utc="2026-05-04T23:34:00Z",
    )

    assert proof.proven_source_kind == "claude_project_slash"
    assert proof.remote_session_id == ""
    assert proof.session_url == ""
    assert proof.provider_session_id == f"claude-code:{SESSION_ID}"
    assert proof.proof_observed_at_utc == "2026-05-04T23:33:42Z"


def test_builtin_remote_control_bridge_status_binds_physical_session_url(
    tmp_path: Path,
) -> None:
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(
        session_path,
        {
            "type": "system",
            "subtype": "local_command",
            "content": "<command-name>/remote-control</command-name>",
            "timestamp": "2026-05-04T23:31:00Z",
            "sessionId": SESSION_ID,
        },
        {
            "type": "system",
            "subtype": "bridge_status",
            "content": (
                "/remote-control is active. Code in CLI or at "
                "https://claude.ai/code/session_real"
            ),
            "url": "https://claude.ai/code/session_real",
            "timestamp": "2026-05-04T23:31:01Z",
            "sessionId": SESSION_ID,
        },
        {
            "timestamp": "2026-05-04T23:31:05Z",
            "attributionSkill": "typed-remote-control",
            "sessionId": SESSION_ID,
        },
    )

    proof = _source_proof.resolve_lifecycle_source_proof_from_projection(
        projection={"session_id": SESSION_ID, "session_path": str(session_path)},
        command_entrypoint="/project:typed-remote-control",
        launcher_source="claude_project_slash",
        now_utc="2026-05-04T23:31:10Z",
    )

    assert proof.proven_source_kind == "claude_project_slash"
    assert proof.session_url == "https://claude.ai/code/session_real"
    assert proof.provider_session_id == f"claude-code:{SESSION_ID}"
    assert proof.proof_channel == "claude_agent_mind_remote_control_bridge_status"
    assert proof.proof_observed_at_utc == "2026-05-04T23:31:01Z"


def test_typed_remote_control_source_proof_prefers_live_session_state_bridge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_state_root = tmp_path / "claude-sessions"
    _write_session_state(
        session_state_root,
        "33330.json",
        {
            "pid": 33330,
            "sessionId": SESSION_ID,
            "cwd": str(tmp_path),
            "status": "idle",
            "updatedAt": _epoch_ms("2026-05-04T23:31:08Z"),
            "bridgeSessionId": "session_state",
        },
    )
    monkeypatch.setattr(
        _session_state_proof,
        "CLAUDE_SESSION_STATE_ROOT",
        session_state_root,
    )
    monkeypatch.setattr(_session_state_proof, "_pid_alive", lambda _pid: True)
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(
        session_path,
        {
            "timestamp": "2026-05-04T23:31:05Z",
            "attributionSkill": "typed-remote-control",
            "sessionId": SESSION_ID,
        },
    )

    proof = _source_proof.resolve_lifecycle_source_proof_from_projection(
        projection={"session_id": SESSION_ID, "session_path": str(session_path)},
        command_entrypoint="/project:typed-remote-control",
        launcher_source="claude_project_slash",
        now_utc="2026-05-04T23:31:10Z",
    )

    assert proof.proven_source_kind == "claude_project_slash"
    assert proof.remote_session_id == "session_state"
    assert proof.session_url == "https://claude.ai/code/session_state"
    assert proof.proof_channel == "claude_session_state"
    assert proof.physical_confirmation_method == "claude_session_state_bridge"


def test_builtin_remote_control_hook_binds_physical_session_url(
    tmp_path: Path,
) -> None:
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(
        session_path,
        {
            "type": "system",
            "subtype": "local_command",
            "content": "<command-name>/remote-control</command-name>",
            "timestamp": "2026-05-04T23:31:00Z",
            "sessionId": SESSION_ID,
        },
        {
            "type": "system",
            "subtype": "bridge_status",
            "content": (
                "/remote-control is active. Code in CLI or at "
                "https://claude.ai/code/session_hook"
            ),
            "timestamp": "2026-05-04T23:31:01Z",
            "sessionId": SESSION_ID,
        },
    )

    proof = _source_proof.resolve_builtin_source_proof_from_hook_payload(
        payload={
            "hook_event_name": "UserPromptSubmit",
            "prompt": "/remote-control",
            "session_id": SESSION_ID,
            "transcript_path": str(session_path),
        },
        now_utc="2026-05-04T23:31:10Z",
    )

    assert proof.proven_source_kind == "claude_builtin_slash"
    assert proof.session_url == "https://claude.ai/code/session_hook"
    assert proof.provider_session_id == f"claude-code:{SESSION_ID}"
    assert proof.proof_channel == "claude_hook"
    assert proof.physical_confirmation_method == "claude_hook_transcript"
    assert proof.hook_event_name == "UserPromptSubmit"
    assert proof.hook_prompt == "/remote-control"
    assert proof.hook_session_id == SESSION_ID
    assert proof.hook_transcript_path == str(session_path)
    assert proof.hook_dedupe_key


def test_builtin_remote_control_hook_prefers_live_session_state_bridge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_state_root = tmp_path / "claude-sessions"
    _write_session_state(
        session_state_root,
        "33330.json",
        {
            "pid": 33330,
            "sessionId": SESSION_ID,
            "cwd": str(tmp_path),
            "status": "idle",
            "updatedAt": _epoch_ms("2026-05-04T23:31:08Z"),
            "bridgeSessionId": "session_state",
        },
    )
    monkeypatch.setattr(
        _session_state_proof,
        "CLAUDE_SESSION_STATE_ROOT",
        session_state_root,
    )
    monkeypatch.setattr(_session_state_proof, "_pid_alive", lambda _pid: True)
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(
        session_path,
        {
            "type": "system",
            "subtype": "bridge_status",
            "content": (
                "/remote-control is active. Code in CLI or at "
                "https://claude.ai/code/session_old"
            ),
            "timestamp": "2026-05-04T23:00:01Z",
            "sessionId": SESSION_ID,
        },
    )

    proof = _source_proof.resolve_builtin_source_proof_from_hook_payload(
        payload={
            "hook_event_name": "UserPromptExpansion",
            "prompt": "/remote-control",
            "command_name": "remote-control",
            "session_id": SESSION_ID,
            "transcript_path": str(session_path),
            "cwd": str(tmp_path),
        },
        now_utc="2026-05-04T23:31:10Z",
    )

    assert proof.proven_source_kind == "claude_builtin_slash"
    assert proof.remote_session_id == "session_state"
    assert proof.session_url == "https://claude.ai/code/session_state"
    assert proof.proof_channel == "claude_session_state"
    assert proof.physical_confirmation_method == "claude_session_state_bridge"
    assert proof.proof_source == str(session_state_root / "33330.json")


def test_user_prompt_expansion_hook_binds_same_physical_session_url(
    tmp_path: Path,
) -> None:
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(
        session_path,
        {
            "type": "system",
            "subtype": "local_command",
            "content": "<command-name>/remote-control</command-name>",
            "timestamp": "2026-05-04T23:31:00Z",
            "sessionId": SESSION_ID,
        },
        {
            "type": "system",
            "subtype": "bridge_status",
            "content": (
                "/remote-control is active. Code in CLI or at "
                "https://claude.ai/code/session_hook"
            ),
            "timestamp": "2026-05-04T23:31:01Z",
            "sessionId": SESSION_ID,
        },
    )
    submit_payload = {
        "hook_event_name": "UserPromptSubmit",
        "prompt": "/remote-control",
        "session_id": SESSION_ID,
        "transcript_path": str(session_path),
    }
    expansion_payload = {
        "hook_event_name": "UserPromptExpansion",
        "prompt": "/remote-control",
        "command_name": "remote-control",
        "command_args": "",
        "command_source": "builtin",
        "session_id": SESSION_ID,
        "transcript_path": str(session_path),
    }

    submit_proof = _source_proof.resolve_builtin_source_proof_from_hook_payload(
        payload=submit_payload,
        now_utc="2026-05-04T23:31:10Z",
    )
    expansion_proof = _source_proof.resolve_builtin_source_proof_from_hook_payload(
        payload=expansion_payload,
        now_utc="2026-05-04T23:31:10Z",
    )

    assert expansion_proof.proven_source_kind == "claude_builtin_slash"
    assert expansion_proof.session_url == "https://claude.ai/code/session_hook"
    assert expansion_proof.hook_event_name == "UserPromptExpansion"
    assert expansion_proof.hook_command_name == "remote-control"
    assert expansion_proof.hook_dedupe_key == submit_proof.hook_dedupe_key


def test_hook_rejects_bridge_status_from_different_session(tmp_path: Path) -> None:
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(
        session_path,
        {
            "type": "system",
            "subtype": "local_command",
            "content": "<command-name>/remote-control</command-name>",
            "timestamp": "2026-05-04T23:31:00Z",
            "sessionId": SESSION_ID,
        },
        {
            "type": "system",
            "subtype": "bridge_status",
            "content": (
                "/remote-control is active. Code in CLI or at "
                "https://claude.ai/code/session_other"
            ),
            "timestamp": "2026-05-04T23:31:01Z",
            "sessionId": "other-session",
        },
    )

    proof = _source_proof.resolve_builtin_source_proof_from_hook_payload(
        payload={
            "hook_event_name": "UserPromptExpansion",
            "prompt": "/remote-control",
            "command_name": "remote-control",
            "session_id": SESSION_ID,
            "transcript_path": str(session_path),
        },
        now_utc="2026-05-04T23:31:10Z",
    )

    assert proof.proven_source_kind == "claude_builtin_slash"
    assert proof.session_url == ""
    assert proof.physical_confirmation_method == "none"


def test_hook_ignores_non_remote_control_prompts(tmp_path: Path) -> None:
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(session_path)

    assert (
        _source_proof.hook_prompt_action(
            {
                "hook_event_name": "UserPromptSubmit",
                "prompt": "please keep coding",
                "session_id": SESSION_ID,
                "transcript_path": str(session_path),
            }
        )
        == "ignore"
    )
    proof = _source_proof.resolve_builtin_source_proof_from_hook_payload(
        payload={
            "hook_event_name": "UserPromptSubmit",
            "prompt": "please keep coding",
            "session_id": SESSION_ID,
            "transcript_path": str(session_path),
        },
        now_utc="2026-05-04T23:31:10Z",
    )

    assert proof.proven_source_kind == "unspecified"


def test_bridge_status_without_builtin_command_binds_activation_session_url(
    tmp_path: Path,
) -> None:
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(
        session_path,
        {
            "type": "system",
            "subtype": "bridge_status",
            "content": (
                "/remote-control is active. Code in CLI or at "
                "https://claude.ai/code/session_real"
            ),
            "timestamp": "2026-05-04T23:31:01Z",
            "sessionId": SESSION_ID,
        },
        {
            "timestamp": "2026-05-04T23:31:05Z",
            "attributionSkill": "typed-remote-control",
            "sessionId": SESSION_ID,
        },
    )

    proof = _source_proof.resolve_lifecycle_source_proof_from_projection(
        projection={"session_id": SESSION_ID, "session_path": str(session_path)},
        command_entrypoint="/project:typed-remote-control",
        launcher_source="claude_project_slash",
        now_utc="2026-05-04T23:31:10Z",
    )

    assert proof.proven_source_kind == "claude_project_slash"
    assert proof.session_url == "https://claude.ai/code/session_real"
    assert proof.proof_channel == "claude_agent_mind_remote_control_bridge_status"


def test_stale_builtin_remote_control_bridge_status_does_not_bind_session_url(
    tmp_path: Path,
) -> None:
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(
        session_path,
        {
            "type": "system",
            "subtype": "local_command",
            "content": "<command-name>/remote-control</command-name>",
            "timestamp": "2026-05-04T23:00:00Z",
            "sessionId": SESSION_ID,
        },
        {
            "type": "system",
            "subtype": "bridge_status",
            "content": (
                "/remote-control is active. Code in CLI or at "
                "https://claude.ai/code/session_stale"
            ),
            "timestamp": "2026-05-04T23:00:01Z",
            "sessionId": SESSION_ID,
        },
        {
            "timestamp": "2026-05-04T23:31:05Z",
            "attributionSkill": "typed-remote-control",
            "sessionId": SESSION_ID,
        },
    )

    proof = _source_proof.resolve_lifecycle_source_proof_from_projection(
        projection={"session_id": SESSION_ID, "session_path": str(session_path)},
        command_entrypoint="/project:typed-remote-control",
        launcher_source="claude_project_slash",
        now_utc="2026-05-04T23:31:10Z",
    )

    assert proof.proven_source_kind == "claude_project_slash"
    assert proof.session_url == ""


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provider", "codex"),
        ("entrypoint", "/project:remote-control"),
        ("launcher_source", "direct_cli"),
        ("remote_session_id", "claude-code:existing"),
        ("session_url", "https://claude.ai/code/session"),
        ("status_dir", "/tmp/status-override"),
    ],
)
def test_lifecycle_source_proof_requires_every_non_flag_condition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
) -> None:
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(
        session_path,
        {
            "timestamp": "2026-05-04T23:33:42Z",
            "attributionSkill": "typed-remote-control",
        },
    )
    monkeypatch.setattr(
        _source_proof,
        "read_agent_mind_projection",
        lambda *args, **kwargs: {
            "session_id": SESSION_ID,
            "session_path": str(session_path),
        },
    )

    proof = _source_proof.resolve_lifecycle_source_proof(
        _base_args(**{field: value}),
        repo_root=tmp_path,
        now_utc="2026-05-04T23:34:00Z",
        environ=CLAUDE_ENV,
    )

    assert proof.proven_source_kind == "unspecified"
    assert proof.remote_session_id == ""


@pytest.mark.parametrize(
    "environ",
    [
        {},
        {"CLAUDECODE": "1", "AI_AGENT": "codex/0.1", "CLAUDE_CODE_ENTRYPOINT": "cli"},
        {"CLAUDECODE": "1", "AI_AGENT": "claude-code/2.1.126/agent"},
    ],
)
def test_lifecycle_source_proof_requires_claude_process_attestation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    environ: dict[str, str],
) -> None:
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(
        session_path,
        {
            "timestamp": "2026-05-04T23:33:42Z",
            "attributionSkill": "typed-remote-control",
        },
    )
    monkeypatch.setattr(
        _source_proof,
        "read_agent_mind_projection",
        lambda *args, **kwargs: {
            "session_id": SESSION_ID,
            "session_path": str(session_path),
        },
    )

    proof = _source_proof.resolve_lifecycle_source_proof(
        _base_args(),
        repo_root=tmp_path,
        now_utc="2026-05-04T23:34:00Z",
        environ=environ,
    )

    assert proof.proven_source_kind == "unspecified"
    assert proof.remote_session_id == ""


def test_lifecycle_source_proof_accepts_env_and_attribution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_path = tmp_path / f"{SESSION_ID}.jsonl"
    _write_session(
        session_path,
        {
            "timestamp": "2026-05-04T23:33:42Z",
            "attributionSkill": "typed-remote-control",
        },
    )
    monkeypatch.setattr(
        _source_proof,
        "read_agent_mind_projection",
        lambda *args, **kwargs: {
            "session_id": SESSION_ID,
            "session_path": str(session_path),
        },
    )

    proof = _source_proof.resolve_lifecycle_source_proof(
        _base_args(),
        repo_root=tmp_path,
        now_utc="2026-05-04T23:34:00Z",
        environ=CLAUDE_ENV,
    )

    assert proof.proven_source_kind == "claude_project_slash"
    assert proof.remote_session_id == ""
    assert proof.session_url == ""
    assert proof.provider_session_id == f"claude-code:{SESSION_ID}"
