"""Compact projection helpers for review-channel bundles."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from ..runtime.authority_snapshot import (
    summary_blockers,
    summary_next_command,
)
from ..runtime.surface_provenance import (
    attach_surface_provenance,
    surface_provenance_from_mapping,
)
from ..runtime.value_coercion import coerce_mapping as _mapping
from .current_session_projection import current_focus_line
from .projection_observation import build_observation_projection


@dataclass(frozen=True)
class CompactProjectionPayload:
    """Typed shape for the compact review-state projection."""

    schema_version: int
    command: str
    timestamp: object
    snapshot_id: str
    zref: str
    ok: object
    review: object
    authority_snapshot: object
    current_session: object
    review_candidate: object
    recovery_assessment: object
    service_identity: object
    attach_auth_policy: object
    push_decision: object
    doctor: object
    commit_pipeline: object
    bridge: object
    queue: object
    reviewer_observation: object
    warnings: object
    errors: object

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_compact_projection(review_state: dict[str, object]) -> dict[str, object]:
    """Build the compact review-state projection payload."""
    queue = _mapping(review_state.get("queue"))
    bridge = _mapping(review_state.get("bridge"))
    current_session = _mapping(review_state.get("current_session"))
    review_candidate = review_state.get("review_candidate")
    compat = _mapping(review_state.get("_compat"))
    service_identity = compat.get("service_identity")
    attach_auth_policy = compat.get("attach_auth_policy")
    push_decision = compat.get("push_decision")
    doctor = compat.get("doctor")
    commit_pipeline = review_state.get("commit_pipeline")
    snapshot_id = str(review_state.get("snapshot_id") or "").strip()
    zref = str(review_state.get("zref") or "").strip()
    current_focus = current_focus_line(review_state)
    payload = CompactProjectionPayload(
        schema_version=1,
        command="review-channel",
        timestamp=review_state.get("timestamp"),
        snapshot_id=snapshot_id,
        zref=zref,
        ok=review_state.get("ok"),
        review=review_state.get("review"),
        authority_snapshot=review_state.get("authority_snapshot"),
        current_session=current_session,
        review_candidate=review_candidate,
        recovery_assessment=review_state.get("recovery_assessment"),
        service_identity=service_identity,
        attach_auth_policy=attach_auth_policy,
        push_decision=_with_surface_identity(push_decision, snapshot_id, zref),
        doctor=_with_surface_identity(doctor, snapshot_id, zref),
        commit_pipeline=commit_pipeline,
        bridge=_compact_bridge(bridge, current_focus=current_focus),
        queue=_compact_queue(queue, current_focus=current_focus),
        reviewer_observation=build_observation_projection(review_state),
        warnings=review_state.get("warnings", []),
        errors=review_state.get("errors", []),
    ).to_dict()
    return attach_surface_provenance(
        payload,
        provenance=surface_provenance_from_mapping(review_state),
    )


def projection_next_command(review_state: Mapping[str, object]) -> str:
    """Return the projected next command for compact authority summaries."""
    recovery = _mapping(review_state.get("recovery_assessment"))
    decision = _mapping(recovery.get("decision"))
    if str(decision.get("action_id") or "").strip() == "cut_checkpoint":
        command = str(decision.get("command") or "").strip()
        if command:
            return command

    if summary_blockers(review_state):
        command = summary_next_command(review_state)
        if command:
            return command

    compat = _mapping(review_state.get("_compat"))
    doctor = _mapping(compat.get("doctor"))
    attention = _mapping(review_state.get("attention"))
    recovery = _mapping(review_state.get("recovery_assessment"))
    decision = _mapping(recovery.get("decision"))
    push_decision = _mapping(compat.get("push_decision"))
    for candidate in (
        doctor.get("recommended_command"),
        decision.get("command"),
        attention.get("recommended_command"),
        push_decision.get("next_step_command"),
    ):
        command = str(candidate or "").strip()
        if command:
            return command
    return ""


def _with_surface_identity(payload: object, snapshot_id: str, zref: str) -> object:
    if not isinstance(payload, dict):
        return payload
    result = dict(payload)
    if snapshot_id and not result.get("snapshot_id"):
        result["snapshot_id"] = snapshot_id
    if zref and not result.get("zref"):
        result["zref"] = zref
    return result


def _compact_bridge(
    bridge: Mapping[str, object],
    *,
    current_focus: str,
) -> dict[str, object]:
    return {
        "last_codex_poll_utc": bridge.get("last_codex_poll_utc"),
        "last_worktree_hash": bridge.get("last_worktree_hash"),
        "head_at_push_time": bridge.get("head_at_push_time", ""),
        "current_instruction": current_focus,
    }


def _compact_queue(
    queue: Mapping[str, object],
    *,
    current_focus: str,
) -> dict[str, object]:
    return {
        **queue,
        "current_focus": current_focus,
    }


__all__ = [
    "build_compact_projection",
    "projection_next_command",
]
