"""Bridge-drift detection and sync helpers for review-channel status."""

from __future__ import annotations

import json
from pathlib import Path

from ...review_channel.bridge_file import rewrite_bridge_markdown
from ...review_channel.bridge_projection import render_bridge_projection
from ...review_channel.current_session_projection import (
    current_session_authority_drift_warning,
)
from ...review_channel.handoff import extract_bridge_snapshot
from ...review_channel.heartbeat import compute_non_audit_worktree_hash
from ...review_channel.pending_packets import assert_no_pending_reviewer_packets


def bridge_current_session_drifted(
    warnings: list[str],
    *,
    bridge_path: Path | None = None,
    review_state_path: Path | None = None,
) -> bool:
    if any(
        "typed `current_session` authority" in str(warning)
        for warning in warnings
    ):
        return True
    if bridge_path is None or review_state_path is None:
        return False
    if not bridge_path.is_file() or not review_state_path.is_file():
        return False
    try:
        prior_review_state = json.loads(review_state_path.read_text(encoding="utf-8"))
        if not isinstance(prior_review_state, dict):
            return False
        snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    return bool(
        current_session_authority_drift_warning(
            snapshot=snapshot,
            prior_review_state=prior_review_state,
        )
    )


def without_bridge_current_session_drift(warnings: object) -> list[str]:
    if not isinstance(warnings, list):
        return []
    return [
        str(warning)
        for warning in warnings
        if "typed `current_session` authority" not in str(warning)
    ]


def sync_bridge_from_typed_projection_if_needed(
    *,
    repo_root: Path,
    bridge_path: Path,
    snapshot,
) -> tuple[bool, str]:
    review_state_path = Path(snapshot.projection_paths.review_state_path)
    if not review_state_path.is_file():
        return (
            False,
            "Skipped `bridge.md` sync during status refresh because the typed "
            "review-state projection is missing.",
        )
    try:
        assert_no_pending_reviewer_packets(
            repo_root=repo_root,
            action_label="bridge sync during status refresh",
        )
    except ValueError as exc:
        return (False, str(exc))
    try:
        review_state_payload = json.loads(review_state_path.read_text(encoding="utf-8"))
        if not isinstance(review_state_payload, dict):
            raise ValueError("Typed review-state projection must be a JSON object.")
        bridge_rel = str(bridge_path.relative_to(repo_root))
        worktree_hash = compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=(bridge_rel,),
        )

        def transform(_bridge_text: str) -> str:
            rendered, _ = render_bridge_projection(
                review_state=review_state_payload,
                last_worktree_hash=worktree_hash,
            )
            return rendered

        rewrite_bridge_markdown(bridge_path, transform=transform)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return (
            False,
            "Failed to synchronize `bridge.md` from typed review-state during "
            f"status refresh: {exc}",
        )
    return (True, "")
