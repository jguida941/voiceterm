"""Runtime checks for the startup-authority contract."""

from __future__ import annotations

import os
from pathlib import Path

# Env var set by ``devctl commit`` on the guard-bundle subprocess to suppress
# the dirty-worktree-after-checkpoint rejection: the staged content is what the
# commit is landing, not post-commit dirt. See LIVE_RUN.md Q1.
_COMMIT_GATE_BYPASS_ENV = "DEVCTL_COMMIT_GATE_BYPASS_STARTUP_AUTHORITY"

_IMPLEMENTATION_STRICT_INTENT = "implementation_strict"
_REVIEWER_BOOTSTRAP_INTENT = "reviewer_bootstrap"

# Hard fallback for the governed remote-commit-pipeline projection root,
# used only when neither ``ProjectGovernance.artifact_roots.review_root``
# nor a repo-pack override resolves a path. The canonical resolution path
# is ``_resolve_commit_pipeline_root_rel`` below — this constant exists so
# the check still has a deterministic last-chance default in completely
# unconfigured environments.
_DEFAULT_REVIEW_STATUS_DIR_REL = "dev/reports/review_channel/latest"

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
_build_work_intake_ownership_state = import_repo_module(
    "dev.scripts.devctl.runtime.work_intake_ownership",
    repo_root=REPO_ROOT,
).build_work_intake_ownership_state
_build_work_intake_coordination_state = import_repo_module(
    "dev.scripts.devctl.runtime.work_intake_coordination",
    repo_root=REPO_ROOT,
).build_work_intake_coordination_state
_load_current_review_state = import_repo_module(
    "dev.scripts.devctl.runtime.review_state_locator",
    repo_root=REPO_ROOT,
).load_current_review_state
_load_remote_commit_pipeline_contract = import_repo_module(
    "dev.scripts.devctl.review_channel.remote_commit_pipeline_artifact",
    repo_root=REPO_ROOT,
).load_remote_commit_pipeline_contract
_active_path_config = import_repo_module(
    "dev.scripts.devctl.repo_packs",
    repo_root=REPO_ROOT,
).active_path_config
_index_tree_hash = import_repo_module(
    "dev.scripts.devctl.commands.vcs.governed_executor_git",
    repo_root=REPO_ROOT,
).index_tree_hash


def _resolve_commit_pipeline_root_rel(governance) -> str:
    """Return the repo-relative review-status dir for the commit-pipeline artifact.

    Resolution order matches the canonical pattern in
    ``dev/scripts/devctl/runtime/review_state_locator.py``:

    1. ``governance.artifact_roots.review_root`` when set on the typed
       contract (the most specific authority).
    2. ``active_path_config().review_status_dir_rel`` from the active
       repo-pack (covers non-default product layouts that override the
       review-status dir without writing it back to ``ProjectGovernance``).
    3. ``_DEFAULT_REVIEW_STATUS_DIR_REL`` as a last-chance hard fallback
       so the check still has a deterministic answer in environments
       where neither typed source resolves a path.

    Each step is fail-soft: an exception or empty value falls through to
    the next candidate; only the final fallback can never fail.
    """
    if governance is not None:
        try:
            review_root = str(
                governance.artifact_roots.review_root or ""
            ).strip()
        except AttributeError:
            review_root = ""
        if review_root:
            return review_root.rstrip("/")
    try:
        repo_pack_rel = str(
            _active_path_config().review_status_dir_rel or ""
        ).strip()
    except (AttributeError, RuntimeError):
        repo_pack_rel = ""
    if repo_pack_rel:
        return repo_pack_rel.rstrip("/")
    return _DEFAULT_REVIEW_STATUS_DIR_REL


