"""Preflight helpers for the governed commit command."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.events import post_packet, resolve_artifact_paths, transition_packet
from ...review_channel.packet_contract import PacketTransitionRequest
from ...runtime.control_plane_read_model import build_control_plane_read_model
from ...runtime.governance_scan import scan_repo_governance_safely
from .commit_guard_bundle import GUARD_PROFILE
from .commit_guard_replay import sync_pipeline_approval_state
from .commit_pipeline_blocking import build_active_pipeline_block_report
from .commit_preflight_support import (
    APPROVE_PENDING_COMMAND,
    COMMIT_START_COMMAND,
    OPERATOR_HISTORY_COMMAND,
    OPERATOR_INBOX_COMMAND,
    next_command_guidance,
    should_auto_approve,
)
from .commit_visibility import commit_visibility_payload
from .governed_executor import GovernedVcsExecutor
from .governed_executor_actions import APPROVAL_PACKET_KIND, _build_report, build_stage_action
from .governed_executor_git import pipeline_is_stale_for_current_repo
from .governed_executor_packets import build_commit_approval_decision, build_commit_approval_request
from .governed_executor_sync import sync_pipeline_approval

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
_PIPELINE_BLOCKING_STATES = frozenset({"commit_recorded", "push_pending", "push_blocked"})
_EXPLICIT_APPROVAL_PIPELINE_STATES = frozenset(
    {
        "guards_passed",
        "operator_approval_pending",
        "approved",
        "commit_pending",
    }
)

def resolve_interaction_mode(repo_root: Path) -> str:
    """Return the current operator interaction mode for commit approval."""
    try:
        governance = scan_repo_governance_safely(repo_root)
        model = build_control_plane_read_model(
            repo_root,
            governance=governance,
        )
    except (OSError, ValueError):
        return "unresolved"
    return str(model.operator_interaction_mode or "").strip() or "unresolved"


def prepare_pipeline(
    *,
    args,
    repo_root: Path,
    resolved_policy,
    vcs_executor: GovernedVcsExecutor,
):
    """Load or restage the governed pipeline before guard replay."""
    stage_warnings: list[str] = []
    pipeline = vcs_executor.load_pipeline()
    stale_pipeline = pipeline_is_stale_for_current_repo(
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
        return pipeline, stage_warnings, build_active_pipeline_block_report(
            repo_root=repo_root,
            pipeline=pipeline,
        )

    if (
        not pipeline.pipeline_id
        or pipeline.state not in _REUSABLE_PIPELINE_STATES
        or stale_pipeline
    ):
        stage_result = vcs_executor.execute(
            build_stage_action(
                repo_pack_id=resolved_policy.repo_pack_id,
                commit_message_draft=str(getattr(args, "message", "") or ""),
                push_requested=False,
                guard_profile=GUARD_PROFILE,
                work_intake_ref="devctl.commit",
                reuse_staged_index=True,
                allow_empty=bool(getattr(args, "passthrough", ()) and "--allow-empty" in getattr(args, "passthrough", ())),
                requested_by="devctl.commit",
            )
        )
        pipeline = vcs_executor.load_pipeline()
        stage_warnings = list(stage_result.warnings)
        if not stage_result.ok:
            return pipeline, stage_warnings, _build_report(
                status="blocked",
                reason=stage_result.reason,
                pipeline_id=pipeline.pipeline_id,
                pipeline_state=pipeline.state,
                operator_guidance=stage_result.operator_guidance,
                warnings=list(stage_result.warnings),
            )
    return pipeline, stage_warnings, None


def load_pipeline_for_explicit_approval(
    *,
    repo_root: Path,
    vcs_executor: GovernedVcsExecutor,
):
    """Return the existing governed pipeline for explicit operator approval."""
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
    if pipeline_is_stale_for_current_repo(
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
        return pipeline, build_active_pipeline_block_report(
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


def ensure_pipeline_approval(
    *,
    vcs_executor: GovernedVcsExecutor,
    pipeline,
    resolved_mode: str,
    stage_warnings: list[str],
):
    """Return the synced approval state or the blocking approval report."""
    if pipeline.approval_state == "approved":
        vcs_executor._persist_pipeline(pipeline)
        return pipeline, None
    request_packet_id = ""
    if should_auto_approve(resolved_mode):
        _apply_local_approval(vcs_executor, pipeline)
    else:
        request_packet_id = _ensure_approval_request(vcs_executor, pipeline)
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
        interaction_mode=resolved_mode,
        warnings=stage_warnings,
    )


def apply_explicit_operator_approval(
    *,
    vcs_executor: GovernedVcsExecutor,
    pipeline,
    resolved_mode: str,
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
    _record_operator_approval(
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
        interaction_mode=resolved_mode,
        warnings=stage_warnings,
    )

def _ensure_approval_request(
    executor: GovernedVcsExecutor,
    pipeline,
) -> str:
    """Post the typed approval request once per governed pipeline."""
    synced = sync_pipeline_approval(
        pipeline,
        executor._event_packets(),
        approval_packet_kind=APPROVAL_PACKET_KIND,
    )
    if synced.approval_packet_id or synced.approval_state == "approved":
        executor._persist_pipeline(synced)
        return synced.approval_packet_id
    artifact_paths = resolve_artifact_paths(repo_root=executor.repo_root)
    _, event = post_packet(
        repo_root=executor.repo_root,
        review_channel_path=executor.review_channel_path,
        artifact_paths=artifact_paths,
        request=build_commit_approval_request(pipeline),
    )
    return str(event.get("packet_id") or "").strip()


def _apply_local_approval(executor: GovernedVcsExecutor, pipeline) -> None:
    """Record request + applied operator decision for local terminal commits."""
    _record_operator_approval(
        executor,
        pipeline,
        summary=f"Local terminal approval for `{pipeline.pipeline_id}`",
        body=(
            "The local terminal operator approved the guarded staged "
            "snapshot for governed commit execution."
        ),
    )


def _record_operator_approval(
    executor: GovernedVcsExecutor,
    pipeline,
    *,
    summary: str,
    body: str,
) -> None:
    """Post and apply one typed operator approval for the current pipeline."""
    artifact_paths = resolve_artifact_paths(repo_root=executor.repo_root)
    request_packet_id = _ensure_approval_request(executor, pipeline)
    if request_packet_id:
        try:
            transition_packet(
                repo_root=executor.repo_root,
                review_channel_path=executor.review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketTransitionRequest(
                    action="apply",
                    packet_id=request_packet_id,
                    actor="operator",
                ),
            )
        except ValueError:
            pass
    _, decision_event = post_packet(
        repo_root=executor.repo_root,
        review_channel_path=executor.review_channel_path,
        artifact_paths=artifact_paths,
        request=build_commit_approval_decision(
            pipeline,
            summary=summary,
            body=body,
        ),
    )
    transition_packet(
        repo_root=executor.repo_root,
        review_channel_path=executor.review_channel_path,
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(decision_event.get("packet_id") or ""),
            actor="operator",
        ),
    )
