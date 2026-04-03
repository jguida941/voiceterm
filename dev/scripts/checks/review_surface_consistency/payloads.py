"""Runtime payload assembly helpers for review-surface consistency."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from dev.scripts.devctl.commands.review_channel._bridge_poll_support import (
    build_bridge_poll_result,
)
from dev.scripts.devctl.review_channel.handoff import (
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from dev.scripts.devctl.review_channel.heartbeat import (
    compute_non_audit_worktree_hash,
)
from dev.scripts.devctl.review_channel.turn_authority import (
    build_reviewer_turn_authority,
)

from .support import _nested


def load_bridge_poll_payload(
    *,
    repo_root: Path,
    review_state_payload: dict[str, object],
) -> dict[str, object]:
    return _load_runtime_payload(
        repo_root=repo_root,
        review_state_payload=review_state_payload,
        builder=lambda bridge_text, current_worktree_hash: build_bridge_poll_result(
            bridge_text,
            current_worktree_hash=current_worktree_hash,
            typed_review_state=review_state_payload,
        ).to_dict(),
    )


def load_turn_authority_payload(
    *,
    repo_root: Path,
    review_state_payload: dict[str, object],
) -> dict[str, object]:
    def _build_turn_authority_payload(
        bridge_text: str,
        current_worktree_hash: str | None,
    ) -> dict[str, object]:
        snapshot = extract_bridge_snapshot(bridge_text)
        return build_reviewer_turn_authority(
            snapshot=snapshot,
            bridge_liveness=summarize_bridge_liveness(
                snapshot,
                current_worktree_hash=current_worktree_hash,
            ),
            typed_review_state=review_state_payload,
        ).to_dict()

    return _load_runtime_payload(
        repo_root=repo_root,
        review_state_payload=review_state_payload,
        builder=_build_turn_authority_payload,
    )


def _load_runtime_payload(
    *,
    repo_root: Path,
    review_state_payload: dict[str, object],
    builder: Callable[[str, str | None], dict[str, object]],
) -> dict[str, object]:
    bridge_rel = _nested(review_state_payload, "review", "bridge_path")
    bridge_path = repo_root / bridge_rel if bridge_rel else repo_root / "bridge.md"
    if bridge_path is None or not bridge_path.exists():
        return {}
    try:
        bridge_text = bridge_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        bridge_rel = str(bridge_path.relative_to(repo_root))
    except ValueError:
        bridge_rel = bridge_path.name
    try:
        current_worktree_hash = compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=(bridge_rel,),
        )
    except (OSError, ValueError):
        current_worktree_hash = None
    return builder(bridge_text, current_worktree_hash)
