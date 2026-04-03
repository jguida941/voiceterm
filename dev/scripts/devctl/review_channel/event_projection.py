"""Projection helpers shared by event-backed review-channel outputs."""

from __future__ import annotations

from dataclasses import asdict
from collections.abc import Mapping
from pathlib import Path

from ..runtime.review_state_models import ReviewQueueState
from .attention import derive_bridge_attention
from .attach_auth_policy import build_attach_auth_policy
from .attach_auth_projection import (
    build_attach_auth_policy_state,
    build_service_identity_state,
)
from .core import DEFAULT_BRIDGE_REL
from .current_session_projection import (
    build_event_current_session,
    current_session_payload,
)
from .event_projection_context import (
    append_event_instruction_context,
    build_event_context_packet,
    build_instruction_source,
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
from .event_projection_queue import (
    derive_event_next_instruction,
    derive_event_next_instruction_bundle,
    derive_event_next_instruction_source,
)
from .service_identity import build_service_identity


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


def enrich_event_review_state(
    *,
    review_state: dict[str, object],
    repo_root: Path,
    review_channel_path: Path,
    projections_root: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    """Attach parity fields needed by event-backed review-state projections."""
    review_state = dict(review_state)
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
    current_session = build_event_current_session(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
    )
    attention = derive_bridge_attention(bridge_liveness)
    collaboration = build_collaboration_session(
        timestamp=str(review_state.get("timestamp") or ""),
        plan_id=str(_mapping(review_state.get("review")).get("plan_id") or ""),
        session_id=str(_mapping(review_state.get("review")).get("session_id") or ""),
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        attention=attention,
        session_output_root=projections_root,
    )
    reviewer_runtime = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness=bridge_liveness,
            current_session=current_session,
            attention=attention,
            collaboration=collaboration,
            session_output_root=projections_root,
            rollover_dir=projections_root.parent / "rollovers",
        )
    )
    commit_pipeline = load_remote_commit_pipeline_contract(output_root=projections_root)
    bridge_liveness["review_accepted"] = (
        reviewer_runtime.review_acceptance.review_accepted
    )
    bridge_liveness["publish_clear"] = reviewer_runtime.publish_clear
    review_state["current_session"] = current_session_payload(current_session)
    review_state["collaboration"] = asdict(collaboration)
    review_state["reviewer_runtime"] = asdict(reviewer_runtime)
    review_state["commit_pipeline"] = commit_pipeline.to_dict()
    review_state["bridge"] = build_event_bridge_state_projection(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
        reviewer_runtime=reviewer_runtime,
    )
    review_state["attention"] = attention
    existing_compat = review_state.get("_compat")
    merged_compat = dict(existing_compat) if isinstance(existing_compat, dict) else {}
    runtime_daemons = _mapping(_mapping(merged_compat.get("runtime")).get("daemons"))
    merged_compat["service_identity"] = build_service_identity_state(raw_service_identity)
    merged_compat["attach_auth_policy"] = build_attach_auth_policy_state(
        raw_attach_auth_policy
    )
    merged_compat["doctor"] = build_reviewer_doctor_surface(
        contract=reviewer_runtime,
        attention=attention,
        commit_pipeline=commit_pipeline,
        publisher_state=_mapping(runtime_daemons.get("publisher")),
        reviewer_supervisor_state=_mapping(
            runtime_daemons.get("reviewer_supervisor")
        ),
    )
    review_state["_compat"] = merged_compat
    return review_state, {
        "bridge_liveness": bridge_liveness,
        "attention": attention,
        "service_identity": raw_service_identity,
        "attach_auth_policy": raw_attach_auth_policy,
    }
def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
