"""Packet-scoped authority bridge for governed commit."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from ...repo_packs import active_path_config
from ...review_channel.event_store import append_event, load_events, next_event_id
from ...review_channel.events import resolve_artifact_paths
from ...runtime.review_state_collaboration_models import (
    granted_capabilities_from_row as _granted_capabilities,
)
from ...review_channel.packet_contract import PacketTransitionRequest
from ...review_channel.packet_transition_events import (
    build_transition_event,
    finish_transition_event,
)
from ...review_channel.pending_packets import load_pending_packet_queue
from ...review_channel.state import project_id_for_repo
from ...runtime.review_state_locator import load_current_review_state_payload
from ...time_utils import utc_timestamp
from .commit_action_request_evidence import (
    capabilities_grant_action,
    derive_caller_role,
    derive_pipeline_evidence,
    invalid_evidence_fields,
    missing_evidence_fields,
    policy_denial,
    target_actor_has_action_authority,
)
from .commit_action_request_lifecycle_gate import lifecycle_status_block
from .commit_action_request_pipeline import pipeline_binding_block
from .commit_action_request_revision import target_revision_freshness_block

_CALLER_AGENT_ENV_VARS = ("DEVCTL_CALLER_AGENT", "REVIEW_CHANNEL_CALLER_AGENT")
_CALLER_ROLE_ENV_VARS = ("DEVCTL_CALLER_ROLE", "REVIEW_CHANNEL_CALLER_ROLE")
_SUPPORTED_REQUEST_ACTION = "stage_commit_pipeline"
_STAGE_HANDOFF_CAPABILITIES = ("repo.stage_handoff",)
_COMMIT_CAPABILITIES = ("repo.stage", "repo.commit")
_ACTION_REQUEST_INTERACTION_MODES = frozenset({"remote_control", "dual_agent"})


@dataclass(frozen=True, slots=True)
class CommitActionRequestGrant:
    """Scoped authority derived from one review-channel action_request."""

    packet_id: str
    authorized: bool
    reason: str
    caller_role: str = ""
    caller_role_source: str = ""
    caller_role_label: str = ""
    caller_session_id: str = ""
    caller_session_id_source: str = ""
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
    derived_fields: tuple[str, ...] = ()
    derivation_sources: tuple[str, ...] = ()
    missing_evidence_fields: tuple[str, ...] = ()
    invalid_evidence_fields: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["granted_capabilities"] = list(self.granted_capabilities)
        payload["identity_authority_capabilities"] = list(
            self.identity_authority_capabilities
        )
        payload["derived_fields"] = list(self.derived_fields)
        payload["derivation_sources"] = list(self.derivation_sources)
        payload["missing_evidence_fields"] = list(self.missing_evidence_fields)
        payload["invalid_evidence_fields"] = list(self.invalid_evidence_fields)
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
        packet=packet,
    )
    if caller_agent and not caller_role:
        caller_role, caller_role_source = derive_caller_role(
            caller_agent=caller_agent,
            payloads=_review_state_payloads(repo_root),
        )
    caller_role_label, _ = _resolve_caller_role_label(
        repo_root=repo_root, caller_agent=caller_agent
    )
    caller_session_id, caller_session_id_source = _resolve_caller_session_id()
    base = CommitActionRequestGrant(
        packet_id=packet_id,
        authorized=False,
        reason="action_request_not_validated",
        caller_role=caller_role,
        caller_role_source=caller_role_source,
        caller_role_label=caller_role_label,
        caller_session_id=caller_session_id,
        caller_session_id_source=caller_session_id_source,
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

    base = derive_pipeline_evidence(
        repo_root=repo_root,
        packet=packet,
        grant=base,
        pipeline=pipeline,
    )
    identity_source, identity_capabilities = _identity_authority(
        repo_root=repo_root,
        grant=base,
    )
    granted_capabilities = _granted_action_capabilities(identity_capabilities)
    base = replace(
        base,
        granted_capabilities=granted_capabilities,
        identity_authority_source=identity_source,
        identity_authority_capabilities=identity_capabilities,
    )
    denial = _deny_reason(
        repo_root=repo_root,
        packet=packet,
        grant=base,
        pipeline=pipeline,
    )
    if denial:
        return replace(
            base,
            reason=denial,
            missing_evidence_fields=missing_evidence_fields(
                repo_root=repo_root,
                packet=packet,
                grant=base,
                pipeline=pipeline,
            ),
            invalid_evidence_fields=invalid_evidence_fields(
                repo_root=repo_root,
                packet=packet,
                grant=base,
                pipeline=pipeline,
                denial=denial,
            ),
        )

    return replace(
        base,
        authorized=True,
        reason="action_request_authorized",
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


def _caller_identity_block(grant: CommitActionRequestGrant) -> str:
    if grant.caller_agent and grant.target_agent != grant.caller_agent:
        return "action_request_target_mismatch"
    if not grant.caller_agent:
        return "action_request_caller_identity_missing"
    return ""


def _env_pivot_block() -> str:
    pivot_block_env = _text(os.environ.get("DEVCTL_PIVOT_REQUIRED", ""))
    if pivot_block_env and pivot_block_env.lower() not in {"0", "false", "no", ""}:
        return "action_request_inbox_pivot_required"
    return ""


def _grant_attestation_block(
    packet: Mapping[str, object],
    grant: CommitActionRequestGrant,
) -> str:
    if grant.interaction_mode not in _ACTION_REQUEST_INTERACTION_MODES:
        return "action_request_interaction_mode_not_remote"
    if not grant.identity_authority_source:
        return "action_request_actor_authority_missing"
    if grant.requested_action != _SUPPORTED_REQUEST_ACTION:
        return "action_request_unsupported_requested_action"
    policy_block = policy_denial(packet=packet, grant=grant)
    if policy_block:
        return policy_block
    if _text(packet.get("target_kind")) != "runtime":
        return "action_request_target_kind_mismatch"
    if not grant.target_ref.startswith("devctl_commit:"):
        return "action_request_target_ref_mismatch"
    if not grant.full_guard_bundle_evidence:
        return "action_request_guard_evidence_missing"
    return ""


def _target_discriminator_block(
    packet: Mapping[str, object],
    grant: CommitActionRequestGrant,
) -> str:
    # Per rev_pkt_2472 + rev_pkt_2549/2551 (Plan 4.1 Scope 2): when the packet
    # was scoped to a specific role or session (e.g. coder-claude vs
    # dashboard-claude), refuse the grant unless the caller's resolved typed
    # role/session matches. Typed grant authority wins; env vars are accepted
    # only as compatibility evidence so a spoofed env cannot satisfy the
    # discriminator and a typed-authorized caller without that exact env
    # label is not falsely blocked. Empty target_role / target_session_id
    # leaves the legacy any-claude behavior intact for older packets.
    target_role = _text(_mapping(packet.get("target")).get("target_role"))
    if not target_role:
        target_role = _text(packet.get("target_role"))
    target_session_id = _text(_mapping(packet.get("target")).get("target_session_id"))
    if not target_session_id:
        target_session_id = _text(packet.get("target_session_id"))
    if target_role:
        typed_role = _text(grant.caller_role_label) or _text(grant.caller_role)
        env_role = _text(os.environ.get("DEVCTL_CALLER_ROLE_LABEL", ""))
        caller_role = typed_role or env_role
        if caller_role and caller_role != target_role:
            return "action_request_target_role_mismatch"
        if not caller_role:
            return "action_request_target_role_unset"
    if target_session_id:
        typed_session = _text(grant.caller_session_id)
        env_session = _text(os.environ.get("DEVCTL_CALLER_SESSION_ID", ""))
        caller_session = typed_session or env_session
        if caller_session and caller_session != target_session_id:
            return "action_request_target_session_mismatch"
        if not caller_session:
            return "action_request_target_session_unset"
    return ""


def _deny_reason(
    *,
    repo_root: Path,
    packet: Mapping[str, object],
    grant: CommitActionRequestGrant,
    pipeline: object | None,
) -> str:
    # Phase chain. Each helper returns "" when its phase is clean and a
    # specific denial reason string when the gate must block. Order matters:
    # lifecycle terminals before identity, identity before discriminator,
    # typed packet-attention (rev_pkt_2498 durable authority) before the
    # legacy env pivot fallback, attestations/freshness before pipeline.
    return (
        lifecycle_status_block(packet)
        or _caller_identity_block(grant)
        or _target_discriminator_block(packet, grant)
        or _typed_packet_attention_block(repo_root=repo_root)
        or _env_pivot_block()
        or _grant_attestation_block(packet, grant)
        or target_revision_freshness_block(repo_root=repo_root, grant=grant)
        or pipeline_binding_block(
            repo_root=repo_root, grant=grant, pipeline=pipeline
        )
    )


def _identity_authority(
    *,
    repo_root: Path,
    grant: CommitActionRequestGrant,
) -> tuple[str, tuple[str, ...]]:
    """Return actor-authority evidence for the target packet executor."""
    for payload in (
        _load_review_state(repo_root),
        *_load_review_state_payloads_from_path_config(repo_root),
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
    for row in actor_rows:
        actor_id = _text(row.get("actor_id") or row.get("provider")).lower()
        provider = _text(row.get("provider") or row.get("actor_id")).lower()
        if grant.caller_agent not in {actor_id, provider}:
            continue
        if not _is_live(row):
            continue
        capabilities = _granted_capabilities(row)
        if capabilities_grant_action(capabilities):
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


def _resolve_caller_role_label(
    *, repo_root: Path, caller_agent: str
) -> tuple[str, str]:
    # Per rev_pkt_2549/2551 (Plan 4.1 Scope 2): the discriminator gate must
    # consult typed session-posture authority for the caller's role label
    # (e.g. coder-claude vs dashboard-claude) before falling back to env.
    # Returns (label, source) where source is "session_posture" when typed
    # state resolved or "env:DEVCTL_CALLER_ROLE_LABEL" when env was used.
    if caller_agent:
        review_state = _load_review_state(repo_root)
        posture = _mapping(review_state.get("session_posture"))
        actors_value = posture.get("actors")
        if isinstance(actors_value, list | tuple):
            for actor in actors_value:
                if not isinstance(actor, Mapping):
                    continue
                actor_id = _text(actor.get("actor_id"))
                provider = _text(actor.get("provider"))
                if caller_agent in {actor_id, provider}:
                    if actor_id:
                        return actor_id, "session_posture"
    env_label = _text(os.environ.get("DEVCTL_CALLER_ROLE_LABEL", ""))
    if env_label:
        return env_label, "env:DEVCTL_CALLER_ROLE_LABEL"
    return "", ""


def _resolve_caller_session_id() -> tuple[str, str]:
    # Typed session-id authority would live on SessionPostureActor; until
    # that field exists we still accept env as the source so the
    # discriminator gate has a value to compare. Codex follow-up: add
    # SessionPostureActor.session_id and prefer it here.
    env_session = _text(os.environ.get("DEVCTL_CALLER_SESSION_ID", ""))
    if env_session:
        return env_session, "env:DEVCTL_CALLER_SESSION_ID"
    return "", ""


def _resolve_caller_agent(
    *,
    repo_root: Path,
    caller_role: str,
    packet: Mapping[str, object] | None,
) -> tuple[str, str]:
    for env_name in _CALLER_AGENT_ENV_VARS:
        env_agent = _text(os.environ.get(env_name)).lower()
        if env_agent:
            return env_agent, f"env:{env_name}"
    inferred = _caller_agent_from_review_state(repo_root=repo_root, role=caller_role)
    if inferred:
        return inferred, "review_state:collaboration"
    packet_target = _text(_mapping(packet).get("to_agent")).lower()
    if packet_target and target_actor_has_action_authority(
        actor=packet_target,
        payloads=_review_state_payloads(repo_root),
        granted_capabilities=_granted_capabilities,
    ):
        return packet_target, "review_state:target_actor_authority"
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


def _review_state_payloads(repo_root: Path) -> tuple[Mapping[str, object], ...]:
    return (
        _load_review_state(repo_root),
        *_load_review_state_payloads_from_path_config(repo_root),
    )


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
    payloads = _load_review_state_payloads_from_path_config(repo_root)
    return dict(payloads[0]) if payloads else {}


def _load_review_state_payloads_from_path_config(
    repo_root: Path,
) -> tuple[dict[str, object], ...]:
    config = active_path_config()
    candidates = [
        *(
            repo_root / candidate
            for candidate in config.review_state_candidates
        ),
        repo_root / config.review_status_dir_rel / "review_state.json",
        repo_root / config.review_state_json_rel,
    ]
    payloads: list[dict[str, object]] = []
    for path in candidates:
        try:
            if path.is_file():
                candidate_payload = json.loads(path.read_text(encoding="utf-8"))
            else:
                continue
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(candidate_payload, dict):
            payloads.append(candidate_payload)
    return tuple(payloads)


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


def _typed_packet_attention_block(*, repo_root: Path) -> str:
    """Read typed PacketAttentionState from review_state and decide gating.

    Per rev_pkt_2498 (4): governed mutation must read typed state, not
    env-only. This loads the persisted reviewer_runtime.packet_attention
    projection and enforces:
    - wake_required True → block (new packet unobserved, superseded, pending)
    - pivot_required True (incl. actor_identity_ambiguous) → block
    - stale_reason set → block

    Returns "" when typed state says the caller is current; otherwise returns
    a specific denial reason string. Returns "" (compatibility) when the
    typed state is missing entirely (older projections without the field) so
    that legacy env-var path can still fire below; rev_pkt_2498 expects the
    projection-rebuild path to land before the typed-only enforcement closes.
    """
    review_state = _load_review_state(repo_root)
    reviewer_runtime = _mapping(review_state.get("reviewer_runtime"))
    attention = _mapping(reviewer_runtime.get("packet_attention"))
    if not attention:
        # Typed projection not yet populated; defer to env path.
        return ""
    # Per rev_pkt_2498 (4) refinement: only consume the typed projection when
    # it represents the CURRENT commit caller. If the projection's
    # observation_actor_id does not match the env-declared caller (or env
    # caller is unset), the projection is stale or referencing a different
    # session — defer to env path rather than blocking on stale typed state.
    caller_agent = _text(os.environ.get("DEVCTL_CALLER_AGENT", ""))
    projection_actor = _text(attention.get("observation_actor_id"))
    if not caller_agent:
        return ""
    if not projection_actor or projection_actor != caller_agent:
        # Stale, empty, or cross-session projection (the projection wasn't
        # written with this caller's identity). Defer to env-fallback path
        # rather than blocking on stale typed state.
        return ""
    # Per rev_pkt_2498 (4) refinement: action_request commit is acting ON one
    # specific packet. The gate must NOT block on pivot_required when the
    # only pivot signal is "packet exists in the inbox" — that packet IS the
    # authorization. Block on truly unobserved/superseded/ambiguous-identity
    # signals.
    pivot_reasons = list(attention.get("pivot_reasons") or [])
    blocking_reasons = [
        reason
        for reason in pivot_reasons
        if _text(reason)
        and reason not in {"pending_packets_unconsumed"}
    ]
    if blocking_reasons:
        return f"action_request_packet_attention_pivot_required:{','.join(blocking_reasons)}"
    stale = _text(attention.get("stale_reason"))
    if stale and stale != "wake_required":
        return f"action_request_packet_attention_stale:{stale}"
    return ""
