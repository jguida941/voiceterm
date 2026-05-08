"""Main governed commit flow after entrypoint authority gates pass."""

from __future__ import annotations

from pathlib import Path

from ...runtime.governance_scan import scan_repo_governance_safely
from ...runtime.review_snapshot_refresh import receipt_commit_parent_sha
from .commit_action_request_runtime import (
    emit_action_request_block_report,
    finalize_commit_action_request,
)
from .commit_action_result_report import action_result_report_fields
from .commit_guard_replay import pipeline_needs_guard_replay, replay_pipeline_guards
from .commit_preflight import (
    apply_explicit_operator_approval,
    ensure_pipeline_approval,
    load_pipeline_for_explicit_approval,
    prepare_pipeline,
    resolve_commit_approval_authority,
)
from .commit_visibility import commit_visibility_payload
from .governed_executor_actions import _build_report, build_commit_action
from .progress import emit_vcs_progress


def run_commit_pipeline_flow(
    *,
    args,
    repo_root: Path,
    resolved_policy,
    vcs_executor,
    guard_runner,
    passthrough,
    action_request_grant,
    interaction_mode: str | None,
    emit_report,
) -> int:
    """Run staging, guards, approval, commit, and action-request finalization."""
    approve_pending = bool(getattr(args, "approve_pending", False))
    if approve_pending and tuple(getattr(args, "paths", ()) or ()):
        emit_action_request_block_report(
            args=args,
            repo_root=repo_root,
            grant=action_request_grant,
            report=_paths_with_approve_pending_report(),
            reason="paths_not_allowed_with_approve_pending",
            emit_report=emit_report,
        )
        return 1

    emit_vcs_progress("commit.prepare_pipeline", "staging snapshot and preflight inputs")
    pipeline, stage_warnings, preflight_report = _prepare_commit_pipeline(
        args=args,
        repo_root=repo_root,
        resolved_policy=resolved_policy,
        vcs_executor=vcs_executor,
        approve_pending=approve_pending,
        action_request_grant=action_request_grant,
    )
    if preflight_report is not None:
        emit_action_request_block_report(
            args=args,
            repo_root=repo_root,
            grant=action_request_grant,
            report=preflight_report,
            reason=str(preflight_report.get("reason") or "commit_preflight_blocked"),
            emit_report=emit_report,
        )
        return 1

    emit_vcs_progress("commit.guard_replay", "checking guard replay requirements")
    replay_report = _replay_guard_report(
        vcs_executor=vcs_executor,
        repo_root=repo_root,
        guard_runner=guard_runner,
        pipeline=pipeline,
        stage_warnings=stage_warnings,
    )
    if replay_report is not None:
        emit_action_request_block_report(
            args=args,
            repo_root=repo_root,
            grant=action_request_grant,
            report=replay_report,
            reason="guard_bundle_failed",
            emit_report=emit_report,
        )
        return 1
    pipeline = vcs_executor.load_pipeline()

    emit_vcs_progress("commit.approval", "resolving operator approval state")
    pipeline, resolved_mode, approval_report = _ensure_commit_approval(
        repo_root=repo_root,
        vcs_executor=vcs_executor,
        pipeline=pipeline,
        approve_pending=approve_pending,
        interaction_mode=interaction_mode,
        stage_warnings=stage_warnings,
    )
    if approval_report is not None:
        emit_action_request_block_report(
            args=args,
            repo_root=repo_root,
            grant=action_request_grant,
            report=approval_report,
            reason=str(approval_report.get("reason") or "approval_blocked"),
            emit_report=emit_report,
        )
        return 1

    emit_vcs_progress("commit.execute", "running approved commit action")
    commit_result = vcs_executor.execute(
        build_commit_action(
            repo_pack_id=resolved_policy.repo_pack_id,
            pipeline_id=vcs_executor.load_pipeline().pipeline_id,
            commit_message_draft=str(getattr(args, "message", "") or ""),
            amend=bool(getattr(args, "amend", False)),
            allow_empty=passthrough.allow_empty,
            no_edit=passthrough.no_edit,
            action_request_packet_id=(
                str(getattr(action_request_grant, "packet_id", "") or "")
                if action_request_grant is not None
                else ""
            ),
            action_request_target_agent=(
                str(getattr(action_request_grant, "target_agent", "") or "")
                if action_request_grant is not None
                else ""
            ),
            requested_by="devctl.commit",
        )
    )
    emit_vcs_progress("commit.reconcile", "reloading pipeline and resolving receipt head")
    pipeline = vcs_executor.load_pipeline()
    commit_sha, receipt_commit_sha = report_commit_shas(
        repo_root=repo_root,
        commit_sha=pipeline.commit_sha,
    )
    action_request_grant, report_reason, _, action_request_ok = (
        finalize_commit_action_request(
            repo_root=repo_root,
            grant=action_request_grant,
            pipeline=pipeline,
            commit_result=commit_result,
            commit_sha=commit_sha,
        )
    )
    report_status = "committed" if commit_result.ok and action_request_ok else "blocked"
    emit_vcs_progress("commit.report", f"emitting governed commit report status={report_status}")
    emit_report(
        args,
        _commit_report(
            status=report_status,
            reason=report_reason,
            pipeline=pipeline,
            commit_result=commit_result,
            commit_sha=commit_sha,
            receipt_commit_sha=receipt_commit_sha,
            resolved_mode=resolved_mode,
            action_request_grant=action_request_grant,
            stage_warnings=stage_warnings,
        ),
    )
    return 0 if commit_result.ok and action_request_ok else 1


