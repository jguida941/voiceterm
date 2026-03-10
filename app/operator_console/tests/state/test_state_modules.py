from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

from app.operator_console.state.activity.activity_assist import (
    build_assist_draft,
    build_summary_draft,
)
from app.operator_console.state.activity.activity_reports import (
    build_activity_report,
    resolve_report_option,
)
from app.operator_console.workflows import (
    DEVCTL_ENTRYPOINT,
    DEVCTL_PYTHON,
    OPERATOR_DECISION_MODULE,
    REVIEW_CHANNEL_SUBCOMMAND,
    build_launch_command,
    build_orchestrate_status_command,
    build_operator_decision_command,
    build_process_audit_command,
    build_review_channel_post_command,
    build_rollover_command,
    build_status_command,
    build_swarm_run_command,
    build_triage_command,
    evaluate_orchestrate_status_report,
    evaluate_review_channel_post,
    evaluate_review_channel_launch,
    evaluate_review_channel_rollover,
    evaluate_swarm_run_report,
    evaluate_start_swarm_launch,
    evaluate_start_swarm_preflight,
    parse_operator_decision_report,
    parse_orchestrate_status_report,
    parse_review_channel_report,
    parse_swarm_run_report,
    render_command,
    terminal_app_live_support_detail,
    terminal_app_live_supported,
)
from app.operator_console.state.bridge.bridge_sections import parse_markdown_sections
from app.operator_console.state.bridge.lane_builder import (
    build_claude_lane,
    build_codex_lane,
    build_cursor_lane,
    build_operator_lane,
)
from app.operator_console.layout.layout_state import (
    LayoutStateSnapshot,
    default_layout_state_path,
    load_layout_state,
    save_layout_state,
)
from app.operator_console.state.core.models import (
    ApprovalRequest,
    ContextPackRef,
    OperatorConsoleSnapshot,
    QualityBacklogSnapshot,
    QualityPrioritySignal,
)
from app.operator_console.state.review.operator_decisions import (
    _atomic_write_text,
    main as operator_decisions_main,
    record_operator_decision,
)
from app.operator_console.state.review.review_state import (
    find_review_full_path,
    find_review_state_path,
    load_pending_approvals,
)
from app.operator_console.state.repo.repo_state import RepoStateSnapshot
from app.operator_console.state.sessions.session_trace_reader import (
    SessionTraceSnapshot,
    load_live_session_trace,
)
from app.operator_console.state.snapshots.snapshot_builder import (
    build_operator_console_snapshot,
)
from app.operator_console.workflows.workflow_presets import (
    DEFAULT_WORKFLOW_PRESET_ID,
    available_workflow_presets,
    resolve_workflow_preset,
)
from app.operator_console.collaboration.timeline_builder import build_timeline_from_snapshot
from app.operator_console.workflows.workflow_surface_state import (
    build_workflow_surface_state,
)


def _bridge_text() -> str:
    return "\n".join(
        [
            "# Code Audit Channel",
            "",
            "- Last Codex poll: `2026-03-08T20:00:00Z`",
            "- Last non-audit worktree hash: `abc123`",
            "",
            "## Poll Status",
            "",
            "- active reviewer loop",
            "",
            "## Current Verdict",
            "",
            "- still in progress",
            "",
            "## Open Findings",
            "",
            "- pending operator decision",
            "",
            "## Current Instruction For Claude",
            "",
            "- wait for approval",
            "",
            "## Claude Status",
            "",
            "- coding paused",
            "",
            "## Claude Questions",
            "",
            "- should I push?",
            "",
            "## Claude Ack",
            "",
            "- acknowledged",
            "",
        ]
    )


def _review_state_json() -> dict[str, object]:
    return {
        "packets": [
            {
                "packet_id": "pkt-1",
                "from_agent": "codex",
                "to_agent": "operator",
                "summary": "Approve guarded push",
                "body": "Need operator approval before push.",
                "policy_hint": "operator_approval_required",
                "requested_action": "git_push",
                "approval_required": True,
                "status": "pending",
                "evidence_refs": ["code_audit.md#L1"],
                "context_pack_refs": [
                    {
                        "pack_kind": "task_pack",
                        "pack_ref": ".voiceterm/memory/exports/task_pack.json",
                        "adapter_profile": "canonical",
                        "generated_at_utc": "2026-03-09T13:22:00Z",
                    }
                ],
            }
        ]
    }


def _fresh_live_trace(provider: str) -> SessionTraceSnapshot:
    updated_at = _fresh_timestamp()
    return SessionTraceSnapshot(
        provider=provider,
        session_name=f"{provider}-conductor",
        capture_mode="terminal-script",
        prepared_at=updated_at,
        updated_at=updated_at,
        metadata_path=f"/tmp/{provider}-conductor.json",
        log_path=f"/tmp/{provider}-conductor.log",
        tail_text="live output",
        screen_text="live output",
        history_text="live output",
    )


def _fresh_timestamp() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


