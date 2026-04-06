"""Doctor/status projection helpers for the typed reviewer-runtime contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from ..governance.push_state_support import is_expired
from ..runtime.remote_commit_pipeline_models import (
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
)
from ..runtime.review_state_models import RecoveryAssessmentState
from ..runtime.reviewer_runtime_models import ReviewerRuntimeContract
from .peer_liveness import reviewer_mode_is_active
from .peer_recovery import STALE_PEER_RECOVERY
from .reviewer_runtime_publication import (
    PublicationTruth,
    resolve_publication_blocked_reason,
    resolve_publication_truth,
)


def build_reviewer_doctor_surface(
    *,
    contract: ReviewerRuntimeContract,
    recovery_assessment: RecoveryAssessmentState | None = None,
    attention: Mapping[str, object] | None = None,
    commit_pipeline: RemoteCommitPipelineContract | None = None,
    push_authorization: PushAuthorizationRecord | None = None,
    push_enforcement: Mapping[str, object] | None = None,
    runtime_state: Mapping[str, object] | None = None,
    snapshot_id: str = "",
) -> dict[str, object]:
    """Project a read-only doctor surface from reviewer-runtime authority."""
    pipeline = commit_pipeline or RemoteCommitPipelineContract()
    runtime = runtime_state if isinstance(runtime_state, Mapping) else {}
    publisher = _runtime_mapping(runtime.get("publisher"))
    reviewer_supervisor = _runtime_mapping(runtime.get("reviewer_supervisor"))
    publication = resolve_publication_truth(
        pipeline=pipeline,
        push_enforcement=push_enforcement,
    )
    diagnosis = recovery_assessment.diagnosis if recovery_assessment is not None else None
    decision = recovery_assessment.decision if recovery_assessment is not None else None
    attention_summary = (
        str(diagnosis.root_cause or "").strip()
        if diagnosis is not None and diagnosis.status not in {"", "healthy"}
        else str((attention or {}).get("summary") or "").strip()
    )
    recommended_command = str(
        (decision.command if decision is not None else "")
        or (attention or {}).get("recommended_command")
        or contract.recovery_action_allowed
        or ""
    ).strip()
    status = _doctor_status(contract)
    summary = attention_summary or _doctor_summary(
        contract,
        status=status,
        publication=publication,
    )
    surface: dict[str, object] = {}
    surface["status"] = status
    surface["summary"] = summary
    surface["diagnosis_status"] = (
        diagnosis.status
        if diagnosis is not None
        else contract.stale_reason or "healthy"
    )
    surface["root_cause"] = (
        diagnosis.root_cause if diagnosis is not None else attention_summary
    )
    surface["reviewer_mode"] = contract.reviewer_mode
    surface["effective_reviewer_mode"] = contract.effective_reviewer_mode
    surface["reviewer_freshness"] = contract.reviewer_freshness
    surface["stale_reason"] = contract.stale_reason
    surface["conductor_visibility"] = contract.conductor_visibility
    surface["implementer_ack_current"] = contract.implementer_ack_current
    surface["implementation_blocked"] = contract.implementation_blocked
    surface["implementation_block_reason"] = contract.implementation_block_reason
    surface["last_codex_poll_utc"] = contract.last_poll.last_codex_poll_utc
    surface["last_codex_poll_age_seconds"] = contract.last_poll.last_codex_poll_age_seconds
    surface["rollover_id"] = contract.rollover.rollover_id
    surface["rollover_ack_pending"] = contract.rollover.ack_pending
    surface["rollover_trigger"] = contract.rollover.trigger
    surface["session_pid"] = contract.session_owner.session_pid
    surface["terminal_window_id"] = contract.session_owner.terminal_window_id
    surface["script_path"] = contract.session_owner.script_path
    surface["session_visibility"] = contract.session_owner.session_visibility
    surface["recovery_action_allowed"] = contract.recovery_action_allowed
    surface["recommended_command"] = recommended_command
    surface["decision_action_id"] = decision.action_id if decision is not None else ""
    surface["decision_command"] = decision.command if decision is not None else ""
    surface["decision_execution_owner"] = (
        decision.execution_owner if decision is not None else ""
    )
    surface["decision_requires_approval"] = (
        decision.requires_approval if decision is not None else False
    )
    surface["decision_can_auto_fix"] = (
        decision.can_auto_fix if decision is not None else False
    )
    surface["review_accepted"] = contract.review_acceptance.review_accepted
    surface["current_verdict"] = contract.review_acceptance.current_verdict
    surface["open_findings"] = contract.review_acceptance.open_findings
    surface["reviewer_accepted_implementer_state_hash"] = (
        contract.review_acceptance.reviewer_accepted_implementer_state_hash
    )
    surface["publish_clear"] = contract.publish_clear
    surface.update(
        _runtime_daemon_surface(
            publisher=publisher,
            reviewer_supervisor=reviewer_supervisor,
        )
    )
    surface["pipeline_id"] = pipeline.pipeline_id
    surface["pipeline_state"] = pipeline.state
    surface["guard_status"] = _action_result_status(pipeline.guard_result)
    surface["approval_state"] = pipeline.approval_state
    surface["commit_ready"] = _commit_ready(contract=contract, pipeline=pipeline)
    surface["push_ready"] = _push_ready(
        contract=contract,
        pipeline=pipeline,
        push_authorization=push_authorization,
    )
    surface["blocked_reason"] = resolve_publication_blocked_reason(
        pipeline=pipeline,
        push_enforcement=push_enforcement,
    )
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
    surface["push_report_path"] = publication.push_report_path
    surface["commit_sha"] = pipeline.commit_sha
    surface["published_remote"] = publication.published_remote
    surface["post_push_green"] = publication.post_push_green
    surface["publication_source"] = publication.source
    surface["recovery_action_allowed"] = (
        pipeline.recovery_action_allowed or surface["recovery_action_allowed"]
    )
    surface["approval_expires_at_utc"] = pipeline.approval_expires_at_utc
    surface["generation_id"] = pipeline.generation_id
    surface["approved_target_identity"] = pipeline.approved_target_identity
    surface.update(
        _push_authorization_surface(
            pipeline=pipeline,
            push_authorization=push_authorization,
        )
    )
    surface["snapshot_id"] = snapshot_id or pipeline.snapshot_id
    if recovery_assessment is not None:
        surface["recovery_assessment"] = asdict(recovery_assessment)
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
    publication: PublicationTruth,
) -> str:
    if publication.published_remote and not publication.post_push_green:
        return (
            "Remote publication is already recorded for the current HEAD, "
            "but post-push follow-up is not green yet."
        )
    if publication.published_remote and publication.post_push_green:
        return "Remote publication and post-push validation are already recorded."
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


def _runtime_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _runtime_daemon_surface(
    *,
    publisher: Mapping[str, object],
    reviewer_supervisor: Mapping[str, object],
) -> dict[str, object]:
    surface: dict[str, object] = {}
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
    return surface


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
    push_authorization: PushAuthorizationRecord | None,
) -> bool:
    if _push_authorization_current(
        pipeline=pipeline,
        push_authorization=push_authorization,
    ):
        if not pipeline.commit_sha:
            return True
        return pipeline.state in {
            "commit_recorded",
            "push_pending",
            "push_blocked",
            "push_completed",
        }
    return (
        contract.publish_clear
        and bool(pipeline.commit_sha)
        and pipeline.state in {"commit_recorded", "push_pending", "push_completed"}
        and not pipeline.blocked_reason
    )


def _push_authorization_current(
    *,
    pipeline: RemoteCommitPipelineContract,
    push_authorization: PushAuthorizationRecord | None,
) -> bool:
    if push_authorization is None:
        return False
    if is_expired(push_authorization.expires_at_utc):
        return False
    if push_authorization.guard_status != "pass":
        return False
    if push_authorization.authorized_head_sha and pipeline.commit_sha:
        if push_authorization.authorized_head_sha != pipeline.commit_sha:
            return False
    if (
        push_authorization.approved_target_identity
        and pipeline.approved_target_identity
        and push_authorization.approved_target_identity
        != pipeline.approved_target_identity
    ):
        return False
    return True


def _push_authorization_surface(
    *,
    pipeline: RemoteCommitPipelineContract,
    push_authorization: PushAuthorizationRecord | None,
) -> dict[str, object]:
    return {
        "push_authorization_id": (
            push_authorization.authorization_id if push_authorization is not None else ""
        ),
        "push_authorization_mode": (
            push_authorization.approval_mode if push_authorization is not None else ""
        ),
        "push_authorization_head_sha": (
            push_authorization.authorized_head_sha
            if push_authorization is not None
            else ""
        ),
        "push_authorization_valid": _push_authorization_current(
            pipeline=pipeline,
            push_authorization=push_authorization,
        ),
        "push_authorization_reason": (
            ""
            if push_authorization is None
            else push_authorization.override_reason
            or push_authorization.guard_reason
        ),
    }
