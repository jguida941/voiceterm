"""Shared source-proof types for remote-control lifecycle code."""

from __future__ import annotations

from dataclasses import asdict, dataclass

CLAUDE_BUILTIN_SLASH_SOURCE = "claude_builtin_slash"
CLAUDE_PROJECT_SLASH_SOURCE = "claude_project_slash"
CLAUDE_CODE_SESSION_ID_PREFIX = "claude-code:"
DEFAULT_SOURCE_PROOF_MAX_AGE_SECONDS = 300
TYPED_REMOTE_CONTROL_ATTRIBUTION = "typed-remote-control"


@dataclass(frozen=True, slots=True)
class RemoteControlSourceProof:
    """Evidence that a lifecycle call came from a provider-owned surface."""

    proven_source_kind: str = "unspecified"
    remote_session_id: str = ""
    session_url: str = ""
    provider_session_id: str = ""
    proof_channel: str = ""
    proof_source: str = ""
    proof_observed_at_utc: str = ""
    physical_confirmation_method: str = "none"
    hook_event_name: str = ""
    hook_prompt: str = ""
    hook_command_name: str = ""
    hook_session_id: str = ""
    hook_transcript_path: str = ""
    hook_dedupe_key: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


__all__ = [
    "CLAUDE_BUILTIN_SLASH_SOURCE",
    "CLAUDE_CODE_SESSION_ID_PREFIX",
    "CLAUDE_PROJECT_SLASH_SOURCE",
    "DEFAULT_SOURCE_PROOF_MAX_AGE_SECONDS",
    "RemoteControlSourceProof",
    "TYPED_REMOTE_CONTROL_ATTRIBUTION",
]
