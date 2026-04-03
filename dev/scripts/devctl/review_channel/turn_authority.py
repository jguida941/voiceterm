"""Shared typed reviewer turn-authority helpers for bridge-backed consumers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from ..runtime.review_state_parser import review_state_from_payload
from ..runtime.role_profile import TandemRole
from .attention import derive_bridge_attention
from .current_session_projection import (
    bridge_implementer_state_hash,
    build_bridge_current_session,
)
from .handoff import BridgeLiveness, BridgeSnapshot
from .launch_truth import (
    classify_launch_truth,
    effective_reviewer_mode as _compute_effective_reviewer_mode,
)
from .peer_liveness import (
    AttentionStatus,
    REVIEWER_WAIT_STATE_MARKERS,
    reviewer_mode_is_active,
)
from .peer_recovery import STALE_PEER_RECOVERY


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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_reviewer_turn_authority(
    *,
    snapshot: BridgeSnapshot,
    bridge_liveness: BridgeLiveness,
    typed_review_state: Mapping[str, object] | None = None,
) -> ReviewerTurnAuthority:
    """Build the shared reviewer-turn projection from typed review state."""
    review_state = (
        review_state_from_payload(typed_review_state or {}) if typed_review_state else None
    )
    fallback_session = build_bridge_current_session(snapshot, asdict(bridge_liveness))
    current_session = review_state.current_session if review_state is not None else fallback_session
    bridge = review_state.bridge if review_state is not None else None
    reviewer_runtime = review_state.reviewer_runtime if review_state is not None else None
    attention = review_state.attention if review_state is not None else None

    # Detect whether typed state carries complete authority.  A populated
    # bridge.launch_truth means the state came from refresh_status_snapshot()
    # — the same pipeline status/doctor/startup use.  When launch_truth is
    # empty the typed state is partial (scaffolding only), and the authority
    # fields (effective_reviewer_mode, attention, launch_truth) are defaulted,
    # not computed.  In that case, derive them from bridge_liveness via the
    # same shared classifiers that status/doctor use.
    _typed_authority_complete = (
        review_state is not None
        and bridge is not None
        and bool(bridge.launch_truth)
    )
    _needs_fallback = not _typed_authority_complete
    _liveness_dict = asdict(bridge_liveness) if _needs_fallback else {}
    _has_lifecycle = (
        "publisher_running" in _liveness_dict
        or "reviewer_supervisor_running" in _liveness_dict
    )
    if _has_lifecycle:
        _fallback_attention = derive_bridge_attention(_liveness_dict)
        _fallback_launch_truth = str(
            _liveness_dict.get("launch_truth")
            or classify_launch_truth(_liveness_dict).value
        )
        _fallback_effective_mode = _compute_effective_reviewer_mode(_liveness_dict)
    else:
        _fallback_attention = None
        _fallback_launch_truth = ""
        _fallback_effective_mode = ""

    reviewer_mode = (
        reviewer_runtime.reviewer_mode
        if _typed_authority_complete and reviewer_runtime is not None and reviewer_runtime.reviewer_mode
        else bridge.reviewer_mode
        if _typed_authority_complete and bridge is not None and bridge.reviewer_mode
        else bridge_liveness.reviewer_mode
    )
    effective_reviewer_mode = (
        reviewer_runtime.effective_reviewer_mode
        if _typed_authority_complete and reviewer_runtime is not None and reviewer_runtime.effective_reviewer_mode
        else bridge.effective_reviewer_mode
        if _typed_authority_complete and bridge is not None and bridge.effective_reviewer_mode
        else _fallback_effective_mode
        if _fallback_effective_mode
        else reviewer_mode
    )
    reviewer_freshness = (
        reviewer_runtime.reviewer_freshness
        if reviewer_runtime is not None and reviewer_runtime.reviewer_freshness
        else bridge.reviewer_freshness
        if bridge is not None and bridge.reviewer_freshness
        else bridge_liveness.reviewer_freshness
    )
    attention_status = (
        attention.status
        if _typed_authority_complete and attention is not None and attention.status
        else reviewer_runtime.stale_reason
        if _typed_authority_complete and reviewer_runtime is not None and reviewer_runtime.stale_reason
        else str(_fallback_attention.get("status", ""))
        if _fallback_attention is not None
        else ""
    )
    recovery_action_allowed = (
        reviewer_runtime.recovery_action_allowed
        if _typed_authority_complete and reviewer_runtime is not None and reviewer_runtime.recovery_action_allowed
        else _recommended_command(attention_status)
    )
    implementation_blocked = bool(
        reviewer_runtime.implementation_blocked
        if _typed_authority_complete and reviewer_runtime is not None
        else False
    )
    implementation_block_reason = (
        reviewer_runtime.implementation_block_reason
        if _typed_authority_complete and reviewer_runtime is not None and reviewer_runtime.implementation_block_reason
        else attention_status
        if implementation_blocked and attention_status
        else ""
    )
    reviewed_hash_current = (
        bridge.reviewed_hash_current
        if bridge is not None
        else bridge_liveness.reviewed_hash_current
    )
    review_needed = (
        bridge.review_needed if bridge is not None else _review_needed(reviewed_hash_current)
    )
    claude_ack_current = (
        current_session.implementer_ack_state == "current"
        if current_session.implementer_ack_state
        else bool(bridge_liveness.claude_ack_current)
    )

    current_impl_hash = current_session.implementer_state_hash or bridge_implementer_state_hash(snapshot)
    accepted_impl_hash = (
        reviewer_runtime.review_acceptance.reviewer_accepted_implementer_state_hash
        if reviewer_runtime is not None
        and hasattr(reviewer_runtime.review_acceptance, "reviewer_accepted_implementer_state_hash")
        else ""
    )
    next_turn_required, next_turn_role, next_turn_reason = _derive_next_turn_state(
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

    return ReviewerTurnAuthority(
        snapshot_id=review_state.snapshot_id if review_state is not None else "",
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        reviewer_freshness=reviewer_freshness,
        launch_truth=(
            bridge.launch_truth
            if bridge is not None and bridge.launch_truth
            else _fallback_launch_truth
        ),
        attention_status=attention_status,
        recovery_action_allowed=recovery_action_allowed,
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
        current_instruction=current_session.current_instruction,
        current_instruction_revision=current_session.current_instruction_revision,
        claude_ack_revision=current_session.implementer_ack_revision,
        claude_ack_current=claude_ack_current,
        implementer_state_hash=(
            current_session.implementer_state_hash or bridge_implementer_state_hash(snapshot)
        ),
        reviewer_accepted_implementer_state_hash=(
            reviewer_runtime.review_acceptance.reviewer_accepted_implementer_state_hash
            if reviewer_runtime is not None
            and hasattr(reviewer_runtime.review_acceptance, "reviewer_accepted_implementer_state_hash")
            else ""
        ),
        reviewed_hash_current=reviewed_hash_current,
        review_needed=review_needed,
        next_turn_required=next_turn_required,
        next_turn_role=next_turn_role,
        next_turn_reason=next_turn_reason,
    )


def _review_needed(reviewed_hash_current: bool | None) -> bool | None:
    if reviewed_hash_current is None:
        return None
    return not reviewed_hash_current


def _derive_next_turn_state(
    *,
    snapshot: BridgeSnapshot,
    bridge_liveness: BridgeLiveness,
    reviewer_mode: str,
    effective_reviewer_mode: str,
    attention_status: str,
    implementation_blocked: bool,
    implementation_block_reason: str,
    current_instruction: str,
    claude_status: str,
    claude_ack: str,
    claude_ack_current: bool,
    reviewed_hash_current: bool | None,
    review_needed: bool | None,
    implementer_state_hash: str = "",
    reviewer_accepted_implementer_state_hash: str = "",
) -> tuple[bool, str, str]:
    if not reviewer_mode_is_active(reviewer_mode):
        return False, "", "inactive"
    if not reviewer_mode_is_active(effective_reviewer_mode):
        return True, TandemRole.REVIEWER.value, _runtime_downgrade_reason(
            attention_status,
            implementation_block_reason,
        )
    if not current_instruction.strip():
        return True, TandemRole.REVIEWER.value, "reviewer_instruction_missing"
    if not _has_content(claude_status, bridge_liveness.claude_status_present):
        return True, TandemRole.IMPLEMENTER.value, "implementer_status_missing"
    if not _has_content(claude_ack, bridge_liveness.claude_ack_present):
        return True, TandemRole.IMPLEMENTER.value, "implementer_ack_missing"
    if not claude_ack_current:
        return True, TandemRole.IMPLEMENTER.value, "implementer_ack_stale"

    blocked_attention = _blocked_attention_turn(attention_status)
    if blocked_attention is not None:
        return blocked_attention

    if implementation_blocked and implementation_block_reason:
        return (
            True,
            _attention_turn_role(implementation_block_reason),
            implementation_block_reason,
        )
    if attention_status in {
        AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED.value,
        AttentionStatus.REVIEWED_HASH_STALE.value,
    }:
        return True, TandemRole.REVIEWER.value, AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED.value
    if review_needed is True or reviewed_hash_current is False:
        return True, TandemRole.REVIEWER.value, AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED.value
    if (
        reviewer_accepted_implementer_state_hash
        and implementer_state_hash
        and implementer_state_hash != reviewer_accepted_implementer_state_hash
        and claude_ack_current
    ):
        return True, TandemRole.REVIEWER.value, "implementer_state_changed"
    if _reviewer_wait_state(snapshot=snapshot, current_instruction=current_instruction):
        return True, TandemRole.REVIEWER.value, "reviewer_wait_state"
    return False, "", "up_to_date"


def _blocked_attention_turn(attention_status: str) -> tuple[bool, str, str] | None:
    recovery = STALE_PEER_RECOVERY.get(attention_status)
    if not isinstance(recovery, dict):
        return None
    if str(recovery.get("guard_behavior") or "") not in {"block_launch", "block_loop"}:
        return None
    return True, _attention_turn_role(attention_status), attention_status


def _runtime_downgrade_reason(attention_status: str, block_reason: str) -> str:
    return (
        attention_status
        or block_reason
        or AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value
    )


def _attention_turn_role(attention_status: str) -> str:
    recovery = STALE_PEER_RECOVERY.get(attention_status)
    owner = str(recovery.get("owner") or "") if isinstance(recovery, dict) else ""
    if owner == "claude":
        return TandemRole.IMPLEMENTER.value
    return TandemRole.REVIEWER.value


def _recommended_command(attention_status: str) -> str:
    recovery = STALE_PEER_RECOVERY.get(attention_status)
    if not isinstance(recovery, dict):
        return ""
    return str(recovery.get("recommended_command") or "").strip()


def _reviewer_wait_state(*, snapshot: BridgeSnapshot, current_instruction: str) -> bool:
    haystack = "\n".join(
        [
            current_instruction,
            snapshot.sections.get("Poll Status", "").strip(),
        ]
    ).lower()
    return any(marker in haystack for marker in REVIEWER_WAIT_STATE_MARKERS)


def _has_content(value: str, present: bool) -> bool:
    return bool(value.strip()) or present
