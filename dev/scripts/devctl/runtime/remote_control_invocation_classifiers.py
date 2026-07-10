"""Closed enums and classifiers for remote-control invocation receipts."""

from __future__ import annotations


REMOTE_CONTROL_INVOCATION_ACTIONS: tuple[str, ...] = (
    "start",
    "enter",
    "heartbeat",
    "exit",
)
REMOTE_CONTROL_INVOCATION_STATE_CHANGES: tuple[str, ...] = (
    "preview",
    "created",
    "refreshed",
    "heartbeat_refreshed",
    "no_op",
    "detached",
    "already_detached",
    "launched_then_detached",
    "evidence_missing",
    "failed",
)
REMOTE_CONTROL_INVOCATION_SOURCE_KINDS: tuple[str, ...] = (
    "claude_builtin_slash",
    "claude_project_slash",
    "codex_project_slash",
    "direct_cli",
    "review_channel_attach",
    "unspecified",
)
DEFAULT_REMOTE_CONTROL_INVOCATION_REL = (
    "dev/state/remote_control/invocations.jsonl"
)


def classify_state_change(
    *,
    before_status: str,
    after_status: str,
    before_attachment_id: str,
    after_attachment_id: str,
    error_message: str = "",
) -> str:
    """Classify a lifecycle invocation's effect on the typed attachment."""
    if error_message:
        return "evidence_missing"
    before_clean = (before_status or "").strip().lower()
    after_clean = (after_status or "").strip().lower()
    if after_clean == "evidence_missing":
        return "evidence_missing"
    if after_clean == "failed":
        return "failed"
    if after_clean == "detached":
        if not before_clean and not before_attachment_id:
            return "already_detached"
        return "detached"
    if not before_clean and after_clean:
        return "created"
    if not before_attachment_id and after_attachment_id:
        return "created"
    if before_clean == after_clean and before_attachment_id == after_attachment_id:
        return "no_op"
    return "heartbeat_refreshed"


def resolve_invocation_origin(
    *,
    caller_supplied: str,
    proven_source_kind: str,
) -> str:
    """Resolve authoritative invocation origin from proven evidence only."""
    supplied = (caller_supplied or "").strip()
    proven = (proven_source_kind or "").strip() or "unspecified"
    if supplied and supplied == proven and proven != "unspecified":
        return supplied
    if proven != "unspecified":
        return proven
    return "direct_cli"


def classify_claimed_source_kind(
    *,
    entrypoint: str,
    launcher_source: str,
    invocation_origin: str = "",
) -> str:
    """Classify the caller's self-attested remote-control invocation source."""
    entry = (entrypoint or "").strip()
    launcher = (launcher_source or "").strip().lower()
    origin = (invocation_origin or "").strip().lower()
    if origin in {
        "claude_builtin_slash",
        "claude_project_slash",
        "codex_project_slash",
    }:
        return origin
    if origin == "review_channel_attach":
        return origin
    if origin == "direct_cli":
        return "direct_cli"
    if launcher == "claude_builtin_slash":
        return "claude_builtin_slash"
    if entry.startswith("/project:") and launcher == "claude_project_slash":
        return "claude_project_slash"
    if entry.startswith("/project:") and launcher == "codex_project_slash":
        return "codex_project_slash"
    if launcher == "review_channel_attach":
        return "review_channel_attach"
    if launcher in {"slash", "bridge-loop-alias"} and entry.startswith("/project:"):
        return "claude_project_slash"
    if launcher or entry:
        return "direct_cli"
    return "unspecified"


__all__ = [
    "DEFAULT_REMOTE_CONTROL_INVOCATION_REL",
    "REMOTE_CONTROL_INVOCATION_ACTIONS",
    "REMOTE_CONTROL_INVOCATION_SOURCE_KINDS",
    "REMOTE_CONTROL_INVOCATION_STATE_CHANGES",
    "classify_claimed_source_kind",
    "classify_state_change",
    "resolve_invocation_origin",
]
