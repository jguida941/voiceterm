from __future__ import annotations

from dev.scripts.devctl.runtime.review_state_parser_rows import (
    canonicalize_current_instruction_state,
    current_session_state_from_payload,
)


def test_canonicalize_current_instruction_state_clears_missing_placeholder_revision() -> None:
    instruction, revision = canonicalize_current_instruction_state(
        "(missing)",
        "rev-123",
    )

    assert instruction == "(missing)"
    assert revision == ""


def test_current_session_state_from_payload_clears_missing_placeholder_revision() -> None:
    state = current_session_state_from_payload(
        current_session={
            "current_instruction": "(missing)",
            "current_instruction_revision": "rev-123",
            "implementer_ack_state": "missing",
        },
        bridge={},
    )

    assert state.current_instruction == "(missing)"
    assert state.current_instruction_revision == ""
