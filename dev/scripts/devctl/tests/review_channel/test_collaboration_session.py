"""Focused tests for collaboration-session topology and ownership state."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.review_channel import collaboration_session as collaboration_mod
from dev.scripts.devctl.review_channel import (
    collaboration_session_coordination as coordination_mod,
)
from dev.scripts.devctl.review_channel import (
    collaboration_session_roster_lookup as roster_lookup_mod,
)
from dev.scripts.devctl.review_channel.session_probe import ConductorSessionRecord
from dev.scripts.devctl.runtime.review_state_models import ReviewCurrentSessionState
from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
)


def _session_record(
    provider: str,
    role: str,
    *,
    live: bool = True,
    requested_worker_budget: int | None = None,
    planned_lanes: tuple[dict[str, str], ...] = (),
    workspace_root: str = "",
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
        workspace_root=workspace_root,
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


def test_build_collaboration_session_keeps_planned_lanes_out_of_runtime_topology(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_records = (
        _session_record(
            "codex",
            "reviewer",
            planned_lanes=(
                {
                    "agent_id": "AGENT-1",
                    "provider": "claude",
                    "lane": "planned worker lane",
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
        lambda repo_root: (),
    )

    session = collaboration_mod.build_collaboration_session(
        timestamp="2026-04-22T14:00:00Z",
        plan_id="MP-377",
        session_id="session-1",
        bridge_liveness={
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
        },
        current_session=_current_session(
            instruction="Prepare a planned lane without requesting fanout.",
            last_reviewed_scope="dev/scripts/devctl/review_channel/launch.py",
        ),
        repo_root=tmp_path,
        session_output_root=tmp_path,
    )

    assert session.topology_mode == "dual_agent"
    assert len(session.delegated_work) == 1
    assert session.delegated_work[0].live is False
    delegated_gate = next(
        row for row in session.ready_gates if row.gate_id == "delegated_work"
    )
    assert delegated_gate.status == "not_requested"


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
    assert session.mutation_owner == "claude"
    assert session.verification_owner == "codex"
    assert session.verification_status == "live"
    assert session.watcher_owner == "claude"
    assert session.watcher_status == "live"


def test_build_collaboration_session_promotes_active_remote_control_attachment(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_records = (
        _session_record("codex", "reviewer", live=False),
        _session_record("claude", "implementer", live=False),
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_conductor_sessions",
        lambda *, session_output_root: session_records,
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_remote_control_attachments",
        lambda *, output_root, active_only=False: (
            RemoteControlAttachmentState(
                provider="claude",
                role="implementer",
                attachment_id="remote-attach-1",
                session_name="claude-remote-control",
                remote_session_id="session_abc123",
                session_url="https://claude.ai/code/session_abc123",
                status="attached",
                attached_at_utc="2026-04-11T00:00:00Z",
                last_seen_utc="2026-04-11T00:00:01Z",
                metadata_path=str(tmp_path / "sessions" / "claude-remote-control.json"),
            ),
        ),
    )
    monkeypatch.setattr(
        coordination_mod,
        "dirty_paths_for_repo",
        lambda repo_root: ("dev/scripts/devctl/runtime/startup_context.py",),
    )

    session = collaboration_mod.build_collaboration_session(
        timestamp="2026-04-11T00:00:00Z",
        plan_id="MP-380",
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

    claude_rows = [row for row in session.participants if row.provider == "claude"]
    assert len(claude_rows) == 1
    assert claude_rows[0].live is True
    assert claude_rows[0].capture_mode == "remote-control"
    assert claude_rows[0].session_name == "claude-remote-control"
    coding_assignment = next(
        row for row in session.role_assignments if row.role_id == "coding_agent"
    )
    assert coding_assignment.live is True
    assert coding_assignment.source == "remote_control_attachment"
    assert session.restart.status == "live"
    assert session.restart.source == "remote_control_attachment"


def test_build_collaboration_session_collapses_single_agent_remote_dashboard_to_local_writer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_records = (
        _session_record("codex", "reviewer", live=False),
        _session_record("claude", "implementer", live=False),
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_conductor_sessions",
        lambda *, session_output_root: session_records,
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_remote_control_attachments",
        lambda *, output_root, active_only=False: (
            RemoteControlAttachmentState(
                provider="claude",
                role="operator",
                attachment_id="remote-attach-1",
                session_name="claude-dashboard",
                remote_session_id="session_dash",
                session_url="https://claude.ai/code/session_dash",
                status="attached",
                attached_at_utc="2026-04-11T00:00:00Z",
                last_seen_utc="2026-04-11T00:00:01Z",
                metadata_path=str(tmp_path / "sessions" / "claude-remote-control.json"),
            ),
        ),
    )
    monkeypatch.setattr(
        coordination_mod,
        "dirty_paths_for_repo",
        lambda repo_root: ("dev/scripts/devctl/runtime/startup_context.py",),
    )

    session = collaboration_mod.build_collaboration_session(
        timestamp="2026-04-11T00:00:00Z",
        plan_id="MP-380",
        session_id="session-1",
        bridge_liveness={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "codex_poll_state": "fresh",
        },
        current_session=_current_session(
            instruction="Tighten `dev/scripts/devctl/runtime/startup_context.py`.",
            last_reviewed_scope="dev/scripts/devctl/runtime/startup_context.py",
        ),
        repo_root=tmp_path,
        session_output_root=tmp_path,
    )

    review_assignment = next(
        row for row in session.role_assignments if row.role_id == "review_agent"
    )
    coding_assignment = next(
        row for row in session.role_assignments if row.role_id == "coding_agent"
    )
    operator_assignment = next(
        row for row in session.role_assignments if row.role_id == "operator_agent"
    )

    assert review_assignment.provider == "codex"
    assert review_assignment.live is True
    assert review_assignment.source == "reviewer_turn"
    assert coding_assignment.provider == "codex"
    assert coding_assignment.live is True
    assert coding_assignment.source == "reviewer_turn"
    assert operator_assignment.provider == "claude"
    assert operator_assignment.live is True
    assert operator_assignment.source == "remote_control_attachment"
    assert session.mutation_owner == "codex"
    assert session.verification_owner == "claude"
    assert session.verification_status == "live"
    assert session.watcher_owner == "claude"
    assert session.watcher_status == "live"


def test_build_collaboration_session_carries_lane_identity_from_session_metadata(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_records = (
        _session_record(
            "codex",
            "reviewer",
            planned_lanes=(
                {
                    "agent_id": "AGENT-1",
                    "provider": "codex",
                    "lane": "Codex review lane",
                    "mp_scope": "MP-377",
                    "worktree": "../wt-review",
                    "branch": "feature/review",
                },
            ),
            workspace_root=str((tmp_path / "../wt-review").resolve()),
        ),
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_conductor_sessions",
        lambda *, session_output_root: session_records,
    )
    monkeypatch.setattr(
        coordination_mod,
        "dirty_paths_for_repo",
        lambda repo_root: (),
    )

    session = collaboration_mod.build_collaboration_session(
        timestamp="2026-04-11T00:00:00Z",
        plan_id="MP-377",
        session_id="session-1",
        bridge_liveness={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
        },
        current_session=_current_session(
            instruction="Drive lane identity through typed coordination.",
            last_reviewed_scope="dev/scripts/devctl/review_channel/launch.py",
        ),
        repo_root=tmp_path,
        session_output_root=tmp_path,
    )

    participant = next(row for row in session.participants if row.provider == "codex")
    assert participant.lane == "Codex review lane"
    assert participant.mp_scope == "MP-377"
    assert participant.worktree == "../wt-review"
    assert participant.branch == "feature/review"
    assert participant.workspace_root == str((tmp_path / "../wt-review").resolve())


def test_build_collaboration_session_promotes_fresh_local_single_agent_reviewer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_records = (
        _session_record("codex", "reviewer", live=False),
        _session_record("claude", "implementer", live=False),
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_conductor_sessions",
        lambda *, session_output_root: session_records,
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_remote_control_attachments",
        lambda *, output_root, active_only=False: (
            RemoteControlAttachmentState(
                provider="claude",
                role="implementer",
                attachment_id="remote-attach-1",
                session_name="claude-remote-control",
                remote_session_id="session_abc123",
                session_url="https://claude.ai/code/session_abc123",
                status="attached",
                attached_at_utc="2026-04-11T00:00:00Z",
                last_seen_utc="2026-04-11T00:00:01Z",
                metadata_path=str(tmp_path / "sessions" / "claude-remote-control.json"),
            ),
        ),
    )
    monkeypatch.setattr(
        coordination_mod,
        "dirty_paths_for_repo",
        lambda repo_root: ("dev/scripts/devctl/runtime/startup_context.py",),
    )

    session = collaboration_mod.build_collaboration_session(
        timestamp="2026-04-11T00:00:00Z",
        plan_id="MP-380",
        session_id="session-1",
        bridge_liveness={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "codex_poll_state": "fresh",
            "last_codex_poll_utc": "2026-04-11T00:00:01Z",
        },
        current_session=_current_session(
            instruction="Tighten `dev/scripts/devctl/runtime/startup_context.py`.",
            last_reviewed_scope="dev/scripts/devctl/runtime/startup_context.py",
        ),
        repo_root=tmp_path,
        session_output_root=tmp_path,
    )

    live_providers = {
        row.provider for row in session.participants if row.live
    }
    assert live_providers == {"claude", "codex"}
    review_assignment = next(
        row for row in session.role_assignments if row.role_id == "review_agent"
    )
    assert review_assignment.live is True
    assert review_assignment.source == "reviewer_turn"


def test_build_collaboration_session_promotes_recent_local_reviewer_packet_activity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_records = (
        _session_record("codex", "reviewer", live=False),
        _session_record("claude", "implementer", live=False),
    )
    projections_root = tmp_path / "projections" / "latest"
    projections_root.mkdir(parents=True)
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "trace.ndjson").write_text(
        json.dumps(
            {
                "event_type": "packet_acked",
                "timestamp_utc": "2026-04-11T21:17:45Z",
                "metadata": {"actor": "codex"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_conductor_sessions",
        lambda *, session_output_root: session_records,
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_remote_control_attachments",
        lambda *, output_root, active_only=False: (
            RemoteControlAttachmentState(
                provider="claude",
                role="implementer",
                attachment_id="remote-attach-1",
                session_name="claude-remote-control",
                remote_session_id="session_abc123",
                session_url="https://claude.ai/code/session_abc123",
                status="attached",
                attached_at_utc="2026-04-11T00:00:00Z",
                last_seen_utc="2026-04-11T00:00:01Z",
                metadata_path=str(tmp_path / "sessions" / "claude-remote-control.json"),
            ),
        ),
    )
    monkeypatch.setattr(
        collaboration_mod,
        "_utcnow",
        lambda: datetime(2026, 4, 11, 21, 24, 30, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(
        coordination_mod,
        "dirty_paths_for_repo",
        lambda repo_root: ("dev/scripts/devctl/runtime/startup_context.py",),
    )

    session = collaboration_mod.build_collaboration_session(
        timestamp="2026-04-11T21:24:30Z",
        plan_id="MP-380",
        session_id="session-1",
        bridge_liveness={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "reviewer_freshness": "overdue",
            "codex_poll_state": "stale",
        },
        current_session=_current_session(
            instruction="Tighten `dev/scripts/devctl/runtime/startup_context.py`.",
            last_reviewed_scope="dev/scripts/devctl/runtime/startup_context.py",
        ),
        repo_root=tmp_path,
        session_output_root=projections_root,
    )

    live_providers = {row.provider for row in session.participants if row.live}
    assert live_providers == {"claude", "codex"}
    review_assignment = next(
        row for row in session.role_assignments if row.role_id == "review_agent"
    )
    assert review_assignment.live is True
    assert review_assignment.source == "reviewer_turn"


def test_build_collaboration_session_promotes_recent_local_reviewer_rollout_activity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_records = (
        _session_record("codex", "reviewer", live=False),
        _session_record("claude", "implementer", live=False),
    )
    projections_root = tmp_path / "projections" / "latest"
    projections_root.mkdir(parents=True)
    rollout_path = (
        tmp_path
        / "sessions"
        / "2026"
        / "04"
        / "11"
        / "rollout-2026-04-11T21-22-00-codex-live.jsonl"
    )
    rollout_path.parent.mkdir(parents=True, exist_ok=True)
    rollout_path.write_text("{}\n", encoding="utf-8")
    rollout_mtime = datetime(2026, 4, 11, 21, 22, 0, tzinfo=timezone.utc).timestamp()
    os.utime(rollout_path, (rollout_mtime, rollout_mtime))
    monkeypatch.setattr(
        collaboration_mod,
        "discover_latest_session",
        lambda provider: rollout_path if provider == "codex" else None,
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_conductor_sessions",
        lambda *, session_output_root: session_records,
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_remote_control_attachments",
        lambda *, output_root, active_only=False: (
            RemoteControlAttachmentState(
                provider="claude",
                role="implementer",
                attachment_id="remote-attach-1",
                session_name="claude-remote-control",
                remote_session_id="session_abc123",
                session_url="https://claude.ai/code/session_abc123",
                status="attached",
                attached_at_utc="2026-04-11T00:00:00Z",
                last_seen_utc="2026-04-11T00:00:01Z",
                metadata_path=str(tmp_path / "sessions" / "claude-remote-control.json"),
            ),
        ),
    )
    monkeypatch.setattr(
        collaboration_mod,
        "_utcnow",
        lambda: datetime(2026, 4, 11, 21, 24, 30, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(
        coordination_mod,
        "dirty_paths_for_repo",
        lambda repo_root: ("dev/scripts/devctl/runtime/startup_context.py",),
    )

    session = collaboration_mod.build_collaboration_session(
        timestamp="2026-04-11T21:24:30Z",
        plan_id="MP-380",
        session_id="session-1",
        bridge_liveness={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "reviewer_freshness": "overdue",
            "codex_poll_state": "stale",
        },
        current_session=_current_session(
            instruction="Tighten `dev/scripts/devctl/runtime/startup_context.py`.",
            last_reviewed_scope="dev/scripts/devctl/runtime/startup_context.py",
        ),
        repo_root=tmp_path,
        session_output_root=projections_root,
    )

    live_providers = {row.provider for row in session.participants if row.live}
    assert live_providers == {"claude", "codex"}
    review_assignment = next(
        row for row in session.role_assignments if row.role_id == "review_agent"
    )
    assert review_assignment.live is True
    assert review_assignment.source == "reviewer_turn"


def test_build_collaboration_session_promotes_recent_packet_active_implementer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_records = (
        _session_record("codex", "reviewer", live=True),
        _session_record("claude", "implementer", live=False),
    )
    projections_root = tmp_path / "projections" / "latest"
    projections_root.mkdir(parents=True)
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "trace.ndjson").write_text(
        json.dumps(
            {
                "event_type": "packet_posted",
                "timestamp_utc": "2026-04-15T19:35:58Z",
                "from_agent": "claude",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_conductor_sessions",
        lambda *, session_output_root: session_records,
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_remote_control_attachments",
        lambda *, output_root, active_only=False: (),
    )
    monkeypatch.setattr(
        collaboration_mod,
        "_utcnow",
        lambda: datetime(2026, 4, 15, 19, 36, 10, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(
        coordination_mod,
        "dirty_paths_for_repo",
        lambda repo_root: ("dev/scripts/devctl/runtime/startup_context.py",),
    )

    session = collaboration_mod.build_collaboration_session(
        timestamp="2026-04-15T19:36:10Z",
        plan_id="MP-377",
        session_id="session-1",
        bridge_liveness={
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
        },
        current_session=_current_session(
            instruction="Tighten `dev/scripts/devctl/runtime/control_topology.py`.",
            last_reviewed_scope="dev/scripts/devctl/runtime/control_topology.py",
        ),
        repo_root=tmp_path,
        session_output_root=projections_root,
    )

    live_providers = {row.provider for row in session.participants if row.live}
    assert live_providers == {"claude", "codex"}
    coding_assignment = next(
        row for row in session.role_assignments if row.role_id == "coding_agent"
    )
    assert coding_assignment.live is True
    assert coding_assignment.source == "packet_activity"


def test_build_collaboration_session_single_agent_ignores_stale_implementer_packet_activity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session_records = (
        _session_record("codex", "reviewer", live=False),
        _session_record("claude", "implementer", live=False),
    )
    projections_root = tmp_path / "projections" / "latest"
    projections_root.mkdir(parents=True)
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "trace.ndjson").write_text(
        json.dumps(
            {
                "event_type": "packet_posted",
                "timestamp_utc": "2026-04-22T14:40:00Z",
                "from_agent": "claude",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_conductor_sessions",
        lambda *, session_output_root: session_records,
    )
    monkeypatch.setattr(
        collaboration_mod,
        "load_remote_control_attachments",
        lambda *, output_root, active_only=False: (),
    )
    monkeypatch.setattr(
        collaboration_mod,
        "_utcnow",
        lambda: datetime(2026, 4, 22, 14, 41, 0, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(
        coordination_mod,
        "dirty_paths_for_repo",
        lambda repo_root: (),
    )

    session = collaboration_mod.build_collaboration_session(
        timestamp="2026-04-22T14:41:00Z",
        plan_id="MP-377",
        session_id="session-1",
        bridge_liveness={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "codex_poll_state": "fresh",
            "last_codex_poll_utc": "2026-04-22T14:40:59Z",
        },
        current_session=_current_session(
            instruction="Keep Codex as the single local implementer.",
            last_reviewed_scope="dev/scripts/devctl/review_channel/launch.py",
        ),
        repo_root=tmp_path,
        session_output_root=projections_root,
    )

    coding_assignment = next(
        row for row in session.role_assignments if row.role_id == "coding_agent"
    )
    claude_participant = next(
        row for row in session.participants if row.provider == "claude"
    )

    assert coding_assignment.provider == "codex"
    assert coding_assignment.live is True
    assert coding_assignment.source == "reviewer_turn"
    assert claude_participant.live is False
    assert session.mutation_owner == "codex"
    assert session.topology_mode == "single_agent"


def test_build_collaboration_session_demotes_stale_implementer_assignment_when_attachment_is_operator(
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
        collaboration_mod,
        "load_remote_control_attachments",
        lambda *, output_root, active_only=False: (
            RemoteControlAttachmentState(
                provider="claude",
                role="operator",
                attachment_id="remote-attach-1",
                session_name="claude-remote-control",
                remote_session_id="session_dash",
                session_url="https://claude.ai/code/session_dash",
                status="attached",
                attached_at_utc="2026-04-18T00:00:00Z",
                last_seen_utc="2026-04-18T00:00:01Z",
                metadata_path=str(tmp_path / "sessions" / "claude-remote-control.json"),
            ),
        ),
    )
    monkeypatch.setattr(
        coordination_mod,
        "dirty_paths_for_repo",
        lambda repo_root: ("dev/scripts/devctl/runtime/control_topology.py",),
    )

    session = collaboration_mod.build_collaboration_session(
        timestamp="2026-04-18T00:00:00Z",
        plan_id="MP-377",
        session_id="session-1",
        bridge_liveness={
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
            "codex_conductor_active": True,
            "claude_conductor_active": True,
        },
        current_session=_current_session(
            instruction="Keep the typed control topology honest.",
            last_reviewed_scope="dev/scripts/devctl/runtime/control_topology.py",
        ),
        repo_root=tmp_path,
        session_output_root=tmp_path,
    )

    claude_participant = next(
        row for row in session.participants if row.provider == "claude"
    )
    coding_assignment = next(
        row for row in session.role_assignments if row.role_id == "coding_agent"
    )
    runtime_gate = next(
        row for row in session.ready_gates if row.gate_id == "runtime_truth"
    )

    assert claude_participant.role == "operator"
    assert coding_assignment.provider == "claude"
    assert coding_assignment.live is False
    assert coding_assignment.status == "configured"
    assert coding_assignment.source == "remote_control_attachment"
    assert runtime_gate.status == "blocked"
    assert (
        runtime_gate.summary
        == "Active dual-agent mode still requires live reviewer and implementer conductor sessions."
    )


def test_role_assignment_fails_closed_for_unknown_role_id() -> None:
    assignment = roster_lookup_mod.role_assignment(
        "observer_agent",
        "claude",
        "Claude",
        (_session_record("claude", "implementer"),),
    )

    assert assignment.provider == "claude"
    assert assignment.live is False
    assert assignment.status == "configured"
    assert assignment.source == "session_metadata"
