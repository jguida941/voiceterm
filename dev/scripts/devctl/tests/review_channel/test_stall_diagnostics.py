"""Tests for review-channel conductor stall diagnostics."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from dev.scripts.devctl.review_channel.stall_diagnostics import (
    ConductorStallDiagnosis,
    diagnose_conductor_stall,
)


def _iso_to_unix(iso_utc: str) -> float:
    return datetime.fromisoformat(iso_utc.replace("Z", "+00:00")).timestamp()


def _write_rollout(path: Path, *, events: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event) + "\n")


def test_no_task_complete_returns_not_stalled(tmp_path: Path) -> None:
    rollouts_root = tmp_path / "sessions"
    rollout = rollouts_root / "rollout-2026-04-20T17-08-08-019dacb8.jsonl"
    _write_rollout(
        rollout,
        events=[{"type": "reasoning", "timestamp": "2026-04-20T21:10:00.000Z"}],
    )

    diagnosis = diagnose_conductor_stall(
        session_id="019dacb8",
        rollout_path=rollout,
        rollouts_root=rollouts_root,
        observation_utc="2026-04-20T21:25:00.000Z",
        observation_unix_seconds=_iso_to_unix("2026-04-20T21:25:00.000Z"),
    )

    assert isinstance(diagnosis, ConductorStallDiagnosis)
    assert diagnosis.stalled is False
    assert diagnosis.reason == "no_task_complete_yet"
    assert diagnosis.latest_task_complete_utc == ""
    assert diagnosis.latest_escalation_utc == ""


def test_task_complete_within_budget_is_not_stalled(tmp_path: Path) -> None:
    rollouts_root = tmp_path / "sessions"
    rollout = rollouts_root / "rollout-2026-04-20T17-08-08-019dacb8.jsonl"
    _write_rollout(
        rollout,
        events=[
            {"type": "reasoning", "timestamp": "2026-04-20T21:10:00.000Z"},
            {"type": "task_complete", "timestamp": "2026-04-20T21:24:00.000Z"},
        ],
    )

    observation_iso = "2026-04-20T21:25:00.000Z"
    diagnosis = diagnose_conductor_stall(
        session_id="019dacb8",
        rollout_path=rollout,
        rollouts_root=rollouts_root,
        observation_utc=observation_iso,
        observation_unix_seconds=_iso_to_unix(observation_iso),
    )

    assert diagnosis.stalled is False
    assert diagnosis.reason == "within_budget"
    assert diagnosis.latest_task_complete_utc == "2026-04-20T21:24:00.000Z"
    assert diagnosis.elapsed_seconds_since_task_complete == 60.0


def test_task_complete_past_budget_with_no_replacement_is_stalled(tmp_path: Path) -> None:
    rollouts_root = tmp_path / "sessions"
    rollout = rollouts_root / "rollout-2026-04-20T17-08-08-019dacb8.jsonl"
    _write_rollout(
        rollout,
        events=[{"type": "task_complete", "timestamp": "2026-04-20T20:00:00.000Z"}],
    )

    observation_iso = "2026-04-20T21:00:00.000Z"
    diagnosis = diagnose_conductor_stall(
        session_id="019dacb8",
        rollout_path=rollout,
        rollouts_root=rollouts_root,
        observation_utc=observation_iso,
        observation_unix_seconds=_iso_to_unix(observation_iso),
        stall_budget_seconds=300.0,
    )

    assert diagnosis.stalled is True
    assert diagnosis.reason == "stalled_beyond_budget"
    assert diagnosis.new_session_since_task_complete is False
    assert diagnosis.elapsed_seconds_since_task_complete == 3600.0


def test_explicit_replacement_session_clears_stall(tmp_path: Path) -> None:
    """rev_pkt_1515: caller-supplied replacement session ids opt into clearance."""
    rollouts_root = tmp_path / "sessions"
    old_rollout = rollouts_root / "rollout-2026-04-20T17-08-08-019dacb8.jsonl"
    _write_rollout(
        old_rollout,
        events=[{"type": "task_complete", "timestamp": "2026-04-20T20:00:00.000Z"}],
    )
    new_rollout = rollouts_root / "rollout-2026-04-20T20-30-00-019dacff.jsonl"
    _write_rollout(
        new_rollout,
        events=[{"type": "reasoning", "timestamp": "2026-04-20T20:30:00.000Z"}],
    )

    observation_iso = "2026-04-20T21:00:00.000Z"
    diagnosis = diagnose_conductor_stall(
        session_id="019dacb8",
        rollout_path=old_rollout,
        rollouts_root=rollouts_root,
        observation_utc=observation_iso,
        observation_unix_seconds=_iso_to_unix(observation_iso),
        stall_budget_seconds=300.0,
        replacement_session_ids=frozenset({"019dacff"}),
    )

    assert diagnosis.stalled is False
    assert diagnosis.reason == "new_session_spawned"
    assert diagnosis.new_session_since_task_complete is True


def test_unrelated_newer_rollout_does_not_clear_stall(tmp_path: Path) -> None:
    """rev_pkt_1515 fix: newer rollout from an unrelated lane must NOT clear the stall."""
    rollouts_root = tmp_path / "sessions"
    old_rollout = rollouts_root / "rollout-2026-04-20T17-08-08-019dacb8.jsonl"
    _write_rollout(
        old_rollout,
        events=[{"type": "task_complete", "timestamp": "2026-04-20T20:00:00.000Z"}],
    )
    unrelated_rollout = rollouts_root / "rollout-2026-04-20T20-30-00-claude-other.jsonl"
    _write_rollout(
        unrelated_rollout,
        events=[{"type": "reasoning", "timestamp": "2026-04-20T20:30:00.000Z"}],
    )

    observation_iso = "2026-04-20T21:00:00.000Z"
    diagnosis = diagnose_conductor_stall(
        session_id="019dacb8",
        rollout_path=old_rollout,
        rollouts_root=rollouts_root,
        observation_utc=observation_iso,
        observation_unix_seconds=_iso_to_unix(observation_iso),
        stall_budget_seconds=300.0,
        # Caller did not opt in to claude-other as a replacement.
        replacement_session_ids=frozenset(),
    )

    assert diagnosis.stalled is True
    assert diagnosis.reason == "stalled_beyond_budget"
    assert diagnosis.new_session_since_task_complete is False


def test_escalation_deadlock_when_escalation_is_latest_event(tmp_path: Path) -> None:
    """Reproduces empirical sandbox-escalation deadlock from session 019dacd1."""
    rollouts_root = tmp_path / "sessions"
    rollout = rollouts_root / "rollout-2026-04-20T17-34-45-019dacd1.jsonl"
    _write_rollout(
        rollout,
        events=[
            {
                "event_type": "response_item:function_call",
                "is_escalation": True,
                "summary": "ESCALATION: Do you want me to inspect the stuck startup-context processes outside the sandbox so I can diagnose the bootstrap state?",
                "tool_command": "ps -Ao pid,ppid,stat,etime,command",
                "timestamp": "2026-04-20T21:36:54.924Z",
            },
        ],
    )

    observation_iso = "2026-04-20T21:50:00.000Z"
    diagnosis = diagnose_conductor_stall(
        session_id="019dacd1",
        rollout_path=rollout,
        rollouts_root=rollouts_root,
        observation_utc=observation_iso,
        observation_unix_seconds=_iso_to_unix(observation_iso),
        stall_budget_seconds=300.0,
    )

    assert diagnosis.stalled is True
    assert diagnosis.reason == "escalation_deadlock"
    assert diagnosis.latest_escalation_utc == "2026-04-20T21:36:54.924Z"
    assert "ESCALATION" in diagnosis.latest_escalation_summary
    assert diagnosis.elapsed_seconds_since_latest_escalation > 300.0


def test_escalation_followed_by_later_activity_is_not_deadlock(tmp_path: Path) -> None:
    """rev_pkt_1516 fix: escalation followed by later events is NOT a deadlock."""
    rollouts_root = tmp_path / "sessions"
    rollout = rollouts_root / "rollout-2026-04-20T17-34-45-019dacd1.jsonl"
    _write_rollout(
        rollout,
        events=[
            {
                "event_type": "response_item:function_call",
                "is_escalation": True,
                "summary": "ESCALATION: approval requested",
                "tool_command": "ps -Ao pid,ppid,stat,etime,command",
                "timestamp": "2026-04-20T21:36:54.924Z",
            },
            {
                "event_type": "response_item:reasoning",
                "is_escalation": False,
                "summary": "reasoning (encrypted)",
                "timestamp": "2026-04-20T21:37:10.000Z",
            },
        ],
    )

    observation_iso = "2026-04-20T21:50:00.000Z"
    diagnosis = diagnose_conductor_stall(
        session_id="019dacd1",
        rollout_path=rollout,
        rollouts_root=rollouts_root,
        observation_utc=observation_iso,
        observation_unix_seconds=_iso_to_unix(observation_iso),
        stall_budget_seconds=300.0,
    )

    assert diagnosis.stalled is False
    assert diagnosis.reason == "escalation_recent"
    assert diagnosis.latest_event_utc == "2026-04-20T21:37:10.000Z"
    assert diagnosis.latest_escalation_utc == "2026-04-20T21:36:54.924Z"


def test_recent_escalation_within_budget_is_not_stalled(tmp_path: Path) -> None:
    rollouts_root = tmp_path / "sessions"
    rollout = rollouts_root / "rollout-2026-04-20T17-34-45-019dacd1.jsonl"
    _write_rollout(
        rollout,
        events=[
            {
                "event_type": "response_item:function_call",
                "is_escalation": True,
                "summary": "ESCALATION: approval requested",
                "timestamp": "2026-04-20T21:49:00.000Z",
            },
        ],
    )

    observation_iso = "2026-04-20T21:50:00.000Z"
    diagnosis = diagnose_conductor_stall(
        session_id="019dacd1",
        rollout_path=rollout,
        rollouts_root=rollouts_root,
        observation_utc=observation_iso,
        observation_unix_seconds=_iso_to_unix(observation_iso),
        stall_budget_seconds=300.0,
    )

    assert diagnosis.stalled is False
    assert diagnosis.reason == "escalation_recent"


def test_missing_rollout_file_is_not_stalled(tmp_path: Path) -> None:
    rollouts_root = tmp_path / "sessions"
    rollouts_root.mkdir()
    missing = rollouts_root / "rollout-missing.jsonl"

    diagnosis = diagnose_conductor_stall(
        session_id="019dacb8",
        rollout_path=missing,
        rollouts_root=rollouts_root,
        observation_utc="2026-04-20T21:25:00.000Z",
        observation_unix_seconds=_iso_to_unix("2026-04-20T21:25:00.000Z"),
    )

    assert diagnosis.stalled is False
    assert diagnosis.reason == "no_task_complete_yet"
