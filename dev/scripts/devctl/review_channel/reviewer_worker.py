"""Reviewer-worker seam for the review-channel controller.

Provides ``check_review_needed`` to detect when the current tree has changed
since the last reviewed hash, without claiming semantic review completion.
Extracted from ``reviewer_state`` to stay under file-size soft limits.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .heartbeat import (
    NON_AUDIT_HASH_EXCLUDED_PREFIXES,
    compute_non_audit_worktree_hash,
)
from .peer_liveness import ReviewerMode
from .reviewer_state import (
    current_reviewed_hash,
    reviewer_mode_from_bridge_text,
)
_BRIDGE_EXCLUDED_REL_PATHS = ("bridge.md",)


@dataclass(frozen=True)
class ReviewerWorkerTick:
    """One mode-aware tick from the repo-owned reviewer-worker seam."""

    state: str
    review_needed: bool
    reviewed_hash: str
    current_hash: str
    reviewer_mode: str
    detail: str
    semantic_review_claimed: bool = False


def reviewer_worker_tick_to_dict(
    tick: ReviewerWorkerTick | None,
) -> dict[str, object] | None:
    if tick is None:
        return None
    return asdict(tick)


def check_review_needed(
    *,
    repo_root: Path,
    bridge_path: Path,
    bridge_text: str | None = None,
    current_hash: str | None = None,
) -> ReviewerWorkerTick:
    """Return reviewer-worker state without claiming semantic review completion.

    This is intentionally a narrow first seam: expose when the reviewer worker
    should wake up, but do not claim that a real reviewer pass has happened.
    """
    if bridge_text is None and not bridge_path.exists():
        return ReviewerWorkerTick(
            state="bridge_missing",
            review_needed=False,
            reviewed_hash="",
            current_hash="",
            reviewer_mode="unknown",
            detail="Bridge file does not exist",
        )
    if bridge_text is None:
        bridge_text = bridge_path.read_text(encoding="utf-8")
    reviewed_hash = current_reviewed_hash(bridge_text)
    current_mode = reviewer_mode_from_bridge_text(bridge_text)
    if current_mode != ReviewerMode.ACTIVE_DUAL_AGENT:
        return ReviewerWorkerTick(
            state="inactive_mode",
            review_needed=False,
            reviewed_hash=reviewed_hash,
            current_hash=current_hash or "",
            reviewer_mode=str(current_mode),
            detail=(
                "Reviewer worker is idle until reviewer mode returns to "
                "active_dual_agent."
            ),
        )
    if current_hash is None:
        try:
            current_hash = compute_non_audit_worktree_hash(
                repo_root=repo_root,
                excluded_rel_paths=_BRIDGE_EXCLUDED_REL_PATHS,
                excluded_prefixes=NON_AUDIT_HASH_EXCLUDED_PREFIXES,
            )
        except (ValueError, OSError):
            return ReviewerWorkerTick(
                state="hash_unavailable",
                review_needed=False,
                reviewed_hash=reviewed_hash,
                current_hash="",
                reviewer_mode=str(current_mode),
                detail="Failed to compute current tree hash",
            )
    if not reviewed_hash:
        return ReviewerWorkerTick(
            state="review_needed",
            review_needed=True,
            reviewed_hash="",
            current_hash=current_hash,
            reviewer_mode=str(current_mode),
            detail="No reviewed hash is recorded yet.",
        )
    review_needed = reviewed_hash != current_hash
    return ReviewerWorkerTick(
        state="review_needed" if review_needed else "up_to_date",
        review_needed=review_needed,
        reviewed_hash=reviewed_hash,
        current_hash=current_hash,
        reviewer_mode=str(current_mode),
        detail=(
            "Tree has changed since last review"
            if review_needed
            else "Tree matches reviewed hash"
        ),
    )
