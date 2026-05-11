"""Canonical reviewer operating-mode contract."""

from __future__ import annotations

from collections.abc import Mapping

from .enum_compat import StrEnum


class ReviewerMode(StrEnum):
    """Top-level reviewer operating modes for runtime authority decisions."""

    ACTIVE_DUAL_AGENT = "active_dual_agent"
    SINGLE_AGENT = "single_agent"
    TOOLS_ONLY = "tools_only"
    PAUSED = "paused"
    OFFLINE = "offline"


REVIEWER_MODE_CLI_CHOICES = tuple(mode.value for mode in ReviewerMode)
"""Allowed CLI values for reviewer-mode arguments."""

ACTIVE_REVIEWER_MODES = frozenset({ReviewerMode.ACTIVE_DUAL_AGENT})
INACTIVE_REVIEWER_MODES = frozenset(
    {
        ReviewerMode.SINGLE_AGENT,
        ReviewerMode.TOOLS_ONLY,
        ReviewerMode.PAUSED,
        ReviewerMode.OFFLINE,
    }
)


def normalize_reviewer_mode(
    value: object,
    *,
    default: ReviewerMode = ReviewerMode.ACTIVE_DUAL_AGENT,
) -> ReviewerMode:
    """Normalize text into one canonical reviewer mode enum."""
    raw = str(value or "").strip().lower()
    for mode in ReviewerMode:
        if raw == mode.value:
            return mode
    return default


def normalize_reviewer_mode_value(
    value: object,
    *,
    default: ReviewerMode = ReviewerMode.TOOLS_ONLY,
) -> str:
    """Normalize text into a reviewer mode value string."""
    return normalize_reviewer_mode(value, default=default).value


def resolve_reviewer_mode(
    *values: object,
    default: ReviewerMode = ReviewerMode.TOOLS_ONLY,
) -> str:
    """Resolve reviewer mode from ordered values and fail closed."""
    for value in values:
        raw = str(value or "").strip()
        if raw:
            return normalize_reviewer_mode_value(raw, default=default)
    return default.value


def authority_reviewer_mode(
    reviewer_mode: object,
    effective_reviewer_mode: object = "",
    *,
    default: ReviewerMode = ReviewerMode.TOOLS_ONLY,
) -> str:
    """Return the reviewer mode that typed authority consumers should trust."""
    mode = normalize_reviewer_mode_value(reviewer_mode, default=default)
    if str(effective_reviewer_mode or "").strip():
        return normalize_reviewer_mode_value(effective_reviewer_mode, default=default)
    return mode


def resolve_reported_reviewer_mode(source: Mapping[str, object] | None) -> str:
    """Resolve the declared reviewer mode without inventing active dual-agent state."""
    if source is None:
        return ReviewerMode.TOOLS_ONLY.value
    raw_mode = str(source.get("reviewer_mode") or "").strip()
    if raw_mode:
        return normalize_reviewer_mode(raw_mode).value
    raw_mode = str(source.get("effective_reviewer_mode") or "").strip()
    if raw_mode:
        return normalize_reviewer_mode(raw_mode).value
    return ReviewerMode.TOOLS_ONLY.value


def reviewer_mode_is_active(value: object) -> bool:
    """Return True only when the runtime mode is actively dual-agent."""
    return normalize_reviewer_mode(value) in ACTIVE_REVIEWER_MODES


def reviewer_mode_is_single_agent(value: object) -> bool:
    """Return True when the runtime mode is single-agent (local takeover authorized)."""
    return normalize_reviewer_mode(value) is ReviewerMode.SINGLE_AGENT


def reviewer_mode_allows_implementer(value: object) -> bool:
    """Return True when an implementer may own bounded implementation work."""
    return normalize_reviewer_mode(value) is ReviewerMode.ACTIVE_DUAL_AGENT


def reviewer_mode_allows_reviewer_mutation(value: object) -> bool:
    """Return True when the reviewer may mutate without an explicit takeover."""
    return normalize_reviewer_mode(value) is ReviewerMode.SINGLE_AGENT
