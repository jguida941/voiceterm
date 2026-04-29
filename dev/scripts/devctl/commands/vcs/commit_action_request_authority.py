"""Packet-scoped authority bridge for governed commit."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from ...repo_packs import active_path_config
from ...review_channel.event_store import append_event, load_events, next_event_id
from ...review_channel.events import resolve_artifact_paths
from ...review_channel.packet_contract import PacketTransitionRequest
from ...review_channel.packet_transition_events import (
    build_transition_event,
    finish_transition_event,
)
from ...review_channel.pending_packets import load_pending_packet_queue
from ...review_channel.state import project_id_for_repo
from ...runtime.review_state_locator import load_current_review_state_payload
from ...time_utils import utc_timestamp

_CALLER_AGENT_ENV_VARS = ("DEVCTL_CALLER_AGENT", "REVIEW_CHANNEL_CALLER_AGENT")
_CALLER_ROLE_ENV_VARS = ("DEVCTL_CALLER_ROLE", "REVIEW_CHANNEL_CALLER_ROLE")
_SUPPORTED_REQUEST_ACTION = "stage_commit_pipeline"
_SAFE_POLICY_HINT = "safe_auto_apply"
_STAGE_HANDOFF_CAPABILITIES = ("repo.stage_handoff",)
_COMMIT_CAPABILITIES = ("repo.stage", "repo.commit")
_ACTIONABLE_PACKET_STATUSES = frozenset({"pending", "acked"})
_ACTION_REQUEST_INTERACTION_MODES = frozenset({"remote_control", "dual_agent"})


@dataclass(frozen=True, slots=True)
class CommitActionRequestGrant:
    """Scoped authority derived from one review-channel action_request."""

    packet_id: str
    authorized: bool
    reason: str
    caller_role: str = ""
    caller_role_source: str = ""
    caller_agent: str = ""
    caller_agent_source: str = ""
    interaction_mode: str = ""
    target_agent: str = ""
    requested_action: str = ""
    target_ref: str = ""
    target_revision: str = ""
    pipeline_generation: str = ""
    staged_snapshot_hash: str = ""
    full_guard_bundle_evidence: str = ""
    granted_capabilities: tuple[str, ...] = ()
    execution_receipt_event_id: str = ""
    apply_event_id: str = ""
    lifecycle_state: str = ""
    execution_failure_reason: str = ""
    apply_pending_reason: str = ""
    identity_authority_source: str = ""
    identity_authority_capabilities: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["granted_capabilities"] = list(self.granted_capabilities)
        payload["identity_authority_capabilities"] = list(
            self.identity_authority_capabilities
        )
        payload["warnings"] = list(self.warnings)
        return payload


def resolve_commit_action_request_grant(
    *,
    args: object,
    repo_root: Path,
    pipeline: object | None = None,
    interaction_mode: str = "",
) -> CommitActionRequestGrant | None:
    """Return a scoped commit grant when ``--action-request`` is present."""
    packet_id = _text(getattr(args, "action_request", ""))
    if not packet_id:
        return None

    packet = _load_action_request_packet(repo_root=repo_root, packet_id=packet_id)
    caller_role, caller_role_source = _resolve_caller_role(args)
    caller_agent, caller_agent_source = _resolve_caller_agent(
        repo_root=repo_root,
        caller_role=caller_role,
    )
    base = CommitActionRequestGrant(
        packet_id=packet_id,
        authorized=False,
        reason="action_request_not_validated",
        caller_role=caller_role,
        caller_role_source=caller_role_source,
        caller_agent=caller_agent,
        caller_agent_source=caller_agent_source,
        interaction_mode=_text(interaction_mode),
        target_agent=_text(packet.get("to_agent")) if packet else "",
        requested_action=_text(packet.get("requested_action")) if packet else "",
        target_ref=_text(packet.get("target_ref")) if packet else "",
        target_revision=_text(packet.get("target_revision")) if packet else "",
        pipeline_generation=_text(packet.get("pipeline_generation")) if packet else "",
        staged_snapshot_hash=_text(packet.get("staged_snapshot_hash")) if packet else "",
        full_guard_bundle_evidence=(
            _text(packet.get("full_guard_bundle_evidence")) if packet else ""
        ),
    )
    if packet is None:
        return replace(base, reason="action_request_not_found")

    denial = _deny_reason(
        repo_root=repo_root,
        packet=packet,
        grant=base,
        pipeline=pipeline,
    )
    if denial:
        return replace(base, reason=denial)

    identity_source, identity_capabilities = _identity_authority(
        repo_root=repo_root,
        grant=base,
    )
    granted_capabilities = _granted_action_capabilities(identity_capabilities)
    return replace(
        base,
        authorized=True,
        reason="action_request_authorized",
        granted_capabilities=granted_capabilities,
        identity_authority_source=identity_source,
        identity_authority_capabilities=identity_capabilities,
    )


def mark_commit_action_request_execution_started(
    *,
    repo_root: Path,
    grant: CommitActionRequestGrant,
) -> CommitActionRequestGrant:
    """Ack the action_request so replay becomes visible in packet lifecycle."""
    if not grant.authorized:
        return grant
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    packet = _load_action_request_packet(repo_root=repo_root, packet_id=grant.packet_id)
    if packet is not None and _text(packet.get("status")) == "acked":
        return replace(
            grant,
            execution_receipt_event_id=_execution_started_event_id(packet),
        )
    event = _append_action_request_ack_event(
        repo_root=repo_root,
        artifact_paths=artifact_paths,
        packet=packet,
        grant=grant,
    )
    return replace(
        grant,
        execution_receipt_event_id=_text(event.get("event_id")),
    )


def _append_action_request_ack_event(
    *,
    repo_root: Path,
    artifact_paths,
    packet: Mapping[str, object],
    grant: CommitActionRequestGrant,
) -> dict[str, object]:
    """Append a packet ACK without forcing a full review-state refresh."""
    actor = grant.caller_agent or grant.target_agent
    request = PacketTransitionRequest(
        action="ack",
        packet_id=grant.packet_id,
        actor=actor,
    )
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


def _execution_started_event_id(packet: Mapping[str, object]) -> str:
    for row in reversed(_rows(packet.get("acknowledged_events"))):
        if _text(row.get("action")) == "execution_started" or _text(
            row.get("event_kind")
        ) == "execution_started":
            return _text(row.get("event_id"))
    return _text(packet.get("latest_event_id")) or _text(packet.get("event_id"))


def action_request_authority_block_report(
    grant: CommitActionRequestGrant,
) -> dict[str, object]:
    """Render a blocking report for an invalid explicit action request."""
    return {
        "status": "blocked",
        "reason": "action_request_authority_blocked",
        "action_request_authority": grant.to_dict(),
        "action_request_reason": grant.reason,
        "blocked_actions": ["vcs.stage", "vcs.commit", "git.commit"],
        "operator_guidance": (
            "The requested action_request packet does not grant this governed "
            "commit invocation. Refresh typed packet state or request a new "
            "scoped action_request instead of reconstructing commit scope by hand."
        ),
    }


def action_request_execution_receipt_report(
    *,
    grant: CommitActionRequestGrant,
    error: Exception,
) -> dict[str, object]:
    """Render a blocking report when execution-start receipt cannot be recorded."""
    return {
        "status": "blocked",
        "reason": "action_request_execution_receipt_failed",
        "action_request_authority": grant.to_dict(),
        "errors": [str(error)],
        "blocked_actions": ["vcs.stage", "vcs.commit", "git.commit"],
        "operator_guidance": (
            "The action_request grant was valid, but devctl could not write the "
            "execution-start lifecycle receipt. Do not retry through a raw git "
            "path; repair the packet lifecycle write and rerun the governed command."
        ),
    }


def _deny_reason(
    *,
    repo_root: Path,
    packet: Mapping[str, object],
    grant: CommitActionRequestGrant,
    pipeline: object | None,
) -> str:
    if _text(packet.get("kind")) != "action_request":
        return "action_request_kind_mismatch"
    if _text(packet.get("status")) not in _ACTIONABLE_PACKET_STATUSES:
        return "action_request_not_actionable"
    if _text(packet.get("execution_failed_at_utc")):
        return "action_request_execution_failed"
    if _text(packet.get("apply_pending_after_execution_at_utc")):
        return "action_request_apply_pending_after_execution"
    if _is_expired(packet):
        return "action_request_expired"
    if grant.caller_agent and grant.target_agent != grant.caller_agent:
        return "action_request_target_mismatch"
    if not grant.caller_agent:
        return "action_request_caller_identity_missing"
    if grant.interaction_mode not in _ACTION_REQUEST_INTERACTION_MODES:
        return "action_request_interaction_mode_not_remote"
    if not _identity_authority(repo_root=repo_root, grant=grant)[0]:
        return "action_request_actor_authority_missing"
    if grant.requested_action != _SUPPORTED_REQUEST_ACTION:
        return "action_request_unsupported_requested_action"
    if _text(packet.get("policy_hint")) != _SAFE_POLICY_HINT:
        return "action_request_policy_not_safe"
    if _text(packet.get("target_kind")) != "runtime":
        return "action_request_target_kind_mismatch"
    if not grant.target_ref.startswith("devctl_commit:"):
        return "action_request_target_ref_mismatch"
    if not grant.full_guard_bundle_evidence:
        return "action_request_guard_evidence_missing"

    head = _current_head(repo_root)
    target_ref_revision = grant.target_ref.removeprefix("devctl_commit:")
    if grant.target_revision and grant.target_revision != head:
        return "action_request_target_revision_stale"
    if target_ref_revision and target_ref_revision != head:
        return "action_request_target_ref_stale"

    pipeline_generation = _pipeline_generation(pipeline)
    pipeline_hash = _pipeline_hash(pipeline)
    if pipeline_generation or pipeline_hash:
        if not grant.pipeline_generation:
            return "action_request_pipeline_generation_missing"
        if not grant.staged_snapshot_hash:
            return "action_request_staged_snapshot_missing"
    if grant.pipeline_generation and grant.pipeline_generation != pipeline_generation:
        return "action_request_pipeline_generation_mismatch"
    if grant.staged_snapshot_hash and grant.staged_snapshot_hash != pipeline_hash:
        return "action_request_staged_snapshot_mismatch"
    return ""


def _identity_authority(
    *,
    repo_root: Path,
    grant: CommitActionRequestGrant,
) -> tuple[str, tuple[str, ...]]:
    """Return actor-authority evidence for the target packet executor."""
    for payload in (
        _load_review_state(repo_root),
        _load_review_state_from_path_config(repo_root),
    ):
        authority = _identity_authority_from_payload(payload, grant=grant)
        if authority[0]:
            return authority
    return "", ()


def _identity_authority_from_payload(
    payload: Mapping[str, object],
    *,
    grant: CommitActionRequestGrant,
) -> tuple[str, tuple[str, ...]]:
    collaboration = _mapping(payload.get("collaboration"))
    actor_rows = _rows(collaboration.get("actor_authorities"))
    if not actor_rows:
        return "", ()
    required_any = {"repo.stage_handoff"}
    required_all = {"repo.stage", "repo.commit"}
    for row in actor_rows:
        actor_id = _text(row.get("actor_id") or row.get("provider")).lower()
        provider = _text(row.get("provider") or row.get("actor_id")).lower()
        if grant.caller_agent not in {actor_id, provider}:
            continue
        if not _is_live(row):
            continue
        capabilities = _granted_capabilities(row)
        if required_any & set(capabilities) or required_all.issubset(capabilities):
            return _text(row.get("source")) or "CollaborationSession", capabilities
    return "", ()


def _granted_action_capabilities(
    identity_capabilities: tuple[str, ...],
) -> tuple[str, ...]:
    capabilities = set(identity_capabilities)
    if {"repo.stage", "repo.commit"}.issubset(capabilities):
        return _COMMIT_CAPABILITIES
    if "repo.stage_handoff" in capabilities:
        return _STAGE_HANDOFF_CAPABILITIES
    return ()


def _granted_capabilities(row: Mapping[str, object]) -> tuple[str, ...]:
    capabilities: list[str] = []
    for grant in _rows(row.get("grants")):
        if not bool(grant.get("granted")):
            continue
        capability = _text(grant.get("capability"))
        if capability:
            capabilities.append(capability)
    return tuple(capabilities)


def _load_action_request_packet(
    *,
    repo_root: Path,
    packet_id: str,
) -> dict[str, object] | None:
    enriched_packet = _load_action_request_packet_from_review_state(
        repo_root=repo_root,
        packet_id=packet_id,
    )
    queue = load_pending_packet_queue(repo_root, fail_closed=True)
    for packet in (*queue.pending_packets, *queue.control_packets):
        if _text(packet.get("packet_id")) == packet_id:
            merged = dict(enriched_packet or {})
            merged.update(dict(packet))
            if enriched_packet:
                for field in ("semantic_zref", "source_identity"):
                    if not merged.get(field) and enriched_packet.get(field):
                        merged[field] = enriched_packet[field]
            return merged
    return dict(enriched_packet) if enriched_packet else None


def _load_action_request_packet_from_review_state(
    *,
    repo_root: Path,
    packet_id: str,
) -> dict[str, object] | None:
    payload = _load_review_state(repo_root)
    packets = payload.get("packets")
    if not isinstance(packets, list):
        return None
    for packet in packets:
        if not isinstance(packet, Mapping):
            continue
        if _text(packet.get("packet_id")) == packet_id:
            return dict(packet)
    return None


def _resolve_caller_role(args: object) -> tuple[str, str]:
    explicit_role = _normalize_role(getattr(args, "role", None))
    if explicit_role:
        return explicit_role, "arg:role"
    for env_name in _CALLER_ROLE_ENV_VARS:
        env_role = _normalize_role(os.environ.get(env_name))
        if env_role:
            return env_role, f"env:{env_name}"
    return "", ""


def _resolve_caller_agent(*, repo_root: Path, caller_role: str) -> tuple[str, str]:
    for env_name in _CALLER_AGENT_ENV_VARS:
        env_agent = _text(os.environ.get(env_name)).lower()
        if env_agent:
            return env_agent, f"env:{env_name}"
    inferred = _caller_agent_from_review_state(repo_root=repo_root, role=caller_role)
    if inferred:
        return inferred, "review_state:collaboration"
    return "", ""


def _caller_agent_from_review_state(*, repo_root: Path, role: str) -> str:
    payload = _load_review_state(repo_root)
    collaboration = payload.get("collaboration") if isinstance(payload, Mapping) else {}
    role_ids = {
        "dashboard": ("operator_agent",),
        "observer": ("operator_agent",),
        "reviewer": ("review_agent",),
        "implementer": ("coding_agent",),
    }.get(role, ())
    for row in _rows(_mapping(collaboration).get("role_assignments")):
        if _text(row.get("role_id")) in role_ids and _is_live(row):
            return _text(row.get("agent_id") or row.get("provider")).lower()
    return ""


def _load_review_state(repo_root: Path) -> dict[str, object]:
    payload = load_current_review_state_payload(
        repo_root,
        prefer_cached_projection=True,
        allow_live_refresh=False,
    )
    if isinstance(payload, Mapping):
        merged = dict(payload)
        fallback = _load_review_state_from_path_config(repo_root)
        if not _rows(_mapping(merged.get("collaboration")).get("actor_authorities")):
            fallback_collaboration = _mapping(fallback.get("collaboration"))
            if fallback_collaboration:
                merged_collaboration = dict(_mapping(merged.get("collaboration")))
                merged_collaboration.update(fallback_collaboration)
                merged["collaboration"] = merged_collaboration
        return merged
    return _load_review_state_from_path_config(repo_root)


def _load_review_state_from_path_config(repo_root: Path) -> dict[str, object]:
    config = active_path_config()
    candidates = [
        repo_root / config.review_status_dir_rel / "review_state.json",
        *(
            repo_root / candidate
            for candidate in config.review_state_candidates
        ),
        repo_root / config.review_state_json_rel,
    ]
    for path in candidates:
        try:
            if path.is_file():
                candidate_payload = json.loads(path.read_text(encoding="utf-8"))
            else:
                continue
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(candidate_payload, dict):
            return candidate_payload
    return {}


def _current_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _is_expired(packet: Mapping[str, object]) -> bool:
    raw = _text(packet.get("expires_at_utc"))
    if not raw:
        return False
    try:
        expires_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at.astimezone(timezone.utc) <= datetime.now(timezone.utc)


def _pipeline_generation(pipeline: object | None) -> str:
    return _text(getattr(pipeline, "generation_id", ""))


def _pipeline_hash(pipeline: object | None) -> str:
    intent = getattr(pipeline, "intent", None)
    return _text(getattr(intent, "staged_tree_hash", ""))


def _rows(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _is_live(row: Mapping[str, object]) -> bool:
    return bool(row.get("live")) or _text(row.get("status")).lower() == "live"


def _normalize_role(value: object) -> str:
    role = _text(value).lower()
    return role if role in {"dashboard", "implementer", "observer", "reviewer"} else ""


def _text(value: object) -> str:
    return str(value or "").strip()
