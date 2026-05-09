"""Governed push publication scope helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...governance.push_state import current_head_commit_sha
from ...runtime.remote_commit_pipeline_state import PUSHABLE_PIPELINE_STATES
from ...runtime.vcs import run_git_capture


def commit_pipeline_authorizes_publication_scope(
    pipeline: Any,
    *,
    state: Any,
    repo_root: Path = REPO_ROOT,
) -> bool:
    """Return True when validation can bind to a governed commit pipeline."""
    if pipeline is None:
        return False
    pipeline_id = str(getattr(pipeline, "pipeline_id", "") or "").strip()
    pipeline_state = str(getattr(pipeline, "state", "") or "").strip()
    commit_sha = str(getattr(pipeline, "commit_sha", "") or "").strip()
    branch = str(getattr(pipeline, "branch", "") or "").strip()
    current_head = current_head_commit_sha(repo_root=repo_root)
    current_branch = state.live_branch or state.branch
    if not (
        pipeline_id
        and pipeline_state in PUSHABLE_PIPELINE_STATES
        and commit_sha
        and current_head
        and _head_matches_pipeline_publication(
            current_head,
            commit_sha,
            repo_root=repo_root,
        )
        and branch
        and current_branch
        and branch == current_branch
        and state.branch == current_branch
    ):
        return False
    authorization = getattr(pipeline, "push_authorization", None)
    authorized_head = authorized_head_sha(pipeline)
    if not authorized_head or authorized_head != commit_sha:
        return False
    approval_mode = str(getattr(authorization, "approval_mode", "") or "").strip()
    return approval_mode in {"commit_pipeline_approval", "override_push"}


def authorized_head_sha(pipeline: Any) -> str:
    authorization = getattr(pipeline, "push_authorization", None)
    return str(getattr(authorization, "authorized_head_sha", "") or "").strip()


def refresh_authorized_preflight_head_after_managed_receipts(
    state: Any,
    *,
    commit_pipeline: Any = None,
    repo_root: Path = REPO_ROOT,
) -> None:
    """Bind push preflight to the current publishable HEAD after receipt commits."""
    if not getattr(state, "push_authorization_head_commit", "") or commit_pipeline is None:
        return
    current_head = current_head_commit_sha(repo_root=repo_root)
    if (
        not current_head
        or current_head == state.push_authorization_head_commit
        or not commit_pipeline_authorizes_publication_scope(
            commit_pipeline,
            state=state,
            repo_root=repo_root,
        )
    ):
        return
    state.warnings.append(
        "Managed projection receipt moved HEAD; validating the current "
        f"publication head {current_head[:12]} instead of the authorized content "
        f"head {state.push_authorization_head_commit[:12]}."
    )
    state.push_authorization_head_commit = current_head


def _head_matches_pipeline_publication(
    current_head: str,
    commit_sha: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> bool:
    if current_head == commit_sha:
        return True
    return _head_is_managed_projection_receipt_for(
        current_head,
        commit_sha,
        repo_root=repo_root,
    )


def _head_is_managed_projection_receipt_for(
    current_head: str,
    commit_sha: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> bool:
    subject_code, subject, _ = run_git_capture(
        ["show", "-s", "--format=%s", current_head],
        repo_root=repo_root,
    )
    if subject_code != 0:
        return False
    if not str(subject or "").startswith(
        (
            "Refresh policy-owned generated surfaces for ",
            "Refresh external review snapshot for ",
        )
    ):
        return False
    parents_code, parents, _ = run_git_capture(
        ["rev-list", "--parents", "-n", "1", current_head],
        repo_root=repo_root,
    )
    if parents_code != 0:
        return False
    parent_shas = tuple(str(parents or "").strip().split()[1:])
    return commit_sha in parent_shas


__all__ = [
    "authorized_head_sha",
    "commit_pipeline_authorizes_publication_scope",
    "refresh_authorized_preflight_head_after_managed_receipts",
]
