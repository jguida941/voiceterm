"""Assembly helpers for materializing StartupContext from its components.

Extracted from startup_context.py to keep that module under the shape budget.
The build_startup_context entrypoint computes all inputs and delegates the
final dataclass construction here so the orchestration body stays focused on
the resolution/computation phase.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from .key_surfaces import startup_key_surfaces
from .lifetime_bypass_mode import (
    DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
    BypassAuthorityScope,
    BypassLifecycle,
    active_bypass_lifecycles,
)
from .packet_intent_anchor import plan_iteration_session_from_anchors
from .project_governance import ProjectGovernance
from .remote_control_attachment_models import RemoteControlAttachmentState
from .startup_connectivity_registry import startup_connectivity_registry
from .startup_context_models import StartupContext
from .startup_context_projections import build_contract_ownership_map
from .startup_continuity import (
    startup_continuity_attention,
    startup_packet_carry_forward_debt,
    startup_packet_continuity_index,
    startup_runtime_spine_closure,
)

if TYPE_CHECKING:
    from pathlib import Path
    from .review_state_models import ReviewState


def _review_state_remote_control_attachment(
    review_state: "ReviewState | None",
) -> RemoteControlAttachmentState | None:
    if review_state is None:
        return None
    return review_state.reviewer_runtime.remote_control_attachment


def _startup_key_surfaces(governance: ProjectGovernance | None) -> tuple[str, ...]:
    return startup_key_surfaces(governance)


class StartupContextAssemblyInput(NamedTuple):
    repo_root: "Path"
    governance: ProjectGovernance
    review_state: "ReviewState | None"
    gate: object
    push_decision: object
    advisory: object
    observed_control_topology: object
    implementation_permission: object
    recovery_authority: object
    work_intake: object
    coordination_snapshot: object
    coordination_state_projection: dict[str, object]
    current_session: object
    runtime_truth: object
    packet_intent_anchors: object
    quality_signals: object
    orphan_snapshot: object
    blocker: object
    runtime_spine_closure: object
    packet_continuity_index: object
    packet_carry_forward_debt: object
    continuity_attention: object
    bypass_lifecycles: object
    snapshot_id: object
    zref: object


def _assemble_startup_context(spec: StartupContextAssemblyInput) -> StartupContext:
    """Materialize the StartupContext dataclass from its computed components."""
    review_state = spec.review_state
    return StartupContext(
        governance=spec.governance,
        reviewer_gate=spec.gate,
        push_decision=spec.push_decision,
        advisory_action=spec.advisory.action,
        advisory_reason=spec.advisory.reason,
        observed_control_topology=spec.observed_control_topology,
        implementation_permission=spec.implementation_permission,
        recovery_authority=spec.recovery_authority,
        rule_summary=spec.advisory.rule_summary,
        match_evidence=spec.advisory.match_evidence,
        rejected_rule_traces=spec.advisory.rejected_rule_traces,
        product_thesis=spec.governance.product_thesis if spec.governance else "",
        work_intake=spec.work_intake,
        coordination=spec.coordination_snapshot,
        coordination_state_projection=spec.coordination_state_projection,
        collaboration=(review_state.collaboration if review_state is not None else None),
        reviewer_runtime=(
            review_state.reviewer_runtime if review_state is not None else None
        ),
        session_posture=(
            review_state.reviewer_runtime.session_posture
            if review_state is not None
            else None
        ),
        runtime_truth=spec.runtime_truth,
        remote_control_attachment=_review_state_remote_control_attachment(review_state),
        attention=(review_state.attention if review_state is not None else None),
        current_session=spec.current_session,
        packet_inbox=(review_state.packet_inbox if review_state is not None else None),
        packet_intent_anchors=spec.packet_intent_anchors,
        plan_iteration_session=plan_iteration_session_from_anchors(
            spec.packet_intent_anchors
        ),
        quality_signals=spec.quality_signals,
        orphan_snapshot=spec.orphan_snapshot,
        blocker=spec.blocker,
        contract_ownership_map=build_contract_ownership_map(),
        connectivity_registry=startup_connectivity_registry(spec.repo_root),
        runtime_spine_closure=spec.runtime_spine_closure,
        packet_continuity_index=spec.packet_continuity_index,
        packet_carry_forward_debt=spec.packet_carry_forward_debt,
        continuity_attention=spec.continuity_attention,
        bypass_lifecycles=tuple(spec.bypass_lifecycles or ()),
        key_surfaces=_startup_key_surfaces(spec.governance),
        snapshot_id=spec.snapshot_id,
        zref=spec.zref,
    )


def extract_coordination_state_projection(
    review_state: "ReviewState | None",
) -> dict[str, object]:
    """Pull the typed CoordinationStateProjection out of review_state.

    Per Codex rev_pkt_2313/2326/2337: surfaces the 4-field split for recovery
    and push consumers alongside the legacy observed_control_topology field.
    """
    if review_state is None:
        return {}
    cs = getattr(review_state, "coordination_state", None)
    if isinstance(cs, dict):
        return dict(cs)
    return {}


def _collect_active_bypass_lifecycles(
    *,
    repo_root: "Path",
    role: object = "",
) -> tuple[BypassLifecycle, ...]:
    """Collect active typed bypass lifecycles for startup-context consumers."""
    return active_bypass_lifecycles(
        store_path=repo_root / DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
        target_role=str(role or "").strip(),
        required_scope=BypassAuthorityScope.EDIT_ONLY,
    )


def compute_startup_continuity_signals(
    *,
    repo_root: "Path",
    review_state: "ReviewState | None",
) -> tuple[object, object, object, object]:
    """Derive the four continuity signals consumed by build_startup_context.

    Returns (runtime_spine_closure, packet_carry_forward_debt,
    packet_continuity_index, continuity_attention) in a single call so the
    orchestration body stays compact.
    """
    runtime_spine_closure = startup_runtime_spine_closure(repo_root)
    packet_carry_forward_debt = startup_packet_carry_forward_debt(
        repo_root=repo_root,
        review_state=review_state,
    )
    packet_continuity_index = startup_packet_continuity_index(review_state)
    continuity_attention = startup_continuity_attention(
        runtime_spine_closure=runtime_spine_closure,
        packet_carry_forward_debt=packet_carry_forward_debt,
        packet_continuity_index=packet_continuity_index,
    )
    return (
        runtime_spine_closure,
        packet_carry_forward_debt,
        packet_continuity_index,
        continuity_attention,
    )


__all__ = [
    "StartupContextAssemblyInput",
    "_assemble_startup_context",
    "_collect_active_bypass_lifecycles",
    "compute_startup_continuity_signals",
    "extract_coordination_state_projection",
]
