"""Focused tests for collaboration-session topology and ownership state."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.review_channel import collaboration_session as collaboration_mod
from dev.scripts.devctl.review_channel import (
    collaboration_session_coordination as coordination_mod,
)
from dev.scripts.devctl.review_channel.session_probe import ConductorSessionRecord
from dev.scripts.devctl.runtime.review_state_models import ReviewCurrentSessionState


def _session_record(
    provider: str,
    role: str,
    *,
    live: bool = True,
    requested_worker_budget: int | None = None,
    planned_lanes: tuple[dict[str, str], ...] = (),
) -> ConductorSessionRecord:
    return ConductorSessionRecord(
        provider=provider,
        role=role,
        provider_name=provider.title(),
        session_name=f"{provider}-conductor",
        capture_mode="visible",
        prepared_at="2026-04-08T00:00:00Z",
        repo_root="",
        script_path="",
        log_path="",
        launch_command="",
        supervision_mode="",
        approval_mode="balanced",
        planned_lane_count=len(planned_lanes),
        requested_worker_budget=requested_worker_budget,
        terminal_window_id=None,
        session_pid=None,
        planned_lanes=planned_lanes,
        metadata_path="",
        live=live,
        age_seconds=5,
    )


def _current_session(*, instruction: str, last_reviewed_scope: str) -> ReviewCurrentSessionState:
    return ReviewCurrentSessionState(
        current_instruction=instruction,
        current_instruction_revision="rev-123",
        implementer_status="- coding",
        implementer_ack="- acknowledged; instruction-rev: `rev-123`",
        implementer_ack_revision="rev-123",
        implementer_ack_state="current",
        open_findings="",
        last_reviewed_scope=last_reviewed_scope,
    )


def test_build_collaboration_session_marks_concurrent_writer_conflict(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_records = (
        _session_record(
            "codex",
            "reviewer",
            requested_worker_budget=1,
            planned_lanes=(
                {
                    "agent_id": "AGENT-1",
                    "provider": "claude",
                    "lane": "AGENT-1",
                    "role": "implementer",
                },
            ),
        ),
        _session_record("claude", "implementer"),
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_conductor_sessions",
        lambda *, session_output_root: session_records,
    )
    monkeypatch.setattr(
        coordination_mod,
        "dirty_paths_for_repo",
        lambda repo_root: ("dev/scripts/devctl/review_channel/session_state_hints.py",),
    )

    session = collaboration_mod.build_collaboration_session(
        timestamp="2026-04-08T00:00:00Z",
        plan_id="MP-377",
        session_id="session-1",
        bridge_liveness={
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
        },
        current_session=_current_session(
            instruction="Tighten `dev/scripts/devctl/runtime/startup_context.py`.",
            last_reviewed_scope="dev/scripts/devctl/runtime/startup_context.py",
        ),
        repo_root=tmp_path,
        session_output_root=tmp_path,
    )

    assert session.topology_mode == "multi_agent_orchestrated"
    assert session.work_ownership_mode == "concurrent_writer_conflict"
    assert session.ownership.status == "concurrent_writer_activity"
    assert session.ownership.outside_scope_dirty_paths == (
        "dev/scripts/devctl/review_channel/session_state_hints.py",
    )
    assert session.ownership.live_agents == ("codex", "claude")


def test_build_collaboration_session_marks_dual_agent_exclusive_slice(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_records = (
        _session_record("codex", "reviewer"),
        _session_record("claude", "implementer"),
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_conductor_sessions",
        lambda *, session_output_root: session_records,
    )
    monkeypatch.setattr(
        coordination_mod,
        "dirty_paths_for_repo",
        lambda repo_root: ("dev/scripts/devctl/runtime/startup_context.py",),
    )

    session = collaboration_mod.build_collaboration_session(
        timestamp="2026-04-08T00:00:00Z",
        plan_id="MP-377",
        session_id="session-1",
        bridge_liveness={
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
        },
        current_session=_current_session(
            instruction="Tighten `dev/scripts/devctl/runtime/startup_context.py`.",
            last_reviewed_scope="dev/scripts/devctl/runtime/startup_context.py",
        ),
        repo_root=tmp_path,
        session_output_root=tmp_path,
    )

    assert session.topology_mode == "dual_agent"
    assert session.work_ownership_mode == "exclusive_slice"
    assert session.ownership.status == "in_scope_dirty_paths"
    assert session.ownership.in_scope_dirty_paths == (
        "dev/scripts/devctl/runtime/startup_context.py",
    )
