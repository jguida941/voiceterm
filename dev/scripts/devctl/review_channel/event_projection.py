"""Projection helpers shared by event-backed review-channel outputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, replace
from pathlib import Path

from ..runtime.governance_scan import scan_repo_governance_safely
from ..runtime.coordination_loader import load_coordination_snapshot
from ..runtime.review_state_parser import review_state_from_payload
from ..runtime.review_state_models import ReviewQueueState
from ..runtime.review_packet_inbox import build_packet_inbox_payload
from ..runtime.surface_snapshot import build_surface_snapshot_id
from .attach_auth_policy import build_attach_auth_policy
from .attach_auth_projection import (
    build_attach_auth_policy_state,
    build_service_identity_state,
)
from .core import DEFAULT_BRIDGE_REL
from .current_session_projection import current_session_payload
from .current_session_projection import (
    build_bridge_current_session,
    build_event_current_session,
)
from .event_projection_context import (
    append_event_instruction_context,
    build_event_context_packet,
    build_instruction_source,
)
from .event_projection_enrichment import (
    EventProjectionContext,
)
from .collaboration_session import build_collaboration_session
from .event_projection_bridge import (
    build_event_bridge_liveness_projection,
    build_event_bridge_state_projection,
    detect_event_implementer_stall,
)
from .remote_commit_pipeline_artifact import load_remote_commit_pipeline_contract
from .reviewer_runtime_contract import (
    ReviewerRuntimeInputs,
    build_reviewer_doctor_surface,
    build_reviewer_runtime_contract,
)
from .recovery_assessment import (
    build_recovery_assessment,
    recovery_assessment_to_attention_payload,
)
from .status_projection_helpers import build_bridge_push_enforcement_state
from .status_push_decision import build_status_push_decision
from .action_request_delivery import attach_action_request_delivery_receipts
from .event_projection_current_session import resolve_current_session
from .event_projection_queue import derive_event_next_instruction_bundle
from .service_identity import build_service_identity


def _operator_interaction_mode(repo_root: Path) -> str:
    governance = scan_repo_governance_safely(repo_root)
    if governance is None:
        return ""
    return str(governance.bridge_config.operator_interaction_mode or "").strip()


def build_event_queue_summary(
    pending_counts: dict[str, int],
    stale_packet_count: int,
    *,
    packets: list[dict[str, object]],
) -> dict[str, object]:
    """Build the event-backed queue summary plus derived next-step hint."""
    derived_instruction, derived_source = derive_event_next_instruction_bundle(
        packets,
        build_event_context_packet_fn=build_event_context_packet,
        append_event_instruction_context_fn=append_event_instruction_context,
        build_instruction_source_fn=build_instruction_source,
    )
    summary: dict[str, object] = {
        "pending_total": sum(pending_counts.values()),
        "derived_next_instruction": derived_instruction,
        "derived_next_instruction_source": derived_source,
    }
    for provider, count in pending_counts.items():
        summary[f"pending_{provider}"] = count
    summary["stale_packet_count"] = stale_packet_count
    return summary


def build_event_queue_state(
    pending_counts: dict[str, int],
    stale_packet_count: int,
    packet_rows: list[dict[str, object]],
) -> ReviewQueueState:
    """Build a typed ReviewQueueState from event reduction outputs."""
    derived_instruction, derived_source = derive_event_next_instruction_bundle(
        packet_rows,
        build_event_context_packet_fn=build_event_context_packet,
        append_event_instruction_context_fn=append_event_instruction_context,
        build_instruction_source_fn=build_instruction_source,
    )
    return ReviewQueueState(
        pending_total=sum(pending_counts.values()),
        pending_codex=pending_counts.get("codex", 0),
        pending_claude=pending_counts.get("claude", 0),
        pending_cursor=pending_counts.get("cursor", 0),
        pending_operator=pending_counts.get("operator", 0),
        stale_packet_count=stale_packet_count,
        derived_next_instruction=derived_instruction,
        derived_next_instruction_source=derived_source,
    )


def _attach_event_queue_state(
    review_state: dict[str, object],
    *,
    artifact_root: Path | None,
) -> None:
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return
    review_state["packets"] = attach_action_request_delivery_receipts(
        packets=packets,
        artifact_root=artifact_root,
    )
    queue = _mapping(review_state.get("queue"))
    pending_counts = {
        "codex": int(queue.get("pending_codex") or 0),
        "claude": int(queue.get("pending_claude") or 0),
        "cursor": int(queue.get("pending_cursor") or 0),
        "operator": int(queue.get("pending_operator") or 0),
    }
    review_state["queue"] = asdict(
        build_event_queue_state(
            pending_counts,
            int(queue.get("stale_packet_count") or 0),
            review_state["packets"],
        )
    )


def _resolve_current_session(
    review_state: dict[str, object],
    *,
    context: EventProjectionContext,
    bridge_liveness: dict[str, object],
):
    """Keep compatibility patches against this module's helper names alive."""
    return resolve_current_session(
        review_state=review_state,
        repo_root=context.repo_root,
        prior_review_state=context.prior_review_state,
        bridge_liveness=bridge_liveness,
        build_event_current_session_fn=build_event_current_session,
        build_bridge_current_session_fn=build_bridge_current_session,
    )