def _governed_pipeline_parked_at_checkpoint(
    repo_root: Path | None,
    *,
    governance=None,
    pipeline=None,
    current_tree_hash: str | None = None,
) -> bool:
    """Return True iff a governed remote-commit pipeline is holding the worktree.

    The exemption is narrow by design: the pipeline must carry a non-empty
    ``pipeline_id``, its ``state`` must be in the canonical parked-at-checkpoint
    set, its ``intent`` must declare both a ``staged_tree_hash`` and a
    ``staged_path_count >= 1``, AND the current git index tree hash must
    still match ``intent.staged_tree_hash`` so the parked snapshot has not
    drifted under the operator. Any looser shape falls through to normal
    enforcement.

    The pipeline artifact root is resolved via
    ``_resolve_commit_pipeline_root_rel`` so non-default product layouts
    that point ``ProjectGovernance.artifact_roots.review_root`` or the
    active repo-pack at a different review-status dir still find the
    canonical ``commit_pipeline.json``.

    Callers may inject ``pipeline`` and/or ``current_tree_hash`` directly
    for unit tests; otherwise both are read from the live repo. Unreadable
    or malformed artifacts fail closed by returning False (no exemption).
    """
    if pipeline is None:
        if repo_root is None:
            return False
        try:
            pipeline = _load_remote_commit_pipeline_contract(
                output_root=repo_root / _resolve_commit_pipeline_root_rel(governance),
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
    staged_tree_hash = getattr(intent, "staged_tree_hash", "") or ""
    if not staged_tree_hash:
        return False
    try:
        staged_path_count = int(getattr(intent, "staged_path_count", 0) or 0)
    except (TypeError, ValueError):
        return False
    if staged_path_count <= 0:
        return False
    # F18: bind the exemption to the current index tree hash so a drifted
    # worktree (edits landed after staging) does not get silently exempted.
    # ``vcs.commit`` would later reject the same drift as
    # ``staged_snapshot_changed``; this check stays consistent with that
    # contract by refusing the exemption when the hashes diverge.
    resolved_current = current_tree_hash
    if resolved_current is None:
        if repo_root is None:
            return False
        try:
            resolved_current = (_index_tree_hash(repo_root) or "").strip()
        except (OSError, ValueError):
            return False
    if not resolved_current or resolved_current != staged_tree_hash:
        return False
    return True


def collect_checkpoint_budget_errors(gov) -> list[str]:
    """Return fail-closed errors when the worktree is over the continuation budget."""
    if os.environ.get(_COMMIT_GATE_BYPASS_ENV, "").strip() == "1":
        return []  # commit gate bypass — the checkpoint commit is the budget repair action
    push = gov.push_enforcement
    if push.checkpoint_required or not push.safe_to_continue_editing:
        return [
            "Startup authority is over budget: "
            f"checkpoint_required={push.checkpoint_required}, "
            f"safe_to_continue_editing={push.safe_to_continue_editing}, "
            f"reason={push.checkpoint_reason or 'worktree_budget_exceeded'}, "
            f"staged_path_count={getattr(push, 'staged_path_count', 0)}, "
            f"unstaged_path_count={getattr(push, 'unstaged_path_count', 0)}."
        ]
    return []
def collect_post_checkpoint_dirty_worktree_errors(
    gov,
    *,
    repo_root: Path | None = None,
    pipeline=None,
    current_tree_hash: str | None = None,
) -> list[str]:
    """Return fail-closed errors when a local checkpoint exists but the worktree is dirty again.

    The normal enforcement still demands a clean worktree after a checkpoint.
    The one narrow exemption is a governed remote-commit pipeline that is
    intentionally parked at the checkpoint/approval boundary AND whose
    frozen ``intent.staged_tree_hash`` still matches the current git index
    tree hash. In that case the dirty worktree IS the staged snapshot the
    pipeline is landing, and flagging ``commit_before_push`` here would
    collide with the very step that is trying to commit. The exemption is
    gated by the typed pipeline contract loaded from the resolved
    review-status dir (``ProjectGovernance.artifact_roots.review_root`` ->
    repo-pack override -> hard fallback) and by a tree-hash bind-check so
    a drifted worktree (edits landed after staging) is NOT exempted. Any
    other dirty-after-checkpoint shape still fails closed.

    Tests may inject ``pipeline`` and/or ``current_tree_hash`` directly to
    bypass live git/policy reads.
    """
    if os.environ.get(_COMMIT_GATE_BYPASS_ENV, "").strip() == "1":
        return []  # devctl commit gate bypass — see module-level comment (LIVE_RUN Q1)
    push = gov.push_enforcement
    ahead = getattr(push, "ahead_of_upstream_commits", None)
    if not isinstance(ahead, int) or ahead <= 0:
        return []
    if not getattr(push, "worktree_dirty", False):
        return []
    if (repo_root is not None or pipeline is not None) and (
        _governed_pipeline_parked_at_checkpoint(
            repo_root,
            governance=gov,
            pipeline=pipeline,
            current_tree_hash=current_tree_hash,
        )
    ):
        return []
    return [
        "Startup authority detected a dirty worktree after a local checkpoint: "
        f"ahead_of_upstream_commits={ahead}, "
        f"dirty_path_count={getattr(push, 'dirty_path_count', 0)}, "
        f"untracked_path_count={getattr(push, 'untracked_path_count', 0)}, "
        f"staged_path_count={getattr(push, 'staged_path_count', 0)}, "
        f"unstaged_path_count={getattr(push, 'unstaged_path_count', 0)}, "
        f"recommended_action={getattr(push, 'recommended_action', '') or 'checkpoint_before_continue'}."
    ]


def collect_concurrent_writer_errors(
    repo_root: Path,
    gov,
    *,
    review_state=None,
) -> list[str]:
    """Return fail-closed errors when typed peer activity overlaps outside-scope dirt."""
    if os.environ.get(_COMMIT_GATE_BYPASS_ENV, "").strip() == "1":
        return []  # commit gate bypass — LIVE_RUN Q1/Q30
    resolved_review_state = review_state
    if resolved_review_state is None:
        try:
            resolved_review_state = _load_current_review_state(
                repo_root,
                governance=gov,
            )
        except (AttributeError, OSError, ValueError):
            resolved_review_state = None
    ownership = _build_work_intake_ownership_state(
        repo_root=repo_root,
        review_state=resolved_review_state,
    )
    coordination = _build_work_intake_coordination_state(
        governance=gov,
        review_state=resolved_review_state,
        ownership=ownership,
    )
    if ownership.status == "concurrent_writer_activity":
        outside_paths = ", ".join(ownership.outside_scope_dirty_paths[:4]) or "unknown"
        live_agents = ", ".join(ownership.live_agents[:4]) or "unknown"
        return [
            "Startup authority detected concurrent writer activity: "
            f"outside_scope_dirty_paths={outside_paths}, "
            f"live_agents={live_agents}, "
            f"scope_source={ownership.scope_source or 'unknown'}."
        ]
    if coordination.concurrent_writer_conflict_detected:
        duplicate_worktrees = ", ".join(
            coordination.duplicate_delegated_worktrees[:4]
        ) or "unknown"
        delegated_agents = ", ".join(coordination.delegated_agents[:4]) or "unknown"
        return [
            "Startup authority detected concurrent writer activity: "
            f"duplicate_delegated_worktrees={duplicate_worktrees}, "
            f"delegated_agents={delegated_agents}."
        ]
    return []
def collect_reviewer_loop_block_errors(
    repo_root: Path,
    gov,
    *,
    intent: str = _IMPLEMENTATION_STRICT_INTENT,
    reviewer_gate=None,
) -> list[str]:
    """Return fail-closed errors when the active reviewer loop blocks implementation."""
    if os.environ.get(_COMMIT_GATE_BYPASS_ENV, "").strip() == "1":
        return []  # commit gate bypass — local checkpoint must not depend on live reviewer freshness
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
