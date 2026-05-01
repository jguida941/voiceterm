"""Regression tests for typed coordination + work-board markdown renderer.

Per Codex rev_pkt_2381: ``event_render.render_event_md`` calls
``_append_coordination_state_section`` and ``_append_work_board_section``;
both helpers MUST be defined or the renderer NameErrors mid-write,
which Codex saw on ``review-channel --action post --format md``. The
caller had already mutated state, so the CLI exited rc=1 leaving the
caller uncertain whether the post succeeded.

Per Codex rev_pkt_2374/2382: the renderer must render Work Board rows
and Coordination State block when sync-status emits them, with full
column detail (actor_id, role, packet, status, mutation, branch,
worktree, focus, idle, blocker, source_event_id, confidence_class).
"""

from __future__ import annotations

# Pre-load the commands package so the cross-package event_render imports
# resolve in the same order as the CLI. Direct top-of-module
# `from dev.scripts.devctl.review_channel.event_render import render_event_md`
# triggers a pre-existing circular import in
# `commands.review_channel_bridge_render`. Importing the CLI parser first
# warms the chain, matching how production callers reach event_render.
from dev.scripts.devctl import cli as _cli  # noqa: F401

from dev.scripts.devctl.review_channel.event_render import render_event_md


def _base_report(coordination_state: dict | None, work_board: dict | None) -> dict:
    return {
        "ok": True,
        "action": "sync-status",
        "execution_mode": "event-backed",
        "queue": {"pending_total": 0, "stale_packet_count": 0},
        "coordination_state": coordination_state,
        "work_board": work_board,
        "canonical_active_packets": {"claude": "rev_pkt_2288", "codex": ""},
    }


def _typed_coordination_state() -> dict:
    return {
        "schema_version": 1,
        "contract_id": "CoordinationStateProjection",
        "coordination_topology": "multi_agent_active",
        "authority_mode": "single_writer",
        "recovery_eligibility": "remote_only",
        "legacy_reviewer_mode": "single_agent",
        "legacy_authority_label": "single_agent",
        "observed_runtime": {
            "active_actor_count": 3,
            "active_runtime_providers": ["codex", "claude"],
            "active_operator_channels": ["manual"],
        },
    }


def _typed_work_board_one_row() -> dict:
    return {
        "schema_version": 1,
        "contract_id": "AgentWorkBoardProjection",
        "event_index": "rev_evt_45000",
        "rows": [
            {
                "actor_id": "claude",
                "provider": "claude",
                "role": "implementer",
                "session_id": "abc123",
                "active_packet_id": "rev_pkt_2288",
                "status": "working",
                "mutation_mode": "live_tree",
                "branch": "feature/x",
                "worktree_identity": "wt-a9",
                "current_command": "pytest",
                "current_check": "",
                "current_file_or_module": "event_render.py",
                "idle_seconds": 5,
                "blocker_or_wait_reason": "",
                "source_event_id": "rev_evt_45000",
                "confidence_class": "direct_typed_event",
            }
        ],
        "barriers": [],
    }


def test_render_event_md_does_not_crash_with_coordination_state() -> None:
    report = _base_report(_typed_coordination_state(), None)
    text = render_event_md(report)
    assert "## Coordination State (typed)" in text
    assert "coordination_topology: multi_agent_active" in text
    assert "authority_mode: single_writer" in text
    assert "recovery_eligibility: remote_only" in text


def test_render_event_md_does_not_crash_with_work_board_rows() -> None:
    report = _base_report(_typed_coordination_state(), _typed_work_board_one_row())
    text = render_event_md(report)
    assert "## Work Board (typed rows)" in text
    assert "claude (implementer/claude)" in text
    assert "packet=rev_pkt_2288" in text
    assert "mutation=live_tree" in text
    assert "source_event_id=rev_evt_45000" in text
    assert "confidence=direct_typed_event" in text


def test_render_event_md_omits_typed_sections_when_payload_empty() -> None:
    """When sync-status emits None for both, the renderer must not crash."""
    report = _base_report(None, None)
    text = render_event_md(report)
    assert "## Coordination State (typed)" not in text
    assert "## Work Board (typed rows)" not in text


def test_render_event_md_renders_legacy_demotion_warning() -> None:
    coord = _typed_coordination_state()
    coord["legacy_reviewer_mode"] = "single_agent"
    report = _base_report(coord, None)
    text = render_event_md(report)
    assert "WARNING: legacy_reviewer_mode='single_agent'" in text


def test_render_event_md_renders_lane_barriers_when_present() -> None:
    work_board = _typed_work_board_one_row()
    work_board["barriers"] = [
        {
            "barrier_id": "barrier-1",
            "lane_id": "lane-a",
            "actor_id": "claude",
            "kind": "review_pending",
            "target_packet_id": "rev_pkt_2380",
            "target_capability": "",
            "target_actor_id": "codex",
            "raised_at_utc": "2026-04-30T05:00:00Z",
            "raised_by_event_id": "rev_evt_45000",
            "expected_clear_signal": "review_accepted",
            "summary": "Awaiting reviewer accept",
        }
    ]
    report = _base_report(_typed_coordination_state(), work_board)
    text = render_event_md(report)
    assert "## Lane Barriers (typed)" in text
    assert "claude blocked by review_pending" in text
    assert "target_packet=rev_pkt_2380" in text
    assert "target_actor=codex" in text
    assert "Awaiting reviewer accept" in text
