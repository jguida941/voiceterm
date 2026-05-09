"""Typed approval packet helpers for governed commit preflight."""

from __future__ import annotations

import secrets
from pathlib import Path

from ...review_channel.context_refs import normalize_context_pack_refs
from ...review_channel.event_store import (
    append_event,
    future_utc_timestamp,
    load_events,
    next_event_id,
)
from ...review_channel.events import post_packet, resolve_artifact_paths, transition_packet
from ...review_channel.packet_attestation import PacketGuardAttestation
from ...review_channel.packet_contract import PacketTransitionRequest
from ...review_channel.packet_transition_events import (
    build_transition_event,
    finish_transition_event,
)
from ...review_channel.state import project_id_for_repo
from ...time_utils import utc_timestamp
from .governed_executor import GovernedVcsExecutor
from .governed_executor_actions import APPROVAL_PACKET_KIND
from .governed_executor_packets import (
    build_commit_approval_decision,
    build_commit_approval_request,
    latest_matching_packet,
)
from .governed_executor_sync import sync_pipeline_approval


def ensure_approval_request(
    executor: GovernedVcsExecutor,
    pipeline,
    *,
    to_agent: str = "operator",
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
        request=build_commit_approval_request(
            pipeline,
            to_agent=to_agent,
        ),
    )
    return str(event.get("packet_id") or "").strip()


def apply_local_approval(
    executor: GovernedVcsExecutor,
    pipeline,
    *,
    approval_actor: str = "operator",
    authority_reason: str = "",
) -> None:
    """Record request + applied approval for trusted local or delegated modes."""
    summary = f"Local terminal approval for `{pipeline.pipeline_id}`"
    body = (
        "The local terminal operator approved the guarded staged "
        "snapshot for governed commit execution."
    )
    if authority_reason == "remote_control_operator_delegate":
        actor_label = str(approval_actor or "operator").strip()
        summary = f"Remote-control delegated approval for `{pipeline.pipeline_id}`"
        body = (
            "The active remote-control operator delegate "
            f"`{actor_label}` approved the guarded staged snapshot for "
            "governed commit execution."
        )
    record_operator_approval(
        executor,
        pipeline,
        summary=summary,
        body=body,
        approval_actor=approval_actor,
    )


def record_operator_approval(
    executor: GovernedVcsExecutor,
    pipeline,
    *,
    summary: str,
    body: str,
    approval_actor: str = "operator",
) -> None:
    """Post and apply one typed operator approval for the current pipeline."""
    if not bool(getattr(executor, "refresh_projections", True)):
        _record_operator_approval_without_refresh(
            executor,
            pipeline,
            summary=summary,
            body=body,
            approval_actor=approval_actor,
        )
        return
    artifact_paths = resolve_artifact_paths(repo_root=executor.repo_root)
    actor = str(approval_actor or "operator").strip() or "operator"
    request_packet_id = ensure_approval_request(
        executor,
        pipeline,
        to_agent=actor,
    )
    if request_packet_id:
        try:
            transition_packet(
                repo_root=executor.repo_root,
                review_channel_path=executor.review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketTransitionRequest(
                    action="apply",
                    packet_id=request_packet_id,
                    actor=actor,
                    guard_attestation=build_commit_approval_attestation(
                        request_packet_id,
                        pipeline,
                        attested_by=actor,
                        operator_signature=actor,
                    ),
                ),
            )
        except ValueError as exc:
            if "PacketGuardAttestation" in str(exc):
                raise
            pass
    existing_decision = _existing_approval_decision(executor, pipeline)
    if existing_decision is not None:
        status = str(getattr(existing_decision, "status", "") or "").strip()
        if status == "applied":
            return
        if status in {"pending", "acked"}:
            _apply_approval_decision(
                executor,
                artifact_paths,
                packet_id=getattr(existing_decision, "packet_id", ""),
                pipeline=pipeline,
                approval_actor=actor,
            )
            return
    _, decision_event = post_packet(
        repo_root=executor.repo_root,
        review_channel_path=executor.review_channel_path,
        artifact_paths=artifact_paths,
        request=build_commit_approval_decision(
            pipeline,
            approved_by=actor,
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
            guard_attestation=build_commit_approval_attestation(
                decision_event.get("packet_id"),
                pipeline,
                attested_by="operator",
                operator_signature=actor,
            ),
        ),
    )


def _apply_approval_decision(
    executor: GovernedVcsExecutor,
    artifact_paths,
    *,
    packet_id: object,
    pipeline,
    approval_actor: str,
) -> None:
    transition_packet(
        repo_root=executor.repo_root,
        review_channel_path=executor.review_channel_path,
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(packet_id or ""),
            actor="operator",
            guard_attestation=build_commit_approval_attestation(
                packet_id,
                pipeline,
                attested_by="operator",
                operator_signature=approval_actor,
            ),
        ),
    )


def _existing_approval_decision(
    executor: GovernedVcsExecutor,
    pipeline,
):
    return latest_matching_packet(
        executor._event_packets(),
        pipeline,
        require_apply=False,
        request_kind="decision",
        approval_packet_kind=APPROVAL_PACKET_KIND,
    )


