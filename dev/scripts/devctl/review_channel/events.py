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

VALID_AGENT_IDS = {"codex", "claude", "cursor", "operator", "system"}
VALID_PACKET_KINDS = {
    "finding",
    "question",
    "draft",
    "instruction",
    "action_request",
    "approval_request",
    "decision",
    "system_notice",
}
VALID_POLICY_HINTS = {
    "review_only",
    "stage_draft",
    "operator_approval_required",
    "safe_auto_apply",
}
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
    from_agent: str,
    to_agent: str,
    kind: str,
    summary: str,
    body: str,
    evidence_refs: list[str],
    context_pack_refs: list[dict[str, object]],
    confidence: float,
    requested_action: str,
    policy_hint: str,
    approval_required: bool,
    packet_id: str | None = None,
    trace_id: str | None = None,
    session_id: str = DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    plan_id: str = DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    controller_run_id: str | None = None,
    expires_in_minutes: int = DEFAULT_PACKET_TTL_MINUTES,
) -> tuple[ReviewChannelEventBundle, dict[str, object]]:
    """Append one packet_posted event and refresh the reduced state."""
    _validate_post_fields(
        from_agent=from_agent,
        to_agent=to_agent,
        kind=kind,
        summary=summary,
        body=body,
        confidence=confidence,
        policy_hint=policy_hint,
        expires_in_minutes=expires_in_minutes,
    )
    existing_events = load_events(Path(artifact_paths.event_log_path))
    next_packet = packet_id or next_packet_id(existing_events)
    next_trace = trace_id or next_trace_id(existing_events, from_agent=from_agent)
    event = {
        "schema_version": 1,
        "event_id": next_event_id(existing_events),
        "session_id": session_id,
        "project_id": project_id_for_repo(repo_root),
        "packet_id": next_packet,
        "trace_id": next_trace,
        "timestamp_utc": utc_timestamp(),
        "source": "review_channel",
        "plan_id": plan_id,
        "controller_run_id": controller_run_id,
        "event_type": "packet_posted",
        "from_agent": from_agent,
        "to_agent": to_agent,
        "kind": kind,
        "summary": summary.strip(),
        "body": body.strip(),
        "evidence_refs": evidence_refs,
        "context_pack_refs": normalize_context_pack_refs(context_pack_refs),
        "confidence": confidence,
        "requested_action": requested_action.strip() or "review_only",
        "policy_hint": policy_hint,
        "approval_required": approval_required,
        "status": "pending",
        "idempotency_key": idempotency_key(
            "packet_posted",
            next_packet,
            from_agent,
            to_agent,
            summary,
            body,
        ),
        "nonce": secrets.token_hex(12),
        "expires_at_utc": future_utc_timestamp(minutes=expires_in_minutes),
        "metadata": {},
    }
    append_event(
        Path(artifact_paths.event_log_path),
        event,
        existing_events=existing_events,
    )
    bundle = refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    return bundle, event


def transition_packet(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    action: str,
    packet_id: str,
    actor: str,
    session_id: str = DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    plan_id: str = DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    controller_run_id: str | None = None,
) -> tuple[ReviewChannelEventBundle, dict[str, object]]:
    """Append one packet transition event and refresh the reduced state."""
    if action not in TRANSITION_EVENT_TYPES:
        raise ValueError(f"Unsupported packet transition action: {action}")
    if actor not in VALID_AGENT_IDS:
        raise ValueError(f"Unsupported review-channel actor: {actor}")
    bundle = load_or_refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    packet = packet_by_id(bundle.review_state, packet_id)
    if packet is None:
        raise ValueError(f"Unknown review packet: {packet_id}")
    _validate_transition(packet=packet, action=action, actor=actor)
    event_type = TRANSITION_EVENT_TYPES[action]
    event = {
        "schema_version": 1,
        "event_id": next_event_id(bundle.events),
        "session_id": session_id,
        "project_id": project_id_for_repo(repo_root),
        "packet_id": packet_id,
        "trace_id": packet.get("trace_id"),
        "timestamp_utc": utc_timestamp(),
        "source": "review_channel",
        "plan_id": plan_id,
        "controller_run_id": controller_run_id,
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
        "status": {
            "ack": "acked",
            "dismiss": "dismissed",
            "apply": "applied",
        }[action],
        "idempotency_key": idempotency_key(event_type, packet_id, actor),
        "nonce": secrets.token_hex(12),
        "expires_at_utc": packet.get("expires_at_utc"),
        "metadata": {"actor": actor},
    }
    append_event(
        Path(artifact_paths.event_log_path),
        event,
        existing_events=bundle.events,
    )
    refreshed = refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    return refreshed, event


def _validate_post_fields(
    *,
    from_agent: str,
    to_agent: str,
    kind: str,
    summary: str,
    body: str,
    confidence: float,
    policy_hint: str,
    expires_in_minutes: int,
) -> None:
    if from_agent not in VALID_AGENT_IDS:
        raise ValueError(f"Unsupported review-channel from-agent: {from_agent}")
    if to_agent not in VALID_AGENT_IDS:
        raise ValueError(f"Unsupported review-channel to-agent: {to_agent}")
    if kind not in VALID_PACKET_KINDS:
        raise ValueError(f"Unsupported review-channel packet kind: {kind}")
    if not summary.strip():
        raise ValueError("--summary is required for review-channel post.")
    if not body.strip():
        raise ValueError("Review-channel post body is required.")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("--confidence must be between 0.0 and 1.0.")
    if policy_hint not in VALID_POLICY_HINTS:
        raise ValueError(f"Unsupported review-channel policy hint: {policy_hint}")
    if expires_in_minutes <= 0:
        raise ValueError("--expires-in-minutes must be greater than zero.")
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
