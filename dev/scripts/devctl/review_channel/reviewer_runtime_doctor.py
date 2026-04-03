"""Doctor/status projection helpers for the typed reviewer-runtime contract."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.remote_commit_pipeline_models import (
    RemoteCommitPipelineContract,
)
from ..runtime.reviewer_runtime_models import ReviewerRuntimeContract
from .peer_liveness import reviewer_mode_is_active
from .peer_recovery import STALE_PEER_RECOVERY


def build_reviewer_doctor_surface(
    *,
    contract: ReviewerRuntimeContract,
    attention: Mapping[str, object] | None = None,
    commit_pipeline: RemoteCommitPipelineContract | None = None,
    publisher_state: Mapping[str, object] | None = None,
    reviewer_supervisor_state: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Project a read-only doctor surface from reviewer-runtime authority."""
    pipeline = commit_pipeline or RemoteCommitPipelineContract()
    publisher = publisher_state or {}
    reviewer_supervisor = reviewer_supervisor_state or {}
    attention_summary = str((attention or {}).get("summary") or "").strip()
    recommended_command = str(
        (attention or {}).get("recommended_command")
        or contract.recovery_action_allowed
        or ""
    ).strip()
    status = _doctor_status(contract)
    summary = attention_summary or _doctor_summary(contract, status=status)
    surface: dict[str, object] = {}
    surface["status"] = status
    surface["summary"] = summary
    surface["reviewer_mode"] = contract.reviewer_mode
    surface["effective_reviewer_mode"] = contract.effective_reviewer_mode
    surface["reviewer_freshness"] = contract.reviewer_freshness
    surface["stale_reason"] = contract.stale_reason
    surface["last_codex_poll_utc"] = contract.last_poll.last_codex_poll_utc
    surface["last_codex_poll_age_seconds"] = contract.last_poll.last_codex_poll_age_seconds
    surface["rollover_id"] = contract.rollover.rollover_id
    surface["rollover_ack_pending"] = contract.rollover.ack_pending
    surface["rollover_trigger"] = contract.rollover.trigger
    surface["session_pid"] = contract.session_owner.session_pid
    surface["terminal_window_id"] = contract.session_owner.terminal_window_id
    surface["script_path"] = contract.session_owner.script_path
    surface["recovery_action_allowed"] = contract.recovery_action_allowed
    surface["recommended_command"] = recommended_command
    surface["review_accepted"] = contract.review_acceptance.review_accepted
    surface["current_verdict"] = contract.review_acceptance.current_verdict
    surface["open_findings"] = contract.review_acceptance.open_findings
    surface["publish_clear"] = contract.publish_clear
    surface["publisher_running"] = bool(publisher.get("running"))
    surface["publisher_stop_reason"] = str(publisher.get("stop_reason") or "")
    surface["publisher_last_heartbeat_utc"] = str(
        publisher.get("last_heartbeat_utc") or ""
    )
    surface["reviewer_supervisor_running"] = bool(reviewer_supervisor.get("running"))
    surface["reviewer_supervisor_stop_reason"] = str(
        reviewer_supervisor.get("stop_reason") or ""
    )
    surface["reviewer_supervisor_last_heartbeat_utc"] = str(
        reviewer_supervisor.get("last_heartbeat_utc") or ""
    )
    surface["pipeline_id"] = pipeline.pipeline_id
    surface["pipeline_state"] = pipeline.state
    surface["guard_status"] = _action_result_status(pipeline.guard_result)
    surface["approval_state"] = pipeline.approval_state
    surface["commit_ready"] = _commit_ready(contract=contract, pipeline=pipeline)
    surface["push_ready"] = _push_ready(contract=contract, pipeline=pipeline)
    surface["blocked_reason"] = pipeline.blocked_reason
    surface["staged_tree_hash"] = pipeline.intent.staged_tree_hash
    surface["staged_path_count"] = pipeline.intent.staged_path_count
    surface["diff_summary"] = pipeline.intent.diff_summary
    surface["commit_message_draft"] = pipeline.intent.commit_message_draft
    surface["approval_packet_id"] = pipeline.approval_packet_id
    surface["decision_packet_id"] = pipeline.decision_packet_id
    surface["guard_artifact_paths"] = (
        list(pipeline.guard_result.artifact_paths)
        if pipeline.guard_result is not None
        else []
    )
    surface["push_report_path"] = pipeline.push_report_path
    surface["commit_sha"] = pipeline.commit_sha
    surface["published_remote"] = _published_remote(pipeline)
    surface["post_push_green"] = _post_push_green(pipeline)
    surface["recovery_action_allowed"] = (
        pipeline.recovery_action_allowed or surface["recovery_action_allowed"]
    )
    surface["approval_expires_at_utc"] = pipeline.approval_expires_at_utc
    surface["generation_id"] = pipeline.generation_id
    surface["approved_target_identity"] = pipeline.approved_target_identity
    return surface


def _doctor_status(contract: ReviewerRuntimeContract) -> str:
    if contract.publish_clear:
        return "healthy"
    if contract.stale_reason:
        return contract.stale_reason
    if contract.rollover.ack_pending:
        return "rollover_ack_pending"
    if not contract.review_acceptance.review_accepted:
        return "review_pending"
    if reviewer_mode_is_active(contract.reviewer_mode):
        return "not_publish_clear"
    return "healthy"


def _doctor_summary(
    contract: ReviewerRuntimeContract,
    *,
    status: str,
) -> str:
    if status == "healthy":
        return "Reviewer runtime is green and publish-clear."
    if status == "review_pending":
        return "Reviewer verdict/findings are not accepted yet."
    if status == "rollover_ack_pending":
        return "Rollover is still awaiting fresh conductor ACK lines."
    recovery = STALE_PEER_RECOVERY.get(status)
    if isinstance(recovery, dict):
        return str(recovery.get("summary") or "").strip()
    return "Reviewer runtime is not publish-clear."


def _action_result_status(result: object) -> str:
    if result is None:
        return "not_run"
    return str(getattr(result, "status", "") or "unknown")


def _commit_ready(
    *,
    contract: ReviewerRuntimeContract,
    pipeline: RemoteCommitPipelineContract,
) -> bool:
    return (
        contract.publish_clear
        and _action_result_status(pipeline.guard_result) == "pass"
        and pipeline.approval_state == "approved"
        and not pipeline.blocked_reason
    )


def _push_ready(
    *,
    contract: ReviewerRuntimeContract,
    pipeline: RemoteCommitPipelineContract,
) -> bool:
    return (
        contract.publish_clear
        and bool(pipeline.commit_sha)
        and pipeline.state in {"commit_recorded", "push_pending", "push_completed"}
        and not pipeline.blocked_reason
    )


def _published_remote(pipeline: RemoteCommitPipelineContract) -> bool:
    if pipeline.state == "push_completed":
        return True
    if pipeline.push_result is None:
        return False
    return bool(pipeline.push_result.ok and pipeline.push_result.status == "pass")


def _post_push_green(pipeline: RemoteCommitPipelineContract) -> bool:
    return pipeline.state == "push_completed" and _published_remote(pipeline)
