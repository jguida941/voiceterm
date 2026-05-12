"""Tests for event-backed review-channel post guards."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from dev.scripts.devctl.commands.review_channel import event_post_action


def _args(
    *,
    kind: str = "task_produced",
    from_agent: str = "codex",
    commit_sha: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        kind=kind,
        from_agent=from_agent,
        evidence_ref=[],
        evidence_artifact_path=[],
        action_result_id=[],
        commit_sha=commit_sha,
        plan_revision_before="",
        plan_revision_after="",
    )


def test_codex_task_produced_requires_commit_or_clean_worktree(monkeypatch) -> None:
    monkeypatch.setattr(event_post_action, "_worktree_clean", lambda _repo_root: False)
    args = _args()

    with pytest.raises(ValueError, match="task_produced from codex requires commit"):
        event_post_action._require_commit_or_clean_worktree_for_publish(
            Path("/repo"),
            args,
            event_post_action._post_evidence_refs(args),
        )


def test_codex_task_produced_allows_commit_evidence_on_dirty_worktree(
    monkeypatch,
) -> None:
    monkeypatch.setattr(event_post_action, "_worktree_clean", lambda _repo_root: False)
    args = _args(commit_sha="a" * 40)

    event_post_action._require_commit_or_clean_worktree_for_publish(
        Path("/repo"),
        args,
        event_post_action._post_evidence_refs(args),
    )


def test_codex_task_produced_allows_clean_worktree(monkeypatch) -> None:
    monkeypatch.setattr(event_post_action, "_worktree_clean", lambda _repo_root: True)
    args = _args()

    event_post_action._require_commit_or_clean_worktree_for_publish(
        Path("/repo"),
        args,
        event_post_action._post_evidence_refs(args),
    )


def test_claude_audit_packets_do_not_use_codex_publish_guard(monkeypatch) -> None:
    monkeypatch.setattr(event_post_action, "_worktree_clean", lambda _repo_root: False)
    args = _args(kind="review_accepted", from_agent="claude")

    event_post_action._require_commit_or_clean_worktree_for_publish(
        Path("/repo"),
        args,
        event_post_action._post_evidence_refs(args),
    )
