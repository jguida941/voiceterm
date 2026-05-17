"""Doctor/status projection helpers for the typed reviewer-runtime contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from ..runtime.remote_commit_pipeline_models import (
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
)
from ..runtime.review_state_models import RecoveryAssessmentState
from ..runtime.reviewer_runtime_models import ReviewerRuntimeContract
from .peer_liveness import reviewer_mode_is_active
from .peer_recovery import STALE_PEER_RECOVERY
from .runtime_counts import build_runtime_counts
from .reviewer_runtime_doctor_surface import (
    doctor_identity_surface,
    doctor_pipeline_surface,
    doctor_review_surface,
    doctor_session_surface,
    runtime_daemon_surface,
)
from .reviewer_runtime_publication import (
    PublicationTruth,
    current_pipeline_projection,
    resolve_publication_truth,
)


def build_reviewer_doctor_surface(
    *,
    contract: ReviewerRuntimeContract,
    **surface_inputs: object,
) -> dict[str, object]:
    """Project a read-only doctor surface from reviewer-runtime authority."""
    collaboration = surface_inputs.get("collaboration")
    bridge_liveness = surface_inputs.get("bridge_liveness")
    recovery_assessment = surface_inputs.get("recovery_assessment")
    attention = _runtime_mapping(surface_inputs.get("attention"))
    commit_pipeline = surface_inputs.get("commit_pipeline")
    push_authorization = surface_inputs.get("push_authorization")
    push_enforcement = _runtime_mapping(surface_inputs.get("push_enforcement"))
    runtime_state = _runtime_mapping(surface_inputs.get("runtime_state"))
    snapshot_id = str(surface_inputs.get("snapshot_id") or "")
    pipeline = current_pipeline_projection(
        pipeline=(
            commit_pipeline
            if isinstance(commit_pipeline, RemoteCommitPipelineContract)
            else RemoteCommitPipelineContract()
        ),
        push_enforcement=push_enforcement,
    )
    publisher = _runtime_mapping(runtime_state.get("publisher"))
    reviewer_supervisor = _runtime_mapping(runtime_state.get("reviewer_supervisor"))
    publication = resolve_publication_truth(
        pipeline=pipeline,
        push_enforcement=push_enforcement,
    )
    diagnosis = (
        recovery_assessment.diagnosis
        if isinstance(recovery_assessment, RecoveryAssessmentState)
        else None
    )
    decision = (
        recovery_assessment.decision
        if isinstance(recovery_assessment, RecoveryAssessmentState)
        else None
    )
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
    surface = doctor_identity_surface(
        contract=contract,
        status=status,
        summary=summary,
        diagnosis=diagnosis,
        attention_summary=attention_summary,
    )
    surface.update(
        doctor_session_surface(
            contract=contract,
            recommended_command=recommended_command,
            decision=decision,
        )
    )
    surface.update(doctor_review_surface(contract))
    surface.update(
        runtime_daemon_surface(
            publisher=publisher,
            reviewer_supervisor=reviewer_supervisor,
        )
    )
    surface["runtime_counts"] = build_runtime_counts(
        collaboration=collaboration,
        bridge_liveness=bridge_liveness,
        publisher_running=bool(publisher.get("running")),
        reviewer_supervisor_running=bool(reviewer_supervisor.get("running")),
    )
    surface.update(
        doctor_pipeline_surface(
            contract=contract,
            pipeline=pipeline,
            publication=publication,
            push_authorization=push_authorization,
            push_enforcement=push_enforcement,
        )
    )
    surface["snapshot_id"] = snapshot_id or pipeline.snapshot_id
    if isinstance(recovery_assessment, RecoveryAssessmentState):
        surface["recovery_assessment"] = asdict(recovery_assessment)
    return surface


def _doctor_status(contract: ReviewerRuntimeContract) -> str:
    if contract.stale_reason:
        return contract.stale_reason
    if contract.publish_clear:
        return "healthy"
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
