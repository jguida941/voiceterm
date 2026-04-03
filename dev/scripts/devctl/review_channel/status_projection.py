"""Helpers for bridge-backed review-state projection payloads.

Builds the canonical ``ReviewState`` shape from bridge markdown snapshots so
the bridge-backed and event-backed paths emit the same top-level contract.
Bridge-specific extras (``runtime``, ``service_identity``,
``attach_auth_policy``, ``project_id``) are nested under a
``_compat`` key so they do not masquerade as canonical contract fields.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from ..common import display_path
from ..runtime.review_state_models import (
    AgentRegistryState,
    ReviewAttentionState,
    ReviewQueueState,
    ReviewSessionState,
    ReviewState,
)
from .collaboration_session import build_collaboration_session
from .current_session_projection import build_bridge_current_session
from .handoff import BridgeSnapshot
from .peer_liveness import OverallLivenessState
from .promotion import PromotionCandidate, promotion_candidate_to_dict
from .remote_commit_pipeline_artifact import load_remote_commit_pipeline_contract
from .status_projection_bridge_state import (
    build_review_bridge_state,
    build_typed_bridge_liveness,
)
from .status_projection_compat import (
    CompatProjectionInputs,
    build_bridge_compat_projection,
)
from .reviewer_runtime_contract import (
    ReviewerRuntimeInputs,
    build_reviewer_doctor_surface,
    build_reviewer_runtime_contract,
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


def build_bridge_review_state(
    *,
    context: ReviewStateContext,
    snapshot: BridgeSnapshot,
    bridge_liveness: dict[str, object],
    attention: dict[str, object],
    promotion_candidate: PromotionCandidate | None,
    reduced_runtime: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a canonical ReviewState dict from bridge markdown state."""
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    current_session = build_bridge_current_session(snapshot, bridge_liveness)
    collaboration = build_collaboration_session(
        timestamp=context.timestamp,
        plan_id=context.plan_id,
        session_id="markdown-bridge",
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        attention=attention,
        session_output_root=context.output_root,
    )
    typed_bridge_liveness = build_typed_bridge_liveness(
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        collaboration=collaboration,
    )
    reviewer_runtime = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=snapshot,
            bridge_liveness=typed_bridge_liveness,
            current_session=current_session,
            attention=attention,
            collaboration=collaboration,
            session_output_root=context.output_root,
            rollover_dir=context.output_root.parent / "rollovers",
            bridge_text=context.bridge_text,
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
    commit_pipeline = load_remote_commit_pipeline_contract(
        output_root=context.output_root,
    )
    runtime_daemons = (
        reduced_runtime.get("daemons", {})
        if isinstance(reduced_runtime, dict)
        else {}
    )
    doctor = build_reviewer_doctor_surface(
        contract=reviewer_runtime,
        attention=attention,
        commit_pipeline=commit_pipeline,
        publisher_state=(
            runtime_daemons.get("publisher")
            if isinstance(runtime_daemons.get("publisher"), dict)
            else None
        ),
        reviewer_supervisor_state=(
            runtime_daemons.get("reviewer_supervisor")
            if isinstance(runtime_daemons.get("reviewer_supervisor"), dict)
            else None
        ),
    )

    review_state = ReviewState(
        schema_version=1,
        contract_id="ReviewState",
        command="review-channel",
        action="status",
        timestamp=context.timestamp,
        ok=_projection_ok(overall_state, context.errors),
        review=_build_review_session(context),
        queue=_build_queue_state(promotion_candidate),
        current_session=current_session,
        collaboration=collaboration,
        bridge=bridge_state,
        reviewer_runtime=reviewer_runtime,
        commit_pipeline=commit_pipeline,
        attention=_build_attention(attention),
        packets=(),
        registry=_build_agent_registry(
            timestamp=context.timestamp,
            plan_id=context.plan_id,
            collaboration=collaboration,
        ),
        warnings=context.warnings,
        errors=context.errors,
    )

    result: dict[str, object] = asdict(review_state)

    # Bridge-specific extras live under _compat so the canonical ReviewState
    # payload stays exact.  Consumers should migrate to _compat access; once
    # all callers are migrated the _compat key can be removed entirely.
    registry_dict = result.get("registry")
    raw_agents = registry_dict.get("agents", []) if isinstance(registry_dict, dict) else []
    legacy_agents = []
    for agent in raw_agents:
        entry = dict(agent) if isinstance(agent, dict) else {}
        entry["status"] = entry.get("job_state", "")
        entry["role"] = entry.get("current_job", "")
        entry["capabilities"] = []
        legacy_agents.append(entry)

    compat_inputs = CompatProjectionInputs(
        project_id=context.project_id,
        bridge_text=context.bridge_text,
        bridge_liveness=typed_bridge_liveness,
        reduced_runtime=reduced_runtime,
        service_identity=context.service_identity,
        attach_auth_policy=context.attach_auth_policy,
        legacy_agents=legacy_agents,
        current_session=result.get("current_session"),
        bridge_state=result.get("bridge"),
        doctor=doctor,
    )
    result["_compat"] = _build_compat_projection(compat_inputs)

    return result


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


def _build_queue_state(
    promotion_candidate: PromotionCandidate | None,
) -> ReviewQueueState:
    return ReviewQueueState(
        pending_total=0,
        pending_codex=0,
        pending_claude=0,
        pending_cursor=0,
        pending_operator=0,
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


def _build_attention(attention: dict[str, object]) -> ReviewAttentionState | None:
    if not attention:
        return None
    return ReviewAttentionState(
        status=str(attention.get("status") or ""),
        owner=str(attention.get("owner") or ""),
        summary=str(attention.get("summary") or ""),
        recommended_action=str(attention.get("recommended_action") or ""),
        recommended_command=str(attention.get("recommended_command") or ""),
    )
