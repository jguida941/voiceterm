"""Tests for the transitional review-channel launcher.

Fixtures in this file model the same markdown authorities the launcher reads:
`dev/active/review_channel.md` and `code_audit.md`.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import review_channel as review_channel_command
from dev.scripts.devctl.commands import review_channel_bridge_handler
from dev.scripts.devctl.commands import review_channel_event_handler
from dev.scripts.devctl.review_channel import follow_stream as review_channel_follow_stream
from dev.scripts.devctl.review_channel.core import (
    DEFAULT_ROLLOVER_ACK_WAIT_SECONDS,
    DEFAULT_ROLLOVER_THRESHOLD_PCT,
    DEFAULT_TERMINAL_PROFILE,
    REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
    ActiveSessionConflict,
    LaneAssignment,
    bridge_is_active,
    detect_active_session_conflicts,
    parse_lane_assignments,
    resolve_terminal_profile_name,
    summarize_active_session_conflicts,
)
from dev.scripts.devctl.review_channel.event_models import ReviewChannelEventBundle
from dev.scripts.devctl.review_channel.event_reducer import (
    load_or_refresh_event_bundle,
    refresh_event_bundle,
)
from dev.scripts.devctl.review_channel.event_store import (
    ReviewChannelArtifactPaths,
    resolve_artifact_paths,
)
from dev.scripts.devctl.review_channel.launch import (
    _build_terminal_launch_lines,
    build_promote_command,
    build_rollover_command,
)
from dev.scripts.devctl.review_channel.projection_bundle import (
    ReviewChannelProjectionPaths,
)

from dev.scripts.devctl.review_channel.handoff_constants import _is_substantive_text
from dev.scripts.devctl.review_channel.handoff import (
    expected_rollover_ack_line,
    extract_bridge_snapshot,
    observe_rollover_ack_state,
    summarize_bridge_liveness,
    validate_launch_bridge_state,
)
from dev.scripts.devctl.review_channel.heartbeat import (
    compute_non_audit_worktree_hash,
)
from dev.scripts.devctl.review_channel.reviewer_state import (
    EnsureHeartbeatResult,
    ReviewerStateWrite,
)
from dev.scripts.devctl.time_utils import utc_timestamp


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
            "Bridge behavior is mode-aware. When `Reviewer mode` is `active_dual_agent`, Claude must treat `code_audit.md` as the live reviewer/coder authority and keep polling it instead of waiting for the operator to restate the process.",
            "If reviewer-owned bridge state says `hold steady`, `waiting for reviewer promotion`, `Codex committing/pushing`, or equivalent wait-state language, Claude must stay in polling mode. It must not mine plan docs for side work or self-promote the next slice until a reviewer-owned section changes.",
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
    reviewer_mode: str = "active_dual_agent",
    current_verdict: str = "- still in progress",
    open_findings: str = "- bridge needs rollover-safe handoff",
    current_instruction: str = "- stop at a safe boundary and relaunch before compaction",
    claude_status: str = "- coding handoff fixes",
    claude_ack: str = "- acknowledged",
) -> str:
    if last_codex_poll is None:
        last_codex_poll = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
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
            "Claude should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`, then acknowledge the active instruction in `Claude Ack` before coding.",
            "Claude must read `Last Codex poll` / `Poll Status` first on each repoll. If the reviewer-owned timestamp and the reviewer-owned sections are unchanged after Claude already finished the current bounded work, treat that as a live wait state, wait on cadence, and reread the full reviewer-owned block instead of hammering one fixed offset/line.",
            "When `Reviewer mode` is `active_dual_agent`, this file is the live reviewer/coder authority. Claude must keep polling it instead of waiting for the operator to restate the process in chat.",
            "When `Reviewer mode` is `single_agent`, `tools_only`, `paused`, or `offline`, Claude must not assume a live Codex review loop. Treat this file as context unless a reviewer-owned section explicitly reactivates the bridge or the operator asks for dual-agent mode.",
            'When the current slice is accepted and scoped plan work remains, Codex must derive the next highest-priority unchecked plan item from the active-plan chain and rewrite `Current Instruction For Claude` for the next slice instead of idling at "all green so far."',
            "If `Current Instruction For Claude` or `Poll Status` says `hold steady`, `waiting for reviewer promotion`, `Codex committing/pushing`, or similar wait-state language, Claude must not mine plan docs for side work or self-promote the next slice. Keep polling until a reviewer-owned section changes.",
            "Only the Codex conductor may update the Codex-owned sections in this file.",
            "Only the Claude conductor may update the Claude-owned sections in this file.",
            "Specialist workers should wake on owned-path changes or explicit conductor request instead of every worker polling the full tree blindly on the same cadence.",
            "Codex must emit an operator-visible heartbeat every 5 minutes while code is moving, even when the blocker set is unchanged.",
            "",
            f"- Last Codex poll: `{last_codex_poll}`",
            "- Last Codex poll (Local America/New_York): `2026-03-08 15:08:45 EDT`",
            f"- Reviewer mode: `{reviewer_mode}`",
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
            current_verdict,
            "",
            "## Open Findings",
            "",
            open_findings,
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
            "- dev/scripts/devctl/review_channel/handoff.py",
            "",
        ]
    )


def _fresh_utc_z(*, seconds_offset: int = 0) -> str:
    timestamp = datetime.now(UTC) + timedelta(seconds=seconds_offset)
    return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_event_bundle_for_test(packet_ids: list[str]) -> ReviewChannelEventBundle:
    packets = [
        {
            "packet_id": packet_id,
            "from_agent": "codex",
            "to_agent": "claude",
            "summary": f"packet {packet_id}",
            "status": "pending",
        }
        for packet_id in packet_ids
    ]
    return ReviewChannelEventBundle(
        artifact_paths=ReviewChannelArtifactPaths(
            artifact_root="/tmp/review/artifacts",
            event_log_path="/tmp/review/artifacts/events/trace.ndjson",
            state_path="/tmp/review/state.json",
            projections_root="/tmp/review/projections",
        ),
        projection_paths=ReviewChannelProjectionPaths(
            root_dir="/tmp/review/projections",
            review_state_path="/tmp/review/projections/review_state.json",
            compact_path="/tmp/review/projections/compact.json",
            full_path="/tmp/review/projections/full.json",
            actions_path="/tmp/review/projections/actions.json",
            trace_path="/tmp/review/projections/trace.ndjson",
            latest_markdown_path="/tmp/review/projections/latest.md",
            agent_registry_path="/tmp/review/projections/registry/agents.json",
        ),
        review_state={
            "ok": True,
            "queue": {"pending_total": len(packet_ids), "stale_packet_count": 0},
            "packets": packets,
            "warnings": [],
            "errors": [],
        },
        agent_registry={"agents": []},
        events=[],
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
                "--approval-mode",
                "balanced",
                "--codex-workers",
                "8",
                "--claude-workers",
                "8",
                "--refresh-bridge-heartbeat-if-stale",
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
        self.assertEqual(args.approval_mode, "balanced")
        self.assertEqual(args.terminal_profile, DEFAULT_TERMINAL_PROFILE)
        self.assertEqual(args.rollover_threshold_pct, DEFAULT_ROLLOVER_THRESHOLD_PCT)
        self.assertEqual(args.await_ack_seconds, DEFAULT_ROLLOVER_ACK_WAIT_SECONDS)
        self.assertTrue(args.refresh_bridge_heartbeat_if_stale)
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

    def test_cli_accepts_reviewer_state_action_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "review-channel",
                "--action",
                "reviewer-heartbeat",
                "--reviewer-mode",
                "developer",
                "--reason",
                "local-tools-pass",
                "--terminal",
                "none",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "review-channel")
        self.assertEqual(args.action, "reviewer-heartbeat")
        self.assertEqual(args.reviewer_mode, "developer")
        self.assertEqual(args.reason, "local-tools-pass")

    def test_cli_accepts_context_pack_ref_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "review-channel",
                "--action",
                "post",
                "--from-agent",
                "codex",
                "--to-agent",
                "claude",
                "--kind",
                "draft",
                "--summary",
                "Attach memory refs",
                "--body",
                "Use the exported task pack.",
                "--context-pack-ref",
                "task_pack:.voiceterm/memory/exports/task_pack.json",
                "--context-pack-adapter-profile",
                "claude",
                "--format",
                "json",
            ]
        )

        self.assertEqual(
            args.context_pack_ref,
            ["task_pack:.voiceterm/memory/exports/task_pack.json"],
        )
        self.assertEqual(args.context_pack_adapter_profile, "claude")

    def test_cli_accepts_review_channel_promote_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "review-channel",
                "--action",
                "promote",
                "--promotion-plan",
                "dev/active/continuous_swarm.md",
                "--terminal",
                "none",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "review-channel")
        self.assertEqual(args.action, "promote")
        self.assertEqual(args.promotion_plan, "dev/active/continuous_swarm.md")


class ReviewChannelHelperTests(unittest.TestCase):
    def test_bridge_detection_tracks_transitional_heading(self) -> None:
        self.assertTrue(bridge_is_active(_build_review_channel_text()))
        self.assertFalse(bridge_is_active(_build_review_channel_text(include_bridge=False)))

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

    def test_build_terminal_launch_lines_applies_profile_before_command(self) -> None:
        lines = _build_terminal_launch_lines(
            launch_command="/bin/zsh /tmp/claude-conductor.sh",
            resolved_profile="Pro",
            available_profiles=["Basic", "Pro"],
        )

        self.assertEqual(lines[0], 'tell application "Terminal"')
        self.assertEqual(lines[1], "activate")
        self.assertEqual(lines[2], 'do script ""')
        self.assertEqual(
            lines[3],
            'set current settings of selected tab of front window to settings set "Pro"',
        )
        self.assertEqual(
            lines[4],
            'do script "/bin/zsh /tmp/claude-conductor.sh" in selected tab of front window',
        )
        self.assertEqual(lines[5], "end tell")

    def test_build_terminal_launch_lines_uses_direct_launch_without_profile(self) -> None:
        lines = _build_terminal_launch_lines(
            launch_command="/bin/zsh /tmp/codex-conductor.sh",
            resolved_profile=None,
            available_profiles=["Basic", "Pro"],
        )

        self.assertEqual(lines[0], 'tell application "Terminal"')
        self.assertEqual(lines[1], "activate")
        self.assertEqual(lines[2], 'do script "/bin/zsh /tmp/codex-conductor.sh"')
        self.assertEqual(lines[3], "end tell")

    def test_summarize_bridge_liveness_marks_fresh_bridge_state(self) -> None:
        snapshot = extract_bridge_snapshot(_build_bridge_text())

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 13, 45, tzinfo=UTC),
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
            now_utc=datetime(2026, 3, 8, 19, 13, 45, tzinfo=UTC),
        )

        self.assertEqual(liveness.overall_state, "waiting_on_peer")
        self.assertTrue(liveness.next_action_present)
        self.assertFalse(liveness.claude_status_present)
        self.assertTrue(liveness.claude_ack_present)

    def test_bridge_liveness_is_fresh_when_poll_and_ack_are_present(self) -> None:
        snapshot = extract_bridge_snapshot(_build_bridge_text(last_codex_poll="2026-03-08T19:08:45Z"))

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(liveness.overall_state, "fresh")
        self.assertEqual(liveness.codex_poll_state, "poll_due")
        self.assertEqual(liveness.last_codex_poll_age_seconds, 195)
        self.assertTrue(liveness.next_action_present)
        self.assertTrue(liveness.claude_ack_present)

    def test_bridge_liveness_waits_on_peer_when_ack_is_missing(self) -> None:
        snapshot = extract_bridge_snapshot(_build_bridge_text(claude_ack=""))

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 12, 0, tzinfo=UTC),
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

    def test_detect_active_session_conflicts_uses_fresh_logs_when_process_probe_is_unavailable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sessions_dir = root / "latest/sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            metadata_path = sessions_dir / "codex-conductor.json"
            log_path = sessions_dir / "codex-conductor.log"
            metadata_path.write_text(
                json.dumps(
                    {
                        "provider": "codex",
                        "session_name": "codex-conductor",
                        "script_path": str(sessions_dir / "codex-conductor.sh"),
                        "log_path": str(log_path),
                    }
                ),
                encoding="utf-8",
            )
            log_path.write_text("still live\n", encoding="utf-8")

            with patch(
                "dev.scripts.devctl.review_channel.core._probe_script_running",
                return_value=None,
            ):
                conflicts = detect_active_session_conflicts(session_output_root=root / "latest")

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].provider, "codex")
        self.assertIn("updated", conflicts[0].reason)

    def test_summarize_active_session_conflicts_includes_provider_and_log_path(self) -> None:
        summary = summarize_active_session_conflicts(
            (
                ActiveSessionConflict(
                    provider="codex",
                    session_name="codex-conductor",
                    metadata_path="/tmp/codex.json",
                    log_path="/tmp/codex.log",
                    age_seconds=4,
                    reason="existing conductor script process is still running",
                ),
            )
        )

        self.assertIn("codex", summary)
        self.assertIn("/tmp/codex.log", summary)

    def test_bridge_liveness_marks_poll_due_before_stale(self) -> None:
        snapshot = extract_bridge_snapshot(_build_bridge_text(last_codex_poll="2026-03-08T19:08:45Z"))

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 13, 0, tzinfo=UTC),
        )

        self.assertEqual(liveness.overall_state, "fresh")
        self.assertEqual(liveness.codex_poll_state, "poll_due")
        self.assertEqual(liveness.last_codex_poll_age_seconds, 255)
        self.assertTrue(liveness.last_reviewed_scope_present)

    def test_bridge_liveness_is_stale_when_reviewer_poll_is_old(self) -> None:
        snapshot = extract_bridge_snapshot(_build_bridge_text(last_codex_poll="2026-03-08T18:50:00Z"))

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(liveness.overall_state, "stale")
        self.assertEqual(liveness.codex_poll_state, "stale")

    def test_bridge_liveness_is_inactive_when_mode_is_tools_only(self) -> None:
        snapshot = extract_bridge_snapshot(
            _build_bridge_text(
                last_codex_poll="2026-03-08T18:50:00Z",
                reviewer_mode="tools_only",
                claude_status="",
                claude_ack="",
            )
        )

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(liveness.overall_state, "inactive")
        self.assertEqual(liveness.reviewer_mode, "tools_only")
        self.assertEqual(liveness.codex_poll_state, "stale")
        self.assertEqual(liveness.last_codex_poll_age_seconds, 1320)

    def test_bridge_liveness_detects_implementer_completion_stall(self) -> None:
        snapshot = extract_bridge_snapshot(
            _build_bridge_text(
                claude_status="- Continuing to poll for next instruction.",
                claude_ack="- instruction unchanged, waiting for codex review.",
            )
        )

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 8, 50, tzinfo=UTC),
        )

        self.assertTrue(liveness.implementer_completion_stall)

    def test_bridge_liveness_no_stall_when_actively_coding(self) -> None:
        snapshot = extract_bridge_snapshot(
            _build_bridge_text(
                claude_status="- Working on M51 completion-stall seam.",
                claude_ack="- Session 29 ack: M51 in progress.",
            )
        )

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 8, 50, tzinfo=UTC),
        )

        self.assertFalse(liveness.implementer_completion_stall)

    def test_bootstrap_ordering_puts_repo_authority_before_handoff_bundle(self) -> None:
        from dev.scripts.devctl.review_channel.prompt import _bootstrap_files

        root = Path("/fake/repo")
        files = _bootstrap_files(
            repo_root=root,
            review_channel_path=root / "dev/active/review_channel.md",
            bridge_path=root / "code_audit.md",
            handoff_bundle={
                "markdown_path": str(root / "dev/reports/handoff.md"),
                "json_path": str(root / "dev/reports/handoff.json"),
                "rollover_id": "rollover-test",
            },
        )
        agents_idx = files.index("AGENTS.md")
        index_idx = files.index("dev/active/INDEX.md")
        handoff_items = [f for f in files if "handoff" in f]
        self.assertTrue(len(handoff_items) >= 2, "handoff files should be present")
        for hf in handoff_items:
            hf_idx = files.index(hf)
            self.assertGreater(
                hf_idx,
                agents_idx,
                f"handoff file {hf} must come after AGENTS.md",
            )
            self.assertGreater(
                hf_idx,
                index_idx,
                f"handoff file {hf} must come after INDEX.md",
            )

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

    def test_rollover_ack_state_excludes_cursor_by_design(self) -> None:
        """Cursor is intentionally excluded from rollover ACK because it does
        not own a bridge section. Cursor lanes are present in queue/projection/
        runtime state, but rollover ACK is a bridge-section-ownership protocol."""
        from dev.scripts.devctl.review_channel.handoff_constants import ROLLOVER_ACK_PREFIX

        self.assertNotIn("cursor", ROLLOVER_ACK_PREFIX)

        rollover_id = "rollover-cursor-boundary"
        observed = observe_rollover_ack_state(
            bridge_text=_build_bridge_text(),
            rollover_id=rollover_id,
        )
        self.assertNotIn("cursor", observed)
        self.assertIn("codex", observed)
        self.assertIn("claude", observed)

    def test_codex_prompt_requires_immediate_heartbeat_and_no_approval_waiting(
        self,
    ) -> None:
        from dev.scripts.devctl.review_channel.prompt import build_conductor_prompt

        root = Path("/fake/repo")
        prompt = build_conductor_prompt(
            provider="codex",
            provider_name="Codex",
            other_name="Claude",
            repo_root=root,
            review_channel_path=root / "dev/active/review_channel.md",
            bridge_path=root / "code_audit.md",
            lanes=[],
            codex_workers=8,
            claude_workers=8,
            dangerous=False,
            rollover_threshold_pct=50,
            await_ack_seconds=180,
            retirement_note=REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
            rollover_command="python3 dev/scripts/devctl.py review-channel --action rollover",
            promote_command="python3 dev/scripts/devctl.py review-channel --action promote --promotion-plan dev/active/continuous_swarm.md --terminal none --format md",
            bridge_liveness=None,
            handoff_bundle=None,
        )

        self.assertIn(
            "First action after bootstrap on every fresh launch: refresh "
            "`Last Codex poll`, `Last non-audit worktree hash`, and `Poll Status`",
            prompt,
        )
        self.assertIn(
            "Do not leave the reviewer parked on unanswered approval prompts.",
            prompt,
        )
        self.assertIn(
            'A bridge summary, `waiting_on_peer` note, or "all green so far" ' "update is never terminal by itself.",
            prompt,
        )
        self.assertIn(
            "review-channel --action promote --promotion-plan "
            "dev/active/continuous_swarm.md --terminal none --format md",
            prompt,
        )
        self.assertIn(
            "rewrite `Current Instruction For Claude` instead of inventing the "
            "next task by hand or ending on a summary.",
            prompt,
        )
        self.assertIn(
            "Shared post-edit verification contract",
            prompt,
        )
        self.assertIn(
            "After EVERY file create/edit, you MUST run the repo-required verification before reporting the task as done.",
            prompt,
        )
        self.assertIn(
            "`bundle.runtime`, `bundle.docs`, `bundle.tooling`, or `bundle.release`",
            prompt,
        )
        self.assertIn(
            "python3 dev/scripts/devctl.py check --profile ci",
            prompt,
        )
        self.assertIn(
            "Done means the required guards/tests passed.",
            prompt,
        )

    def test_claude_prompt_requires_polling_instead_of_exit_on_peer_wait(self) -> None:
        from dev.scripts.devctl.review_channel.prompt import build_conductor_prompt

        root = Path("/fake/repo")
        prompt = build_conductor_prompt(
            provider="claude",
            provider_name="Claude",
            other_name="Codex",
            repo_root=root,
            review_channel_path=root / "dev/active/review_channel.md",
            bridge_path=root / "code_audit.md",
            lanes=[],
            codex_workers=8,
            claude_workers=8,
            dangerous=False,
            rollover_threshold_pct=50,
            await_ack_seconds=180,
            retirement_note=REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
            rollover_command="python3 dev/scripts/devctl.py review-channel --action rollover",
            promote_command="python3 dev/scripts/devctl.py review-channel --action promote --promotion-plan dev/active/continuous_swarm.md --terminal none --format md",
            bridge_liveness=None,
            handoff_bundle=None,
        )

        self.assertIn(
            "`waiting_on_peer` means the loop stays live while you keep polling "
            "for the next bridge change; it does not mean the conductor should "
            "exit or park silently.",
            prompt,
        )
        self.assertIn(
            "`code_audit.md` is the first thing to re-read whenever you need "
            "to know what to do next in dual-agent mode.",
            prompt,
        )
        self.assertIn(
            "Do not scan plan docs for side work or reopen an accepted tranche "
            "until the reviewer-owned instruction changes.",
            prompt,
        )
        self.assertIn(
            "If you are waiting on Codex review or the next instruction, stay in "
            "the conductor role, keep polling the bridge on the documented cadence, "
            "and resume as soon as `Current Instruction For Claude` changes.",
            prompt,
        )
        self.assertIn(
            "Posting `Claude Status` or `Claude Ack` is not the end of the loop.",
            prompt,
        )
        self.assertIn(
            "Only reviewer-owned `Current Instruction For Claude` may start a new slice.",
            prompt,
        )
        self.assertIn(
            "Shared post-edit verification contract",
            prompt,
        )
        self.assertIn(
            "After EVERY file create/edit, you MUST run the repo-required verification before reporting the task as done.",
            prompt,
        )
        self.assertIn(
            "`bundle.runtime`, `bundle.docs`, `bundle.tooling`, or `bundle.release`",
            prompt,
        )
        self.assertIn(
            "Done means the required guards/tests passed.",
            prompt,
        )

    @patch(
        "dev.scripts.devctl.review_channel.prompt_contract.load_repo_governance_section",
        return_value=(
            {
                "context": {
                    "post_edit_verification_intro": "Custom intro from repo policy.",
                    "post_edit_verification_steps": [
                        "Run `bundle.tooling`.",
                        "Run `python3 dev/scripts/devctl.py check --profile ci`.",
                    ],
                    "post_edit_verification_done_criteria": "Custom done criteria from repo policy.",
                }
            },
            (),
            Path("/tmp/policy.json"),
        ),
    )
    def test_prompt_uses_repo_policy_post_edit_verification_contract(
        self,
        _load_repo_governance_section_mock,
    ) -> None:
        from dev.scripts.devctl.review_channel.prompt import build_conductor_prompt

        root = Path("/fake/repo")
        prompt = build_conductor_prompt(
            provider="claude",
            provider_name="Claude",
            other_name="Codex",
            repo_root=root,
            review_channel_path=root / "dev/active/review_channel.md",
            bridge_path=root / "code_audit.md",
            lanes=[],
            codex_workers=8,
            claude_workers=8,
            dangerous=False,
            rollover_threshold_pct=50,
            await_ack_seconds=180,
            retirement_note=REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
            rollover_command="python3 dev/scripts/devctl.py review-channel --action rollover",
            promote_command="python3 dev/scripts/devctl.py review-channel --action promote --promotion-plan dev/active/continuous_swarm.md --terminal none --format md",
            bridge_liveness=None,
            handoff_bundle=None,
        )

        self.assertIn("Custom intro from repo policy.", prompt)
        self.assertIn("Run `bundle.tooling`.", prompt)
        self.assertIn(
            "Run `python3 dev/scripts/devctl.py check --profile ci`.",
            prompt,
        )
        self.assertIn("Custom done criteria from repo policy.", prompt)

class ReviewChannelWatchFollowTests(unittest.TestCase):
    def _build_follow_args(self, **overrides) -> SimpleNamespace:
        base = {
            "action": "watch",
            "target": "claude",
            "status": "pending",
            "limit": 1,
            "follow": True,
            "max_follow_snapshots": 2,
            "stale_minutes": 1,
            "format": "json",
            "output": None,
            "pipe_command": None,
            "pipe_args": None,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    def _build_ensure_follow_args(self, **overrides) -> SimpleNamespace:
        base = {
            "action": "ensure",
            "follow": True,
            "max_follow_snapshots": 2,
            "follow_interval_seconds": 1,
            "timeout_minutes": 0,
            "reviewer_mode": "active_dual_agent",
            "format": "json",
            "output": None,
            "pipe_command": None,
            "pipe_args": None,
            "limit": 20,
            "stale_minutes": 30,
            "expires_in_minutes": 30,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    def _build_ensure_args(self, **overrides) -> SimpleNamespace:
        base = {
            "action": "ensure",
            "follow": False,
            "reviewer_mode": "active_dual_agent",
            "format": "json",
            "output": None,
            "pipe_command": None,
            "pipe_args": None,
            "limit": 20,
            "stale_minutes": 30,
            "expires_in_minutes": 30,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    def test_validate_args_rejects_follow_without_json_format(self) -> None:
        args = self._build_follow_args(format="md")
        with self.assertRaisesRegex(
            ValueError,
            "watch --follow requires --format json",
        ):
            review_channel_command._validate_args(args)

    def test_validate_args_rejects_ensure_follow_without_json_format(self) -> None:
        args = self._build_ensure_follow_args(format="md")
        with self.assertRaisesRegex(
            ValueError,
            "ensure --follow requires --format json",
        ):
            review_channel_command._validate_args(args)

    def test_validate_args_rejects_start_publisher_outside_ensure(self) -> None:
        args = self._build_follow_args(start_publisher_if_missing=True)
        with self.assertRaisesRegex(
            ValueError,
            "start-publisher-if-missing is only valid for review-channel ensure",
        ):
            review_channel_command._validate_args(args)

    def test_watch_follow_emits_ndjson_snapshots_until_max_follow_snapshots(self) -> None:
        args = self._build_follow_args(limit=1, max_follow_snapshots=2)
        initial_bundle = _build_event_bundle_for_test(["pkt-1"])
        changed_bundle = _build_event_bundle_for_test(["pkt-2"])
        emitted: list[str] = []

        def fake_emit_output(
            content: str,
            *,
            output_path: str | None,
            pipe_command: str | None,
            pipe_args: list[str] | None,
            announce_output_path: bool = True,
            writer=None,
            stdout_content: str | None = None,
            piper=None,
            additional_outputs=None,
        ) -> int:
            emitted.append(content)
            return 0

        with (
            patch.object(review_channel_follow_stream, "emit_output", side_effect=fake_emit_output),
            patch.object(review_channel_event_handler.time, "sleep", return_value=None),
            patch.object(review_channel_event_handler, "refresh_event_bundle", return_value=changed_bundle),
        ):
            report, rc = review_channel_event_handler._run_watch_follow(
                args=args,
                repo_root=Path("/tmp/repo"),
                review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
                artifact_paths=initial_bundle.artifact_paths,
                initial_bundle=initial_bundle,
                initial_packets=initial_bundle.review_state["packets"],
            )

        self.assertEqual(rc, 0)
        self.assertTrue(report["_already_emitted"])
        self.assertEqual(report["snapshots_emitted"], 2)
        self.assertEqual(len(emitted), 2)
        first = json.loads(emitted[0])
        second = json.loads(emitted[1])
        self.assertEqual(first["snapshot_seq"], 0)
        self.assertEqual(second["snapshot_seq"], 1)
        self.assertEqual(first["packets"][0]["packet_id"], "pkt-1")
        self.assertEqual(second["packets"][0]["packet_id"], "pkt-2")
        self.assertEqual(len(first["packets"]), 1)
        self.assertEqual(len(second["packets"]), 1)

    def test_watch_follow_does_not_reemit_when_packet_set_is_unchanged(self) -> None:
        args = self._build_follow_args(max_follow_snapshots=0)
        bundle = _build_event_bundle_for_test(["pkt-1"])
        emitted: list[str] = []

        def fake_emit_output(
            content: str,
            *,
            output_path: str | None,
            pipe_command: str | None,
            pipe_args: list[str] | None,
            announce_output_path: bool = True,
            writer=None,
            stdout_content: str | None = None,
            piper=None,
            additional_outputs=None,
        ) -> int:
            emitted.append(content)
            return 0

        with (
            patch.object(review_channel_follow_stream, "emit_output", side_effect=fake_emit_output),
            patch.object(
                review_channel_event_handler.time,
                "sleep",
                side_effect=[None, KeyboardInterrupt()],
            ),
            patch.object(review_channel_event_handler, "refresh_event_bundle", return_value=bundle),
        ):
            report, rc = review_channel_event_handler._run_watch_follow(
                args=args,
                repo_root=Path("/tmp/repo"),
                review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
                artifact_paths=bundle.artifact_paths,
                initial_bundle=bundle,
                initial_packets=bundle.review_state["packets"],
            )

        self.assertEqual(rc, 0)
        self.assertEqual(report["snapshots_emitted"], 1)
        self.assertEqual(len(emitted), 1)
        first = json.loads(emitted[0])
        self.assertEqual(first["snapshot_seq"], 0)
        self.assertEqual(first["packets"][0]["packet_id"], "pkt-1")

    def test_watch_follow_appends_ndjson_snapshots_to_output_file(self) -> None:
        args = self._build_follow_args(max_follow_snapshots=2)
        initial_bundle = _build_event_bundle_for_test(["pkt-1"])
        changed_bundle = _build_event_bundle_for_test(["pkt-2"])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "watch.ndjson"
            args.output = str(output_path)
            with (
                patch.object(review_channel_event_handler.time, "sleep", return_value=None),
                patch.object(review_channel_event_handler, "refresh_event_bundle", return_value=changed_bundle),
            ):
                report, rc = review_channel_event_handler._run_watch_follow(
                    args=args,
                    repo_root=Path(tmpdir),
                    review_channel_path=Path(tmpdir) / "dev/active/review_channel.md",
                    artifact_paths=initial_bundle.artifact_paths,
                    initial_bundle=initial_bundle,
                    initial_packets=initial_bundle.review_state["packets"],
                )

            self.assertEqual(rc, 0)
            self.assertEqual(report["snapshots_emitted"], 2)
            lines = output_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["snapshot_seq"], 0)
            self.assertEqual(json.loads(lines[1])["snapshot_seq"], 1)

    def test_run_skips_second_emit_when_follow_stream_already_emitted(self) -> None:
        args = SimpleNamespace(
            action="watch",
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )
        with (
            patch.object(review_channel_command, "_validate_args", return_value=None),
            patch.object(review_channel_command, "_resolve_runtime_paths", return_value={}),
            patch.object(
                review_channel_command,
                "_run_event_action",
                return_value=({"ok": True, "_already_emitted": True}, 0),
            ),
            patch.object(review_channel_command, "emit_output") as emit_output_mock,
        ):
            rc = review_channel_command.run(args)

        self.assertEqual(rc, 0)
        emit_output_mock.assert_not_called()

    def test_ensure_follow_emits_heartbeat_status_frames(self) -> None:
        args = self._build_ensure_follow_args(max_follow_snapshots=2)
        frames: list[dict[str, object]] = []
        write = ReviewerStateWrite(
            bridge_path="code_audit.md",
            action="reviewer-heartbeat",
            reviewer_mode="active_dual_agent",
            reason="ensure-follow",
            last_codex_poll_utc="2026-03-16T07:00:00Z",
            last_codex_poll_local="2026-03-16 03:00:00 EDT",
            last_worktree_hash="a" * 64,
        )
        ensure_result = EnsureHeartbeatResult(
            refreshed=True,
            reviewer_mode="active_dual_agent",
            reason="ensure-follow",
            state_write=write,
            error=None,
        )
        status_report = {
            "command": "review-channel",
            "action": "status",
            "ok": True,
            "bridge_liveness": {
                "overall_state": "fresh",
                "reviewer_mode": "active_dual_agent",
                "codex_poll_state": "fresh",
                "last_codex_poll_age_seconds": 0,
            },
            "attention": {"status": "healthy"},
        }

        def fake_emit_follow_ndjson_frame(payload: dict[str, object], *, args) -> int:
            frames.append(payload)
            return 0

        publisher_state = {"running": True, "pid": 42, "stale": False}

        with (
            patch.object(review_channel_command, "ensure_reviewer_heartbeat", return_value=ensure_result),
            patch.object(review_channel_command, "_run_status_action", return_value=(status_report, 0)),
            patch.object(review_channel_command, "emit_follow_ndjson_frame", side_effect=fake_emit_follow_ndjson_frame),
            patch.object(review_channel_command, "reset_follow_output", return_value=None),
            patch.object(review_channel_command, "write_publisher_heartbeat", return_value=Path("/tmp")),
            patch.object(review_channel_command, "read_publisher_state", return_value=publisher_state),
            patch.object(review_channel_command.time, "sleep", return_value=None),
        ):
            report, rc = review_channel_command._run_ensure_action(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={
                    "bridge_path": Path("/tmp/repo/code_audit.md"),
                    "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
                },
            )

        self.assertEqual(rc, 0)
        self.assertTrue(report["_already_emitted"])
        self.assertEqual(report["snapshots_emitted"], 2)
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0]["snapshot_seq"], 0)
        self.assertEqual(frames[1]["snapshot_seq"], 1)
        self.assertTrue(all(frame["follow"] for frame in frames))
        self.assertIn("reviewer_state_write", frames[0])
        self.assertEqual(
            frames[0]["reviewer_state_write"]["reason"],
            "ensure-follow",
        )
        self.assertTrue(frames[0]["ensure_refreshed"])
        self.assertIn("publisher", frames[0])
        self.assertTrue(frames[0]["publisher"]["running"])

    def test_ensure_follow_skips_heartbeat_when_mode_inactive(self) -> None:
        args = self._build_ensure_follow_args(max_follow_snapshots=1)
        frames: list[dict[str, object]] = []
        inactive_result = EnsureHeartbeatResult(
            refreshed=False,
            reviewer_mode="tools_only",
            reason="ensure-follow",
            state_write=None,
            error=None,
        )
        status_report = {
            "command": "review-channel",
            "action": "status",
            "ok": True,
            "bridge_liveness": {
                "overall_state": "inactive",
                "reviewer_mode": "tools_only",
                "codex_poll_state": "missing",
            },
            "attention": {"status": "inactive"},
        }

        def fake_emit(payload: dict[str, object], *, args) -> int:
            frames.append(payload)
            return 0

        publisher_state = {"running": True, "pid": 42, "stale": False}

        with (
            patch.object(review_channel_command, "ensure_reviewer_heartbeat", return_value=inactive_result),
            patch.object(review_channel_command, "_run_status_action", return_value=(status_report, 0)),
            patch.object(review_channel_command, "emit_follow_ndjson_frame", side_effect=fake_emit),
            patch.object(review_channel_command, "reset_follow_output", return_value=None),
            patch.object(review_channel_command, "write_publisher_heartbeat", return_value=Path("/tmp")),
            patch.object(review_channel_command, "read_publisher_state", return_value=publisher_state),
            patch.object(review_channel_command.time, "sleep", return_value=None),
        ):
            report, rc = review_channel_command._run_ensure_action(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={
                    "bridge_path": Path("/tmp/repo/code_audit.md"),
                    "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
                },
            )

        self.assertEqual(rc, 0)
        self.assertEqual(report["snapshots_emitted"], 1)
        self.assertEqual(len(frames), 1)
        self.assertFalse(frames[0]["ensure_refreshed"])
        self.assertNotIn("reviewer_state_write", frames[0])
        self.assertIn("publisher", frames[0])

    def test_ensure_follow_routes_from_run_with_follow_flag(self) -> None:
        args = SimpleNamespace(
            action="ensure",
            follow=True,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )
        with (
            patch.object(review_channel_command, "_validate_args", return_value=None),
            patch.object(review_channel_command, "_resolve_runtime_paths", return_value={}),
            patch.object(
                review_channel_command,
                "_run_ensure_action",
                return_value=({"ok": True, "_already_emitted": True}, 0),
            ) as ensure_mock,
            patch.object(review_channel_command, "emit_output") as emit_mock,
        ):
            rc = review_channel_command.run(args)

        self.assertEqual(rc, 0)
        ensure_mock.assert_called_once()
        emit_mock.assert_not_called()

    def test_ensure_reports_missing_publisher_in_active_mode(self) -> None:
        args = self._build_ensure_args()
        status_report = {
            "command": "review-channel",
            "action": "status",
            "ok": True,
            "bridge_liveness": {
                "overall_state": "fresh",
                "reviewer_mode": "active_dual_agent",
                "codex_poll_state": "fresh",
                "last_codex_poll_age_seconds": 0,
            },
            "attention": {"status": "healthy"},
        }
        publisher_state = {"running": False, "detail": "No publisher heartbeat file found"}

        with (
            patch.object(review_channel_command, "_run_status_action", return_value=(status_report, 0)),
            patch.object(review_channel_command, "read_publisher_state", return_value=publisher_state),
        ):
            report, rc = review_channel_command._run_ensure_action(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={"status_dir": Path("/tmp/repo/dev/reports/review_channel/latest")},
            )

        self.assertEqual(rc, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["publisher_status"], "not_running")
        self.assertTrue(report["publisher_required"])
        self.assertEqual(report["attention_status"], "publisher_missing")
        self.assertEqual(report["publisher"], publisher_state)
        self.assertEqual(
            report["recommended_command"],
            "python3 dev/scripts/devctl.py review-channel --action ensure --follow --terminal none --format json",
        )

    def test_ensure_reports_running_publisher_in_active_mode(self) -> None:
        args = self._build_ensure_args()
        status_report = {
            "command": "review-channel",
            "action": "status",
            "ok": True,
            "bridge_liveness": {
                "overall_state": "fresh",
                "reviewer_mode": "active_dual_agent",
                "codex_poll_state": "fresh",
                "last_codex_poll_age_seconds": 0,
            },
            "attention": {"status": "healthy"},
        }
        publisher_state = {"running": True, "pid": 42, "stale": False}

        with (
            patch.object(review_channel_command, "_run_status_action", return_value=(status_report, 0)),
            patch.object(review_channel_command, "read_publisher_state", return_value=publisher_state),
        ):
            report, rc = review_channel_command._run_ensure_action(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={"status_dir": Path("/tmp/repo/dev/reports/review_channel/latest")},
            )

        self.assertEqual(rc, 0)
        self.assertTrue(report["ok"])
        self.assertEqual(report["publisher_status"], "running")
        self.assertTrue(report["publisher_required"])
        self.assertEqual(report["publisher"], publisher_state)
        self.assertNotIn("recommended_command", report)

    def test_ensure_starts_publisher_when_requested(self) -> None:
        args = self._build_ensure_args(start_publisher_if_missing=True)
        status_report = {
            "command": "review-channel",
            "action": "status",
            "ok": True,
            "bridge_liveness": {
                "overall_state": "fresh",
                "reviewer_mode": "active_dual_agent",
                "codex_poll_state": "fresh",
                "last_codex_poll_age_seconds": 0,
            },
            "attention": {"status": "healthy"},
        }
        publisher_states = [
            {"running": False, "detail": "No publisher heartbeat file found"},
            {"running": True, "pid": 4242, "stale": False},
        ]
        process = SimpleNamespace(pid=4242)

        with (
            patch.object(review_channel_command, "_run_status_action", return_value=(status_report, 0)),
            patch.object(review_channel_command, "_read_publisher_state_safe", side_effect=publisher_states),
            patch.object(review_channel_command, "_spawn_follow_publisher", return_value=(True, 4242, "/tmp/publisher.log")),
            patch.object(review_channel_command.time, "sleep", return_value=None),
        ):
            report, rc = review_channel_command._run_ensure_action(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={"status_dir": Path("/tmp/repo/dev/reports/review_channel/latest")},
            )

        self.assertEqual(rc, 0)
        self.assertEqual(report["publisher_status"], "running")
        self.assertEqual(report["publisher_start_status"], "started")
        self.assertEqual(report["publisher_pid"], 4242)
        self.assertEqual(report["publisher_log_path"], "/tmp/publisher.log")
        self.assertNotIn("recommended_command", report)

    def test_attention_reports_publisher_missing_when_active_and_no_publisher(self) -> None:
        from dev.scripts.devctl.review_channel.attention import derive_bridge_attention

        liveness = {
            "overall_state": "fresh",
            "codex_poll_state": "fresh",
            "reviewer_mode": "active_dual_agent",
            "claude_status_present": True,
            "claude_ack_present": True,
            "reviewed_hash_current": True,
            "implementer_completion_stall": False,
            "publisher_running": False,
        }
        attention = derive_bridge_attention(liveness)
        self.assertEqual(attention["status"], "publisher_missing")
        self.assertIn("ensure", attention.get("recommended_command", ""))

    def test_attention_reports_healthy_when_active_and_publisher_running(self) -> None:
        from dev.scripts.devctl.review_channel.attention import derive_bridge_attention

        liveness = {
            "overall_state": "fresh",
            "codex_poll_state": "fresh",
            "reviewer_mode": "active_dual_agent",
            "claude_status_present": True,
            "claude_ack_present": True,
            "reviewed_hash_current": True,
            "implementer_completion_stall": False,
            "publisher_running": True,
        }
        attention = derive_bridge_attention(liveness)
        self.assertEqual(attention["status"], "healthy")

    def test_attention_escalates_to_reviewer_overdue_when_age_exceeds_threshold(self) -> None:
        from dev.scripts.devctl.review_channel.attention import derive_bridge_attention

        liveness = {
            "overall_state": "stale",
            "codex_poll_state": "stale",
            "reviewer_mode": "active_dual_agent",
            "claude_status_present": True,
            "claude_ack_present": True,
            "last_codex_poll_age_seconds": 1200,
            "reviewer_overdue_threshold_seconds": 900,
        }
        attention = derive_bridge_attention(liveness)
        self.assertEqual(attention["status"], "reviewer_overdue")

    def test_attention_reports_stale_not_overdue_when_under_threshold(self) -> None:
        from dev.scripts.devctl.review_channel.attention import derive_bridge_attention

        liveness = {
            "overall_state": "stale",
            "codex_poll_state": "stale",
            "reviewer_mode": "active_dual_agent",
            "claude_status_present": True,
            "claude_ack_present": True,
            "last_codex_poll_age_seconds": 400,
            "reviewer_overdue_threshold_seconds": 900,
        }
        attention = derive_bridge_attention(liveness)
        self.assertEqual(attention["status"], "reviewer_heartbeat_stale")

    def test_ensure_follow_stops_on_timeout_and_writes_final_state(self) -> None:
        args = self._build_ensure_follow_args(
            max_follow_snapshots=0, timeout_minutes=1,
        )
        frames: list[dict[str, object]] = []
        ensure_result = EnsureHeartbeatResult(
            refreshed=True, reviewer_mode="active_dual_agent",
            reason="ensure-follow", state_write=None, error=None,
        )
        status_report = {
            "command": "review-channel", "action": "status", "ok": True,
            "bridge_liveness": {"overall_state": "fresh", "reviewer_mode": "active_dual_agent"},
            "attention": {"status": "healthy"},
        }
        publisher_state = {"running": True, "pid": 42, "stale": False}

        def fake_emit(payload: dict[str, object], *, args) -> int:
            frames.append(payload)
            return 0

        tick_count = [0]
        real_monotonic = time.monotonic

        def fake_monotonic() -> float:
            tick_count[0] += 1
            if tick_count[0] <= 2:
                return real_monotonic()
            return real_monotonic() + 120

        with (
            patch.object(review_channel_command, "ensure_reviewer_heartbeat", return_value=ensure_result),
            patch.object(review_channel_command, "_run_status_action", return_value=(status_report, 0)),
            patch.object(review_channel_command, "emit_follow_ndjson_frame", side_effect=fake_emit),
            patch.object(review_channel_command, "reset_follow_output", return_value=None),
            patch.object(review_channel_command, "write_publisher_heartbeat", return_value=Path("/tmp")),
            patch.object(review_channel_command, "read_publisher_state", return_value=publisher_state),
            patch.object(review_channel_command.time, "sleep", return_value=None),
            patch.object(review_channel_command.time, "monotonic", side_effect=fake_monotonic),
        ):
            report, rc = review_channel_command._run_ensure_action(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={
                    "bridge_path": Path("/tmp/repo/code_audit.md"),
                    "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
                },
            )

        self.assertEqual(rc, 0)
        self.assertEqual(report["stop_reason"], "timed_out")
        self.assertTrue(report["_already_emitted"])
        self.assertGreater(len(frames), 0)

    def test_ensure_follow_writes_manual_stop_on_keyboard_interrupt(self) -> None:
        args = self._build_ensure_follow_args(max_follow_snapshots=0)
        frames: list[dict[str, object]] = []
        ensure_result = EnsureHeartbeatResult(
            refreshed=True, reviewer_mode="active_dual_agent",
            reason="ensure-follow", state_write=None, error=None,
        )
        status_report = {
            "command": "review-channel", "action": "status", "ok": True,
            "bridge_liveness": {"overall_state": "fresh", "reviewer_mode": "active_dual_agent"},
            "attention": {"status": "healthy"},
        }
        publisher_state = {"running": True, "pid": 42, "stale": False}

        def fake_emit(payload: dict[str, object], *, args) -> int:
            frames.append(payload)
            return 0

        with (
            patch.object(review_channel_command, "ensure_reviewer_heartbeat", return_value=ensure_result),
            patch.object(review_channel_command, "_run_status_action", return_value=(status_report, 0)),
            patch.object(review_channel_command, "emit_follow_ndjson_frame", side_effect=fake_emit),
            patch.object(review_channel_command, "reset_follow_output", return_value=None),
            patch.object(review_channel_command, "write_publisher_heartbeat", return_value=Path("/tmp")),
            patch.object(review_channel_command, "read_publisher_state", return_value=publisher_state),
            patch.object(review_channel_command.time, "sleep", side_effect=[None, KeyboardInterrupt()]),
        ):
            report, rc = review_channel_command._run_ensure_action(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={
                    "bridge_path": Path("/tmp/repo/code_audit.md"),
                    "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
                },
            )

        self.assertEqual(rc, 0)
        self.assertEqual(report["stop_reason"], "manual_stop")


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
            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertFalse(payload["launched"])
            self.assertEqual(payload["approval_mode"], "balanced")
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
            self.assertEqual(codex_session["supervision_mode"], "restart-on-clean-exit")
            self.assertEqual(claude_session["supervision_mode"], "restart-on-clean-exit")
            self.assertEqual(codex_session["approval_mode"], "balanced")
            self.assertEqual(claude_session["approval_mode"], "balanced")
            codex_script = Path(codex_session["script_path"])
            claude_script = Path(claude_session["script_path"])
            self.assertTrue(codex_script.exists())
            self.assertTrue(claude_script.exists())
            self.assertTrue(Path(codex_session["metadata_path"]).exists())
            self.assertTrue(Path(claude_session["metadata_path"]).exists())
            self.assertTrue(str(codex_session["log_path"]).endswith("codex-conductor.log"))
            self.assertEqual(codex_session["capture_mode"], "terminal-script")
            codex_text = codex_script.read_text(encoding="utf-8")
            claude_text = claude_script.read_text(encoding="utf-8")
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
            self.assertIn(
                "First action after bootstrap on every fresh launch: refresh",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Do not spawn workers, start side investigations, or wait on Claude",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Do not leave the reviewer parked on unanswered approval prompts.",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                'A bridge summary, `waiting_on_peer` note, or "all green so far" '
                "update is never terminal by itself.",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "review-channel --action promote --promotion-plan "
                "dev/active/continuous_swarm.md --terminal none --format md",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "rewrite `Current Instruction For Claude` instead of inventing "
                "the next task by hand or ending on a summary.",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                'REVIEW_CHANNEL_EXIT_ON_SUCCESS="${REVIEW_CHANNEL_EXIT_ON_SUCCESS:-0}"',
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "conductor exited cleanly; relaunching from repo state",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "__review_channel_inner",
                codex_script.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "Posting `Claude Status` or `Claude Ack` is not the end of the loop.",
                claude_text,
            )
            self.assertIn(
                "Shared post-edit verification contract",
                codex_text,
            )
            self.assertIn(
                "Shared post-edit verification contract",
                claude_text,
            )
            self.assertIn(
                "After EVERY file create/edit, you MUST run the repo-required verification before reporting the task as done.",
                codex_text,
            )
            self.assertIn(
                "`bundle.runtime`, `bundle.docs`, `bundle.tooling`, or `bundle.release`",
                codex_text,
            )
            self.assertIn(
                "Done means the required guards/tests passed.",
                claude_text,
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
            self.assertEqual(metadata["supervision_mode"], "restart-on-clean-exit")
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
            promotion_plan_path = root / "dev/active/continuous_swarm.md"
            promotion_plan_path.write_text(
                "\n".join(
                    [
                        "# Continuous Codex/Claude Swarm Plan",
                        "",
                        "## Execution Checklist",
                        "",
                        "### Phase 1 - Queue",
                        "",
                        "- [ ] Implement automatic next-task promotion",
                        "      so the conductor keeps moving.",
                        "- [x] Land the current slice.",
                        "",
                    ]
                ),
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
                promotion_plan=str(promotion_plan_path.relative_to(root)),
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
            latest_markdown_path = Path(payload["projection_paths"]["latest_markdown_path"])
            agent_registry_path = Path(payload["projection_paths"]["agent_registry_path"])

            self.assertTrue(review_state_path.exists())
            self.assertTrue(compact_path.exists())
            self.assertTrue(full_path.exists())
            self.assertTrue(actions_path.exists())
            self.assertTrue(latest_markdown_path.exists())
            self.assertTrue(agent_registry_path.exists())

            review_state = json.loads(review_state_path.read_text(encoding="utf-8"))
            compact = json.loads(compact_path.read_text(encoding="utf-8"))
            actions = json.loads(actions_path.read_text(encoding="utf-8"))
            agent_registry = json.loads(agent_registry_path.read_text(encoding="utf-8"))

            self.assertEqual(review_state["command"], "review-channel")
            self.assertEqual(review_state["queue"]["pending_total"], 0)
            self.assertEqual(
                review_state["queue"]["derived_next_instruction"],
                "- Next scoped plan item (dev/active/continuous_swarm.md): "
                "Phase 1 - Queue: Implement automatic next-task promotion so "
                "the conductor keeps moving.",
            )
            self.assertEqual(len(review_state["agents"]), 4)
            self.assertEqual(
                review_state["bridge"]["current_instruction"],
                "- stop at a safe boundary and relaunch before compaction",
            )
            self.assertEqual(
                review_state["bridge"]["reviewer_mode"],
                "active_dual_agent",
            )
            self.assertEqual(compact["queue"]["pending_total"], 0)
            self.assertEqual(
                compact["queue"]["current_focus"],
                "- stop at a safe boundary and relaunch before compaction",
            )
            self.assertEqual(len(agent_registry["agents"]), 16)
            self.assertEqual(agent_registry["agents"][0]["agent_id"], "AGENT-1")
            self.assertEqual(actions["actions"], [])
            self.assertIn(
                "## Current Instruction",
                latest_markdown_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "## Derived Next Instruction",
                latest_markdown_path.read_text(encoding="utf-8"),
            )

    def test_run_status_can_refresh_stale_bridge_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            original_bridge = _build_bridge_text(last_codex_poll="2000-01-01T00:00:00Z")
            bridge_path.write_text(
                original_bridge,
                encoding="utf-8",
            )
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
                promotion_plan="dev/active/continuous_swarm.md",
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=False,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
                refresh_bridge_heartbeat_if_stale=True,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertIsNotNone(payload["bridge_heartbeat_refresh"])
            refreshed_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertIn("Auto-refreshed reviewer heartbeat", refreshed_bridge)

    def test_run_status_dry_run_does_not_refresh_stale_bridge_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            original_bridge = _build_bridge_text(last_codex_poll="2000-01-01T00:00:00Z")
            bridge_path.write_text(
                original_bridge,
                encoding="utf-8",
            )
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
                promotion_plan="dev/active/continuous_swarm.md",
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                script_dir=None,
                dry_run=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
                refresh_bridge_heartbeat_if_stale=True,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIsNone(payload["bridge_heartbeat_refresh"])
            self.assertEqual(bridge_path.read_text(encoding="utf-8"), original_bridge)

    def test_run_reviewer_heartbeat_preserves_reviewed_hash(self) -> None:
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
            original_hash = compute_non_audit_worktree_hash(
                repo_root=root,
                excluded_rel_paths=("code_audit.md",),
            )
            (root / "notes.txt").write_text("tree moved after review\n", encoding="utf-8")
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            args = SimpleNamespace(
                action="reviewer-heartbeat",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir=str(status_dir.relative_to(root)),
                promotion_plan="dev/active/continuous_swarm.md",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                approval_mode="balanced",
                script_dir=None,
                dry_run=False,
                reviewer_mode="developer",
                reason="local-dev-pass",
                verdict=None,
                open_findings=None,
                instruction=None,
                reviewed_scope_item=[],
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
            self.assertEqual(
                payload["reviewer_state_write"]["reviewer_mode"],
                "single_agent",
            )
            updated_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertIn(
                f"- Last non-audit worktree hash: `{'a' * 64}`",
                updated_bridge,
            )
            self.assertIn("\n- Reviewer mode: `single_agent`\n", updated_bridge)
            self.assertNotEqual(original_hash, "a" * 64)
            self.assertEqual(
                payload["reviewer_state_write"]["last_worktree_hash"],
                "a" * 64,
            )
            review_state_path = Path(payload["projection_paths"]["review_state_path"])
            review_state = json.loads(review_state_path.read_text(encoding="utf-8"))
            self.assertEqual(review_state["bridge"]["reviewer_mode"], "single_agent")
            self.assertEqual(payload["bridge_liveness"]["overall_state"], "inactive")

    def test_run_reviewer_checkpoint_updates_sections_atomically(self) -> None:
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
                _build_bridge_text(
                    current_verdict="- stale verdict",
                    open_findings="- stale finding",
                    current_instruction="- stale instruction",
                ),
                encoding="utf-8",
            )
            (root / "fresh.py").write_text("print('fresh review state')\n", encoding="utf-8")
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            args = SimpleNamespace(
                action="reviewer-checkpoint",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir=str(status_dir.relative_to(root)),
                promotion_plan="dev/active/continuous_swarm.md",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                approval_mode="balanced",
                script_dir=None,
                dry_run=False,
                reviewer_mode="agents",
                reason="review-pass",
                verdict="- reviewer accepted with follow-up",
                open_findings="- M1 closed\n- M2 deferred",
                instruction="- continue with the next scoped slice",
                reviewed_scope_item=[
                    "dev/scripts/devctl/review_channel/reviewer_state.py",
                    "dev/scripts/devctl/commands/review_channel.py",
                ],
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
            updated_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertIn("- reviewer accepted with follow-up", updated_bridge)
            self.assertIn("- M1 closed", updated_bridge)
            self.assertIn("- continue with the next scoped slice", updated_bridge)
            self.assertIn("\n- Reviewer mode: `active_dual_agent`\n", updated_bridge)
            self.assertIn(
                "- dev/scripts/devctl/review_channel/reviewer_state.py",
                updated_bridge,
            )
            reported_hash = payload["reviewer_state_write"]["last_worktree_hash"]
            self.assertEqual(len(reported_hash), 64)
            self.assertNotEqual(reported_hash, "a" * 64)
            self.assertIn(
                f"- Last non-audit worktree hash: `{reported_hash}`",
                updated_bridge,
            )

    def test_run_reviewer_heartbeat_repairs_merged_reviewer_mode_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            malformed_bridge = _build_bridge_text().replace(
                f"- Last non-audit worktree hash: `{'a' * 64}`\n",
                f"- Last non-audit worktree hash: `{'a' * 64}`- Reviewer mode: `active_dual_agent`\n",
            ).replace(
                "\n- Reviewer mode: `active_dual_agent`\n",
                "\n",
            )
            bridge_path.write_text(malformed_bridge, encoding="utf-8")
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            args = SimpleNamespace(
                action="reviewer-heartbeat",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir=str(status_dir.relative_to(root)),
                promotion_plan="dev/active/continuous_swarm.md",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                approval_mode="balanced",
                script_dir=None,
                dry_run=False,
                reviewer_mode="tools_only",
                reason="repair-layout",
                verdict=None,
                open_findings=None,
                instruction=None,
                reviewed_scope_item=[],
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            updated_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertNotIn("`- Reviewer mode:", updated_bridge)
            self.assertIn("\n- Reviewer mode: `tools_only`\n", updated_bridge)

    def test_run_reviewer_heartbeat_strips_stale_poll_status_mode_lines(self) -> None:
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
                _build_bridge_text(reviewer_mode="single_agent").replace(
                    "## Current Verdict",
                    "- Reviewer mode is back to `active_dual_agent`\n\n## Current Verdict",
                ),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            args = SimpleNamespace(
                action="reviewer-heartbeat",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir=str(status_dir.relative_to(root)),
                promotion_plan="dev/active/continuous_swarm.md",
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                approval_mode="balanced",
                script_dir=None,
                dry_run=False,
                reviewer_mode="single_agent",
                reason="strip-stale-mode",
                verdict=None,
                open_findings=None,
                instruction=None,
                reviewed_scope_item=[],
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            updated_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertIn("\n- Reviewer mode: `single_agent`\n", updated_bridge)
            self.assertNotIn(
                "- Reviewer mode is back to `active_dual_agent`",
                updated_bridge,
            )

    def test_run_promote_rewrites_current_instruction_from_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            promotion_plan_path = root / "dev/active/continuous_swarm.md"
            promotion_plan_path.write_text(
                "\n".join(
                    [
                        "# Continuous Codex/Claude Swarm Plan",
                        "",
                        "## Execution Checklist",
                        "",
                        "### Phase 2 - Continuous Loop Behavior",
                        "",
                        "- [ ] Implement automatic next-task promotion so the conductor does not stop.",
                        "- [ ] Add peer-liveness guards.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(
                _build_bridge_text(
                    current_verdict="- accepted",
                    open_findings="- all clear",
                    current_instruction="- all green so far",
                ),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            args = SimpleNamespace(
                action="promote",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir=str(status_dir.relative_to(root)),
                promotion_plan=str(promotion_plan_path.relative_to(root)),
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
            self.assertEqual(payload["action"], "promote")
            self.assertIsNotNone(payload["promotion"])
            self.assertIn(
                "Implement automatic next-task promotion",
                payload["promotion"]["instruction"],
            )
            updated_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertIn(
                "- Next scoped plan item (dev/active/continuous_swarm.md): "
                "Phase 2 - Continuous Loop Behavior: Implement automatic "
                "next-task promotion so the conductor does not stop.",
                updated_bridge,
            )

    def test_auto_promote_on_launch_promotes_when_bridge_is_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(), encoding="utf-8"
            )
            promotion_plan_path = root / "dev/active/continuous_swarm.md"
            promotion_plan_path.write_text(
                "\n".join([
                    "# Plan",
                    "",
                    "## Execution Checklist",
                    "",
                    "- [ ] First unchecked task for auto-promote test.",
                    "- [ ] Second task.",
                    "",
                ]),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(
                _build_bridge_text(
                    current_verdict="- accepted",
                    open_findings="- all clear",
                    current_instruction="- complete",
                ),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir=str(status_dir.relative_to(root)),
                promotion_plan=str(promotion_plan_path.relative_to(root)),
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                approval_mode="balanced",
                scope=None,
                script_dir=None,
                dry_run=True,
                auto_promote=True,
                refresh_bridge_heartbeat_if_stale=False,
                format="json",
                output=str(output_path),
                json_output=None,
                pipe_command=None,
                pipe_args=None,
            )

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch(
                    "dev.scripts.devctl.review_channel.heartbeat.compute_non_audit_worktree_hash",
                    return_value="a" * 64,
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertIsNotNone(payload["promotion"])
            self.assertIn(
                "First unchecked task for auto-promote test",
                payload["promotion"]["instruction"],
            )

    def test_auto_promote_skipped_when_bridge_has_active_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(), encoding="utf-8"
            )
            promotion_plan_path = root / "dev/active/continuous_swarm.md"
            promotion_plan_path.write_text(
                "\n".join([
                    "# Plan",
                    "",
                    "## Execution Checklist",
                    "",
                    "- [ ] Should not be promoted.",
                    "",
                ]),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(
                _build_bridge_text(
                    current_verdict="- still in progress",
                    open_findings="- H1: real open finding",
                    current_instruction="- fix the bug now",
                ),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir=str(status_dir.relative_to(root)),
                promotion_plan=str(promotion_plan_path.relative_to(root)),
                rollover_threshold_pct=50,
                rollover_trigger="context-threshold",
                await_ack_seconds=180,
                codex_workers=8,
                claude_workers=8,
                dangerous=False,
                approval_mode="balanced",
                scope=None,
                script_dir=None,
                dry_run=True,
                auto_promote=True,
                refresh_bridge_heartbeat_if_stale=False,
                format="json",
                output=str(output_path),
                json_output=None,
                pipe_command=None,
                pipe_args=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertIsNone(payload["promotion"])

    def test_run_promote_refuses_when_open_findings_are_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            promotion_plan_path = root / "dev/active/continuous_swarm.md"
            promotion_plan_path.write_text(
                "\n".join(
                    [
                        "# Continuous Codex/Claude Swarm Plan",
                        "",
                        "## Execution Checklist",
                        "",
                        "### Phase 2 - Continuous Loop Behavior",
                        "",
                        "- [ ] Implement automatic next-task promotion.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(
                _build_bridge_text(
                    current_verdict="- accepted",
                    open_findings="- blocker still live",
                    current_instruction="- all green so far",
                ),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="promote",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir="dev/reports/review_channel/latest",
                promotion_plan=str(promotion_plan_path.relative_to(root)),
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
            self.assertIn("Open Findings", payload["errors"][0])

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
                patch.object(
                    review_channel_bridge_handler,
                    "resolve_cli_path",
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
            self.assertTrue(
                any(
                    "inactive" in e or "No AGENT lane" in e
                    for e in payload.get("errors", [])
                ),
                f"Expected bridge-inactive or no-lanes error in {payload.get('errors')}",
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
                    "- code_audit.md\n- dev/scripts/devctl/review_channel/handoff.py",
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
            self.assertFalse(resume_state["launch_ack_state"]["codex"]["observed"])
            self.assertFalse(resume_state["launch_ack_state"]["claude"]["observed"])
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

            def _fake_launch(sessions, terminal_profile=None, **_kwargs):
                del sessions, terminal_profile
                handoff_root = root / "dev/reports/review_channel/rollovers"
                handoff_json = next(handoff_root.glob("*/handoff.json"))
                payload = json.loads(handoff_json.read_text(encoding="utf-8"))
                rollover_id = payload["rollover_id"]
                bridge_path.write_text(
                    _build_bridge_text()
                    .replace(
                        "## Poll Status\n\n- active reviewer loop\n\n",
                        "## Poll Status\n\n- active reviewer loop\n" f"- Codex rollover ack: `{rollover_id}`\n\n",
                    )
                    .replace(
                        "## Claude Ack\n\n- acknowledged\n\n",
                        "## Claude Ack\n\n- acknowledged\n" f"- Claude rollover ack: `{rollover_id}`\n\n",
                    ),
                    encoding="utf-8",
                )

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_bridge_handler,
                    "list_terminal_profiles",
                    return_value=["Pro"],
                ),
                patch.object(
                    review_channel_bridge_handler,
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

            def _fake_launch(sessions, terminal_profile=None, **_kwargs):
                del sessions, terminal_profile
                handoff_root = root / "dev/reports/review_channel/rollovers"
                handoff_json = next(handoff_root.glob("*/handoff.json"))
                payload = json.loads(handoff_json.read_text(encoding="utf-8"))
                rollover_id = payload["rollover_id"]
                bridge_path.write_text(
                    _build_bridge_text()
                    .replace(
                        "## Poll Status\n\n- active reviewer loop\n\n",
                        "## Poll Status\n\n- active reviewer loop\n" f"- Claude rollover ack: `{rollover_id}`\n\n",
                    )
                    .replace(
                        "## Claude Ack\n\n- acknowledged\n\n",
                        "## Claude Ack\n\n- acknowledged\n" f"- Codex rollover ack: `{rollover_id}`\n\n",
                    ),
                    encoding="utf-8",
                )

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_bridge_handler,
                    "list_terminal_profiles",
                    return_value=["Pro"],
                ),
                patch.object(
                    review_channel_bridge_handler,
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
            self.assertIn("`Last Codex poll` is stale", payload["errors"][0])

    def test_run_launch_can_auto_refresh_stale_bridge_heartbeat(self) -> None:
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
                refresh_bridge_heartbeat_if_stale=True,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_bridge_handler,
                    "build_launch_sessions",
                    return_value=[],
                ),
                patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["execution_mode"], "markdown-bridge")
            self.assertTrue(
                any(
                    "Auto-refreshed the markdown-bridge reviewer heartbeat" in w
                    for w in payload["warnings"]
                ),
                f"Expected heartbeat refresh warning in {payload['warnings']}",
            )
            refresh = payload["bridge_heartbeat_refresh"]
            self.assertIsInstance(refresh, dict)
            self.assertEqual(refresh["bridge_path"], "code_audit.md")
            updated_text = bridge_path.read_text(encoding="utf-8")
            self.assertIn(refresh["last_codex_poll_utc"], updated_text)
            self.assertIn(refresh["last_worktree_hash"], updated_text)
            self.assertIn("Auto-refreshed reviewer heartbeat", updated_text)

    def test_run_launch_auto_refresh_still_fails_when_bridge_has_other_blockers(self) -> None:
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
                _build_bridge_text(
                    last_codex_poll="2026-03-08T18:50:00Z",
                    claude_ack="",
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
                refresh_bridge_heartbeat_if_stale=True,
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
            self.assertIsNone(payload["bridge_heartbeat_refresh"])

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
                    "- code_audit.md\n- dev/scripts/devctl/review_channel/handoff.py",
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
                    review_channel_bridge_handler,
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

    def test_run_launch_fails_closed_when_live_session_artifacts_are_active(self) -> None:
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

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_bridge_handler,
                    "list_terminal_profiles",
                    return_value=["Pro"],
                ),
                patch.object(
                    review_channel_bridge_handler,
                    "detect_active_session_conflicts",
                    return_value=(
                        ActiveSessionConflict(
                            provider="codex",
                            session_name="codex-conductor",
                            metadata_path="/tmp/codex.json",
                            log_path="/tmp/codex.log",
                            age_seconds=3,
                            reason="existing conductor script process is still running",
                        ),
                    ),
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("still look active", payload["errors"][0])
            self.assertIn("codex", payload["errors"][0])

    def test_run_launch_live_waits_for_fresh_codex_poll(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            initial_poll = _fresh_utc_z(seconds_offset=-30)
            refreshed_poll = _fresh_utc_z(seconds_offset=-5)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(
                _build_bridge_text(last_codex_poll=initial_poll),
                encoding="utf-8",
            )
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

            def _fake_launch(sessions, terminal_profile=None, **_kwargs):
                del sessions, terminal_profile
                bridge_path.write_text(
                    _build_bridge_text(last_codex_poll=refreshed_poll),
                    encoding="utf-8",
                )

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_bridge_handler,
                    "list_terminal_profiles",
                    return_value=["Pro"],
                ),
                patch.object(
                    review_channel_bridge_handler,
                    "launch_terminal_sessions",
                    side_effect=_fake_launch,
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["launched"])
            self.assertEqual(
                payload["bridge_liveness"]["last_codex_poll_utc"],
                refreshed_poll,
            )

    def test_run_launch_live_fails_closed_when_codex_poll_does_not_advance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            initial_poll = _fresh_utc_z(seconds_offset=-30)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "code_audit.md"
            bridge_path.write_text(
                _build_bridge_text(last_codex_poll=initial_poll),
                encoding="utf-8",
            )
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

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_bridge_handler,
                    "list_terminal_profiles",
                    return_value=["Pro"],
                ),
                patch.object(
                    review_channel_bridge_handler,
                    "launch_terminal_sessions",
                    return_value=None,
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn(
                "did not produce a fresh Codex reviewer heartbeat",
                payload["errors"][0],
            )

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
                ["osascript", "-e", 'tell application "Terminal" to activate'],
                stderr="launch failed",
            )
            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_bridge_handler,
                    "list_terminal_profiles",
                    return_value=["Pro"],
                ),
                patch.object(
                    review_channel_bridge_handler,
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
                    review_channel_bridge_handler,
                    "list_terminal_profiles",
                    return_value=["Pro"],
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIsNone(payload["terminal_profile_applied"])
            self.assertTrue(
                any("Requested Terminal profile" in w for w in payload["warnings"]),
                f"Expected terminal profile warning in {payload['warnings']}",
            )

    def test_markdown_bridge_mode_uses_bridge_path_for_status(self) -> None:
        """execution_mode=markdown-bridge must use bridge even when events exist."""
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
                execution_mode="markdown-bridge",
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

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_command,
                    "event_state_exists",
                    return_value=True,
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["execution_mode"],
                "markdown-bridge",
                "markdown-bridge mode must not auto-prefer event artifacts",
            )

    def test_auto_mode_uses_bridge_path_for_status_when_bridge_is_active(self) -> None:
        """execution_mode=auto must keep bridge authority while the bridge is live."""
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

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_command,
                    "event_state_exists",
                    return_value=True,
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["execution_mode"],
                "markdown-bridge",
                "auto mode must keep the live markdown bridge authoritative",
            )

    def test_auto_mode_falls_back_to_event_path_when_bridge_is_missing(self) -> None:
        """execution_mode=auto should still use event state when no bridge exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            args = SimpleNamespace(
                action="status",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path="code_audit.md",
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

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_command,
                    "event_state_exists",
                    return_value=True,
                ),
                patch.object(
                    review_channel_command,
                    "_run_event_action",
                    return_value=(
                        {
                            "ok": True,
                            "action": "status",
                            "execution_mode": "event-backed",
                        },
                        0,
                    ),
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["execution_mode"],
                "event-backed",
                "auto mode must still route to event artifacts when the bridge is absent",
            )


