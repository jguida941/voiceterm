"""Governed commit command backed by the typed remote/local pipeline."""

from __future__ import annotations

from pathlib import Path

from ...config import REPO_ROOT
from ...governance.push_policy import load_push_policy
from ...runtime.commit_permission import build_commit_permission_decision_for_executor
from .commit_caller_role import caller_role_report
from .commit_guard_bundle import (
    _pipeline_has_validation_plan,
    guard_result,
    pipeline_has_checkpoint_snapshot as _pipeline_has_checkpoint_snapshot,
    run_guard_bundle,
)
from .commit_guard_replay import (
    pipeline_needs_guard_replay,
    replay_pipeline_guards,
)
from .commit_preflight import ensure_pipeline_approval, prepare_pipeline, resolve_interaction_mode
from .commit_passthrough import (
    CommitPassthrough,
    build_git_commit_cmd as _build_git_commit_cmd,
    parse_passthrough as _parse_passthrough,
)
from .governed_executor import GovernedVcsExecutor
from .governed_executor_actions import _build_report, _emit_report, build_commit_action

# Compatibility re-export while commit guard helpers live in their own module.
_run_guard_bundle = run_guard_bundle
_resolve_interaction_mode = resolve_interaction_mode


def _commit_permission_report(vcs_executor: GovernedVcsExecutor) -> dict[str, object] | None:
    """Return a blocking report if startup authority denies governed commit."""
    decision, load_error = build_commit_permission_decision_for_executor(vcs_executor)
    if decision.commit_permission != "blocked":
        return None
    guidance = "Run the reported next_command before staging or committing."
    if load_error:
        guidance = (
            f"Startup authority could not be loaded for the commit gate: {load_error}. "
            "Rerun startup-context and repair blockers before requesting a commit."
        )
    return _build_report(
        status="blocked",
        reason="commit_permission_blocked",
        commit_permission=decision.to_dict(),
        operator_guidance=guidance,
    )


def run_commit(
    args,
    *,
    repo_root: Path = REPO_ROOT,
    guard_runner=None,
    policy=None,
    executor: GovernedVcsExecutor | None = None,
    interaction_mode: str | None = None,
) -> int:
    """Run governed commit through the typed remote/local pipeline."""
    passthrough = _parse_passthrough(args)
    if passthrough.unsupported:
        report = _build_report(
            status="blocked",
            reason="unsupported_passthrough",
            unsupported_passthrough=list(passthrough.unsupported),
            guidance=(
                "Stage the exact paths first, then rerun `devctl commit`. "
                "The governed commit path only supports `--allow-empty` and "
                "`--no-edit`."
            ),
        )
        _emit_report(args, report)
        return 1

    resolved_policy = policy or load_push_policy(repo_root=repo_root)
    vcs_executor = executor or GovernedVcsExecutor(
        repo_root=repo_root,
        push_policy=resolved_policy,
    )
    role_report = caller_role_report(args)
    if role_report is not None:
        _emit_report(args, role_report)
        return 1
    permission_report = _commit_permission_report(vcs_executor)
    if permission_report is not None:
        _emit_report(args, permission_report)
        return 1
    pipeline, stage_warnings, preflight_report = prepare_pipeline(
        args=args,
        repo_root=repo_root,
        resolved_policy=resolved_policy,
        vcs_executor=vcs_executor,
    )
    if preflight_report is not None:
        _emit_report(args, preflight_report)
        return 1

    if pipeline_needs_guard_replay(pipeline):
        guard_rc, pipeline = replay_pipeline_guards(
            vcs_executor=vcs_executor,
            repo_root=repo_root,
            guard_runner=guard_runner,
            pipeline=pipeline,
        )
        if guard_rc != 0:
            report = _build_report(
                status="blocked",
                reason="guard_bundle_failed",
                guard_exit_code=guard_rc,
                pipeline_id=pipeline.pipeline_id,
                pipeline_state=pipeline.state,
                warnings=stage_warnings,
            )
            _emit_report(args, report)
            return 1

    resolved_mode = interaction_mode or resolve_interaction_mode(repo_root)
    pipeline, approval_report = ensure_pipeline_approval(
        vcs_executor=vcs_executor,
        pipeline=pipeline,
        resolved_mode=resolved_mode,
        stage_warnings=stage_warnings,
    )
    if approval_report is not None:
        _emit_report(args, approval_report)
        return 1

    commit_result = vcs_executor.execute(
        build_commit_action(
            repo_pack_id=resolved_policy.repo_pack_id,
            pipeline_id=vcs_executor.load_pipeline().pipeline_id,
            commit_message_draft=str(getattr(args, "message", "") or ""),
            amend=bool(getattr(args, "amend", False)),
            allow_empty=passthrough.allow_empty,
            no_edit=passthrough.no_edit,
            requested_by="devctl.commit",
        )
    )
    pipeline = vcs_executor.load_pipeline()
    report = _build_report(
        status="committed" if commit_result.ok else "blocked",
        reason=commit_result.reason,
        pipeline_id=pipeline.pipeline_id,
        pipeline_state=pipeline.state,
        approval_state=pipeline.approval_state,
        commit_sha=pipeline.commit_sha,
        operator_guidance=commit_result.operator_guidance,
        interaction_mode=resolved_mode,
        warnings=[*stage_warnings, *commit_result.warnings],
    )
    _emit_report(args, report)
    return 0 if commit_result.ok else 1


def run(args) -> int:
    """Entry point for ``devctl commit``."""
    return run_commit(args)
