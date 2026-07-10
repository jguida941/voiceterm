"""Surface-building helpers for reviewer runtime doctor/status projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from ..governance.push_state_support import is_expired
from ..runtime.remote_commit_pipeline_models import (
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
)
from ..runtime.reviewer_runtime_models import ReviewerRuntimeContract
from .reviewer_runtime_publication import (
    PublicationTruth,
    resolve_publication_blocked_reason,
)


@dataclass(frozen=True, slots=True)
class DoctorIdentitySurfaceRecord:
    status: str
    summary: str
    diagnosis_status: str
    root_cause: str
    reviewer_mode: str
    effective_reviewer_mode: str
    reviewer_freshness: str
    stale_reason: str
    conductor_visibility: str
    implementer_ack_current: bool
    implementation_blocked: bool
    implementation_block_reason: str


@dataclass(frozen=True, slots=True)
class DoctorSessionSurfaceRecord:
    last_codex_poll_utc: str
    last_codex_poll_age_seconds: object
    last_reviewer_poll_utc: str
    last_reviewer_poll_age_seconds: object
    rollover_id: str
    rollover_ack_pending: bool
    rollover_trigger: str
    session_pid: object
    terminal_window_id: object
    script_path: str
    session_visibility: str
    recovery_action_allowed: str
    recommended_command: str
    decision_action_id: str
    decision_command: str
    decision_execution_owner: str
    decision_requires_approval: bool
    decision_can_auto_fix: bool


@dataclass(frozen=True, slots=True)
class DoctorPipelineSurfaceRecord:
    pipeline_id: str
    pipeline_state: str
    guard_status: str
    approval_state: str
    commit_ready: bool
    push_ready: bool
    blocked_reason: str
    staged_tree_hash: str
    staged_path_count: object
    diff_summary: str
    commit_message_draft: str
    approval_packet_id: str
    decision_packet_id: str
    guard_artifact_paths: list[str]
    push_report_path: str
    commit_sha: str
    published_remote: bool
    post_push_green: bool
    publication_source: str
    recovery_action_allowed: str
    approval_expires_at_utc: str
    generation_id: str
    approved_target_identity: str


def doctor_identity_surface(
    *,
    contract: ReviewerRuntimeContract,
    status: str,
    summary: str,
    diagnosis: object | None,
    attention_summary: str,
) -> dict[str, object]:
    return asdict(
        DoctorIdentitySurfaceRecord(
            status=status,
            summary=summary,
            diagnosis_status=(
                getattr(diagnosis, "status", "") or contract.stale_reason or "healthy"
            ),
            root_cause=getattr(diagnosis, "root_cause", "") or attention_summary,
            reviewer_mode=contract.reviewer_mode,
            effective_reviewer_mode=contract.effective_reviewer_mode,
            reviewer_freshness=contract.reviewer_freshness,
            stale_reason=contract.stale_reason,
            conductor_visibility=contract.conductor_visibility,
            implementer_ack_current=contract.implementer_ack_current,
            implementation_blocked=contract.implementation_blocked,
            implementation_block_reason=contract.implementation_block_reason,
        )
    )


def doctor_session_surface(
    *,
    contract: ReviewerRuntimeContract,
    recommended_command: str,
    decision: object | None,
) -> dict[str, object]:
    return asdict(
        DoctorSessionSurfaceRecord(
            last_codex_poll_utc=contract.last_poll.last_codex_poll_utc,
            last_codex_poll_age_seconds=contract.last_poll.last_codex_poll_age_seconds,
            last_reviewer_poll_utc=(
                contract.last_poll.last_reviewer_poll_utc
                or contract.last_poll.last_codex_poll_utc
            ),
            last_reviewer_poll_age_seconds=(
                contract.last_poll.last_reviewer_poll_age_seconds
                or contract.last_poll.last_codex_poll_age_seconds
            ),
            rollover_id=contract.rollover.rollover_id,
            rollover_ack_pending=contract.rollover.ack_pending,
            rollover_trigger=contract.rollover.trigger,
            session_pid=contract.session_owner.session_pid,
            terminal_window_id=contract.session_owner.terminal_window_id,
            script_path=contract.session_owner.script_path,
            session_visibility=contract.session_owner.session_visibility,
            recovery_action_allowed=contract.recovery_action_allowed,
            recommended_command=recommended_command,
            decision_action_id=getattr(decision, "action_id", "") or "",
            decision_command=getattr(decision, "command", "") or "",
            decision_execution_owner=getattr(decision, "execution_owner", "") or "",
            decision_requires_approval=bool(
                getattr(decision, "requires_approval", False)
            ),
            decision_can_auto_fix=bool(getattr(decision, "can_auto_fix", False)),
        )
    )


def doctor_pipeline_surface(
    *,
    contract: ReviewerRuntimeContract,
    pipeline: RemoteCommitPipelineContract,
    publication: PublicationTruth,
    push_authorization: PushAuthorizationRecord | None,
    push_enforcement: Mapping[str, object] | None,
) -> dict[str, object]:
    surface = asdict(
        DoctorPipelineSurfaceRecord(
            pipeline_id=pipeline.pipeline_id,
            pipeline_state=pipeline.state,
            guard_status=action_result_status(pipeline.guard_result),
            approval_state=pipeline.approval_state,
            commit_ready=_commit_ready(contract=contract, pipeline=pipeline),
            push_ready=_push_ready(
                contract=contract,
                pipeline=pipeline,
                push_authorization=push_authorization,
            ),
            blocked_reason=resolve_publication_blocked_reason(
                pipeline=pipeline,
                push_enforcement=push_enforcement,
            ),
            staged_tree_hash=pipeline.intent.staged_tree_hash,
            staged_path_count=pipeline.intent.staged_path_count,
            diff_summary=pipeline.intent.diff_summary,
            commit_message_draft=pipeline.intent.commit_message_draft,
            approval_packet_id=pipeline.approval_packet_id,
            decision_packet_id=pipeline.decision_packet_id,
            guard_artifact_paths=(
                list(pipeline.guard_result.artifact_paths)
                if pipeline.guard_result is not None
                else []
            ),
            push_report_path=publication.push_report_path,
            commit_sha=pipeline.commit_sha,
            published_remote=publication.published_remote,
            post_push_green=publication.post_push_green,
            publication_source=publication.source,
            recovery_action_allowed=(
                pipeline.recovery_action_allowed or contract.recovery_action_allowed
            ),
            approval_expires_at_utc=pipeline.approval_expires_at_utc,
            generation_id=pipeline.generation_id,
            approved_target_identity=pipeline.approved_target_identity,
        )
    )
    surface.update(
        _push_authorization_surface(
            pipeline=pipeline,
            push_authorization=push_authorization,
        )
    )
    return surface


def doctor_review_surface(contract: ReviewerRuntimeContract) -> dict[str, object]:
    return {
        "review_accepted": contract.review_acceptance.review_accepted,
        "current_verdict": contract.review_acceptance.current_verdict,
        "open_findings": contract.review_acceptance.open_findings,
        "reviewer_accepted_implementer_state_hash": (
            contract.review_acceptance.reviewer_accepted_implementer_state_hash
        ),
        "publish_clear": contract.publish_clear,
    }


def runtime_daemon_surface(
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


def action_result_status(result: object) -> str:
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
        and action_result_status(pipeline.guard_result) == "pass"
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
