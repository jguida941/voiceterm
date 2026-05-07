"""Validation and staging helpers extracted from commit_preflight."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .commit_guard_bundle import GUARD_PROFILE
from .commit_preflight_atomicity import preflight_import_index_atomicity
from .commit_pipeline_blocking import build_active_pipeline_block_report
from .commit_pipeline_blocking import (
    auto_transition_non_destructive_push_failure,
)
from .commit_preflight_support import (
    COMMIT_START_COMMAND,
    next_command_guidance,
)
from .commit_preflight_stage_failure import StageFailureContext, stage_failure_report
from .commit_visibility import commit_visibility_payload
from .governed_executor import GovernedVcsExecutor
from .orphan_snapshot_advisory import append_orphan_snapshot_advisory
from .governed_executor_actions import (
    _build_report,
    build_stage_action,
)
from .governed_executor_commit_runtime import (
    post_commit_execution_handoff,
    post_commit_stage_handoff,
)
from .governed_executor_git import (
    dirty_paths,
    pipeline_is_stale_for_current_repo,
    staged_paths,
    unstaged_paths,
)
from .governed_executor_stage_snapshot import non_receipt_artifact_paths
from ...runtime.remote_commit_pipeline_state import BLOCKING_PIPELINE_STATES

_REUSABLE_PIPELINE_STATES = frozenset(
    {
        "staged",
        "guards_running",
        "guards_passed",
        "operator_approval_pending",
        "approved",
        "commit_pending",
    }
)
_PIPELINE_BLOCKING_STATES = BLOCKING_PIPELINE_STATES
_EXPLICIT_APPROVAL_PIPELINE_STATES = frozenset(
    {
        "guards_passed",
        "operator_approval_pending",
        "approved",
        "commit_pending",
    }
)


@dataclass(frozen=True, slots=True)
class CommitPreflightDeps:
    pipeline_is_stale_for_current_repo_fn: object = pipeline_is_stale_for_current_repo
    build_active_pipeline_block_report_fn: object = build_active_pipeline_block_report
    auto_transition_non_destructive_push_failure_fn: object = (
        auto_transition_non_destructive_push_failure
    )
    post_commit_execution_handoff_fn: object = post_commit_execution_handoff
    post_commit_stage_handoff_fn: object = post_commit_stage_handoff


def prepare_pipeline(
    *,
    args,
    repo_root: Path,
    resolved_policy,
    vcs_executor: GovernedVcsExecutor,
    action_request_grant: object | None = None,
    deps: CommitPreflightDeps | None = None,
):
    """Load or restage the governed pipeline before guard replay."""
    resolved_deps = deps or CommitPreflightDeps()
    selected_paths = _selected_stage_paths(args)
    stage_warnings: list[str] = []
    pipeline = vcs_executor.load_pipeline()
    stale_pipeline = resolved_deps.pipeline_is_stale_for_current_repo_fn(
        repo_root=repo_root,
        pipeline=pipeline,
    )
    if stale_pipeline:
        stage_warnings.append(
            "Ignoring stale governed pipeline "
            f"`{pipeline.pipeline_id}` while preparing a new checkpoint for the current repo state."
        )
    if (
        pipeline.pipeline_id
        and pipeline.state in _PIPELINE_BLOCKING_STATES
        and not stale_pipeline
    ):
        pipeline = _reload_after_auto_push_failure_transition(
            repo_root=repo_root,
            pipeline=pipeline,
            vcs_executor=vcs_executor,
            deps=resolved_deps,
        )
        if pipeline.state in _PIPELINE_BLOCKING_STATES:
            return pipeline, stage_warnings, (
                resolved_deps.build_active_pipeline_block_report_fn(
                    repo_root=repo_root,
                    pipeline=pipeline,
                )
            )

    if (
        not pipeline.pipeline_id
        or pipeline.state not in _REUSABLE_PIPELINE_STATES
        or stale_pipeline
    ):
        stage_result = vcs_executor.execute(
            build_stage_action(
                repo_pack_id=resolved_policy.repo_pack_id,
                paths=selected_paths,
                commit_message_draft=str(getattr(args, "message", "") or ""),
                push_requested=False,
                guard_profile=GUARD_PROFILE,
                work_intake_ref="devctl.commit",
                reuse_staged_index=_reuse_staged_index(
                    repo_root=repo_root,
                    selected_paths=selected_paths,
                    action_request_grant=action_request_grant,
                ),
                allow_empty=bool(
                    getattr(args, "passthrough", ())
                    and "--allow-empty" in getattr(args, "passthrough", ())
                ),
                requested_by="devctl.commit",
            )
        )
        pipeline = vcs_executor.load_pipeline()
        stage_warnings = list(stage_result.warnings)
        if not stage_result.ok:
            return (
                pipeline,
                stage_warnings,
                stage_failure_report(
                    StageFailureContext(
                        args=args,
                        repo_root=repo_root,
                        vcs_executor=vcs_executor,
                        deps=resolved_deps,
                        pipeline=pipeline,
                        stage_result=stage_result,
                        stale_pipeline=stale_pipeline,
                    )
                ),
            )
    stage_warnings, atomicity_report = preflight_import_index_atomicity(
        repo_root=repo_root,
        pipeline=pipeline,
        stage_warnings=stage_warnings,
    )
    if atomicity_report is not None:
        return pipeline, stage_warnings, atomicity_report
    append_orphan_snapshot_advisory(
        stage_warnings,
        repo_root=repo_root,
        scan_trigger="commit_preflight",
    )
    return pipeline, stage_warnings, None


def _selected_stage_paths(args) -> tuple[str, ...]:
    """Return explicit governed stage paths requested by ``devctl commit``."""
    paths = getattr(args, "paths", ()) or ()
    selected: list[str] = []
    seen: set[str] = set()
    for path in paths:
        text = str(path or "").strip()
        if text and text not in seen:
            selected.append(text)
            seen.add(text)
    return tuple(selected)


def _reuse_staged_index(
    *,
    repo_root: Path,
    selected_paths: tuple[str, ...],
    action_request_grant: object | None,
) -> bool:
    """Return whether stage should preserve an already-staged user index."""
    if selected_paths:
        return False
    if _grant_has_capability(action_request_grant, "repo.stage"):
        return False
    if _grant_has_capability(action_request_grant, "repo.stage_handoff"):
        return False
    try:
        staged = staged_paths(repo_root)
        dirty = dirty_paths(repo_root)
        unstaged = unstaged_paths(repo_root)
    except (OSError, ValueError):
        return True
    if dirty and not non_receipt_artifact_paths(repo_root=repo_root, paths=staged):
        return False
    if non_receipt_artifact_paths(repo_root=repo_root, paths=unstaged):
        return False
    return True


def _grant_has_capability(grant: object | None, capability: str) -> bool:
    if grant is None or not bool(getattr(grant, "authorized", False)):
        return False
    return capability in tuple(getattr(grant, "granted_capabilities", ()) or ())


def _reload_after_auto_push_failure_transition(
    *,
    repo_root: Path,
    pipeline,
    vcs_executor: GovernedVcsExecutor,
    deps: CommitPreflightDeps,
):
    transitioned = deps.auto_transition_non_destructive_push_failure_fn(
        repo_root=repo_root,
        pipeline=pipeline,
    )
    if not transitioned:
        return pipeline
    return vcs_executor.load_pipeline()


def load_pipeline_for_explicit_approval(
    *,
    repo_root: Path,
    vcs_executor: GovernedVcsExecutor,
    deps: CommitPreflightDeps | None = None,
):
    """Return the existing governed pipeline for explicit operator approval."""
    resolved_deps = deps or CommitPreflightDeps()
    pipeline = vcs_executor.load_pipeline()
    if not pipeline.pipeline_id:
        return pipeline, _build_report(
            status="blocked",
            reason="no_pending_pipeline_to_approve",
            **commit_visibility_payload(pipeline),
            recommended_next_action="stage_commit_pipeline",
            next_command=COMMIT_START_COMMAND,
            operator_guidance=next_command_guidance(COMMIT_START_COMMAND),
        )
    if resolved_deps.pipeline_is_stale_for_current_repo_fn(
        repo_root=repo_root,
        pipeline=pipeline,
    ):
        return pipeline, _build_report(
            status="blocked",
            reason="pending_pipeline_stale_for_current_repo",
            pipeline_id=pipeline.pipeline_id,
            pipeline_state=pipeline.state,
            approval_state=pipeline.approval_state,
            **commit_visibility_payload(pipeline),
            recommended_next_action="stage_commit_pipeline",
            next_command=COMMIT_START_COMMAND,
            operator_guidance=next_command_guidance(COMMIT_START_COMMAND),
        )
    if pipeline.state in _PIPELINE_BLOCKING_STATES:
        return pipeline, resolved_deps.build_active_pipeline_block_report_fn(
            repo_root=repo_root,
            pipeline=pipeline,
        )
    if pipeline.state not in _EXPLICIT_APPROVAL_PIPELINE_STATES:
        return pipeline, _build_report(
            status="blocked",
            reason="pipeline_not_waiting_for_operator_approval",
            pipeline_id=pipeline.pipeline_id,
            pipeline_state=pipeline.state,
            approval_state=pipeline.approval_state,
            **commit_visibility_payload(pipeline),
            operator_guidance=(
                "Only guarded pipelines awaiting or holding approval may be "
                "resumed with `devctl commit --approve-pending`."
            ),
        )
    return pipeline, None
