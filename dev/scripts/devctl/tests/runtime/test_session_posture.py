"""Focused tests for typed SessionPosture projection."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from dev.scripts.devctl.runtime.review_state_collaboration_models import (
    ActorAuthorityState,
    CapabilityGrantState,
)
from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
)
from dev.scripts.devctl.runtime.session_posture import build_session_posture


def test_capability_grants_do_not_imply_current_occupied_lane() -> None:
    posture = build_session_posture(
        collaboration=SimpleNamespace(
            actor_authorities=(
                ActorAuthorityState(
                    actor_id="claude",
                    provider="claude",
                    role="operator",
                    live=True,
                    status="attached",
                    source="authority_snapshot",
                    grants=(
                        CapabilityGrantState(
                            capability="repo.commit",
                            granted=True,
                            source="remote_control",
                        ),
                    ),
                ),
            )
        )
    )

    actor = posture.actors[0]
    assert actor.actor_id == "claude"
    assert actor.granted_capabilities == ("repo.commit",)
    assert actor.occupied_lane == ""
    assert actor.current_activity == "waiting"


def test_remote_control_attachment_sets_occupancy_separate_from_grants() -> None:
    posture = build_session_posture(
        interaction_mode="local_terminal",
        remote_control_attachment=RemoteControlAttachmentState(
            provider="claude",
            role="operator",
            status="attached",
            remote_session_id="remote-1",
        ),
        collaboration=SimpleNamespace(
            actor_authorities=(
                ActorAuthorityState(
                    actor_id="claude",
                    provider="claude",
                    role="operator",
                    live=True,
                    status="attached",
                    source="authority_snapshot",
                    grants=(
                        CapabilityGrantState(
                            capability="repo.commit",
                            granted=True,
                            source="remote_control",
                        ),
                    ),
                ),
            )
        ),
    )

    actor = posture.actors[0]
    assert posture.interaction_mode == "remote_control"
    assert actor.occupied_lane == "dashboard"
    assert actor.granted_capabilities == ("repo.commit",)
    assert actor.current_activity == "waiting"


def test_agent_mind_freshness_marks_actor_live_without_assigning_lane() -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    posture = build_session_posture(
        agent_mind={
            "agent_provider": "codex",
            "events": [{"timestamp": now, "event_type": "file_change"}],
        }
    )

    actor = posture.actors[0]
    assert actor.actor_id == "codex"
    assert actor.live is True
    assert actor.presence == "live"
    assert actor.occupied_lane == ""
    assert actor.current_activity == "reading"


def test_agent_mind_activity_projects_operator_friendly_state() -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    posture = build_session_posture(
        agent_mind={
            "agent_provider": "codex",
            "events": [
                {
                    "timestamp": now,
                    "event_type": "tool_call",
                    "tool_name": "pytest",
                    "summary": "running focused tests",
                }
            ],
        }
    )

    actor = posture.actors[0]
    assert actor.current_activity == "running_tests"
    assert actor.current_target == "running focused tests"
