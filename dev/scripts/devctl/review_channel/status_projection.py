"""Helpers for bridge-backed review-state projection payloads.

Builds the canonical ``ReviewState`` shape from bridge markdown snapshots so
the bridge-backed and event-backed paths emit the same top-level contract.
Bridge-specific extras (``runtime``, ``service_identity``,
``attach_auth_policy``, ``project_id``) are nested under a
``_compat`` key so they do not masquerade as canonical contract fields.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

from ..runtime.coordination_loader import load_coordination_snapshot
from ..runtime.governance_scan import scan_repo_governance_safely
from ..runtime.review_state_models import (
    RecoveryAssessmentState,
    ReviewState,
)
from .collaboration_session import build_collaboration_session
from .current_session_projection import resolve_current_session_authority
from .handoff import BridgeSnapshot
from .peer_liveness import OverallLivenessState
from .promotion import PromotionCandidate, promotion_candidate_to_dict
from .status_projection_bridge_state import (
    build_review_bridge_state,
    build_typed_bridge_liveness,
)
from .status_projection_compat import (
    CompatProjectionInputs,
)
from .reviewer_runtime_contract import (
    ReviewerRuntimeInputs,
    build_reviewer_runtime_contract,
)
from .recovery_assessment import recovery_assessment_to_attention_state
from .status_projection_commit_bundle import (
    CommitProjectionInputs,
    build_commit_projection_bundle,
)
from .projection_provenance import (
    PROVENANCE_INFERRED_FIELDS,
    PROVENANCE_OBSERVED_FIELDS,
    REVIEW_STATE_SOURCE_CONTRACT,
    STATUS_SOURCE_COMMAND,
    projection_source_identity,
)
from .registry_context import AgentRegistryContext
from .status_projection_support import (
    ReviewStateContext,
    ReviewStatePayloadInputs,
    attach_review_state_compat,
    build_review_state_payload,
    review_candidate_with_errors,
)


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
    current_session = context.current_session or resolve_current_session_authority(
        snapshot=snapshot,
        bridge_liveness=bridge_liveness,
        prior_review_state=context.prior_review_state,
    )
    warnings = list(context.warnings)
    errors = list(context.errors)
    typed_attention = attention if isinstance(attention, Mapping) else {}
    collaboration = build_collaboration_session(
        timestamp=context.timestamp,
        plan_id=context.plan_id,
        session_id="markdown-bridge",
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        attention=typed_attention,
        repo_root=context.repo_root,
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
    review_candidate, candidate_error = review_candidate_with_errors(
        context=context,
        current_session=current_session,
        bridge_liveness=typed_bridge_liveness,
    )
    if candidate_error and candidate_error not in errors:
        errors.append(candidate_error)
    commit_bundle = build_commit_projection_bundle(
        CommitProjectionInputs(
            output_root=context.output_root,
            reviewer_runtime=reviewer_runtime,
            collaboration=collaboration,
            recovery_assessment=recovery_assessment,
            attention=typed_attention,
            push_decision=push_decision,
            bridge_liveness=typed_bridge_liveness,
            reduced_runtime=reduced_runtime,
        )
    )
    head_sha = str(
        (typed_bridge_liveness.get("push_enforcement") or {}).get("current_head_commit")
        or commit_bundle.commit_pipeline.commit_sha
        or ""
    ).strip()

    registry_context = AgentRegistryContext(
        timestamp=context.timestamp,
        plan_id=context.plan_id,
        snapshot_id=commit_bundle.snapshot_id,
        zref=commit_bundle.zref,
        source_identity=projection_source_identity(
            typed_bridge_liveness=typed_bridge_liveness,
            generation_id=commit_bundle.commit_pipeline.generation_id,
            head_sha=head_sha,
        ),
        source_contract=REVIEW_STATE_SOURCE_CONTRACT,
        source_command=STATUS_SOURCE_COMMAND,
        observed_fields=PROVENANCE_OBSERVED_FIELDS,
        inferred_fields=PROVENANCE_INFERRED_FIELDS,
    )
    review_state = build_review_state_payload(
        ReviewStatePayloadInputs(
            context=context,
            overall_state=overall_state,
            errors=tuple(errors),
            promotion_candidate=promotion_candidate,
            current_session=current_session,
            collaboration=collaboration,
            bridge_state=bridge_state,
            review_candidate=review_candidate,
            reviewer_runtime=reviewer_runtime,
            commit_bundle=commit_bundle,
            typed_attention=typed_attention,
            typed_bridge_liveness=typed_bridge_liveness,
            recovery_assessment=recovery_assessment,
            registry_context=registry_context,
        )
    )
    governance = scan_repo_governance_safely(context.repo_root)
    review_state = replace(
        review_state,
        coordination=load_coordination_snapshot(
            repo_root=context.repo_root,
            sources={"review_state": review_state.to_dict()},
            governance=governance,
            review_state=review_state,
        ),
    )
    return attach_review_state_compat(
        review_state=review_state,
        context=context,
        typed_bridge_liveness=typed_bridge_liveness,
        reduced_runtime=reduced_runtime,
        doctor=commit_bundle.doctor,
    )


def _projection_ok(overall_state: str, errors: tuple[str, ...]) -> bool:
    if errors:
        return False
    return overall_state in (
        OverallLivenessState.FRESH,
        OverallLivenessState.INACTIVE,
        OverallLivenessState.SINGLE_AGENT_ACTIVE,
    )
