"""Typed startup-context surface for AI agent sessions."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from .recovery_authority import derive_recovery_authority
from .reviewer_runtime_models import (
    has_active_remote_control_attachment,
)

if TYPE_CHECKING:
    from .review_state_models import ReviewState

from .authority_snapshot import AuthoritySnapshot, project_authority_snapshot
from .conductor_capability import authority_reviewer_mode, normalize_reviewer_mode
from .control_topology import derive_startup_control_truth
from .governance_scan import scan_repo_governance_safely
from .key_surfaces import startup_key_surfaces
from .operator_context import is_resolved, resolve_operator_interaction_mode
from .packet_intent_anchor import (
    packet_intent_anchors_from_packets,
    plan_iteration_session_from_anchors,
)
from .project_governance import ProjectGovernance
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
        prefer_cached_projection=False,
    )
    gov_mode = _governance_interaction_mode(governance)
    return _detect_reviewer_gate_from_review_state(state, governance_mode=gov_mode)


def _interaction_mode_from_reviewer_mode(
    effective_mode: str,
    governance_mode: str = "",
    remote_control_attachment: RemoteControlAttachmentState | None = None,
) -> str:
    """Derive operator interaction mode; fails closed to 'unresolved'.

    Per rev_pkt_3021 #3: ``governance_mode == "remote_control"`` alone is
    NOT sufficient to promote operator location. Governance can DECLARE
    intent, but typed attachment evidence is required to confirm it. The
    prior shape (governance precedence without attachment proof) reopened
    the cross-surface divergence operator_context.py and session_posture.py
    already fail closed on, so startup-context now matches their semantics.

    Other resolved governance values (local_direct, dashboard_remote, etc.)
    are still trusted directly because they are not the contested promotion
    path — only remote_control requires attachment evidence.
    """
    gov = (governance_mode or "").strip()
    resolved = resolve_operator_interaction_mode(gov)
    attachment_active = has_active_remote_control_attachment(remote_control_attachment)
    resolved_value = resolved.value
    if (
        is_resolved(resolved_value)
        and resolved_value not in {"local_terminal", "remote_control"}
    ):
        return resolved_value
    if resolved_value == "remote_control" and attachment_active:
        return "remote_control"
    if attachment_active:
        return "remote_control"
    if gov == "local_terminal":
        return "local_terminal"
    normalized = normalize_reviewer_mode(effective_mode) if effective_mode else ""
    if normalized == "active_dual_agent":
        return "dual_agent"
    if normalized == "single_agent":
        return "single_agent"
    return "unresolved"


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
    mode = reviewer_runtime.reviewer_mode
    effective_mode = str(reviewer_runtime.effective_reviewer_mode or "").strip() or mode
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
    attachment = reviewer_runtime.remote_control_attachment
    recovery_command = (
        str(assessment.decision.command or "").strip() if assessment is not None else ""
    )
    interaction_mode = _interaction_mode_from_reviewer_mode(
        effective_mode,
        governance_mode=governance_mode,
        remote_control_attachment=attachment,
    )
    posture = reviewer_runtime.session_posture
    posture_has_runtime_truth = bool(
        posture.actors
        or posture.interaction_mode != "unresolved"
        or posture.reviewer_mode != "single_agent"
    )
    if posture_has_runtime_truth:
        mode = posture.reviewer_mode or mode
        effective_mode = posture.effective_reviewer_mode or effective_mode
    if posture.interaction_mode != "unresolved":
        interaction_mode = posture.interaction_mode
    declared_active = normalize_reviewer_mode(mode) == "active_dual_agent"
    effective_active = normalize_reviewer_mode(effective_mode) == "active_dual_agent"
    gate_mode = authority_reviewer_mode(mode, effective_mode)
    attention_status = str(getattr(attention, "status", "") or "").strip()
    implementation_blocked = reviewer_runtime.implementation_blocked
    implementation_block_reason = reviewer_runtime.implementation_block_reason
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


def build_startup_context(
    *,
    repo_root: Path | None = None,
    governance: ProjectGovernance | None = None,
    review_state: "ReviewState | None" = None,
    review_status_dir: Path | None = None,
    caller_role: object = "",
) -> StartupContext:
    """Build the typed startup-context packet for the current repo state.

    ``governance`` and ``review_state`` are optional frozen inputs that let
    callers (in particular the F1 coordination-parity proof in
    ``test_startup_context`` and any composite renderer that wants a single
    tick to cover all three governance surfaces) lock one typed review-state
    snapshot across ``build_startup_context``, ``build_control_plane_read_
    model``, and ``session_resume_support.build_from_sources``. When both are
    omitted, the function still performs a fresh governance scan and
    bridge-refreshed review-state load so the standalone command behavior is
    unchanged. ``review_status_dir`` threads the caller-selected review bundle
    through that single review-state load so startup-context stays on the same
    frozen bundle as the dashboard and session-resume surfaces when a custom
    status root is in play. ``caller_role`` only affects reduced advisory
    authority projection, letting read-only composite surfaces reuse the same
    startup tick without exposing mutating next commands.
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
    push_decision = _derive_push_decision(
        governance.push_enforcement,
        review_gate_allows_push=gate.review_gate_allows_push,
        implementation_blocked=gate.implementation_blocked,
        implementation_block_reason=gate.implementation_block_reason,
    )
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
    return bool(push.checkpoint_required or not push.safe_to_continue_editing)
