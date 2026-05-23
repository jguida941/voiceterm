"""Shared typed reviewer turn-authority helpers for bridge-backed consumers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from ..runtime.review_state_models import ReviewBridgeState
from ..runtime.review_state_parser import review_state_from_payload
from ..runtime.role_profile import TandemRole
from .active_packet_authority import current_active_packet_for_agent
from .current_session_projection import (
    bridge_implementer_state_hash,
    build_bridge_current_session,
)
from .handoff import BridgeLiveness, BridgeSnapshot
from .peer_liveness import AttentionStatus
from .turn_authority_helpers import (
    attention_block_detail,
    derive_next_turn_state,
    fallback_authority_fields,
    is_attention_launch_blocked,
    resolve_claude_ack_current,
)
from .turn_authority_resolution import (
    resolve_implementation_block,
    resolve_modes,
    resolve_recovery_action,
)
from .turn_authority_resolution import review_needed as derive_review_needed


@dataclass(frozen=True, slots=True)
class ReviewerTurnAuthority:
    """Shared typed reviewer-turn projection for bridge/status consumers."""

    snapshot_id: str
    reviewer_mode: str
    effective_reviewer_mode: str
    reviewer_freshness: str
    launch_truth: str
    attention_status: str
    recovery_action_allowed: str
    implementation_blocked: bool
    implementation_block_reason: str
    current_instruction: str
    current_instruction_revision: str
    claude_ack_revision: str
    claude_ack_current: bool
    implementer_state_hash: str
    reviewer_accepted_implementer_state_hash: str
    reviewed_hash_current: bool | None
    review_needed: bool | None
    next_turn_required: bool
    next_turn_role: str
    next_turn_reason: str
    diagnosis_status: str = ""
    decision_action_id: str = ""
    decision_command: str = ""
    decision_execution_owner: str = ""
    decision_requires_approval: bool = False
    decision_can_auto_fix: bool = False
    zref: str = ""
    # Per Codex rev_pkt_2326/2361/2367/2368: typed coordination_state fields
    # surfaced alongside legacy reviewer_mode so bridge-poll, dashboard,
    # claude-loop, and startup-context can render the SAME typed answer
    # instead of a single_agent / multi_agent_active contradiction.
    coordination_topology: str = ""
    authority_mode: str = ""
    recovery_eligibility: str = ""
    canonical_active_packet_for_claude: str = ""
    canonical_active_packet_for_codex: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_reviewer_turn_authority(
    *,
    snapshot: BridgeSnapshot,
    bridge_liveness: BridgeLiveness,
    typed_review_state: Mapping[str, object] | None = None,
) -> ReviewerTurnAuthority:
    """Build the shared reviewer-turn projection from typed review state."""
    if not isinstance(snapshot, BridgeSnapshot):
        raise TypeError("build_reviewer_turn_authority requires BridgeSnapshot")
    if not isinstance(bridge_liveness, BridgeLiveness):
        raise TypeError("build_reviewer_turn_authority requires BridgeLiveness")
    review_state = (
        review_state_from_payload(typed_review_state or {})
        if typed_review_state
        else None
    )
    fallback_session = build_bridge_current_session(snapshot, asdict(bridge_liveness))
    current_session = (
        review_state.current_session if review_state is not None else fallback_session
    )
    bridge = review_state.bridge if review_state is not None else None
    reviewer_runtime = (
        review_state.reviewer_runtime if review_state is not None else None
    )
    attention = review_state.attention if review_state is not None else None
    recovery_assessment = (
        review_state.recovery_assessment if review_state is not None else None
    )
    # Per rev_pkt_2326/2361/2367/2368: typed coordination_state is the
    # primary authority for topology / authority_mode / recovery_eligibility.
    # Bridge-poll legacy reviewer_mode remains as a compatibility surface,
    # but the COMMAND fields below get gated on typed recovery_eligibility.
    coordination_state = (
        review_state.coordination_state if review_state is not None else {}
    )
    coordination_topology = str(
        (coordination_state or {}).get("coordination_topology") or ""
    ).strip()
    authority_mode = str(
        (coordination_state or {}).get("authority_mode") or ""
    ).strip()
    recovery_eligibility = str(
        (coordination_state or {}).get("recovery_eligibility") or ""
    ).strip()
    canonical_active_packet_for_claude = current_active_packet_for_agent(
        typed_review_state or {}, "claude"
    )
    canonical_active_packet_for_codex = current_active_packet_for_agent(
        typed_review_state or {}, "codex"
    )

    typed_authority_complete = bool(
        review_state is not None and bridge is not None and bridge.launch_truth
    )
    (
        fallback_attention,
        fallback_launch_truth,
        fallback_effective_mode,
        fallback_assessment,
    ) = (
        fallback_authority_fields(bridge_liveness, typed_review_state)
        if not typed_authority_complete
        else (None, "", "", None)
    )

    reviewer_mode, effective_reviewer_mode, reviewer_freshness = resolve_modes(
        bridge_liveness,
        bridge,
        reviewer_runtime,
        typed_authority_complete,
        fallback_effective_mode,
    )
    attention_status = _resolve_attention_status(
        bridge_liveness,
        bridge,
        reviewer_runtime,
        attention,
        recovery_assessment,
        typed_authority_complete,
        fallback_attention,
        fallback_assessment,
    )
    recovery_action_allowed = resolve_recovery_action(
        reviewer_runtime,
        recovery_assessment,
        typed_authority_complete,
        fallback_assessment,
        attention_status,
        recovery_eligibility=recovery_eligibility,
    )
    implementation_blocked, implementation_block_reason = resolve_implementation_block(
        reviewer_runtime,
        typed_authority_complete,
        attention_status,
    )

    reviewed_hash_current = (
        bridge.reviewed_hash_current
        if bridge is not None
        else bridge_liveness.reviewed_hash_current
    )
    review_needed = (
        bridge.review_needed
        if bridge is not None
        else derive_review_needed(reviewed_hash_current)
    )
    claude_ack_current = resolve_claude_ack_current(
        current_session=current_session,
        bridge=bridge,
        bridge_liveness=bridge_liveness,
    )
    current_impl_hash = (
        current_session.implementer_state_hash
        or bridge_implementer_state_hash(snapshot)
    )
    accepted_impl_hash = (
        reviewer_runtime.review_acceptance.reviewer_accepted_implementer_state_hash
        if reviewer_runtime is not None
        and hasattr(
            reviewer_runtime.review_acceptance,
            "reviewer_accepted_implementer_state_hash",
        )
        else ""
    )

    next_turn_required, next_turn_role, next_turn_reason = derive_next_turn_state(
        snapshot=snapshot,
        bridge_liveness=bridge_liveness,
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        attention_status=attention_status,
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
        current_instruction=current_session.current_instruction,
        claude_status=current_session.implementer_status,
        claude_ack=current_session.implementer_ack,
        claude_ack_current=claude_ack_current,
        reviewed_hash_current=reviewed_hash_current,
        review_needed=review_needed,
        implementer_state_hash=current_impl_hash,
        reviewer_accepted_implementer_state_hash=accepted_impl_hash,
    )

    return _build_authority_result(
        review_state=review_state,
        bridge=bridge,
        bridge_liveness=bridge_liveness,
        recovery_assessment=recovery_assessment,
        fallback_assessment=fallback_assessment,
        fallback_launch_truth=fallback_launch_truth,
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        reviewer_freshness=reviewer_freshness,
        attention_status=attention_status,
        recovery_action_allowed=recovery_action_allowed,
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
        current_session=current_session,
        claude_ack_current=claude_ack_current,
        current_impl_hash=current_impl_hash,
        accepted_impl_hash=accepted_impl_hash,
        reviewed_hash_current=reviewed_hash_current,
        review_needed=review_needed,
        next_turn_required=next_turn_required,
        next_turn_role=next_turn_role,
        next_turn_reason=next_turn_reason,
        coordination_topology=coordination_topology,
        authority_mode=authority_mode,
        recovery_eligibility=recovery_eligibility,
        canonical_active_packet_for_claude=canonical_active_packet_for_claude,
        canonical_active_packet_for_codex=canonical_active_packet_for_codex,
    )


def _resolve_attention_status(
    bridge_liveness,
    bridge,
    reviewer_runtime,
    attention,
    recovery_assessment,
    typed_complete,
    fallback_attention,
    fallback_assessment,
):
    if (
        typed_complete
        and recovery_assessment is not None
        and recovery_assessment.diagnosis.status
    ):
        return recovery_assessment.diagnosis.status

    if typed_complete and attention is not None and attention.status:
        return attention.status

    if (
        typed_complete
        and reviewer_runtime is not None
        and reviewer_runtime.stale_reason
    ):
        return reviewer_runtime.stale_reason

    if fallback_assessment is not None and fallback_assessment.diagnosis.status:
        return fallback_assessment.diagnosis.status

    if fallback_attention is not None:
        return str(fallback_attention.get("status", ""))

    return ""


def _build_authority_result(
    *,
    review_state,
    bridge,
    bridge_liveness,
    recovery_assessment,
    fallback_assessment,
    fallback_launch_truth,
    reviewer_mode,
    effective_reviewer_mode,
    reviewer_freshness,
    attention_status,
    recovery_action_allowed,
    implementation_blocked,
    implementation_block_reason,
    current_session,
    claude_ack_current,
    current_impl_hash,
    accepted_impl_hash,
    reviewed_hash_current,
    review_needed,
    next_turn_required,
    next_turn_role,
    next_turn_reason,
    coordination_topology: str = "",
    authority_mode: str = "",
    recovery_eligibility: str = "",
    canonical_active_packet_for_claude: str = "",
    canonical_active_packet_for_codex: str = "",
):
    return ReviewerTurnAuthority(
        snapshot_id=review_state.snapshot_id if review_state is not None else "",
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        reviewer_freshness=reviewer_freshness,
        launch_truth=(
            bridge.launch_truth
            if bridge is not None and bridge.launch_truth
            else fallback_launch_truth
        ),
        attention_status=attention_status,
        recovery_action_allowed=recovery_action_allowed,
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
        current_instruction=current_session.current_instruction,
        current_instruction_revision=current_session.current_instruction_revision,
        claude_ack_revision=current_session.implementer_ack_revision,
        claude_ack_current=claude_ack_current,
        implementer_state_hash=current_impl_hash,
        reviewer_accepted_implementer_state_hash=accepted_impl_hash,
        reviewed_hash_current=reviewed_hash_current,
        review_needed=review_needed,
        next_turn_required=next_turn_required,
        next_turn_role=next_turn_role,
        next_turn_reason=next_turn_reason,
        diagnosis_status=attention_status,
        decision_action_id=(
            recovery_assessment.decision.action_id
            if recovery_assessment is not None
            else (
                fallback_assessment.decision.action_id
                if fallback_assessment is not None
                else ""
            )
        ),
        decision_command=recovery_action_allowed,
        decision_execution_owner=(
            recovery_assessment.decision.execution_owner
            if recovery_assessment is not None
            else (
                fallback_assessment.decision.execution_owner
                if fallback_assessment is not None
                else ""
            )
        ),
        decision_requires_approval=(
            recovery_assessment.decision.requires_approval
            if recovery_assessment is not None
            else (
                fallback_assessment.decision.requires_approval
                if fallback_assessment is not None
                else False
            )
        ),
        decision_can_auto_fix=(
            recovery_assessment.decision.can_auto_fix
            if recovery_assessment is not None
            else (
                fallback_assessment.decision.can_auto_fix
                if fallback_assessment is not None
                else False
            )
        ),
        zref=review_state.zref if review_state is not None else "",
        coordination_topology=coordination_topology,
        authority_mode=authority_mode,
        recovery_eligibility=recovery_eligibility,
        canonical_active_packet_for_claude=canonical_active_packet_for_claude,
        canonical_active_packet_for_codex=canonical_active_packet_for_codex,
    )
