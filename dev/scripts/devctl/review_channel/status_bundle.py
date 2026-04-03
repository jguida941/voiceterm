"""Status projection bundle builders for bridge-backed review-channel state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..common import display_path
from .core import LaneAssignment, project_id_for_repo
from .handoff import extract_bridge_snapshot
from .projection_bundle import (
    ReviewChannelProjectionPaths,
    write_projection_bundle,
)
from .promotion import derive_promotion_candidate
from .status_projection import ReviewStateContext, build_bridge_review_state
from .topology import build_planned_topology
from ..time_utils import utc_timestamp


@dataclass(frozen=True)
class StatusProjectionContext:
    """Static inputs for writing one status projection bundle."""

    repo_root: Path
    bridge_path: Path
    review_channel_path: Path
    output_root: Path
    promotion_plan_path: Path | None
    lanes: list[LaneAssignment]
    bridge_liveness: dict[str, object]
    attention: dict[str, object]
    plan_id: str = ""


@dataclass(frozen=True)
class StatusProjectionPayload:
    """Dynamic status payload projected into operator-facing bundle files."""

    reviewer_worker: dict[str, object] | None
    push_decision: dict[str, object] | None
    service_identity: dict[str, object]
    attach_auth_policy: dict[str, object]
    warnings: list[str]
    errors: list[str]
    reduced_runtime: dict[str, object] | None = None


@dataclass(frozen=True)
class StatusProjectionBundleResult:
    """Written projection paths plus the canonical in-memory ReviewState payload."""

    projection_paths: ReviewChannelProjectionPaths
    review_state: dict[str, object]


def write_status_projection_bundle(
    *,
    context: StatusProjectionContext,
    payload: StatusProjectionPayload,
) -> StatusProjectionBundleResult:
    """Write bridge-backed status projections for operator/read-only consumers."""
    bridge_text = context.bridge_path.read_text(encoding="utf-8")
    snapshot = extract_bridge_snapshot(bridge_text)
    timestamp = utc_timestamp()
    review_state = _build_status_review_state(
        context=context,
        payload=payload,
        bridge_text=bridge_text,
        snapshot=snapshot,
        timestamp=timestamp,
    )
    snapshot_id = str(review_state.get("snapshot_id") or "").strip()
    agent_registry = _status_agent_registry(review_state)
    projection_paths = write_projection_bundle(
        output_root=context.output_root,
        review_state=review_state,
        agent_registry=agent_registry,
        action="status",
        trace_events=[],
        full_extras=_status_full_extras(
            context=context,
            payload=payload,
            snapshot_id=snapshot_id,
        ),
    )
    return StatusProjectionBundleResult(
        projection_paths=projection_paths,
        review_state=review_state,
    )


def _build_status_review_state(
    *,
    context: StatusProjectionContext,
    payload: StatusProjectionPayload,
    bridge_text: str,
    snapshot,
    timestamp: str,
) -> dict[str, object]:
    promotion_candidate = None
    if context.promotion_plan_path is not None:
        promotion_candidate = derive_promotion_candidate(
            repo_root=context.repo_root,
            promotion_plan_path=context.promotion_plan_path,
            require_exists=False,
        )
    review_state = build_bridge_review_state(
        context=ReviewStateContext(
            repo_root=context.repo_root,
            bridge_path=context.bridge_path,
            review_channel_path=context.review_channel_path,
            output_root=context.output_root,
            bridge_text=bridge_text,
            project_id=project_id_for_repo(context.repo_root),
            timestamp=timestamp,
            service_identity=payload.service_identity,
            attach_auth_policy=payload.attach_auth_policy,
            plan_id=context.plan_id,
            warnings=tuple(payload.warnings),
            errors=tuple(payload.errors),
        ),
        snapshot=snapshot,
        bridge_liveness=context.bridge_liveness,
        attention=context.attention,
        promotion_candidate=promotion_candidate,
        push_decision=payload.push_decision,
        reduced_runtime=payload.reduced_runtime,
    )
    snapshot_id = str(review_state.get("snapshot_id") or "").strip()
    compat = review_state.get("_compat")
    if isinstance(compat, dict):
        compat["planned_topology"] = build_planned_topology(
            lanes=context.lanes,
            timestamp=timestamp,
            plan_id=context.plan_id,
            source_path=display_path(
                context.review_channel_path,
                repo_root=context.repo_root,
            ),
        ).to_dict()
        push_enforcement = context.bridge_liveness.get("push_enforcement")
        if isinstance(push_enforcement, dict):
            compat["push_enforcement"] = push_enforcement
        if isinstance(payload.push_decision, dict):
            compat["push_decision"] = _with_snapshot_id(
                payload.push_decision,
                snapshot_id,
            )
    return review_state


def _status_agent_registry(review_state: dict[str, object]) -> dict[str, object]:
    registry = review_state.get("registry")
    if not isinstance(registry, dict):
        return {
            "schema_version": 1,
            "command": "review-channel",
            "timestamp": review_state.get("timestamp"),
            "agents": [],
        }
    return registry


def _status_full_extras(
    *,
    context: StatusProjectionContext,
    payload: StatusProjectionPayload,
    snapshot_id: str,
) -> dict[str, object]:
    push_enforcement = context.bridge_liveness.get("push_enforcement")
    extras = {
        "bridge_liveness": context.bridge_liveness,
        "attention": context.attention,
        "reviewer_worker": payload.reviewer_worker,
        "service_identity": payload.service_identity,
        "attach_auth_policy": payload.attach_auth_policy,
    }
    if isinstance(push_enforcement, dict):
        extras["push_enforcement"] = push_enforcement
    if isinstance(payload.push_decision, dict):
        extras["push_decision"] = _with_snapshot_id(
            payload.push_decision,
            snapshot_id,
        )
    return extras


def _with_snapshot_id(
    payload: dict[str, object],
    snapshot_id: str,
) -> dict[str, object]:
    result = dict(payload)
    if snapshot_id:
        result["snapshot_id"] = snapshot_id
    return result
