"""Support helpers for event-backed review-state projection composition."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from ..runtime.coordination_loader import load_coordination_snapshot
from ..runtime.review_state_parser import review_state_from_payload
from .attach_auth_projection import (
    build_attach_auth_policy_state,
    build_service_identity_state,
)
from .reviewer_runtime_contract import build_reviewer_doctor_surface


@dataclass(frozen=True, slots=True)
class CompatProjectionInputs:
    raw_service_identity: object
    raw_attach_auth_policy: object
    bridge_liveness: dict[str, object]
    reviewer_runtime: object
    collaboration: object
    recovery_assessment: object
    attention: object
    commit_pipeline: object
    push_decision: object
    snapshot_id: object


def review_identifiers(review_state: Mapping[str, object]) -> tuple[str, str]:
    review_payload = _mapping(review_state.get("review"))
    return (
        str(review_payload.get("plan_id") or ""),
        str(review_payload.get("session_id") or ""),
    )


def operator_interaction_mode(governance: object) -> str:
    if governance is None:
        return ""
    return str(governance.bridge_config.operator_interaction_mode or "").strip()


def push_authorization_payload(commit_pipeline: object) -> dict[str, object] | None:
    push_authorization = commit_pipeline.push_authorization
    return None if push_authorization is None else asdict(push_authorization)


def load_coordination_payload(
    *,
    repo_root: Path,
    review_state: dict[str, object],
    governance: object,
) -> dict[str, object] | None:
    typed_review_state = review_state_from_payload(review_state)
    coordination = load_coordination_snapshot(
        repo_root=repo_root,
        sources={"review_state": review_state},
        governance=governance,
        review_state=typed_review_state,
    )
    return None if coordination is None else coordination.to_dict()


def enrichment_extras(
    *,
    bridge_liveness: dict[str, object],
    attention: dict[str, object],
    raw_service_identity: object,
    raw_attach_auth_policy: object,
) -> dict[str, object]:
    return {
        "bridge_liveness": bridge_liveness,
        "attention": attention,
        "service_identity": raw_service_identity,
        "attach_auth_policy": raw_attach_auth_policy,
    }


def session_output_root(projections_root: Path) -> Path:
    if (
        projections_root.name == "latest"
        and projections_root.parent.name == "projections"
    ):
        return projections_root.parent.parent / projections_root.name
    return projections_root


def apply_compat_projections(
    *,
    merged_compat: dict[str, object],
    inputs: CompatProjectionInputs,
) -> dict[str, object]:
    """Populate the compat mapping with typed doctor / push / bridge fields."""
    runtime_daemons = _mapping(_mapping(merged_compat.get("runtime")).get("daemons"))

    merged_compat["service_identity"] = build_service_identity_state(
        inputs.raw_service_identity
    )
    merged_compat["attach_auth_policy"] = build_attach_auth_policy_state(
        inputs.raw_attach_auth_policy
    )

    push_enforcement = _mapping(inputs.bridge_liveness.get("push_enforcement"))
    if push_enforcement:
        merged_compat["push_enforcement"] = push_enforcement

    merged_compat["doctor"] = build_reviewer_doctor_surface(
        contract=inputs.reviewer_runtime,
        collaboration=asdict(inputs.collaboration),
        recovery_assessment=inputs.recovery_assessment,
        attention=inputs.attention,
        commit_pipeline=inputs.commit_pipeline,
        push_authorization=inputs.commit_pipeline.push_authorization,
        push_enforcement=push_enforcement,
        runtime_state=runtime_daemons,
        snapshot_id=inputs.snapshot_id,
    )

    if inputs.push_decision:
        merged_compat["push_decision"] = inputs.push_decision

    if inputs.snapshot_id:
        _propagate_snapshot_id(
            merged_compat=merged_compat,
            snapshot_id=inputs.snapshot_id,
        )

    return merged_compat


def _propagate_snapshot_id(
    *,
    merged_compat: dict[str, object],
    snapshot_id: object,
) -> None:
    merged_compat["snapshot_id"] = snapshot_id

    compat_push_decision = _mapping(merged_compat.get("push_decision"))
    if compat_push_decision:
        updated_push_decision = dict(compat_push_decision)
        updated_push_decision["snapshot_id"] = snapshot_id
        merged_compat["push_decision"] = updated_push_decision

    bridge_projection = _mapping(merged_compat.get("bridge_projection"))
    metadata = _mapping(bridge_projection.get("metadata"))
    if not metadata:
        return

    updated_bridge_projection = dict(bridge_projection)
    updated_metadata = dict(metadata)
    updated_metadata["snapshot_id"] = snapshot_id
    updated_bridge_projection["metadata"] = updated_metadata
    merged_compat["bridge_projection"] = updated_bridge_projection


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
