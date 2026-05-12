from __future__ import annotations

from dev.scripts.devctl.commands.development.final_response_gate import (
    FinalResponseGateResult,
)
from dev.scripts.devctl.runtime.reviewer_response_shape import (
    reviewer_response_shape_for_gate,
)


def test_response_shape_blocks_status_table_when_final_gate_denies() -> None:
    shape = reviewer_response_shape_for_gate(
        FinalResponseGateResult(
            allow_final_response=False,
            action="continue_to_goal",
            next_required_command="python3 dev/scripts/devctl.py agent-loop --format json",
            blocking_packet_id="rev_pkt_3744",
            continuation_state="must_continue",
            continuation_goal="rev_pkt_3744",
        ),
        actor_id="claude",
        role="reviewer",
        session_activity_log_ref="session_activity_log:claude:session-1",
        proposed_response_text=(
            "| Status | Detail |\n"
            "| --- | --- |\n"
            "| holding position | waiting for codex |\n"
            "Final summary complete."
        ),
    )

    assert shape.status == "blocked"
    assert shape.response_mode == "continue_to_goal"
    assert shape.status_prose_allowed is False
    assert shape.completion_prose_allowed is False
    assert shape.operator_status_source == "session_activity_log:claude:session-1"
    assert shape.proposed_response_text_observed is True
    assert shape.proposed_response_text_source == "direct_argument"
    assert "status_marker:markdown_table" in shape.violations
    assert "status_marker:holding position" in shape.violations
    assert "completion_marker:complete" in shape.violations


def test_response_shape_blocks_terminal_response_when_final_gate_denies_without_candidate() -> None:
    shape = reviewer_response_shape_for_gate(
        FinalResponseGateResult(
            allow_final_response=False,
            action="run_next_command",
            next_required_command="python3 dev/scripts/devctl.py develop next --actor codex --format md",
            continuation_state="must_continue",
            continuation_goal="typed controller goal",
        ),
        actor_id="codex",
        role="reviewer",
    )

    assert shape.status == "blocked"
    assert shape.final_response_allowed is False
    assert shape.status_prose_allowed is False
    assert shape.completion_prose_allowed is False
    assert shape.proposed_response_text_observed is False
    assert shape.violations == ()


def test_response_shape_allows_receipt_summary_when_final_gate_allows() -> None:
    shape = reviewer_response_shape_for_gate(
        FinalResponseGateResult(
            allow_final_response=True,
            action="allow_final_response",
            continuation_state="may_stop",
        ),
        actor_id="codex",
        role="implementer",
        session_activity_log_ref="session_activity_log:codex:session-2",
        proposed_response_text=(
            "Completed MP377 slice; receipts are in the session activity log."
        ),
    )

    assert shape.status == "allowed"
    assert shape.response_mode == "completion_summary_from_receipts"
    assert shape.status_prose_allowed is True
    assert shape.completion_prose_allowed is True
    assert shape.operator_status_source == "session_activity_log:codex:session-2"
    assert shape.proposed_response_text_observed is True
    assert shape.violations == ()
