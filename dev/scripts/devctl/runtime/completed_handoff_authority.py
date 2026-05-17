"""Publication authority helpers for completed-handoff receipts."""

from __future__ import annotations

import os
from pathlib import Path

from ..governance.push_state import current_head_commit_sha
from ..review_channel.agent_session_outcome_events import (
    latest_current_completed_handoff_outcome,
)
from ..review_channel.event_store import resolve_artifact_paths
from ..review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
)
from .agent_session_outcome import AgentSessionOutcomeState
from .governance_scan import scan_repo_governance_safely
from .review_snapshot_refresh import (
    receipt_commit_ancestor_shas,
)
from .vcs import run_git_capture

_DEFAULT_COMPLETED_HANDOFF_PROVIDER = "codex"


def current_completed_handoff_outcome(
    *,
    repo_root: Path,
    expected_provider: str = _DEFAULT_COMPLETED_HANDOFF_PROVIDER,
) -> AgentSessionOutcomeState | None:
    """Return a current completed handoff bound to the publication target."""
    try:
        outcome = latest_current_completed_handoff_outcome(
            repo_root=repo_root,
            expected_target_revisions=handoff_target_revisions(repo_root),
        )
    except (OSError, ValueError):
        return None
    if outcome is None:
        return None
    provider = str(expected_provider or "").strip().lower()
    if provider and outcome.provider.lower() != provider:
        return None
    return outcome


def has_current_completed_handoff(
    *,
    repo_root: Path,
    expected_provider: str = _DEFAULT_COMPLETED_HANDOFF_PROVIDER,
) -> bool:
    """Return True when a current completed-handoff receipt exists."""
    return (
        current_completed_handoff_outcome(
            repo_root=repo_root,
            expected_provider=expected_provider,
        )
        is not None
    )


def handoff_target_revisions(repo_root: Path) -> tuple[str, ...]:
    """Return current HEAD plus managed receipt-chain roots accepted for handoff."""
    current_head = current_head_commit_sha(repo_root=repo_root)
    if not current_head:
        return ()

    governance = scan_repo_governance_safely(repo_root)
    revisions: list[str] = []
    content_head = _append_receipt_chain_revisions(
        revisions,
        repo_root=repo_root,
        current_head=current_head,
        governance=governance,
    )

    pipeline_commit = _current_pipeline_commit_sha(repo_root)
    pipeline_content_head = ""
    if pipeline_commit:
        pipeline_content_head = _append_receipt_chain_revisions(
            revisions,
            repo_root=repo_root,
            current_head=pipeline_commit,
            governance=governance,
        )
    if pipeline_content_head and pipeline_content_head == content_head:
        _append_handoff_parent_revisions(
            revisions,
            repo_root=repo_root,
            content_head=content_head,
            governance=governance,
        )
    return tuple(revisions)


def _append_receipt_chain_revisions(
    revisions: list[str],
    *,
    repo_root: Path,
    current_head: str,
    governance,
) -> str:
    target = str(current_head or "").strip()
    if not target:
        return ""
    _append_unique(revisions, target)
    receipt_ancestors = receipt_commit_ancestor_shas(
        repo_root=repo_root,
        current_head=target,
        governance=governance,
    )
    for ancestor in receipt_ancestors:
        _append_unique(revisions, ancestor)
    return receipt_ancestors[-1] if receipt_ancestors else target


def _append_handoff_parent_revisions(
    revisions: list[str],
    *,
    repo_root: Path,
    content_head: str,
    governance,
) -> None:
    parent = _commit_parent_sha(repo_root, content_head)
    if not parent:
        return
    parent_content_head = _append_receipt_chain_revisions(
        revisions,
        repo_root=repo_root,
        current_head=parent,
        governance=governance,
    )
    if parent_content_head and parent_content_head != parent:
        _append_unique(revisions, _commit_parent_sha(repo_root, parent_content_head))


def _current_pipeline_commit_sha(repo_root: Path) -> str:
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    pipeline = load_remote_commit_pipeline_contract(
        output_root=Path(artifact_paths.projections_root)
    )
    result = pipeline.commit_result
    if not (result is not None and result.ok and result.action_id == "vcs.commit"):
        return ""
    return str(pipeline.commit_sha or "").strip()


def _commit_parent_sha(repo_root: Path, commit_sha: str) -> str:
    target = str(commit_sha or "").strip()
    if not target:
        return ""
    code, stdout, _ = run_git_capture(
        ["rev-parse", f"{target}^"],
        repo_root=repo_root,
    )
    if code != 0:
        return ""
    return stdout.strip()


def _append_unique(values: list[str], value: str) -> None:
    text = str(value or "").strip()
    if text and text not in values:
        values.append(text)


__all__ = [
    "current_completed_handoff_outcome",
    "handoff_target_revisions",
    "has_current_completed_handoff",
]
