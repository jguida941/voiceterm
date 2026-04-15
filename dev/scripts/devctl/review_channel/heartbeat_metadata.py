"""Metadata helpers for bridge heartbeat refreshes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from .bridge_validation import extract_poll_status_reviewer_modes
from .poll_status import AUTO_REFRESH_PREFIX, rewrite_poll_status as _rewrite_poll_status

LAST_CODEX_POLL_RE = re.compile(r"(?m)^- Last Codex poll:\s*`.*?`\s*$")
LAST_CODEX_POLL_LOCAL_RE = re.compile(
    r"(?m)^- Last Codex poll \(Local [^)]+\):\s*`.*?`\s*$"
)
LAST_WORKTREE_HASH_RE = re.compile(
    r"(?m)^- Last non-audit worktree hash:\s*`.*?`\s*$"
)
CURRENT_INSTRUCTION_REVISION_RE = re.compile(
    r"(?m)^- Current instruction revision:\s*`.*?`\s*$"
)
LAST_CHECKPOINT_ACTION_RE = re.compile(
    r"(?m)^- Last checkpoint action:\s*`.*?`\s*$"
)
HEAD_AT_PUSH_TIME_RE = re.compile(
    r"(?m)^- Head at push time:\s*`.*?`\s*$"
)
_REPO_OWNED_POLL_STATUS_PREFIXES = (
    AUTO_REFRESH_PREFIX,
    "- Reviewer checkpoint updated through repo-owned tooling",
    "- Reviewer heartbeat refreshed through repo-owned tooling",
    "- Reviewer state:",
    "- Reviewer mode ",
    "- Reviewer conductor ",
)
_TIMESTAMPED_POLL_STATUS_RE = re.compile(
    r"^-\s+`?\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z`?(?:\b|[/:])"
)
_HISTORICAL_POLL_STATUS_PHRASES = (
    "bridge attention no longer reflects an ack wait",
    "live bridge status now matches the reviewed tree hash",
    "structural authority docs are green on the current tree",
)


@dataclass(frozen=True, slots=True)
class HeartbeatMetadataInputs:
    bridge_text: str
    last_codex_poll_utc: str
    last_codex_poll_local: str
    tz_label: str
    reason: str
    observed_hash: str
    reviewed_hash: str


def rewrite_heartbeat_metadata(
    *,
    inputs: HeartbeatMetadataInputs,
) -> str:
    """Rewrite the heartbeat timestamp lines and the repo-owned poll note."""
    updated_text = replace_or_insert_metadata_line(
        inputs.bridge_text,
        pattern=LAST_CODEX_POLL_RE,
        replacement=f"- Last Codex poll: `{inputs.last_codex_poll_utc}`",
    )
    updated_text = replace_or_insert_metadata_line(
        updated_text,
        pattern=LAST_CODEX_POLL_LOCAL_RE,
        replacement=(
            f"- Last Codex poll (Local {inputs.tz_label}): "
            f"`{inputs.last_codex_poll_local}`"
        ),
    )
    return _rewrite_poll_status(
        updated_text,
        note=(
            f"{AUTO_REFRESH_PREFIX} `{inputs.last_codex_poll_utc}` "
            f"(reason: {inputs.reason}; observed-tree: {inputs.observed_hash[:12]}; "
            f"reviewed-tree: {inputs.reviewed_hash[:12]})."
        ),
    )


def replace_or_insert_metadata_line(
    text: str,
    *,
    pattern: re.Pattern[str],
    replacement: str,
) -> str:
    """Replace a metadata line or insert it before the protocol block."""
    updated, count = pattern.subn(replacement, text, count=1)
    if count == 1:
        return updated
    marker = "\n## Protocol\n"
    if marker not in text:
        raise ValueError("Unable to locate the markdown-bridge metadata block.")
    return text.replace(marker, f"\n{replacement}{marker}", 1)


def should_strip_poll_status_line(line: str) -> bool:
    """Return whether a bridge poll-status line is repo-owned/stale noise."""
    stripped = line.strip()
    if any(
        stripped.startswith(prefix) for prefix in _REPO_OWNED_POLL_STATUS_PREFIXES
    ):
        return True
    if extract_poll_status_reviewer_modes(stripped):
        return True
    if _TIMESTAMPED_POLL_STATUS_RE.match(stripped):
        return True
    lowered = stripped.lower()
    return any(phrase in lowered for phrase in _HISTORICAL_POLL_STATUS_PHRASES)


def format_local_timestamp(timestamp_utc: datetime) -> str:
    """Render a UTC timestamp in the repo-configured display timezone."""
    from ..repo_packs import active_path_config

    tz_name = active_path_config().display_timezone
    local = timestamp_utc.astimezone(ZoneInfo(tz_name))
    return local.strftime("%Y-%m-%d %H:%M:%S %Z")
