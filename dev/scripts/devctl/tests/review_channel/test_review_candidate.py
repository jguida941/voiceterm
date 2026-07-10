"""Focused regressions for typed review-candidate handoff."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from dev.scripts.devctl.review_channel.review_candidate import (
    build_review_candidate,
    review_candidate_error,
)
from dev.scripts.devctl.runtime.review_state_models import ReviewCurrentSessionState
from dev.scripts.devctl.tests.vcs.test_governed_executor import (
    _init_repo,
    _run_git,
)


def _ready_session(
    *,
    instruction: str,
    instruction_revision: str = "rev-123",
    state_hash: str = "state-123",
) -> ReviewCurrentSessionState:
    return ReviewCurrentSessionState(
        current_instruction=instruction,
        current_instruction_revision=instruction_revision,
        implementer_status=(
            "- implemented the requested slice and ran "
            "`pytest tests/test_tracked.py` plus "
            "`python3 dev/scripts/devctl.py check --profile ci`"
        ),
        implementer_ack=f"- ready for review; instruction-rev: `{instruction_revision}`",
        implementer_ack_revision=instruction_revision,
        implementer_ack_state="current",
        implementer_state_hash=state_hash,
        open_findings="- none",
        last_reviewed_scope="- tracked.txt",
    )


def test_build_review_candidate_prefers_dirty_tree_slice(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    head_sha = _run_git(repo_root, "rev-parse", "HEAD")

    candidate = build_review_candidate(
        repo_root=repo_root,
        current_session=_ready_session(instruction="- review `tracked.txt`"),
        bridge_liveness={
            "head_at_push_time": head_sha,
            "last_worktree_hash": "a" * 64,
        },
        prior_review_state=None,
    )

    assert candidate is not None
    assert candidate.artifact_kind == "dirty_tree"
    assert candidate.valid is True
    assert candidate.ready_for_review is True
    assert "tracked.txt" in candidate.changed_paths
    assert candidate.tests_run == ("pytest tests/test_tracked.py",)
    assert candidate.guards_run == (
        "python3 dev/scripts/devctl.py check --profile ci",
    )


def test_build_review_candidate_invalidates_on_worktree_drift_without_new_completion(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    head_sha = _run_git(repo_root, "rev-parse", "HEAD")
    current_session = _ready_session(instruction="- review `tracked.txt`")

    first = build_review_candidate(
        repo_root=repo_root,
        current_session=current_session,
        bridge_liveness={
            "head_at_push_time": head_sha,
            "last_worktree_hash": "a" * 64,
        },
        prior_review_state=None,
    )
    assert first is not None

    (repo_root / "tracked.txt").write_text("updated again\n", encoding="utf-8")
    second = build_review_candidate(
        repo_root=repo_root,
        current_session=current_session,
        bridge_liveness={
            "head_at_push_time": head_sha,
            "last_worktree_hash": "b" * 64,
        },
        prior_review_state={"review_candidate": asdict(first)},
    )

    assert second is not None
    assert second.candidate_id == first.candidate_id
    assert second.valid is False
    assert second.ready_for_review is False
    assert second.invalidation_reason == "worktree_drift_after_candidate"


def test_build_review_candidate_blocks_scope_mismatch(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    head_sha = _run_git(repo_root, "rev-parse", "HEAD")
    current_session = _ready_session(instruction="- review `other.txt`")

    candidate = build_review_candidate(
        repo_root=repo_root,
        current_session=current_session,
        bridge_liveness={
            "head_at_push_time": head_sha,
            "last_worktree_hash": "c" * 64,
        },
        prior_review_state=None,
    )

    assert candidate is not None
    assert candidate.valid is False
    assert candidate.invalidation_reason == "scope_mismatch"
    assert candidate.missing_scope_paths == ("other.txt",)
    error = review_candidate_error(
        current_session=current_session,
        candidate=candidate,
    )
    assert error is not None
    assert "stale or wrong" in error
