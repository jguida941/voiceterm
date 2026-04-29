from __future__ import annotations

from dev.scripts.devctl.runtime.control_topology_bridge_counts import (
    active_conductor_count,
    bridge_role_counts,
)
from dev.scripts.devctl.runtime.dashboard_snapshot_authority import (
    normalize_dashboard_snapshot,
)
from dev.scripts.devctl.runtime.session_liveness_builder import (
    build_session_liveness_signals,
    session_liveness_rows,
)
from dev.scripts.devctl.runtime.session_liveness_counts import provider_has_live_session
from dev.scripts.devctl.runtime.session_liveness_signal import (
    SessionLivenessInputs,
    classify_session_liveness,
)


def test_session_liveness_signal_family_classifies_all_states() -> None:
    alive = build_session_liveness_signals(
        bridge_liveness={
            "publisher_running": True,
            "reviewer_supervisor_running": True,
        },
        active_providers=["codex"],
    )[0]
    degraded = build_session_liveness_signals(
        bridge_liveness={},
        active_providers=["codex"],
    )[0]
    detached = build_session_liveness_signals(
        bridge_liveness={"active_runtime_providers": ["claude"]},
        active_providers=[],
    )[0]

    assert alive.state == "alive"
    assert degraded.state == "degraded"
    assert detached.state == "detached_runtime_only"
    assert provider_has_live_session(session_liveness_rows([degraded]), "codex") is True
    assert provider_has_live_session(session_liveness_rows([detached]), "claude") is False
    assert (
        classify_session_liveness(
            SessionLivenessInputs(provider="cursor", role="implementer")
        ).state
        == "dead"
    )


def test_startup_counts_prefer_session_liveness_signals() -> None:
    bridge = {
        "codex_conductor_active": False,
        "claude_conductor_active": False,
        "session_liveness_signals": [
            {"provider": "codex", "role": "reviewer", "state": "degraded"},
            {"provider": "claude", "role": "implementer", "state": "dead"},
        ],
    }

    assert active_conductor_count(bridge=bridge, live_participants=[]) == 1
    assert bridge_role_counts(bridge) == {
        "live_participants_total": 1,
        "live_reviewer_total": 1,
        "live_implementer_total": 0,
    }


def test_dashboard_snapshot_projects_session_liveness_section() -> None:
    snapshot = normalize_dashboard_snapshot(
        {},
        review_state={
            "bridge_liveness": {
                "session_liveness_signals": [
                    {"provider": "codex", "role": "reviewer", "state": "degraded"}
                ]
            }
        },
    )

    assert snapshot["session_liveness"]["available"] is True
    assert snapshot["session_liveness"]["signals"][0]["provider"] == "codex"


def test_dashboard_codex_sessions_prefer_session_posture_liveness() -> None:
    snapshot = normalize_dashboard_snapshot(
        {
            "control_plane": {
                "session_posture": {
                    "interaction_mode": "remote_control",
                    "reviewer_mode": "single_agent",
                    "actors": [
                        {
                            "actor_id": "codex",
                            "provider": "codex",
                            "live": True,
                            "current_activity": "running_tests",
                            "current_target": "focused guard batch",
                        }
                    ],
                }
            }
        },
        review_state={},
    )

    codex = snapshot["active_codex_sessions"]
    assert codex["live_count"] == 1
    assert codex["sessions"][0]["source"] == "session_posture"
    assert codex["sessions"][0]["current_activity"] == "running_tests"
