"""Focused tests for inactive-mode recovery summaries."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.review_channel import collaboration_session as collaboration_mod
from dev.scripts.devctl.review_channel.recovery_assessment import (
    build_recovery_assessment,
)
from dev.scripts.devctl.review_channel.status_projection_helpers import (
    attach_conductor_session_state,
    bridge_liveness_warnings,
)
from dev.scripts.devctl.runtime.review_state_models import ReviewCurrentSessionState


def _current_session() -> ReviewCurrentSessionState:
    return ReviewCurrentSessionState(
        current_instruction="Keep polling typed status.",
        current_instruction_revision="rev-123",
        implementer_status="- dashboard observing",
        implementer_ack="- acknowledged; instruction-rev: `rev-123`",
        implementer_ack_revision="rev-123",
        implementer_ack_state="current",
        open_findings="",
        last_reviewed_scope="dev/scripts/devctl/review_channel/collaboration_session.py",
    )


def test_single_agent_inactive_summary_mentions_typed_authority_when_lane_is_live() -> None:
    assessment = build_recovery_assessment(
        bridge_liveness={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "active_conductor_providers": ["codex", "claude"],
            "codex_conductor_active": True,
            "claude_conductor_active": True,
            "claude_status_present": True,
            "claude_ack_present": True,
            "claude_ack_current": True,
            "current_instruction_revision": "rev-123",
            "last_reviewed_scope_present": True,
            "next_action_present": True,
        },
        current_session=_current_session(),
    )

    assert assessment.diagnosis.status == "inactive"
    assert "typed packets/status remain authoritative" in (
        assessment.diagnosis.root_cause
    )


def test_single_agent_warning_mentions_typed_authority_when_lane_is_live() -> None:
    warnings = bridge_liveness_warnings(
        {
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "active_conductor_providers": ["codex", "claude"],
            "codex_conductor_active": True,
            "claude_conductor_active": True,
            "claude_status_present": True,
            "claude_ack_current": True,
        }
    )

    assert any(
        "typed status/packet surfaces remain authoritative" in warning
        for warning in warnings
    )


def test_single_agent_warning_mentions_typed_authority_for_recent_rollout_activity(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "dev/reports/review_channel/latest"
    output_root.mkdir(parents=True)
    rollout_path = (
        tmp_path
        / "sessions"
        / "2026"
        / "04"
        / "11"
        / "rollout-2026-04-11T21-52-00-codex-live.jsonl"
    )
    rollout_path.parent.mkdir(parents=True, exist_ok=True)
    rollout_path.write_text("{}\n", encoding="utf-8")
    rollout_mtime = datetime(2026, 4, 11, 21, 52, 0, tzinfo=timezone.utc).timestamp()
    os.utime(rollout_path, (rollout_mtime, rollout_mtime))
    bridge_liveness = {
        "reviewer_mode": "single_agent",
        "effective_reviewer_mode": "single_agent",
        "claude_conductor_active": True,
        "claude_status_present": True,
        "claude_ack_current": True,
    }

    with patch.object(
        collaboration_mod,
        "discover_latest_session",
        return_value=rollout_path,
    ), patch.object(
        collaboration_mod,
        "_utcnow",
        return_value=datetime(2026, 4, 11, 21, 54, 0, tzinfo=timezone.utc),
    ):
        attach_conductor_session_state(
            bridge_liveness=bridge_liveness,
            output_root=output_root,
        )

    warnings = bridge_liveness_warnings(bridge_liveness)

    assert bridge_liveness["codex_conductor_active"] is True
    assert any(
        "typed status/packet surfaces remain authoritative" in warning
        for warning in warnings
    )
