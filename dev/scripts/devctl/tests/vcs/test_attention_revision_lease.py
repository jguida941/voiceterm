"""Regression tests for the Q100 attention-revision lease pattern.

The commit pipeline approves at `attention_revision=N`, then its own guard
bundle may write typed state (event projection, inbox refresh, dogfood row)
that bumps the live revision to `N+1`. Without a held lease the final
commit-record check would compare the pre-guard revision to the live
post-guard revision and self-invalidate the already-approved pipeline with
`reason=attention_revision_stale`.

These tests pin the three-step drift scenario:
    1. approve → lease captures `N`
    2. intervening typed-state write → live revision becomes `N+1`
    3. final stale check reads the held lease, not the live revision, and
       does not block the commit.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime import (
    attention_revision_stale,
    live_attention_revision,
)
from dev.scripts.devctl.commands.vcs.governed_executor_support import (
    commit_failed_pipeline,
    commit_recorded_pipeline,
)
from dev.scripts.devctl.runtime.action_contracts import ActionOutcome
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    CommitIntentState,
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
    remote_commit_pipeline_contract_from_mapping,
)


def _result_builder(**kwargs: object) -> object:
    return SimpleNamespace(**kwargs)


def _approved_pipeline(lease: str = "") -> RemoteCommitPipelineContract:
    return RemoteCommitPipelineContract(
        pipeline_id="pipeline-q100",
        state="approved",
        approval_state="approved",
        approval_packet_id="req-1",
        decision_packet_id="dec-1",
        intent=CommitIntentState(staged_tree_hash="tree-hash"),
        attention_revision_lease=lease,
    )


def _inbox_with(attention_revision: str) -> SimpleNamespace:
    return SimpleNamespace(
        packet_inbox=SimpleNamespace(
            attention_revision=attention_revision,
            agents=(
                SimpleNamespace(
                    agent="codex",
                    attention_status="review_needed",
                    wake_reason="finding_pending",
                    pending_actionable_packet_ids=(),
                ),
            ),
        )
    )


def test_held_lease_suppresses_stale_gate_even_when_live_revision_drifts() -> None:
    """Three-step drift: approve N, mid-bundle bump to N+1, check still passes."""
    # Step 1: approval moment snapshots `N` into the pipeline lease.
    held_lease = "rev-N"

    # Step 2: an intervening typed-state write (event projection refresh,
    # dogfood row, inbox update) bumps the live revision to N+1.
    live_review_state = _inbox_with("rev-N-plus-1")

    # Step 3: final commit-record stale check reads the held lease, not live.
    with (
        patch(
            "dev.scripts.devctl.commands.vcs."
            "governed_executor_commit_runtime.load_live_review_state",
            return_value=live_review_state,
        ),
        patch(
            "dev.scripts.devctl.commands.vcs."
            "governed_executor_commit_runtime.resolve_commit_execution_target",
            return_value="codex",
        ),
        patch(
            "dev.scripts.devctl.commands.vcs."
            "governed_executor_commit_runtime.load_startup_receipt",
            return_value=SimpleNamespace(attention_revision="rev-receipt"),
        ),
    ):
        assert (
            attention_revision_stale(
                repo_root=Path("."),
                review_channel_path=Path("dev/active/review_channel.md"),
                held_lease=held_lease,
            )
            is False
        )


def test_absent_lease_preserves_pre_q100_stale_semantics() -> None:
    """No lease held → the check still flags live != receipt drift."""
    live_review_state = _inbox_with("rev-live")
    with (
        patch(
            "dev.scripts.devctl.commands.vcs."
            "governed_executor_commit_runtime.load_live_review_state",
            return_value=live_review_state,
        ),
        patch(
            "dev.scripts.devctl.commands.vcs."
            "governed_executor_commit_runtime.resolve_commit_execution_target",
            return_value="codex",
        ),
        patch(
            "dev.scripts.devctl.commands.vcs."
            "governed_executor_commit_runtime.load_startup_receipt",
            return_value=SimpleNamespace(attention_revision="rev-receipt"),
        ),
    ):
        assert (
            attention_revision_stale(
                repo_root=Path("."),
                review_channel_path=Path("dev/active/review_channel.md"),
            )
            is True
        )


def test_empty_lease_string_is_treated_as_no_lease() -> None:
    """Whitespace-only lease must not short-circuit the live comparison."""
    live_review_state = _inbox_with("rev-live")
    with (
        patch(
            "dev.scripts.devctl.commands.vcs."
            "governed_executor_commit_runtime.load_live_review_state",
            return_value=live_review_state,
        ),
        patch(
            "dev.scripts.devctl.commands.vcs."
            "governed_executor_commit_runtime.resolve_commit_execution_target",
            return_value="codex",
        ),
        patch(
            "dev.scripts.devctl.commands.vcs."
            "governed_executor_commit_runtime.load_startup_receipt",
            return_value=SimpleNamespace(attention_revision="rev-receipt"),
        ),
    ):
        assert (
            attention_revision_stale(
                repo_root=Path("."),
                review_channel_path=Path("dev/active/review_channel.md"),
                held_lease="   ",
            )
            is True
        )


def test_live_attention_revision_reads_packet_inbox_revision() -> None:
    """`live_attention_revision` exposes the current live revision for lease capture."""
    with patch(
        "dev.scripts.devctl.commands.vcs."
        "governed_executor_commit_runtime.load_live_review_state",
        return_value=_inbox_with("rev-live-42"),
    ):
        assert (
            live_attention_revision(
                repo_root=Path("."),
                review_channel_path=Path("dev/active/review_channel.md"),
            )
            == "rev-live-42"
        )


def test_live_attention_revision_returns_empty_when_state_missing() -> None:
    """`live_attention_revision` must tolerate a missing review state."""
    with patch(
        "dev.scripts.devctl.commands.vcs."
        "governed_executor_commit_runtime.load_live_review_state",
        return_value=None,
    ):
        assert (
            live_attention_revision(
                repo_root=Path("."),
                review_channel_path=Path("dev/active/review_channel.md"),
            )
            == ""
        )


def test_pipeline_model_round_trips_lease_field() -> None:
    """The typed contract persists and rehydrates the lease across projections."""
    original = _approved_pipeline(lease="rev-held")
    hydrated = remote_commit_pipeline_contract_from_mapping(original.to_dict())
    assert hydrated.attention_revision_lease == "rev-held"


def test_pipeline_model_defaults_empty_lease_when_field_missing() -> None:
    """Old projections without the field must load as empty lease."""
    legacy_payload = {
        "pipeline_id": "legacy",
        "state": "approved",
        "approval_state": "approved",
    }
    hydrated = remote_commit_pipeline_contract_from_mapping(legacy_payload)
    assert hydrated.attention_revision_lease == ""


def test_commit_recorded_releases_held_lease() -> None:
    """Successful commit transitions `commit_recorded` and clears the lease."""
    pending = replace(
        _approved_pipeline(lease="rev-held"),
        state="commit_pending",
    )
    completed = commit_recorded_pipeline(
        pending_pipeline=pending,
        action_id="vcs.commit",
        commit_sha="deadbeef",
        push_authorization=PushAuthorizationRecord(),
        artifact_relpath="dev/reports/review_channel/latest/commit_pipeline.json",
        result_builder=_result_builder,
    )
    assert completed.state == "commit_recorded"
    assert completed.attention_revision_lease == ""


def test_commit_failed_releases_held_lease() -> None:
    """Hard commit failure clears the lease so restage starts clean."""
    pending = replace(
        _approved_pipeline(lease="rev-held"),
        state="commit_pending",
    )
    failed = commit_failed_pipeline(
        pending_pipeline=pending,
        action_id="vcs.commit",
        commit_error="fatal: refusing",
        artifact_relpath="dev/reports/review_channel/latest/commit_pipeline.json",
        result_builder=_result_builder,
    )
    assert failed.state == "push_blocked"
    assert failed.attention_revision_lease == ""
    # The commit result carries the structured failure reason through the
    # generic commit_failed default.
    assert failed.commit_result.status == ActionOutcome.FAIL
