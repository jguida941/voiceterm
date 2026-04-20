"""Source and payload helpers for governed session-resume packets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...platform.coordination_snapshot_models import CoordinationSnapshot
from ...runtime.control_plane_read_model import (
    ControlPlaneReadModel,
    build_control_plane_read_model,
)
from ...runtime.control_plane_resolve import (
    load_git_state,
    load_sources,
    read_json_artifact,
)
from ...runtime.finding_backlog import load_finding_backlog
from ...runtime.review_state_models import (
    PacketInboxState,
    ReviewCandidateRecord,
    review_candidate_from_mapping,
)
from .session_resume_authority_payload import (
    SessionResumeAuthorityPayload,
    SessionResumeCurrentSessionPayload,
    SessionResumePacketInboxPayload,
)

if TYPE_CHECKING:
    from ...runtime.project_governance import ProjectGovernance
    from ...runtime.review_state_models import ReviewState


@dataclass(frozen=True, slots=True)
class AuthorityPayloadInputs:
    current_instruction: str
    instruction_revision: str
    ack_state: str
    observed_control_topology: str
    implementation_permission: str
    attention_payload: dict[str, Any]
    recovery_payload: dict[str, Any]
    coordination: CoordinationSnapshot | None
    packet_inbox: PacketInboxState | None
    next_command: str
    push_governance: dict[str, Any]


def resolve_open_findings(
    *,
    repo_root: Path,
    governance: "ProjectGovernance | None",
    fallback: str,
) -> str:
    try:
        backlog = load_finding_backlog(repo_root=repo_root, governance=governance)
    except Exception:  # broad-except: allow reason=best-effort backlog summary must degrade to the packet-derived count on load or parse failure. fallback=return fallback
        return fallback
    if backlog.total_rows <= 0:
        return fallback
    count = len(backlog.open_rows)
    if count:
        return f"{count} open finding(s) (backlog)"
    return "0 open findings (backlog)"


def build_authority_payload(
    *,
    model: ControlPlaneReadModel,
    payload_inputs: AuthorityPayloadInputs,
) -> dict[str, Any]:
    return SessionResumeAuthorityPayload(
        reviewer_mode=model.reviewer_mode,
        reviewer_freshness=model.reviewer_freshness,
        operator_interaction_mode=model.operator_interaction_mode,
        observed_control_topology=payload_inputs.observed_control_topology,
        implementation_permission=payload_inputs.implementation_permission,
        attention=payload_inputs.attention_payload,
        recovery_assessment=payload_inputs.recovery_payload,
        current_session=SessionResumeCurrentSessionPayload(
            current_instruction=payload_inputs.current_instruction,
            current_instruction_revision=payload_inputs.instruction_revision,
            implementer_ack_state=payload_inputs.ack_state,
        ),
        coordination=payload_inputs.coordination,
        packet_inbox=SessionResumePacketInboxPayload.from_state(
            payload_inputs.packet_inbox
        ),
        next_command=payload_inputs.next_command,
        governance=payload_inputs.push_governance,
    ).to_dict()


def extract_current_session(sources: dict[str, Any]) -> dict[str, Any] | None:
    review_state = sources.get("review_state")
    session = _nested_dict(review_state, "current_session")
    if session:
        return session
    return _nested_dict(sources.get("compact_json"), "current_session")


def extract_attention_payload(
    sources: dict[str, Any],
    *,
    default_status: str,
    default_summary: str,
) -> dict[str, Any]:
    for key in ("review_state", "compact_json", "full_json"):
        attention = _nested_dict(sources.get(key), "attention")
        if attention:
            return attention
    payload: dict[str, Any] = {}
    if default_status:
        payload["status"] = default_status
    if default_summary:
        payload["summary"] = default_summary
    return payload


def extract_recovery_assessment_payload(sources: dict[str, Any]) -> dict[str, Any]:
    for key in ("review_state", "full_json", "compact_json"):
        recovery = _nested_dict(sources.get(key), "recovery_assessment")
        if recovery:
            return recovery
    return {}


def extract_head_at_push_time(sources: dict[str, Any]) -> str:
    for key in ("review_state", "compact_json"):
        bridge = _nested_dict(sources.get(key), "bridge")
        sha = _str_field(bridge, "head_at_push_time")
        if sha:
            return sha
    return ""


def extract_review_candidate(
    sources: dict[str, Any],
) -> ReviewCandidateRecord | None:
    """Return the current typed review candidate from governed status sources."""
    for key in ("review_state", "compact_json", "full_json"):
        payload = sources.get(key)
        if not isinstance(payload, dict):
            continue
        candidate = review_candidate_from_mapping(payload.get("review_candidate"))
        if candidate is not None:
            return candidate
        review_state = payload.get("review_state")
        if isinstance(review_state, dict):
            candidate = review_candidate_from_mapping(review_state.get("review_candidate"))
            if candidate is not None:
                return candidate
    return None


def extract_coordination(
    sources: dict[str, Any],
    *,
    repo_root: Path,
    governance: "ProjectGovernance | None",
) -> CoordinationSnapshot | None:
    """Return governed coordination truth via the shared loader."""
    from ...runtime.coordination_loader import load_coordination_snapshot

    fresh = load_coordination_snapshot(
        repo_root=repo_root,
        sources=sources,
        governance=governance,
    )
    if fresh is not None:
        return fresh
    try:
        from ...runtime.startup_context import build_startup_context
    except ImportError:
        return None
    startup_context = build_startup_context(repo_root=repo_root)
    return startup_context.coordination


def _load_governed_sources(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
    review_state: "ReviewState | None" = None,
) -> dict[str, Any]:
    """Load governed sources without reprojecting review state mid-read."""
    from . import session_resume_support as _support

    base = getattr(_support, "load_sources", load_sources)(
        repo_root,
        governance=governance,
        review_state_override=review_state,
    )
    if review_state is not None:
        base["review_state"] = review_state.to_dict()

    gov_paths = getattr(_support, "resolve_source_paths")(repo_root, governance=governance)
    compact_path = repo_root / gov_paths["compact"]
    base["compact_json"] = getattr(
        _support, "read_json_artifact", read_json_artifact
    )(compact_path)
    return base


def _load_session_resume_sources_and_model(
    repo_root: Path,
    *,
    head_sha: str,
    governance: "ProjectGovernance | None",
    review_state: "ReviewState | None",
    read_model_override: "ControlPlaneReadModel | None",
    sources_override: dict[str, Any] | None,
) -> tuple[dict[str, Any], ControlPlaneReadModel]:
    sources = sources_override if sources_override is not None else _load_governed_sources(
        repo_root,
        governance=governance,
        review_state=review_state,
    )
    from . import session_resume_support as _support

    git = (
        getattr(_support, "load_git_state", load_git_state)(repo_root)
        if sources_override is None
        else {
            "branch": "unknown",
            "head": head_sha,
            "clean": True,
            "ahead": 0,
        }
    )
    model_builder = getattr(
        _support,
        "build_control_plane_read_model",
        build_control_plane_read_model,
    )
    model = read_model_override or model_builder(
        repo_root,
        sources_override=sources,
        git_override=git,
        governance=governance,
        review_state=review_state,
    )
    return sources, model


def _nested_dict(data: object, key: str) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    value = data.get(key)
    return value if isinstance(value, dict) else None


def _str_field(data: dict[str, Any] | None, key: str) -> str:
    if not data:
        return ""
    return str(data.get(key) or "").strip()
