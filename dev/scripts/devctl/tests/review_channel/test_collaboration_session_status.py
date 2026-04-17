from __future__ import annotations

from dev.scripts.devctl.review_channel.collaboration_session_status import (
    _collaboration_status,
    _implementer_gate_status,
    _implementer_gate_summary,
)
from dev.scripts.devctl.runtime.review_state_models import ReviewCurrentSessionState


def _current_session(*, instruction: str) -> ReviewCurrentSessionState:
    return ReviewCurrentSessionState(
        current_instruction=instruction,
        current_instruction_revision="rev-123",
        implementer_status="",
        implementer_ack="",
        implementer_ack_revision="",
        implementer_ack_state="missing",
        open_findings="",
        last_reviewed_scope="",
    )


def test_implementer_gate_ignores_missing_instruction_placeholder() -> None:
    current_session = _current_session(instruction="(missing)")

    assert (
        _implementer_gate_status(
            current_session,
            reviewer_mode="active_dual_agent",
        )
        == "not_required"
    )
    assert (
        _implementer_gate_summary(
            current_session,
            reviewer_mode="active_dual_agent",
        )
        == "No active implementer instruction is present."
    )


def test_collaboration_status_ignores_missing_instruction_placeholder() -> None:
    current_session = _current_session(instruction="(missing)")

    assert (
        _collaboration_status(
            participants=(),
            delegated_work=(),
            current_session=current_session,
        )
        == "inactive"
    )
