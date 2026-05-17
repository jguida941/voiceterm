"""Poll-status parsing helpers for bridge validation."""

from __future__ import annotations

import re

from .peer_liveness import ReviewerMode, normalize_reviewer_mode

_POLL_STATUS_REVIEWER_MODE_PATTERNS = (
    re.compile(
        r"(?i)\breviewer mode(?:\s+is(?:\s+\w+)?(?:\s+to)?|\s*:)\s*`(?P<mode>[^`]+)`"
    ),
    re.compile(r"\(mode:\s*(?P<mode>[a-z_]+)\b"),
)
_REVIEWER_STATE_WRITE_RE = re.compile(
    r"(?i)^-\s*Reviewer\s+"
    r"(?P<action>heartbeat|checkpoint)\s+"
    r"(?:(?:refreshed|updated)\s+through\s+repo-owned\s+tooling|"
    r"preserved\s+reviewed\s+baseline\s+through\s+repo-owned\s+tooling)\s+"
    r"\(mode:\s*(?P<mode>[a-z_]+);\s*reason:\s*(?P<reason>[^;)\n]+)"
)
_AUTO_REFRESH_POLL_STATUS_RE = re.compile(
    r"(?i)^-\s*Auto-refreshed reviewer heartbeat:\s*`[^`]+`\s*"
    r"\(reason:\s*(?P<reason>[^;)\n]+)"
)
_AUTOMATION_ONLY_REVIEWER_REASONS = frozenset(
    {"ensure", "ensure-follow", "reviewer-follow"}
)


def extract_poll_status_reviewer_modes(poll_status: str) -> tuple[str, ...]:
    """Return normalized reviewer modes explicitly asserted inside Poll Status."""
    seen: list[str] = []
    valid_modes = {mode.value for mode in ReviewerMode}
    for pattern in _POLL_STATUS_REVIEWER_MODE_PATTERNS:
        for match in pattern.finditer(poll_status):
            normalized = normalize_reviewer_mode(match.group("mode"))
            if normalized in valid_modes and normalized not in seen:
                seen.append(normalized)
    return tuple(seen)


def extract_poll_status_write_context(poll_status: str) -> tuple[str, str]:
    """Return the latest repo-owned reviewer write action/reason from Poll Status."""
    text = (poll_status or "").strip()
    if not text:
        return "", ""
    match = _REVIEWER_STATE_WRITE_RE.match(text)
    if match is not None:
        return (
            f"reviewer-{match.group('action').strip().lower()}",
            match.group("reason").strip().lower(),
        )
    match = _AUTO_REFRESH_POLL_STATUS_RE.match(text)
    if match is not None:
        return "auto-refresh", match.group("reason").strip().lower()
    return "", ""


def poll_status_is_automation_only_refresh(poll_status: str) -> bool:
    """Return True when Poll Status shows only tooling-side heartbeat refresh."""
    action, reason = extract_poll_status_write_context(poll_status)
    if action == "auto-refresh":
        return True
    return action == "reviewer-heartbeat" and reason in _AUTOMATION_ONLY_REVIEWER_REASONS
