"""Regression coverage for governed commit visibility diagnostics."""

from __future__ import annotations

from types import SimpleNamespace

from dev.scripts.devctl.commands.vcs.commit_visibility import commit_visibility_payload


def test_commit_recorded_with_approval_state_does_not_render_ready_to_commit() -> None:
    pipeline = SimpleNamespace(
        pipeline_id="pipeline-1",
        state="commit_recorded",
        approval_state="approved",
        commit_sha="abc123",
    )

    payload = commit_visibility_payload(pipeline)

    assert payload["commit_phase"] == "committed"
    assert payload["commit_progress"] == "commit_recorded"
    assert payload["git_commit_state"] == "landed"
    assert payload["post_commit_state"] == "commit_recorded_projection_pending"
    assert payload["publication_state"] == "awaiting_governed_push"


def test_push_pending_with_approval_state_renders_publication_pending() -> None:
    pipeline = SimpleNamespace(
        pipeline_id="pipeline-1",
        state="push_pending",
        approval_state="approved",
        commit_sha="abc123",
    )

    payload = commit_visibility_payload(pipeline)

    assert payload["commit_phase"] == "ready_to_push"
    assert payload["commit_progress"] == "commit_recorded_waiting_for_push"
    assert payload["git_commit_state"] == "landed"
    assert payload["post_commit_state"] == "publication_pending"
    assert payload["publication_state"] == "awaiting_governed_push"


def test_push_blocked_without_commit_sha_reports_commit_failure() -> None:
    pipeline = SimpleNamespace(
        pipeline_id="pipeline-1",
        state="push_blocked",
        approval_state="approved",
        commit_sha="",
        commit_result=SimpleNamespace(ok=False, reason="git_index_write_blocked"),
    )

    payload = commit_visibility_payload(pipeline)

    assert payload["commit_phase"] == "push_blocked"
    assert payload["git_commit_state"] == "failed"
    assert payload["post_commit_state"] == "blocked_by_commit_failure"
    assert payload["publication_state"] == "blocked_before_commit"
