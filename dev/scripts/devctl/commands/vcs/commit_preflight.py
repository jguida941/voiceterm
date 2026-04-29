"""Preflight helpers for the governed commit command."""

from __future__ import annotations

from pathlib import Path

from ...repo_packs import active_path_config
from ...runtime.control_plane_read_model import (
    ControlPlaneReadModelOptions,
    build_control_plane_read_model,
)
from ...runtime.governance_scan import scan_repo_governance_safely
from ...review_channel.remote_control_attachment_artifact import (
    load_remote_control_attachment,
)
from .commit_guard_replay import sync_pipeline_approval_state
from .commit_pipeline_blocking import build_active_pipeline_block_report
from .commit_preflight_approval_packets import (
    apply_local_approval,
    ensure_approval_request,
    record_operator_approval,
)
from .commit_preflight_support import (
    APPROVE_PENDING_COMMAND,
    CommitApprovalAuthority,
    OPERATOR_HISTORY_COMMAND,
    OPERATOR_INBOX_COMMAND,
    build_commit_approval_authority,
    next_command_guidance,
    should_auto_approve,
)
from .commit_preflight_validators import (
    CommitPreflightDeps,
    load_pipeline_for_explicit_approval as _load_pipeline_for_explicit_approval,
    prepare_pipeline as _prepare_pipeline,
)
from .commit_visibility import commit_visibility_payload
from .governed_executor import GovernedVcsExecutor
from .governed_executor_actions import APPROVAL_PACKET_KIND, _build_report
from .governed_executor_commit_runtime import post_commit_execution_handoff
from .governed_executor_git import pipeline_is_stale_for_current_repo
from .governed_executor_sync import sync_pipeline_approval


def resolve_commit_approval_authority(
    repo_root: Path,
    *,
    interaction_mode_override: str | None = None,
) -> CommitApprovalAuthority:
    """Return the typed approval authority for the current commit attempt."""
    override_mode = str(interaction_mode_override or "").strip()
    if override_mode and override_mode != "remote_control":
        return build_commit_approval_authority(
            interaction_mode=override_mode,
        )
    if override_mode == "remote_control":
        output_root = repo_root / active_path_config().review_status_dir_rel
        return build_commit_approval_authority(
            interaction_mode=override_mode,
            remote_control_attachment=load_remote_control_attachment(
                output_root=output_root,
            ),
        )

    remote_control_attachment = None
    try:
        governance = scan_repo_governance_safely(repo_root)
        model = build_control_plane_read_model(
            repo_root,
            options=ControlPlaneReadModelOptions(governance=governance),
        )
    except (OSError, ValueError):
        interaction_mode = "unresolved"
    else:
        interaction_mode = (
            str(model.operator_interaction_mode or "").strip()
            or "unresolved"
        )
        remote_control_attachment = getattr(model, "remote_control_attachment", None)
    return build_commit_approval_authority(
        interaction_mode=interaction_mode,
        remote_control_attachment=remote_control_attachment,
    )


def resolve_interaction_mode(repo_root: Path) -> str:
    """Return the current operator interaction mode for commit approval."""
    return resolve_commit_approval_authority(repo_root).interaction_mode


def prepare_pipeline(
    *,
    args,
    repo_root: Path,
    resolved_policy,
    vcs_executor: GovernedVcsExecutor,
    action_request_grant: object | None = None,
):
    return _prepare_pipeline(
        args=args,
        repo_root=repo_root,
        resolved_policy=resolved_policy,
        vcs_executor=vcs_executor,
        action_request_grant=action_request_grant,
        deps=CommitPreflightDeps(
            pipeline_is_stale_for_current_repo_fn=pipeline_is_stale_for_current_repo,
            build_active_pipeline_block_report_fn=build_active_pipeline_block_report,
            post_commit_execution_handoff_fn=post_commit_execution_handoff,
        ),
    )


