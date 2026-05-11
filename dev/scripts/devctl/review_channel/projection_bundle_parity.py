"""Phase 0 parity-field promotion for canonical review-state persistence."""

from __future__ import annotations

from collections.abc import Mapping


def apply_phase_zero_parity_projection(
    review_state_payload: dict[str, object],
) -> None:
    """Promote the Phase 0 parity fields onto canonical persisted review-state."""
    authority_snapshot = _mapping(review_state_payload.get("authority_snapshot"))
    reviewer_runtime = _mapping(review_state_payload.get("reviewer_runtime"))
    current_session = _mapping(review_state_payload.get("current_session"))
    coordination = _mapping(review_state_payload.get("coordination"))
    bridge = _mapping(review_state_payload.get("bridge"))
    last_poll = _mapping(reviewer_runtime.get("last_poll"))

    effective_reviewer_mode = str(
        reviewer_runtime.get("effective_reviewer_mode")
        or authority_snapshot.get("effective_reviewer_mode")
        or reviewer_runtime.get("reviewer_mode")
        or ""
    ).strip()
    reviewer_mode = str(
        authority_snapshot.get("gate_mode")
        or authority_snapshot.get("reviewer_mode")
        or reviewer_runtime.get("reviewer_mode")
        or effective_reviewer_mode
        or ""
    ).strip()
    if reviewer_mode:
        review_state_payload["reviewer_mode"] = reviewer_mode
    if effective_reviewer_mode:
        review_state_payload["effective_reviewer_mode"] = effective_reviewer_mode

    reviewer_freshness = str(reviewer_runtime.get("reviewer_freshness") or "").strip()
    if reviewer_freshness:
        review_state_payload["reviewer_freshness"] = reviewer_freshness

    review_state_payload["current_instruction_revision"] = str(
        authority_snapshot.get("current_instruction_revision")
        or current_session.get("current_instruction_revision")
        or ""
    ).strip()
    review_state_payload["implementer_ack_state"] = str(
        authority_snapshot.get("implementer_ack_state")
        or current_session.get("implementer_ack_state")
        or ""
    ).strip()

    last_codex_poll = str(
        last_poll.get("last_codex_poll_utc")
        or bridge.get("last_codex_poll_utc")
        or ""
    ).strip()
    if last_codex_poll:
        review_state_payload["last_codex_poll"] = last_codex_poll
        review_state_payload["last_codex_poll_utc"] = last_codex_poll

    if coordination:
        review_state_payload["safe_to_fanout"] = bool(
            coordination.get("safe_to_fanout", False)
        )
        review_state_payload["resync_required"] = bool(
            coordination.get("resync_required", False)
        )
        ownership_status = str(coordination.get("ownership_status") or "").strip()
        if ownership_status:
            review_state_payload["ownership_status"] = ownership_status

    next_command = str(authority_snapshot.get("next_command") or "").strip()
    if next_command:
        review_state_payload["next_command"] = next_command


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
