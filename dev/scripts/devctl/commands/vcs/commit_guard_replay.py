"""Guard-replay helpers for reusable governed commit pipelines."""

from __future__ import annotations

from pathlib import Path

from ...runtime.action_contracts import ActionOutcome
from .commit_guard_bundle import run_guard_bundle_with_result
from .governed_executor import GovernedVcsExecutor
from .governed_executor_actions import APPROVAL_PACKET_KIND
from .governed_executor_sync import sync_pipeline_approval


def pipeline_needs_guard_replay(pipeline) -> bool:
    """Return whether the reusable pipeline needs a fresh guard receipt."""
    if pipeline.guard_result is None or pipeline.guard_result.status != ActionOutcome.PASS:
        return True
    validation_receipt = pipeline.validation_receipt
    if validation_receipt is None:
        return True
    if validation_receipt.staged_tree_hash != pipeline.intent.staged_tree_hash:
        return True
    return not validation_receipt.checkpoint_sufficient


def sync_pipeline_approval_state(
    executor: GovernedVcsExecutor,
    pipeline,
):
    """Refresh and persist approval state after guard-side pipeline writes."""
    synced = sync_pipeline_approval(
        pipeline,
        executor._event_packets(),
        approval_packet_kind=APPROVAL_PACKET_KIND,
    )
    if synced != pipeline:
        executor._persist_pipeline(synced)
    return synced


def replay_pipeline_guards(
    *,
    vcs_executor: GovernedVcsExecutor,
    repo_root: Path,
    guard_runner,
    pipeline,
):
    """Replay the routed guard bundle for one reusable governed pipeline."""
    guard_rc, action_result = run_guard_bundle_with_result(
        repo_root=repo_root,
        runner=guard_runner,
        pipeline=pipeline,
    )
    pipeline = vcs_executor.record_guard_result(action_result)
    if guard_rc == 0:
        pipeline = sync_pipeline_approval_state(vcs_executor, pipeline)
    return guard_rc, pipeline
