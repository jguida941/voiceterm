"""Reviewer-owned tandem-consistency checks."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from dev.scripts.devctl.review_channel.heartbeat import (
    NON_AUDIT_HASH_EXCLUDED_PREFIXES,
    compute_non_audit_worktree_hash,
)
from dev.scripts.devctl.review_channel.peer_liveness import (
    CODEX_POLL_DUE_AFTER_SECONDS,
    CODEX_POLL_STALE_AFTER_SECONDS,
    normalize_reviewer_mode,
    reviewer_mode_is_active,
)
from dev.scripts.devctl.runtime.role_profile import TandemRole

from .support import (
    current_utc,
    extract_metadata_value,
    make_result,
    skip_live_freshness,
)

_BRIDGE_EXCLUDED_REL_PATHS = ("code_audit.md",)
_TANDEM_GUARD_STALE_THRESHOLD = CODEX_POLL_STALE_AFTER_SECONDS + 300


def check_reviewer_freshness(bridge_text: str) -> dict[str, object]:
    """Verify the reviewer heartbeat is within the freshness window."""
    _CK, _R = "reviewer_freshness", TandemRole.REVIEWER
    reviewer_mode = normalize_reviewer_mode(
        extract_metadata_value(bridge_text, "Reviewer mode:")
    )
    if not reviewer_mode_is_active(reviewer_mode):
        return make_result(
            _CK,
            _R,
            True,
            f"Reviewer mode is `{reviewer_mode}`; live reviewer freshness is not required.",
            reviewer_mode=reviewer_mode,
            status="inactive",
        )
    last_poll = extract_metadata_value(bridge_text, "Last Codex poll:")
    if not last_poll:
        return make_result(_CK, _R, False, "No reviewer heartbeat timestamp found in bridge.")
    try:
        poll_time = datetime.strptime(last_poll, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return make_result(_CK, _R, False, f"Invalid reviewer heartbeat timestamp: {last_poll}")
    age = int((current_utc() - poll_time).total_seconds())
    if age < 0:
        return make_result(_CK, _R, False, "Reviewer heartbeat is in the future.")
    if age > _TANDEM_GUARD_STALE_THRESHOLD and not skip_live_freshness():
        return make_result(
            _CK,
            _R,
            False,
            f"Reviewer heartbeat is stale ({age}s, threshold {_TANDEM_GUARD_STALE_THRESHOLD}s).",
            age_seconds=age,
        )
    status = "poll_due" if age > CODEX_POLL_DUE_AFTER_SECONDS else "fresh"
    return make_result(
        _CK,
        _R,
        True,
        f"Reviewer heartbeat age: {age}s ({status}).",
        age_seconds=age,
        status=status,
    )


def check_reviewed_hash_honesty(
    bridge_text: str,
    *,
    repo_root: Path | None = None,
    ci_bundle: bool = False,
) -> dict[str, object]:
    """Verify the reviewed worktree hash matches the current tree state."""
    reviewer_mode = normalize_reviewer_mode(
        extract_metadata_value(bridge_text, "Reviewer mode:")
    )
    last_hash = extract_metadata_value(bridge_text, "Last non-audit worktree hash:")
    if not last_hash:
        return {
            "check": "reviewed_hash_honesty",
            "role": TandemRole.REVIEWER,
            "ok": False,
            "detail": "No reviewed worktree hash found in bridge.",
        }
    if not re.fullmatch(r"[0-9a-f]{64}", last_hash):
        return {
            "check": "reviewed_hash_honesty",
            "role": TandemRole.REVIEWER,
            "ok": False,
            "detail": f"Invalid worktree hash format: {last_hash[:20]}...",
        }
    if repo_root is not None:
        try:
            current_hash = compute_non_audit_worktree_hash(
                repo_root=repo_root,
                excluded_rel_paths=_BRIDGE_EXCLUDED_REL_PATHS,
                excluded_prefixes=NON_AUDIT_HASH_EXCLUDED_PREFIXES,
            )
            matches = last_hash == current_hash
            ok = (
                matches
                or skip_live_freshness()
                or ci_bundle
                or not reviewer_mode_is_active(reviewer_mode)
            )
            return {
                "check": "reviewed_hash_honesty",
                "role": TandemRole.REVIEWER,
                "ok": ok,
                "reviewer_mode": reviewer_mode,
                "hash_prefix": last_hash[:12],
                "current_hash_prefix": current_hash[:12],
                "matches_current": matches,
                "detail": (
                    f"Reviewed hash {last_hash[:12]}... "
                    f"{'matches' if matches else 'does NOT match'} "
                    f"current tree {current_hash[:12]}..."
                ),
            }
        except (ValueError, OSError):
            pass
    return {
        "check": "reviewed_hash_honesty",
        "role": TandemRole.REVIEWER,
        "ok": True,
        "hash_prefix": last_hash[:12],
        "matches_current": None,
        "detail": f"Reviewed worktree hash is valid ({last_hash[:12]}...), current tree comparison unavailable.",
    }
