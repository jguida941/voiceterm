"""Orchestration helpers for event-backed review-state projections."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from types import SimpleNamespace

from ..runtime.governance_scan import scan_repo_governance_safely
from ..runtime.review_packet_inbox import build_packet_inbox_payload
from ..runtime.review_state_parser import review_state_from_payload
from ..runtime.surface_snapshot import build_surface_snapshot_id, build_surface_zref
from .core import DEFAULT_BRIDGE_REL
from .current_session_attention import codex_packet_attention_requires_clear
from .current_session_projection import current_session_payload
from .event_projection_bridge import build_event_bridge_state_projection
from .event_projection_support import (
    CompatProjectionInputs,
    apply_compat_projections,
    enrichment_extras,
    push_authorization_payload,
)
from .handoff import extract_bridge_snapshot
from .reviewer_runtime_contract import ReviewerRuntimeInputs


@dataclass(frozen=True, slots=True)
class EventProjectionBaseState:
    repo_root: object
    projections_root: object
    session_output_root: object
    review_channel_path: object
    plan_id: str
    session_id: str
    bridge_text: str
    bridge_snapshot: object


@dataclass(frozen=True, slots=True)
class EventProjectionIdentityState:
    raw_service_identity: object
    raw_attach_auth_policy: object


@dataclass(frozen=True, slots=True)
class EventProjectionRuntimeState:
    governance: object
    bridge_liveness: dict[str, object]
    current_session: object
    recovery_assessment: object
    attention: dict[str, object]
    collaboration: object
    typed_bridge_liveness: dict[str, object]
    reviewer_runtime: object
    push_decision: object
    commit_pipeline: object
    snapshot_id: str = ""
    zref: str = ""


def enrich_event_review_state_impl(
    *,
    review_state: dict[str, object],
    context,
    deps: SimpleNamespace,
) -> tuple[dict[str, object], dict[str, object]]:
    review_state = dict(review_state)
    deps.attach_event_queue_state(review_state, artifact_root=context.artifact_root)

    base = _build_projection_base(review_state, context, deps)
    identity = _build_projection_identity(base, deps)
    runtime = _build_projection_runtime(review_state, context, deps, base)

    snapshot_id = build_surface_snapshot_id(
        reviewer_runtime=runtime.reviewer_runtime,
        commit_pipeline=runtime.commit_pipeline,
        push_decision=runtime.push_decision,
    )
    head_sha = str(
        (runtime.typed_bridge_liveness.get("push_enforcement") or {}).get(
            "current_head_commit"
        )
        or runtime.commit_pipeline.commit_sha
        or ""
    ).strip()
    zref = build_surface_zref(snapshot_id=snapshot_id, head_sha=head_sha)
    commit_pipeline = replace(runtime.commit_pipeline, snapshot_id=snapshot_id, zref=zref)

    review_state, extras = _apply_review_state_enrichment(
        review_state=review_state,
        deps=deps,
        base=base,
        identity=identity,
        runtime=replace(
            runtime,
            commit_pipeline=commit_pipeline,
            snapshot_id=snapshot_id,
            zref=zref,
        ),
    )
    return review_state, extras


def _build_projection_base(
    review_state: dict[str, object],
    context,
    deps: SimpleNamespace,
) -> EventProjectionBaseState:
    repo_root = context.repo_root
    projections_root = context.projections_root
    session_output_root = deps.resolve_session_output_root(projections_root)
    plan_id, session_id = deps.review_identifiers(review_state)
    bridge_text, bridge_snapshot = _load_bridge_inputs(repo_root)
    return EventProjectionBaseState(
        repo_root=repo_root,
        projections_root=projections_root,
        session_output_root=session_output_root,
        review_channel_path=context.review_channel_path,
        plan_id=plan_id,
        session_id=session_id,
        bridge_text=bridge_text,
        bridge_snapshot=bridge_snapshot,
    )


def _build_projection_identity(
    base: EventProjectionBaseState,
    deps: SimpleNamespace,
) -> EventProjectionIdentityState:
    raw_service_identity = deps.build_service_identity(
        repo_root=base.repo_root,
        bridge_path=base.repo_root / DEFAULT_BRIDGE_REL,
        review_channel_path=base.review_channel_path,
        output_root=base.projections_root,
    )
    raw_attach_auth_policy = deps.build_attach_auth_policy(
        service_identity=raw_service_identity
    )
    return EventProjectionIdentityState(
        raw_service_identity=raw_service_identity,
        raw_attach_auth_policy=raw_attach_auth_policy,
    )


def _build_projection_runtime(
    review_state: dict[str, object],
    context,
    deps: SimpleNamespace,
    base: EventProjectionBaseState,
) -> EventProjectionRuntimeState:
    bridge_liveness = deps.build_event_bridge_liveness_projection(
        review_state,
        bridge_snapshot=base.bridge_snapshot,
    )
    bridge_liveness["push_enforcement"] = (
        context.push_enforcement
        if context.push_enforcement is not None
        else deps.build_bridge_push_enforcement_state(base.repo_root)
    )
    deps.attach_conductor_session_state(
        bridge_liveness=bridge_liveness,
        output_root=base.session_output_root,
    )
    current_session = _resolve_current_session(
        review_state,
        context,
        bridge_liveness,
        deps,
        bridge_snapshot=base.bridge_snapshot,
    )
    governance = scan_repo_governance_safely(base.repo_root)
    recovery_assessment = deps.build_recovery_assessment(
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        operator_interaction_mode=deps.operator_interaction_mode(governance),
    )
    attention = deps.recovery_assessment_to_attention_payload(recovery_assessment)
    collaboration = deps.build_collaboration_session(
        timestamp=str(review_state.get("timestamp") or ""),
        plan_id=base.plan_id,
        session_id=base.session_id,
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        attention=attention,
        repo_root=base.repo_root,
        session_output_root=base.session_output_root,
    )
    typed_bridge_liveness = deps.build_typed_bridge_liveness(
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        collaboration=collaboration,
        snapshot=base.bridge_snapshot,
    )
    reviewer_runtime = deps.build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness=typed_bridge_liveness,
            current_session=current_session,
            recovery_assessment=recovery_assessment,
            attention=attention,
            collaboration=collaboration,
            session_output_root=base.session_output_root,
            rollover_dir=base.projections_root.parent / "rollovers",
        )
    )
    push_decision = deps.build_status_push_decision(
        bridge_liveness=typed_bridge_liveness,
        reviewer_runtime=reviewer_runtime,
    )
    commit_pipeline = deps.load_remote_commit_pipeline_contract(
        output_root=base.projections_root
    )
    return EventProjectionRuntimeState(
        governance=governance,
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        recovery_assessment=recovery_assessment,
        attention=attention,
        collaboration=collaboration,
        typed_bridge_liveness=typed_bridge_liveness,
        reviewer_runtime=reviewer_runtime,
        push_decision=push_decision,
        commit_pipeline=commit_pipeline,
    )


def _apply_review_state_enrichment(
    *,
    review_state: dict[str, object],
    deps: SimpleNamespace,
    base: EventProjectionBaseState,
    identity: EventProjectionIdentityState,
    runtime: EventProjectionRuntimeState,
) -> tuple[dict[str, object], dict[str, object]]:
    runtime.typed_bridge_liveness["review_accepted"] = (
        runtime.reviewer_runtime.review_acceptance.review_accepted
    )
    runtime.typed_bridge_liveness["publish_clear"] = runtime.reviewer_runtime.publish_clear

    review_state["snapshot_id"] = runtime.snapshot_id
    review_state["zref"] = runtime.zref
    review_state["current_session"] = current_session_payload(runtime.current_session)
    review_state["collaboration"] = asdict(runtime.collaboration)
    review_state["reviewer_runtime"] = asdict(runtime.reviewer_runtime)
    review_state["commit_pipeline"] = runtime.commit_pipeline.to_dict()
    review_state["push_authorization"] = push_authorization_payload(
        runtime.commit_pipeline
    )
    review_state["recovery_assessment"] = asdict(runtime.recovery_assessment)
    review_state["bridge"] = build_event_bridge_state_projection(
        review_state=review_state,
        bridge_liveness=runtime.typed_bridge_liveness,
        reviewer_runtime=runtime.reviewer_runtime,
    )
    review_state["attention"] = runtime.attention
    review_state["packet_inbox"] = build_packet_inbox_payload(
        review_state.get("packets", ()),
        attention=runtime.attention,
    )

    typed_review_state = review_state_from_payload(review_state)
    coordination = deps.load_coordination_snapshot(
        repo_root=base.repo_root,
        sources={"review_state": review_state},
        governance=runtime.governance,
        review_state=typed_review_state,
    )
    if coordination is not None:
        review_state["coordination"] = coordination.to_dict()

    existing_compat = review_state.get("_compat")
    merged_compat = dict(existing_compat) if isinstance(existing_compat, dict) else {}
    review_state["_compat"] = apply_compat_projections(
        merged_compat=merged_compat,
        inputs=CompatProjectionInputs(
            raw_service_identity=identity.raw_service_identity,
            raw_attach_auth_policy=identity.raw_attach_auth_policy,
            bridge_text=base.bridge_text,
            bridge_liveness=runtime.typed_bridge_liveness,
            current_session=review_state["current_session"],
            reviewer_runtime_payload=review_state["reviewer_runtime"],
            bridge_state=review_state["bridge"],
            packets=review_state.get("packets"),
            reviewer_runtime=runtime.reviewer_runtime,
            collaboration=runtime.collaboration,
            recovery_assessment=runtime.recovery_assessment,
            attention=runtime.attention,
            commit_pipeline=runtime.commit_pipeline,
            push_decision=runtime.push_decision,
            snapshot_id=runtime.snapshot_id,
            zref=runtime.zref,
        ),
    )

    return review_state, enrichment_extras(
        bridge_liveness=runtime.typed_bridge_liveness,
        attention=runtime.attention,
        raw_service_identity=identity.raw_service_identity,
        raw_attach_auth_policy=identity.raw_attach_auth_policy,
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
