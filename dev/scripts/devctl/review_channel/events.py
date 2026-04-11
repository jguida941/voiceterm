"""Public event-backed review-channel helpers."""

from __future__ import annotations

import secrets
from pathlib import Path

from .event_models import ReviewChannelEventBundle
from .event_reducer import (
    filter_history_events,
    filter_inbox_packets,
    load_or_refresh_event_bundle,
    packet_by_id,
    reduce_events,
    refresh_event_bundle,
)
from .action_request_delivery import (
    record_action_request_execution_start,
    seed_action_request_delivery_receipt,
)
from .context_refs import normalize_context_pack_refs
from .event_store import (
    DEFAULT_PACKET_TTL_MINUTES,
    DEFAULT_REVIEW_ARTIFACT_ROOT_REL,
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    DEFAULT_REVIEW_EVENT_LOG_REL,
    DEFAULT_REVIEW_PROJECTIONS_DIR_REL,
    DEFAULT_REVIEW_STATE_JSON_REL,
    ReviewChannelArtifactPaths,
    append_event,
    artifact_paths_to_dict,
    event_state_exists,
    future_utc_timestamp,
    idempotency_key,
    load_events,
    next_event_id,
    next_packet_id,
    next_trace_id,
    resolve_artifact_paths,
)
from .state import project_id_for_repo
from ..time_utils import utc_timestamp
from .packet_contract import (
    PacketPostRequest,
    PacketTransitionRequest,
    validate_post_request,
)
from .packet_agents import (
    packet_agent_ids_from_review_state,
    packet_agent_ids_from_session_output,
)
TRANSITION_EVENT_TYPES = {
    "ack": "packet_acked",
    "dismiss": "packet_dismissed",
    "apply": "packet_applied",
}


def post_packet(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    request: PacketPostRequest,
) -> tuple[ReviewChannelEventBundle, dict[str, object]]:
    """Append one packet_posted event and refresh the reduced state."""

    # Load existing state or fall back to raw event log
    existing_bundle = _load_existing_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    existing_events = (
        existing_bundle.events
        if existing_bundle is not None
        else load_events(Path(artifact_paths.event_log_path))
    )

    # Validate the post request against known agent IDs
    validate_post_request(
        request,
        valid_agent_ids=(
            packet_agent_ids_from_review_state(existing_bundle.review_state)
            if existing_bundle is not None
            else packet_agent_ids_from_session_output(
                Path(artifact_paths.projections_root)
            )
        ),
    )

    # Assign packet and trace IDs (caller-supplied or auto-generated)
    next_packet = request.packet_id or next_packet_id(existing_events)
    next_trace = request.trace_id or next_trace_id(
        existing_events,
        from_agent=request.from_agent,
    )

    event = {
        "schema_version": 1,
        "event_id": next_event_id(existing_events),
        "session_id": request.session_id,
        "project_id": project_id_for_repo(repo_root),
        "packet_id": next_packet,
        "trace_id": next_trace,
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
        "status": "pending",
        "idempotency_key": idempotency_key(
            "packet_posted",
            next_packet,
            request.from_agent,
            request.to_agent,
            request.summary,
            request.body,
        ),
        "nonce": secrets.token_hex(12),
        "expires_at_utc": future_utc_timestamp(minutes=request.expires_in_minutes),
        "metadata": {},
    }

    # Persist event and refresh reduced state
    written_event = append_event(
        Path(artifact_paths.event_log_path),
        event,
        existing_events=existing_events,
    )
    seed_action_request_delivery_receipt(
        artifact_root=Path(artifact_paths.artifact_root),
        packet=written_event,
    )
    bundle = refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    return bundle, written_event


