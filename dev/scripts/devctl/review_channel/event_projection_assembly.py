"""Orchestration helpers for event-backed review-state projections."""

from __future__ import annotations

from dataclasses import asdict, replace
from types import SimpleNamespace

from ..runtime.coordination_loader import load_coordination_snapshot
from ..runtime.governance_scan import scan_repo_governance_safely
from ..runtime.review_packet_inbox import build_packet_inbox_payload
from ..runtime.review_state_parser import review_state_from_payload
from ..runtime.surface_snapshot import build_surface_snapshot_id, build_surface_zref
from .attach_auth_policy import build_attach_auth_policy
from .attach_auth_projection import (
    build_attach_auth_policy_state,
    build_service_identity_state,
)
from .collaboration_session import build_collaboration_session
from .core import DEFAULT_BRIDGE_REL
from .current_session_projection import (
    build_event_current_session,
    current_session_payload,
)
from .event_projection_bridge import (
    build_event_bridge_liveness_projection,
    build_event_bridge_state_projection,
)
from .event_projection_context import (
    append_event_instruction_context,
    build_event_context_packet,
    build_instruction_source,
)
from .current_session_attention import codex_packet_attention_requires_clear
from .event_projection_queue import attach_event_queue_state
from .event_projection_support import (
    CompatProjectionInputs,
    apply_compat_projections,
    enrichment_extras,
    operator_interaction_mode,
    push_authorization_payload,
    review_identifiers,
    session_output_root as resolve_session_output_root,
)
from .handoff import extract_bridge_snapshot
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
from .status_projection_helpers import build_bridge_push_enforcement_state
from .status_push_decision import build_status_push_decision


def enrich_event_review_state_impl(
    *,
    review_state: dict[str, object],
    context,
    deps: SimpleNamespace,
) -> tuple[dict[str, object], dict[str, object]]:
    review_state = dict(review_state)
    deps.attach_event_queue_state(review_state, artifact_root=context.artifact_root)

    repo_root, projections_root = context.repo_root, context.projections_root
    session_output_root = deps.resolve_session_output_root(projections_root)
    review_channel_path = context.review_channel_path
    plan_id, session_id = deps.review_identifiers(review_state)
    bridge_text, bridge_snapshot = _load_bridge_inputs(repo_root)

    raw_service_identity = deps.build_service_identity(
        repo_root=repo_root,
        bridge_path=repo_root / DEFAULT_BRIDGE_REL,
        review_channel_path=review_channel_path,
        output_root=projections_root,
    )
    raw_attach_auth_policy = deps.build_attach_auth_policy(service_identity=raw_service_identity)

    bridge_liveness = deps.build_event_bridge_liveness_projection(review_state, bridge_snapshot=bridge_snapshot)
    bridge_liveness["push_enforcement"] = (
        context.push_enforcement
        if context.push_enforcement is not None
        else deps.build_bridge_push_enforcement_state(repo_root)
    )
    deps.attach_conductor_session_state(
        bridge_liveness=bridge_liveness,
        output_root=session_output_root,
    )

    current_session = _resolve_current_session(
        review_state,
        context,
        bridge_liveness,
        deps,
        bridge_snapshot=bridge_snapshot,
    )

    governance = scan_repo_governance_safely(repo_root)
    recovery_assessment = deps.build_recovery_assessment(
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        operator_interaction_mode=deps.operator_interaction_mode(governance),
    )
    attention = deps.recovery_assessment_to_attention_payload(recovery_assessment)

    collaboration = deps.build_collaboration_session(
        timestamp=str(review_state.get("timestamp") or ""),
        plan_id=plan_id,
        session_id=session_id,
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        attention=attention,
        repo_root=repo_root,
        session_output_root=session_output_root,
    )

    reviewer_runtime = deps.build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness=bridge_liveness,
            current_session=current_session,
            recovery_assessment=recovery_assessment,
            attention=attention,
            collaboration=collaboration,
            session_output_root=session_output_root,
            rollover_dir=projections_root.parent / "rollovers",
        )
    )

    push_decision = deps.build_status_push_decision(
        bridge_liveness=bridge_liveness,
        reviewer_runtime=reviewer_runtime,
    )
    commit_pipeline = deps.load_remote_commit_pipeline_contract(output_root=projections_root)
    existing_compat = review_state.get("_compat")
    merged_compat = dict(existing_compat) if isinstance(existing_compat, dict) else {}

    snapshot_id = build_surface_snapshot_id(
        reviewer_runtime=reviewer_runtime,
        commit_pipeline=commit_pipeline,
        push_decision=push_decision,
    )
    head_sha = str(
        (bridge_liveness.get("push_enforcement") or {}).get("current_head_commit")
        or commit_pipeline.commit_sha
        or ""
    ).strip()
    zref = build_surface_zref(snapshot_id=snapshot_id, head_sha=head_sha)
    commit_pipeline = replace(commit_pipeline, snapshot_id=snapshot_id, zref=zref)

    bridge_liveness["review_accepted"] = (
        reviewer_runtime.review_acceptance.review_accepted
    )
    bridge_liveness["publish_clear"] = reviewer_runtime.publish_clear

    review_state["snapshot_id"] = snapshot_id
    review_state["zref"] = zref
    review_state["current_session"] = current_session_payload(current_session)
    review_state["collaboration"] = asdict(collaboration)
    review_state["reviewer_runtime"] = asdict(reviewer_runtime)
    review_state["commit_pipeline"] = commit_pipeline.to_dict()
    review_state["push_authorization"] = push_authorization_payload(commit_pipeline)
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
    coordination = deps.load_coordination_snapshot(
        repo_root=repo_root,
        sources={"review_state": review_state},
        governance=governance,
        review_state=typed_review_state,
    )
    if coordination is not None:
        review_state["coordination"] = coordination.to_dict()

    merged_compat = apply_compat_projections(
        merged_compat=merged_compat,
        inputs=CompatProjectionInputs(
            raw_service_identity=raw_service_identity,
            raw_attach_auth_policy=raw_attach_auth_policy,
            bridge_text=bridge_text,
            bridge_liveness=bridge_liveness,
            current_session=review_state["current_session"],
            reviewer_runtime_payload=review_state["reviewer_runtime"],
            bridge_state=review_state["bridge"],
            packets=review_state.get("packets"),
            reviewer_runtime=reviewer_runtime,
            collaboration=collaboration,
            recovery_assessment=recovery_assessment,
            attention=attention,
            commit_pipeline=commit_pipeline,
            push_decision=push_decision,
            snapshot_id=snapshot_id,
            zref=zref,
        ),
    )
    review_state["_compat"] = merged_compat

    return review_state, enrichment_extras(
        bridge_liveness=bridge_liveness,
        attention=attention,
        raw_service_identity=raw_service_identity,
        raw_attach_auth_policy=raw_attach_auth_policy,
    )


def _resolve_current_session(
    review_state: dict[str, object],
    context,
    bridge_liveness: dict[str, object],
    deps: SimpleNamespace,
    *,
    bridge_snapshot=None,
):
    current_session = deps.build_event_current_session(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
        prior_review_state=context.prior_review_state,
    )
    if codex_packet_attention_requires_clear(review_state):
        current_session = replace(
            current_session,
            current_instruction="",
            current_instruction_revision="",
        )
    return current_session


def _load_bridge_inputs(repo_root):
    try:
        bridge_text = (repo_root / DEFAULT_BRIDGE_REL).read_text(encoding="utf-8")
    except OSError:
        return "", None
    return bridge_text, extract_bridge_snapshot(bridge_text)
