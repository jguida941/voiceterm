"""Non-flag source proof for remote-control lifecycle calls."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ...time_utils import parse_utc_timestamp
from ..rollout_tail.discovery import (
    discover_latest_session,
    session_id_from_path,
)
from ..rollout_tail.constants import PROVIDER_CLAUDE
from ...runtime.agent_mind_projection_read import read_agent_mind_projection
from ._proof_types import (
    CLAUDE_BUILTIN_SLASH_SOURCE,
    CLAUDE_CODE_SESSION_ID_PREFIX,
    CLAUDE_PROJECT_SLASH_SOURCE,
    DEFAULT_SOURCE_PROOF_MAX_AGE_SECONDS,
    RemoteControlSourceProof,
    TYPED_REMOTE_CONTROL_ATTRIBUTION,
)
from ._hook_source_proof import (
    hook_prompt_action,
    resolve_builtin_source_proof_from_hook_payload,
)
from ._session_state_proof import (
    SESSION_STATE_PHYSICAL_METHOD,
    SESSION_STATE_PROOF_CHANNEL,
    resolve_live_session_state_bridge_proof,
)
from ._transcript_proof import (
    latest_matching_builtin_remote_control_proof,
    read_jsonl_tail,
    remote_control_session_url,
)


def resolve_lifecycle_source_proof(
    args: Any,
    *,
    repo_root: Path,
    now_utc: str,
    environ: Mapping[str, str] | None = None,
) -> RemoteControlSourceProof:
    """Resolve proof that is independent of user-supplied CLI flags.

    The slash adapter passes ``--entrypoint`` and ``--launcher-source`` for audit
    narrative only; a copied direct CLI can pass the same strings. This resolver
    only promotes when the command also has Claude process evidence and a fresh
    Claude transcript event attributed to the typed slash command.
    """
    if _field(args, "status_dir"):
        # Test/portable overrides must not consume ambient project-level Claude
        # transcript proof from the developer machine.
        return RemoteControlSourceProof()
    if _field(args, "provider") != "claude":
        return RemoteControlSourceProof()
    if _field(args, "entrypoint") != "/project:typed-remote-control":
        return RemoteControlSourceProof()
    if _field(args, "launcher_source") != CLAUDE_PROJECT_SLASH_SOURCE:
        return RemoteControlSourceProof()
    if _field(args, "remote_session_id") or _field(args, "session_url"):
        return RemoteControlSourceProof()

    env = environ if environ is not None else os.environ
    if not _claude_process_attested(env):
        return RemoteControlSourceProof()

    projection = read_agent_mind_projection(repo_root, provider="claude")
    return resolve_lifecycle_source_proof_from_projection(
        projection=projection,
        command_entrypoint=_field(args, "entrypoint"),
        launcher_source=_field(args, "launcher_source"),
        now_utc=now_utc,
    )


def resolve_lifecycle_source_proof_from_projection(
    *,
    projection: Mapping[str, object],
    command_entrypoint: str,
    launcher_source: str,
    now_utc: str,
    max_age_seconds: int = DEFAULT_SOURCE_PROOF_MAX_AGE_SECONDS,
) -> RemoteControlSourceProof:
    """Resolve typed slash proof from an agent-mind projection + JSONL source."""
    if command_entrypoint != "/project:typed-remote-control":
        return RemoteControlSourceProof()
    if launcher_source != CLAUDE_PROJECT_SLASH_SOURCE:
        return RemoteControlSourceProof()
    path, session_id = _resolve_claude_session(projection)
    if not session_id or path is None:
        return RemoteControlSourceProof()
    events = read_jsonl_tail(path)
    event = _latest_matching_typed_remote_control_event(
        events=events,
        command_entrypoint=command_entrypoint,
        launcher_source=launcher_source,
        now_utc=now_utc,
        max_age_seconds=max_age_seconds,
    )
    if not event:
        return RemoteControlSourceProof()
    session_state = resolve_live_session_state_bridge_proof(
        session_id=session_id,
        now_utc=now_utc,
        max_age_seconds=max_age_seconds,
    )
    if session_state is not None:
        return RemoteControlSourceProof(
            proven_source_kind=CLAUDE_PROJECT_SLASH_SOURCE,
            remote_session_id=session_state.bridge_session_id,
            session_url=session_state.session_url,
            provider_session_id=f"{CLAUDE_CODE_SESSION_ID_PREFIX}{session_id}",
            proof_channel=SESSION_STATE_PROOF_CHANNEL,
            proof_source=str(session_state.path),
            proof_observed_at_utc=session_state.updated_at_utc,
            physical_confirmation_method=SESSION_STATE_PHYSICAL_METHOD,
        )
    physical = latest_matching_builtin_remote_control_proof(
        events=events,
        session_id=session_id,
        before_event=event,
        now_utc=now_utc,
        max_age_seconds=max_age_seconds,
    )
    if physical is not None:
        return RemoteControlSourceProof(
            proven_source_kind=CLAUDE_PROJECT_SLASH_SOURCE,
            session_url=remote_control_session_url(physical),
            provider_session_id=f"{CLAUDE_CODE_SESSION_ID_PREFIX}{session_id}",
            proof_channel="claude_agent_mind_remote_control_bridge_status",
            proof_source=str(path),
            proof_observed_at_utc=_text(physical.get("timestamp")),
        )
    return RemoteControlSourceProof(
        proven_source_kind=CLAUDE_PROJECT_SLASH_SOURCE,
        provider_session_id=f"{CLAUDE_CODE_SESSION_ID_PREFIX}{session_id}",
        proof_channel="claude_agent_mind_attribution",
        proof_source=str(path),
        proof_observed_at_utc=_text(event.get("timestamp")),
    )


def _latest_matching_typed_remote_control_event(
    *,
    events: list[Mapping[str, object]],
    command_entrypoint: str,
    launcher_source: str,
    now_utc: str,
    max_age_seconds: int,
) -> Mapping[str, object] | None:
    now = parse_utc_timestamp(now_utc)
    if now is None:
        return None
    for raw in reversed(events):
        if not _is_typed_remote_control_event(raw):
            continue
        timestamp = parse_utc_timestamp(raw.get("timestamp"))
        if timestamp is None:
            continue
        if max((now - timestamp).total_seconds(), 0.0) > max_age_seconds:
            continue
        if _is_typed_remote_control_attribution(raw):
            return raw
        if _is_typed_remote_control_slash_metadata(raw):
            return raw
        command = _bash_command(raw)
        if _command_matches(
            command,
            command_entrypoint=command_entrypoint,
            launcher_source=launcher_source,
        ):
            return raw
    return None


def _resolve_claude_session(
    projection: Mapping[str, object],
) -> tuple[Path | None, str]:
    session_id = _text(projection.get("session_id"))
    session_path = _text(projection.get("session_path"))
    if session_path:
        path = Path(session_path)
        if not session_id:
            session_id = session_id_from_path(path, provider=PROVIDER_CLAUDE)
        return path, session_id
    path = discover_latest_session(PROVIDER_CLAUDE)
    if path is None:
        return None, ""
    return path, session_id_from_path(path, provider=PROVIDER_CLAUDE)


def _is_typed_remote_control_event(raw: Mapping[str, object]) -> bool:
    if _is_typed_remote_control_attribution(raw):
        return True
    return _is_typed_remote_control_slash_metadata(raw)


def _is_typed_remote_control_attribution(raw: Mapping[str, object]) -> bool:
    return _text(raw.get("attributionSkill")) == TYPED_REMOTE_CONTROL_ATTRIBUTION


def _is_typed_remote_control_slash_metadata(raw: Mapping[str, object]) -> bool:
    content = _text(raw.get("content"))
    return (
        _text(raw.get("type")) == "system"
        and _text(raw.get("subtype")) == "local_command"
        and "<command-name>/typed-remote-control</command-name>" in content
    )


def _bash_command(raw: Mapping[str, object]) -> str:
    message = raw.get("message")
    if not isinstance(message, Mapping):
        return ""
    content = message.get("content")
    if not isinstance(content, list):
        return ""
    for item in content:
        if not isinstance(item, Mapping):
            continue
        if item.get("type") != "tool_use" or item.get("name") != "Bash":
            continue
        input_payload = item.get("input")
        if isinstance(input_payload, Mapping):
            return _text(input_payload.get("command"))
    return ""


def _command_matches(
    command: str,
    *,
    command_entrypoint: str,
    launcher_source: str,
) -> bool:
    return (
        "dev/scripts/devctl.py remote-control enter" in command
        and f"--entrypoint {command_entrypoint}" in command
        and f"--launcher-source {launcher_source}" in command
    )


def _claude_process_attested(environ: Mapping[str, str]) -> bool:
    return (
        _text(environ.get("CLAUDECODE")) == "1"
        and _text(environ.get("AI_AGENT")).startswith("claude-code/")
        and bool(_text(environ.get("CLAUDE_CODE_ENTRYPOINT")))
    )


def _field(value: object, name: str) -> str:
    if value is None:
        return ""
    return _text(getattr(value, name, ""))


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "CLAUDE_CODE_SESSION_ID_PREFIX",
    "CLAUDE_BUILTIN_SLASH_SOURCE",
    "CLAUDE_PROJECT_SLASH_SOURCE",
    "DEFAULT_SOURCE_PROOF_MAX_AGE_SECONDS",
    "RemoteControlSourceProof",
    "TYPED_REMOTE_CONTROL_ATTRIBUTION",
    "hook_prompt_action",
    "resolve_builtin_source_proof_from_hook_payload",
    "resolve_lifecycle_source_proof",
    "resolve_lifecycle_source_proof_from_projection",
]