def enrich_event_review_state(
    *,
    review_state: dict[str, object],
    context: EventProjectionContext,
) -> tuple[dict[str, object], dict[str, object]]:
    """Attach parity fields needed by event-backed review-state projections."""
    review_state = dict(review_state)
    _attach_event_queue_state(review_state, artifact_root=context.artifact_root)
    repo_root = context.repo_root
    projections_root = context.projections_root
    review_channel_path = context.review_channel_path
    prior_review_state = context.prior_review_state
    raw_service_identity = build_service_identity(
        repo_root=repo_root,
        bridge_path=repo_root / DEFAULT_BRIDGE_REL,
        review_channel_path=review_channel_path,
        output_root=projections_root,
    )
    raw_attach_auth_policy = build_attach_auth_policy(
        service_identity=raw_service_identity
    )
    bridge_liveness = build_event_bridge_liveness_projection(review_state)
    bridge_liveness["push_enforcement"] = (
        context.push_enforcement
        if context.push_enforcement is not None
        else build_bridge_push_enforcement_state(repo_root)
    )
    current_session = _resolve_current_session(
        review_state,
        context=context,
        bridge_liveness=bridge_liveness,
    )
    governance = scan_repo_governance_safely(repo_root)
    recovery_assessment = build_recovery_assessment(
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        operator_interaction_mode=(
            str(governance.bridge_config.operator_interaction_mode or "").strip()
            if governance is not None
            else ""
        ),
    )
    attention = recovery_assessment_to_attention_payload(recovery_assessment)
    collaboration = build_collaboration_session(
        timestamp=str(review_state.get("timestamp") or ""),
        plan_id=str(_mapping(review_state.get("review")).get("plan_id") or ""),
        session_id=str(_mapping(review_state.get("review")).get("session_id") or ""),
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        attention=attention,
        repo_root=repo_root,
        session_output_root=projections_root,
    )
    reviewer_runtime = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness=bridge_liveness,
            current_session=current_session,
            recovery_assessment=recovery_assessment,
            attention=attention,
            collaboration=collaboration,
            session_output_root=projections_root,
            rollover_dir=projections_root.parent / "rollovers",
        )
    )
    push_decision = build_status_push_decision(
        bridge_liveness=bridge_liveness,
        reviewer_runtime=reviewer_runtime,
    )
    commit_pipeline = load_remote_commit_pipeline_contract(output_root=projections_root)
    existing_compat = review_state.get("_compat")
    merged_compat = dict(existing_compat) if isinstance(existing_compat, dict) else {}
    snapshot_id = build_surface_snapshot_id(
        reviewer_runtime=reviewer_runtime,
        commit_pipeline=commit_pipeline,
        push_decision=push_decision,
    )
    commit_pipeline = replace(commit_pipeline, snapshot_id=snapshot_id)
    bridge_liveness["review_accepted"] = (
        reviewer_runtime.review_acceptance.review_accepted
    )
    bridge_liveness["publish_clear"] = reviewer_runtime.publish_clear
    review_state["snapshot_id"] = snapshot_id
    review_state["current_session"] = current_session_payload(current_session)
    review_state["collaboration"] = asdict(collaboration)
    review_state["reviewer_runtime"] = asdict(reviewer_runtime)
    review_state["commit_pipeline"] = commit_pipeline.to_dict()
    review_state["push_authorization"] = (
        None
        if commit_pipeline.push_authorization is None
        else asdict(commit_pipeline.push_authorization)
    )
    review_state["recovery_assessment"] = asdict(recovery_assessment)
    review_state["bridge"] = build_event_bridge_state_projection(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
        reviewer_runtime=reviewer_runtime,
    )
    review_state["attention"] = attention
    review_state["packet_inbox"] = build_packet_inbox_payload(
        review_state.get("packets", ()),
        attention=attention,
    )
    typed_review_state = review_state_from_payload(review_state)
    coordination = load_coordination_snapshot(
        repo_root=repo_root,
        sources={"review_state": review_state},
        governance=governance,
        review_state=typed_review_state,
    )
    if coordination is not None:
        review_state["coordination"] = coordination.to_dict()
    merged_compat = _apply_compat_projections(
        merged_compat=merged_compat,
        raw_service_identity=raw_service_identity,
        raw_attach_auth_policy=raw_attach_auth_policy,
        bridge_liveness=bridge_liveness,
        reviewer_runtime=reviewer_runtime,
        collaboration=collaboration,
        recovery_assessment=recovery_assessment,
        attention=attention,
        commit_pipeline=commit_pipeline,
        push_decision=push_decision,
        snapshot_id=snapshot_id,
    )
    review_state["_compat"] = merged_compat
    return review_state, {
        "bridge_liveness": bridge_liveness,
        "attention": attention,
        "service_identity": raw_service_identity,
        "attach_auth_policy": raw_attach_auth_policy,
    }


