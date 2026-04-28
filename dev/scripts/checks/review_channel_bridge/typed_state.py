"""Typed bridge metadata validation for the review-channel bridge guard."""

from __future__ import annotations

import re
from datetime import timedelta
from pathlib import Path

from dev.scripts.devctl.review_channel.ack_freshness_authority import (
    is_implementer_ack_current,
)
from dev.scripts.devctl.review_channel.handoff_constants import (
    DEFAULT_CODEX_POLL_STALE_AFTER_SECONDS,
)
from dev.scripts.devctl.review_channel.peer_liveness import (
    ReviewerMode,
    reviewer_mode_is_active,
)
from dev.scripts.devctl.runtime.review_state_locator import load_current_review_state

UTC_TIMESTAMP_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?Z$"
)
WORKTREE_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
MAX_POLL_AGE_MINUTES = DEFAULT_CODEX_POLL_STALE_AFTER_SECONDS // 60


def extract_bridge_compatibility_metadata(text: str) -> dict[str, str]:
    """Return compatibility-only bridge metadata with no freshness authority."""
    metadata: dict[str, str] = {}
    for line in text.splitlines():
        trimmed = line.strip().lstrip("-").strip()
        if trimmed.startswith("Reviewer mode:"):
            metadata["reviewer_mode"] = _strip_backticks(trimmed.split(":", 1)[1])
        elif trimmed.startswith("Last non-audit worktree hash:"):
            metadata["last_worktree_hash"] = _strip_backticks(trimmed.split(":", 1)[1])
    return metadata


def load_typed_review_state(repo_root: Path):
    """Load live typed ReviewState for bridge-active checks."""
    return load_current_review_state(
        repo_root,
        prefer_cached_projection=False,
    )


def validate_bridge_metadata(
    text: str,
    review_state,
    *,
    enforce_live_poll_freshness: bool,
) -> list[str]:
    """Validate bridge metadata using typed freshness and ACK authority."""
    metadata = extract_bridge_compatibility_metadata(text)
    errors: list[str] = []
    bridge = getattr(review_state, "bridge", None)
    current_session = getattr(review_state, "current_session", None)
    reviewer_mode = str(getattr(bridge, "reviewer_mode", "") or "").strip()
    if not reviewer_mode:
        reviewer_mode = metadata.get("reviewer_mode", "")
    valid_reviewer_modes = {mode.value for mode in ReviewerMode}

    if not reviewer_mode:
        errors.append(
            "Missing `Reviewer mode`; expected one of: "
            + ", ".join(sorted(valid_reviewer_modes))
            + "."
        )
    elif reviewer_mode not in valid_reviewer_modes:
        errors.append(
            "Invalid `Reviewer mode`; expected one of: "
            + ", ".join(sorted(valid_reviewer_modes))
            + f". Got `{reviewer_mode}`."
        )

    if bridge is None:
        errors.append(
            "Missing typed ReviewState bridge metadata; bridge-active checks "
            "require event-backed `last_codex_poll_utc` and freshness age."
        )
        return errors

    errors.extend(
        _typed_poll_errors(
            bridge=bridge,
            reviewer_mode=reviewer_mode,
            enforce_live_poll_freshness=enforce_live_poll_freshness,
        )
    )
    if current_session is None:
        errors.append(
            "Missing typed ReviewState current-session metadata; bridge-active "
            "checks require implementer ACK authority."
        )
    elif reviewer_mode_is_active(reviewer_mode) and not is_implementer_ack_current(
        current_session
    ):
        errors.append(
            "Typed implementer ACK is not current for the active instruction revision."
        )

    if not WORKTREE_HASH_PATTERN.fullmatch(metadata.get("last_worktree_hash", "")):
        errors.append(
            "Invalid `Last non-audit worktree hash`; expected a 64-character "
            "lowercase SHA-256 hex digest."
        )
    return errors


def _typed_poll_errors(
    *,
    bridge,
    reviewer_mode: str,
    enforce_live_poll_freshness: bool,
) -> list[str]:
    last_codex_poll = str(getattr(bridge, "last_codex_poll_utc", "") or "").strip()
    if not UTC_TIMESTAMP_PATTERN.fullmatch(last_codex_poll):
        return [
            "Invalid typed `last_codex_poll_utc`; expected ISO-8601 UTC like "
            "`2026-03-08T19:08:45Z` or `2026-03-08T19:08:45.123Z`."
        ]
    max_age = timedelta(minutes=MAX_POLL_AGE_MINUTES)
    poll_age = timedelta(
        seconds=int(getattr(bridge, "last_codex_poll_age_seconds", 0) or 0)
    )
    if poll_age < timedelta(0):
        return ["Typed `last_codex_poll_age_seconds` is negative."]
    if (
        poll_age > max_age
        and enforce_live_poll_freshness
        and reviewer_mode_is_active(reviewer_mode)
    ):
        return [
            "Typed `last_codex_poll_age_seconds` is stale; bridge-active "
            f"reviews must refresh within {MAX_POLL_AGE_MINUTES} minutes."
        ]
    return []


def _strip_backticks(text: str) -> str:
    return text.strip().strip("`").strip()


__all__ = [
    "extract_bridge_compatibility_metadata",
    "load_typed_review_state",
    "validate_bridge_metadata",
]
