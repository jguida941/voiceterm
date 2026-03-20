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
    VALID_AGENT_IDS,
    validate_post_request,
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
    validate_post_request(request)
    existing_events = load_events(Path(artifact_paths.event_log_path))
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
        "context_pack_refs": normalize_context_pack_refs(
            list(request.context_pack_refs)
        ),
        "confidence": request.confidence,
        "requested_action": request.requested_action.strip() or "review_only",
        "policy_hint": request.policy_hint,
        "approval_required": request.approval_required,
        **request.target.to_event_fields(),
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
    written_event = append_event(
        Path(artifact_paths.event_log_path),
        event,
        existing_events=existing_events,
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
    if request.action not in TRANSITION_EVENT_TYPES:
        raise ValueError(
            f"Unsupported packet transition action: {request.action}"
        )
    if request.actor not in VALID_AGENT_IDS:
        raise ValueError(f"Unsupported review-channel actor: {request.actor}")
    bundle = load_or_refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    packet = packet_by_id(bundle.review_state, request.packet_id)
    if packet is None:
        raise ValueError(f"Unknown review packet: {request.packet_id}")
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
    written_event = append_event(
        Path(artifact_paths.event_log_path),
        event,
        existing_events=bundle.events,
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
    if status not in {"pending", "acked"}:
        raise ValueError(
            f"Packet {packet['packet_id']} cannot transition via {action} from "
            f"status {status}."
        )
    if action == "apply" and actor not in {to_agent, "operator"}:
        raise ValueError(
            f"Packet {packet['packet_id']} can only be applied by {to_agent} or operator."
        )
