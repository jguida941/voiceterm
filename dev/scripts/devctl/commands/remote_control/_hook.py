"""Claude hook input handling for remote-control lifecycle state."""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ...time_utils import utc_timestamp
from ._hook_source_proof import (
    hook_prompt_action,
    resolve_builtin_source_proof_from_hook_payload,
)
from ._proof_types import RemoteControlSourceProof


@dataclass(frozen=True, slots=True)
class HookReport:
    command: str
    action: str
    ok: bool
    observed_at_utc: str
    hook_event_name: str
    hook_prompt_action: str
    hook_prompt_matched: bool
    hook_prompt: str = ""
    hook_command_name: str = ""
    hook_session_id: str = ""
    hook_transcript_path: str = ""
    hook_dedupe_key: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def load_hook_payload(args: Any) -> Mapping[str, object]:
    """Read a Claude hook JSON payload from ``--hook-input-file`` or stdin."""
    path_value = str(getattr(args, "hook_input_file", "") or "").strip()
    try:
        if path_value:
            raw = Path(path_value).read_text(encoding="utf-8")
        else:
            raw = sys.stdin.read()
    except OSError:
        return {}
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, Mapping) else {}


def wait_for_hook_source_proof(
    payload: Mapping[str, object],
    *,
    poll_seconds: float,
    now_utc: str | None = None,
) -> RemoteControlSourceProof:
    """Poll the Claude transcript for the session URL created by the slash."""
    action = hook_prompt_action(payload)
    if action == "ignore":
        return RemoteControlSourceProof()
    deadline = time.monotonic() + max(0.0, poll_seconds)
    while True:
        proof = resolve_builtin_source_proof_from_hook_payload(
            payload=payload,
            now_utc=now_utc or utc_timestamp(),
        )
        if action == "exit" or proof.session_url or time.monotonic() >= deadline:
            return proof
        time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))


def hook_report(
    *,
    payload: Mapping[str, object],
    action: str,
) -> dict[str, object]:
    """Build a small report for hook calls that do not mutate state."""
    return HookReport(
        command="remote-control",
        action="hook",
        ok=True,
        observed_at_utc=utc_timestamp(),
        hook_event_name=str(payload.get("hook_event_name") or "").strip(),
        hook_prompt_action=action,
        hook_prompt_matched=action != "ignore",
        hook_prompt=str(payload.get("prompt") or "").strip(),
        hook_command_name=str(payload.get("command_name") or "").strip(),
        hook_session_id=str(payload.get("session_id") or "").strip(),
        hook_transcript_path=str(payload.get("transcript_path") or "").strip(),
        hook_dedupe_key="",
    ).to_dict()


__all__ = [
    "hook_report",
    "load_hook_payload",
    "wait_for_hook_source_proof",
]
