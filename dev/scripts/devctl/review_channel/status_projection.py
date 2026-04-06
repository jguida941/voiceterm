"""Helpers for bridge-backed review-state projection payloads.

Builds the canonical ``ReviewState`` shape from bridge markdown snapshots so
the bridge-backed and event-backed paths emit the same top-level contract.
Bridge-specific extras (``runtime``, ``service_identity``,
``attach_auth_policy``, ``project_id``) are nested under a
``_compat`` key so they do not masquerade as canonical contract fields.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from collections.abc import Mapping
from pathlib import Path

from ..common import display_path
from ..runtime.review_state_models import (
    AgentRegistryState,
    RecoveryAssessmentState,
    ReviewAttentionState,
    ReviewQueueState,
    ReviewSessionState,
    ReviewState,
)
from ..runtime.surface_snapshot import build_surface_snapshot_id
from .collaboration_session import build_collaboration_session
from .current_session_projection import build_bridge_current_session
from .handoff import BridgeSnapshot
from .peer_liveness import OverallLivenessState
from .promotion import PromotionCandidate, promotion_candidate_to_dict
from .remote_commit_pipeline_artifact import load_remote_commit_pipeline_contract
from .review_candidate import build_review_candidate, review_candidate_error
from .status_projection_bridge_state import (
    build_review_bridge_state,
    build_typed_bridge_liveness,
)
from .status_projection_compat import (
    CompatProjectionInputs,
    attach_bridge_compat_projection,
    build_bridge_compat_projection,
    legacy_agent_entry,
)
from .reviewer_runtime_contract import (
    ReviewerRuntimeInputs,
    build_reviewer_doctor_surface,
    build_reviewer_runtime_contract,
)
from .recovery_assessment import recovery_assessment_to_attention_state
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
    reviewer_accepted_implementer_state_hash_override: str | None = None
    recovery_assessment: RecoveryAssessmentState | None = None
    pending_packets: tuple[dict[str, object], ...] = ()


def build_bridge_review_state(
    *,
    context: ReviewStateContext,
    snapshot: BridgeSnapshot,
    bridge_liveness: dict[str, object],
    attention: dict[str, object] | None,
    recovery_assessment: RecoveryAssessmentState | None,
    promotion_candidate: PromotionCandidate | None,
    push_decision: Mapping[str, object] | None = None,
    reduced_runtime: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a canonical ReviewState dict from bridge markdown state."""
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    current_session = build_bridge_current_session(snapshot, bridge_liveness)
    warnings = list(context.warnings)
    errors = list(context.errors)
    typed_attention = (
        attention
        if isinstance(attention, Mapping)
        else {}
    )
    collaboration = build_collaboration_session(
        timestamp=context.timestamp,
        plan_id=context.plan_id,
        session_id="markdown-bridge",
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        attention=typed_attention,
        session_output_root=context.output_root,
    )
    typed_bridge_liveness = build_typed_bridge_liveness(
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        collaboration=collaboration,
        snapshot=snapshot,
    )
    reviewer_runtime = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=snapshot,
            bridge_liveness=typed_bridge_liveness,
            current_session=current_session,
            recovery_assessment=recovery_assessment,
            attention=typed_attention,
            collaboration=collaboration,
            session_output_root=context.output_root,
            rollover_dir=context.output_root.parent / "rollovers",
            bridge_text=context.bridge_text,
            prior_review_state=context.prior_review_state,
            reviewer_accepted_implementer_state_hash_override=(
                context.reviewer_accepted_implementer_state_hash_override
            ),
        )
    )
    bridge_state = build_review_bridge_state(
        snapshot=snapshot,
        bridge_liveness=typed_bridge_liveness,
        overall_state=overall_state,
        current_session=current_session,
        collaboration=collaboration,
        reviewer_runtime=reviewer_runtime,
    )
    review_candidate, candidate_error = _review_candidate_with_errors(
        context=context,
        current_session=current_session,
        bridge_liveness=typed_bridge_liveness,
    )
    if candidate_error and candidate_error not in errors:
        errors.append(candidate_error)
    commit_pipeline = load_remote_commit_pipeline_contract(
        output_root=context.output_root,
    )
    snapshot_id = build_surface_snapshot_id(
        reviewer_runtime=reviewer_runtime,
        commit_pipeline=commit_pipeline,
        push_decision=push_decision,
    )
    commit_pipeline = replace(commit_pipeline, snapshot_id=snapshot_id)
    runtime_daemons = (
        reduced_runtime.get("daemons", {})
        if isinstance(reduced_runtime, dict)
        else {}
    )
    doctor = build_reviewer_doctor_surface(
        contract=reviewer_runtime,
        recovery_assessment=recovery_assessment,
        attention=typed_attention,
        commit_pipeline=commit_pipeline,
        push_authorization=commit_pipeline.push_authorization,
        push_enforcement=typed_bridge_liveness.get("push_enforcement"),
        runtime_state=runtime_daemons,
        snapshot_id=snapshot_id,
    )

    review_state = ReviewState(
        schema_version=1,
        contract_id="ReviewState",
        command="review-channel",
        action="status",
        timestamp=context.timestamp,
        ok=_projection_ok(overall_state, tuple(errors)),
        review=_build_review_session(context),
        queue=_build_queue_state(
            promotion_candidate,
            pending_packets=context.pending_packets,
        ),
        current_session=current_session,
        collaboration=collaboration,
        bridge=bridge_state,
        review_candidate=review_candidate,
        push_authorization=commit_pipeline.push_authorization,
        reviewer_runtime=reviewer_runtime,
        commit_pipeline=commit_pipeline,
        attention=_build_attention(
            typed_attention,
            recovery_assessment=recovery_assessment,
        ),
        packets=context.pending_packets,
        registry=_build_agent_registry(
            timestamp=context.timestamp,
            plan_id=context.plan_id,
            collaboration=collaboration,
        ),
        recovery_assessment=recovery_assessment,
        warnings=tuple(warnings),
        errors=tuple(errors),
        snapshot_id=snapshot_id,
    )

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
            legacy_agents=_legacy_agents(result.get("registry")),
            current_session=result.get("current_session"),
            bridge_state=result.get("bridge"),
            doctor=doctor,
            snapshot_id=snapshot_id,
        ),
    )


