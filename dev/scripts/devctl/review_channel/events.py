"""Public event-backed review-channel helpers."""

from __future__ import annotations

import json
import secrets
from collections.abc import Iterable, Mapping
from pathlib import Path

from ..runtime.review_state_collaboration_models import (
    granted_capabilities_from_row as _granted_capabilities,
)
from ..runtime.packet_transport_expiry import packet_uses_transport_expiry
from ..runtime.review_state_locator import load_current_review_state_payload
from .event_models import ReviewChannelEventBundle
from .event_reducer import (
    filter_history_packets,
    filter_history_events,
    filter_inbox_packets,
    load_or_refresh_event_bundle,
    load_projected_event_bundle,
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
from .packet_plan_context import enrich_packet_request_plan_context
from .packet_route_resolution import resolve_packet_post_route_scope
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
    request = enrich_packet_request_plan_context(
        repo_root=repo_root,
        review_state_payload=(
            existing_bundle.review_state if existing_bundle is not None else None
        ),
        request=request,
    )
    authority_payloads = _action_request_authority_payloads(
        repo_root=repo_root,
        existing_bundle=existing_bundle,
        artifact_paths=artifact_paths,
    )
    request = resolve_packet_post_route_scope(
        request,
        review_state=_first_payload_with_session_state(authority_payloads),
    )
    authority_evidence = _runtime_authority_evidence_from_payloads(
        request=request,
        payloads=authority_payloads,
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
        **request.attention.to_event_fields(),
        **request.target.to_event_fields(),
        **request.runtime_approval.to_event_fields(),
        **request.guard_bundle_evidence.to_event_fields(),
        "plan_proposal": (
            plan_proposal.to_dict() if plan_proposal.has_values() else None
        ),
        "semantic_zref": "",
        "source_identity": {},
        "status": "pending",
        "idempotency_key": "",
        "nonce": secrets.token_hex(12),
        "expires_at_utc": "",
        "metadata": (
            {"runtime_authority_evidence": authority_evidence}
            if authority_evidence
            else {}
        ),
    }
    if packet_uses_transport_expiry(event):
        event["expires_at_utc"] = future_utc_timestamp(
            minutes=request.expires_in_minutes
        )

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
    bundle = _load_existing_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    if bundle is None:
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


def _runtime_authority_evidence_for_request(
    *,
    request: PacketPostRequest,
    review_state: Mapping[str, object],
) -> dict[str, object]:
    """Attach typed actor capability evidence to executable action requests."""
    if request.kind != "action_request":
        return {}
    if request.requested_action not in {"commit", "push", "stage_commit_pipeline"}:
        return {}
    actor_row = _authority_row_for_actor(
        review_state=review_state,
        actor=request.to_agent,
    )
    if not actor_row:
        return {}
    capabilities = _granted_capabilities(actor_row)
    if not _capabilities_grant_action(capabilities):
        return {}
    return {
        "contract_id": "ActionRequestRuntimeAuthorityEvidence",
        "source_contract": _text(actor_row.get("source_contract"))
        or "CollaborationSession",
        "identity_authority_source": _text(actor_row.get("source"))
        or "CollaborationSession",
        "actor_id": _text(actor_row.get("actor_id")),
        "provider": _text(actor_row.get("provider") or actor_row.get("actor_id")),
        "granted_capabilities": list(capabilities),
    }


def _action_request_authority_payloads(
    *,
    repo_root: Path,
    existing_bundle: ReviewChannelEventBundle | None,
    artifact_paths: ReviewChannelArtifactPaths,
) -> tuple[Mapping[str, object], ...]:
    """Return typed review-state payloads in priority order for authority lookup.

    Order: in-memory bundle → governed live locator → reduced state file.
    The locator step closes the gap where actor authority exists only in the
    configured raw review-state candidate before event projection has caught up.
    """
    payloads: list[Mapping[str, object]] = []
    if existing_bundle is not None and isinstance(
        existing_bundle.review_state, Mapping
    ):
        payloads.append(existing_bundle.review_state)
    locator_payload = load_current_review_state_payload(
        repo_root,
        prefer_cached_projection=True,
        allow_live_refresh=False,
    )
    if isinstance(locator_payload, Mapping):
        payloads.append(locator_payload)
    state_payload = _load_state_path_payload(artifact_paths)
    if state_payload:
        payloads.append(state_payload)
    return tuple(payloads)


def _runtime_authority_evidence_from_payloads(
    *,
    request: PacketPostRequest,
    payloads: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Return the first non-empty authority evidence across ordered payloads."""
    for payload in payloads:
        evidence = _runtime_authority_evidence_for_request(
            request=request,
            review_state=payload,
        )
        if evidence:
            return evidence
    return {}


def _first_payload_with_session_state(
    payloads: Iterable[Mapping[str, object]],
) -> Mapping[str, object]:
    for payload in payloads:
        if not isinstance(payload, Mapping):
            continue
        agent_work_board = payload.get("agent_work_board")
        work_board = payload.get("work_board")
        if isinstance(agent_work_board, Mapping) or isinstance(work_board, Mapping):
            return payload
    return {}


def _load_state_path_payload(
    artifact_paths: ReviewChannelArtifactPaths,
) -> dict[str, object]:
    path = Path(artifact_paths.state_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _authority_row_for_actor(
    *,
    review_state: Mapping[str, object],
    actor: str,
) -> Mapping[str, object]:
    target = _text(actor).lower()
    if not target:
        return {}
    collaboration = review_state.get("collaboration")
    if not isinstance(collaboration, Mapping):
        return {}
    for row in _mapping_rows(collaboration.get("actor_authorities")):
        actor_id = _text(row.get("actor_id") or row.get("provider")).lower()
        provider = _text(row.get("provider") or row.get("actor_id")).lower()
        if target in {actor_id, provider} and _is_live(row):
            return row
    return {}




def _capabilities_grant_action(capabilities: tuple[str, ...]) -> bool:
    granted = set(capabilities)
    return bool(
        {"repo.stage_handoff"} & granted
        or {"repo.stage", "repo.commit"}.issubset(granted)
    )


def _mapping_rows(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _is_live(row: Mapping[str, object]) -> bool:
    return bool(row.get("live")) or _text(row.get("status")).lower() == "live"


def _text(value: object) -> str:
    return str(value or "").strip()


def _load_existing_bundle(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
) -> ReviewChannelEventBundle | None:
    projected = load_projected_event_bundle(
        artifact_paths=artifact_paths,
        include_events=True,
    )
    if projected is not None:
        return projected
    try:
        return load_or_refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
    except ValueError:
        return None
