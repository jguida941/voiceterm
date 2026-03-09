"""Tests for the transitional review-channel launcher.

Fixtures in this file model the same markdown authorities the launcher reads:
`dev/active/review_channel.md` and `code_audit.md`.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import review_channel as review_channel_command
from dev.scripts.devctl.review_channel import (
    DEFAULT_ROLLOVER_ACK_WAIT_SECONDS,
    DEFAULT_ROLLOVER_THRESHOLD_PCT,
    DEFAULT_TERMINAL_PROFILE,
    LaneAssignment,
    REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
    bridge_is_active,
    parse_lane_assignments,
    resolve_terminal_profile_name,
)
from dev.scripts.devctl.review_channel_handoff import (
    extract_bridge_snapshot,
    expected_rollover_ack_line,
    observe_rollover_ack_state,
    summarize_bridge_liveness,
    validate_launch_bridge_state,
)


def _build_review_channel_text(*, include_bridge: bool = True) -> str:
    if not include_bridge:
        return "\n".join(
            [
                "# Review Channel + Shared Screen Plan",
                "",
                "## Structured Review Channel (Planned Mode)",
                "",
                "The markdown bridge has been retired for this scenario.",
            ]
        )
    bridge_heading = "## Transitional Markdown Bridge (Current Operating Mode)"
    rows = [
        "| Agent | Lane | Primary active docs | MP scope | Worktree | Branch |",
        "|---|---|---|---|---|---|",
        "| `AGENT-1` | Codex architecture contract review | `dev/active/review_channel.md` | `MP-340, MP-355` | `../codex-voice-wt-a1` | `feature/a1` |",
        "| `AGENT-2` | Codex clean-code and state-boundary review | `dev/active/review_channel.md` | `MP-267, MP-355` | `../codex-voice-wt-a2` | `feature/a2` |",
        "| `AGENT-3` | Codex runtime and handoff review | `dev/active/review_channel.md` | `MP-233, MP-355` | `../codex-voice-wt-a3` | `feature/a3` |",
        "| `AGENT-4` | Codex CI and workflow reviewer | `dev/active/review_channel.md` | `MP-297, MP-355` | `../codex-voice-wt-a4` | `feature/a4` |",
        "| `AGENT-5` | Codex devctl and process-hygiene reviewer | `dev/active/review_channel.md` | `MP-300, MP-356` | `../codex-voice-wt-a5` | `feature/a5` |",
        "| `AGENT-6` | Codex overlay and UX reviewer | `dev/active/review_channel.md` | `MP-340, MP-355` | `../codex-voice-wt-a6` | `feature/a6` |",
        "| `AGENT-7` | Codex guard and test reviewer | `dev/active/review_channel.md` | `MP-303, MP-355` | `../codex-voice-wt-a7` | `feature/a7` |",
        "| `AGENT-8` | Codex integration and re-review loop | `dev/active/review_channel.md` | `MP-340, MP-355` | `../codex-voice-wt-a8` | `feature/a8` |",
        "| `AGENT-9` | Claude bridge push-safety fixes | `dev/active/review_channel.md` | `MP-303, MP-355` | `../codex-voice-wt-a9` | `feature/a9` |",
        "| `AGENT-10` | Claude live Git-context fixes | `dev/active/review_channel.md` | `MP-340, MP-355` | `../codex-voice-wt-a10` | `feature/a10` |",
        "| `AGENT-11` | Claude refresh, redraw, and footer fixes | `dev/active/review_channel.md` | `MP-340, MP-355` | `../codex-voice-wt-a11` | `feature/a11` |",
        "| `AGENT-12` | Claude broker and clipboard fixes | `dev/active/review_channel.md` | `MP-340, MP-355` | `../codex-voice-wt-a12` | `feature/a12` |",
        "| `AGENT-13` | Claude handoff and bootstrap fixes | `dev/active/review_channel.md` | `MP-243, MP-355` | `../codex-voice-wt-a13` | `feature/a13` |",
        "| `AGENT-14` | Claude workflow and publication-sync fixes | `dev/active/review_channel.md` | `MP-300, MP-355` | `../codex-voice-wt-a14` | `feature/a14` |",
        "| `AGENT-15` | Claude clean-code refactors | `dev/active/review_channel.md` | `MP-267, MP-355` | `../codex-voice-wt-a15` | `feature/a15` |",
        "| `AGENT-16` | Claude proof and regression closure | `dev/active/review_channel.md` | `MP-303, MP-356` | `../codex-voice-wt-a16` | `feature/a16` |",
    ]
    return "\n".join(
        [
            "# Review Channel + Shared Screen Plan",
            "",
            bridge_heading,
            "",
            "`code_audit.md` is the temporary bridge.",
            "In autonomous mode `MASTER_PLAN.md` remains the canonical tracker and",
            "   `INDEX.md` remains the router for the minimal active docs set.",
            "For the current operator-facing loop, each meaningful Codex reviewer write to",
            "   `code_audit.md` must also emit a concise operator-visible chat update.",
            "Bridge writes stay conductor-owned: only one Codex conductor updates the Codex-owned bridge",
            "sections while specialist workers report back instead of editing the bridge directly.",
            "The reviewer should emit an operator-visible",
            "heartbeat every five minutes even when the blocker set is unchanged.",
            "Default multi-agent wakeups should be change-routed instead of brute-force.",
            "The header should expose `last_poll_local` for the operator.",
            "Until the structured path lands, `check_review_channel_bridge.py` guards this bridge.",
            "The repo-native continuous fallback is `devctl swarm_run --continuous`.",
            "Completion stall is a named failure mode that the bridge must prevent.",
            "",
            "## 0) Current Execution Mode",
            "",
            *rows,
            "",
        ]
    )


def _build_bridge_text(
    *,
    last_codex_poll: str | None = None,
    current_instruction: str = "- stop at a safe boundary and relaunch before compaction",
    claude_status: str = "- coding handoff fixes",
    claude_ack: str = "- acknowledged",
) -> str:
    if last_codex_poll is None:
        last_codex_poll = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return "\n".join(
        [
            "# Code Audit Channel",
            "",
            "## Start-Of-Conversation Rules",
            "",
            "Codex is the reviewer. Claude is the coder.",
            "At conversation start, both agents must bootstrap repo authority in this order before acting: `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and `dev/active/review_channel.md`.",
            "Codex must poll non-`code_audit.md` worktree changes every 2-3 minutes while code is moving.",
            "Codex must exclude `code_audit.md` itself when computing the reviewed worktree hash.",
            "Each meaningful review must include an operator-visible chat update.",
            "Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.",
            "Claude should start from `Current Verdict`, `Open Findings`, and `Current Instruction For Claude`, then acknowledge the active instruction in `Claude Ack` before coding.",
            "When the current slice is accepted and scoped plan work remains, Codex must derive the next highest-priority unchecked plan item from the active-plan chain and rewrite `Current Instruction For Claude` for the next slice instead of idling at \"all green so far.\"",
            "Only the Codex conductor may update the Codex-owned sections in this file.",
            "Only the Claude conductor may update the Claude-owned sections in this file.",
            "Specialist workers should wake on owned-path changes or explicit conductor request instead of every worker polling the full tree blindly on the same cadence.",
            "Codex must emit an operator-visible heartbeat every 5 minutes while code is moving, even when the blocker set is unchanged.",
            "",
            f"- Last Codex poll: `{last_codex_poll}`",
            "- Last Codex poll (Local America/New_York): `2026-03-08 15:08:45 EDT`",
            f"- Last non-audit worktree hash: `{'a' * 64}`",
            "",
            "## Protocol",
            "",
            "- Poll target: every 5 minutes when code is moving (operator-directed live loop cadence)",
            "- Only unresolved findings, current verdicts, current ack state, and next instructions should stay live here.",
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
            "- bridge needs rollover-safe handoff",
            "",
            "## Current Instruction For Claude",
            "",
            current_instruction,
            "",
            "## Claude Status",
            "",
            claude_status,
            "",
            "## Claude Questions",
            "",
            "- none",
            "",
            "## Claude Ack",
            "",
            claude_ack,
            "",
            "## Last Reviewed Scope",
            "",
            "- code_audit.md",
            "- dev/scripts/devctl/review_channel_handoff.py",
            "",
        ]
    )


class ReviewChannelParserTests(unittest.TestCase):
    def test_cli_accepts_review_channel_launch_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "review-channel",
                "--action",
                "launch",
                "--execution-mode",
                "auto",
                "--terminal",
                "none",
                "--codex-workers",
                "8",
                "--claude-workers",
                "8",
                "--dangerous",
                "--dry-run",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "review-channel")
        self.assertEqual(args.action, "launch")
        self.assertEqual(args.execution_mode, "auto")
        self.assertEqual(args.terminal, "none")
        self.assertEqual(args.terminal_profile, DEFAULT_TERMINAL_PROFILE)
        self.assertEqual(args.rollover_threshold_pct, DEFAULT_ROLLOVER_THRESHOLD_PCT)
        self.assertEqual(args.await_ack_seconds, DEFAULT_ROLLOVER_ACK_WAIT_SECONDS)
        self.assertTrue(args.dangerous)
        self.assertTrue(args.dry_run)

    def test_cli_accepts_review_channel_status_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "review-channel",
                "--action",
                "status",
                "--terminal",
                "none",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "review-channel")
        self.assertEqual(args.action, "status")
        self.assertEqual(args.terminal, "none")
        self.assertEqual(args.status_dir, "dev/reports/review_channel/latest")


class ReviewChannelHelperTests(unittest.TestCase):
    def test_bridge_detection_tracks_transitional_heading(self) -> None:
        self.assertTrue(bridge_is_active(_build_review_channel_text()))
        self.assertFalse(
            bridge_is_active(_build_review_channel_text(include_bridge=False))
        )

    def test_parse_lane_assignments_returns_expected_counts(self) -> None:
        lanes = parse_lane_assignments(_build_review_channel_text())
        self.assertEqual(len(lanes), 16)
        self.assertEqual(sum(1 for lane in lanes if lane.provider == "codex"), 8)
        self.assertEqual(sum(1 for lane in lanes if lane.provider == "claude"), 8)
        self.assertIsInstance(lanes[0], LaneAssignment)

    def test_resolve_terminal_profile_name_prefers_known_dark_profile(self) -> None:
        resolved = resolve_terminal_profile_name(
            "auto-dark",
            available_profiles=["Basic", "Clear Dark", "Pro"],
        )
        self.assertEqual(resolved, "Pro")

    def test_resolve_terminal_profile_name_can_disable_profile_override(self) -> None:
        self.assertIsNone(
            resolve_terminal_profile_name(
                "default",
                available_profiles=["Basic", "Pro"],
            )
        )

    def test_summarize_bridge_liveness_marks_fresh_bridge_state(self) -> None:
        snapshot = extract_bridge_snapshot(_build_bridge_text())

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 13, 45, tzinfo=timezone.utc),
        )

        self.assertEqual(liveness.overall_state, "fresh")
        self.assertEqual(liveness.codex_poll_state, "fresh")
        self.assertTrue(liveness.next_action_present)
        self.assertTrue(liveness.claude_status_present)
        self.assertTrue(liveness.claude_ack_present)

    def test_summarize_bridge_liveness_waits_on_missing_claude_status(self) -> None:
        bridge_text = _build_bridge_text().replace(
            "## Claude Status\n\n- coding handoff fixes\n\n",
            "## Claude Status\n\n",
        )
        snapshot = extract_bridge_snapshot(bridge_text)

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 13, 45, tzinfo=timezone.utc),
        )

        self.assertEqual(liveness.overall_state, "waiting_on_peer")
        self.assertTrue(liveness.next_action_present)
        self.assertFalse(liveness.claude_status_present)
        self.assertTrue(liveness.claude_ack_present)

    def test_bridge_liveness_is_fresh_when_poll_and_ack_are_present(self) -> None:
        snapshot = extract_bridge_snapshot(
            _build_bridge_text(last_codex_poll="2026-03-08T19:08:45Z")
        )

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(liveness.overall_state, "fresh")
        self.assertEqual(liveness.codex_poll_state, "poll_due")
        self.assertEqual(liveness.last_codex_poll_age_seconds, 195)
        self.assertTrue(liveness.next_action_present)
        self.assertTrue(liveness.claude_ack_present)

    def test_bridge_liveness_waits_on_peer_when_ack_is_missing(self) -> None:
        snapshot = extract_bridge_snapshot(
            _build_bridge_text(claude_ack="")
        )

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(liveness.overall_state, "waiting_on_peer")
        self.assertEqual(liveness.codex_poll_state, "fresh")
        self.assertTrue(liveness.next_action_present)
        self.assertFalse(liveness.claude_ack_present)

    def test_validate_launch_bridge_state_requires_claude_status(self) -> None:
        snapshot = extract_bridge_snapshot(_build_bridge_text(claude_status=""))

        errors = validate_launch_bridge_state(
            snapshot,
            liveness=summarize_bridge_liveness(snapshot),
        )

        self.assertTrue(any("Claude Status" in error for error in errors))

    def test_validate_launch_bridge_state_requires_claude_ack(self) -> None:
        snapshot = extract_bridge_snapshot(_build_bridge_text(claude_ack=""))

        errors = validate_launch_bridge_state(
            snapshot,
            liveness=summarize_bridge_liveness(snapshot),
        )

        self.assertTrue(any("Claude Ack" in error for error in errors))

    def test_bridge_liveness_marks_poll_due_before_stale(self) -> None:
        snapshot = extract_bridge_snapshot(
            _build_bridge_text(last_codex_poll="2026-03-08T19:08:45Z")
        )

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 13, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(liveness.overall_state, "fresh")
        self.assertEqual(liveness.codex_poll_state, "poll_due")
        self.assertEqual(liveness.last_codex_poll_age_seconds, 255)
        self.assertTrue(liveness.last_reviewed_scope_present)

    def test_bridge_liveness_is_stale_when_reviewer_poll_is_old(self) -> None:
        snapshot = extract_bridge_snapshot(
            _build_bridge_text(last_codex_poll="2026-03-08T18:50:00Z")
        )

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(liveness.overall_state, "stale")
        self.assertEqual(liveness.codex_poll_state, "stale")
        self.assertEqual(liveness.last_codex_poll_age_seconds, 1320)

    def test_rollover_ack_state_requires_provider_owned_sections(self) -> None:
        rollover_id = "rollover-20260308T191500Z"
        bridge_text = _build_bridge_text().replace(
            "## Claude Ack\n\n- acknowledged\n\n",
            "## Claude Ack\n\n"
            f"{expected_rollover_ack_line(provider='codex', rollover_id=rollover_id)}\n"
            f"{expected_rollover_ack_line(provider='claude', rollover_id=rollover_id)}\n\n",
        )

        observed = observe_rollover_ack_state(
            bridge_text=bridge_text,
            rollover_id=rollover_id,
        )

        self.assertEqual(observed, {"codex": False, "claude": True})


class ReviewChannelCommandTests(unittest.TestCase):
    def test_run_dry_run_emits_scripts_and_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            script_dir = root / "scripts"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=str(script_dir.relative_to(root)),
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )
            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertFalse(payload["launched"])
            self.assertEqual(payload["terminal_profile_requested"], "auto-dark")
            self.assertEqual(payload["terminal_profile_applied"], "Pro")
            self.assertEqual(payload["bridge_liveness"]["overall_state"], "fresh")
            self.assertTrue(payload["bridge_liveness"]["claude_ack_present"])
            self.assertEqual(payload["codex_lane_count"], 8)
            self.assertEqual(payload["claude_lane_count"], 8)
            self.assertTrue(payload["bridge_liveness"]["claude_status_present"])
            self.assertTrue(payload["bridge_liveness"]["open_findings_present"])
            self.assertEqual(len(payload["sessions"]), 2)
            codex_session = payload["sessions"][0]
            claude_session = payload["sessions"][1]
            codex_script = Path(codex_session["script_path"])
            claude_script = Path(claude_session["script_path"])
            self.assertTrue(codex_script.exists())
            self.assertTrue(claude_script.exists())
            self.assertTrue(Path(codex_session["metadata_path"]).exists())
            self.assertTrue(Path(claude_session["metadata_path"]).exists())
            self.assertTrue(str(codex_session["log_path"]).endswith("codex-conductor.log"))
            self.assertEqual(codex_session["capture_mode"], "terminal-script")
            self.assertIn("--full-auto", codex_script.read_text(encoding="utf-8"))
            self.assertIn(
                "--permission-mode auto",
                claude_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "unset CLAUDECODE || true",
                claude_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "script -q -F -t 0",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "docs-check --strict-tooling",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "review-channel --action rollover",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "--await-ack-seconds 180",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "50% context remaining",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "claude_status_present: True",
                codex_script.read_text(encoding="utf-8"),
            )

    def test_run_dry_run_propagates_custom_rollover_ack_timeout_to_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            script_dir = root / "scripts"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=42,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=str(script_dir.relative_to(root)),
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            codex_script = Path(payload["sessions"][0]["script_path"])
            metadata_path = Path(payload["sessions"][0]["metadata_path"])
            self.assertIn(
                "--await-ack-seconds 42",
                codex_script.read_text(encoding="utf-8"),
            )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["provider"], "codex")
            self.assertEqual(metadata["capture_mode"], "terminal-script")
            self.assertEqual(metadata["worker_budget"], 8)

    def test_run_status_writes_projection_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            args = SimpleNamespace(
                action="status",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir=str(status_dir.relative_to(root)),
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["action"], "status")
            self.assertEqual(payload["sessions"], [])
            self.assertIsNone(payload["handoff_bundle"])
            self.assertIsNotNone(payload["projection_paths"])

            review_state_path = Path(payload["projection_paths"]["review_state_path"])
            compact_path = Path(payload["projection_paths"]["compact_path"])
            full_path = Path(payload["projection_paths"]["full_path"])
            actions_path = Path(payload["projection_paths"]["actions_path"])
            latest_markdown_path = Path(
                payload["projection_paths"]["latest_markdown_path"]
            )
            agent_registry_path = Path(
                payload["projection_paths"]["agent_registry_path"]
            )

            self.assertTrue(review_state_path.exists())
            self.assertTrue(compact_path.exists())
            self.assertTrue(full_path.exists())
            self.assertTrue(actions_path.exists())
            self.assertTrue(latest_markdown_path.exists())
            self.assertTrue(agent_registry_path.exists())

            review_state = json.loads(review_state_path.read_text(encoding="utf-8"))
            compact = json.loads(compact_path.read_text(encoding="utf-8"))
            actions = json.loads(actions_path.read_text(encoding="utf-8"))
            agent_registry = json.loads(
                agent_registry_path.read_text(encoding="utf-8")
            )

            self.assertEqual(review_state["command"], "review-channel")
            self.assertEqual(review_state["queue"]["pending_total"], 0)
            self.assertEqual(len(review_state["agents"]), 3)
            self.assertEqual(
                review_state["bridge"]["current_instruction"],
                "- stop at a safe boundary and relaunch before compaction",
            )
            self.assertEqual(compact["queue"]["pending_total"], 0)
            self.assertEqual(len(agent_registry["agents"]), 16)
            self.assertEqual(agent_registry["agents"][0]["agent_id"], "AGENT-1")
            self.assertEqual(actions["actions"], [])
            self.assertIn(
                "## Current Instruction",
                latest_markdown_path.read_text(encoding="utf-8"),
            )

    def test_run_reports_structured_error_when_provider_cli_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )
            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch(
                    "dev.scripts.devctl.review_channel.resolve_cli_path",
                    side_effect=ValueError("Required CLI not found on PATH: codex"),
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("Required CLI not found on PATH: codex", payload["errors"][0])

    def test_run_fails_closed_when_bridge_inactive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(include_bridge=False),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )
            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("inactive", payload["errors"][0])
            self.assertEqual(
                payload["retirement_note"],
                REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
            )

    def test_run_fails_when_bridge_guard_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(
                _build_bridge_text().replace(
                    "- code_audit.md\n- dev/scripts/devctl/review_channel_handoff.py",
                    "",
                ),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("bridge guard", payload["errors"][0])
            self.assertIn("Last Reviewed Scope", payload["errors"][0])

    def test_run_rollover_writes_handoff_bundle_and_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            script_dir = root / "scripts"
            rollover_dir = root / "dev/reports/review_channel/rollovers"
            args = SimpleNamespace(
                action="rollover",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir=str(rollover_dir.relative_to(root)),
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=str(script_dir.relative_to(root)),
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )
            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["action"], "rollover")
            self.assertEqual(
                payload["handoff_bundle"]["trigger"],
                "context-threshold",
            )
            self.assertTrue(payload["handoff_bundle"]["rollover_id"].startswith("rollover-"))
            handoff_json = Path(payload["handoff_bundle"]["json_path"])
            handoff_md = Path(payload["handoff_bundle"]["markdown_path"])
            self.assertTrue(handoff_json.exists())
            self.assertTrue(handoff_md.exists())
            handoff_payload = json.loads(handoff_json.read_text(encoding="utf-8"))
            self.assertIn("Open Findings", handoff_payload["sections"])
            self.assertEqual(
                handoff_payload["rollover_id"],
                payload["handoff_bundle"]["rollover_id"],
            )
            resume_state = handoff_payload["resume_state"]
            self.assertEqual(
                resume_state["current_blockers"],
                ["bridge needs rollover-safe handoff"],
            )
            self.assertEqual(
                resume_state["next_action"],
                "stop at a safe boundary and relaunch before compaction",
            )
            self.assertEqual(resume_state["reviewed_worktree_hash"], "a" * 64)
            self.assertEqual(
                resume_state["current_atomic_step"],
                "coding handoff fixes",
            )
            self.assertEqual(len(resume_state["owned_lanes"]["codex"]), 8)
            self.assertEqual(len(resume_state["owned_lanes"]["claude"]), 8)
            self.assertEqual(
                resume_state["owned_lanes"]["codex"][0]["agent_id"],
                "AGENT-1",
            )
            self.assertFalse(
                resume_state["launch_ack_state"]["codex"]["observed"]
            )
            self.assertFalse(
                resume_state["launch_ack_state"]["claude"]["observed"]
            )
            self.assertEqual(
                resume_state["launch_ack_state"]["codex"]["required_section"],
                "Poll Status",
            )
            self.assertEqual(
                resume_state["launch_ack_state"]["claude"]["required_section"],
                "Claude Ack",
            )
            self.assertIn("Codex rollover ack:", handoff_md.read_text(encoding="utf-8"))
            self.assertIn("## Resume State", handoff_md.read_text(encoding="utf-8"))
            codex_script = Path(payload["sessions"][0]["script_path"])
            self.assertIn(
                handoff_md.name,
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                f"Codex rollover ack: `{payload['handoff_bundle']['rollover_id']}`",
                codex_script.read_text(encoding="utf-8"),
            )

    def test_run_rollover_live_waits_for_visible_ack_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="rollover",
                execution_mode="auto",
                terminal="terminal-app",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=1,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=False,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            def _fake_launch(sessions, terminal_profile):
                del sessions, terminal_profile
                handoff_root = root / "dev/reports/review_channel/rollovers"
                handoff_json = next(handoff_root.glob("*/handoff.json"))
                payload = json.loads(handoff_json.read_text(encoding="utf-8"))
                rollover_id = payload["rollover_id"]
                bridge_path.write_text(
                    _build_bridge_text()
                    .replace(
                        "## Poll Status\n\n- active reviewer loop\n\n",
                        "## Poll Status\n\n- active reviewer loop\n"
                        f"- Codex rollover ack: `{rollover_id}`\n\n",
                    )
                    .replace(
                        "## Claude Ack\n\n- acknowledged\n\n",
                        "## Claude Ack\n\n- acknowledged\n"
                        f"- Claude rollover ack: `{rollover_id}`\n\n",
                    ),
                    encoding="utf-8",
                )

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_command,
                    "list_terminal_profiles",
                    return_value=["Pro"],
                ),
                patch.object(
                    review_channel_command,
                    "launch_terminal_sessions",
                    side_effect=_fake_launch,
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["launched"])
            self.assertTrue(payload["handoff_ack_required"])
            self.assertEqual(
                payload["handoff_ack_observed"],
                {"codex": True, "claude": True},
            )

    def test_run_rollover_rejects_ack_lines_in_wrong_owner_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="rollover",
                execution_mode="auto",
                terminal="terminal-app",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=1,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=False,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            def _fake_launch(sessions, terminal_profile):
                del sessions, terminal_profile
                handoff_root = root / "dev/reports/review_channel/rollovers"
                handoff_json = next(handoff_root.glob("*/handoff.json"))
                payload = json.loads(handoff_json.read_text(encoding="utf-8"))
                rollover_id = payload["rollover_id"]
                bridge_path.write_text(
                    _build_bridge_text()
                    .replace(
                        "## Poll Status\n\n- active reviewer loop\n\n",
                        "## Poll Status\n\n- active reviewer loop\n"
                        f"- Claude rollover ack: `{rollover_id}`\n\n",
                    )
                    .replace(
                        "## Claude Ack\n\n- acknowledged\n\n",
                        "## Claude Ack\n\n- acknowledged\n"
                        f"- Codex rollover ack: `{rollover_id}`\n\n",
                    ),
                    encoding="utf-8",
                )

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_command,
                    "list_terminal_profiles",
                    return_value=["Pro"],
                ),
                patch.object(
                    review_channel_command,
                    "launch_terminal_sessions",
                    side_effect=_fake_launch,
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertTrue(payload["handoff_ack_required"])
            self.assertEqual(
                payload["handoff_ack_observed"],
                {"codex": False, "claude": False},
            )
            self.assertIn("Timed out waiting", payload["errors"][0])

    def test_run_launch_fails_closed_when_bridge_poll_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(
                _build_bridge_text(last_codex_poll="2026-03-08T18:50:00Z"),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("within 5 minutes", payload["errors"][0])

    def test_run_launch_fails_closed_when_next_action_is_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(
                _build_bridge_text(current_instruction="- all green so far"),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("Current Instruction For Claude", payload["errors"][0])

    def test_run_launch_fails_closed_when_last_reviewed_scope_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(
                _build_bridge_text().replace(
                    "- code_audit.md\n- dev/scripts/devctl/review_channel_handoff.py",
                    "",
                ),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("Last Reviewed Scope", payload["errors"][0])

    def test_run_launch_fails_closed_when_bridge_files_are_untracked(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_command,
                    "build_bridge_guard_report",
                    return_value={
                        "ok": False,
                        "code_audit": {
                            "path": "code_audit.md",
                            "error": "Bridge-active file is untracked by git: code_audit.md",
                        },
                        "review_channel": {
                            "path": "dev/active/review_channel.md",
                            "error": "Bridge-active file is untracked by git: dev/active/review_channel.md",
                        },
                    },
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("code_audit.md", payload["errors"][0])
            self.assertIn("dev/active/review_channel.md", payload["errors"][0])

    def test_run_rollover_rejects_zero_second_ack_wait(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="rollover",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=0,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn(
                "greater than zero for rollover",
                payload["errors"][0],
            )

    def test_run_reports_structured_error_when_terminal_launch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="terminal-app",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=False,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )
            launch_error = subprocess.CalledProcessError(
                1,
                ["osascript", "-e", "tell application \"Terminal\" to activate"],
                stderr="launch failed",
            )
            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_command,
                    "list_terminal_profiles",
                    return_value=["Pro"],
                ),
                patch.object(
                    review_channel_command,
                    "launch_terminal_sessions",
                    side_effect=launch_error,
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("launcher subprocess failed", payload["errors"][0])

    def test_status_projection_marks_waiting_bridge_not_ok_when_claude_status_is_missing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(
                _build_bridge_text(claude_status=""),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="status",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("waiting_on_peer", payload["warnings"][0])

            review_state_path = Path(payload["projection_paths"]["review_state_path"])
            full_path = Path(payload["projection_paths"]["full_path"])
            review_state = json.loads(review_state_path.read_text(encoding="utf-8"))
            full_payload = json.loads(full_path.read_text(encoding="utf-8"))

            self.assertFalse(review_state["ok"])
            self.assertEqual(review_state["agents"][1]["status"], "waiting")
            self.assertEqual(review_state["bridge"]["claude_status"], "(missing)")
            self.assertFalse(full_payload["ok"])

    def test_run_fails_launch_when_claude_ack_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(
                _build_bridge_text(claude_ack=""),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("Claude Ack", payload["errors"][0])

    def test_run_warns_when_requested_terminal_profile_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="terminal-app",
                terminal_profile="Missing Dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_command,
                    "list_terminal_profiles",
                    return_value=["Pro"],
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIsNone(payload["terminal_profile_applied"])
            self.assertIn("Requested Terminal profile", payload["warnings"][-1])

if __name__ == "__main__":
    unittest.main()