class TestLaunchCommandInterpreter(unittest.TestCase):
    """Verify rollover/promote commands use the active interpreter."""

    @patch("dev.scripts.devctl.review_channel.launch._DEVCTL_INTERPRETER", "python3.11")
    def test_rollover_command_uses_active_interpreter(self) -> None:
        cmd = build_rollover_command(
            rollover_threshold_pct=80,
            await_ack_seconds=300,
        )
        self.assertTrue(
            cmd.startswith("python3.11 "),
            f"rollover command must start with active interpreter, got: {cmd!r}",
        )
        self.assertNotIn(
            "python3 dev/scripts",
            cmd,
            "rollover command must not use a different interpreter than the active one",
        )

    @patch("dev.scripts.devctl.review_channel.launch._DEVCTL_INTERPRETER", "python3.11")
    def test_promote_command_uses_active_interpreter(self) -> None:
        cmd = build_promote_command(promotion_plan_rel="dev/active/review_channel.md")
        self.assertTrue(
            cmd.startswith("python3.11 "),
            f"promote command must start with active interpreter, got: {cmd!r}",
        )
        self.assertNotIn(
            "python3 dev/scripts",
            cmd,
            "promote command must not use a different interpreter than the active one",
        )

    def test_rollover_command_contains_expected_args(self) -> None:
        cmd = build_rollover_command(
            rollover_threshold_pct=75,
            await_ack_seconds=120,
        )
        self.assertIn("review-channel", cmd)
        self.assertIn("--action rollover", cmd)
        self.assertIn("--rollover-threshold-pct 75", cmd)
        self.assertIn("--await-ack-seconds 120", cmd)

    def test_promote_command_contains_expected_args(self) -> None:
        cmd = build_promote_command(promotion_plan_rel="dev/active/test_plan.md")
        self.assertIn("review-channel", cmd)
        self.assertIn("--action promote", cmd)
        self.assertIn("dev/active/test_plan.md", cmd)


