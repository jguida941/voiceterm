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
    "reviewer_mode": re.compile(r"^- Reviewer mode:\s*`(?P<value>.+?)`\s*$"),
    "last_non_audit_worktree_hash": re.compile(
        r"^- Last non-audit worktree hash:\s*`(?P<value>.+?)`\s*$"
    ),
    "current_instruction_revision": re.compile(
        r"^- Current instruction revision:\s*`(?P<value>.+?)`\s*$"
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
# Rollover ACK contract: only providers that own bridge sections participate.
# Cursor is intentionally excluded because it does not own a dedicated bridge
# section (no "Cursor Status" / "Cursor Ack" in bridge.md). Cursor lanes
# are present in the event-backed queue, projection roster, and runtime state,
# but rollover ACK is a bridge-section-ownership protocol.
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
    "reviewer_mode",
    "codex_poll_state",
    "reviewer_freshness",
    "last_codex_poll_utc",
    "last_codex_poll_age_seconds",
    "last_reviewed_scope_present",
    "next_action_present",
    "open_findings_present",
    "claude_status_present",
    "claude_ack_present",
    "claude_ack_current",
    "current_instruction_revision",
    "claude_ack_revision",
    "implementer_completion_stall",
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
GENERIC_NEXT_ACTION_MARKERS = (
    "next unchecked",
    "continue checklist",
    "continue the next",
    "continue next",
    "start the next",
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
SUSPICIOUS_BRIDGE_LINE_PATTERNS = (
    re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"),
    re.compile(r"(?i)\bplease run /login\b"),
    re.compile(r"(?i)\bnot logged in\b"),
    re.compile(r"(?i)\bcommand not found\b"),
    re.compile(r"(?i)^usage:\s"),
    re.compile(r"(?i)^traceback \(most recent call last\):"),
    re.compile(r"(?i)\binvalid choice:\b"),
    re.compile(r"(?i)^zsh:\d*:"),
    re.compile(r"(?i)^bash:\s"),
    re.compile(r"(?i)^test .+\.\.\. ok$"),
    re.compile(r"(?i)^running \d+ tests$"),
    re.compile(r"(?i)^test result:"),
    re.compile(r"(?i)^compiling "),
    re.compile(r"(?i)^finished "),
    re.compile(r"(?i)^doc-tests "),
    re.compile(r"(?i)^\s*running tests/"),
    re.compile(r"(?i)^\[process-sweep-post\]"),
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


def find_suspicious_bridge_text_lines(text: str | None) -> tuple[str, ...]:
    """Return suspicious terminal/status lines that should not become bridge authority."""
    if not text:
        return ()
    hits: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        match = MARKDOWN_ITEM_RE.match(stripped)
        candidate = match.group("value").strip() if match is not None else stripped
        if any(pattern.search(candidate) for pattern in SUSPICIOUS_BRIDGE_LINE_PATTERNS):
            if candidate not in hits:
                hits.append(candidate)
    return tuple(hits)
