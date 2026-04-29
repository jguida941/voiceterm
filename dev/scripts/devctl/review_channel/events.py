"""Public event-backed review-channel helpers."""

from __future__ import annotations

import secrets
from pathlib import Path

from .event_models import ReviewChannelEventBundle
from .event_reducer import (
    filter_history_packets,
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
    load_events,
    next_event_id,
    resolve_artifact_paths,
)
from .state import project_id_for_repo
from ..time_utils import utc_timestamp
from .packet_contract import (
    PacketPostRequest,
    PacketTransitionRequest,
    plan_proposal_for_request,
    validate_post_request,
)
from .packet_transition_events import (
    TRANSITION_EVENT_TYPES,
    build_transition_event,
    finish_transition_event,
)
from .packet_agents import (
    packet_agent_ids_from_review_state,
    packet_agent_ids_from_session_output,
)
from .post_packet_runtime import finalize_post_packet


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
        existing_packets=(
            existing_bundle.review_state.get("packets", [])
            if existing_bundle is not None
            else []
        ),
    )
    plan_proposal = plan_proposal_for_request(request)

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
        "plan_proposal": (
            plan_proposal.to_dict() if plan_proposal.has_values() else None
        ),
        "status": "pending",
        "idempotency_key": "",
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
    written_event = finalize_post_packet(
        repo_root=repo_root,
        artifact_paths=artifact_paths,
        written_event=written_event,
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
    timestamp_utc = utc_timestamp()
    event = build_transition_event(
        packet=packet,
        request=request,
        event_id=next_event_id(bundle.events),
        timestamp_utc=timestamp_utc,
        project_id=project_id_for_repo(repo_root),
    )

    # Persist event and refresh reduced state
    written_event = append_event(
        Path(artifact_paths.event_log_path),
        event,
        existing_events=bundle.events,
    )
    written_event = finish_transition_event(
        repo_root=repo_root,
        artifact_paths=artifact_paths,
        packet=packet,
        request=request,
        written_event=written_event,
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
        allowed_actors = _allowed_ack_or_apply_actors(to_agent)
        if actor not in allowed_actors:
            raise ValueError(
                f"Packet {packet['packet_id']} can only be acked by "
                f"{_format_allowed_actors(allowed_actors)}."
            )
        return

    # Dismiss/apply require pending or acked status
    if status not in {"pending", "acked"}:
        raise ValueError(
            f"Packet {packet['packet_id']} cannot transition via {action} from "
            f"status {status}."
        )

    # Apply additionally requires matching recipient
    if action == "apply" and actor not in _allowed_ack_or_apply_actors(to_agent):
        raise ValueError(
            f"Packet {packet['packet_id']} can only be applied by "
            f"{_format_allowed_actors(_allowed_ack_or_apply_actors(to_agent))}."
        )


def _allowed_ack_or_apply_actors(to_agent: str) -> frozenset[str]:
    normalized = str(to_agent or "").strip()
    if not normalized:
        return frozenset()
    if normalized in {"system", "operator"}:
        return frozenset({"operator"})
    return frozenset({normalized})


def _format_allowed_actors(actors: frozenset[str]) -> str:
    ordered = sorted(actor for actor in actors if actor)
    if not ordered:
        return "the addressed actor"
    if len(ordered) == 1:
        return ordered[0]
    return ", ".join(ordered[:-1]) + f", or {ordered[-1]}"


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
