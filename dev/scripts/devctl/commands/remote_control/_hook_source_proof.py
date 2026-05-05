"""Claude hook proof resolution for built-in remote-control prompts."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from pathlib import Path

from ._proof_types import (
    CLAUDE_BUILTIN_SLASH_SOURCE,
    CLAUDE_CODE_SESSION_ID_PREFIX,
    DEFAULT_SOURCE_PROOF_MAX_AGE_SECONDS,
    RemoteControlSourceProof,
)
from ._session_state_proof import (
    SESSION_STATE_PHYSICAL_METHOD,
    SESSION_STATE_PROOF_CHANNEL,
    resolve_live_session_state_bridge_proof,
)
from ._transcript_proof import (
    latest_fresh_builtin_remote_control_proof,
    read_jsonl_tail,
    remote_control_session_url,
)

USER_PROMPT_SUBMIT_EVENT = "UserPromptSubmit"
USER_PROMPT_EXPANSION_EVENT = "UserPromptExpansion"
REMOTE_CONTROL_PROMPT_RE = re.compile(r"^/(remote-control|rc)(\b|$)")
REMOTE_CONTROL_EXIT_PROMPT_RE = re.compile(
    r"^/(remote-control|rc)\s+(off|exit|stop|disconnect)\b"
)
REMOTE_CONTROL_COMMAND_NAMES = frozenset({"remote-control", "rc"})


def hook_prompt_action(payload: Mapping[str, object]) -> str:
    """Classify a Claude hook payload for built-in remote-control."""
    event_name = _text(payload.get("hook_event_name"))
    if event_name not in {USER_PROMPT_SUBMIT_EVENT, USER_PROMPT_EXPANSION_EVENT}:
        return "ignore"
    prompt = _text(payload.get("prompt"))
    if REMOTE_CONTROL_EXIT_PROMPT_RE.match(prompt):
        return "exit"
    command_name = _normal_command_name(payload)
    if event_name == USER_PROMPT_EXPANSION_EVENT and command_name:
        if _command_args_request_exit(payload):
            return "exit"
        return "enter"
    if REMOTE_CONTROL_PROMPT_RE.match(prompt):
        return "enter"
    return "ignore"


def resolve_builtin_source_proof_from_hook_payload(
    *,
    payload: Mapping[str, object],
    now_utc: str,
    max_age_seconds: int = DEFAULT_SOURCE_PROOF_MAX_AGE_SECONDS,
) -> RemoteControlSourceProof:
    """Resolve physical Claude remote-control proof from hook-owned input."""
    action = hook_prompt_action(payload)
    if action == "ignore":
        return RemoteControlSourceProof()
    session_id = _text(payload.get("session_id"))
    transcript_path = _text(payload.get("transcript_path"))
    hook_fields = _hook_proof_fields(
        payload=payload,
        action=action,
        observed_at_utc=now_utc,
    )
    if not session_id or not transcript_path:
        return RemoteControlSourceProof(
            proven_source_kind=CLAUDE_BUILTIN_SLASH_SOURCE,
            proof_channel="claude_hook",
            proof_observed_at_utc=now_utc,
            **hook_fields,
        )
    session_state = resolve_live_session_state_bridge_proof(
        session_id=session_id,
        now_utc=now_utc,
        expected_cwd=_text(payload.get("cwd")),
        max_age_seconds=max_age_seconds,
    )
    if session_state is not None:
        return RemoteControlSourceProof(
            proven_source_kind=CLAUDE_BUILTIN_SLASH_SOURCE,
            remote_session_id=session_state.bridge_session_id,
            session_url=session_state.session_url,
            provider_session_id=f"{CLAUDE_CODE_SESSION_ID_PREFIX}{session_id}",
            proof_channel=SESSION_STATE_PROOF_CHANNEL,
            proof_source=str(session_state.path),
            proof_observed_at_utc=session_state.updated_at_utc,
            physical_confirmation_method=SESSION_STATE_PHYSICAL_METHOD,
            **_hook_proof_fields(
                payload=payload,
                action=action,
                observed_at_utc=session_state.updated_at_utc,
            ),
        )
    path = Path(transcript_path)
    physical = latest_fresh_builtin_remote_control_proof(
        events=read_jsonl_tail(path),
        session_id=session_id,
        now_utc=now_utc,
        max_age_seconds=max_age_seconds,
    )
    if physical is not None:
        return RemoteControlSourceProof(
            proven_source_kind=CLAUDE_BUILTIN_SLASH_SOURCE,
            session_url=remote_control_session_url(physical),
            provider_session_id=f"{CLAUDE_CODE_SESSION_ID_PREFIX}{session_id}",
            proof_channel="claude_hook",
            proof_source=str(path),
            proof_observed_at_utc=_text(physical.get("timestamp")),
            physical_confirmation_method="claude_hook_transcript",
            **_hook_proof_fields(
                payload=payload,
                action=action,
                observed_at_utc=_text(physical.get("timestamp")),
            ),
        )
    return RemoteControlSourceProof(
        proven_source_kind=CLAUDE_BUILTIN_SLASH_SOURCE,
        provider_session_id=f"{CLAUDE_CODE_SESSION_ID_PREFIX}{session_id}",
        proof_channel="claude_hook",
        proof_source=str(path),
        proof_observed_at_utc=now_utc,
        **hook_fields,
    )


def hook_dedupe_key(
    *,
    payload: Mapping[str, object],
    action: str,
    observed_at_utc: str,
) -> str:
    """Stable key shared by UserPromptSubmit and UserPromptExpansion."""
    command_name = _normal_command_name(payload) or _prompt_command(payload)
    parts = (
        _text(payload.get("session_id")),
        _text(payload.get("transcript_path")),
        action,
        command_name,
        observed_at_utc,
    )
    raw = "\x1f".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _hook_proof_fields(
    *,
    payload: Mapping[str, object],
    action: str,
    observed_at_utc: str,
) -> dict[str, str]:
    fields: dict[str, str] = {}
    fields["hook_event_name"] = _text(payload.get("hook_event_name"))
    fields["hook_prompt"] = _text(payload.get("prompt"))
    fields["hook_command_name"] = _normal_command_name(payload)
    fields["hook_session_id"] = _text(payload.get("session_id"))
    fields["hook_transcript_path"] = _text(payload.get("transcript_path"))
    fields["hook_dedupe_key"] = hook_dedupe_key(
        payload=payload,
        action=action,
        observed_at_utc=observed_at_utc,
    )
    return fields


def _normal_command_name(payload: Mapping[str, object]) -> str:
    command_name = _text(payload.get("command_name")).lstrip("/")
    return command_name if command_name in REMOTE_CONTROL_COMMAND_NAMES else ""


def _prompt_command(payload: Mapping[str, object]) -> str:
    prompt = _text(payload.get("prompt"))
    match = REMOTE_CONTROL_PROMPT_RE.match(prompt)
    return match.group(1) if match else ""


def _command_args_request_exit(payload: Mapping[str, object]) -> bool:
    args = _text(payload.get("command_args"))
    first = args.split(maxsplit=1)[0] if args else ""
    return first in {"off", "exit", "stop", "disconnect"}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "USER_PROMPT_EXPANSION_EVENT",
    "USER_PROMPT_SUBMIT_EVENT",
    "hook_dedupe_key",
    "hook_prompt_action",
    "resolve_builtin_source_proof_from_hook_payload",
]
