"""Safe auto-apply support for tightly scoped review-channel packets."""

from __future__ import annotations

import secrets
from pathlib import Path

from ..time_utils import utc_timestamp
from .action_request_delivery import record_action_request_execution_start
from .context_refs import normalize_context_pack_refs
from .event_store import (
    ReviewChannelArtifactPaths,
    append_event,
    idempotency_key,
    next_event_id,
)
from .packet_attestation import PacketGuardAttestation
from .remote_control_attachment_artifact import heartbeat_repo_remote_control_attachment

SAFE_AUTO_APPLY_ACTION_REQUESTS = frozenset({"stage_commit_pipeline"})
_TRANSITION_EVENT_TYPES = {"ack": "packet_acked", "apply": "packet_applied"}


def append_safe_auto_apply_events(
    *,
    repo_root: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    packet_event: dict[str, object],
    existing_events: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Apply tightly allowlisted system action requests without a manual actor."""
    if not _packet_allows_safe_auto_apply(packet_event):
        return []

    events = list(existing_events)
    written: list[dict[str, object]] = []
    for action in ("ack", "apply"):
        event = _build_auto_transition_event(
            packet_event,
            action=action,
            event_id=next_event_id(events),
        )
        written_event = append_event(
            Path(artifact_paths.event_log_path),
            event,
            existing_events=events,
        )
        events.append(written_event)
        written.append(written_event)
        record_action_request_execution_start(
            artifact_root=Path(artifact_paths.artifact_root),
            packet=packet_event,
            actor="system",
            started_at_utc=str(written_event.get("timestamp_utc") or ""),
        )
    heartbeat_repo_remote_control_attachment(
        repo_root=repo_root,
        provider="system",
        seen_at_utc=str(written[-1].get("timestamp_utc") or ""),
    )
    return written


def _packet_allows_safe_auto_apply(packet: dict[str, object]) -> bool:
    return (
        str(packet.get("event_type") or "").strip() == "packet_posted"
        and str(packet.get("from_agent") or "").strip() == "system"
        and str(packet.get("to_agent") or "").strip() == "claude"
        and str(packet.get("kind") or "").strip() == "action_request"
        and str(packet.get("policy_hint") or "").strip() == "safe_auto_apply"
        and not bool(packet.get("approval_required"))
        and str(packet.get("requested_action") or "").strip()
        in SAFE_AUTO_APPLY_ACTION_REQUESTS
        and str(packet.get("target_kind") or "").strip() == "runtime"
        and str(packet.get("target_ref") or "").strip().startswith("devctl_commit:")
        and bool(str(packet.get("full_guard_bundle_evidence") or "").strip())
    )


def _build_auto_transition_event(
    packet: dict[str, object],
    *,
    action: str,
    event_id: str,
) -> dict[str, object]:
    event_type = _TRANSITION_EVENT_TYPES[action]
    timestamp_utc = utc_timestamp()
    metadata: dict[str, object] = {
        "actor": "system",
        "auto_apply_reason": "safe_auto_apply",
    }
    if action == "apply":
        metadata["guard_attestation"] = PacketGuardAttestation(
            packet_id=str(packet.get("packet_id") or ""),
            attestation_kind="safe_auto_apply_stage_commit_pipeline",
            run_record_ids=(str(packet.get("full_guard_bundle_evidence") or ""),),
            action_result_ids=(f"safe_auto_apply:{event_id}",),
            commit_sha=str(packet.get("target_revision") or ""),
            evidence_artifact_paths=(
                "dev/reports/review_channel/events/trace.ndjson",
            ),
            attested_at_utc=timestamp_utc,
            attested_by="system",
        ).to_dict()
    return dict(
        schema_version=1,
        event_id=event_id,
        session_id=packet.get("session_id"),
        project_id=packet.get("project_id"),
        packet_id=packet.get("packet_id"),
        trace_id=packet.get("trace_id"),
        timestamp_utc=timestamp_utc,
        source="review_channel",
        plan_id=packet.get("plan_id"),
        controller_run_id=packet.get("controller_run_id"),
        event_type=event_type,
        from_agent=packet.get("from_agent"),
        to_agent=packet.get("to_agent"),
        kind=packet.get("kind"),
        summary=packet.get("summary"),
        body=packet.get("body"),
        evidence_refs=list(packet.get("evidence_refs") or []),
        guidance_refs=list(packet.get("guidance_refs") or []),
        context_pack_refs=normalize_context_pack_refs(
            packet.get("context_pack_refs")
        ),
        confidence=float(packet.get("confidence") or 0.0),
        requested_action=packet.get("requested_action"),
        policy_hint=packet.get("policy_hint"),
        approval_required=bool(packet.get("approval_required")),
        target_kind=packet.get("target_kind"),
        target_ref=packet.get("target_ref"),
        target_revision=packet.get("target_revision"),
        anchor_refs=list(packet.get("anchor_refs") or []),
        intake_ref=packet.get("intake_ref"),
        mutation_op=packet.get("mutation_op"),
        pipeline_generation=packet.get("pipeline_generation"),
        staged_snapshot_hash=packet.get("staged_snapshot_hash"),
        guard_results_summary=packet.get("guard_results_summary"),
        full_guard_bundle_evidence=packet.get("full_guard_bundle_evidence"),
        status={"ack": "acked", "apply": "applied"}[action],
        idempotency_key=idempotency_key(
            event_type,
            packet.get("packet_id"),
            "system",
        ),
        nonce=secrets.token_hex(12),
        expires_at_utc=packet.get("expires_at_utc"),
        metadata=metadata,
    )


__all__ = ["SAFE_AUTO_APPLY_ACTION_REQUESTS", "append_safe_auto_apply_events"]
