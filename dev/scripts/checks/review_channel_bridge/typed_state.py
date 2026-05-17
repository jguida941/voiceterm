"""Typed bridge metadata validation for the review-channel bridge guard."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
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
_ROLE_PROGRESS_PROOF_STATES = frozenset({"satisfied", "verified"})
_ROLE_PROGRESS_LOOP_STATES = frozenset(
    {"blocked", "polling", "working", "ready", "waiting", "running"}
)
_ROLE_PROGRESS_DECISIONS = frozenset(
    {"pivot_to_packet", "run_next_command", "report_blocker", "wait_for_review"}
)
_ROLE_PROGRESS_TARGET_FIELDS = (
    "active_packet_id",
    "attention_packet_id",
    "executing_packet_id",
    "target_ref",
)


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
    role_packet_progress = role_neutral_packet_progress_current(
        review_state,
        target_roles=("implementer", "coder"),
    )
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
    if current_session is None and not role_packet_progress:
        errors.append(
            "Missing typed ReviewState current-session metadata; bridge-active "
            "checks require typed role/session progress authority."
        )
    elif (
        current_session is not None
        and reviewer_mode_is_active(reviewer_mode)
        and not is_implementer_ack_current(current_session)
        and not role_packet_progress
    ):
        errors.append(
            "Assigned-role progress is not current for the active instruction "
            "revision; no typed ACK, packet advance, or typed blocker is recorded."
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


def role_neutral_packet_progress_current(
    review_state,
    *,
    target_roles: Iterable[str] = (),
) -> bool:
    """Return whether typed role/session state proves current packet progress.

    Legacy bridge text still names Claude/Codex for compatibility, but the
    authority predicate is role-neutral: any actor can satisfy it when typed
    state shows that actor is assigned to the role and has advanced or blocked
    the packet through the agent-loop proof chain.
    """
    normalized_roles = {
        str(role or "").strip().lower() for role in target_roles if str(role or "").strip()
    }
    for row in _agent_loop_decision_rows(review_state):
        actor_id = _row_text(row, "actor_id")
        actor_role = _row_text(row, "actor_role").lower()
        session_id = _row_text(row, "session_id")
        if not actor_id or not actor_role or not session_id:
            continue
        if normalized_roles and actor_role not in normalized_roles:
            continue
        if _row_text(row, "proof_state").lower() not in _ROLE_PROGRESS_PROOF_STATES:
            continue
        if not _row_has_packet_target(row):
            continue
        loop_state = _row_text(row, "loop_state").lower()
        decision = _row_text(row, "decision").lower()
        required_action = _row_text(row, "required_action")
        reason = _row_text(row, "reason") or _row_text(row, "top_blocker")
        if (
            loop_state in _ROLE_PROGRESS_LOOP_STATES
            or decision in _ROLE_PROGRESS_DECISIONS
            or required_action
            or reason
        ):
            return True
    return False


def _agent_loop_decision_rows(review_state) -> list[Mapping[str, object]]:
    if review_state is None:
        return []
    rows = getattr(review_state, "agent_loop_decisions", ())
    if isinstance(rows, Mapping):
        values = rows.get("decisions") or rows.get("rows") or rows.values()
    else:
        values = rows
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes)):
        return []
    return [row for row in values if isinstance(row, Mapping)]


def _row_has_packet_target(row: Mapping[str, object]) -> bool:
    target_kind = _row_text(row, "target_kind").lower()
    if target_kind and target_kind != "packet":
        return False
    return any(_row_text(row, field) for field in _ROLE_PROGRESS_TARGET_FIELDS)


def _row_text(row: Mapping[str, object], field: str) -> str:
    return str(row.get(field) or "").strip()


__all__ = [
    "extract_bridge_compatibility_metadata",
    "load_typed_review_state",
    "role_neutral_packet_progress_current",
    "validate_bridge_metadata",
]
