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

from .runtime_import_atomicity import (
    collect_import_index_atomicity_finding_records,
    collect_import_index_atomicity_findings,
)
from .runtime_push_checks import collect_push_decision_contract_errors
from .runtime_reviewer_loop import collect_reviewer_loop_block_errors

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
_checkpoint_budget_shape = import_repo_module(
    "dev.scripts.devctl.runtime.checkpoint_budget_shape",
    repo_root=REPO_ROOT,
)
CheckpointBudgetShape = _checkpoint_budget_shape.CheckpointBudgetShape
CHECKPOINT_BUDGET_COMMIT_GATE_BYPASS = (
    _checkpoint_budget_shape.CHECKPOINT_BUDGET_COMMIT_GATE_BYPASS
)
CHECKPOINT_BUDGET_PIPELINE_DRIFTED = (
    _checkpoint_budget_shape.CHECKPOINT_BUDGET_PIPELINE_DRIFTED
)
CHECKPOINT_BUDGET_PIPELINE_INCOMPLETE = (
    _checkpoint_budget_shape.CHECKPOINT_BUDGET_PIPELINE_INCOMPLETE
)
CHECKPOINT_BUDGET_RAW_EXCEEDED = _checkpoint_budget_shape.CHECKPOINT_BUDGET_RAW_EXCEEDED
CHECKPOINT_BUDGET_TYPED_PIPELINE = (
    _checkpoint_budget_shape.CHECKPOINT_BUDGET_TYPED_PIPELINE
)
CHECKPOINT_BUDGET_WITHIN_BUDGET = (
    _checkpoint_budget_shape.CHECKPOINT_BUDGET_WITHIN_BUDGET
)
CHECKPOINT_NEXT_ACTION_CUT_CHECKPOINT = (
    _checkpoint_budget_shape.CHECKPOINT_NEXT_ACTION_CUT_CHECKPOINT
)
CHECKPOINT_NEXT_ACTION_GOVERNED_COMMIT = (
    _checkpoint_budget_shape.CHECKPOINT_NEXT_ACTION_GOVERNED_COMMIT
)
CHECKPOINT_NEXT_ACTION_NONE = _checkpoint_budget_shape.CHECKPOINT_NEXT_ACTION_NONE
CHECKPOINT_NEXT_ACTION_REPAIR = _checkpoint_budget_shape.CHECKPOINT_NEXT_ACTION_REPAIR
CHECKPOINT_NEXT_ACTION_RUN_VALIDATION = (
    _checkpoint_budget_shape.CHECKPOINT_NEXT_ACTION_RUN_VALIDATION
)
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


def classify_checkpoint_budget_shape(
    gov,
    *,
    repo_root: Path | None = None,
    pipeline=None,
    current_tree_hash: str | None = None,
) -> CheckpointBudgetShape:
    """Classify checkpoint pressure using typed pipeline evidence when present."""
    push = gov.push_enforcement
    checkpoint_required = bool(getattr(push, "checkpoint_required", False))
    safe_to_continue = bool(getattr(push, "safe_to_continue_editing", True))
    base = _checkpoint_budget_shape_base(
        push,
        checkpoint_required=checkpoint_required,
        safe_to_continue=safe_to_continue,
    )
    if os.environ.get(_COMMIT_GATE_BYPASS_ENV, "").strip() == "1":
        return CheckpointBudgetShape(
            **base,
            state=CHECKPOINT_BUDGET_COMMIT_GATE_BYPASS,
            reason="commit_gate_bypass",
            bootstrap_blocked=False,
            next_required_action=CHECKPOINT_NEXT_ACTION_NONE,
        )
    if not (checkpoint_required or not safe_to_continue):
        return CheckpointBudgetShape(
            **base,
            state=CHECKPOINT_BUDGET_WITHIN_BUDGET,
            reason=getattr(push, "checkpoint_reason", "") or "within_budget",
            bootstrap_blocked=False,
            next_required_action=CHECKPOINT_NEXT_ACTION_NONE,
        )

    resolved_pipeline = _resolve_checkpoint_budget_pipeline(
        repo_root,
        governance=gov,
        pipeline=pipeline,
    )
    if resolved_pipeline is None:
        return CheckpointBudgetShape(
            **base,
            state=CHECKPOINT_BUDGET_RAW_EXCEEDED,
            reason=getattr(push, "checkpoint_reason", "") or "worktree_budget_exceeded",
            bootstrap_blocked=True,
            next_required_action=CHECKPOINT_NEXT_ACTION_CUT_CHECKPOINT,
            errors=("no governed checkpoint pipeline evidence was found",),
        )

    pipeline_fields = _checkpoint_pipeline_fields(
        resolved_pipeline,
        repo_root=repo_root,
        current_tree_hash=current_tree_hash,
    )
    errors = _checkpoint_pipeline_shape_errors(pipeline_fields)
    if errors:
        return CheckpointBudgetShape(
            **base,
            **pipeline_fields,
            state=(
                CHECKPOINT_BUDGET_PIPELINE_DRIFTED
                if pipeline_fields.get("staged_tree_hash")
                and pipeline_fields.get("current_tree_hash")
                and not pipeline_fields.get("tree_hash_match")
                else CHECKPOINT_BUDGET_PIPELINE_INCOMPLETE
            ),
            reason=getattr(push, "checkpoint_reason", "") or "worktree_budget_exceeded",
            bootstrap_blocked=True,
            next_required_action=CHECKPOINT_NEXT_ACTION_CUT_CHECKPOINT,
            errors=tuple(errors),
        )

    return CheckpointBudgetShape(
        **base,
        **pipeline_fields,
        state=CHECKPOINT_BUDGET_TYPED_PIPELINE,
        reason=getattr(push, "checkpoint_reason", "") or "typed_checkpoint_pipeline",
        bootstrap_blocked=False,
        next_required_action=_checkpoint_pipeline_next_action(resolved_pipeline),
        errors=(),
    )


