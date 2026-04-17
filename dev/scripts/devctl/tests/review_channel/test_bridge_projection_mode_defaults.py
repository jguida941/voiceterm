"""Regressions for missing reviewer-mode compatibility projections."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.bridge_projection_metadata import (
    projection_metadata,
)
from dev.scripts.devctl.review_channel.bridge_projection_state import (
    BridgeProjectionState,
    bridge_projection_metadata_lines,
)
from dev.scripts.devctl.review_channel.handoff import BridgeSnapshot
from dev.scripts.devctl.review_channel.status_projection_bridge_state import (
    build_review_bridge_state,
    build_typed_bridge_liveness,
)
from dev.scripts.devctl.runtime.review_state_models import ReviewCurrentSessionState


def _current_session() -> ReviewCurrentSessionState:
    return ReviewCurrentSessionState(
        current_instruction="",
        current_instruction_revision="",
        implementer_status="",
        implementer_ack="",
        implementer_ack_revision="",
        implementer_ack_state="missing",
    )


def test_build_typed_bridge_liveness_defaults_missing_mode_to_tools_only() -> None:
    payload = build_typed_bridge_liveness(
        bridge_liveness={},
        current_session=_current_session(),
    )

    assert payload["reviewer_mode"] == "tools_only"
    assert payload["launch_truth"] == "inactive"
    assert payload["effective_reviewer_mode"] == "tools_only"
    assert payload["implementer_capability"]["queue_policy"] == "inactive"


def test_build_review_bridge_state_uses_tools_only_when_declared_mode_missing() -> None:
    state = build_review_bridge_state(
        snapshot=BridgeSnapshot(metadata={}, sections={}),
        bridge_liveness={"effective_reviewer_mode": "tools_only"},
        overall_state="inactive",
        current_session=_current_session(),
    )

    assert state.reviewer_mode == "tools_only"
    assert state.effective_reviewer_mode == "tools_only"


def test_projection_metadata_uses_effective_mode_when_declared_mode_missing() -> None:
    metadata = projection_metadata(
        snapshot=BridgeSnapshot(metadata={}, sections={}),
        bridge_liveness={},
        sections={},
        current_session={},
        bridge_state={"effective_reviewer_mode": "tools_only"},
    )

    assert metadata["reviewer_mode"] == "tools_only"


def test_bridge_projection_metadata_lines_fail_closed_to_tools_only() -> None:
    lines = bridge_projection_metadata_lines(
        BridgeProjectionState(
            metadata={},
            sections={"Current Instruction For Claude": ""},
            lines_before=0,
            bytes_before=0,
            dropped_headings=(),
            sanitized_sections=(),
        ),
        last_worktree_hash="a" * 64,
    )

    assert "- Reviewer mode: `tools_only`" in lines
