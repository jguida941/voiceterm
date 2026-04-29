"""Lifecycle receipts for packet-authorized governed commits."""

from __future__ import annotations

import secrets
from collections.abc import Mapping
from pathlib import Path

from ...review_channel.context_refs import normalize_context_pack_refs
from ...review_channel.event_store import (
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    append_event,
    idempotency_key,
    load_events,
    next_event_id,
)
from ...review_channel.events import resolve_artifact_paths
from ...review_channel.packet_attestation import PacketGuardAttestation
from ...review_channel.packet_contract import PacketTransitionRequest
from ...review_channel.packet_transition_events import (
    build_transition_event,
    finish_transition_event,
)
from ...review_channel.pending_packets import load_pending_packet_queue
from ...review_channel.state import project_id_for_repo
from ...runtime.review_state_locator import load_current_review_state_payload
from ...time_utils import utc_timestamp


def apply_commit_action_request_packet(
    *,
    repo_root: Path,
    grant: object,
    pipeline: object,
    commit_result: object,
    commit_sha: str,
) -> dict[str, object]:
    """Apply the action_request packet after the governed commit lands."""
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    request = PacketTransitionRequest(
        action="apply",
        packet_id=_field(grant, "packet_id"),
        actor=_grant_actor(grant),
        guard_attestation=_build_apply_attestation(
            grant=grant,
            pipeline=pipeline,
            commit_result=commit_result,
            commit_sha=commit_sha,
        ),
    )
    packet = _packet_for_grant(repo_root=repo_root, grant=grant)
    events_path = Path(artifact_paths.event_log_path)
    existing_events = load_events(events_path)
    event = build_transition_event(
        packet=dict(packet),
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
        packet=dict(packet),
        request=request,
        written_event=written_event,
    )


def record_commit_action_request_execution_failure(
    *,
    repo_root: Path,
    grant: object,
    reason: str,
) -> None:
    """Record blocked execution after an action_request has been acked."""
    packet = _packet_for_grant(repo_root=repo_root, grant=grant)
    if _field(packet, "execution_failed_at_utc"):
        return
    _append_action_request_lifecycle_event(
        repo_root=repo_root,
        packet=packet,
        actor=_grant_actor(grant),
        event_type="action_request_execution_failed",
        status="failed",
        reason=reason,
    )


def record_commit_action_request_apply_pending(
    *,
    repo_root: Path,
    grant: object,
    reason: str,
) -> None:
    """Record commit-landed but packet apply did not persist."""
    packet = _packet_for_grant(repo_root=repo_root, grant=grant)
    if _field(packet, "apply_pending_after_execution_at_utc"):
        return
    _append_action_request_lifecycle_event(
        repo_root=repo_root,
        packet=packet,
        actor=_grant_actor(grant),
        event_type="action_request_apply_pending_after_execution",
        status="apply_pending_after_execution",
        reason=reason,
    )


def _append_action_request_lifecycle_event(
    *,
    repo_root: Path,
    packet: Mapping[str, object],
    actor: str,
    event_type: str,
    status: str,
    reason: str,
) -> dict[str, object]:
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    events_path = Path(artifact_paths.event_log_path)
    existing_events = load_events(events_path)
    timestamp_utc = utc_timestamp()
    event = {
        "schema_version": 1,
        "event_id": next_event_id(existing_events),
        "session_id": _field(packet, "session_id") or DEFAULT_REVIEW_CHANNEL_SESSION_ID,
        "project_id": project_id_for_repo(repo_root),
        "packet_id": _field(packet, "packet_id"),
        "trace_id": _field(packet, "trace_id"),
        "timestamp_utc": timestamp_utc,
        "source": "review_channel",
        "plan_id": _field(packet, "plan_id") or DEFAULT_REVIEW_CHANNEL_PLAN_ID,
        "controller_run_id": packet.get("controller_run_id"),
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
        "full_guard_bundle_evidence": packet.get("full_guard_bundle_evidence"),
        "semantic_zref": (
            packet.get("semantic_zref") or f"packet:{_field(packet, 'packet_id')}"
        ),
        "source_identity": _source_identity(packet),
        "status": status,
        "idempotency_key": idempotency_key(
            event_type,
            _field(packet, "packet_id"),
            actor,
        ),
        "nonce": secrets.token_hex(12),
        "expires_at_utc": packet.get("expires_at_utc"),
        "metadata": {
            "actor": actor,
            "reason": str(reason or "").strip() or status,
        },
    }
    return append_event(
        events_path,
        event,
        existing_events=existing_events,
    )