def collect_checkpoint_budget_errors(
    gov,
    *,
    repo_root: Path | None = None,
    pipeline=None,
    current_tree_hash: str | None = None,
    shape: CheckpointBudgetShape | None = None,
) -> list[str]:
    """Return fail-closed errors when the worktree is over the continuation budget."""
    resolved_shape = shape or classify_checkpoint_budget_shape(
        gov,
        repo_root=repo_root,
        pipeline=pipeline,
        current_tree_hash=current_tree_hash,
    )
    if resolved_shape.state == CHECKPOINT_BUDGET_COMMIT_GATE_BYPASS:
        return []  # commit gate bypass — the checkpoint commit is the budget repair action
    if resolved_shape.bootstrap_blocked:
        push = gov.push_enforcement
        evidence = (
            f", pipeline_id={resolved_shape.pipeline_id}, "
            f"pipeline_state={resolved_shape.pipeline_state}, "
            f"shape={resolved_shape.state}"
            if resolved_shape.pipeline_id
            else f", shape={resolved_shape.state}"
        )
        detail = (
            f", evidence_errors={'; '.join(resolved_shape.errors)}"
            if resolved_shape.errors
            else ""
        )
        return [
            "Startup authority is over budget: "
            f"checkpoint_required={resolved_shape.checkpoint_required}, "
            f"safe_to_continue_editing={resolved_shape.safe_to_continue_editing}, "
            f"reason={push.checkpoint_reason or 'worktree_budget_exceeded'}, "
            f"staged_path_count={resolved_shape.staged_path_count}, "
            f"unstaged_path_count={resolved_shape.unstaged_path_count}"
            f"{evidence}{detail}."
        ]
    return []


def _checkpoint_budget_shape_base(
    push,
    *,
    checkpoint_required: bool,
    safe_to_continue: bool,
) -> dict[str, object]:
    return {
        "checkpoint_required": checkpoint_required,
        "safe_to_continue_editing": safe_to_continue,
        "staged_path_count": _coerce_nonnegative_int(
            getattr(push, "staged_path_count", 0)
        ),
        "unstaged_path_count": _coerce_nonnegative_int(
            getattr(push, "unstaged_path_count", 0)
        ),
        "dirty_path_count": _coerce_nonnegative_int(
            getattr(push, "dirty_path_count", 0)
        ),
        "untracked_path_count": _coerce_nonnegative_int(
            getattr(push, "untracked_path_count", 0)
        ),
    }


def _resolve_checkpoint_budget_pipeline(
    repo_root: Path | None,
    *,
    governance=None,
    pipeline=None,
):
    if pipeline is not None:
        return pipeline
    if repo_root is None:
        return None
    try:
        loaded = _load_remote_commit_pipeline_contract(
            output_root=repo_root / _resolve_commit_pipeline_root_rel(governance),
        )
    except (OSError, ValueError):
        return None
    if not getattr(loaded, "pipeline_id", ""):
        return None
    return loaded


