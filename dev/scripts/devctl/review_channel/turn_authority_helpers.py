"""Shared helpers for reviewer turn-authority field resolution and classification."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from ..runtime.review_state_models import (
    RecoveryAssessmentState,
    ReviewBridgeState,
    ReviewCurrentSessionState,
)
from ..runtime.role_profile import TandemRole
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
from .recovery_assessment import (
    build_recovery_assessment,
    recovery_assessment_to_attention_payload,
)


# ── Attention / turn-role helpers ────────────────────────────────


def is_attention_launch_blocked(attention_status: str) -> bool:
    """Return True when the peer-recovery contract blocks launch for this status."""
    recovery = STALE_PEER_RECOVERY.get(attention_status)
    if not isinstance(recovery, dict):
        return False
    return str(recovery.get("guard_behavior") or "") == "block_launch"


def attention_block_detail(attention_status: str) -> tuple[str, str]:
    """Return (summary, recommended_action) for a blocked attention status."""
    recovery = STALE_PEER_RECOVERY.get(attention_status)
    if not isinstance(recovery, dict):
        return attention_status, "inspect bridge state"
    return (
        str(recovery.get("summary") or attention_status),
        str(recovery.get("recovery") or "inspect bridge state"),
    )


def blocked_attention_turn(attention_status: str) -> tuple[bool, str, str] | None:
    recovery = STALE_PEER_RECOVERY.get(attention_status)
    if not isinstance(recovery, dict):
        return None
    if str(recovery.get("guard_behavior") or "") not in {"block_launch", "block_loop"}:
        return None
    return True, attention_turn_role(attention_status), attention_status


def runtime_downgrade_reason(attention_status: str, block_reason: str) -> str:
    return (
        attention_status
        or block_reason
        or AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value
    )


def attention_turn_role(attention_status: str) -> str:
    recovery = STALE_PEER_RECOVERY.get(attention_status)
    owner = str(recovery.get("owner") or "") if isinstance(recovery, dict) else ""
    if owner == "claude":
        return TandemRole.IMPLEMENTER.value
    return TandemRole.REVIEWER.value


def recommended_command(attention_status: str) -> str:
    recovery = STALE_PEER_RECOVERY.get(attention_status)
    if not isinstance(recovery, dict):
        return ""
    return str(recovery.get("recommended_command") or "").strip()


def reviewer_wait_state(*, snapshot: BridgeSnapshot, current_instruction: str) -> bool:
    haystack = "\n".join(
        [
            current_instruction,
            snapshot.sections.get("Poll Status", "").strip(),
        ]
    ).lower()
    return any(marker in haystack for marker in REVIEWER_WAIT_STATE_MARKERS)


def has_content(value: str, present: bool) -> bool:
    return bool(value.strip()) or present


# ── Claude ACK resolution ────────────────────────────────────────


def resolve_claude_ack_current(
    *,
    current_session: ReviewCurrentSessionState,
    bridge: ReviewBridgeState | None,
    bridge_liveness: BridgeLiveness,
) -> bool:
    ack_state = str(current_session.implementer_ack_state or "").strip().lower()
    if ack_state == "current":
        return True
    if ack_state in {"stale", "missing"}:
        return False

    if bridge is not None and hasattr(bridge, "claude_ack_current"):
        return bool(bridge.claude_ack_current)
    return bool(bridge_liveness.claude_ack_current)


# ── Fallback authority / liveness dict ───────────────────────────


_LIFECYCLE_OVERLAY_KEYS = (
    "publisher_running",
    "reviewer_supervisor_running",
    "codex_conductor_active",
    "claude_conductor_active",
    "review_needed",
    "review_accepted",
    "publish_clear",
    "publisher_stop_reason",
    "reviewer_supervisor_stop_reason",
)


def fallback_authority_fields(
    bridge_liveness: BridgeLiveness,
    typed_review_state: Mapping[str, object] | None,
) -> tuple[dict[str, object] | None, str, str, RecoveryAssessmentState | None]:
    liveness_dict = build_fallback_liveness_dict(bridge_liveness, typed_review_state)
    if (
        "publisher_running" not in liveness_dict
        and "reviewer_supervisor_running" not in liveness_dict
    ):
        return None, "", "", None

    assessment = build_recovery_assessment(bridge_liveness=liveness_dict)
    return (
        recovery_assessment_to_attention_payload(assessment),
        str(liveness_dict.get("launch_truth") or classify_launch_truth(liveness_dict).value),
        _compute_effective_reviewer_mode(liveness_dict),
        assessment,
    )


def build_fallback_liveness_dict(
    bridge_liveness: BridgeLiveness,
    typed_review_state: Mapping[str, object] | None,
) -> dict[str, object]:
    """Merge raw lifecycle fields from a partial typed payload over BridgeLiveness."""
    base = asdict(bridge_liveness)
    if typed_review_state is None:
        return base

    bl = typed_review_state.get("bridge_liveness")
    if isinstance(bl, Mapping):
        for key in _LIFECYCLE_OVERLAY_KEYS:
            if key in bl:
                base[key] = bl[key]

    br = typed_review_state.get("bridge")
    if isinstance(br, Mapping):
        for key in _LIFECYCLE_OVERLAY_KEYS:
            if key not in base and key in br:
                base[key] = br[key]

    return base


# ── Next-turn derivation ─────────────────────────────────────────


def derive_next_turn_state(
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
        return True, TandemRole.REVIEWER.value, runtime_downgrade_reason(
            attention_status,
            implementation_block_reason,
        )

    if not current_instruction.strip():
        return True, TandemRole.REVIEWER.value, "reviewer_instruction_missing"

    if not has_content(claude_status, bridge_liveness.claude_status_present):
        return True, TandemRole.IMPLEMENTER.value, "implementer_status_missing"

    if not has_content(claude_ack, bridge_liveness.claude_ack_present):
        return True, TandemRole.IMPLEMENTER.value, "implementer_ack_missing"

    if not claude_ack_current:
        return True, TandemRole.IMPLEMENTER.value, "implementer_ack_stale"

    blocked = blocked_attention_turn(attention_status)
    if blocked is not None:
        return blocked

    if implementation_blocked and implementation_block_reason:
        return (
            True,
            attention_turn_role(implementation_block_reason),
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

    if reviewer_wait_state(snapshot=snapshot, current_instruction=current_instruction):
        return True, TandemRole.REVIEWER.value, "reviewer_wait_state"

    return False, "", "up_to_date"
