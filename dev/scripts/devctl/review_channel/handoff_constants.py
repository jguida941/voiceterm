"""Constants and small helpers for bridge handoff validation."""

from __future__ import annotations

import re

from .peer_liveness import (
    CODEX_POLL_DUE_AFTER_SECONDS,
    CODEX_POLL_STALE_AFTER_SECONDS,
)

MARKDOWN_ITEM_RE = re.compile(r"^(?:[-*+]\s+|\d+\.\s+)(?P<value>.+)$")
BRIDGE_METADATA_PATTERNS = {
    "last_codex_poll_utc": re.compile(r"^- Last Codex poll:\s*`(?P<value>.+?)`\s*$"),
    "last_codex_poll_local": re.compile(
        r"^- Last Codex poll \(Local America/New_York\):\s*`(?P<value>.+?)`\s*$"
    ),
    "last_non_audit_worktree_hash": re.compile(
        r"^- Last non-audit worktree hash:\s*`(?P<value>.+?)`\s*$"
    ),
}
TRACKED_BRIDGE_SECTIONS = (
    "Poll Status",
    "Current Verdict",
    "Open Findings",
    "Current Instruction For Claude",
    "Claude Status",
    "Claude Questions",
    "Claude Ack",
    "Last Reviewed Scope",
)
ROLLOVER_ACK_PREFIX = {
    "codex": "Codex rollover ack:",
    "claude": "Claude rollover ack:",
}
ROLLOVER_ACK_SECTION = {
    "codex": "Poll Status",
    "claude": "Claude Ack",
}
BRIDGE_LIVENESS_KEYS = (
    "overall_state",
    "codex_poll_state",
    "last_codex_poll_utc",
    "last_codex_poll_age_seconds",
    "last_reviewed_scope_present",
    "next_action_present",
    "open_findings_present",
    "claude_status_present",
    "claude_ack_present",
)
DEFAULT_CODEX_POLL_DUE_AFTER_SECONDS = CODEX_POLL_DUE_AFTER_SECONDS
DEFAULT_CODEX_POLL_STALE_AFTER_SECONDS = CODEX_POLL_STALE_AFTER_SECONDS
IDLE_NEXT_ACTION_MARKERS = (
    "all green so far",
    "no next action",
    "n/a",
    "none recorded",
    "idle",
    "placeholder",
)
PLACEHOLDER_STATUS_MARKERS = (
    "none",
    "n/a",
    "none recorded",
    "placeholder",
    "not started",
    "pending",
)
IDLE_FINDING_MARKERS = (
    "(none)",
    "none",
    "no blockers",
    "all clear",
    "all green",
    "resolved",
)
RESOLVED_VERDICT_MARKERS = (
    "accepted",
    "all green",
    "reviewer-accepted",
    "resolved",
)
_RESOLVED_ECHO_RE = re.compile(
    r"\b(?:accepted|all\s+green|reviewer[- ]accepted|resolved)\b",
    re.IGNORECASE,
)


def _is_substantive_text(text: str | None) -> bool:
    """Return True only if *text* has content beyond placeholder markers."""
    if not text:
        return False
    stripped = text.strip().lstrip("-").strip().lower()
    if not stripped:
        return False
    return not any(
        stripped == marker for marker in PLACEHOLDER_STATUS_MARKERS
    )
