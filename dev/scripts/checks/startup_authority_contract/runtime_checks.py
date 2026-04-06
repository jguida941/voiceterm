"""Runtime checks for the startup-authority contract."""

from __future__ import annotations

from pathlib import Path

_IMPLEMENTATION_STRICT_INTENT = "implementation_strict"
_REVIEWER_BOOTSTRAP_INTENT = "reviewer_bootstrap"

# Canonical location for the governed remote-commit-pipeline projection.
# Kept in lockstep with ``active_path_config().review_status_dir_rel`` — this
# is the repo-local path every other governance surface already agrees on.
_REVIEW_STATUS_DIR_REL = "dev/reports/review_channel/latest"

# Pipeline states where the frozen staged snapshot is intentionally held in
# the dirty worktree awaiting the next governed step (guard bundle, approval
# packet, commit). Post-commit states (``commit_recorded``, ``push_pending``,
# ``push_blocked``, ``push_completed``, ``rejected``) are excluded on purpose:
# once a commit is recorded, the staged snapshot is behind that commit and
# any remaining dirt is new dirt that still deserves the normal
# "commit_before_push" rejection. The canonical active-state set lives in
# ``dev.scripts.devctl.commands.vcs.governed_executor_actions`` — this guard
# intentionally inlines the parked subset so the check has no cross-layer
# import dependency into the vcs command package.
_PIPELINE_PARKED_AT_CHECKPOINT_STATES = frozenset(
    {
        "drafted",
        "staged",
        "guards_running",
        "guards_passed",
        "guards_failed",
        "operator_approval_pending",
        "approved",
        "commit_pending",
    }
)

try:
    from check_bootstrap import (
        REPO_ROOT,
        import_repo_module,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        import_repo_module,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )

from .runtime_import_atomicity import collect_import_index_atomicity_findings
from .runtime_push_checks import collect_push_decision_contract_errors

_detect_reviewer_gate = import_repo_module(
    "dev.scripts.devctl.runtime.startup_context",
    repo_root=REPO_ROOT,
)._detect_reviewer_gate

_load_remote_commit_pipeline_contract = import_repo_module(
    "dev.scripts.devctl.review_channel.remote_commit_pipeline_artifact",
    repo_root=REPO_ROOT,
).load_remote_commit_pipeline_contract


def _governed_pipeline_parked_at_checkpoint(
    repo_root: Path | None,
    *,
    pipeline=None,
) -> bool:
    """Return True iff a governed remote-commit pipeline is holding the worktree.

    The exemption is narrow by design: the pipeline must carry a non-empty
    ``pipeline_id``, its ``state`` must be in the canonical parked-at-checkpoint
    set, and its ``intent`` must declare both a ``staged_tree_hash`` and a
    ``staged_path_count >= 1``. Any looser shape falls through to normal
    enforcement. Callers may inject ``pipeline`` directly for unit tests;
    otherwise the contract is loaded from the canonical review-status dir
    relative to ``repo_root`` and unreadable/malformed artifacts fail closed
    by returning False (i.e. no exemption).
    """
    if pipeline is None:
        if repo_root is None:
            return False
        try:
            pipeline = _load_remote_commit_pipeline_contract(
                output_root=repo_root / _REVIEW_STATUS_DIR_REL,
            )
        except (OSError, ValueError):
            return False
    if pipeline is None:
        return False
    if not getattr(pipeline, "pipeline_id", ""):
        return False
    state = getattr(pipeline, "state", "") or ""
    if state not in _PIPELINE_PARKED_AT_CHECKPOINT_STATES:
        return False
    intent = getattr(pipeline, "intent", None)
    if intent is None:
        return False
    if not getattr(intent, "staged_tree_hash", ""):
        return False
    try:
        staged_path_count = int(getattr(intent, "staged_path_count", 0) or 0)
    except (TypeError, ValueError):
        return False
    if staged_path_count <= 0:
        return False
    return True


def collect_checkpoint_budget_errors(gov) -> list[str]:
    """Return fail-closed errors when the worktree is over the continuation budget."""
    push = gov.push_enforcement
    if push.checkpoint_required or not push.safe_to_continue_editing:
        return [
            "Startup authority is over budget: "
            f"checkpoint_required={push.checkpoint_required}, "
            f"safe_to_continue_editing={push.safe_to_continue_editing}, "
            f"reason={push.checkpoint_reason or 'worktree_budget_exceeded'}."
        ]
    return []


def collect_post_checkpoint_dirty_worktree_errors(
    gov,
    *,
    repo_root: Path | None = None,
    pipeline=None,
) -> list[str]:
    """Return fail-closed errors when a local checkpoint exists but the worktree is dirty again.

    The normal enforcement still demands a clean worktree after a checkpoint.
    The one narrow exemption is a governed remote-commit pipeline that is
    intentionally parked at the checkpoint/approval boundary: in that case
    the dirty worktree IS the staged snapshot the pipeline is landing, and
    flagging ``commit_before_push`` here would collide with the very step
    that is trying to commit. The exemption is gated by the typed pipeline
    contract loaded from the canonical review-status dir under ``repo_root``
    (or injected directly via ``pipeline`` for unit tests). Any other
    dirty-after-checkpoint shape still fails closed.
    """
    push = gov.push_enforcement
    ahead = getattr(push, "ahead_of_upstream_commits", None)
    if not isinstance(ahead, int) or ahead <= 0:
        return []
    if not getattr(push, "worktree_dirty", False):
        return []
    if (repo_root is not None or pipeline is not None) and (
        _governed_pipeline_parked_at_checkpoint(repo_root, pipeline=pipeline)
    ):
        return []
    return [
        "Startup authority detected a dirty worktree after a local checkpoint: "
        f"ahead_of_upstream_commits={ahead}, "
        f"dirty_path_count={getattr(push, 'dirty_path_count', 0)}, "
        f"untracked_path_count={getattr(push, 'untracked_path_count', 0)}, "
        f"recommended_action={getattr(push, 'recommended_action', '') or 'checkpoint_before_continue'}."
    ]


def collect_reviewer_loop_block_errors(
    repo_root: Path,
    gov,
    *,
    intent: str = _IMPLEMENTATION_STRICT_INTENT,
    reviewer_gate=None,
) -> list[str]:
    """Return fail-closed errors when the active reviewer loop blocks implementation."""
    gate = reviewer_gate
    if gate is None:
        try:
            gate = _detect_reviewer_gate(repo_root, governance=gov)
        except AttributeError:
            gate = _detect_reviewer_gate(repo_root)
    if not gate.implementation_blocked:
        return []
    if gate.review_gate_allows_push:
        return []
    if intent == _REVIEWER_BOOTSTRAP_INTENT:
        return []
    reason = gate.implementation_block_reason or "reviewer_loop_blocked"
    return [
        "Reviewer loop blocks a new implementation slice: "
        f"reviewer_mode={gate.reviewer_mode}, "
        f"review_accepted={gate.review_accepted}, "
        f"reason={reason}."
    ]
