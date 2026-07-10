from dev.scripts.devctl.runtime.reviewer_gate_logic import (
    ReviewerRuntimeBlockInputs,
    reviewer_loop_block_state,
    reviewer_runtime_block_state,
)


def test_reviewer_loop_block_state_ignores_missing_instruction() -> None:
    blocked, reason = reviewer_loop_block_state(
        ReviewerRuntimeBlockInputs(
            reviewer_mode="active_dual_agent",
            effective_reviewer_mode="active_dual_agent",
            implementer_ack_current=False,
            attention_status="claude_ack_stale",
            current_instruction="",
            implementer_status="",
            implementer_ack="pending",
            implementer_ack_state="missing",
        )
    )

    assert blocked is False
    assert reason == ""


def test_reviewer_runtime_block_state_ignores_missing_instruction() -> None:
    blocked, reason = reviewer_runtime_block_state(
        ReviewerRuntimeBlockInputs(
            reviewer_mode="active_dual_agent",
            effective_reviewer_mode="active_dual_agent",
            implementer_ack_current=False,
            attention_status="claude_ack_stale",
            current_instruction="(missing)",
            implementer_status="",
            implementer_ack="pending",
            implementer_ack_state="missing",
        )
    )

    assert blocked is False
    assert reason == ""


def test_reviewer_runtime_block_state_still_blocks_live_instruction_without_ack() -> None:
    blocked, reason = reviewer_runtime_block_state(
        ReviewerRuntimeBlockInputs(
            reviewer_mode="active_dual_agent",
            effective_reviewer_mode="active_dual_agent",
            implementer_ack_current=False,
            attention_status="claude_ack_stale",
            current_instruction="- implement the current slice",
            implementer_status="working",
            implementer_ack="acknowledged",
            implementer_ack_state="stale",
        )
    )

    assert blocked is True
    assert reason == "claude_ack_stale"
