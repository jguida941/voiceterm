"""Projection helpers shared by event-backed review-channel outputs."""

from __future__ import annotations

from types import SimpleNamespace

from .attach_auth_policy import build_attach_auth_policy
from .attach_auth_projection import (
    build_attach_auth_policy_state,
    build_service_identity_state,
)
from .collaboration_session import build_collaboration_session
from .current_session_projection import (
    build_bridge_current_session,
    build_event_current_session,
    current_session_payload,
)
from .event_projection_assembly import enrich_event_review_state_impl
from .event_projection_bridge import (
    build_event_bridge_liveness_projection,
    build_event_bridge_state_projection,
)
from .event_projection_context import (
    append_event_instruction_context,
    build_event_context_packet,
    build_instruction_source,
)
from .event_projection_enrichment import EventProjectionContext
from .event_projection_queue import (
    attach_event_queue_state,
    build_event_queue_summary as _build_event_queue_summary,
    build_event_queue_state as _build_event_queue_state,
)
from .event_projection_support import (
    apply_compat_projections,
    enrichment_extras,
    operator_interaction_mode,
    push_authorization_payload,
    review_identifiers,
    session_output_root as resolve_session_output_root,
)
from .recovery_assessment import (
    build_recovery_assessment,
    recovery_assessment_to_attention_payload,
)
from .remote_commit_pipeline_artifact import load_remote_commit_pipeline_contract
from .reviewer_runtime_contract import (
    ReviewerRuntimeInputs,
    build_reviewer_runtime_contract,
)
from .service_identity import build_service_identity
from .status_projection_helpers import (
    attach_conductor_session_state,
    build_bridge_push_enforcement_state,
)
from .status_projection_bridge_state import build_typed_bridge_liveness
from .status_push_decision import build_status_push_decision
from ..runtime.coordination_loader import load_coordination_snapshot
from ..runtime.surface_snapshot import build_surface_snapshot_id


def build_event_queue_summary(
    pending_counts: dict[str, int],
    stale_packet_count: int,
    *,
    packets: list[dict[str, object]],
) -> dict[str, object]:
    return _build_event_queue_summary(
        pending_counts,
        stale_packet_count,
        packets=packets,
        build_event_context_packet_fn=build_event_context_packet,
        append_event_instruction_context_fn=append_event_instruction_context,
        build_instruction_source_fn=build_instruction_source,
    )


def build_event_queue_state(
    pending_counts: dict[str, int],
    stale_packet_count: int,
    packet_rows: list[dict[str, object]],
) -> object:
    return _build_event_queue_state(
        pending_counts,
        stale_packet_count,
        packet_rows,
        build_event_context_packet_fn=build_event_context_packet,
        append_event_instruction_context_fn=append_event_instruction_context,
        build_instruction_source_fn=build_instruction_source,
    )


def enrich_event_review_state(
    *,
    review_state: dict[str, object],
    context: EventProjectionContext,
) -> tuple[dict[str, object], dict[str, object]]:
    deps = SimpleNamespace(
        attach_event_queue_state=attach_event_queue_state,
        build_attach_auth_policy=build_attach_auth_policy,
        build_attach_auth_policy_state=build_attach_auth_policy_state,
        build_bridge_current_session=build_bridge_current_session,
        build_bridge_push_enforcement_state=build_bridge_push_enforcement_state,
        build_collaboration_session=build_collaboration_session,
        build_event_bridge_liveness_projection=build_event_bridge_liveness_projection,
        build_event_bridge_state_projection=build_event_bridge_state_projection,
        build_event_current_session=build_event_current_session,
        build_recovery_assessment=build_recovery_assessment,
        attach_conductor_session_state=attach_conductor_session_state,
        build_reviewer_runtime_contract=build_reviewer_runtime_contract,
        build_service_identity=build_service_identity,
        build_service_identity_state=build_service_identity_state,
        build_status_push_decision=build_status_push_decision,
        build_typed_bridge_liveness=build_typed_bridge_liveness,
        current_session_payload=current_session_payload,
        enrichment_extras=enrichment_extras,
        load_coordination_snapshot=load_coordination_snapshot,
        load_remote_commit_pipeline_contract=load_remote_commit_pipeline_contract,
        operator_interaction_mode=operator_interaction_mode,
        push_authorization_payload=push_authorization_payload,
        recovery_assessment_to_attention_payload=recovery_assessment_to_attention_payload,
        review_identifiers=review_identifiers,
        resolve_session_output_root=resolve_session_output_root,
        apply_compat_projections=apply_compat_projections,
    )
    return enrich_event_review_state_impl(
        review_state=review_state,
        context=context,
        deps=deps,
    )
