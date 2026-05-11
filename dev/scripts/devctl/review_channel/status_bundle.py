"""Status projection bundle builders for bridge-backed review-channel state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..common import display_path
from ..runtime.review_state_models import (
    RecoveryAssessmentState,
    ReviewCurrentSessionState,
)
from .core import LaneAssignment, project_id_for_repo
from .handoff import extract_bridge_snapshot
from .agent_loop_decision_projection import (
    attach_agent_loop_decision_projections,
)
from .agent_work_board_posture import apply_work_board_session_posture
from .projection_bundle import (
    ReviewChannelProjectionPaths,
    artifact_writes_suppressed,
    canonical_projection_root_for_status_root,
    canonicalize_projection_review_state,
    projection_paths_for_root,
    write_projection_bundle,
)
from .pending_packets import load_pending_packet_queue
from .promotion import derive_promotion_candidate
from .status_projection import build_bridge_review_state
from .status_projection_support import ReviewStateContext
from .status_work_board_identity import refresh_preserved_work_board_runtime_identity
from .event_projection_current_session_preserve import (
    preserve_current_session_context_from_prior,
)
from .status_bundle_current_session_sync import sync_current_session_runtime_context
from .topology import build_planned_topology
from ..time_utils import utc_timestamp

_refresh_preserved_work_board_runtime_identity = (
    refresh_preserved_work_board_runtime_identity
)


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
    current_session: ReviewCurrentSessionState | None = None
    recovery_assessment: RecoveryAssessmentState | None = None
    plan_id: str = ""
    prior_review_state: Mapping[str, object] | None = None
    reviewer_accepted_implementer_state_hash_override: str | None = None


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
    review_state = canonicalize_projection_review_state(review_state)
    refreshed_work_board = refresh_preserved_work_board_runtime_identity(
        review_state.get("agent_work_board"),
        collaboration=review_state.get("collaboration"),
    )
    if refreshed_work_board is not review_state.get("agent_work_board"):
        review_state = dict(review_state)
        review_state["agent_work_board"] = refreshed_work_board
        review_state = _attach_agent_loop_decisions(review_state)
    review_state = apply_work_board_session_posture(review_state)
    review_state = _attach_agent_loop_decisions(review_state)
    snapshot_id = str(review_state.get("snapshot_id") or "").strip()
    zref = str(review_state.get("zref") or "").strip()
    agent_registry = _status_agent_registry(review_state)
    projection_root = canonical_projection_root_for_status_root(context.output_root)
    if artifact_writes_suppressed():
        projection_paths = projection_paths_for_root(projection_root)
    else:
        projection_paths = write_projection_bundle(
            output_root=projection_root,
            review_state=review_state,
            agent_registry=agent_registry,
            action="status",
            trace_events=[],
            full_extras=_status_full_extras(
                context=context,
                payload=payload,
                snapshot_id=snapshot_id,
                zref=zref,
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
    pending_queue = load_pending_packet_queue(context.repo_root)
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
            prior_review_state=context.prior_review_state,
            current_session=context.current_session,
            reviewer_accepted_implementer_state_hash_override=(
                context.reviewer_accepted_implementer_state_hash_override
            ),
            pending_packets=pending_queue.control_packets,
            stale_packet_count=pending_queue.stale_packet_count,
        ),
        snapshot=snapshot,
        bridge_liveness=context.bridge_liveness,
        attention=context.attention,
        recovery_assessment=context.recovery_assessment,
        promotion_candidate=promotion_candidate,
        push_decision=payload.push_decision,
        reduced_runtime=payload.reduced_runtime,
    )
    review_state = _preserve_typed_runtime_addenda(
        review_state,
        prior_review_state=context.prior_review_state,
    )
    review_state = apply_work_board_session_posture(review_state)
    review_state = _attach_agent_loop_decisions(review_state)
    snapshot_id = str(review_state.get("snapshot_id") or "").strip()
    zref = str(review_state.get("zref") or "").strip()
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
            compat["push_decision"] = _with_surface_identity(
                payload.push_decision,
                snapshot_id,
                zref,
            )
    return review_state


def _attach_agent_loop_decisions(
    review_state: dict[str, object],
) -> dict[str, object]:
    return attach_agent_loop_decision_projections(review_state)


def _preserve_typed_runtime_addenda(
    review_state: dict[str, object],
    *,
    prior_review_state: Mapping[str, object] | None,
) -> dict[str, object]:
    """Keep event-backed runtime addenda when bridge status refreshes.

    Bridge-backed status owns bridge/session/checkpoint projection fields. It
    does not own agent_sync, work-board, coordination-state, or round-proof
    reducers. Dropping those fields during a read-only status refresh makes
    status/doctor disagree with sync-status and erases the shared agent loop
    cursor. Preserve the previous event-backed addenda until that reducer
    publishes a newer snapshot.
    """
    prior = _prior_review_state_payload(prior_review_state)
    if not prior:
        return review_state
    merged = dict(review_state)
    merged, current_session_preserved = preserve_current_session_context_from_prior(
        merged,
        prior,
    )
    if current_session_preserved:
        sync_current_session_runtime_context(merged)
    prior_packets = prior.get("packets")
    if prior_packets and not merged.get("packets"):
        merged["packets"] = prior_packets
    for key in (
        "round_proofs",
        "agent_sync",
        "agent_work_board",
        "coordination_state",
        "agent_loop_decisions",
        "attention_windows",
    ):
        value = prior.get(key)
        if value:
            if key == "agent_work_board":
                value = refresh_preserved_work_board_runtime_identity(
                    value,
                    collaboration=merged.get("collaboration"),
                )
            merged[key] = value
    prior_runtime = prior.get("reviewer_runtime")
    if isinstance(prior_runtime, Mapping):
        runtime = dict(merged.get("reviewer_runtime") or {})
        for key in ("agent_runtime_clock", "packet_attention", "inbox_observation"):
            prior_value = prior_runtime.get(key)
            if prior_value and _runtime_field_missing(runtime.get(key), key):
                runtime[key] = prior_value
        merged["reviewer_runtime"] = runtime
    return merged


def _prior_review_state_payload(
    prior_review_state: Mapping[str, object] | None,
) -> Mapping[str, object]:
    if not isinstance(prior_review_state, Mapping):
        return {}
    nested = prior_review_state.get("review_state")
    if isinstance(nested, Mapping):
        return nested
    return prior_review_state


def _runtime_field_missing(value: object, key: str) -> bool:
    if not isinstance(value, Mapping):
        return True
    if key == "agent_runtime_clock":
        return not str(value.get("source_latest_event_id") or "").strip()
    if key == "packet_attention":
        return not str(value.get("latest_inbox_event_id") or "").strip()
    if key == "inbox_observation":
        return not str(value.get("last_inbox_event_id") or "").strip()
    return False


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
    zref: str,
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
        extras["push_decision"] = _with_surface_identity(
            payload.push_decision,
            snapshot_id,
            zref,
        )
    return extras
def _with_surface_identity(
    payload: dict[str, object],
    snapshot_id: str,
    zref: str,
) -> dict[str, object]:
    result = dict(payload)
    if snapshot_id:
        result["snapshot_id"] = snapshot_id
    if zref:
        result["zref"] = zref
    return result
