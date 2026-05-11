"""Regressions for missing reviewer-mode compatibility projections."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import patch

from dev.scripts.devctl.review_channel.bridge_projection_metadata import (
    projection_metadata,
)
from dev.scripts.devctl.review_channel.bridge_projection_state import (
    BridgeProjectionState,
    bridge_projection_metadata_lines,
)
from dev.scripts.devctl.review_channel.handoff import BridgeSnapshot
from dev.scripts.devctl.review_channel.remote_control_attachment_artifact import (
    persist_remote_control_attachment,
)
from dev.scripts.devctl.review_channel.reviewer_activity_liveness import (
    apply_reviewer_activity_liveness,
)
from dev.scripts.devctl.review_channel.status_projection_bridge_state import (
    build_review_bridge_state,
    build_typed_bridge_liveness,
)
from dev.scripts.devctl.review_channel.status_projection_helpers import (
    attach_conductor_session_state,
)
from dev.scripts.devctl.runtime.review_state_models import ReviewCurrentSessionState
from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
)


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


def test_reviewer_activity_liveness_overlays_stale_bridge_poll(tmp_path) -> None:
    event_log = tmp_path / "events" / "trace.ndjson"
    event_log.parent.mkdir(parents=True)
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    event_log.write_text(
        json.dumps(
            {
                "event_type": "packet_acked",
                "timestamp_utc": observed_at,
                "metadata": {"actor": "codex"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    bridge_liveness = {
        "last_codex_poll_age_seconds": 60 * 60 * 14,
        "last_codex_poll_utc": "2026-04-24T02:32:15Z",
        "codex_poll_state": "stale",
        "reviewer_freshness": "overdue",
    }

    activity = apply_reviewer_activity_liveness(
        bridge_liveness=bridge_liveness,
        reviewer_provider="codex",
        session_output_root=tmp_path / "latest",
    )

    assert activity is not None
    assert bridge_liveness["reviewer_activity_source"] == "typed_packet_activity"
    assert bridge_liveness["last_codex_poll_utc"] == observed_at
    assert bridge_liveness["last_reviewer_poll_utc"] == observed_at
    assert bridge_liveness["reviewer_freshness"] == "fresh"
    assert bridge_liveness["codex_poll_state"] == "fresh"


def test_build_review_bridge_state_prefers_typed_activity_poll_over_metadata() -> None:
    state = build_review_bridge_state(
        snapshot=BridgeSnapshot(
            metadata={"last_codex_poll_utc": "2026-04-24T02:32:15Z"},
            sections={},
        ),
        bridge_liveness={
            "effective_reviewer_mode": "tools_only",
            "last_codex_poll_utc": "2026-04-24T17:03:43Z",
        },
        overall_state="inactive",
        current_session=_current_session(),
    )

    assert state.last_codex_poll_utc == "2026-04-24T17:03:43Z"


def test_typed_reviewer_activity_and_remote_control_do_not_prove_dual_agent_live(
    tmp_path,
) -> None:
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    persist_remote_control_attachment(
        RemoteControlAttachmentState(
            provider="claude",
            role="operator",
            attachment_id="remote-claude",
            session_name="Claude remote-control operator",
            remote_session_id="session_remote_claude",
            status="attached",
            attached_at_utc=observed_at,
            last_seen_utc=observed_at,
        ),
        output_root=tmp_path,
    )
    bridge_liveness = {
        "reviewer_mode": "active_dual_agent",
        "overall_state": "fresh",
        "codex_poll_state": "fresh",
        "reviewer_poll_state": "fresh",
        "reviewer_freshness": "fresh",
        "last_codex_poll_utc": observed_at,
        "last_codex_poll_age_seconds": 5,
        "publisher_running": False,
        "reviewer_supervisor_running": False,
        "poll_status_automation_only": False,
    }

    with patch(
        "dev.scripts.devctl.review_channel.status_projection_helpers.active_conductor_providers",
        return_value=[],
    ), patch(
        "dev.scripts.devctl.review_channel.status_projection_helpers.conductor_visibility",
        return_value="none",
    ):
        attach_conductor_session_state(
            bridge_liveness=bridge_liveness,
            output_root=tmp_path,
            reviewer_provider="codex",
        )

    assert bridge_liveness["reviewer_activity_source"] == "reviewer_heartbeat"
    assert bridge_liveness["reviewer_activity_active"] is True
    assert bridge_liveness["launch_truth"] == "runtime_missing"
    assert bridge_liveness["effective_reviewer_mode"] == "tools_only"
    assert bridge_liveness["reviewer_freshness"] == "stale"
    assert bridge_liveness["codex_poll_state"] == "stale"
    assert bridge_liveness["active_conductor_providers"] == []
    assert set(bridge_liveness["active_runtime_providers"]) == {"codex", "claude"}


def test_typed_activity_promotes_stale_tools_only_bridge_metadata_only(
    tmp_path,
) -> None:
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    event_log = tmp_path / "events" / "trace.ndjson"
    event_log.parent.mkdir(parents=True)
    event_log.write_text(
        json.dumps(
            {
                "event_type": "packet_posted",
                "from_agent": "codex",
                "timestamp_utc": observed_at,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    persist_remote_control_attachment(
        RemoteControlAttachmentState(
            provider="claude",
            role="operator",
            attachment_id="remote-claude",
            session_name="Claude remote-control operator",
            remote_session_id="session_remote_claude",
            status="attached",
            attached_at_utc=observed_at,
            last_seen_utc=observed_at,
        ),
        output_root=tmp_path,
    )
    bridge_liveness = {
        "reviewer_mode": "tools_only",
        "overall_state": "inactive",
        "codex_poll_state": "stale",
        "reviewer_freshness": "overdue",
        "last_codex_poll_utc": "2026-04-24T02:32:15Z",
        "last_codex_poll_age_seconds": 60 * 60 * 14,
        "publisher_running": False,
        "reviewer_supervisor_running": False,
    }

    with patch(
        "dev.scripts.devctl.review_channel.status_projection_helpers.active_conductor_providers",
        return_value=[],
    ), patch(
        "dev.scripts.devctl.review_channel.status_projection_helpers.conductor_visibility",
        return_value="none",
    ):
        attach_conductor_session_state(
            bridge_liveness=bridge_liveness,
            output_root=tmp_path,
            reviewer_provider="codex",
        )

    state = build_review_bridge_state(
        snapshot=BridgeSnapshot(metadata={}, sections={}),
        bridge_liveness=bridge_liveness,
        overall_state="fresh",
        current_session=_current_session(),
    )

    assert bridge_liveness["reviewer_mode"] == "tools_only"
    assert bridge_liveness["reviewer_activity_source"] == "typed_packet_activity"
    assert bridge_liveness["launch_truth"] == "inactive"
    assert bridge_liveness["effective_reviewer_mode"] == "tools_only"
    assert "bridge_metadata_reviewer_mode" not in bridge_liveness
    assert set(bridge_liveness["active_runtime_providers"]) == {"codex", "claude"}
    assert state.reviewer_mode == "tools_only"
    assert state.effective_reviewer_mode == "tools_only"
    assert not hasattr(state, "bridge_metadata_reviewer_mode")


def test_fresh_codex_heartbeat_promotes_tools_only_bridge_when_remote_control_live(
    tmp_path,
) -> None:
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    persist_remote_control_attachment(
        RemoteControlAttachmentState(
            provider="claude",
            role="operator",
            attachment_id="remote-claude",
            session_name="Claude remote-control operator",
            remote_session_id="session_remote_claude",
            status="attached",
            attached_at_utc=observed_at,
            last_seen_utc=observed_at,
        ),
        output_root=tmp_path,
    )
    bridge_liveness = {
        "reviewer_mode": "tools_only",
        "overall_state": "inactive",
        "codex_poll_state": "fresh",
        "reviewer_poll_state": "fresh",
        "reviewer_freshness": "fresh",
        "last_codex_poll_utc": observed_at,
        "last_codex_poll_age_seconds": 5,
        "publisher_running": False,
        "reviewer_supervisor_running": False,
        "poll_status_automation_only": False,
    }

    with patch(
        "dev.scripts.devctl.review_channel.status_projection_helpers.active_conductor_providers",
        return_value=[],
    ), patch(
        "dev.scripts.devctl.review_channel.status_projection_helpers.conductor_visibility",
        return_value="none",
    ):
        attach_conductor_session_state(
            bridge_liveness=bridge_liveness,
            output_root=tmp_path,
            reviewer_provider="codex",
        )

    assert bridge_liveness["reviewer_activity_source"] == "reviewer_heartbeat"
    assert bridge_liveness["reviewer_activity_active"] is True
    assert bridge_liveness["reviewer_mode"] == "tools_only"
    assert bridge_liveness["launch_truth"] == "inactive"
    assert bridge_liveness["effective_reviewer_mode"] == "tools_only"
    assert "bridge_metadata_reviewer_mode" not in bridge_liveness
    assert set(bridge_liveness["active_runtime_providers"]) == {"codex", "claude"}


def test_typed_bridge_liveness_keeps_promoted_runtime_presence_out_of_authority() -> None:
    bridge_liveness = build_typed_bridge_liveness(
        bridge_liveness={
            "reviewer_mode": "tools_only",
            "overall_state": "inactive",
            "codex_poll_state": "fresh",
            "reviewer_freshness": "fresh",
            "reviewer_activity_active": True,
            "active_runtime_providers": ["codex", "claude"],
            "remote_control_active_providers": ["claude"],
        },
        current_session=_current_session(),
    )

    assert bridge_liveness["declared_reviewer_mode"] == "tools_only"
    assert bridge_liveness["effective_reviewer_mode"] == "tools_only"
    assert bridge_liveness["reviewer_mode"] == "tools_only"


def test_projection_metadata_uses_effective_mode_when_declared_mode_missing() -> None:
    metadata = projection_metadata(
        snapshot=BridgeSnapshot(metadata={}, sections={}),
        bridge_liveness={},
        sections={},
        current_session={},
        bridge_state={"effective_reviewer_mode": "tools_only"},
    )

    assert metadata["reviewer_mode"] == "tools_only"


def test_projection_metadata_preserves_declared_mode_with_separate_effective_mode() -> None:
    metadata = projection_metadata(
        snapshot=BridgeSnapshot(
            metadata={"reviewer_mode": "active_dual_agent"},
            sections={},
        ),
        bridge_liveness={"reviewer_mode": "active_dual_agent"},
        sections={},
        current_session={},
        bridge_state={"effective_reviewer_mode": "tools_only"},
    )

    assert metadata["reviewer_mode"] == "active_dual_agent"
    assert metadata["declared_reviewer_mode"] == "active_dual_agent"
    assert metadata["effective_reviewer_mode"] == "tools_only"


def test_projection_metadata_treats_checkpoint_placeholder_as_cleared_instruction() -> None:
    metadata = projection_metadata(
        snapshot=BridgeSnapshot(metadata={}, sections={}),
        bridge_liveness={},
        sections={
            "Current Instruction For Implementer": (
                "- Cut a checkpoint before continuing to edit."
            )
        },
        current_session={"current_instruction": "", "current_instruction_revision": ""},
        bridge_state={},
    )

    assert metadata["current_instruction_revision"] == ""
    assert metadata["current_instruction_explicitly_cleared"] == "true"


def test_bridge_projection_metadata_lines_fail_closed_to_tools_only() -> None:
    lines = bridge_projection_metadata_lines(
        BridgeProjectionState(
            metadata={},
            sections={"Current Instruction For Implementer": ""},
            lines_before=0,
            bytes_before=0,
            dropped_headings=(),
            sanitized_sections=(),
        ),
        last_worktree_hash="a" * 64,
    )

    assert "- Reviewer mode: `tools_only`" in lines
