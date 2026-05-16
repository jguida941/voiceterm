"""Typed startup-context surface for AI agent sessions."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from .recovery_authority import derive_recovery_authority

if TYPE_CHECKING:
    from .review_state_models import ReviewState

from .authority_snapshot import AuthoritySnapshot, project_authority_snapshot
from .authority_snapshot_actions import AuthorityModeInputs, authority_mode_projection
from .control_topology import derive_startup_control_truth
from .governance_scan import scan_repo_governance_safely
from .key_surfaces import startup_key_surfaces
from .packet_intent_anchor import (
    packet_intent_anchors_from_packets,
    plan_iteration_session_from_anchors,
)
from .project_governance import ProjectGovernance
from .project_governance_contract import (
    delivery_mode_requires_push,
    normalize_delivery_mode,
)
from .review_state_locator import load_current_review_state
from .review_state_semantics import is_missing_instruction
from .startup_advisory_decision import (
    derive_advisory_decision as _derive_advisory_decision,
)
from .startup_blocker_decision import derive_startup_blocker
from .startup_continuity import (
    startup_continuity_attention,
    startup_packet_continuity_index,
    startup_packet_carry_forward_debt,
    startup_runtime_spine_closure,
)
from .startup_context_assembly import (
    StartupContextAssemblyInput,
    _assemble_startup_context,
    _collect_active_bypass_lifecycles,
    compute_startup_continuity_signals,
    extract_coordination_state_projection,
)
from .startup_context_models import ReviewerGateState, StartupContext
from .startup_context_projections import build_contract_ownership_map
from .startup_push_decision import PushDecisionState
from .startup_push_decision import derive_push_decision as _derive_push_decision
from .startup_review_state import (
    load_startup_review_state as _load_startup_review_state,
)
from .startup_signals import compact_startup_quality_signals, load_startup_quality_signals
from .startup_runtime_truth import (
    StartupQualityBlockerDeps,
    startup_quality_blocker_inputs as _startup_quality_blocker_inputs_impl,
)
from .startup_runtime_truth import (
    startup_runtime_truth_and_gate as _startup_runtime_truth_and_gate,
)
from .surface_snapshot import build_surface_snapshot_id, build_surface_zref
from .work_intake import WorkIntakePacket, WorkIntakeStateInputs, build_work_intake_packet
from .work_intake_coordination import build_work_intake_coordination_state
from .work_intake_ownership import build_work_intake_ownership_state
from .worktree_orphan_snapshot_projection import build_orphan_snapshot_projection


def _startup_quality_blocker_inputs(
    *,
    repo_root: Path,
    review_state: "ReviewState | None",
    push_decision: PushDecisionState,
) -> tuple[object, dict[str, object], object]:
    return _startup_quality_blocker_inputs_impl(
        repo_root=repo_root,
        review_state=review_state,
        push_decision=push_decision,
        deps=StartupQualityBlockerDeps(
            build_orphan_snapshot_projection=build_orphan_snapshot_projection,
            load_startup_quality_signals=load_startup_quality_signals,
            compact_startup_quality_signals=compact_startup_quality_signals,
            derive_startup_blocker=derive_startup_blocker,
        ),
    )


def _detect_reviewer_gate(
    repo_root: Path,
    governance: ProjectGovernance | None = None,
    review_state=None,
    review_status_dir: Path | None = None,
) -> ReviewerGateState:
    """Detect reviewer gate state from typed review-state only."""
    resolved_governance = governance or scan_repo_governance_safely(repo_root)
    gov_interaction_mode = _governance_interaction_mode(resolved_governance)
    typed_gate = _detect_reviewer_gate_from_review_state(
        review_state,
        governance_mode=gov_interaction_mode,
    )
    if typed_gate is None:
        typed_gate = _detect_reviewer_gate_from_typed_state(
            repo_root,
            governance=resolved_governance,
            review_status_dir=review_status_dir,
        )
    if typed_gate is not None:
        return typed_gate
    return _detect_reviewer_gate_without_typed_state(resolved_governance)


def _governance_interaction_mode(
    governance: ProjectGovernance | None,
) -> str:
    """Read operator_interaction_mode from governance BridgeConfig, or empty."""
    if governance is None:
        return ""
    return str(governance.bridge_config.operator_interaction_mode or "").strip()


def _detect_reviewer_gate_from_typed_state(
    repo_root: Path,
    *,
    governance: ProjectGovernance | None = None,
    review_status_dir: Path | None = None,
) -> ReviewerGateState | None:
    """Read reviewer gate from typed review_state.json when available."""
    state = load_current_review_state(
        repo_root,
        governance=governance,
        review_status_dir=review_status_dir,
        prefer_cached_projection=True,
        allow_live_refresh=True,
    )
    gov_mode = _governance_interaction_mode(governance)
    return _detect_reviewer_gate_from_review_state(state, governance_mode=gov_mode)


def _detect_reviewer_gate_from_review_state(
    state,
    governance_mode: str = "",
) -> ReviewerGateState | None:
    """Read reviewer gate from a preloaded typed review state."""
    if state is None:
        return None
    reviewer_runtime = state.reviewer_runtime
    current_session = state.current_session
    attention = state.attention
    assessment = state.recovery_assessment
    payload = state.to_dict() if hasattr(state, "to_dict") else {}
    assessment_payload = payload.get("recovery_assessment")
    assessment_mapping = (
        assessment_payload if isinstance(assessment_payload, dict) else {}
    )
    mode_projection = authority_mode_projection(
        AuthorityModeInputs(
            payload=payload if isinstance(payload, dict) else {},
            reviewer_gate={},
            reviewer_runtime=(
                payload.get("reviewer_runtime")
                if isinstance(payload.get("reviewer_runtime"), dict)
                else {}
            ),
            diagnosis=(
                assessment_mapping.get("diagnosis")
                if isinstance(assessment_mapping.get("diagnosis"), dict)
                else {}
            ),
            attention=(
                payload.get("attention")
                if isinstance(payload.get("attention"), dict)
                else {}
            ),
            doctor=(
                payload.get("doctor") if isinstance(payload.get("doctor"), dict) else {}
            ),
            governance_mode=governance_mode,
        )
    )
    effective_mode = mode_projection.effective_reviewer_mode
    review_accepted = reviewer_runtime.review_acceptance.review_accepted
    publish_clear = reviewer_runtime.publish_clear
    diagnosis_status = (
        str(assessment.diagnosis.status or "").strip() if assessment is not None else ""
    )
    action_id = (
        str(assessment.decision.action_id or "").strip()
        if assessment is not None
        else ""
    )
    recovery_command = (
        str(assessment.decision.command or "").strip() if assessment is not None else ""
    )
    interaction_mode = mode_projection.interaction_mode
    declared_active = mode_projection.declared_active
    effective_active = mode_projection.effective_active
    gate_mode = mode_projection.gate_mode
    attention_status = str(getattr(attention, "status", "") or "").strip()
    implementation_blocked = reviewer_runtime.implementation_blocked
    implementation_block_reason = reviewer_runtime.implementation_block_reason
    if declared_active and not effective_active:
        gate_mode = mode_projection.reviewer_mode or gate_mode
        if not implementation_blocked:
            implementation_blocked = True
            implementation_block_reason = (
                attention_status or reviewer_runtime.stale_reason or "review_loop_not_live"
            )
    if (
        declared_active
        and effective_active
        and not implementation_blocked
        and attention_status == "claude_ack_stale"
        and str(current_session.implementer_ack_state or "").strip() == "stale"
    ):
        implementation_blocked = True
        implementation_block_reason = attention_status
    if not declared_active and not effective_active:
        return ReviewerGateState(
            bridge_active=False,
            reviewer_mode=gate_mode,
            effective_reviewer_mode=effective_mode,
            review_accepted=True,
            required_checks_status="unknown",
            checkpoint_permitted=True,
            review_gate_allows_push=True,
            recovery_diagnosis_status=diagnosis_status,
            recovery_action_id=action_id,
            recovery_command=recovery_command,
            operator_interaction_mode=interaction_mode,
        )
    # Both effective_active and !effective_active dual-agent branches share
    # the same gate shape; only the not-declared-active case differs above.
    return ReviewerGateState(
        bridge_active=True,
        reviewer_mode=gate_mode,
        effective_reviewer_mode=effective_mode,
        review_accepted=review_accepted,
        required_checks_status="unknown",
        checkpoint_permitted=True,
        review_gate_allows_push=publish_clear,
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
        recovery_diagnosis_status=diagnosis_status,
        recovery_action_id=action_id,
        recovery_command=recovery_command,
        operator_interaction_mode=interaction_mode,
    )


def _detect_reviewer_gate_without_typed_state(
    governance: ProjectGovernance | None,
) -> ReviewerGateState:
    if governance is None:
        return ReviewerGateState(
            checkpoint_permitted=True,
            review_gate_allows_push=True,
        )
    bridge_active = bool(
        governance.bridge_config.bridge_active
        or str(governance.bridge_config.review_channel_path or "").strip()
        or str(governance.bridge_config.bridge_path or "").strip()
    )
    if not bridge_active:
        return ReviewerGateState(
            checkpoint_permitted=True,
            review_gate_allows_push=True,
        )
    return ReviewerGateState(
        bridge_active=True,
        reviewer_mode="unknown",
        effective_reviewer_mode="unknown",
        review_accepted=False,
        checkpoint_permitted=True,
        review_gate_allows_push=False,
        implementation_blocked=True,
        implementation_block_reason="typed_review_state_required",
    )


def _derive_advisory_action(
    governance: ProjectGovernance,
    gate: ReviewerGateState,
    *,
    ownership=None,
    coordination=None,
) -> tuple[str, str]:
    decision = _derive_advisory_decision(
        governance,
        gate,
        ownership=ownership,
        coordination=coordination,
    )
    return decision.action, decision.reason


def _load_startup_coordination_snapshot(
    *,
    repo_root: Path,
    governance: ProjectGovernance,
    review_state: "ReviewState | None",
    gate: ReviewerGateState,
    work_intake: WorkIntakePacket,
) -> CoordinationSnapshot | None:
    """Resolve coordination via the shared F1 loader; fall back for bare repos.

    Funnels startup-context, session-resume, and the control-plane read
    model through ``coordination_loader`` so every surface observes the
    same reducer output. The legacy fallback keeps this function non-
    None when no typed review state is available.
    """
    from .coordination_loader import load_coordination_snapshot

    snapshot = load_coordination_snapshot(
        repo_root=repo_root,
        sources={},
        governance=governance,
        review_state=review_state,
        reviewer_gate=gate,
        work_intake=work_intake,
    )
    if snapshot is not None:
        return snapshot
    from ..platform.coordination_snapshot import build_coordination_snapshot

    return build_coordination_snapshot(
        repo_root=repo_root,
        startup_context=SimpleNamespace(
            governance=governance,
            work_intake=work_intake,
        ),
        review_state=review_state,
    )


def _attach_startup_surface_identity(
    *,
    governance: ProjectGovernance,
    review_state: "ReviewState | None",
    push_decision: PushDecisionState,
) -> tuple[PushDecisionState, str, str]:
    snapshot_id = str(
        getattr(review_state, "snapshot_id", "") or ""
    ).strip() or build_surface_snapshot_id(
        reviewer_runtime=(
            getattr(review_state, "reviewer_runtime", None) if review_state else None
        ),
        commit_pipeline=(
            getattr(review_state, "commit_pipeline", None) if review_state else None
        ),
        push_decision=push_decision,
    )
    head_sha = str(
        getattr(
            getattr(governance, "push_enforcement", None), "current_head_commit", ""
        )
        or ""
    ).strip()
    zref = build_surface_zref(snapshot_id=snapshot_id, head_sha=head_sha)
    return replace(push_decision, snapshot_id=snapshot_id, zref=zref), snapshot_id, zref


def _governance_delivery_mode(governance: ProjectGovernance) -> str:
    return normalize_delivery_mode(
        getattr(getattr(governance, "bridge_config", None), "delivery_mode", "")
    )


def _derive_delivery_push_decision(
    governance: ProjectGovernance,
    gate: ReviewerGateState,
) -> PushDecisionState:
    """Derive push decision, skipping publication in non-push delivery modes."""
    delivery_mode = _governance_delivery_mode(governance)
    push = governance.push_enforcement
    if delivery_mode_requires_push(delivery_mode) and push is not None:
        return _derive_push_decision(
            push,
            review_gate_allows_push=gate.review_gate_allows_push,
            implementation_blocked=gate.implementation_blocked,
            implementation_block_reason=gate.implementation_block_reason,
        )
    return PushDecisionState(
        worktree_clean=bool(getattr(push, "worktree_clean", True)),
        review_gate_allows_push=bool(gate.review_gate_allows_push),
        has_remote_work_to_push=False,
        push_eligible_now=False,
        action="no_push_needed",
        reason=f"delivery_mode:{delivery_mode}",
        next_step_summary=(
            "This delivery mode does not require governed git push; continue "
            "with local, library, or embedded-governance workflow steps."
        ),
        rule_summary=(
            "Startup skipped push-decision derivation because the governed "
            f"delivery mode is `{delivery_mode}`, not git publication."
        ),
    )


def build_startup_context(
    *,
    repo_root: Path | None = None,
    governance: ProjectGovernance | None = None,
    review_state: "ReviewState | None" = None,
    review_status_dir: Path | None = None,
    caller_role: object = "",
) -> StartupContext:
    """Build the typed startup-context packet for the current repo state.

    Optional frozen governance/review-state inputs let composite renderers share
    one typed review tick across startup, control-plane, and session-resume
    surfaces. ``review_status_dir`` selects that frozen bundle when needed, and
    ``caller_role`` only affects reduced authority projection.
    """
    repo_root, governance = _resolve_startup_repo_and_governance(
        repo_root=repo_root,
        governance=governance,
    )
    review_state = _load_startup_review_state(
        repo_root,
        governance=governance,
        review_state=review_state,
        review_status_dir=review_status_dir,
    )
    gate = _detect_reviewer_gate(
        repo_root,
        governance=governance,
        review_state=review_state,
        review_status_dir=review_status_dir,
    )
    gate, runtime_truth = _startup_runtime_truth_and_gate(
        repo_root=repo_root,
        review_state=review_state,
        gate=gate,
    )
    push_decision = _derive_delivery_push_decision(governance, gate)
    ownership = build_work_intake_ownership_state(
        repo_root=repo_root,
        review_state=review_state,
    )
    coordination = build_work_intake_coordination_state(
        governance=governance,
        review_state=review_state,
        ownership=ownership,
        reviewer_gate=gate,
    )
    advisory = _derive_advisory_decision(
        governance,
        gate,
        ownership=ownership,
        coordination=coordination,
    )
    work_intake = build_work_intake_packet(
        repo_root=repo_root,
        governance=governance,
        advisory_action=advisory.action,
        advisory_reason=advisory.reason,
        state_inputs=WorkIntakeStateInputs(
            review_state=review_state,
            ownership=ownership,
            coordination=coordination,
            reviewer_gate=gate,
        ),
    )
    coordination_snapshot = _load_startup_coordination_snapshot(
        repo_root=repo_root,
        governance=governance,
        review_state=review_state,
        gate=gate,
        work_intake=work_intake,
    )
    orphan_snapshot, quality_signals, blocker = _startup_quality_blocker_inputs(
        repo_root=repo_root,
        review_state=review_state,
        push_decision=push_decision,
    )
    push_decision, snapshot_id, zref = _attach_startup_surface_identity(
        governance=governance,
        review_state=review_state,
        push_decision=push_decision,
    )
    observed_control_topology, implementation_permission = derive_startup_control_truth(
        review_state,
        reviewer_gate=gate,
    )
    recovery_authority = derive_recovery_authority(review_state)
    current_session = _startup_current_session(review_state)
    packet_intent_anchors = packet_intent_anchors_from_packets(
        review_state.packets if review_state is not None else (),
    )

    coordination_state_projection = extract_coordination_state_projection(review_state)

    (
        runtime_spine_closure,
        packet_carry_forward_debt,
        packet_continuity_index,
        continuity_attention,
    ) = compute_startup_continuity_signals(
        repo_root=repo_root,
        review_state=review_state,
    )
    bypass_lifecycles = _collect_active_bypass_lifecycles(
        repo_root=repo_root,
        role=caller_role,
    )

    ctx = _assemble_startup_context(
        StartupContextAssemblyInput(
            repo_root=repo_root,
            governance=governance,
            review_state=review_state,
            gate=gate,
            push_decision=push_decision,
            advisory=advisory,
            observed_control_topology=observed_control_topology,
            implementation_permission=implementation_permission,
            recovery_authority=recovery_authority,
            work_intake=work_intake,
            coordination_snapshot=coordination_snapshot,
            coordination_state_projection=coordination_state_projection,
            current_session=current_session,
            runtime_truth=runtime_truth,
            packet_intent_anchors=packet_intent_anchors,
            quality_signals=quality_signals,
            orphan_snapshot=orphan_snapshot,
            blocker=blocker,
            runtime_spine_closure=runtime_spine_closure,
            packet_continuity_index=packet_continuity_index,
            packet_carry_forward_debt=packet_carry_forward_debt,
            continuity_attention=continuity_attention,
            bypass_lifecycles=bypass_lifecycles,
            snapshot_id=snapshot_id,
            zref=zref,
        )
    )
    return _attach_authority_snapshot(ctx, caller_role=caller_role)
def _attach_authority_snapshot(
    ctx: StartupContext,
    *,
    caller_role: object,
) -> StartupContext:
    authority_snapshot = project_authority_snapshot(
        ctx.to_dict(),
        caller_role=caller_role,
    )
    return replace(ctx, authority_snapshot=authority_snapshot)


def _startup_current_session(review_state: "ReviewState | None"):
    if review_state is None:
        return None
    current_session = review_state.current_session
    if not is_missing_instruction(current_session.current_instruction):
        return current_session
    return replace(
        current_session,
        current_instruction_revision="",
        implementer_ack_state="missing",
    )


def _resolve_startup_repo_and_governance(
    *,
    repo_root: Path | None,
    governance: ProjectGovernance | None,
) -> tuple[Path, ProjectGovernance]:
    if repo_root is None:
        from ..config import get_repo_root

        repo_root = get_repo_root()
    if governance is None:
        from ..governance.draft import scan_repo_governance

        governance = scan_repo_governance(repo_root)
    return repo_root, governance


def blocks_new_implementation(ctx: StartupContext) -> bool:
    """Return whether the typed startup receipt blocks another edit slice.

    Implementation is blocked when the reviewer runtime is not live, but
    publication may still proceed when the reviewer acceptance is valid.
    """
    if ctx.reviewer_gate.implementation_blocked:
        return not ctx.reviewer_gate.review_gate_allows_push
    governance = ctx.governance
    if governance is None:
        return False
    push = governance.push_enforcement
    if push is None:
        return False
    return bool(push.checkpoint_required or not push.safe_to_continue_editing)