def _projection_ok(overall_state: str, errors: tuple[str, ...]) -> bool:
    if errors:
        return False
    return overall_state in (
        OverallLivenessState.FRESH,
        OverallLivenessState.INACTIVE,
    )


def _build_compat_projection(
    inputs: CompatProjectionInputs,
) -> dict[str, object]:
    return build_bridge_compat_projection(inputs=inputs)


def _legacy_agents(registry: object) -> list[dict[str, object]]:
    registry_dict = registry if isinstance(registry, dict) else {}
    raw_agents = registry_dict.get("agents", [])
    return [legacy_agent_entry(agent) for agent in raw_agents]


def _build_review_session(context: ReviewStateContext) -> ReviewSessionState:
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


def _build_agent_registry(
    *,
    timestamp: str,
    collaboration,
    plan_id: str = "",
) -> AgentRegistryState:
    return build_runtime_agent_registry(
        timestamp=timestamp,
        plan_id=plan_id,
        collaboration=collaboration,
    )


def _review_candidate_with_errors(
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


def _build_queue_state(
    promotion_candidate: PromotionCandidate | None,
    *,
    pending_packets: tuple[dict[str, object], ...] = (),
) -> ReviewQueueState:
    pending_counts = _count_pending_by_target(pending_packets)
    return ReviewQueueState(
        pending_total=sum(pending_counts.values()),
        pending_codex=pending_counts.get("codex", 0),
        pending_claude=pending_counts.get("claude", 0),
        pending_cursor=pending_counts.get("cursor", 0),
        pending_operator=pending_counts.get("operator", 0),
        stale_packet_count=0,
        derived_next_instruction=(
            promotion_candidate.instruction if promotion_candidate is not None else ""
        ),
        derived_next_instruction_source=(
            promotion_candidate_to_dict(promotion_candidate)
            if promotion_candidate is not None
            else {}
        ),
    )


def _count_pending_by_target(
    packets: tuple[dict[str, object], ...],
) -> dict[str, int]:
    """Count pending packets grouped by target agent."""
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


def _build_attention(
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