def report_commit_shas(*, repo_root: Path, commit_sha: str) -> tuple[str, str]:
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


def _prepare_commit_pipeline(
    *,
    args,
    repo_root: Path,
    resolved_policy,
    vcs_executor,
    approve_pending: bool,
    action_request_grant,
):
    if approve_pending:
        pipeline, preflight_report = load_pipeline_for_explicit_approval(
            repo_root=repo_root,
            vcs_executor=vcs_executor,
        )
        return pipeline, [], preflight_report
    return prepare_pipeline(
        args=args,
        repo_root=repo_root,
        resolved_policy=resolved_policy,
        vcs_executor=vcs_executor,
        action_request_grant=action_request_grant,
    )


def _replay_guard_report(
    *,
    vcs_executor,
    repo_root: Path,
    guard_runner,
    pipeline,
    stage_warnings: list[str],
) -> dict[str, object] | None:
    if not pipeline_needs_guard_replay(pipeline):
        return None
    guard_rc, pipeline = replay_pipeline_guards(
        vcs_executor=vcs_executor,
        repo_root=repo_root,
        guard_runner=guard_runner,
        pipeline=pipeline,
    )
    if guard_rc == 0:
        return None
    guard_action_result = pipeline.guard_result
    return _build_report(
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


def _ensure_commit_approval(
    *,
    repo_root: Path,
    vcs_executor,
    pipeline,
    approve_pending: bool,
    interaction_mode: str | None,
    stage_warnings: list[str],
):
    approval_authority = resolve_commit_approval_authority(
        repo_root,
        interaction_mode_override=interaction_mode,
    )
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
    return pipeline, approval_authority.interaction_mode, approval_report


def _commit_report(
    *,
    status: str,
    reason: str,
    pipeline,
    commit_result,
    commit_sha: str,
    receipt_commit_sha: str,
    resolved_mode: str,
    action_request_grant,
    stage_warnings: list[str],
) -> dict[str, object]:
    return _build_report(
        status=status,
        reason=reason,
        pipeline_id=pipeline.pipeline_id,
        pipeline_state=pipeline.state,
        approval_state=pipeline.approval_state,
        **commit_visibility_payload(pipeline),
        commit_sha=commit_sha,
        receipt_commit_sha=receipt_commit_sha or None,
        receipt_projection_state=_receipt_projection_state(
            commit_ok=commit_result.ok,
            commit_sha=commit_sha,
            receipt_commit_sha=receipt_commit_sha,
        ),
        action_result=commit_result.to_dict(),
        operator_guidance=commit_result.operator_guidance,
        interaction_mode=resolved_mode,
        action_request_authority=(
            action_request_grant.to_dict()
            if action_request_grant is not None
            else None
        ),
        warnings=[*stage_warnings, *commit_result.warnings],
    )


def _paths_with_approve_pending_report() -> dict[str, object]:
    return _build_report(
        status="blocked",
        reason="paths_not_allowed_with_approve_pending",
        operator_guidance=(
            "`--approve-pending` resumes the existing governed staged "
            "snapshot. Rerun without `--paths`, or recover and restage "
            "a fresh pipeline with the intended path scope."
        ),
    )


def _receipt_projection_state(
    *,
    commit_ok: bool,
    commit_sha: str,
    receipt_commit_sha: str,
) -> str:
    if receipt_commit_sha:
        return "receipt_commit_recorded"
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
