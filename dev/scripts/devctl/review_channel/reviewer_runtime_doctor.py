"""Doctor/status projection helpers for the typed reviewer-runtime contract."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.reviewer_runtime_models import ReviewerRuntimeContract
from .peer_liveness import reviewer_mode_is_active
from .peer_recovery import STALE_PEER_RECOVERY


def build_reviewer_doctor_surface(
    *,
    contract: ReviewerRuntimeContract,
    attention: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Project a read-only doctor surface from reviewer-runtime authority."""
    attention_summary = str((attention or {}).get("summary") or "").strip()
    recommended_command = str(
        (attention or {}).get("recommended_command")
        or contract.recovery_action_allowed
        or ""
    ).strip()
    status = _doctor_status(contract)
    summary = attention_summary or _doctor_summary(contract, status=status)
    surface: dict[str, object] = {}
    surface["status"] = status
    surface["summary"] = summary
    surface["reviewer_mode"] = contract.reviewer_mode
    surface["effective_reviewer_mode"] = contract.effective_reviewer_mode
    surface["reviewer_freshness"] = contract.reviewer_freshness
    surface["stale_reason"] = contract.stale_reason
    surface["last_codex_poll_utc"] = contract.last_poll.last_codex_poll_utc
    surface["last_codex_poll_age_seconds"] = contract.last_poll.last_codex_poll_age_seconds
    surface["rollover_id"] = contract.rollover.rollover_id
    surface["rollover_ack_pending"] = contract.rollover.ack_pending
    surface["rollover_trigger"] = contract.rollover.trigger
    surface["session_pid"] = contract.session_owner.session_pid
    surface["terminal_window_id"] = contract.session_owner.terminal_window_id
    surface["script_path"] = contract.session_owner.script_path
    surface["recovery_action_allowed"] = contract.recovery_action_allowed
    surface["recommended_command"] = recommended_command
    surface["review_accepted"] = contract.review_acceptance.review_accepted
    surface["current_verdict"] = contract.review_acceptance.current_verdict
    surface["open_findings"] = contract.review_acceptance.open_findings
    surface["publish_clear"] = contract.publish_clear
    return surface


def _doctor_status(contract: ReviewerRuntimeContract) -> str:
    if contract.publish_clear:
        return "healthy"
    if contract.stale_reason:
        return contract.stale_reason
    if contract.rollover.ack_pending:
        return "rollover_ack_pending"
    if not contract.review_acceptance.review_accepted:
        return "review_pending"
    if reviewer_mode_is_active(contract.reviewer_mode):
        return "not_publish_clear"
    return "healthy"


def _doctor_summary(
    contract: ReviewerRuntimeContract,
    *,
    status: str,
) -> str:
    if status == "healthy":
        return "Reviewer runtime is green and publish-clear."
    if status == "review_pending":
        return "Reviewer verdict/findings are not accepted yet."
    if status == "rollover_ack_pending":
        return "Rollover is still awaiting fresh conductor ACK lines."
    recovery = STALE_PEER_RECOVERY.get(status)
    if isinstance(recovery, dict):
        return str(recovery.get("summary") or "").strip()
    return "Reviewer runtime is not publish-clear."