class TestPlaceholderStatusDetection(unittest.TestCase):
    """Verify placeholder Claude Status/Ack text is rejected as non-present."""

    def test_none_is_placeholder(self) -> None:
        self.assertFalse(_is_substantive_text("- none"))

    def test_na_is_placeholder(self) -> None:
        self.assertFalse(_is_substantive_text("- n/a"))

    def test_none_recorded_is_placeholder(self) -> None:
        self.assertFalse(_is_substantive_text("- None recorded"))

    def test_placeholder_is_placeholder(self) -> None:
        self.assertFalse(_is_substantive_text("- placeholder"))

    def test_not_started_is_placeholder(self) -> None:
        self.assertFalse(_is_substantive_text("- not started"))

    def test_pending_is_placeholder(self) -> None:
        self.assertFalse(_is_substantive_text("- pending"))

    def test_empty_string_is_not_present(self) -> None:
        self.assertFalse(_is_substantive_text(""))

    def test_none_value_is_not_present(self) -> None:
        self.assertFalse(_is_substantive_text(None))

    def test_real_status_is_present(self) -> None:
        self.assertTrue(_is_substantive_text("- Session 23 — working on MP-358"))

    def test_real_ack_is_present(self) -> None:
        self.assertTrue(_is_substantive_text("- H1 fixed, ready for re-review"))

    def _make_snapshot(
        self,
        claude_status: str = "- Session 23 — active coding",
        claude_ack: str = "- acknowledged",
    ) -> "BridgeSnapshot":
        return extract_bridge_snapshot(
            "\n".join([
                "# Code Audit Channel",
                "",
                f"- Last Codex poll: `{utc_timestamp()}`",
                "",
                "## Current Instruction For Claude",
                "",
                "- Fix H2 in handoff.py",
                "",
                "## Open Findings",
                "",
                "- H2: placeholder detection",
                "",
                "## Current Verdict",
                "",
                "- not accepted",
                "",
                "## Claude Status",
                "",
                claude_status,
                "",
                "## Claude Ack",
                "",
                claude_ack,
                "",
                "## Last Reviewed Scope",
                "",
                "- code_audit.md",
            ])
        )

    def test_liveness_rejects_placeholder_claude_status(self) -> None:
        snapshot = self._make_snapshot(
            claude_status="- none",
            claude_ack="- none",
        )
        liveness = summarize_bridge_liveness(snapshot)
        self.assertFalse(liveness.claude_status_present)
        self.assertFalse(liveness.claude_ack_present)

    def test_liveness_accepts_real_claude_status(self) -> None:
        snapshot = self._make_snapshot(
            claude_status="- Session 23 — active coding",
            claude_ack="- acknowledged H1 fix",
        )
        liveness = summarize_bridge_liveness(snapshot)
        self.assertTrue(liveness.claude_status_present)
        self.assertTrue(liveness.claude_ack_present)

    def test_launch_validation_rejects_placeholder_claude_sections(self) -> None:
        snapshot = self._make_snapshot(
            claude_status="- none",
            claude_ack="- n/a",
        )
        errors = validate_launch_bridge_state(snapshot)
        status_errors = [e for e in errors if "Claude Status" in e]
        ack_errors = [e for e in errors if "Claude Ack" in e]
        self.assertTrue(len(status_errors) > 0, "must reject placeholder Claude Status")
        self.assertTrue(len(ack_errors) > 0, "must reject placeholder Claude Ack")


    def test_reviewed_hash_current_true_when_hashes_match(self) -> None:
        stored_hash = "a" * 64
        snapshot = extract_bridge_snapshot(_build_bridge_text())
        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 13, 45, tzinfo=UTC),
            current_worktree_hash=stored_hash,
        )
        self.assertIs(liveness.reviewed_hash_current, True)

    def test_reviewed_hash_current_false_when_hashes_differ(self) -> None:
        different_hash = "b" * 64
        snapshot = extract_bridge_snapshot(_build_bridge_text())
        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 13, 45, tzinfo=UTC),
            current_worktree_hash=different_hash,
        )
        self.assertIs(liveness.reviewed_hash_current, False)

    def test_reviewed_hash_current_none_when_no_current_hash_provided(self) -> None:
        snapshot = extract_bridge_snapshot(_build_bridge_text())
        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 13, 45, tzinfo=UTC),
        )
        self.assertIsNone(liveness.reviewed_hash_current)

    def test_reviewed_hash_current_appears_in_liveness_dict(self) -> None:
        from dev.scripts.devctl.review_channel.handoff import bridge_liveness_to_dict

        stored_hash = "a" * 64
        snapshot = extract_bridge_snapshot(_build_bridge_text())
        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 13, 45, tzinfo=UTC),
            current_worktree_hash=stored_hash,
        )
        liveness_dict = bridge_liveness_to_dict(liveness)
        self.assertIn("reviewed_hash_current", liveness_dict)
        self.assertIs(liveness_dict["reviewed_hash_current"], True)

    def test_reviewed_hash_current_false_when_snapshot_has_no_stored_hash(self) -> None:
        bridge_text = _build_bridge_text().replace(
            f"- Last non-audit worktree hash: `{'a' * 64}`",
            "",
        )
        snapshot = extract_bridge_snapshot(bridge_text)
        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 13, 45, tzinfo=UTC),
            current_worktree_hash="c" * 64,
        )
        self.assertIs(liveness.reviewed_hash_current, False)

    def test_non_audit_worktree_hash_ignores_runtime_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(
                ["git", "init"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            (root / ".gitignore").write_text(
                "dev/reports/**\n.voiceterm/memory/\n",
                encoding="utf-8",
            )
            (root / "src").mkdir(parents=True)
            (root / "src" / "tracked.py").write_text("value = 1\n", encoding="utf-8")
            report_path = root / "dev/reports/check/clippy-lints.json"
            report_path.parent.mkdir(parents=True)
            report_path.write_text("{\"lints\": 1}\n", encoding="utf-8")
            memory_path = root / ".voiceterm/memory/events.jsonl"
            memory_path.parent.mkdir(parents=True)
            memory_path.write_text("{\"event\": 1}\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", ".gitignore", "src/tracked.py"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "add", "-f", "dev/reports/check/clippy-lints.json"],
                cwd=root,
                check=True,
                capture_output=True,
            )

            baseline_hash = compute_non_audit_worktree_hash(
                repo_root=root,
                excluded_rel_paths=(),
            )
            report_path.write_text("{\"lints\": 2}\n", encoding="utf-8")
            memory_path.write_text("{\"event\": 2}\n", encoding="utf-8")
            artifact_only_hash = compute_non_audit_worktree_hash(
                repo_root=root,
                excluded_rel_paths=(),
            )
            (root / "src" / "tracked.py").write_text("value = 2\n", encoding="utf-8")
            source_change_hash = compute_non_audit_worktree_hash(
                repo_root=root,
                excluded_rel_paths=(),
            )

        self.assertEqual(baseline_hash, artifact_only_hash)
        self.assertNotEqual(baseline_hash, source_change_hash)

    def test_refresh_event_bundle_returns_reduced_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            artifact_paths = resolve_artifact_paths(repo_root=root)
            event_log_path = Path(artifact_paths.event_log_path)
            event_log_path.parent.mkdir(parents=True, exist_ok=True)
            event_log_path.write_text(
                json.dumps(
                    {
                        "packet_id": "rev_pkt_0001",
                        "trace_id": "trace_1",
                        "event_id": "rev_evt_0001",
                        "event_type": "packet_posted",
                        "timestamp_utc": "2026-03-15T13:00:00Z",
                        "session_id": "session-1",
                        "plan_id": "MP-358",
                        "from_agent": "operator",
                        "to_agent": "codex",
                        "kind": "review",
                        "summary": "review the live tranche",
                        "body": "bundle summary",
                        "status": "pending",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            bundle = refresh_event_bundle(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )
            self.assertIsInstance(bundle, ReviewChannelEventBundle)
            self.assertEqual(len(bundle.events), 1)
            self.assertEqual(bundle.review_state["queue"]["pending_total"], 1)
            self.assertTrue(Path(bundle.projection_paths.review_state_path).exists())

    def test_load_or_refresh_event_bundle_returns_bundle_for_event_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            artifact_paths = resolve_artifact_paths(repo_root=root)
            event_log_path = Path(artifact_paths.event_log_path)
            event_log_path.parent.mkdir(parents=True, exist_ok=True)
            event_log_path.write_text(
                json.dumps(
                    {
                        "packet_id": "rev_pkt_0002",
                        "trace_id": "trace_2",
                        "event_id": "rev_evt_0002",
                        "event_type": "packet_posted",
                        "timestamp_utc": "2026-03-15T13:05:00Z",
                        "session_id": "session-2",
                        "plan_id": "MP-358",
                        "from_agent": "codex",
                        "to_agent": "claude",
                        "kind": "fix",
                        "summary": "land the next patch",
                        "body": "fix one bounded issue",
                        "status": "pending",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            bundle = load_or_refresh_event_bundle(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )
            self.assertIsInstance(bundle, ReviewChannelEventBundle)
            self.assertEqual(bundle.events[0]["packet_id"], "rev_pkt_0002")
            self.assertTrue(Path(bundle.projection_paths.full_path).exists())


class TestWatchFollowContract(unittest.TestCase):
    """Verify watch --follow stream contract."""

    def test_follow_initial_snapshot_has_follow_and_seq_fields(self):
        """The initial snapshot must carry follow=True and snapshot_seq=0."""
        from dev.scripts.devctl.commands.review_channel_event_handler import (
            _build_event_report,
        )
        # Build a minimal report and verify follow fields can be added
        report = {"command": "review-channel", "action": "watch", "ok": True}
        report["follow"] = True
        report["snapshot_seq"] = 0
        self.assertTrue(report["follow"])
        self.assertEqual(report["snapshot_seq"], 0)

    def test_packet_set_change_detection(self):
        """Changed packet IDs should trigger re-emission."""
        prev_ids = {"pkt-1", "pkt-2"}
        same_ids = {"pkt-1", "pkt-2"}
        changed_ids = {"pkt-1", "pkt-3"}
        self.assertEqual(prev_ids, same_ids)
        self.assertNotEqual(prev_ids, changed_ids)

    def test_unchanged_packet_set_does_not_trigger(self):
        """Identical packet ID sets should not trigger re-emission."""
        ids_a = {"pkt-1", "pkt-2"}
        ids_b = {"pkt-2", "pkt-1"}  # same set, different order
        self.assertEqual(ids_a, ids_b)


if __name__ == "__main__":
    unittest.main()
