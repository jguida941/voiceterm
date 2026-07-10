"""Regression tests for typed read-path convergence on bridge-poll.

Per Codex rev_pkt_2368/2375: bridge-poll, dashboard, claude-loop, and
startup-context must read the same typed canonical active packet, typed
coordination_topology, and typed recovery_eligibility. Legacy fields may
remain only as clearly marked compatibility surfaces. Local devctl-commit
recovery commands MUST be suppressed when typed
``coordination_state.recovery_eligibility`` is ``remote_only`` or
``blocked``.

This module covers the bridge-poll surface specifically. Without these
guards, bridge-poll silently disagrees with sync-status/dashboard and
operators see ``single_agent`` + local-commit advice while the typed
authority says multi-agent + remote_only.
"""

from __future__ import annotations

from datetime import datetime, timezone

from dev.scripts.devctl.commands.review_channel._bridge_poll import (
    build_bridge_poll_result,
)
from dev.scripts.devctl.tests.review_channel.test_bridge_poll import (
    _build_bridge_text,
    _typed_review_state,
)


def _typed_state_with_typed_authority(
    *,
    coordination_topology: str,
    recovery_eligibility: str,
    canonical_active_packet_for_claude: str = "",
    canonical_active_packet_for_codex: str = "",
) -> dict[str, object]:
    state = _typed_review_state(
        recovery_action_allowed=(
            'python3 dev/scripts/devctl.py commit -m "<descriptive message>"'
        ),
    )
    state["coordination_state"] = {
        "schema_version": 1,
        "contract_id": "CoordinationStateProjection",
        "coordination_topology": coordination_topology,
        "authority_mode": "single_writer",
        "recovery_eligibility": recovery_eligibility,
        "legacy_reviewer_mode": "single_agent",
        "legacy_authority_label": "single_agent",
        "observed_runtime": {
            "active_actor_count": 3,
            "active_runtime_providers": ["codex", "claude"],
            "active_operator_channels": ["manual"],
            "active_conductors": ["codex", "claude"],
            "detached_runtime_providers": [],
            "work_board_row_counts": {"total": 3, "status_working": 3},
        },
    }
    rows: list[dict[str, object]] = []
    if canonical_active_packet_for_claude:
        rows.append(
            {
                "actor_id": "claude",
                "active_packet_id": canonical_active_packet_for_claude,
                "source_event_id": "rev_evt_45000",
            }
        )
    if canonical_active_packet_for_codex:
        rows.append(
            {
                "actor_id": "codex",
                "active_packet_id": canonical_active_packet_for_codex,
                "source_event_id": "rev_evt_45001",
            }
        )
    state["agent_work_board"] = {
        "schema_version": 1,
        "contract_id": "AgentWorkBoardProjection",
        "event_index": "rev_evt_45001",
        "rows": rows,
    }
    return state


def test_bridge_poll_suppresses_local_commit_when_recovery_remote_only() -> None:
    bridge_text = _build_bridge_text(
        last_codex_poll=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    typed_state = _typed_state_with_typed_authority(
        coordination_topology="multi_agent_active",
        recovery_eligibility="remote_only",
        canonical_active_packet_for_claude="rev_pkt_2288",
    )

    result = build_bridge_poll_result(
        bridge_text,
        typed_review_state=typed_state,
    )

    assert result.recovery_action_allowed == ""
    assert result.decision_command == ""
    assert result.coordination_topology == "multi_agent_active"
    assert result.recovery_eligibility == "remote_only"
    assert result.canonical_active_packet_for_claude == "rev_pkt_2288"


def test_bridge_poll_suppresses_local_commit_when_recovery_blocked() -> None:
    bridge_text = _build_bridge_text(
        last_codex_poll=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    typed_state = _typed_state_with_typed_authority(
        coordination_topology="multi_agent_active",
        recovery_eligibility="blocked",
    )

    result = build_bridge_poll_result(
        bridge_text,
        typed_review_state=typed_state,
    )

    assert result.recovery_action_allowed == ""
    assert result.decision_command == ""
    assert result.recovery_eligibility == "blocked"


def test_bridge_poll_emits_typed_coordination_alongside_legacy_mode() -> None:
    bridge_text = _build_bridge_text(
        last_codex_poll=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    typed_state = _typed_state_with_typed_authority(
        coordination_topology="multi_agent_active",
        recovery_eligibility="remote_only",
        canonical_active_packet_for_claude="rev_pkt_2288",
        canonical_active_packet_for_codex="rev_pkt_2300",
    )

    result = build_bridge_poll_result(
        bridge_text,
        typed_review_state=typed_state,
    )

    assert result.coordination_topology == "multi_agent_active"
    assert result.authority_mode == "single_writer"
    assert result.canonical_active_packet_for_claude == "rev_pkt_2288"
    assert result.canonical_active_packet_for_codex == "rev_pkt_2300"


def test_bridge_poll_keeps_local_command_when_typed_eligibility_absent() -> None:
    bridge_text = _build_bridge_text(
        last_codex_poll=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    typed_state = _typed_review_state(
        recovery_action_allowed=(
            'python3 dev/scripts/devctl.py commit -m "<descriptive message>"'
        ),
    )

    result = build_bridge_poll_result(
        bridge_text,
        typed_review_state=typed_state,
    )

    assert "devctl.py commit" in result.recovery_action_allowed
    assert result.recovery_eligibility == ""
    assert result.coordination_topology == ""