def _apply_compat_projections(
    *,
    merged_compat: dict[str, object],
    raw_service_identity: object,
    raw_attach_auth_policy: object,
    bridge_liveness: dict[str, object],
    reviewer_runtime: object,
    collaboration: object,
    recovery_assessment: object,
    attention: object,
    commit_pipeline: object,
    push_decision: object,
    snapshot_id: object,
) -> dict[str, object]:
    """Populate the compat mapping with typed doctor / push / bridge fields."""
    runtime_daemons = _mapping(_mapping(merged_compat.get("runtime")).get("daemons"))
    merged_compat["service_identity"] = build_service_identity_state(raw_service_identity)
    merged_compat["attach_auth_policy"] = build_attach_auth_policy_state(
        raw_attach_auth_policy
    )
    push_enforcement = _mapping(bridge_liveness.get("push_enforcement"))
    if push_enforcement:
        merged_compat["push_enforcement"] = push_enforcement
    merged_compat["doctor"] = build_reviewer_doctor_surface(
        contract=reviewer_runtime,
        collaboration=asdict(collaboration),
        recovery_assessment=recovery_assessment,
        attention=attention,
        commit_pipeline=commit_pipeline,
        push_authorization=commit_pipeline.push_authorization,
        push_enforcement=push_enforcement,
        runtime_state=runtime_daemons,
        snapshot_id=snapshot_id,
    )
    if push_decision:
        merged_compat["push_decision"] = push_decision
    if snapshot_id:
        merged_compat["snapshot_id"] = snapshot_id
        compat_push_decision = _mapping(merged_compat.get("push_decision"))
        if compat_push_decision:
            updated_push_decision = dict(compat_push_decision)
            updated_push_decision["snapshot_id"] = snapshot_id
            merged_compat["push_decision"] = updated_push_decision
        bridge_projection = _mapping(merged_compat.get("bridge_projection"))
        metadata = _mapping(bridge_projection.get("metadata"))
        if metadata:
            updated_bridge_projection = dict(bridge_projection)
            updated_metadata = dict(metadata)
            updated_metadata["snapshot_id"] = snapshot_id
            updated_bridge_projection["metadata"] = updated_metadata
            merged_compat["bridge_projection"] = updated_bridge_projection
    return merged_compat


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