def transition_packet(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    request: PacketTransitionRequest,
) -> tuple[ReviewChannelEventBundle, dict[str, object]]:
    """Append one packet transition event and refresh the reduced state."""

    # Validate the requested action verb
    if request.action not in TRANSITION_EVENT_TYPES:
        raise ValueError(
            f"Unsupported packet transition action: {request.action}"
        )

    # Load current state and resolve the target packet
    bundle = load_or_refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )

    valid_agent_ids = set(packet_agent_ids_from_review_state(bundle.review_state))
    if request.actor not in valid_agent_ids:
        raise ValueError(f"Unsupported review-channel actor: {request.actor}")

    packet = packet_by_id(bundle.review_state, request.packet_id)
    if packet is None:
        raise ValueError(f"Unknown review packet: {request.packet_id}")

    # Enforce transition rules before building the event
    _validate_transition(packet=packet, action=request.action, actor=request.actor)
    event_type = TRANSITION_EVENT_TYPES[request.action]

    event = {
        "schema_version": 1,
        "event_id": next_event_id(bundle.events),
        "session_id": request.session_id,
        "project_id": project_id_for_repo(repo_root),
        "packet_id": request.packet_id,
        "trace_id": packet.get("trace_id"),
        "timestamp_utc": utc_timestamp(),
        "source": "review_channel",
        "plan_id": request.plan_id,
        "controller_run_id": request.controller_run_id,
        "event_type": event_type,
        "from_agent": packet.get("from_agent"),
        "to_agent": packet.get("to_agent"),
        "kind": packet.get("kind"),
        "summary": packet.get("summary"),
        "body": packet.get("body"),
        "evidence_refs": list(packet.get("evidence_refs") or []),
        "guidance_refs": list(packet.get("guidance_refs") or []),
        "context_pack_refs": normalize_context_pack_refs(
            packet.get("context_pack_refs")
        ),
        "confidence": float(packet.get("confidence") or 0.0),
        "requested_action": packet.get("requested_action"),
        "policy_hint": packet.get("policy_hint"),
        "approval_required": bool(packet.get("approval_required")),
        "target_kind": packet.get("target_kind"),
        "target_ref": packet.get("target_ref"),
        "target_revision": packet.get("target_revision"),
        "anchor_refs": list(packet.get("anchor_refs") or []),
        "intake_ref": packet.get("intake_ref"),
        "mutation_op": packet.get("mutation_op"),
        "pipeline_generation": packet.get("pipeline_generation"),
        "staged_snapshot_hash": packet.get("staged_snapshot_hash"),
        "guard_results_summary": packet.get("guard_results_summary"),
        "status": {
            "ack": "acked",
            "dismiss": "dismissed",
            "apply": "applied",
        }[request.action],
        "idempotency_key": idempotency_key(
            event_type,
            request.packet_id,
            request.actor,
        ),
        "nonce": secrets.token_hex(12),
        "expires_at_utc": packet.get("expires_at_utc"),
        "metadata": {"actor": request.actor},
    }

    # Persist event and refresh reduced state
    written_event = append_event(
        Path(artifact_paths.event_log_path),
        event,
        existing_events=bundle.events,
    )
    if request.action in {"ack", "apply"}:
        record_action_request_execution_start(
            artifact_root=Path(artifact_paths.artifact_root),
            packet=packet,
            actor=request.actor,
            started_at_utc=str(written_event.get("timestamp_utc") or ""),
        )
    refreshed = refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    return refreshed, written_event


def _validate_transition(
    *,
    packet: dict[str, object],
    action: str,
    actor: str,
) -> None:
    status = str(packet.get("status") or "").strip()
    to_agent = str(packet.get("to_agent") or "").strip()

    # Ack requires pending status and matching recipient
    if action == "ack":
        if status != "pending":
            raise ValueError(
                f"Packet {packet['packet_id']} cannot be acked from status {status}."
            )
        if actor not in {to_agent, "operator"}:
            raise ValueError(
                f"Packet {packet['packet_id']} can only be acked by {to_agent} "
                "or operator."
            )
        return

    # Dismiss/apply require pending or acked status
    if status not in {"pending", "acked"}:
        raise ValueError(
            f"Packet {packet['packet_id']} cannot transition via {action} from "
            f"status {status}."
        )

    # Apply additionally requires matching recipient
    if action == "apply" and actor not in {to_agent, "operator"}:
        raise ValueError(
            f"Packet {packet['packet_id']} can only be applied by {to_agent} or operator."
        )


def _load_existing_bundle(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
) -> ReviewChannelEventBundle | None:
    try:
        return load_or_refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
    except ValueError:
        return None