def _checkpoint_pipeline_fields(
    pipeline,
    *,
    repo_root: Path | None,
    current_tree_hash: str | None,
) -> dict[str, object]:
    intent = getattr(pipeline, "intent", None)
    staged_tree_hash = getattr(intent, "staged_tree_hash", "") if intent else ""
    staged_tree_hash = str(staged_tree_hash or "").strip()
    pipeline_staged_path_count = _coerce_nonnegative_int(
        getattr(intent, "staged_path_count", 0) if intent else 0
    )
    resolved_current_hash = _resolve_checkpoint_current_tree_hash(
        repo_root,
        current_tree_hash=current_tree_hash,
    )
    guard_result = getattr(pipeline, "guard_result", None)
    validation_receipt = getattr(pipeline, "validation_receipt", None)
    guard_action_id = str(
        getattr(guard_result, "action_id", "")
        or getattr(pipeline, "guard_action_id", "")
        or ""
    ).strip()
    validation_receipt_id = str(
        getattr(validation_receipt, "receipt_id", "") or ""
    ).strip()
    validation_staged_tree_hash = str(
        getattr(validation_receipt, "staged_tree_hash", "") or ""
    ).strip()
    validation_checkpoint_sufficient = bool(
        getattr(validation_receipt, "checkpoint_sufficient", False)
    ) and (
        not validation_staged_tree_hash
        or validation_staged_tree_hash == staged_tree_hash
    )
    return {
        "pipeline_id": str(getattr(pipeline, "pipeline_id", "") or "").strip(),
        "pipeline_state": str(getattr(pipeline, "state", "") or "").strip(),
        "pipeline_staged_path_count": pipeline_staged_path_count,
        "staged_tree_hash": staged_tree_hash,
        "current_tree_hash": resolved_current_hash,
        "tree_hash_match": bool(
            staged_tree_hash
            and resolved_current_hash
            and staged_tree_hash == resolved_current_hash
        ),
        "typed_pipeline_parked": (
            str(getattr(pipeline, "state", "") or "").strip()
            in _PIPELINE_PARKED_AT_CHECKPOINT_STATES
        ),
        "receipt_backed": bool(guard_action_id or validation_receipt_id),
        "guard_action_id": guard_action_id,
        "guard_status": str(getattr(guard_result, "status", "") or "").strip(),
        "guard_ok": bool(getattr(guard_result, "ok", False)),
        "validation_receipt_id": validation_receipt_id,
        "validation_receipt_status": str(
            getattr(validation_receipt, "status", "") or ""
        ).strip(),
        "validation_checkpoint_sufficient": validation_checkpoint_sufficient,
    }


def _checkpoint_pipeline_shape_errors(fields: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if not fields.get("pipeline_id"):
        errors.append("pipeline_id is empty")
    if not fields.get("typed_pipeline_parked"):
        errors.append(
            "pipeline state is not parked at the governed checkpoint boundary"
        )
    if not fields.get("staged_tree_hash"):
        errors.append("pipeline staged_tree_hash is empty")
    if _coerce_nonnegative_int(fields.get("pipeline_staged_path_count", 0)) <= 0:
        errors.append("pipeline staged_path_count is empty")
    if not fields.get("current_tree_hash"):
        errors.append("current index tree hash is unavailable")
    if (
        fields.get("staged_tree_hash")
        and fields.get("current_tree_hash")
        and not fields.get("tree_hash_match")
    ):
        errors.append("current index tree hash differs from pipeline staged_tree_hash")
    return errors


def _checkpoint_pipeline_next_action(pipeline) -> str:
    validation_receipt = getattr(pipeline, "validation_receipt", None)
    if (
        validation_receipt is not None
        and bool(getattr(validation_receipt, "checkpoint_sufficient", False))
    ):
        return CHECKPOINT_NEXT_ACTION_GOVERNED_COMMIT
    guard_result = getattr(pipeline, "guard_result", None)
    if guard_result is None:
        return CHECKPOINT_NEXT_ACTION_RUN_VALIDATION
    if bool(getattr(guard_result, "ok", False)):
        return CHECKPOINT_NEXT_ACTION_GOVERNED_COMMIT
    return CHECKPOINT_NEXT_ACTION_REPAIR


def _resolve_checkpoint_current_tree_hash(
    repo_root: Path | None,
    *,
    current_tree_hash: str | None,
) -> str:
    if current_tree_hash is not None:
        return str(current_tree_hash or "").strip()
    if repo_root is None:
        return ""
    try:
        return str(_index_tree_hash(repo_root) or "").strip()
    except (OSError, ValueError):
        return ""


def _coerce_nonnegative_int(value: object) -> int:
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return max(parsed, 0)


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
