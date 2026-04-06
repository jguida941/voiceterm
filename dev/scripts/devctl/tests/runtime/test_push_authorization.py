"""Tests for persisted publication authorization decisions."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.runtime.action_contracts import ActionOutcome
from dev.scripts.devctl.runtime.push_authorization import (
    publication_authorization_decision,
)
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
)


def _review_state() -> SimpleNamespace:
    return SimpleNamespace(
        reviewer_runtime=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            effective_reviewer_mode="active_dual_agent",
            reviewer_freshness="stale",
            stale_reason="reviewer_missing",
        )
    )


def _pipeline(*, authorized_head_sha: str) -> RemoteCommitPipelineContract:
    return RemoteCommitPipelineContract(
        pipeline_id="pipeline-123",
        state="commit_recorded",
        commit_sha=authorized_head_sha,
        approved_target_identity="tree-receipt-20260403T010000Z:tree-123",
        push_authorization=PushAuthorizationRecord(
            authorization_id="push-auth-20260403T010000Z",
            pipeline_id="pipeline-123",
            generation_id="gen-123",
            authorized_head_sha=authorized_head_sha,
            approved_target_identity="tree-receipt-20260403T010000Z:tree-123",
            approval_mode="commit_pipeline_approval",
            guard_action_id="quality.guard_bundle",
            guard_status=ActionOutcome.PASS,
            approved_by="operator",
            approved_at_utc="2026-04-05T12:00:00Z",
        ),
    )


@patch("dev.scripts.devctl.runtime.push_authorization.scan_repo_governance")
@patch("dev.scripts.devctl.runtime.push_authorization.load_review_state")
@patch("dev.scripts.devctl.runtime.push_authorization.current_head_commit_sha")
@patch("dev.scripts.devctl.runtime.push_authorization._load_pipeline")
def test_publication_authorization_allows_current_head_with_stale_reviewer_runtime(
    load_pipeline_mock,
    current_head_mock,
    load_review_state_mock,
    _scan_governance_mock,
) -> None:
    load_review_state_mock.return_value = _review_state()
    current_head_mock.return_value = "head-123"
    load_pipeline_mock.return_value = _pipeline(authorized_head_sha="head-123")

    decision = publication_authorization_decision(repo_root=Path("/tmp/repo"))

    assert decision.authorized is True
    assert decision.reason == "push_authorization_current"
    assert decision.push_authorization is not None
    assert decision.push_authorization.approval_mode == "commit_pipeline_approval"


@patch("dev.scripts.devctl.runtime.push_authorization.scan_repo_governance")
@patch("dev.scripts.devctl.runtime.push_authorization.load_review_state")
@patch("dev.scripts.devctl.runtime.push_authorization.current_head_commit_sha")
@patch("dev.scripts.devctl.runtime.push_authorization._load_pipeline")
def test_publication_authorization_blocks_when_head_changes_after_authorization(
    load_pipeline_mock,
    current_head_mock,
    load_review_state_mock,
    _scan_governance_mock,
) -> None:
    load_review_state_mock.return_value = _review_state()
    current_head_mock.return_value = "head-new"
    load_pipeline_mock.return_value = _pipeline(authorized_head_sha="head-old")

    decision = publication_authorization_decision(repo_root=Path("/tmp/repo"))

    assert decision.authorized is False
    assert decision.reason == "head_changed_after_authorization"
    assert decision.push_authorization is not None
