"""Trigger-gate helpers for reviewer follow-up packet decisions.

Extracted from reviewer_follow_packet_guard.py to keep both modules
under the code-shape soft limit. Contains the typed-report, authority,
and legacy trigger condition checks.
"""

from __future__ import annotations

from .turn_authority import ReviewerTurnAuthority


def typed_report_trigger_available(report: dict[str, object]) -> bool:
    """True when the report carries typed authority_snapshot for trigger gating."""
    authority_snap = report.get("authority_snapshot")
    return isinstance(authority_snap, dict) and bool(authority_snap.get("reviewer_mode"))


def typed_report_trigger_met(report: dict[str, object]) -> bool:
    """Typed-report gate: reviewer mode is active, resync not required, and either review needed or relaunch required."""
    from .peer_liveness import reviewer_mode_is_active

    authority_snap = report.get("authority_snapshot")
    if not isinstance(authority_snap, dict):
        return False
    if authority_snap.get("resync_required"):
        return False
    reviewer_mode = str(authority_snap.get("reviewer_mode") or "")
    if not reviewer_mode_is_active(reviewer_mode):
        return False
    attention_status = str(authority_snap.get("attention_status") or "").strip()
    # Relaunch-required always triggers regardless of review_needed
    if attention_status == "review_loop_relaunch_required":
        return True
    # All other triggers require review_needed
    if not bool(report.get("review_needed")):
        return False
    coordination = report.get("coordination")
    if isinstance(coordination, dict):
        launch_truth = str(coordination.get("launch_truth") or "").strip()
        if launch_truth in {
            "detached_runtime_only",
            "automation_only",
            "implementer_without_reviewer",
            "hybrid_claude_only",
        }:
            return True
    return False


def authority_trigger_met(authority: ReviewerTurnAuthority) -> bool:
    """Check trigger condition using the shared turn-authority contract."""
    if not authority.next_turn_required:
        return False
    return authority.next_turn_role == "reviewer"


def legacy_trigger_met(
    bridge_liveness: dict[str, object],
    attention: dict[str, object],
) -> bool:
    """Fallback trigger condition for callers without a turn authority."""
    from .peer_liveness import reviewer_mode_is_active

    reviewer_mode = str(
        bridge_liveness.get("effective_reviewer_mode")
        or bridge_liveness.get("reviewer_mode")
        or ""
    )
    if not reviewer_mode_is_active(reviewer_mode):
        return False
    attention_status = str(attention.get("status") or "").strip()
    if attention_status == "review_loop_relaunch_required":
        return True
    launch_truth = str(bridge_liveness.get("launch_truth") or "").strip()
    if launch_truth in {
        "detached_runtime_only",
        "automation_only",
        "implementer_without_reviewer",
        "hybrid_claude_only",
    }:
        return True
    return bool(bridge_liveness.get("poll_status_automation_only"))
