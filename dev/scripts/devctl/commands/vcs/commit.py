"""Governed commit command backed by the typed remote/local pipeline."""

from __future__ import annotations

from pathlib import Path

from ...config import REPO_ROOT
from ...governance.push_policy import load_push_policy
from ...runtime.governance_scan import scan_repo_governance_safely
from ...runtime.review_snapshot_refresh import receipt_commit_parent_sha
from ...runtime.commit_permission import build_commit_permission_decision_for_executor
from .commit_caller_role import caller_role_report
from .commit_action_result_report import action_result_report_fields
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
from .commit_preflight import (
    apply_explicit_operator_approval,
    ensure_pipeline_approval,
    load_pipeline_for_explicit_approval,
    prepare_pipeline,
    resolve_commit_approval_authority,
    resolve_interaction_mode,
)
from .commit_visibility import commit_visibility_payload
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


def _report_commit_shas(
    *,
    repo_root: Path,
    commit_sha: str,
) -> tuple[str, str]:
    """Return ``(content_commit_sha, receipt_commit_sha)`` for reporting."""
    head_sha = str(commit_sha or "").strip()
    if not head_sha:
        return "", ""
    try:
        governance = scan_repo_governance_safely(repo_root)
    except (OSError, ValueError):
        governance = None
    content_sha = receipt_commit_parent_sha(
        repo_root=repo_root,
        current_head=head_sha,
        governance=governance,
    )
    if content_sha and content_sha != head_sha:
        return content_sha, head_sha
    return head_sha, ""


def _commit_permission_report(vcs_executor: GovernedVcsExecutor) -> dict[str, object] | None:
    """Return a blocking report if startup authority denies governed commit."""
    decision, load_error = build_commit_permission_decision_for_executor(vcs_executor)
    if decision.commit_permission != "blocked":
        return None
    next_command = str(decision.next_command or "").strip()
    guidance = "Run the reported next_command before staging or committing."
    if next_command:
        guidance = f"Run `{next_command}` before staging or committing."
    if load_error:
        guidance = (
            f"Startup authority could not be loaded for the commit gate: {load_error}. "
            "Rerun startup-context and repair blockers before requesting a commit."
        )
    return _build_report(
        status="blocked",
        reason="commit_permission_blocked",
        commit_permission=decision.to_dict(),
        blockers=list(decision.blockers),
        next_command=next_command,
        allowed_actions=list(decision.allowed_actions),
        blocked_actions=list(decision.blocked_actions),
        recovery_action=decision.recovery_action,
        escalation_action=decision.escalation_action,
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
                "The governed commit path only supports `--allow-empty`, "
                "`--no-edit`, and `--amend`."
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
    approve_pending = bool(getattr(args, "approve_pending", False))
    stage_warnings: list[str] = []
    if approve_pending:
        pipeline, preflight_report = load_pipeline_for_explicit_approval(
            repo_root=repo_root,
            vcs_executor=vcs_executor,
        )
    else:
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
            guard_action_result = pipeline.guard_result
            report = _build_report(
                status="blocked",
                reason="guard_bundle_failed",
                guard_exit_code=guard_rc,
                pipeline_id=pipeline.pipeline_id,
                pipeline_state=pipeline.state,
                approval_state=pipeline.approval_state,
                **commit_visibility_payload(pipeline),
                **(
                    action_result_report_fields(guard_action_result)
                    if guard_action_result is not None
                    else _empty_action_result_report()
                ),
                warnings=stage_warnings,
            )
            _emit_report(args, report)
            return 1

    approval_authority = resolve_commit_approval_authority(
        repo_root,
        interaction_mode_override=interaction_mode,
    )
    resolved_mode = approval_authority.interaction_mode
    if approve_pending:
        pipeline, approval_report = apply_explicit_operator_approval(
            vcs_executor=vcs_executor,
            pipeline=pipeline,
            approval_authority=approval_authority,
            stage_warnings=stage_warnings,
        )
    else:
        pipeline, approval_report = ensure_pipeline_approval(
            vcs_executor=vcs_executor,
            pipeline=pipeline,
            approval_authority=approval_authority,
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
    commit_sha, receipt_commit_sha = _report_commit_shas(
        repo_root=repo_root,
        commit_sha=pipeline.commit_sha,
    )
    report = _build_report(
        status="committed" if commit_result.ok else "blocked",
        reason=commit_result.reason,
        pipeline_id=pipeline.pipeline_id,
        pipeline_state=pipeline.state,
        approval_state=pipeline.approval_state,
        **commit_visibility_payload(pipeline),
        commit_sha=commit_sha,
        receipt_commit_sha=receipt_commit_sha or None,
        receipt_projection_state=(
            "receipt_commit_recorded"
            if receipt_commit_sha
            else _receipt_projection_state(
                commit_ok=commit_result.ok,
                commit_sha=commit_sha,
            )
        ),
        action_result=commit_result.to_dict(),
        operator_guidance=commit_result.operator_guidance,
        interaction_mode=resolved_mode,
        warnings=[*stage_warnings, *commit_result.warnings],
    )
    _emit_report(args, report)
    return 0 if commit_result.ok else 1


def _receipt_projection_state(*, commit_ok: bool, commit_sha: str) -> str:
    """Return the report-only post-commit receipt/projection state."""
    if not commit_ok:
        return "not_started"
    if commit_sha:
        return "receipt_projection_pending_or_not_required"
    return "commit_not_recorded"


def _empty_action_result_report() -> dict[str, object]:
    return {
        "action_result": None,
        "reason_chain": [],
        "remediation": "",
        "auto_executable": False,
        "errors": [],
    }


def run(args) -> int:
    """Entry point for ``devctl commit``."""
    return run_commit(args)