def _build_apply_attestation(
    *,
    grant: object,
    pipeline: object,
    commit_result: object,
    commit_sha: str,
) -> PacketGuardAttestation:
    guard_action_id = _guard_action_id(pipeline)
    action_result_ids = tuple(
        item
        for item in (
            _field(getattr(pipeline, "commit_result", None), "action_id"),
            _field(commit_result, "action_id"),
            _field(getattr(pipeline, "guard_result", None), "action_id"),
        )
        if item
    )
    evidence_paths = _evidence_paths(pipeline, commit_result)
    return PacketGuardAttestation(
        packet_id=_field(grant, "packet_id"),
        attestation_kind="stage_commit_pipeline_result",
        run_record_ids=(guard_action_id,),
        action_result_ids=action_result_ids or ("vcs.commit",),
        commit_sha=str(commit_sha or "").strip(),
        evidence_artifact_paths=evidence_paths,
        attested_by=_grant_actor(grant),
        pipeline_generation=_field(pipeline, "generation_id"),
        staged_snapshot_hash=_field(getattr(pipeline, "intent", None), "staged_tree_hash"),
    )


def _guard_action_id(pipeline: object) -> str:
    guard_action_id = _field(pipeline, "guard_action_id")
    if guard_action_id:
        return guard_action_id
    guard_result = getattr(pipeline, "guard_result", None)
    action_id = _field(guard_result, "action_id")
    return action_id or "quality.guard_bundle"


def _evidence_paths(pipeline: object, commit_result: object) -> tuple[str, ...]:
    rows: list[str] = []
    for source in (
        getattr(pipeline, "validation_receipt", None),
        getattr(pipeline, "guard_result", None),
        getattr(pipeline, "commit_result", None),
        commit_result,
    ):
        receipt_id = _field(source, "receipt_id")
        if receipt_id:
            rows.append(receipt_id)
        for path in tuple(getattr(source, "artifact_paths", ()) or ()):
            text = str(path or "").strip()
            if text:
                rows.append(text)
    if not rows:
        rows.append("dev/reports/review_channel/projections/latest/commit_pipeline.json")
    return tuple(dict.fromkeys(rows))


def _packet_for_grant(*, repo_root: Path, grant: object) -> Mapping[str, object]:
    packet_id = _field(grant, "packet_id")
    enriched = _packet_from_review_state(repo_root=repo_root, packet_id=packet_id)
    if enriched:
        return enriched
    try:
        queue = load_pending_packet_queue(repo_root, fail_closed=True)
    except ValueError:
        queue = None
    if queue is not None:
        for packet in (*queue.pending_packets, *queue.control_packets):
            if str(packet.get("packet_id") or "").strip() == packet_id:
                return dict(packet)
    return _packet_from_grant(grant)


def _packet_from_review_state(
    *,
    repo_root: Path,
    packet_id: str,
) -> Mapping[str, object]:
    payload = load_current_review_state_payload(
        repo_root,
        prefer_cached_projection=True,
        allow_live_refresh=False,
    )
    if not isinstance(payload, Mapping):
        return {}
    packets = payload.get("packets")
    if not isinstance(packets, list):
        return {}
    for packet in packets:
        if not isinstance(packet, Mapping):
            continue
        if str(packet.get("packet_id") or "").strip() == packet_id:
            return dict(packet)
    return {}


def _packet_from_grant(grant: object) -> Mapping[str, object]:
    return {
        "packet_id": _field(grant, "packet_id"),
        "trace_id": "",
        "kind": "action_request",
        "to_agent": _field(grant, "target_agent"),
        "requested_action": _field(grant, "requested_action"),
        "target_kind": "runtime",
        "target_ref": _field(grant, "target_ref"),
        "target_revision": _field(grant, "target_revision"),
        "pipeline_generation": _field(grant, "pipeline_generation"),
        "staged_snapshot_hash": _field(grant, "staged_snapshot_hash"),
        "full_guard_bundle_evidence": _field(grant, "full_guard_bundle_evidence"),
    }


def _source_identity(packet: Mapping[str, object]) -> dict[str, object]:
    raw = packet.get("source_identity")
    if not isinstance(raw, Mapping):
        return {}
    return {
        str(key).strip(): str(value or "").strip()
        for key, value in raw.items()
        if str(key).strip() and str(value or "").strip()
    }


def _grant_actor(grant: object) -> str:
    return _field(grant, "caller_agent") or _field(grant, "target_agent")


def _field(value: object, name: str) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return str(value.get(name) or "").strip()
    return str(getattr(value, name, "") or "").strip()
