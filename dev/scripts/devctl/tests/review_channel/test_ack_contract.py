"""Focused regressions for semantic ACK parsing and typed authority."""

from __future__ import annotations

from dev.scripts.devctl.commands.review_channel._bridge_poll import (
    build_bridge_poll_result,
)
from dev.scripts.devctl.review_channel.bridge_projection_state import (
    build_bridge_projection_state,
)
from dev.scripts.devctl.review_channel.bridge_validation import (
    validate_live_bridge_contract,
)
from dev.scripts.devctl.review_channel.current_session_projection import (
    build_bridge_current_session,
)
from dev.scripts.devctl.review_channel.handoff import extract_bridge_snapshot


def _bridge_text(*, claude_ack: str) -> str:
    return "\n".join(
        [
            "# Review Bridge",
            "",
            "## Start-Of-Conversation Rules",
            "",
            "Codex is the reviewer. Claude is the coder.",
            "",
            "- Last Codex poll: `2026-03-29T23:20:00Z`",
            "- Last Codex poll (Local America/New_York): `2026-03-29 19:20:00 EDT`",
            "- Reviewer mode: `active_dual_agent`",
            f"- Last non-audit worktree hash: `{'a' * 64}`",
            "- Current instruction revision: `56bcd5d01510`",
            "",
            "## Protocol",
            "",
            "- Keep this file current-state only.",
            "",
            "## Poll Status",
            "",
            "- active reviewer loop",
            "",
            "## Current Verdict",
            "",
            "- reviewer checkpoint pending",
            "",
            "## Open Findings",
            "",
            "- keep the slice bounded",
            "",
            "## Claude Status",
            "",
            "- editing review-channel authority helpers",
            "",
            "## Claude Questions",
            "",
            "- none",
            "",
            "## Claude Ack",
            "",
            claude_ack,
            "",
            "## Current Instruction For Claude",
            "",
            "- Implement the typed authority slice.",
            "",
            "## Last Reviewed Scope",
            "",
            "- dev/scripts/devctl/review_channel",
            "",
        ]
    )


def test_build_bridge_current_session_accepts_semantic_ack_phrase() -> None:
    snapshot = extract_bridge_snapshot(
        _bridge_text(claude_ack="- Acknowledged instruction revision `56bcd5d01510`")
    )

    current_session = build_bridge_current_session(snapshot, {})

    assert current_session.implementer_ack_revision == "56bcd5d01510"
    assert current_session.implementer_ack_state == "current"


def test_validate_live_bridge_contract_accepts_semantic_ack_phrase() -> None:
    snapshot = extract_bridge_snapshot(
        _bridge_text(claude_ack="- Acknowledged instruction revision `56bcd5d01510`")
    )

    errors = validate_live_bridge_contract(snapshot)

    assert not any("Claude Ack" in error for error in errors)


def test_build_bridge_projection_state_prefers_typed_current_session_sections() -> None:
    projection_state = build_bridge_projection_state(
        bridge_text=_bridge_text(claude_ack="- acknowledged; instruction-rev: `deadbeef1234`"),
        bridge_liveness={"current_instruction_revision": "56bcd5d01510"},
        current_session={
            "current_instruction": "- Typed instruction wins.",
            "current_instruction_revision": "56bcd5d01510",
            "implementer_status": "- Typed status wins.",
            "implementer_ack": "- Acknowledged instruction revision `56bcd5d01510`",
            "implementer_ack_revision": "56bcd5d01510",
            "open_findings": "- Typed findings win.",
            "last_reviewed_scope": "- typed/scope.py",
        },
        reviewer_runtime={
            "review_acceptance": {
                "current_verdict": "- Typed verdict wins.",
                "open_findings": "- Typed findings win.",
            }
        },
        bridge_state={"current_instruction_revision": "56bcd5d01510"},
    )

    assert projection_state.sections["Current Verdict"] == "- Typed verdict wins."
    assert projection_state.sections["Open Findings"] == "- Typed findings win."
    assert projection_state.sections["Claude Status"] == "- Typed status wins."
    assert (
        projection_state.sections["Claude Ack"]
        == "- Acknowledged instruction revision `56bcd5d01510`"
    )
    assert (
        projection_state.sections["Current Instruction For Claude"]
        == "- Typed instruction wins."
    )
    assert projection_state.sections["Last Reviewed Scope"] == "- typed/scope.py"
    assert projection_state.metadata["current_instruction_revision"] == "56bcd5d01510"


def test_build_bridge_poll_result_prefers_typed_current_session_authority() -> None:
    result = build_bridge_poll_result(
        _bridge_text(claude_ack="- acknowledged; instruction-rev: `deadbeef1234`"),
        typed_review_state={
            "current_session": {
                "current_instruction": "- Typed instruction wins.",
                "current_instruction_revision": "56bcd5d01510",
                "implementer_ack_revision": "56bcd5d01510",
            },
            "bridge": {
                "claude_ack_current": True,
                "reviewed_hash_current": True,
                "review_needed": False,
            },
        },
    )

    assert result.current_instruction == "- Typed instruction wins."
    assert result.current_instruction_revision == "56bcd5d01510"
    assert result.claude_ack_revision == "56bcd5d01510"
    assert result.claude_ack_current is True
    assert result.changed_since_last_ack is False
    assert result.reviewed_hash_current is True
    assert result.review_needed is False