def build_commit_approval_attestation(
    packet_id: object,
    pipeline,
    *,
    attested_by: str = "operator",
    operator_signature: str = "operator",
) -> PacketGuardAttestation:
    """Build apply-time evidence for one governed commit approval packet."""
    validation_receipt = getattr(pipeline, "validation_receipt", None)
    guard_action_id = _approval_guard_action_id(pipeline, validation_receipt)
    evidence_paths = _approval_evidence_paths(validation_receipt)
    return PacketGuardAttestation(
        packet_id=str(packet_id or "").strip(),
        attestation_kind="commit_approval_guard",
        run_record_ids=(str(guard_action_id),),
        evidence_artifact_paths=evidence_paths,
        pipeline_generation=str(getattr(pipeline, "generation_id", "") or ""),
        staged_snapshot_hash=str(
            getattr(getattr(pipeline, "intent", None), "staged_tree_hash", "")
            or ""
        ),
        operator_signature=str(operator_signature or attested_by or "operator"),
        attested_by=str(attested_by or "operator"),
    )


def _record_operator_approval_without_refresh(
    executor: GovernedVcsExecutor,
    pipeline,
    *,
    summary: str,
    body: str,
    approval_actor: str,
) -> None:
    """Append approval evidence without rebuilding full review projections."""
    artifact_paths = resolve_artifact_paths(repo_root=executor.repo_root)
    actor = str(approval_actor or "operator").strip() or "operator"
    _append_post_packet_without_refresh(
        repo_root=executor.repo_root,
        artifact_paths=artifact_paths,
        request=build_commit_approval_request(
            pipeline,
            to_agent=actor,
        ),
    )
    request = build_commit_approval_decision(
        pipeline,
        approved_by=actor,
        summary=summary,
        body=body,
    )
    decision_event = _append_post_packet_without_refresh(
        repo_root=executor.repo_root,
        artifact_paths=artifact_paths,
        request=request,
    )
    packet_id = str(decision_event.get("packet_id") or "").strip()
    apply_request = PacketTransitionRequest(
        action="apply",
        packet_id=packet_id,
        actor="operator",
        guard_attestation=build_commit_approval_attestation(
            packet_id,
            pipeline,
            attested_by="operator",
            operator_signature=actor,
        ),
    )
    _append_transition_without_refresh(
        repo_root=executor.repo_root,
        artifact_paths=artifact_paths,
        packet=dict(decision_event),
        request=apply_request,
    )


def _append_post_packet_without_refresh(
    *,
    repo_root: Path,
    artifact_paths,
    request,
) -> dict[str, object]:
    events_path = Path(artifact_paths.event_log_path)
    existing_events = load_events(events_path)
    event = {
        "schema_version": 1,
        "event_id": next_event_id(existing_events),
        "session_id": request.session_id,
        "project_id": project_id_for_repo(repo_root),
        "packet_id": request.packet_id,
        "trace_id": request.trace_id,
        "timestamp_utc": utc_timestamp(),
        "source": "review_channel",
        "plan_id": request.plan_id,
        "controller_run_id": request.controller_run_id,
        "event_type": "packet_posted",
        "from_agent": request.from_agent,
        "to_agent": request.to_agent,
        "kind": request.kind,
        "summary": request.summary.strip(),
        "body": request.body.strip(),
        "evidence_refs": list(request.evidence_refs),
        "guidance_refs": list(request.guidance_refs),
        "context_pack_refs": normalize_context_pack_refs(
            list(request.context_pack_refs)
        ),
        "confidence": request.confidence,
        "requested_action": request.requested_action.strip() or "review_only",
        "policy_hint": request.policy_hint,
        "approval_required": request.approval_required,
        **request.target.to_event_fields(),
        **request.runtime_approval.to_event_fields(),
        **request.guard_bundle_evidence.to_event_fields(),
        "plan_proposal": None,
        "status": "pending",
        "idempotency_key": "",
        "nonce": secrets.token_hex(12),
        "expires_at_utc": future_utc_timestamp(minutes=request.expires_in_minutes),
        "metadata": {},
    }
    return append_event(events_path, event, existing_events=existing_events)


def _append_transition_without_refresh(
    *,
    repo_root: Path,
    artifact_paths,
    packet: dict[str, object],
    request: PacketTransitionRequest,
) -> dict[str, object]:
    events_path = Path(artifact_paths.event_log_path)
    existing_events = load_events(events_path)
    event = build_transition_event(
        packet=packet,
        request=request,
        event_id=next_event_id(existing_events),
        timestamp_utc=utc_timestamp(),
        project_id=project_id_for_repo(repo_root),
    )
    written_event = append_event(
        events_path,
        event,
        existing_events=existing_events,
    )
    return finish_transition_event(
        repo_root=repo_root,
        artifact_paths=artifact_paths,
        packet=packet,
        request=request,
        written_event=written_event,
    )


def _approval_evidence_paths(validation_receipt: object | None) -> tuple[str, ...]:
    if validation_receipt is None:
        return ()
    receipt_id = str(getattr(validation_receipt, "receipt_id", "") or "").strip()
    return (receipt_id,) if receipt_id else ()


def _approval_guard_action_id(
    pipeline: object,
    validation_receipt: object | None,
) -> str:
    action_id = str(getattr(validation_receipt, "action_id", "") or "").strip()
    if action_id:
        return action_id
    action_id = str(getattr(pipeline, "guard_action_id", "") or "").strip()
    if action_id:
        return action_id
    guard_result = getattr(pipeline, "guard_result", None)
    action_id = str(getattr(guard_result, "action_id", "") or "").strip()
    if action_id:
        return action_id
    return "quality.guard_bundle"
