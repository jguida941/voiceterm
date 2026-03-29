"""Status projection bundle builders for bridge-backed review-channel state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .core import LaneAssignment, project_id_for_repo
from .handoff import extract_bridge_snapshot
from .peer_liveness import OverallLivenessState
from .projection_bundle import (
    ReviewChannelProjectionPaths,
    build_agent_registry_from_lanes,
    write_projection_bundle,
)
from .promotion import derive_promotion_candidate
from .status_projection import ReviewStateContext, build_bridge_review_state
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
    service_identity: dict[str, object]
    attach_auth_policy: dict[str, object]
    warnings: list[str]
    errors: list[str]
    reduced_runtime: dict[str, object] | None = None


def write_status_projection_bundle(
    *,
    context: StatusProjectionContext,
    payload: StatusProjectionPayload,
) -> ReviewChannelProjectionPaths:
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
    agent_registry = _build_status_agent_registry(context=context, timestamp=timestamp)
    return write_projection_bundle(
        output_root=context.output_root,
        review_state=review_state,
        agent_registry=agent_registry,
        action="status",
        trace_events=[],
        full_extras=_status_full_extras(context=context, payload=payload),
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
    return build_bridge_review_state(
        context=ReviewStateContext(
            repo_root=context.repo_root,
            bridge_path=context.bridge_path,
            review_channel_path=context.review_channel_path,
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
        reduced_runtime=payload.reduced_runtime,
    )


def _build_status_agent_registry(
    *,
    context: StatusProjectionContext,
    timestamp: str,
) -> list[dict[str, object]]:
    return build_agent_registry_from_lanes(
        context.lanes,
        timestamp=timestamp,
        provider_state=_status_provider_state(context.bridge_liveness),
    )


def _status_provider_state(
    bridge_liveness: dict[str, object],
) -> dict[str, dict[str, object]]:
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    return {
        "codex": {
            "job_state": overall_state,
            "waiting_on": (
                "peer"
                if overall_state == OverallLivenessState.WAITING_ON_PEER
                else None
            ),
        },
        "claude": {
            "job_state": (
                "assigned"
                if bool(bridge_liveness.get("claude_status_present"))
                and bool(bridge_liveness.get("claude_ack_present"))
                else "waiting"
            ),
        },
    }


def _status_full_extras(
    *,
    context: StatusProjectionContext,
    payload: StatusProjectionPayload,
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
    return extras
