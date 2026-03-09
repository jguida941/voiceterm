from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from app.operator_console.state.activity_assist import (
    build_assist_draft,
    build_summary_draft,
)
from app.operator_console.state.activity_reports import (
    build_activity_report,
    resolve_report_option,
)
from app.operator_console.state.command_builder import (
    DEVCTL_ENTRYPOINT,
    OPERATOR_DECISION_MODULE,
    DEVCTL_PYTHON,
    REVIEW_CHANNEL_SUBCOMMAND,
    build_launch_command,
    build_operator_decision_command,
    build_process_audit_command,
    build_rollover_command,
    build_status_command,
    build_triage_command,
    evaluate_start_swarm_launch,
    evaluate_start_swarm_preflight,
    parse_operator_decision_report,
    parse_review_channel_report,
    render_command,
    terminal_app_live_support_detail,
    terminal_app_live_supported,
)
from app.operator_console.state.bridge_sections import parse_markdown_sections
from app.operator_console.state.lane_builder import (
    build_claude_lane,
    build_codex_lane,
    build_operator_lane,
)
from app.operator_console.state.models import ApprovalRequest
from app.operator_console.state.operator_decisions import (
    _atomic_write_text,
    main as operator_decisions_main,
    record_operator_decision,
)
from app.operator_console.state.review_state import (
    find_review_full_path,
    find_review_state_path,
    load_pending_approvals,
)
from app.operator_console.state.snapshot_builder import (
    build_operator_console_snapshot,
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
            }
        ]
    }


class StateModuleTests(unittest.TestCase):
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
        self.assertIn("CODEX SESSION", snapshot.codex_session_text)
        self.assertIn("AGENT-1 [active] Reviewing bridge hardening", snapshot.codex_session_text)
        self.assertIn("CLAUDE SESSION", snapshot.claude_session_text)
        self.assertIn("AGENT-9 [assigned] Implementing UI follow-up", snapshot.claude_session_text)

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

        self.assertIn("source: live session trace", snapshot.codex_session_text)
        self.assertIn("review tail", snapshot.codex_session_text)
        self.assertIn("ready", snapshot.codex_session_text)
        self.assertNotIn("Script started on", snapshot.codex_session_text)
        self.assertIn("source: review-channel projection + markdown bridge", snapshot.claude_session_text)

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
        self.assertIn("one push only", latest_markdown)

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

    def test_claude_lane_warning_when_paused(self) -> None:
        sections = {"Claude Status": "- coding paused", "Claude Questions": "", "Claude Ack": ""}
        lane = build_claude_lane(sections)
        self.assertEqual(lane.status_hint, "warning")

    def test_claude_lane_active_when_coding(self) -> None:
        sections = {"Claude Status": "- coding in progress", "Claude Questions": "", "Claude Ack": ""}
        lane = build_claude_lane(sections)
        self.assertEqual(lane.status_hint, "active")

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
        self.assertIsNotNone(snapshot.operator_lane)
        self.assertEqual(snapshot.codex_lane.provider_name, "Codex")
        self.assertEqual(snapshot.claude_lane.provider_name, "Claude")
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

    def test_resolve_report_option_falls_back_to_overview(self) -> None:
        option = resolve_report_option("missing")
        self.assertEqual(option.report_id, "overview")


if __name__ == "__main__":
    unittest.main()