def load_pipeline_for_explicit_approval(
    *,
    repo_root: Path,
    vcs_executor: GovernedVcsExecutor,
):
    return _load_pipeline_for_explicit_approval(
        repo_root=repo_root,
        vcs_executor=vcs_executor,
        deps=CommitPreflightDeps(
            pipeline_is_stale_for_current_repo_fn=pipeline_is_stale_for_current_repo,
            build_active_pipeline_block_report_fn=build_active_pipeline_block_report,
            post_commit_execution_handoff_fn=post_commit_execution_handoff,
        ),
    )


def ensure_pipeline_approval(
    *,
    vcs_executor: GovernedVcsExecutor,
    pipeline,
    approval_authority: CommitApprovalAuthority,
    stage_warnings: list[str],
):
    """Return the synced approval state or the blocking approval report."""
    if pipeline.approval_state == "approved":
        vcs_executor._persist_pipeline(pipeline)
        return pipeline, None
    request_packet_id = ""
    if should_auto_approve(approval_authority):
        apply_local_approval(
            vcs_executor,
            pipeline,
            approval_actor=approval_authority.approval_actor,
            authority_reason=approval_authority.authority_reason,
        )
    else:
        request_packet_id = ensure_approval_request(
            vcs_executor,
            pipeline,
            to_agent=approval_authority.approval_actor,
        )
    pipeline = sync_pipeline_approval_state(
        vcs_executor,
        vcs_executor.load_pipeline(),
    )
    if pipeline.approval_state == "approved":
        return pipeline, None
    return pipeline, _build_report(
        status="blocked",
        reason="operator_approval_missing",
        pipeline_id=pipeline.pipeline_id,
        pipeline_state=pipeline.state,
        approval_state=pipeline.approval_state,
        **commit_visibility_payload(pipeline),
        requested_action="approve_commit_pipeline",
        next_command=OPERATOR_INBOX_COMMAND,
        approval_request_packet_id=request_packet_id,
        resume_command=APPROVE_PENDING_COMMAND,
        operator_guidance=next_command_guidance(OPERATOR_INBOX_COMMAND),
        interaction_mode=approval_authority.interaction_mode,
        warnings=stage_warnings,
    )


def apply_explicit_operator_approval(
    *,
    vcs_executor: GovernedVcsExecutor,
    pipeline,
    approval_authority: CommitApprovalAuthority,
    stage_warnings: list[str],
):
    """Record explicit operator approval for the current governed pipeline."""
    pipeline = sync_pipeline_approval(
        pipeline,
        vcs_executor._event_packets(),
        approval_packet_kind=APPROVAL_PACKET_KIND,
    )
    if pipeline.approval_state == "approved":
        vcs_executor._persist_pipeline(pipeline)
        return pipeline, None
    record_operator_approval(
        vcs_executor,
        pipeline,
        summary=(
            "Remote-control operator approved governed commit pipeline "
            f"`{pipeline.pipeline_id}`"
        ),
        body=(
            "The remote-control operator explicitly approved the current "
            "guarded staged snapshot for governed commit execution."
        ),
        approval_actor=approval_authority.approval_actor,
    )
    pipeline = sync_pipeline_approval(
        vcs_executor.load_pipeline(),
        vcs_executor._event_packets(),
        approval_packet_kind=APPROVAL_PACKET_KIND,
    )
    if pipeline.approval_state == "approved":
        vcs_executor._persist_pipeline(pipeline)
        return pipeline, None
    return pipeline, _build_report(
        status="blocked",
        reason="operator_approval_missing",
        pipeline_id=pipeline.pipeline_id,
        pipeline_state=pipeline.state,
        approval_state=pipeline.approval_state,
        **commit_visibility_payload(pipeline),
        requested_action="reconcile_operator_approval",
        next_command=OPERATOR_HISTORY_COMMAND,
        operator_guidance=next_command_guidance(OPERATOR_HISTORY_COMMAND),
        interaction_mode=approval_authority.interaction_mode,
        warnings=stage_warnings,
    )
