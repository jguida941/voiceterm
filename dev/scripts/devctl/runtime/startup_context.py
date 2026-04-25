"""Typed startup-context surface for AI agent sessions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from ..platform.coordination_snapshot_models import CoordinationSnapshot
from .finding_contracts import RejectedRuleTraceRecord, RuleMatchEvidenceRecord
from .recovery_authority import RecoveryAuthorityState, derive_recovery_authority
from .review_state_models import (
    PacketInboxState,
    ReviewAttentionState,
    ReviewCurrentSessionState,
)
from .reviewer_runtime_models import (
    RemoteControlAttachmentState,
    ReviewerRuntimeContract,
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
from .project_governance import ProjectGovernance
from .review_state_locator import load_current_review_state
from .startup_advisory_decision import (
    derive_advisory_decision as _derive_advisory_decision,
)
from .startup_blocker_decision import BlockerSnapshot, derive_startup_blocker
from .startup_connectivity_registry import startup_connectivity_registry
from .startup_context_projections import (
    bounded_contract_ownership_map,
    build_contract_ownership_map,
    startup_coordination_dict,
    startup_orphan_snapshot_dict,
)
from .startup_governance_projection import startup_governance_dict
from .startup_packet_inbox import startup_packet_inbox_dict
from .startup_push_decision import PushDecisionState
from .startup_push_decision import derive_push_decision as _derive_push_decision
from .startup_review_state import (
    load_startup_review_state as _load_startup_review_state,
)
from .startup_signals import load_startup_quality_signals
from .surface_snapshot import build_surface_snapshot_id, build_surface_zref
from .work_intake import (
    WorkIntakePacket,
    WorkIntakeStateInputs,
    build_work_intake_packet,
)
from .work_intake_coordination import build_work_intake_coordination_state
from .work_intake_ownership import build_work_intake_ownership_state
from .worktree_orphan_snapshot import OrphanSnapshot
from .worktree_orphan_snapshot_projection import build_orphan_snapshot_projection


@dataclass(frozen=True, slots=True)
class ReviewerGateState:
    """Current reviewer/ready-gate inputs for safe checkpoint/push decisions."""

    bridge_active: bool = False
    reviewer_mode: str = "single_agent"
    effective_reviewer_mode: str = "single_agent"
    review_accepted: bool = False
    required_checks_status: str = "unknown"
    checkpoint_permitted: bool = True
    review_gate_allows_push: bool = False
    implementation_blocked: bool = False
    implementation_block_reason: str = ""
    recovery_diagnosis_status: str = ""
    recovery_action_id: str = ""
    recovery_command: str = ""
    operator_interaction_mode: str = "unresolved"


@dataclass(frozen=True, slots=True)
class StartupContext:
    """Typed packet for AI agent session startup."""

    schema_version: int = 1
    contract_id: str = "StartupContext"
    governance: ProjectGovernance | None = None
    reviewer_gate: ReviewerGateState = field(default_factory=ReviewerGateState)
    push_decision: PushDecisionState = field(default_factory=PushDecisionState)
    advisory_action: str = "continue_editing"
    advisory_reason: str = ""
    observed_control_topology: str = "no_live_agents"
    implementation_permission: str = "blocked"
    recovery_authority: RecoveryAuthorityState = field(
        default_factory=RecoveryAuthorityState
    )
    rule_summary: str = ""
    match_evidence: tuple[RuleMatchEvidenceRecord, ...] = ()
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...] = ()
    product_thesis: str = ""
    work_intake: WorkIntakePacket | None = None
    coordination: CoordinationSnapshot | None = None
    authority_snapshot: AuthoritySnapshot | None = None
    reviewer_runtime: ReviewerRuntimeContract | None = None
    remote_control_attachment: RemoteControlAttachmentState | None = None
    attention: ReviewAttentionState | None = None
    current_session: ReviewCurrentSessionState | None = None
    packet_inbox: PacketInboxState | None = None
    quality_signals: dict[str, object] = field(default_factory=dict)
    orphan_snapshot: OrphanSnapshot | None = None
    blocker: BlockerSnapshot = field(default_factory=BlockerSnapshot)
    contract_ownership_map: dict[str, dict[str, object]] = field(default_factory=dict)
    connectivity_registry: dict[str, object] = field(default_factory=dict)
    key_surfaces: tuple[str, ...] = ()
    snapshot_id: str = ""
    zref: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        d["schema_version"] = self.schema_version
        d["contract_id"] = self.contract_id
        d["action"] = self.advisory_action
        d["reason"] = self.advisory_reason
        d["advisory_action"] = self.advisory_action
        d["advisory_reason"] = self.advisory_reason
        d["interaction_mode"] = self.reviewer_gate.operator_interaction_mode
        d["observed_control_topology"] = self.observed_control_topology
        d["implementation_permission"] = self.implementation_permission
        d["recovery_action"] = self.recovery_authority.recovery_action
        d["recovery_basis"] = self.recovery_authority.recovery_basis
        d["recovery_scope"] = self.recovery_authority.recovery_scope
        d["recovery_authority"] = self.recovery_authority.to_dict()
        d["rule_summary"] = self.rule_summary
        d["match_evidence"] = [evidence.to_dict() for evidence in self.match_evidence]
        d["rejected_rule_traces"] = [
            trace.to_dict() for trace in self.rejected_rule_traces
        ]
        d["reviewer_gate"] = asdict(self.reviewer_gate)
        d["push_decision"] = self.push_decision.to_dict()
        d["quality_signals"] = dict(self.quality_signals)
        d["blocker"] = self.blocker.to_dict()
        d["contract_ownership_map"] = bounded_contract_ownership_map(
            self.contract_ownership_map
        )
        d["connectivity_registry"] = dict(self.connectivity_registry)
        d["key_surfaces"] = list(self.key_surfaces)
        d["snapshot_id"] = self.snapshot_id
        d["zref"] = self.zref
        if self.product_thesis:
            d["product_thesis"] = self.product_thesis
        if self.governance is not None:
            d["governance"] = startup_governance_dict(self.governance)
        if self.work_intake is not None:
            d["work_intake"] = self.work_intake.to_dict()
        if self.coordination is not None:
            d["coordination"] = startup_coordination_dict(self.coordination)
        if self.authority_snapshot is not None:
            d["authority_snapshot"] = self.authority_snapshot.to_dict()
        if self.reviewer_runtime is not None:
            d["reviewer_runtime"] = asdict(self.reviewer_runtime)
        if self.remote_control_attachment is not None:
            d["remote_control_attachment"] = asdict(self.remote_control_attachment)
        if self.attention is not None:
            d["attention"] = asdict(self.attention)
        if self.current_session is not None:
            d["current_session"] = asdict(self.current_session)
        if self.packet_inbox is not None:
            d["packet_inbox"] = startup_packet_inbox_dict(self.packet_inbox)
        if self.orphan_snapshot is not None:
            d["orphan_snapshot"] = startup_orphan_snapshot_dict(self.orphan_snapshot)
        return d


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


def _review_state_remote_control_attachment(
    review_state: "ReviewState | None",
) -> RemoteControlAttachmentState | None:
    if review_state is None:
        return None
    return review_state.reviewer_runtime.remote_control_attachment


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
    """Derive operator interaction mode; fails closed to 'unresolved'."""
    gov = (governance_mode or "").strip()
    resolved = resolve_operator_interaction_mode(gov)
    if is_resolved(resolved.value) and resolved.value != "local_terminal":
        return resolved.value
    # An active remote-control attachment overrides the local_terminal governance
    # default so operators on phone/remote sessions resolve to remote_control
    # without needing a repo-policy flip. (rev_pkt_0448)
    if has_active_remote_control_attachment(remote_control_attachment):
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


def _startup_key_surfaces(governance: ProjectGovernance | None) -> tuple[str, ...]:
    return startup_key_surfaces(governance)


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
    if repo_root is None:
        from ..config import get_repo_root

        repo_root = get_repo_root()

    if governance is None:
        from ..governance.draft import scan_repo_governance

        governance = scan_repo_governance(repo_root)
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
    orphan_snapshot = build_orphan_snapshot_projection(
        repo_root=repo_root,
        review_state=review_state,
        scan_trigger="startup_context",
    )
    quality_signals = load_startup_quality_signals(repo_root)
    blocker = derive_startup_blocker(
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

    ctx = StartupContext(
        governance=governance,
        reviewer_gate=gate,
        push_decision=push_decision,
        advisory_action=advisory.action,
        advisory_reason=advisory.reason,
        observed_control_topology=observed_control_topology,
        implementation_permission=implementation_permission,
        recovery_authority=recovery_authority,
        rule_summary=advisory.rule_summary,
        match_evidence=advisory.match_evidence,
        rejected_rule_traces=advisory.rejected_rule_traces,
        product_thesis=governance.product_thesis if governance else "",
        work_intake=work_intake,
        coordination=coordination_snapshot,
        reviewer_runtime=(
            review_state.reviewer_runtime if review_state is not None else None
        ),
        remote_control_attachment=_review_state_remote_control_attachment(review_state),
        attention=(review_state.attention if review_state is not None else None),
        current_session=(
            review_state.current_session if review_state is not None else None
        ),
        packet_inbox=(review_state.packet_inbox if review_state is not None else None),
        quality_signals=quality_signals,
        orphan_snapshot=orphan_snapshot,
        blocker=blocker,
        contract_ownership_map=build_contract_ownership_map(),
        connectivity_registry=startup_connectivity_registry(repo_root),
        key_surfaces=_startup_key_surfaces(governance),
        snapshot_id=snapshot_id,
        zref=zref,
    )
    snapshot_payload = ctx.to_dict()
    authority_snapshot = project_authority_snapshot(
        snapshot_payload,
        caller_role=caller_role,
    )
    return replace(ctx, authority_snapshot=authority_snapshot)


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