class StateModuleTests(unittest.TestCase):
    def test_layout_state_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = default_layout_state_path(root)
            expected = LayoutStateSnapshot(
                layout_mode="workbench",
                workbench_preset="balanced",
                workbench_surface="terminal",
                monitor_surface="diagnostics",
                lane_splitter_sizes=(500, 200, 500),
                utility_splitter_sizes=(700, 250, 250),
            )

            save_layout_state(path, expected)
            loaded = load_layout_state(path)

        self.assertEqual(loaded, expected)

    def test_layout_state_loader_handles_invalid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = default_layout_state_path(root)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{not-json", encoding="utf-8")

            loaded = load_layout_state(path)

        self.assertIsNone(loaded)

    def test_timeline_builder_includes_lane_and_operator_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            snapshot = build_operator_console_snapshot(root)
            events = build_timeline_from_snapshot(snapshot)

        actors = {event.actor for event in events}
        self.assertIn("codex", actors)
        self.assertIn("claude", actors)
        self.assertIn("operator", actors)

    def test_timeline_builder_reads_rollover_handoff_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            handoff_root = root / "dev/reports/review_channel/rollovers/20260309T120000Z"
            handoff_root.mkdir(parents=True, exist_ok=True)
            (handoff_root / "handoff.json").write_text(
                json.dumps(
                    {
                        "created_at": "2026-03-09T12:00:00Z",
                        "resume_state": {
                            "next_action": "continue reviewer loop",
                            "current_atomic_step": "wait for claude ack",
                            "reviewed_worktree_hash": "abc123",
                        },
                    }
                ),
                encoding="utf-8",
            )
            snapshot = build_operator_console_snapshot(root)
            events = build_timeline_from_snapshot(snapshot, repo_root=root)

        self.assertTrue(
            any(event.source == "rollover handoff" for event in events),
            "Expected rollover handoff event in timeline output.",
        )

    def test_workflow_surface_state_tracks_slice_and_footer_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            review_state_path = root / "review_state.json"
            review_state_path.write_text(
                json.dumps(_review_state_json()),
                encoding="utf-8",
            )
            snapshot = build_operator_console_snapshot(
                root,
                review_state_path=review_state_path,
            )
            repo_state = RepoStateSnapshot(
                branch="develop",
                head_sha="a" * 40,
                head_short="aaaaaaaa",
                is_dirty=True,
                dirty_file_count=3,
                staged_count=1,
                unstaged_count=1,
                untracked_count=1,
                active_mp_scope="MP-359",
                changed_path_categories=("python-app", "docs"),
                risk_summary="medium",
            )
            state = build_workflow_surface_state(
                snapshot,
                repo_state=repo_state,
                workflow_preset_id="review_channel",
                swarm_health_label="Swarm Running",
            )

        self.assertIn("MP-355", state.current_slice)
        self.assertEqual(state.branch, "develop")
        self.assertEqual(state.current_writer, "Operator")
        self.assertEqual(state.swarm_health, "Swarm Running")
        self.assertEqual(len(state.stages), 7)
        self.assertTrue(state.next_action)
        stage_levels = {stage.stage_id: stage.status_level for stage in state.stages}
        self.assertEqual(stage_levels["posted"], "active")
        self.assertEqual(stage_levels["apply"], "warning")

    def test_parse_markdown_sections_reads_second_level_sections(self) -> None:
        sections = parse_markdown_sections(_bridge_text())
        self.assertEqual(sections["Poll Status"], "- active reviewer loop")
        self.assertEqual(sections["Claude Ack"], "- acknowledged")

    def test_load_pending_approvals_filters_pending_required_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "review_state.json"
            path.write_text(json.dumps(_review_state_json()), encoding="utf-8")
            approvals = load_pending_approvals(path)

        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0].packet_id, "pkt-1")
        self.assertEqual(approvals[0].requested_action, "git_push")
        self.assertEqual(len(approvals[0].context_pack_refs), 1)
        self.assertEqual(approvals[0].context_pack_refs[0].pack_kind, "task_pack")

    def test_find_review_state_path_prefers_canonical_projection_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            canonical = root / "dev/reports/review_channel/projections/latest/review_state.json"
            legacy = root / "dev/reports/review_channel/latest/review_state.json"
            canonical.parent.mkdir(parents=True, exist_ok=True)
            legacy.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text(json.dumps(_review_state_json()), encoding="utf-8")
            legacy.write_text("{}", encoding="utf-8")

            resolved = find_review_state_path(root)

        self.assertEqual(resolved, canonical)

    def test_find_review_full_path_prefers_canonical_projection_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            canonical = root / "dev/reports/review_channel/projections/latest/full.json"
            legacy = root / "dev/reports/review_channel/latest/full.json"
            canonical.parent.mkdir(parents=True, exist_ok=True)
            legacy.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text("{}", encoding="utf-8")
            legacy.write_text("{}", encoding="utf-8")

            resolved = find_review_full_path(root)

        self.assertEqual(resolved, canonical)

    def test_build_operator_console_snapshot_combines_bridge_and_review_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            review_state_path = root / "review_state.json"
            review_state_path.write_text(
                json.dumps(_review_state_json()),
                encoding="utf-8",
            )
            full_path = root / "dev/reports/review_channel/latest/full.json"
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(
                json.dumps(
                    {
                        "review": {
                            "surface_mode": "markdown-bridge",
                            "session_id": "markdown-bridge",
                            "active_lane": "review",
                        },
                        "agent_registry": {
                            "agents": [
                                {
                                    "agent_id": "AGENT-1",
                                    "display_name": "AGENT-1",
                                    "provider": "codex",
                                    "lane": "codex",
                                    "job_state": "active",
                                    "current_job": "Reviewing bridge hardening",
                                    "mp_scope": "`MP-355`",
                                    "worktree": "`../codex-voice-wt-a1`",
                                    "branch": "`feature/a1`",
                                },
                                {
                                    "agent_id": "AGENT-9",
                                    "display_name": "AGENT-9",
                                    "provider": "claude",
                                    "lane": "claude",
                                    "job_state": "assigned",
                                    "current_job": "Implementing UI follow-up",
                                    "mp_scope": "`MP-359`",
                                    "worktree": "`../codex-voice-wt-a9`",
                                    "branch": "`feature/a9`",
                                },
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )

            snapshot = build_operator_console_snapshot(
                root,
                review_state_path=review_state_path,
            )

        self.assertIn("Poll Status", snapshot.codex_panel_text)
        self.assertIn("Claude Status", snapshot.claude_panel_text)
        self.assertIn("Pending approvals:", snapshot.operator_panel_text)
        self.assertIn("\n1\n", snapshot.operator_panel_text)
        self.assertEqual(snapshot.last_codex_poll, "2026-03-08T20:00:00Z")
        self.assertEqual(len(snapshot.pending_approvals), 1)
        self.assertIn("live_terminal: unavailable", snapshot.codex_session_text)
        self.assertIn("AGENT-1 [active] Reviewing bridge hardening", snapshot.codex_session_registry_text)
        self.assertIn("source: review-channel projection + markdown bridge", snapshot.codex_session_stats_text)
        self.assertIn("live_terminal: unavailable", snapshot.claude_session_text)
        self.assertIn("AGENT-9 [assigned] Implementing UI follow-up", snapshot.claude_session_registry_text)

    def test_build_operator_console_snapshot_prefers_live_session_trace_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            review_state_path = root / "review_state.json"
            review_state_path.write_text(
                json.dumps(_review_state_json()),
                encoding="utf-8",
            )
            full_path = root / "dev/reports/review_channel/latest/full.json"
            sessions_dir = full_path.parent / "sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            full_path.write_text(
                json.dumps(
                    {
                        "review": {
                            "surface_mode": "markdown-bridge",
                            "session_id": "markdown-bridge",
                            "active_lane": "review",
                        },
                        "agent_registry": {
                            "agents": [
                                {
                                    "agent_id": "AGENT-1",
                                    "display_name": "AGENT-1",
                                    "provider": "codex",
                                    "lane": "codex",
                                    "job_state": "active",
                                    "current_job": "Reviewing bridge hardening",
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            (sessions_dir / "codex-conductor.json").write_text(
                json.dumps(
                    {
                        "provider": "codex",
                        "session_name": "codex-conductor",
                        "capture_mode": "terminal-script",
                        "prepared_at": "2026-03-09T10:00:00Z",
                        "log_path": str(sessions_dir / "codex-conductor.log"),
                    }
                ),
                encoding="utf-8",
            )
            (sessions_dir / "codex-conductor.log").write_text(
                "Script started on 2026-03-09 10:00:00 +0000\n"
                "\x1b[32mreview tail\x1b[0m\n"
                "readx\by\n",
                encoding="utf-8",
            )

            snapshot = build_operator_console_snapshot(
                root,
                review_state_path=review_state_path,
            )

        self.assertIn("source: live session trace", snapshot.codex_session_stats_text)
        self.assertIn("review tail", snapshot.codex_session_text)
        self.assertIn("ready", snapshot.codex_session_text)
        self.assertNotIn("Script started on", snapshot.codex_session_text)
        self.assertIn("source: review-channel projection + markdown bridge", snapshot.claude_session_stats_text)

    def test_build_operator_console_snapshot_prefers_rendered_screen_over_history_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            review_state_path = root / "review_state.json"
            review_state_path.write_text(
                json.dumps(_review_state_json()),
                encoding="utf-8",
            )
            full_path = root / "dev/reports/review_channel/latest/full.json"
            sessions_dir = full_path.parent / "sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            full_path.write_text("{}", encoding="utf-8")
            (sessions_dir / "codex-conductor.json").write_text(
                json.dumps(
                    {
                        "provider": "codex",
                        "session_name": "codex-conductor",
                        "capture_mode": "terminal-script",
                        "prepared_at": "2026-03-09T12:24:29Z",
                        "log_path": str(sessions_dir / "codex-conductor.log"),
                    }
                ),
                encoding="utf-8",
            )
            (sessions_dir / "codex-conductor.log").write_text(
                "Script started on 2026-03-09 12:24:29 +0000\n"
                "\x1b[2J"
                "\x1b[1;1HThis is a multi-agent conductor session"
                "\x1b[2;1H⏺ Reading 1 file… (ctrl+o to expand)"
                "\x1b[3;1H✶ Doing… (35s · ↓ 839 tokens)"
                "\x1b[4;1Hesc to interrupt"
                "\x1b[3;1H✻ Doing… (36s · ↓ 840 tokens)"
                "\x1b[2;1H⏺ Read 1 file (ctrl+o to expand)",
                encoding="utf-8",
            )

            snapshot = build_operator_console_snapshot(
                root,
                review_state_path=review_state_path,
            )

        self.assertIn("This is a multi-agent conductor session", snapshot.codex_session_text)
        self.assertIn("⏺ Read 1 file (ctrl+o to expand)", snapshot.codex_session_text)
        self.assertIn("✻ Doing… (36s · ↓ 840 tokens)", snapshot.codex_session_text)
        self.assertNotIn("⏺ Reading 1 file… (ctrl+o to expand)", snapshot.codex_session_text)
        self.assertNotIn("✶ Doing… (35s · ↓ 839 tokens)", snapshot.codex_session_text)

    def test_load_live_session_trace_reconstructs_terminal_screen(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sessions_dir = root / "dev/reports/review_channel/latest/sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            (sessions_dir / "claude-conductor.json").write_text(
                json.dumps(
                    {
                        "provider": "claude",
                        "session_name": "claude-conductor",
                        "capture_mode": "terminal-script",
                        "prepared_at": "2026-03-09T12:24:29Z",
                        "log_path": str(sessions_dir / "claude-conductor.log"),
                    }
                ),
                encoding="utf-8",
            )
            (sessions_dir / "claude-conductor.log").write_text(
                "Script started on 2026-03-09 12:24:29 +0000\n"
                "\x1b[2J"
                "\x1b[1;1HThis is a multi-agent conductor session"
                "\x1b[2;1HLet me bootstrap by reading the required documents."
                "\x1b[3;1H⏺ Reading 1 file… (ctrl+o to expand)"
                "\x1b[4;1H✶ Doing… (35s · ↓ 839 tokens)"
                "\x1b[5;1Hesc to interrupt"
                "\x1b[4;1H✻ Doing… (36s · ↓ 840 tokens)"
                "\x1b[3;1H⏺ Read 1 file (ctrl+o to expand)",
                encoding="utf-8",
            )

            snapshot = load_live_session_trace(root, provider="claude")

        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertIn("This is a multi-agent conductor session", snapshot.tail_text)
        self.assertIn("Let me bootstrap by reading the required documents.", snapshot.tail_text)
        self.assertIn("⏺ Read 1 file (ctrl+o to expand)", snapshot.tail_text)
        self.assertIn("✻ Doing… (36s · ↓ 840 tokens)", snapshot.tail_text)
        self.assertIn("esc to interrupt", snapshot.tail_text)
        self.assertNotIn("Script started on", snapshot.tail_text)
        self.assertNotIn("\x1b", snapshot.tail_text)
        self.assertIn("This is a multi-agent conductor session", snapshot.screen_text)
        self.assertIn("✻ Doing… (36s · ↓ 840 tokens)", snapshot.history_text)

    def test_load_live_session_trace_filters_spinner_noise_and_private_csi(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sessions_dir = root / "dev/reports/review_channel/latest/sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            (sessions_dir / "claude-conductor.json").write_text(
                json.dumps(
                    {
                        "provider": "claude",
                        "session_name": "claude-conductor",
                        "capture_mode": "terminal-script",
                        "prepared_at": "2026-03-09T12:24:29Z",
                        "lane_count": 8,
                        "worker_budget": 8,
                        "log_path": str(sessions_dir / "claude-conductor.log"),
                    }
                ),
                encoding="utf-8",
            )
            (sessions_dir / "claude-conductor.log").write_text(
                "Script started on 2026-03-09 12:24:29 +0000\n"
                "\x1b[>7u"
                "\x1b[2J"
                "\x1b[1;1H⏺ Update(code_audit.md)"
                "\x1b[2;1HGood - the test file exists!"
                "\x1b[3;1HContext left until auto-compact: 9%"
                "\x1b[4;1H✢ thinking with high effort"
                "\x1b[4;1H✳ thinking with high effort"
                "\x1b[5;1H✻ Thinking… (12m 16s · ↓ 22.2k tokens · thought for 7s)",
                encoding="utf-8",
            )

            snapshot = load_live_session_trace(root, provider="claude")

        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(snapshot.lane_count, 8)
        self.assertEqual(snapshot.worker_budget, 8)
        self.assertIn("Good - the test file exists!", snapshot.history_text)
        self.assertIn("Context left until auto-compact: 9%", snapshot.history_text)
        self.assertNotIn("thinking with high effort", snapshot.history_text.lower())

    def test_load_live_session_trace_drops_partial_prefix_when_tail_is_truncated(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sessions_dir = root / "dev/reports/review_channel/latest/sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            (sessions_dir / "claude-conductor.json").write_text(
                json.dumps(
                    {
                        "provider": "claude",
                        "session_name": "claude-conductor",
                        "capture_mode": "terminal-script",
                        "prepared_at": "2026-03-09T12:24:29Z",
                        "log_path": str(sessions_dir / "claude-conductor.log"),
                    }
                ),
                encoding="utf-8",
            )
            prefix = ("partial-prefix-noise;" * 32) + "\n"
            (sessions_dir / "claude-conductor.log").write_text(
                prefix
                + "Script started on 2026-03-09 12:24:29 +0000\n"
                + "\x1b[2J"
                + "\x1b[1;1Hhealthy rendered line"
                + "\x1b[2;1Hsecond rendered line",
                encoding="utf-8",
            )

            snapshot = load_live_session_trace(root, provider="claude", max_bytes=96)

        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertIn("healthy rendered line", snapshot.screen_text)
        self.assertNotIn("partial-prefix-noise", snapshot.history_text)
        self.assertNotIn("partial-prefix-noise", snapshot.screen_text)

    def test_record_operator_decision_writes_latest_and_timestamped_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            approval = ApprovalRequest(
                packet_id="pkt-1",
                from_agent="codex",
                to_agent="operator",
                summary="Approve guarded push",
                body="Need operator approval before push.",
                policy_hint="operator_approval_required",
                requested_action="git_push",
                status="pending",
                evidence_refs=("code_audit.md#L1",),
                context_pack_refs=(
                    ContextPackRef(
                        pack_kind="task_pack",
                        pack_ref=".voiceterm/memory/exports/task_pack.json",
                        adapter_profile="canonical",
                    ),
                ),
            )
            artifact = record_operator_decision(
                root,
                approval=approval,
                decision="approve",
                note="Approved for this one push only.",
            )

            latest = json.loads(Path(artifact.latest_json_path).read_text(encoding="utf-8"))
            latest_markdown = Path(artifact.latest_markdown_path).read_text(
                encoding="utf-8"
            )

        self.assertEqual(latest["decision"], "approve")
        self.assertEqual(latest["packet_id"], "pkt-1")
        self.assertEqual(latest["context_pack_refs"][0]["pack_kind"], "task_pack")
        self.assertIn("one push only", latest_markdown)
        self.assertIn("Context Pack Refs", latest_markdown)

    def test_atomic_write_text_produces_correct_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "test.json"
            _atomic_write_text(target, '{"key": "value"}')
            self.assertEqual(target.read_text(encoding="utf-8"), '{"key": "value"}')

    def test_atomic_write_text_overwrites_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "test.txt"
            target.write_text("old content", encoding="utf-8")
            _atomic_write_text(target, "new content")
            self.assertEqual(target.read_text(encoding="utf-8"), "new content")

    def test_atomic_write_text_leaves_no_temp_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "test.txt"
            _atomic_write_text(target, "data")
            remaining = list(Path(tmpdir).iterdir())
            self.assertEqual(remaining, [target])


class StructuredLaneTests(unittest.TestCase):
    def test_codex_lane_active_when_poll_status_says_active(self) -> None:
        sections = parse_markdown_sections(_bridge_text())
        lane = build_codex_lane(sections, "2026-03-08T20:00:00Z", "abc123")
        self.assertEqual(lane.provider_name, "Codex")
        self.assertEqual(lane.lane_title, "Codex Bridge Monitor")
        self.assertEqual(lane.role_label, "Reviewer")
        self.assertEqual(lane.status_hint, "active")
        self.assertTrue(len(lane.rows) >= 3)

    def test_codex_lane_idle_when_poll_status_missing(self) -> None:
        lane = build_codex_lane({}, None, None)
        self.assertEqual(lane.status_hint, "idle")

    def test_codex_lane_waiting_state_survives_fresh_live_trace(self) -> None:
        sections = {
            "Poll Status": "- waiting for operator approval",
            "Current Verdict": "- still in progress",
            "Open Findings": "- pending operator decision",
        }
        lane = build_codex_lane(
            sections,
            _fresh_timestamp(),
            "abc123",
            live_trace=_fresh_live_trace("codex"),
        )

        self.assertEqual(lane.status_hint, "warning")
        self.assertEqual(lane.state_label, "Waiting")
        self.assertEqual(dict(lane.rows)["Session"], "codex-conductor [live]")

    def test_claude_lane_warning_when_paused(self) -> None:
        sections = {"Claude Status": "- coding paused", "Claude Questions": "", "Claude Ack": ""}
        lane = build_claude_lane(sections)
        self.assertEqual(lane.status_hint, "warning")

    def test_claude_lane_active_when_coding(self) -> None:
        sections = {"Claude Status": "- coding in progress", "Claude Questions": "", "Claude Ack": ""}
        lane = build_claude_lane(sections)
        self.assertEqual(lane.status_hint, "active")

    def test_claude_lane_blocked_state_survives_fresh_live_trace(self) -> None:
        sections = {
            "Claude Status": "- blocked on codex review feedback",
            "Claude Questions": "- should I wait?",
            "Claude Ack": "- pausing until reviewer responds",
        }
        lane = build_claude_lane(
            sections,
            live_trace=_fresh_live_trace("claude"),
        )

        self.assertEqual(lane.status_hint, "warning")
        self.assertEqual(lane.state_label, "Blocked")
        self.assertEqual(dict(lane.rows)["Session"], "claude-conductor [live]")

    def test_cursor_lane_active_when_live_trace_is_present(self) -> None:
        lane = build_cursor_lane(
            {
                "Cursor Status": "- editing focused files",
                "Cursor Focus": "- app/operator_console/state/snapshot_builder.py",
            },
            live_trace=_fresh_live_trace("cursor"),
        )

        self.assertEqual(lane.provider_name, "Cursor")
        self.assertEqual(lane.role_label, "Editor")
        self.assertEqual(lane.status_hint, "active")
        self.assertEqual(lane.state_label, "Editing")
        self.assertEqual(dict(lane.rows)["Session"], "cursor-conductor [live]")

    def test_operator_lane_warning_when_approvals_pending(self) -> None:
        approval = ApprovalRequest(
            packet_id="pkt-1", from_agent="codex", to_agent="operator",
            summary="test", body="", policy_hint="required",
            requested_action="push", status="pending",
        )
        lane = build_operator_lane({}, (approval,), None)
        self.assertEqual(lane.status_hint, "warning")
        # The rows should include the approval count
        rows_dict = dict(lane.rows)
        self.assertEqual(rows_dict.get("Approvals"), "1")

    def test_operator_lane_active_when_no_approvals(self) -> None:
        lane = build_operator_lane({}, (), None)
        self.assertEqual(lane.status_hint, "active")

    def test_snapshot_includes_structured_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            snapshot = build_operator_console_snapshot(root)

        self.assertIsNotNone(snapshot.codex_lane)
        self.assertIsNotNone(snapshot.claude_lane)
        self.assertIsNotNone(snapshot.cursor_lane)
        self.assertIsNotNone(snapshot.operator_lane)
        self.assertEqual(snapshot.codex_lane.provider_name, "Codex")
        self.assertEqual(snapshot.claude_lane.provider_name, "Claude")
        self.assertEqual(snapshot.cursor_lane.provider_name, "Cursor")
        self.assertEqual(snapshot.operator_lane.provider_name, "Operator")


class CommandBuilderTests(unittest.TestCase):
    def test_commands_use_canonical_entrypoint_constants(self) -> None:
        launch_cmd = build_launch_command(live=False)
        self.assertEqual(launch_cmd[0], DEVCTL_PYTHON)
        self.assertEqual(launch_cmd[1], DEVCTL_ENTRYPOINT)
        self.assertEqual(launch_cmd[2], REVIEW_CHANNEL_SUBCOMMAND)

        rollover_cmd = build_rollover_command(
            threshold_pct=50, await_ack_seconds=180, live=True
        )
        self.assertEqual(rollover_cmd[0], DEVCTL_PYTHON)
        self.assertEqual(rollover_cmd[1], DEVCTL_ENTRYPOINT)
        self.assertEqual(rollover_cmd[2], REVIEW_CHANNEL_SUBCOMMAND)

    def test_build_launch_command_supports_dry_run_and_live(self) -> None:
        self.assertIn("--dry-run", build_launch_command(live=False))
        self.assertNotIn("--dry-run", build_launch_command(live=True))
        self.assertIn(
            "--refresh-bridge-heartbeat-if-stale",
            build_launch_command(
                live=False,
                refresh_bridge_heartbeat_if_stale=True,
            ),
        )

    def test_terminal_app_live_support_is_platform_specific(self) -> None:
        self.assertTrue(terminal_app_live_supported(platform_name="darwin"))
        self.assertFalse(terminal_app_live_supported(platform_name="linux"))
        self.assertIn(
            "current platform: linux",
            terminal_app_live_support_detail(platform_name="linux"),
        )
        self.assertIn(
            "Terminal.app",
            terminal_app_live_support_detail(platform_name="darwin"),
        )

    def test_build_rollover_command_validates_thresholds(self) -> None:
        with self.assertRaises(ValueError):
            build_rollover_command(
                threshold_pct=0,
                await_ack_seconds=180,
                live=True,
            )

    def test_build_status_command_includes_ci_flags(self) -> None:
        command = build_status_command(include_ci=True, require_ci=True)
        self.assertEqual(command[:3], [DEVCTL_PYTHON, DEVCTL_ENTRYPOINT, "status"])
        self.assertIn("--ci", command)
        self.assertIn("--require-ci", command)

    def test_build_triage_command_can_request_ci_context(self) -> None:
        command = build_triage_command(include_ci=True)
        self.assertEqual(command[:3], [DEVCTL_PYTHON, DEVCTL_ENTRYPOINT, "triage"])
        self.assertIn("--ci", command)
        self.assertIn("--format", command)

    def test_build_process_audit_command_supports_strict_mode(self) -> None:
        command = build_process_audit_command(strict=True)
        self.assertEqual(
            command[:3], [DEVCTL_PYTHON, DEVCTL_ENTRYPOINT, "process-audit"]
        )
        self.assertIn("--strict", command)

    def test_build_orchestrate_status_command_uses_repo_owned_entrypoint(self) -> None:
        command = build_orchestrate_status_command(output_format="json")
        self.assertEqual(
            command[:3], [DEVCTL_PYTHON, DEVCTL_ENTRYPOINT, "orchestrate-status"]
        )
        self.assertEqual(command[-2:], ["--format", "json"])

    def test_build_review_channel_post_command_supports_finding_packets(self) -> None:
        command = build_review_channel_post_command(
            to_agent="codex",
            summary="Quality finding packet",
            body="critical hotspot",
            kind="finding",
            output_format="json",
        )
        self.assertEqual(
            command[:3],
            [DEVCTL_PYTHON, DEVCTL_ENTRYPOINT, REVIEW_CHANNEL_SUBCOMMAND],
        )
        self.assertIn("--kind", command)
        self.assertIn("finding", command)

    def test_build_swarm_run_command_uses_selected_plan_scope(self) -> None:
        command = build_swarm_run_command(
            plan_doc="dev/active/continuous_swarm.md",
            mp_scope="MP-358",
            output_format="json",
            continuous=True,
            continuous_max_cycles=5,
            feedback_sizing=True,
        )
        self.assertEqual(command[:3], [DEVCTL_PYTHON, DEVCTL_ENTRYPOINT, "swarm_run"])
        self.assertIn("--plan-doc", command)
        self.assertIn("dev/active/continuous_swarm.md", command)
        self.assertIn("--mp-scope", command)
        self.assertIn("MP-358", command)
        self.assertIn("--continuous", command)
        self.assertIn("--feedback-sizing", command)

    def test_build_operator_decision_command_uses_typed_module_entrypoint(self) -> None:
        approval = ApprovalRequest(
            packet_id="pkt-1",
            from_agent="codex",
            to_agent="operator",
            summary="Approve guarded push",
            body="Need operator approval before push.",
            policy_hint="operator_approval_required",
            requested_action="git_push",
            status="pending",
            evidence_refs=("code_audit.md#L1",),
            context_pack_refs=(
                ContextPackRef(
                    pack_kind="task_pack",
                    pack_ref=".voiceterm/memory/exports/task_pack.json",
                    adapter_profile="canonical",
                ),
            ),
        )

        command = build_operator_decision_command(
            approval=approval,
            decision="deny",
            note="Hold this until CI is green.",
        )

        self.assertEqual(command[:3], [DEVCTL_PYTHON, "-m", OPERATOR_DECISION_MODULE])
        self.assertIn("--decision", command)
        self.assertIn("deny", command)
        self.assertIn("--repo-root", command)
        approval_json = command[command.index("--approval-json") + 1]
        payload = json.loads(approval_json)
        self.assertEqual(payload["packet_id"], "pkt-1")
        self.assertEqual(payload["evidence_refs"], ["code_audit.md#L1"])
        self.assertEqual(payload["context_pack_refs"][0]["pack_kind"], "task_pack")

    def test_render_command_returns_shell_string(self) -> None:
        rendered = render_command(build_rollover_command(
            threshold_pct=80,
            await_ack_seconds=90,
            live=False,
        ))
        self.assertIn("--rollover-threshold-pct 80", rendered)
        self.assertIn("--dry-run", rendered)

    def test_parse_review_channel_report_reads_json_object(self) -> None:
        report = parse_review_channel_report('{"ok": true, "bridge_active": true}')
        self.assertTrue(report["ok"])
        self.assertTrue(report["bridge_active"])

    def test_parse_review_channel_report_rejects_invalid_payloads(self) -> None:
        with self.assertRaises(ValueError):
            parse_review_channel_report("not-json")
        with self.assertRaises(ValueError):
            parse_review_channel_report('["not", "an", "object"]')

    def test_parse_orchestrate_status_report_rejects_invalid_payloads(self) -> None:
        with self.assertRaises(ValueError):
            parse_orchestrate_status_report("not-json")
        with self.assertRaises(ValueError):
            parse_orchestrate_status_report('["not", "an", "object"]')

    def test_parse_swarm_run_report_rejects_invalid_payloads(self) -> None:
        with self.assertRaises(ValueError):
            parse_swarm_run_report("not-json")
        with self.assertRaises(ValueError):
            parse_swarm_run_report('["not", "an", "object"]')

    def test_parse_operator_decision_report_rejects_invalid_payloads(self) -> None:
        with self.assertRaises(ValueError):
            parse_operator_decision_report("not-json")
        with self.assertRaises(ValueError):
            parse_operator_decision_report('["not", "an", "object"]')

    def test_evaluate_start_swarm_preflight_requires_bridge_and_lanes(self) -> None:
        ok, message = evaluate_start_swarm_preflight(
            {
                "ok": True,
                "bridge_active": True,
                "codex_lane_count": 2,
                "claude_lane_count": 1,
            }
        )
        self.assertTrue(ok)
        self.assertIn("Preflight ok", message)

        ok, message = evaluate_start_swarm_preflight(
            {
                "ok": True,
                "bridge_active": False,
                "codex_lane_count": 2,
                "claude_lane_count": 1,
            }
        )
        self.assertFalse(ok)
        self.assertIn("bridge is inactive", message)

    def test_evaluate_start_swarm_launch_requires_live_sessions(self) -> None:
        ok, message = evaluate_start_swarm_launch(
            {
                "ok": True,
                "launched": True,
                "codex_lane_count": 2,
                "claude_lane_count": 2,
            }
        )
        self.assertTrue(ok)
        self.assertIn("Swarm started", message)

    def test_evaluate_review_channel_launch_reports_guard_failures(self) -> None:
        ok, message = evaluate_review_channel_launch(
            {
                "ok": False,
                "errors": ["bridge guard is stale"],
            },
            live=True,
        )
        self.assertFalse(ok)
        self.assertEqual(message, "bridge guard is stale")

    def test_evaluate_review_channel_launch_reports_live_success(self) -> None:
        ok, message = evaluate_review_channel_launch(
            {
                "ok": True,
                "launched": True,
                "codex_lane_count": 2,
                "claude_lane_count": 1,
            },
            live=True,
        )
        self.assertTrue(ok)
        self.assertIn("Live launch started", message)

    def test_evaluate_review_channel_rollover_reports_ack_state(self) -> None:
        ok, message = evaluate_review_channel_rollover(
            {
                "ok": True,
                "handoff_ack_required": True,
                "handoff_ack_observed": True,
            }
        )
        self.assertTrue(ok)
        self.assertIn("ACK was observed", message)

    def test_evaluate_orchestrate_status_report_surfaces_sync_status(self) -> None:
        ok, message = evaluate_orchestrate_status_report(
            {
                "ok": True,
                "git": {"branch": "feature/test", "changed_count": 7},
                "warnings": [],
            }
        )
        self.assertTrue(ok)
        self.assertIn("active-plan sync", message)
        self.assertIn("feature/test", message)

    def test_evaluate_swarm_run_report_summarizes_continuous_run(self) -> None:
        ok, message = evaluate_swarm_run_report(
            {
                "ok": True,
                "mp_scope": "MP-359",
                "run_dir": "dev/reports/autonomy/runs/mock-run",
                "next_steps": ["Refactor workflow launchpad"],
                "continuous": {
                    "cycles_completed": 3,
                    "max_cycles": 10,
                    "stop_reason": "max_cycles_reached",
                },
            }
        )
        self.assertTrue(ok)
        self.assertIn("3/10 cycles", message)
        self.assertIn("Refactor workflow launchpad", message)
        self.assertIn("mock-run", message)


class WorkflowPresetTests(unittest.TestCase):
    def test_default_workflow_preset_is_operator_console(self) -> None:
        self.assertEqual(DEFAULT_WORKFLOW_PRESET_ID, "operator_console")
        self.assertEqual(resolve_workflow_preset(DEFAULT_WORKFLOW_PRESET_ID).mp_scope, "MP-359")

    def test_available_workflow_presets_include_multiple_active_plan_scopes(self) -> None:
        preset_ids = {preset.preset_id for preset in available_workflow_presets()}
        self.assertIn("operator_console", preset_ids)
        self.assertIn("continuous_swarm", preset_ids)
        self.assertIn("review_channel", preset_ids)

    def test_operator_decision_main_writes_json_report(self) -> None:
        approval = ApprovalRequest(
            packet_id="pkt-7",
            from_agent="codex",
            to_agent="operator",
            summary="Approve guarded push",
            body="Need operator approval before push.",
            policy_hint="operator_approval_required",
            requested_action="git_push",
            status="pending",
            evidence_refs=("code_audit.md#L1",),
            context_pack_refs=(
                ContextPackRef(
                    pack_kind="task_pack",
                    pack_ref=".voiceterm/memory/exports/task_pack.json",
                    adapter_profile="canonical",
                ),
            ),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = operator_decisions_main(
                    [
                        "--repo-root",
                        tmpdir,
                        "--decision",
                        "approve",
                        "--approval-json",
                        json.dumps(
                            {
                                "packet_id": approval.packet_id,
                                "from_agent": approval.from_agent,
                                "to_agent": approval.to_agent,
                                "summary": approval.summary,
                                "body": approval.body,
                                "policy_hint": approval.policy_hint,
                                "requested_action": approval.requested_action,
                                "status": approval.status,
                                "evidence_refs": list(approval.evidence_refs),
                                "context_pack_refs": [
                                    {
                                        "pack_kind": ref.pack_kind,
                                        "pack_ref": ref.pack_ref,
                                        "adapter_profile": ref.adapter_profile,
                                    }
                                    for ref in approval.context_pack_refs
                                ],
                            }
                        ),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(rc, 0)
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["decision"], "approve")
            self.assertEqual(payload["packet_id"], "pkt-7")
            self.assertEqual(payload["typed_action_mode"], "wrapper_artifact_command")
            self.assertFalse(payload["devctl_review_channel_action_available"])
            artifact = payload["artifact"]
            self.assertTrue(Path(artifact["latest_json_path"]).exists())
            latest = json.loads(
                Path(artifact["latest_json_path"]).read_text(encoding="utf-8")
            )
            self.assertEqual(latest["context_pack_refs"][0]["pack_kind"], "task_pack")

    def test_operator_decision_main_reports_invalid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = operator_decisions_main(
                    [
                        "--repo-root",
                        tmpdir,
                        "--decision",
                        "approve",
                        "--approval-json",
                        '{"packet_id": "pkt-9"}',
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(rc, 1)
            payload = json.loads(stdout.getvalue())
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["reason"], "operator_decision_failed")

        ok, message = evaluate_start_swarm_launch(
            {
                "ok": True,
                "launched": False,
                "codex_lane_count": 2,
                "claude_lane_count": 2,
            }
        )
        self.assertFalse(ok)
        self.assertIn("did not open", message)


class ActivityAssistTests(unittest.TestCase):
    def test_build_audit_draft_includes_observed_snapshot_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            review_state_path = root / "review_state.json"
            review_state_path.write_text(
                json.dumps(_review_state_json()),
                encoding="utf-8",
            )
            snapshot = build_operator_console_snapshot(
                root,
                review_state_path=review_state_path,
            )

        draft = build_assist_draft(snapshot, mode="audit")
        self.assertEqual(draft.mode, "audit")
        self.assertIn("Pending approvals: 1", draft.body)
        self.assertIn("Worktree hash: abc123", draft.body)
        self.assertIn("Structured review_state:", draft.body)

    def test_build_help_draft_mentions_operator_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            snapshot = build_operator_console_snapshot(root)

        draft = build_assist_draft(snapshot, mode="help")
        self.assertEqual(draft.mode, "help")
        self.assertIn("what the operator should do next", draft.body)
        self.assertIn("Codex (Reviewer)", draft.body)

    def test_build_assist_draft_rejects_unknown_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            snapshot = build_operator_console_snapshot(root)

        with self.assertRaises(ValueError):
            build_assist_draft(snapshot, mode="unknown")

    def test_build_summary_draft_targets_selected_provider_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            snapshot = build_operator_console_snapshot(root)

        draft = build_summary_draft(
            snapshot,
            report_id="claude",
            provider_id="claude",
        )
        self.assertEqual(draft.mode, "summary")
        self.assertIn("Claude Draft", draft.title)
        self.assertIn("Selected report: Claude Report", draft.body)
        self.assertIn("Target provider: Claude Draft", " | ".join(draft.provenance))


class ActivityReportTests(unittest.TestCase):
    def test_build_activity_report_overview_summarizes_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            snapshot = build_operator_console_snapshot(root)

        report = build_activity_report(snapshot, report_id="overview")
        self.assertEqual(report.report_id, "overview")
        self.assertIn("Recommended next step", report.body)
        self.assertIn("review loop", report.summary.lower())

    def test_build_activity_report_technical_mode_keeps_signal_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            snapshot = build_operator_console_snapshot(root)

        report = build_activity_report(
            snapshot,
            report_id="overview",
            audience_mode="technical",
        )
        self.assertIn("Signals used", report.body)

    def test_build_activity_report_simple_mode_marks_plain_language_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            snapshot = build_operator_console_snapshot(root)

        report = build_activity_report(
            snapshot,
            report_id="overview",
            audience_mode="simple",
        )
        self.assertIn("Plain-language snapshot", report.body)
        self.assertIn("Read mode: Simple", report.body)

    def test_build_activity_report_approvals_mentions_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            review_state_path = root / "review_state.json"
            review_state_path.write_text(
                json.dumps(_review_state_json()),
                encoding="utf-8",
            )
            snapshot = build_operator_console_snapshot(
                root,
                review_state_path=review_state_path,
            )

        report = build_activity_report(snapshot, report_id="approvals")
        self.assertIn("1 pending approval", report.body)
        self.assertIn("Approve guarded push", report.body)

    def test_build_summary_draft_respects_selected_audience_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            snapshot = build_operator_console_snapshot(root)

        draft = build_summary_draft(
            snapshot,
            report_id="overview",
            provider_id="codex",
            audience_mode="technical",
        )
        self.assertIn("Signals used", draft.body)

    def test_build_activity_report_quality_clean_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            snapshot = build_operator_console_snapshot(root)

        report = build_activity_report(snapshot, report_id="quality")
        self.assertEqual(report.report_id, "quality")
        self.assertEqual(report.title, "Quality Backlog")
        self.assertIn("Recommended next step", report.body)
        self.assertIn("quality", report.summary.lower())

    def test_build_activity_report_quality_technical_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            snapshot = build_operator_console_snapshot(root)

        report = build_activity_report(
            snapshot, report_id="quality", audience_mode="technical",
        )
        self.assertIn("Guard pipeline coverage", report.body)
        self.assertIn("code_shape", report.body)
        self.assertIn("rust_security_footguns", report.body)

    def test_build_activity_report_quality_simple_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            snapshot = build_operator_console_snapshot(root)

        report = build_activity_report(
            snapshot, report_id="quality", audience_mode="simple",
        )
        self.assertIn("quality signals visible right now", report.body.lower())
        self.assertIn("devctl report command", report.body)

    def test_build_activity_report_quality_includes_live_backlog_snapshot(self) -> None:
        snapshot = OperatorConsoleSnapshot(
            codex_panel_text="",
            claude_panel_text="",
            operator_panel_text="",
            codex_session_text="",
            claude_session_text="",
            raw_bridge_text="",
            review_mode="markdown-only",
            last_codex_poll="2026-03-08T20:00:00Z",
            last_worktree_hash="abc123",
            pending_approvals=(),
            warnings=(),
            review_state_path=None,
            codex_lane=None,
            claude_lane=None,
            operator_lane=None,
            quality_backlog=QualityBacklogSnapshot(
                captured_at_utc="2026-03-09T00:00:00Z",
                ok=False,
                source_files_scanned=20,
                guard_failures=3,
                critical_paths=1,
                high_paths=2,
                medium_paths=1,
                low_paths=0,
                ranked_paths=4,
                failing_checks=("code_shape", "rust_best_practices"),
                top_priorities=(
                    QualityPrioritySignal(
                        path="app/operator_console/views/main_window.py",
                        severity="critical",
                        score=740,
                        signals=("shape:soft",),
                    ),
                ),
            ),
        )

        report = build_activity_report(snapshot, report_id="quality", audience_mode="technical")

        self.assertIn("Guard failures: 3", report.body)
        self.assertIn("Top scored hotspots:", report.body)
        self.assertIn("main_window.py", report.body)

    def test_build_activity_report_quality_with_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "code_audit.md").write_text(_bridge_text(), encoding="utf-8")
            review_state_path = root / "review_state.json"
            review_state_path.write_text(
                json.dumps(_review_state_json()),
                encoding="utf-8",
            )
            snapshot = build_operator_console_snapshot(
                root,
                review_state_path=review_state_path,
            )

        report = build_activity_report(snapshot, report_id="quality")
        self.assertIn("quality signal", report.summary)
        self.assertIn("Recommended next step", report.body)

    def test_resolve_report_option_quality(self) -> None:
        option = resolve_report_option("quality")
        self.assertEqual(option.report_id, "quality")
        self.assertEqual(option.label, "Quality Backlog")

    def test_resolve_report_option_falls_back_to_overview(self) -> None:
        option = resolve_report_option("missing")
        self.assertEqual(option.report_id, "overview")


if __name__ == "__main__":
    unittest.main()
