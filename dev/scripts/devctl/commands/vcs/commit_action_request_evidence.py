"""Typed evidence derivation for packet-scoped governed commit authority."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from pathlib import Path

from .commit_action_request_pipeline import (
    pipeline_binding_required,
    pipeline_generation as _pipeline_generation,
    pipeline_hash as _pipeline_hash,
)
from .governed_executor_git import head_commit

SUPPORTED_REQUEST_ACTION = "stage_commit_pipeline"
SAFE_POLICY_HINT = "safe_auto_apply"
OPERATOR_APPROVAL_POLICY_HINT = "operator_approval_required"
REQUIRED_ACTION_CAPABILITY_ANY = frozenset({"repo.stage_handoff"})
REQUIRED_ACTION_CAPABILITY_ALL = frozenset({"repo.stage", "repo.commit"})


def derive_pipeline_evidence(
    *,
    repo_root: Path,
    packet: Mapping[str, object],
    grant: object,
    pipeline: object | None,
) -> object:
    """Fill missing packet pipeline fields only when typed pipeline facts agree."""
    if not pipeline_binding_required(repo_root=repo_root, pipeline=pipeline):
        if _pipeline_generation(pipeline) or _pipeline_hash(pipeline):
            return append_warning(grant, "stale_pipeline_binding_ignored")
        return grant

    pipeline_generation = _pipeline_generation(pipeline)
    pipeline_hash = _pipeline_hash(pipeline)
    derived_fields = list(getattr(grant, "derived_fields", ()) or ())
    derivation_sources = list(getattr(grant, "derivation_sources", ()) or ())
    updates: dict[str, object] = {}
    if pipeline_generation and not _field(grant, "pipeline_generation"):
        source_generation = _text(
            _mapping(packet.get("source_identity")).get("generation_id")
        )
        if source_generation and source_generation != pipeline_generation:
            # pipeline_binding_required above already verified freshness via
            # pipeline_is_stale_for_current_repo (branch + commit_sha). When that
            # passes but generation_id drifts, the work hasn't moved — only
            # metadata advanced (typically because a prior commit attempt or
            # publisher refresh advanced the typed pipeline). Bail only when the
            # packet's HEAD pin no longer matches current HEAD; that is the real
            # "packet composed against a different state" signal. Otherwise
            # surface the drift via a warning and proceed with derivation so
            # legitimate operator-confirmed packets are not blocked by metadata
            # churn between compose and validate.
            if not _packet_head_pin_matches(packet=packet, repo_root=repo_root):
                return grant
            grant = append_warning(grant, "stale_source_generation_metadata_drift")
        updates["pipeline_generation"] = pipeline_generation
        derived_fields.append("pipeline_generation")
        derivation_sources.append("RemoteCommitPipelineContract.generation_id")
    if pipeline_hash and not _field(grant, "staged_snapshot_hash"):
        updates["staged_snapshot_hash"] = pipeline_hash
        derived_fields.append("staged_snapshot_hash")
        derivation_sources.append("RemoteCommitPipelineContract.intent.staged_tree_hash")
    if not updates:
        return grant
    return replace(
        grant,
        **updates,
        derived_fields=unique(derived_fields),
        derivation_sources=unique(derivation_sources),
    )


def policy_denial(*, packet: Mapping[str, object], grant: object) -> str:
    """Return a policy/evidence denial for one stage-commit action request."""
    policy = _text(packet.get("policy_hint"))
    if policy == SAFE_POLICY_HINT:
        return ""
    if (
        policy == OPERATOR_APPROVAL_POLICY_HINT
        and _field(grant, "requested_action") == SUPPORTED_REQUEST_ACTION
    ):
        if not bool(packet.get("approval_required")):
            return "action_request_approval_required_missing"
        if _text(packet.get("status")) != "acked" and not _text(
            packet.get("acked_at_utc")
        ):
            return "action_request_operator_approval_not_acknowledged"
        capabilities = set(getattr(grant, "identity_authority_capabilities", ()) or ())
        if "approval.commit" not in capabilities:
            return "action_request_approval_capability_missing"
        return ""
    return "action_request_policy_not_safe"


def derive_caller_role(
    *,
    caller_agent: str,
    payloads: Sequence[Mapping[str, object]],
) -> tuple[str, str]:
    """Derive caller role from typed posture for the matched actor only."""
    actor = _text(caller_agent).lower()
    if not actor:
        return "", ""
    for payload in payloads:
        lane = _normalize_role(_mapping(payload.get("agent_lane")).get("lane"))
        if lane:
            return lane, "review_state:agent_lane"
        posture = _mapping(_mapping(payload.get("collaboration")).get("session_posture"))
        for row in _rows(posture.get("actors")):
            actor_id = _text(row.get("actor_id") or row.get("provider")).lower()
            provider = _text(row.get("provider") or row.get("actor_id")).lower()
            if actor not in {actor_id, provider} or not _is_live(row):
                continue
            occupied_lane = _normalize_role(row.get("occupied_lane"))
            if occupied_lane:
                return occupied_lane, "review_state:session_posture"
            role = _normalize_actor_role(row.get("role"))
            if role:
                return role, "review_state:session_posture"
        for row in _rows(_mapping(payload.get("collaboration")).get("actor_authorities")):
            actor_id = _text(row.get("actor_id") or row.get("provider")).lower()
            provider = _text(row.get("provider") or row.get("actor_id")).lower()
            if actor in {actor_id, provider} and _is_live(row):
                role = _normalize_actor_role(row.get("role"))
                if role:
                    return role, "review_state:actor_authorities"
    return "", ""


def target_actor_has_action_authority(
    *,
    actor: str,
    payloads: Sequence[Mapping[str, object]],
    granted_capabilities: Callable[[Mapping[str, object]], tuple[str, ...]],
) -> bool:
    """Return True when the packet target is a live, grantable actor."""
    target = _text(actor).lower()
    if not target:
        return False
    for payload in payloads:
        for row in _rows(_mapping(payload.get("collaboration")).get("actor_authorities")):
            actor_id = _text(row.get("actor_id") or row.get("provider")).lower()
            provider = _text(row.get("provider") or row.get("actor_id")).lower()
            if target not in {actor_id, provider} or not _is_live(row):
                continue
            if capabilities_grant_action(granted_capabilities(row)):
                return True
    return False


def missing_evidence_fields(
    *,
    repo_root: Path,
    packet: Mapping[str, object],
    grant: object,
    pipeline: object | None,
) -> tuple[str, ...]:
    """Return exact missing typed evidence names for an invalid grant."""
    fields: list[str] = []
    if not _field(grant, "caller_agent"):
        fields.append("caller_agent")
    if not _field(grant, "caller_role"):
        fields.append("caller_role")
    if not _field(grant, "identity_authority_source"):
        fields.append("CollaborationSession.actor_authorities")
    elif not capabilities_grant_action(
        tuple(getattr(grant, "identity_authority_capabilities", ()) or ())
    ):
        fields.append("identity_authority_capabilities")
    policy = _text(packet.get("policy_hint"))
    capabilities = set(getattr(grant, "identity_authority_capabilities", ()) or ())
    if policy == OPERATOR_APPROVAL_POLICY_HINT:
        if not bool(packet.get("approval_required")):
            fields.append("approval_required")
        if "approval.commit" not in capabilities:
            fields.append("identity_authority_capabilities.approval.commit")
    elif policy != SAFE_POLICY_HINT:
        fields.append("policy_hint")
    if not _field(grant, "full_guard_bundle_evidence"):
        fields.append("full_guard_bundle_evidence")
    if pipeline_binding_required(repo_root=repo_root, pipeline=pipeline):
        if not _field(grant, "pipeline_generation"):
            fields.append("pipeline_generation")
        if not _field(grant, "staged_snapshot_hash"):
            fields.append("staged_snapshot_hash")
    return unique(fields)


def invalid_evidence_fields(
    *,
    repo_root: Path,
    packet: Mapping[str, object],
    grant: object,
    pipeline: object | None,
    denial: str,
) -> tuple[str, ...]:
    """Return exact invalid typed evidence names for an invalid grant."""
    fields: list[str] = []
    if denial == "action_request_policy_not_safe":
        fields.append("policy_hint")
    if denial == "action_request_operator_approval_not_acknowledged":
        fields.append("acked_at_utc")
    if denial == "action_request_pipeline_generation_mismatch":
        fields.append("pipeline_generation")
    if denial == "action_request_staged_snapshot_mismatch":
        fields.append("staged_snapshot_hash")
    if pipeline_binding_required(repo_root=repo_root, pipeline=pipeline):
        source_generation = _text(
            _mapping(packet.get("source_identity")).get("generation_id")
        )
        pipeline_generation = _pipeline_generation(pipeline)
        if (
            source_generation
            and pipeline_generation
            and source_generation != pipeline_generation
        ):
            fields.append("source_identity.generation_id")
    return unique(fields)


def capabilities_grant_action(capabilities: tuple[str, ...]) -> bool:
    """Return True when a grant can execute a stage handoff or full commit."""
    granted = set(capabilities)
    return bool(
        REQUIRED_ACTION_CAPABILITY_ANY & granted
        or REQUIRED_ACTION_CAPABILITY_ALL.issubset(granted)
    )


def append_warning(grant: object, warning: str) -> object:
    """Return grant with one deduplicated warning."""
    return replace(grant, warnings=unique((*getattr(grant, "warnings", ()), warning)))


def unique(values: object) -> tuple[str, ...]:
    rows: list[str] = []
    if not isinstance(values, list | tuple):
        return ()
    for value in values:
        text = _text(value)
        if text and text not in rows:
            rows.append(text)
    return tuple(rows)


def _packet_head_pin_matches(*, packet: Mapping[str, object], repo_root: Path) -> bool:
    """Return True when packet's target_revision and source HEAD both match current HEAD.

    This is the real "packet still authorizes this state" check that lets
    derive_pipeline_evidence proceed past metadata-only generation drift while
    still bailing on packets composed against a different repo HEAD.
    """
    current_head = head_commit(repo_root)
    if not current_head:
        return False
    target_revision = _text(packet.get("target_revision"))
    source_head_sha = _text(_mapping(packet.get("source_identity")).get("head_sha"))
    if target_revision and target_revision != current_head:
        return False
    if source_head_sha and source_head_sha != current_head:
        return False
    return bool(target_revision or source_head_sha)


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


def _normalize_actor_role(value: object) -> str:
    role = _text(value).lower()
    if role == "operator":
        return "dashboard"
    return _normalize_role(role)


def _field(obj: object, name: str) -> str:
    return _text(getattr(obj, name, ""))


def _text(value: object) -> str:
    return str(value or "").strip()
