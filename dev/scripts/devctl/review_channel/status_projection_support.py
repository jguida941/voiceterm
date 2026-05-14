"""Shared support helpers for bridge-backed review-state projection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from ..common import display_path
from ..runtime.review_packet_inbox import build_packet_inbox_payload
from ..runtime.review_state_models import (
    packet_inbox_from_mapping,
    RecoveryAssessmentState,
    ReviewAttentionState,
    ReviewCurrentSessionState,
    ReviewQueueState,
    ReviewSessionState,
    ReviewState,
)
from .projection_provenance import REVIEW_STATE_SOURCE_CONTRACT, STATUS_SOURCE_COMMAND
from .packet_control_loop import (
    format_priority_instruction,
    select_priority_pending_packet,
)
from .promotion import PromotionCandidate, promotion_candidate_to_dict
from .registry_context import AgentRegistryContext
from .review_candidate import build_review_candidate, review_candidate_error
from .recovery_assessment import recovery_assessment_to_attention_state
from .status_projection_compat import (
    CompatProjectionInputs,
    attach_bridge_compat_projection,
    legacy_agent_entry,
)
from .topology import build_runtime_agent_registry


@dataclass(frozen=True)
class ReviewStateContext:
    """Grouped path/identity context for review-state projection."""

    repo_root: Path
    bridge_path: Path
    review_channel_path: Path
    output_root: Path
    bridge_text: str
    project_id: str
    timestamp: str
    service_identity: dict[str, object]
    attach_auth_policy: dict[str, object]
    plan_id: str = ""
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    prior_review_state: Mapping[str, object] | None = None
    current_session: ReviewCurrentSessionState | None = None
    reviewer_accepted_implementer_state_hash_override: str | None = None
    recovery_assessment: RecoveryAssessmentState | None = None
    pending_packets: tuple[dict[str, object], ...] = ()
    stale_packet_count: int = 0


@dataclass(frozen=True, slots=True)
class ReviewStatePayloadInputs:
    context: ReviewStateContext
    overall_state: str
    errors: tuple[str, ...]
    promotion_candidate: PromotionCandidate | None
    current_session: ReviewCurrentSessionState
    collaboration: object
    bridge_state: object
    review_candidate: object
    reviewer_runtime: object
    commit_bundle: object
    typed_attention: Mapping[str, object]
    typed_bridge_liveness: Mapping[str, object]
    recovery_assessment: RecoveryAssessmentState | None
    registry_context: AgentRegistryContext
    session_status_projection: Mapping[str, object]


def build_review_state_payload(inputs: ReviewStatePayloadInputs) -> ReviewState:
    """Build the canonical ReviewState payload from bridge-backed inputs."""
    return ReviewState(
        schema_version=1,
        contract_id=REVIEW_STATE_SOURCE_CONTRACT,
        command="review-channel",
        action="status",
        timestamp=inputs.context.timestamp,
        ok=_projection_ok(inputs.overall_state, inputs.errors),
        review=build_review_session(inputs.context),
        queue=build_queue_state(
            inputs.promotion_candidate,
            pending_packets=inputs.context.pending_packets,
            stale_packet_count=inputs.context.stale_packet_count,
        ),
        current_session=inputs.current_session,
        collaboration=inputs.collaboration,
        bridge=inputs.bridge_state,
        review_candidate=inputs.review_candidate,
        push_authorization=inputs.commit_bundle.commit_pipeline.push_authorization,
        reviewer_runtime=inputs.reviewer_runtime,
        commit_pipeline=inputs.commit_bundle.commit_pipeline,
        attention=build_attention(
            inputs.typed_attention,
            recovery_assessment=inputs.recovery_assessment,
        ),
        packets=inputs.context.pending_packets,
        registry=build_runtime_agent_registry(
            context=inputs.registry_context,
            collaboration=inputs.collaboration,
        ),
        packet_inbox=(
            packet_inbox_from_mapping(
                build_packet_inbox_payload(
                    inputs.context.pending_packets,
                    attention=inputs.typed_attention,
                )
            )
            or packet_inbox_from_mapping({"attention_revision": "", "agents": []})
        ),
        recovery_assessment=inputs.recovery_assessment,
        session_status_projection=dict(inputs.session_status_projection),
        warnings=inputs.context.warnings,
        errors=inputs.errors,
        source_identity=inputs.registry_context.source_identity_dict(),
        source_contract=inputs.registry_context.source_contract,
        source_command=inputs.registry_context.source_command,
        observed_fields=inputs.registry_context.observed_fields,
        inferred_fields=inputs.registry_context.inferred_fields,
        snapshot_id=inputs.registry_context.snapshot_id,
        zref=inputs.registry_context.zref,
    )


def attach_review_state_compat(
    *,
    review_state: ReviewState,
    context: ReviewStateContext,
    typed_bridge_liveness: dict[str, object],
    reduced_runtime: dict[str, object] | None,
    doctor: dict[str, object],
) -> dict[str, object]:
    result: dict[str, object] = asdict(review_state)
    return attach_bridge_compat_projection(
        result=result,
        inputs=CompatProjectionInputs(
            project_id=context.project_id,
            bridge_text=context.bridge_text,
            bridge_liveness=typed_bridge_liveness,
            reduced_runtime=reduced_runtime,
            service_identity=context.service_identity,
            attach_auth_policy=context.attach_auth_policy,
            legacy_agents=legacy_agents(result.get("registry")),
            current_session=result.get("current_session"),
            reviewer_runtime=result.get("reviewer_runtime"),
            bridge_state=result.get("bridge"),
            doctor=doctor,
            snapshot_id=review_state.snapshot_id,
            zref=review_state.zref,
            source_identity=review_state.source_identity,
            source_contract=review_state.source_contract,
            source_command=review_state.source_command,
            observed_fields=review_state.observed_fields,
            inferred_fields=review_state.inferred_fields,
        ),
    )


def review_candidate_with_errors(
    *,
    context: ReviewStateContext,
    current_session,
    bridge_liveness,
) -> tuple[object, str]:
    candidate = build_review_candidate(
        repo_root=context.repo_root,
        current_session=current_session,
        bridge_liveness=bridge_liveness,
        prior_review_state=context.prior_review_state,
    )
    return candidate, review_candidate_error(
        current_session=current_session,
        candidate=candidate,
    )


def build_review_session(context: ReviewStateContext) -> ReviewSessionState:
    return ReviewSessionState(
        plan_id=context.plan_id,
        controller_run_id="",
        session_id="markdown-bridge",
        surface_mode="markdown-bridge",
        active_lane="review",
        refresh_seq=1,
        bridge_path=display_path(context.bridge_path, repo_root=context.repo_root),
        review_channel_path=display_path(
            context.review_channel_path,
            repo_root=context.repo_root,
        ),
    )


def build_queue_state(
    promotion_candidate: PromotionCandidate | None,
    *,
    pending_packets: tuple[dict[str, object], ...] = (),
    stale_packet_count: int = 0,
) -> ReviewQueueState:
    pending_counts = _count_pending_by_target(pending_packets)
    derived_instruction = ""
    derived_source: dict[str, object] = {}
    selected_packet, control_metadata = select_priority_pending_packet(pending_packets)
    if selected_packet is not None:
        selection_policy = str(control_metadata.get("selection_policy") or "").strip()
        derived_instruction = format_priority_instruction(
            str(selected_packet.get("summary") or "").strip(),
            selection_policy=selection_policy,
        )
        derived_source = {
            "source_type": "review_packet",
            "packet_id": str(selected_packet.get("packet_id") or "").strip(),
            "from_agent": str(selected_packet.get("from_agent") or "").strip(),
            "to_agent": str(selected_packet.get("to_agent") or "").strip(),
            **control_metadata,
        }
    elif promotion_candidate is not None:
        derived_instruction = promotion_candidate.instruction
        derived_source = promotion_candidate_to_dict(promotion_candidate)
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


def build_attention(
    attention: Mapping[str, object],
    *,
    recovery_assessment: RecoveryAssessmentState | None,
) -> ReviewAttentionState | None:
    if recovery_assessment is not None:
        state = recovery_assessment_to_attention_state(recovery_assessment)
        if state is not None:
            return state
    if not attention:
        return None
    return ReviewAttentionState(
        status=str(attention.get("status") or ""),
        owner=str(attention.get("owner") or ""),
        summary=str(attention.get("summary") or ""),
        recommended_action=str(attention.get("recommended_action") or ""),
        recommended_command=str(attention.get("recommended_command") or ""),
    )


def legacy_agents(registry: object) -> list[dict[str, object]]:
    registry_dict = registry if isinstance(registry, dict) else {}
    raw_agents = registry_dict.get("agents", [])
    return [legacy_agent_entry(agent) for agent in raw_agents]


def _count_pending_by_target(
    packets: tuple[dict[str, object], ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if str(packet.get("status") or "") != "pending":
            continue
        target = str(packet.get("to_agent") or "").strip().lower()
        if target:
            counts[target] = counts.get(target, 0) + 1
    return counts


def _projection_ok(overall_state: str, errors: tuple[str, ...]) -> bool:
    if errors:
        return False
    return overall_state in (
        "fresh",
        "inactive",
        "single_agent_active",
    )
