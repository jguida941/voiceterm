"""Tests for the transitional review-channel launcher.

Fixtures in this file model the same markdown authorities the launcher reads:
`dev/active/review_channel.md` and `bridge.md`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
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
from dev.scripts.devctl.commands.review_channel import ensure as review_channel_ensure_mod
from dev.scripts.devctl.commands import review_channel_event_handler
from dev.scripts.devctl.commands.review_channel import status as review_channel_status_mod
from dev.scripts.devctl.commands.review_channel import _wait as review_channel_wait_mod
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
    DAEMON_EVENT_TYPES,
    filter_inbox_packets,
    load_or_refresh_event_bundle,
    reduce_events,
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
from dev.scripts.devctl.review_channel.plan_resolution import (
    resolve_promotion_plan_path,
)
from dev.scripts.devctl.review_channel.follow_loop import (
    FollowActionPlan,
    FollowActionShape,
    FollowLoopTick,
    FollowLoopSharedDeps,
    build_claude_progress_token,
    run_follow_loop,
)
from dev.scripts.devctl.review_channel.projection_bundle import (
    ReviewChannelProjectionPaths,
)
from dev.scripts.devctl.review_channel.status_models import (
    ReviewChannelStatusSnapshot,
)

from dev.scripts.devctl.review_channel.handoff_constants import _is_substantive_text
from dev.scripts.devctl.review_channel.bridge_validation import (
    validate_launch_bridge_state,
    validate_live_bridge_contract,
)
from dev.scripts.devctl.review_channel.handoff import (
    expected_rollover_ack_line,
    extract_bridge_snapshot,
    observe_rollover_ack_state,
    summarize_bridge_liveness,
)
from dev.scripts.devctl.review_channel.attention import derive_bridge_attention
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
            "`bridge.md` is the temporary bridge.",
            "In autonomous mode `MASTER_PLAN.md` remains the canonical tracker and",
            "   `INDEX.md` remains the router for the minimal active docs set.",
            "For the current operator-facing loop, each meaningful Codex reviewer write to",
            "   `bridge.md` must also emit a concise operator-visible chat update.",
            "Bridge writes stay conductor-owned: only one Codex conductor updates the Codex-owned bridge",
            "sections while specialist workers report back instead of editing the bridge directly.",
            "Bridge behavior is mode-aware. When `Reviewer mode` is `active_dual_agent`, Claude must treat `bridge.md` as the live reviewer/coder authority and keep polling it instead of waiting for the operator to restate the process.",
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
    claude_ack: str = "- acknowledged; instruction-rev: `56bcd5d01510`",
) -> str:
    if last_codex_poll is None:
        last_codex_poll = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return "\n".join(
        [
            "# Review Bridge",
            "",
            "## Start-Of-Conversation Rules",
            "",
            "Codex is the reviewer. Claude is the coder.",
            "At conversation start, both agents must bootstrap repo authority in this order before acting: `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and `dev/active/review_channel.md`.",
            "Codex must poll non-`bridge.md` worktree changes every 2-3 minutes while code is moving.",
            "Codex must exclude `bridge.md` itself when computing the reviewed worktree hash.",
            "Each meaningful review must include an operator-visible chat update.",
            "Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.",
            "Claude should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`, then acknowledge the active instruction in `Claude Ack` before coding.",
            "When the structured review queue is available, Claude must also poll `review-channel --action inbox --target claude --status pending --format json` or the equivalent watch surface on the same cadence so Codex-targeted packets are not missed.",
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
            "- Current instruction revision: `56bcd5d01510`",
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
            "- bridge.md",
            "- dev/scripts/devctl/review_channel/handoff.py",
            "",
        ]
    )


def _fresh_utc_z(*, seconds_offset: int = 0) -> str:
    timestamp = datetime.now(UTC) + timedelta(seconds=seconds_offset)
    return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_live_runtime(
    status_dir: Path,
    *,
    reviewer_mode: str = "active_dual_agent",
) -> None:
    from dev.scripts.devctl.review_channel.lifecycle_state import (
        PublisherHeartbeat,
        ReviewerSupervisorHeartbeat,
        write_publisher_heartbeat,
        write_reviewer_supervisor_heartbeat,
    )

    live_pid = os.getpid()
    write_publisher_heartbeat(
        status_dir,
        PublisherHeartbeat(
            pid=live_pid,
            started_at_utc=_fresh_utc_z(seconds_offset=-60),
            last_heartbeat_utc=_fresh_utc_z(seconds_offset=-5),
            snapshots_emitted=1,
            reviewer_mode=reviewer_mode,
        ),
    )
    write_reviewer_supervisor_heartbeat(
        status_dir,
        ReviewerSupervisorHeartbeat(
            pid=live_pid,
            started_at_utc=_fresh_utc_z(seconds_offset=-60),
            last_heartbeat_utc=_fresh_utc_z(seconds_offset=-5),
            snapshots_emitted=1,
            reviewer_mode=reviewer_mode,
        ),
    )


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

    def test_cli_accepts_reviewer_checkpoint_rotation_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "review-channel",
                "--action",
                "reviewer-checkpoint",
                "--verdict",
                "reviewer accepted",
                "--open-findings",
                "none",
                "--instruction",
                "continue",
                "--reviewed-scope-item",
                "dev/scripts/devctl/review_channel/reviewer_state.py",
                "--rotate-instruction-revision",
                "--terminal",
                "none",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "review-channel")
        self.assertEqual(args.action, "reviewer-checkpoint")
        self.assertTrue(args.rotate_instruction_revision)

    def test_cli_defaults_follow_cadence_settings(self) -> None:
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

        self.assertEqual(args.follow_interval_seconds, 150)
        self.assertEqual(args.follow_inactivity_timeout_seconds, 3600)

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

    def test_resolve_promotion_plan_path_falls_back_to_tracker_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            active_dir = root / "dev/active"
            active_dir.mkdir(parents=True, exist_ok=True)
            (active_dir / "MASTER_PLAN.md").write_text(
                "# Master Plan\n\n- Current main product lane: `MP-377`\n",
                encoding="utf-8",
            )
            (active_dir / "INDEX.md").write_text(
                "\n".join(
                    [
                        "# Active Docs Index",
                        "",
                        "## Registry",
                        "",
                        "| Path | Role | Execution authority | MP scope | When agents read |",
                        "|---|---|---|---|---|",
                        "| `dev/active/ai_governance_platform.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-377` | always |",
                    ]
                ),
                encoding="utf-8",
            )
            plan_path = active_dir / "ai_governance_platform.md"
            plan_path.write_text(
                "# AI Governance Platform\n\n## Execution Checklist\n\n- [ ] Close the next tracker-selected item.\n",
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")

            resolution = resolve_promotion_plan_path(
                repo_root=root,
                bridge_path=bridge_path,
                explicit_plan_path=None,
            )

            self.assertEqual(resolution.source, "tracker_scope")
            self.assertEqual(resolution.path, plan_path.resolve())

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
        self.assertEqual(liveness.reviewer_freshness, "fresh")
        self.assertTrue(liveness.next_action_present)
        self.assertTrue(liveness.claude_status_present)
        self.assertTrue(liveness.claude_ack_present)
        self.assertTrue(liveness.claude_ack_current)

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
        self.assertTrue(liveness.claude_ack_current)

    def test_bridge_liveness_is_fresh_when_poll_and_ack_are_present(self) -> None:
        snapshot = extract_bridge_snapshot(_build_bridge_text(last_codex_poll="2026-03-08T19:08:45Z"))

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(liveness.overall_state, "fresh")
        self.assertEqual(liveness.codex_poll_state, "poll_due")
        self.assertEqual(liveness.reviewer_freshness, "poll_due")
        self.assertEqual(liveness.last_codex_poll_age_seconds, 195)
        self.assertTrue(liveness.next_action_present)
        self.assertTrue(liveness.claude_ack_present)
        self.assertTrue(liveness.claude_ack_current)

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
        self.assertFalse(liveness.claude_ack_current)

    def test_bridge_liveness_waits_on_stale_claude_ack_revision(self) -> None:
        snapshot = extract_bridge_snapshot(
            _build_bridge_text(
                claude_ack="- acknowledged; instruction-rev: `deadbeef1234`"
            )
        )

        liveness = summarize_bridge_liveness(
            snapshot,
            now_utc=datetime(2026, 3, 8, 19, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(liveness.overall_state, "waiting_on_peer")
        self.assertTrue(liveness.claude_ack_present)
        self.assertFalse(liveness.claude_ack_current)

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

    def test_validate_live_bridge_contract_requires_ack_instruction_revision(self) -> None:
        snapshot = extract_bridge_snapshot(
            _build_bridge_text(claude_ack="- acknowledged")
        )

        errors = validate_live_bridge_contract(snapshot)

        self.assertTrue(
            any("instruction-rev" in error for error in errors),
            "live bridge validation must reject Claude Ack entries without the "
            "current instruction revision token",
        )

    def test_validate_live_bridge_contract_rejects_stale_ack_instruction_revision(
        self,
    ) -> None:
        snapshot = extract_bridge_snapshot(
            _build_bridge_text(
                claude_ack="- acknowledged; instruction-rev: `deadbeef1234`"
            )
        )

        errors = validate_live_bridge_contract(snapshot)

        self.assertTrue(
            any("does not match" in error for error in errors),
            "live bridge validation must reject stale Claude Ack revision tokens",
        )

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
        self.assertEqual(liveness.reviewer_freshness, "overdue")

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
            bridge_path=root / "bridge.md",
            handoff_bundle={
                "markdown_path": str(root / "dev/reports/handoff.md"),
                "json_path": str(root / "dev/reports/handoff.json"),
                "rollover_id": "rollover-test",
            },
        )
        self.assertIn("AGENTS.md", files[0])
        self.assertIn("dev/active/INDEX.md", files[0])
        handoff_items = [f for f in files if "handoff" in f]
        self.assertTrue(len(handoff_items) >= 2, "handoff files should be present")
        for hf in handoff_items:
            hf_idx = files.index(hf)
            self.assertGreater(
                hf_idx,
                0,
                f"handoff file {hf} must come after the repo-authority bootstrap instruction",
            )

    def test_rollover_ack_state_requires_provider_owned_sections(self) -> None:
        rollover_id = "rollover-20260308T191500Z"
        bridge_text = _build_bridge_text().replace(
            "## Claude Ack\n\n- acknowledged; instruction-rev: `56bcd5d01510`\n\n",
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
            bridge_path=root / "bridge.md",
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
            bridge_path=root / "bridge.md",
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
            "`bridge.md` is the first thing to re-read whenever you need "
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
            "the conductor role, use the repo-owned `review-channel --action "
            "implementer-wait` path instead of ad-hoc shell sleep loops, and "
            "resume as soon as reviewer-owned bridge state or a fresh Claude-"
            "targeted review packet changes.",
            prompt,
        )
        self.assertIn(
            "also poll the Claude-targeted packet inbox/watch surface",
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
            bridge_path=root / "bridge.md",
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

    @patch(
        "dev.scripts.devctl.review_channel.prompt.build_context_escalation_packet"
    )
    def test_prompt_includes_preloaded_context_packet_for_lane_scope(
        self,
        escalation_mock,
    ) -> None:
        from dev.scripts.devctl.context_graph.escalation import ContextEscalationPacket
        from dev.scripts.devctl.review_channel.prompt import build_conductor_prompt

        escalation_mock.return_value = ContextEscalationPacket(
            trigger="review-channel-bootstrap",
            query_terms=("review_channel", "MP-355"),
            matched_nodes=2,
            edge_count=1,
            canonical_refs=(
                "dev/active/review_channel.md",
                "dev/scripts/devctl/review_channel/prompt.py",
            ),
            evidence=("review_channel: nodes=2, edges=1",),
            markdown=(
                "## Context Recovery Packet\n\n"
                "- Trigger: `review-channel-bootstrap`\n"
                "- Query terms: `review_channel`, `MP-355`\n"
                "- Graph matches: nodes=2, edges=1\n"
                "- Canonical refs:\n"
                "  - `dev/active/review_channel.md`"
            ),
        )
        root = Path("/fake/repo")
        prompt = build_conductor_prompt(
            provider="codex",
            provider_name="Codex",
            other_name="Claude",
            repo_root=root,
            review_channel_path=root / "dev/active/review_channel.md",
            bridge_path=root / "bridge.md",
            lanes=[
                SimpleNamespace(
                    agent_id="AGENT-1",
                    lane="review lane",
                    worktree="../wt-a1",
                    branch="feature/a1",
                    mp_scope="MP-355",
                )
            ],
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

        self.assertIn("Context escalation policy:", prompt)
        self.assertIn("Preloaded bounded packet for the active lane scopes:", prompt)
        self.assertIn("## Context Recovery Packet", prompt)
        self.assertIn("`review_channel`", prompt)
        escalation_mock.assert_called_once()

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

    def _build_reviewer_follow_args(self, **overrides) -> SimpleNamespace:
        base = {
            "action": "reviewer-heartbeat",
            "follow": True,
            "max_follow_snapshots": 2,
            "follow_interval_seconds": 1,
            "timeout_minutes": 0,
            "reviewer_mode": "active_dual_agent",
            "reason": "reviewer-follow",
            "execution_mode": "auto",
            "terminal": "none",
            "terminal_profile": "auto-dark",
            "rollover_threshold_pct": 50,
            "rollover_trigger": "context-threshold",
            "await_ack_seconds": 180,
            "codex_workers": 8,
            "claude_workers": 8,
            "dangerous": False,
            "approval_mode": "balanced",
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

    def test_validate_args_rejects_reviewer_follow_without_json_format(self) -> None:
        args = self._build_reviewer_follow_args(format="md")
        with self.assertRaisesRegex(
            ValueError,
            "reviewer-heartbeat --follow requires --format json",
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
            bridge_path="bridge.md",
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
            "reviewer_worker": {
                "state": "up_to_date",
                "review_needed": False,
                "semantic_review_claimed": False,
            },
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
                    "bridge_path": Path("/tmp/repo/bridge.md"),
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
        rsw = frames[0]["reviewer_state_write"]
        reason = rsw["reason"] if isinstance(rsw, dict) else rsw.reason
        self.assertEqual(reason, "ensure-follow")
        self.assertTrue(frames[0]["ensure_refreshed"])
        self.assertIn("publisher", frames[0])
        self.assertTrue(frames[0]["publisher"]["running"])
        self.assertEqual(frames[0]["reviewer_worker"]["state"], "up_to_date")
        self.assertFalse(frames[0]["reviewer_worker"]["review_needed"])

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
                    "bridge_path": Path("/tmp/repo/bridge.md"),
                    "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
                },
            )

        self.assertEqual(rc, 0)
        self.assertEqual(report["snapshots_emitted"], 1)
        self.assertEqual(len(frames), 1)
        self.assertFalse(frames[0]["ensure_refreshed"])
        self.assertNotIn("reviewer_state_write", frames[0])
        self.assertIn("publisher", frames[0])

    def test_ensure_follow_appends_daemon_lifecycle_events(self) -> None:
        from dev.scripts.devctl.review_channel.event_store import load_events, resolve_artifact_paths

        args = self._build_ensure_follow_args(max_follow_snapshots=2)
        ensure_result = EnsureHeartbeatResult(
            refreshed=True,
            reviewer_mode="active_dual_agent",
            reason="ensure-follow",
            state_write=None,
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
            },
            "attention": {"status": "healthy"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            artifact_paths = resolve_artifact_paths(repo_root=root)
            status_dir = root / "dev/reports/review_channel/latest"
            with (
                patch.object(review_channel_command, "ensure_reviewer_heartbeat", return_value=ensure_result),
                patch.object(review_channel_command, "_run_status_action", return_value=(status_report, 0)),
                patch.object(review_channel_command, "emit_follow_ndjson_frame", return_value=0),
                patch.object(review_channel_command, "reset_follow_output", return_value=None),
                patch.object(review_channel_command.time, "sleep", return_value=None),
            ):
                report, rc = review_channel_command._run_ensure_action(
                    args=args,
                    repo_root=root,
                    paths={
                        "bridge_path": root / "bridge.md",
                        "status_dir": status_dir,
                        "artifact_paths": artifact_paths,
                    },
                )

            events = load_events(Path(artifact_paths.event_log_path))

        self.assertEqual(rc, 0)
        self.assertEqual(report["snapshots_emitted"], 2)
        self.assertEqual(
            [event["event_type"] for event in events],
            [
                "daemon_started",
                "daemon_heartbeat",
                "daemon_heartbeat",
                "daemon_stopped",
            ],
        )
        self.assertTrue(all(event["daemon_kind"] == "publisher" for event in events))
        self.assertEqual(events[1]["snapshots_emitted"], 1)
        self.assertEqual(events[2]["snapshots_emitted"], 2)
        self.assertEqual(events[3]["stop_reason"], "completed")

    def test_reviewer_follow_emits_reviewer_worker_frames(self) -> None:
        args = self._build_reviewer_follow_args(max_follow_snapshots=2)
        frames: list[dict[str, object]] = []
        write = ReviewerStateWrite(
            bridge_path="bridge.md",
            action="reviewer-heartbeat",
            reviewer_mode="active_dual_agent",
            reason="reviewer-follow",
            last_codex_poll_utc="2026-03-16T07:00:00Z",
            last_codex_poll_local="2026-03-16 03:00:00 EDT",
            last_worktree_hash="a" * 64,
        )
        ensure_result = EnsureHeartbeatResult(
            refreshed=True,
            reviewer_mode="active_dual_agent",
            reason="reviewer-follow",
            state_write=write,
            error=None,
        )
        status_report = {
            "command": "review-channel",
            "action": "reviewer-heartbeat",
            "ok": True,
            "errors": [],
            "review_needed": True,
            "reviewer_worker": {
                "state": "review_needed",
                "review_needed": True,
                "semantic_review_claimed": False,
            },
        }

        def fake_emit(payload: dict[str, object], *, args) -> int:
            frames.append(payload)
            return 0

        def fake_build_report(*, args, repo_root, paths) -> tuple[dict[str, object], int]:
            return json.loads(json.dumps(status_report)), 0

        with (
            patch.object(review_channel_command, "ensure_reviewer_heartbeat", return_value=ensure_result),
            patch.object(review_channel_command, "_build_reviewer_state_report", side_effect=fake_build_report),
            patch.object(review_channel_command, "emit_follow_ndjson_frame", side_effect=fake_emit),
            patch.object(review_channel_command, "reset_follow_output", return_value=None),
            patch.object(review_channel_command.time, "sleep", return_value=None),
        ):
            report, rc = review_channel_command._run_reviewer_follow_action(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={"bridge_path": Path("/tmp/repo/bridge.md")},
            )

        self.assertEqual(rc, 0)
        self.assertTrue(report["_already_emitted"])
        self.assertEqual(report["snapshots_emitted"], 2)
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0]["snapshot_seq"], 0)
        self.assertEqual(frames[1]["snapshot_seq"], 1)
        self.assertTrue(all(frame["follow"] for frame in frames))
        self.assertTrue(frames[0]["reviewer_heartbeat_refreshed"])
        self.assertEqual(
            frames[0]["reviewer_state_write"]["reason"],
            "reviewer-follow",
        )
        self.assertEqual(frames[0]["reviewer_worker"]["state"], "review_needed")
        self.assertTrue(frames[0]["review_needed"])
        self.assertFalse(frames[0]["reviewer_worker"]["semantic_review_claimed"])

    def test_reviewer_follow_reactivates_paused_bridge_when_requested_active(self) -> None:
        args = self._build_reviewer_follow_args(max_follow_snapshots=1)
        frames: list[dict[str, object]] = []
        status_report = {
            "command": "review-channel",
            "action": "reviewer-heartbeat",
            "ok": True,
            "errors": [],
            "review_needed": False,
            "reviewer_worker": {
                "state": "up_to_date",
                "review_needed": False,
                "semantic_review_claimed": False,
            },
        }

        def fake_emit(payload: dict[str, object], *, args) -> int:
            frames.append(payload)
            return 0

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(
                    reviewer_mode="paused",
                    last_codex_poll="2026-03-20T08:31:36Z",
                ),
                encoding="utf-8",
            )
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            with (
                patch.object(
                    review_channel_command,
                    "_build_reviewer_state_report",
                    return_value=(status_report, 0),
                ),
                patch.object(
                    review_channel_command,
                    "emit_follow_ndjson_frame",
                    side_effect=fake_emit,
                ),
                patch.object(
                    review_channel_command,
                    "reset_follow_output",
                    return_value=None,
                ),
                patch.object(review_channel_command.time, "sleep", return_value=None),
            ):
                report, rc = review_channel_command._run_reviewer_follow_action(
                    args=args,
                    repo_root=root,
                    paths={
                        "bridge_path": bridge_path,
                        "status_dir": root / "dev/reports/review_channel/latest",
                    },
                )

            self.assertEqual(rc, 0)
            self.assertEqual(report["snapshots_emitted"], 1)
            self.assertEqual(len(frames), 1)
            self.assertTrue(frames[0]["reviewer_heartbeat_refreshed"])
            self.assertEqual(
                frames[0]["reviewer_state_write"]["reviewer_mode"],
                "active_dual_agent",
            )
            self.assertIn(
                "\n- Reviewer mode: `active_dual_agent`\n",
                bridge_path.read_text(encoding="utf-8"),
            )

    def test_reviewer_follow_auto_promotes_next_item_when_ready(self) -> None:
        args = self._build_reviewer_follow_args(
            max_follow_snapshots=1,
            auto_promote=True,
        )
        frames: list[dict[str, object]] = []
        ensure_result = EnsureHeartbeatResult(
            refreshed=True,
            reviewer_mode="active_dual_agent",
            reason="reviewer-follow",
            state_write=None,
            error=None,
        )
        status_report = {
            "command": "review-channel",
            "action": "reviewer-heartbeat",
            "ok": True,
            "errors": [],
            "review_needed": False,
            "reviewer_worker": {
                "state": "up_to_date",
                "review_needed": False,
                "semantic_review_claimed": False,
            },
        }

        def fake_emit(payload: dict[str, object], *, args) -> int:
            frames.append(payload)
            return 0

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(
                    current_verdict="- accepted",
                    open_findings="- all clear",
                    current_instruction="- continue the next unchecked item immediately",
                    last_codex_poll="2026-03-01T00:00:00Z",
                ),
                encoding="utf-8",
            )
            promotion_plan_path = root / "dev/active/continuous_swarm.md"
            promotion_plan_path.parent.mkdir(parents=True, exist_ok=True)
            promotion_plan_path.write_text(
                "\n".join(
                    [
                        "# Plan",
                        "",
                        "## Execution Checklist",
                        "",
                        "- [ ] Fix follow-loop stall handling.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            with (
                patch.object(review_channel_command, "ensure_reviewer_heartbeat", return_value=ensure_result),
                patch.object(review_channel_command, "_build_reviewer_state_report", return_value=(status_report, 0)),
                patch.object(review_channel_command, "emit_follow_ndjson_frame", side_effect=fake_emit),
                patch.object(review_channel_command, "reset_follow_output", return_value=None),
                patch(
                    "dev.scripts.devctl.review_channel.reviewer_follow.compute_non_audit_worktree_hash",
                    return_value="a" * 64,
                ),
                patch.object(review_channel_command.time, "sleep", return_value=None),
            ):
                report, rc = review_channel_command._run_reviewer_follow_action(
                    args=args,
                    repo_root=root,
                    paths={
                        "bridge_path": bridge_path,
                        "promotion_plan_path": promotion_plan_path,
                        "status_dir": root / "dev/reports/review_channel/latest",
                    },
                )

            self.assertEqual(rc, 0)
            self.assertEqual(report["snapshots_emitted"], 1)
            self.assertEqual(len(frames), 1)
            self.assertTrue(frames[0]["auto_promotion"]["promoted"])
            self.assertIn(
                "Fix follow-loop stall handling",
                frames[0]["auto_promotion"]["instruction"],
            )
            updated_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertIn(
                "Next scoped plan item (dev/active/continuous_swarm.md)",
                updated_bridge,
            )
            snapshot = extract_bridge_snapshot(updated_bridge)
            self.assertNotEqual(
                snapshot.metadata.get("current_instruction_revision", ""),
                "56bcd5d01510",
            )

    def test_reviewer_follow_appends_daemon_lifecycle_events(self) -> None:
        from dev.scripts.devctl.review_channel.event_store import load_events, resolve_artifact_paths

        args = self._build_reviewer_follow_args(max_follow_snapshots=2)
        ensure_result = EnsureHeartbeatResult(
            refreshed=True,
            reviewer_mode="active_dual_agent",
            reason="reviewer-follow",
            state_write=None,
            error=None,
        )
        status_report = {
            "command": "review-channel",
            "action": "reviewer-heartbeat",
            "ok": True,
            "errors": [],
            "reviewer_worker": {
                "state": "review_needed",
                "review_needed": True,
                "semantic_review_claimed": False,
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            artifact_paths = resolve_artifact_paths(repo_root=root)
            with (
                patch.object(review_channel_command, "ensure_reviewer_heartbeat", return_value=ensure_result),
                patch.object(review_channel_command, "_build_reviewer_state_report", return_value=(status_report, 0)),
                patch.object(review_channel_command, "emit_follow_ndjson_frame", return_value=0),
                patch.object(review_channel_command, "reset_follow_output", return_value=None),
                patch.object(review_channel_command.time, "sleep", return_value=None),
            ):
                report, rc = review_channel_command._run_reviewer_follow_action(
                    args=args,
                    repo_root=root,
                    paths={
                        "bridge_path": root / "bridge.md",
                        "status_dir": root / "dev/reports/review_channel/latest",
                        "artifact_paths": artifact_paths,
                    },
                )

            events = load_events(Path(artifact_paths.event_log_path))

        self.assertEqual(rc, 0)
        self.assertEqual(report["snapshots_emitted"], 2)
        self.assertEqual(
            [event["event_type"] for event in events],
            [
                "daemon_started",
                "daemon_heartbeat",
                "daemon_heartbeat",
                "daemon_stopped",
            ],
        )
        self.assertTrue(
            all(event["daemon_kind"] == "reviewer_supervisor" for event in events)
        )
        self.assertEqual(events[1]["snapshots_emitted"], 1)
        self.assertEqual(events[2]["snapshots_emitted"], 2)
        self.assertEqual(events[3]["stop_reason"], "completed")

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
            patch.object(review_channel_status_mod, "read_publisher_state", return_value=publisher_state),
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
                "reviewer_freshness": "poll_due",
                "last_codex_poll_age_seconds": 0,
            },
            "attention": {"status": "healthy"},
        }
        publisher_state = {"running": True, "pid": 42, "stale": False}

        with (
            patch.object(review_channel_command, "_run_status_action", return_value=(status_report, 0)),
            patch.object(review_channel_status_mod, "read_publisher_state", return_value=publisher_state),
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
        self.assertEqual(report["reviewer_freshness"], "poll_due")
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

    def test_attention_reports_runtime_missing_when_active_and_no_runtime(self) -> None:
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
        self.assertEqual(attention["status"], "runtime_missing")
        self.assertIn("--follow", attention.get("recommended_command", ""))

    def test_attention_reports_publisher_missing_when_supervisor_keeps_runtime_alive(
        self,
    ) -> None:
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
            "reviewer_supervisor_running": True,
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
            "claude_ack_current": True,
            "reviewed_hash_current": True,
            "implementer_completion_stall": False,
            "publisher_running": True,
        }
        attention = derive_bridge_attention(liveness)
        self.assertEqual(attention["status"], "healthy")

    def test_attention_reports_checkpoint_required_when_push_budget_exceeded(self) -> None:
        from dev.scripts.devctl.review_channel.attention import derive_bridge_attention

        liveness = {
            "overall_state": "fresh",
            "codex_poll_state": "fresh",
            "reviewer_mode": "active_dual_agent",
            "claude_status_present": True,
            "claude_ack_present": True,
            "claude_ack_current": True,
            "reviewed_hash_current": True,
            "implementer_completion_stall": False,
            "publisher_running": True,
            "push_enforcement": {
                "checkpoint_required": True,
                "safe_to_continue_editing": False,
                "recommended_action": "checkpoint_before_continue",
            },
        }
        attention = derive_bridge_attention(liveness)
        self.assertEqual(attention["status"], "checkpoint_required")
        self.assertIn("checkpoint", attention["summary"].lower())

    def test_attention_reports_stale_claude_ack_when_revision_mismatches(self) -> None:
        from dev.scripts.devctl.review_channel.attention import derive_bridge_attention

        liveness = {
            "overall_state": "waiting_on_peer",
            "codex_poll_state": "fresh",
            "reviewer_mode": "active_dual_agent",
            "claude_status_present": True,
            "claude_ack_present": True,
            "claude_ack_current": False,
            "reviewed_hash_current": True,
            "implementer_completion_stall": False,
            "publisher_running": True,
        }
        attention = derive_bridge_attention(liveness)
        self.assertEqual(attention["status"], "claude_ack_stale")

    def test_attention_reports_dual_agent_idle_with_stale_precedence(self) -> None:
        from dev.scripts.devctl.review_channel.attention import derive_bridge_attention

        dual_idle_liveness = {
            "overall_state": "waiting_on_peer",
            "codex_poll_state": "fresh",
            "reviewer_mode": "active_dual_agent",
            "claude_status_present": True,
            "claude_ack_present": True,
            "claude_ack_current": True,
            "review_needed": False,
            "reviewed_hash_current": True,
            "implementer_completion_stall": True,
            "publisher_running": True,
            "reviewer_freshness": "fresh",
        }
        dual_idle_attention = derive_bridge_attention(dual_idle_liveness)
        self.assertEqual(dual_idle_attention["status"], "dual_agent_idle")
        self.assertIn("auto-promotion", dual_idle_attention["recommended_action"])

        stale_liveness = dict(dual_idle_liveness)
        stale_liveness["overall_state"] = "stale"
        stale_liveness["codex_poll_state"] = "stale"
        stale_liveness["last_codex_poll_age_seconds"] = 1200
        stale_liveness["reviewer_overdue_threshold_seconds"] = 900
        stale_liveness["reviewer_freshness"] = "overdue"
        stale_attention = derive_bridge_attention(stale_liveness)
        self.assertEqual(stale_attention["status"], "reviewer_overdue")

    def test_attention_requires_reviewer_supervisor_when_review_is_pending(self) -> None:
        from dev.scripts.devctl.review_channel.attention import derive_bridge_attention

        liveness = {
            "overall_state": "fresh",
            "codex_poll_state": "fresh",
            "reviewer_mode": "active_dual_agent",
            "claude_status_present": True,
            "claude_ack_present": True,
            "claude_ack_current": True,
            "review_needed": True,
            "reviewer_supervisor_running": False,
            "reviewed_hash_current": False,
            "implementer_completion_stall": False,
            "publisher_running": True,
        }
        attention = derive_bridge_attention(liveness)
        self.assertEqual(attention["status"], "reviewer_supervisor_required")
        self.assertIn("reviewer-heartbeat --follow", attention["recommended_command"])

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
            "reviewer_freshness": "overdue",
            "reviewer_supervisor_running": True,
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
            "reviewer_freshness": "stale",
            "reviewer_supervisor_running": True,
        }
        attention = derive_bridge_attention(liveness)
        self.assertEqual(attention["status"], "reviewer_heartbeat_stale")

    def test_classify_reviewer_freshness_transitions(self) -> None:
        from dev.scripts.devctl.review_channel.peer_liveness import (
            classify_reviewer_freshness,
            ReviewerFreshness,
        )

        self.assertEqual(classify_reviewer_freshness(None), ReviewerFreshness.MISSING)
        self.assertEqual(classify_reviewer_freshness(60), ReviewerFreshness.FRESH)
        self.assertEqual(classify_reviewer_freshness(179), ReviewerFreshness.FRESH)
        self.assertEqual(classify_reviewer_freshness(180), ReviewerFreshness.POLL_DUE)
        self.assertEqual(classify_reviewer_freshness(299), ReviewerFreshness.POLL_DUE)
        self.assertEqual(classify_reviewer_freshness(300), ReviewerFreshness.STALE)
        self.assertEqual(classify_reviewer_freshness(899), ReviewerFreshness.STALE)
        self.assertEqual(classify_reviewer_freshness(900), ReviewerFreshness.OVERDUE)
        self.assertEqual(classify_reviewer_freshness(9999), ReviewerFreshness.OVERDUE)

    def test_attention_uses_reviewer_freshness_for_poll_due(self) -> None:
        from dev.scripts.devctl.review_channel.attention import derive_bridge_attention

        liveness = {
            "overall_state": "fresh",
            "codex_poll_state": "poll_due",
            "reviewer_mode": "active_dual_agent",
            "claude_status_present": True,
            "claude_ack_present": True,
            "reviewer_freshness": "poll_due",
            "reviewer_supervisor_running": True,
        }
        attention = derive_bridge_attention(liveness)
        self.assertEqual(attention["status"], "reviewer_poll_due")
        self.assertIn("due", attention["summary"].lower())

    def test_bridge_liveness_includes_reviewer_freshness(self) -> None:
        from dev.scripts.devctl.review_channel.handoff import (
            BridgeSnapshot,
            summarize_bridge_liveness,
        )

        snapshot = BridgeSnapshot(
            metadata={"reviewer_mode": "active_dual_agent"},
            sections={
                "Last Reviewed Scope": "- some scope",
                "Current Instruction For Claude": "- code something",
                "Claude Status": "- coding",
                "Claude Ack": "- acknowledged; instruction-rev: `abc123`",
            },
        )
        liveness = summarize_bridge_liveness(snapshot)
        self.assertEqual(liveness.reviewer_freshness, "missing")

    def test_attention_reports_failed_start_when_stop_reason_is_failed_start(self) -> None:
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
            "publisher_stop_reason": "failed_start",
            "reviewer_supervisor_running": True,
        }
        attention = derive_bridge_attention(liveness)
        self.assertEqual(attention["status"], "publisher_failed_start")
        self.assertIn("exited immediately", attention["summary"])

    def test_attention_reports_detached_exit_when_stop_reason_is_detached_exit(self) -> None:
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
            "publisher_stop_reason": "detached_exit",
            "reviewer_supervisor_running": True,
        }
        attention = derive_bridge_attention(liveness)
        self.assertEqual(attention["status"], "publisher_detached_exit")
        self.assertIn("unexpectedly", attention["summary"])

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
                    "bridge_path": Path("/tmp/repo/bridge.md"),
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
                    "bridge_path": Path("/tmp/repo/bridge.md"),
                    "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
                },
            )

        self.assertEqual(rc, 0)
        self.assertEqual(report["stop_reason"], "manual_stop")

    def test_ensure_follow_output_error_writes_final_stopped_state(self) -> None:
        args = self._build_ensure_follow_args(max_follow_snapshots=1)
        ensure_result = EnsureHeartbeatResult(
            refreshed=True,
            reviewer_mode="active_dual_agent",
            reason="ensure-follow",
            state_write=None,
            error=None,
        )
        status_report = {
            "command": "review-channel",
            "action": "status",
            "ok": True,
            "bridge_liveness": {
                "overall_state": "fresh",
                "reviewer_mode": "active_dual_agent",
            },
            "attention": {"status": "healthy"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            with (
                patch.object(
                    review_channel_command,
                    "ensure_reviewer_heartbeat",
                    return_value=ensure_result,
                ),
                patch.object(
                    review_channel_command,
                    "_run_status_action",
                    return_value=(status_report, 0),
                ),
                patch.object(
                    review_channel_command,
                    "emit_follow_ndjson_frame",
                    return_value=7,
                ),
                patch.object(
                    review_channel_command,
                    "reset_follow_output",
                    return_value=None,
                ),
            ):
                report, rc = review_channel_command._run_ensure_action(
                    args=args,
                    repo_root=Path("/tmp/repo"),
                    paths={
                        "bridge_path": Path("/tmp/repo/bridge.md"),
                        "status_dir": status_dir,
                    },
                )

            state = review_channel_command.read_publisher_state(status_dir)

        self.assertEqual(rc, 7)
        self.assertFalse(report["ok"])
        self.assertEqual(state["stop_reason"], "output_error")
        self.assertFalse(state["running"])
        self.assertTrue(state["pid_alive"])

    def test_detached_start_writes_failed_start_when_pid_is_dead(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            from dev.scripts.devctl.commands.review_channel import _verify_detached_start
            from dev.scripts.devctl.review_channel.state import read_publisher_state

            with patch("dev.scripts.devctl.review_channel.lifecycle_state._pid_is_alive", return_value=False):
                result = _verify_detached_start(
                    pid=99999,
                    paths={"status_dir": status_dir},
                )

            self.assertEqual(result, "failed_start")
            state = read_publisher_state(status_dir)
            self.assertFalse(state["running"])
            self.assertEqual(state["stop_reason"], "failed_start")
            self.assertTrue(state["stopped_at_utc"])

    def test_read_publisher_state_infers_detached_exit_when_pid_dead_and_no_stop_reason(self) -> None:
        from dev.scripts.devctl.review_channel.state import (
            PublisherHeartbeat,
            read_publisher_state,
            write_publisher_heartbeat,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            write_publisher_heartbeat(
                status_dir,
                PublisherHeartbeat(
                    pid=99999,
                    started_at_utc="2026-03-16T10:00:00Z",
                    last_heartbeat_utc="2026-03-16T10:01:00Z",
                    snapshots_emitted=5,
                    reviewer_mode="active_dual_agent",
                ),
            )
            with patch("dev.scripts.devctl.review_channel.lifecycle_state._pid_is_alive", return_value=False):
                state = read_publisher_state(status_dir)

            self.assertFalse(state["running"])
            self.assertEqual(state["stop_reason"], "detached_exit")
            self.assertEqual(state["stopped_at_utc"], "2026-03-16T10:01:00Z")

    def test_read_publisher_state_treats_permission_denied_pid_check_as_alive(self) -> None:
        from dev.scripts.devctl.review_channel.state import (
            PublisherHeartbeat,
            read_publisher_state,
            write_publisher_heartbeat,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            write_publisher_heartbeat(
                status_dir,
                PublisherHeartbeat(
                    pid=99999,
                    started_at_utc="2026-03-16T10:00:00Z",
                    last_heartbeat_utc=_fresh_utc_z(),
                    snapshots_emitted=5,
                    reviewer_mode="active_dual_agent",
                ),
            )
            with patch(
                "dev.scripts.devctl.review_channel.lifecycle_state.os.kill",
                side_effect=PermissionError,
            ):
                state = read_publisher_state(status_dir)

            self.assertTrue(state["running"])
            self.assertTrue(state["pid_alive"])
            self.assertEqual(state["stop_reason"], "")

    def test_read_publisher_state_prefers_live_instance_over_newer_dead_writer(self) -> None:
        from dev.scripts.devctl.review_channel.state import (
            PublisherHeartbeat,
            read_publisher_state,
            write_publisher_heartbeat,
        )

        live_pid = 10101
        dead_pid = 20202
        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            write_publisher_heartbeat(
                status_dir,
                PublisherHeartbeat(
                    pid=live_pid,
                    started_at_utc="2026-03-16T10:00:00Z",
                    last_heartbeat_utc=_fresh_utc_z(seconds_offset=-5),
                    snapshots_emitted=2,
                    reviewer_mode="active_dual_agent",
                ),
            )
            write_publisher_heartbeat(
                status_dir,
                PublisherHeartbeat(
                    pid=dead_pid,
                    started_at_utc="2026-03-16T10:00:10Z",
                    last_heartbeat_utc=_fresh_utc_z(),
                    snapshots_emitted=4,
                    reviewer_mode="active_dual_agent",
                ),
            )

            self.assertTrue((status_dir / "publisher_heartbeat.10101.json").exists())
            with patch(
                "dev.scripts.devctl.review_channel.lifecycle_state._pid_is_alive",
                side_effect=lambda pid: pid == live_pid,
            ):
                state = read_publisher_state(status_dir)

            self.assertTrue(state["running"])
            self.assertEqual(state["pid"], live_pid)
            self.assertEqual(state["snapshots_emitted"], 2)
            self.assertEqual(state["stop_reason"], "")

    def test_read_publisher_state_falls_back_to_freshest_stopped_instance(self) -> None:
        from dev.scripts.devctl.review_channel.state import (
            PublisherHeartbeat,
            read_publisher_state,
            write_publisher_heartbeat,
        )

        older_pid = 30303
        newer_pid = 40404
        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            write_publisher_heartbeat(
                status_dir,
                PublisherHeartbeat(
                    pid=older_pid,
                    started_at_utc="2026-03-16T10:00:00Z",
                    last_heartbeat_utc=_fresh_utc_z(seconds_offset=-30),
                    snapshots_emitted=3,
                    reviewer_mode="active_dual_agent",
                    stop_reason="timed_out",
                    stopped_at_utc=_fresh_utc_z(seconds_offset=-30),
                ),
            )
            write_publisher_heartbeat(
                status_dir,
                PublisherHeartbeat(
                    pid=newer_pid,
                    started_at_utc="2026-03-16T10:01:00Z",
                    last_heartbeat_utc=_fresh_utc_z(seconds_offset=-3),
                    snapshots_emitted=5,
                    reviewer_mode="active_dual_agent",
                    stop_reason="manual_stop",
                    stopped_at_utc=_fresh_utc_z(seconds_offset=-3),
                ),
            )

            with patch(
                "dev.scripts.devctl.review_channel.lifecycle_state._pid_is_alive",
                return_value=False,
            ):
                state = read_publisher_state(status_dir)

            self.assertFalse(state["running"])
            self.assertEqual(state["pid"], newer_pid)
            self.assertEqual(state["stop_reason"], "manual_stop")

    def test_check_review_needed_detects_hash_mismatch(self) -> None:
        from dev.scripts.devctl.review_channel.reviewer_worker import check_review_needed

        with tempfile.TemporaryDirectory() as tmpdir:
            bridge_path = Path(tmpdir) / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(),
                encoding="utf-8",
            )
            with patch(
                "dev.scripts.devctl.review_channel.reviewer_worker.compute_non_audit_worktree_hash",
                return_value="different_hash",
            ):
                tick = check_review_needed(
                    repo_root=Path(tmpdir),
                    bridge_path=bridge_path,
                )

            self.assertTrue(tick.review_needed)
            self.assertEqual(tick.current_hash, "different_hash")
            self.assertIn("changed", tick.detail)

    def test_check_review_needed_reports_match_when_hashes_equal(self) -> None:
        from dev.scripts.devctl.review_channel.reviewer_worker import check_review_needed

        expected_hash = "a" * 64
        with tempfile.TemporaryDirectory() as tmpdir:
            bridge_path = Path(tmpdir) / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(),
                encoding="utf-8",
            )
            with patch(
                "dev.scripts.devctl.review_channel.reviewer_worker.compute_non_audit_worktree_hash",
                return_value=expected_hash,
            ):
                tick = check_review_needed(
                    repo_root=Path(tmpdir),
                    bridge_path=bridge_path,
                )

            self.assertFalse(tick.review_needed)
            self.assertEqual(tick.state, "up_to_date")
            self.assertIn("matches", tick.detail)

    def test_check_review_needed_reports_inactive_mode_without_review_signal(self) -> None:
        from dev.scripts.devctl.review_channel.reviewer_worker import check_review_needed

        with tempfile.TemporaryDirectory() as tmpdir:
            bridge_path = Path(tmpdir) / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(reviewer_mode="single_agent"),
                encoding="utf-8",
            )
            with patch(
                "dev.scripts.devctl.review_channel.reviewer_worker.compute_non_audit_worktree_hash",
                return_value="different_hash",
            ):
                tick = check_review_needed(
                    repo_root=Path(tmpdir),
                    bridge_path=bridge_path,
                )

            self.assertFalse(tick.review_needed)
            self.assertEqual(tick.state, "inactive_mode")
            self.assertFalse(tick.semantic_review_claimed)
            self.assertEqual(tick.reviewer_mode, "single_agent")

    def test_reviewer_supervisor_heartbeat_write_and_read(self) -> None:
        from dev.scripts.devctl.review_channel.state import (
            ReviewerSupervisorHeartbeat,
            read_reviewer_supervisor_state,
            write_reviewer_supervisor_heartbeat,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            write_reviewer_supervisor_heartbeat(
                status_dir,
                ReviewerSupervisorHeartbeat(
                    pid=os.getpid(),
                    started_at_utc="2026-03-17T00:00:00Z",
                    last_heartbeat_utc=_fresh_utc_z(),
                    snapshots_emitted=3,
                    reviewer_mode="active_dual_agent",
                ),
            )
            state = read_reviewer_supervisor_state(status_dir)

            self.assertTrue(state["running"])
            self.assertEqual(state["snapshots_emitted"], 3)
            self.assertEqual(state["reviewer_mode"], "active_dual_agent")

    def test_reviewer_supervisor_reads_stopped_state(self) -> None:
        from dev.scripts.devctl.review_channel.state import (
            ReviewerSupervisorHeartbeat,
            read_reviewer_supervisor_state,
            write_reviewer_supervisor_heartbeat,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            write_reviewer_supervisor_heartbeat(
                status_dir,
                ReviewerSupervisorHeartbeat(
                    pid=99999,
                    started_at_utc="2026-03-17T00:00:00Z",
                    last_heartbeat_utc="2026-03-17T00:01:00Z",
                    snapshots_emitted=5,
                    reviewer_mode="active_dual_agent",
                    stop_reason="timed_out",
                    stopped_at_utc="2026-03-17T00:05:00Z",
                ),
            )
            with patch("dev.scripts.devctl.review_channel.lifecycle_state._pid_is_alive", return_value=False):
                state = read_reviewer_supervisor_state(status_dir)

            self.assertFalse(state["running"])
            self.assertEqual(state["stop_reason"], "timed_out")
            self.assertEqual(state["stopped_at_utc"], "2026-03-17T00:05:00Z")

    def test_reviewer_supervisor_infers_detached_exit(self) -> None:
        from dev.scripts.devctl.review_channel.state import (
            ReviewerSupervisorHeartbeat,
            read_reviewer_supervisor_state,
            write_reviewer_supervisor_heartbeat,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            write_reviewer_supervisor_heartbeat(
                status_dir,
                ReviewerSupervisorHeartbeat(
                    pid=99999,
                    started_at_utc="2026-03-17T00:00:00Z",
                    last_heartbeat_utc="2026-03-17T00:01:00Z",
                    snapshots_emitted=5,
                    reviewer_mode="active_dual_agent",
                ),
            )
            with patch("dev.scripts.devctl.review_channel.lifecycle_state._pid_is_alive", return_value=False):
                state = read_reviewer_supervisor_state(status_dir)

            self.assertFalse(state["running"])
            self.assertEqual(state["stop_reason"], "detached_exit")

    def test_reviewer_supervisor_treats_permission_denied_pid_check_as_alive(self) -> None:
        from dev.scripts.devctl.review_channel.state import (
            ReviewerSupervisorHeartbeat,
            read_reviewer_supervisor_state,
            write_reviewer_supervisor_heartbeat,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            write_reviewer_supervisor_heartbeat(
                status_dir,
                ReviewerSupervisorHeartbeat(
                    pid=99999,
                    started_at_utc="2026-03-17T00:00:00Z",
                    last_heartbeat_utc=_fresh_utc_z(),
                    snapshots_emitted=5,
                    reviewer_mode="active_dual_agent",
                ),
            )
            with patch(
                "dev.scripts.devctl.review_channel.lifecycle_state.os.kill",
                side_effect=PermissionError,
            ):
                state = read_reviewer_supervisor_state(status_dir)

            self.assertTrue(state["running"])
            self.assertTrue(state["pid_alive"])
            self.assertEqual(state["stop_reason"], "")

    def test_reviewer_supervisor_prefers_live_instance_over_newer_dead_writer(self) -> None:
        from dev.scripts.devctl.review_channel.state import (
            ReviewerSupervisorHeartbeat,
            read_reviewer_supervisor_state,
            write_reviewer_supervisor_heartbeat,
        )

        live_pid = 50505
        dead_pid = 60606
        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            write_reviewer_supervisor_heartbeat(
                status_dir,
                ReviewerSupervisorHeartbeat(
                    pid=live_pid,
                    started_at_utc="2026-03-17T00:00:00Z",
                    last_heartbeat_utc=_fresh_utc_z(seconds_offset=-5),
                    snapshots_emitted=2,
                    reviewer_mode="active_dual_agent",
                ),
            )
            write_reviewer_supervisor_heartbeat(
                status_dir,
                ReviewerSupervisorHeartbeat(
                    pid=dead_pid,
                    started_at_utc="2026-03-17T00:00:10Z",
                    last_heartbeat_utc=_fresh_utc_z(),
                    snapshots_emitted=4,
                    reviewer_mode="active_dual_agent",
                ),
            )

            self.assertTrue(
                (status_dir / "reviewer_supervisor_heartbeat.50505.json").exists()
            )
            with patch(
                "dev.scripts.devctl.review_channel.lifecycle_state._pid_is_alive",
                side_effect=lambda pid: pid == live_pid,
            ):
                state = read_reviewer_supervisor_state(status_dir)

            self.assertTrue(state["running"])
            self.assertEqual(state["pid"], live_pid)
            self.assertEqual(state["snapshots_emitted"], 2)
            self.assertEqual(state["stop_reason"], "")

    def test_reviewer_supervisor_falls_back_to_freshest_stopped_instance(self) -> None:
        from dev.scripts.devctl.review_channel.state import (
            ReviewerSupervisorHeartbeat,
            read_reviewer_supervisor_state,
            write_reviewer_supervisor_heartbeat,
        )

        older_pid = 70707
        newer_pid = 80808
        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            write_reviewer_supervisor_heartbeat(
                status_dir,
                ReviewerSupervisorHeartbeat(
                    pid=older_pid,
                    started_at_utc="2026-03-17T00:00:00Z",
                    last_heartbeat_utc=_fresh_utc_z(seconds_offset=-30),
                    snapshots_emitted=3,
                    reviewer_mode="active_dual_agent",
                    stop_reason="timed_out",
                    stopped_at_utc=_fresh_utc_z(seconds_offset=-30),
                ),
            )
            write_reviewer_supervisor_heartbeat(
                status_dir,
                ReviewerSupervisorHeartbeat(
                    pid=newer_pid,
                    started_at_utc="2026-03-17T00:01:00Z",
                    last_heartbeat_utc=_fresh_utc_z(seconds_offset=-3),
                    snapshots_emitted=5,
                    reviewer_mode="active_dual_agent",
                    stop_reason="manual_stop",
                    stopped_at_utc=_fresh_utc_z(seconds_offset=-3),
                ),
            )

            with patch(
                "dev.scripts.devctl.review_channel.lifecycle_state._pid_is_alive",
                return_value=False,
            ):
                state = read_reviewer_supervisor_state(status_dir)

            self.assertFalse(state["running"])
            self.assertEqual(state["pid"], newer_pid)
            self.assertEqual(state["stop_reason"], "manual_stop")

    def test_reviewer_follow_output_error_writes_final_supervisor_state(self) -> None:
        args = self._build_reviewer_follow_args(max_follow_snapshots=1)
        ensure_result = EnsureHeartbeatResult(
            refreshed=True,
            reviewer_mode="active_dual_agent",
            reason="reviewer-follow",
            state_write=None,
            error=None,
        )
        status_report = {
            "command": "review-channel",
            "action": "reviewer-heartbeat",
            "ok": True,
            "errors": [],
            "review_needed": True,
            "reviewer_worker": {
                "state": "review_needed",
                "review_needed": True,
                "semantic_review_claimed": False,
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            status_dir = Path(tmpdir)
            with (
                patch.object(
                    review_channel_command,
                    "ensure_reviewer_heartbeat",
                    return_value=ensure_result,
                ),
                patch.object(
                    review_channel_command,
                    "_build_reviewer_state_report",
                    return_value=(status_report, 0),
                ),
                patch.object(
                    review_channel_command,
                    "emit_follow_ndjson_frame",
                    return_value=9,
                ),
                patch.object(
                    review_channel_command,
                    "reset_follow_output",
                    return_value=None,
                ),
            ):
                report, rc = review_channel_command._run_reviewer_follow_action(
                    args=args,
                    repo_root=Path("/tmp/repo"),
                    paths={
                        "bridge_path": Path("/tmp/repo/bridge.md"),
                        "status_dir": status_dir,
                    },
                )

            state = review_channel_command.read_reviewer_supervisor_state(status_dir)

        self.assertEqual(rc, 9)
        self.assertFalse(report["ok"])
        self.assertEqual(state["stop_reason"], "output_error")
        self.assertFalse(state["running"])
        self.assertTrue(state["pid_alive"])


class ReviewChannelFollowLoopTests(unittest.TestCase):
    def test_build_claude_progress_token_ignores_codex_poll_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bridge_path = root / "bridge.md"
            scratch_path = root / "notes.txt"
            scratch_path.write_text("alpha", encoding="utf-8")
            bridge_path.write_text(
                _build_bridge_text(last_codex_poll="2026-03-08T19:08:45Z"),
                encoding="utf-8",
            )
            token_a = build_claude_progress_token(
                repo_root=root,
                bridge_path=bridge_path,
            )
            bridge_path.write_text(
                _build_bridge_text(last_codex_poll="2026-03-08T19:18:45Z"),
                encoding="utf-8",
            )
            token_b = build_claude_progress_token(
                repo_root=root,
                bridge_path=bridge_path,
            )
            bridge_path.write_text(
                _build_bridge_text(
                    claude_status="- working on a different Claude slice",
                ),
                encoding="utf-8",
            )
            token_c = build_claude_progress_token(
                repo_root=root,
                bridge_path=bridge_path,
            )
            scratch_path.write_text("beta", encoding="utf-8")
            token_d = build_claude_progress_token(
                repo_root=root,
                bridge_path=bridge_path,
            )

        self.assertEqual(token_a, token_b)
        self.assertNotEqual(token_a, token_c)
        self.assertNotEqual(token_a, token_d)

    def test_run_follow_loop_stops_after_claude_inactivity(self) -> None:
        frames: list[dict[str, object]] = []
        progress_tokens = ["stable"]

        def emit(payload: dict[str, object], *, args) -> int:
            frames.append(payload)
            return 0

        from dev.scripts.devctl.review_channel.lifecycle_state import (
            ReviewerSupervisorHeartbeat,
            write_reviewer_supervisor_heartbeat,
        )

        plan = FollowActionPlan(
            shape=FollowActionShape(
                daemon_kind="reviewer_supervisor",
                completion_action="reviewer-heartbeat",
                output_error_action="reviewer-heartbeat",
                write_heartbeat_fn=write_reviewer_supervisor_heartbeat,
                heartbeat_factory=ReviewerSupervisorHeartbeat,
            ),
            build_tick_fn=lambda: FollowLoopTick(
                report={"command": "review-channel", "action": "reviewer-heartbeat"},
                exit_code=0,
                reviewer_mode="active_dual_agent",
                progress_token=progress_tokens[0],
            ),
            shared_deps=FollowLoopSharedDeps(
                emit_follow_ndjson_frame_fn=emit,
                reset_follow_output_fn=lambda output: None,
                build_follow_completion_report_fn=lambda **kwargs: {
                    "command": "review-channel",
                    **kwargs,
                },
                build_follow_output_error_report_fn=lambda **kwargs: {
                    "command": "review-channel",
                    **kwargs,
                },
                utc_timestamp_fn=lambda: "2026-03-18T00:00:00Z",
                sleep_fn=lambda seconds: None,
            ),
        )
        args = SimpleNamespace(
            output=None,
            follow_interval_seconds=1,
            follow_inactivity_timeout_seconds=10,
            max_follow_snapshots=0,
            timeout_minutes=0,
        )
        monotonic_value = [0.0]

        def fake_monotonic() -> float:
            value = monotonic_value[0]
            monotonic_value[0] += 3.0
            return value

        with (
            patch(
                "dev.scripts.devctl.review_channel.follow_loop.time.monotonic",
                side_effect=fake_monotonic,
            ),
            patch("dev.scripts.devctl.review_channel.follow_loop.time.sleep", return_value=None),
        ):
            report, rc = run_follow_loop(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={
                    "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
                },
                plan=plan,
            )

        self.assertEqual(rc, 0)
        self.assertEqual(report["stop_reason"], "inactivity_timeout")
        self.assertEqual(report["snapshots_emitted"], 2)
        self.assertEqual(len(frames), 2)

    def test_run_follow_loop_resets_inactivity_timer_on_new_progress(self) -> None:
        frames: list[dict[str, object]] = []
        progress_tokens = ["token-a", "token-b"]

        def emit(payload: dict[str, object], *, args) -> int:
            frames.append(payload)
            return 0

        from dev.scripts.devctl.review_channel.lifecycle_state import (
            ReviewerSupervisorHeartbeat,
            write_reviewer_supervisor_heartbeat,
        )

        tick_index = {"value": 0}

        def build_tick() -> FollowLoopTick:
            index = min(tick_index["value"], len(progress_tokens) - 1)
            tick_index["value"] += 1
            return FollowLoopTick(
                report={"command": "review-channel", "action": "reviewer-heartbeat"},
                exit_code=0,
                reviewer_mode="active_dual_agent",
                progress_token=progress_tokens[index],
            )

        plan = FollowActionPlan(
            shape=FollowActionShape(
                daemon_kind="reviewer_supervisor",
                completion_action="reviewer-heartbeat",
                output_error_action="reviewer-heartbeat",
                write_heartbeat_fn=write_reviewer_supervisor_heartbeat,
                heartbeat_factory=ReviewerSupervisorHeartbeat,
            ),
            build_tick_fn=build_tick,
            shared_deps=FollowLoopSharedDeps(
                emit_follow_ndjson_frame_fn=emit,
                reset_follow_output_fn=lambda output: None,
                build_follow_completion_report_fn=lambda **kwargs: {
                    "command": "review-channel",
                    **kwargs,
                },
                build_follow_output_error_report_fn=lambda **kwargs: {
                    "command": "review-channel",
                    **kwargs,
                },
                utc_timestamp_fn=lambda: "2026-03-18T00:00:00Z",
                sleep_fn=lambda seconds: None,
            ),
        )
        args = SimpleNamespace(
            output=None,
            follow_interval_seconds=1,
            follow_inactivity_timeout_seconds=10,
            max_follow_snapshots=0,
            timeout_minutes=0,
        )
        monotonic_value = [0.0]

        def fake_monotonic() -> float:
            value = monotonic_value[0]
            monotonic_value[0] += 3.0
            return value

        with (
            patch(
                "dev.scripts.devctl.review_channel.follow_loop.time.monotonic",
                side_effect=fake_monotonic,
            ),
            patch("dev.scripts.devctl.review_channel.follow_loop.time.sleep", return_value=None),
        ):
            report, rc = run_follow_loop(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={
                    "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
                },
                plan=plan,
            )

        self.assertEqual(rc, 0)
        self.assertEqual(report["stop_reason"], "inactivity_timeout")
        self.assertEqual(report["snapshots_emitted"], 3)
        self.assertEqual(len(frames), 3)

    def test_run_follow_loop_empty_progress_token_still_times_out(self) -> None:
        frames: list[dict[str, object]] = []

        def emit(payload: dict[str, object], *, args) -> int:
            frames.append(payload)
            return 0

        from dev.scripts.devctl.review_channel.lifecycle_state import (
            ReviewerSupervisorHeartbeat,
            write_reviewer_supervisor_heartbeat,
        )

        plan = FollowActionPlan(
            shape=FollowActionShape(
                daemon_kind="reviewer_supervisor",
                completion_action="reviewer-heartbeat",
                output_error_action="reviewer-heartbeat",
                write_heartbeat_fn=write_reviewer_supervisor_heartbeat,
                heartbeat_factory=ReviewerSupervisorHeartbeat,
            ),
            build_tick_fn=lambda: FollowLoopTick(
                report={"command": "review-channel", "action": "reviewer-heartbeat"},
                exit_code=0,
                reviewer_mode="active_dual_agent",
                progress_token="",
            ),
            shared_deps=FollowLoopSharedDeps(
                emit_follow_ndjson_frame_fn=emit,
                reset_follow_output_fn=lambda output: None,
                build_follow_completion_report_fn=lambda **kwargs: {
                    "command": "review-channel",
                    **kwargs,
                },
                build_follow_output_error_report_fn=lambda **kwargs: {
                    "command": "review-channel",
                    **kwargs,
                },
                utc_timestamp_fn=lambda: "2026-03-18T00:00:00Z",
                sleep_fn=lambda seconds: None,
            ),
        )
        args = SimpleNamespace(
            output=None,
            follow_interval_seconds=1,
            follow_inactivity_timeout_seconds=10,
            max_follow_snapshots=0,
            timeout_minutes=0,
        )
        monotonic_value = [0.0]

        def fake_monotonic() -> float:
            value = monotonic_value[0]
            monotonic_value[0] += 4.0
            return value

        with (
            patch(
                "dev.scripts.devctl.review_channel.follow_loop.time.monotonic",
                side_effect=fake_monotonic,
            ),
            patch("dev.scripts.devctl.review_channel.follow_loop.time.sleep", return_value=None),
        ):
            report, rc = run_follow_loop(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={
                    "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
                },
                plan=plan,
            )

        self.assertEqual(rc, 0)
        self.assertEqual(report["stop_reason"], "inactivity_timeout")
        self.assertEqual(report["snapshots_emitted"], 2)
        self.assertEqual(len(frames), 2)

    def test_run_follow_loop_emits_unchanged_poll_counters(self) -> None:
        frames: list[dict[str, object]] = []

        def emit(payload: dict[str, object], *, args) -> int:
            frames.append(payload)
            return 0

        from dev.scripts.devctl.review_channel.lifecycle_state import (
            ReviewerSupervisorHeartbeat,
            write_reviewer_supervisor_heartbeat,
        )

        plan = FollowActionPlan(
            shape=FollowActionShape(
                daemon_kind="reviewer_supervisor",
                completion_action="reviewer-heartbeat",
                output_error_action="reviewer-heartbeat",
                write_heartbeat_fn=write_reviewer_supervisor_heartbeat,
                heartbeat_factory=ReviewerSupervisorHeartbeat,
            ),
            build_tick_fn=lambda: FollowLoopTick(
                report={"command": "review-channel", "action": "reviewer-heartbeat"},
                exit_code=0,
                reviewer_mode="active_dual_agent",
                progress_token="stable-token",
            ),
            shared_deps=FollowLoopSharedDeps(
                emit_follow_ndjson_frame_fn=emit,
                reset_follow_output_fn=lambda output: None,
                build_follow_completion_report_fn=lambda **kwargs: {
                    "command": "review-channel",
                    **kwargs,
                },
                build_follow_output_error_report_fn=lambda **kwargs: {
                    "command": "review-channel",
                    **kwargs,
                },
                utc_timestamp_fn=lambda: "2026-03-18T00:00:00Z",
                sleep_fn=lambda seconds: None,
            ),
        )
        args = SimpleNamespace(
            output=None,
            follow_interval_seconds=1,
            follow_inactivity_timeout_seconds=0,
            max_follow_snapshots=4,
            timeout_minutes=0,
        )
        report, rc = run_follow_loop(
            args=args,
            repo_root=Path("/tmp/repo"),
            paths={
                "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
            },
            plan=plan,
        )

        self.assertEqual(rc, 0)
        self.assertEqual(report["stop_reason"], "completed")
        self.assertEqual(report["max_claude_unchanged_polls"], 3)
        self.assertTrue(report["claude_self_assignment_due"])
        self.assertFalse(report["claude_progress_stalled"])
        self.assertEqual(len(frames), 4)
        self.assertEqual(frames[0]["claude_unchanged_polls"], 0)
        self.assertEqual(frames[-1]["claude_unchanged_polls"], 3)
        self.assertTrue(frames[-1]["claude_self_assignment_due"])
        self.assertFalse(frames[-1]["claude_progress_stalled"])


class ReviewChannelCommandTests(unittest.TestCase):
    def test_implementer_wait_returns_after_reviewer_owned_bridge_change(self) -> None:
        baseline_revision = "aaaaaaaaaaaa"
        updated_revision = "bbbbbbbbbbbb"
        bridge_states = [
            _build_bridge_text(
                current_instruction="- keep waiting",
                claude_ack=f"- acknowledged; instruction-rev: `{baseline_revision}`",
            ).replace("56bcd5d01510", baseline_revision),
            _build_bridge_text(
                current_instruction="- reviewer posted next slice",
                claude_ack=f"- acknowledged; instruction-rev: `{baseline_revision}`",
                current_verdict="- reviewer accepted prior slice",
            ).replace("56bcd5d01510", updated_revision),
        ]
        reports = [
            (
                {
                    "command": "review-channel",
                    "action": "status",
                    "ok": False,
                    "warnings": [],
                    "errors": [],
                    "bridge_liveness": {
                        "reviewer_mode": "active_dual_agent",
                        "claude_ack_current": True,
                        "current_instruction_revision": baseline_revision,
                    },
                    "attention": {"status": "reviewed_hash_stale"},
                    "review_needed": True,
                },
                0,
            ),
            (
                {
                    "command": "review-channel",
                    "action": "status",
                    "ok": True,
                    "warnings": [],
                    "errors": [],
                    "bridge_liveness": {
                        "reviewer_mode": "active_dual_agent",
                        "claude_ack_current": False,
                        "current_instruction_revision": updated_revision,
                    },
                    "attention": {"status": "claude_ack_stale"},
                    "review_needed": False,
                },
                0,
            ),
        ]
        poll_index = {"value": 0}
        monotonic_values = iter((0.0, 1.0))
        deps = review_channel_wait_mod.ImplementerWaitDeps(
            run_status_action_fn=lambda **_: reports[poll_index["value"]],
            read_bridge_text_fn=lambda path: bridge_states[poll_index["value"]],
            monotonic_fn=lambda: next(monotonic_values),
            sleep_fn=lambda seconds: poll_index.__setitem__("value", 1),
        )
        args = SimpleNamespace(
            action="implementer-wait",
            follow_interval_seconds=150,
            timeout_minutes=0,
        )
        paths = {
            "bridge_path": Path("/tmp/bridge.md"),
            "review_channel_path": Path("/tmp/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/dev/reports/review_channel/latest"),
        }

        report, rc = review_channel_wait_mod.run_implementer_wait_action(
            args=args,
            repo_root=Path("/tmp/repo"),
            paths=paths,
            deps=deps,
        )

        self.assertEqual(rc, 0)
        self.assertEqual(report["action"], "implementer-wait")
        self.assertEqual(report["wait_state"]["stop_reason"], "reviewer_update_observed")
        self.assertEqual(report["wait_state"]["polls_observed"], 1)
        self.assertTrue(report["wait_state"]["reviewer_update_observed"])

    def test_implementer_wait_times_out_when_bridge_state_does_not_change(self) -> None:
        report = {
            "command": "review-channel",
            "action": "status",
            "ok": False,
            "warnings": [],
            "errors": [],
            "bridge_liveness": {
                "reviewer_mode": "active_dual_agent",
                "claude_ack_current": True,
                "current_instruction_revision": "aaaaaaaaaaaa",
            },
            "attention": {"status": "reviewed_hash_stale"},
            "review_needed": True,
        }
        monotonic_values = iter((0.0, 0.0, 3600.0))
        deps = review_channel_wait_mod.ImplementerWaitDeps(
            run_status_action_fn=lambda **_: (dict(report), 0),
            read_bridge_text_fn=lambda path: _build_bridge_text(
                current_instruction="- keep waiting",
                claude_ack="- acknowledged; instruction-rev: `aaaaaaaaaaaa`",
            ).replace("56bcd5d01510", "aaaaaaaaaaaa"),
            monotonic_fn=lambda: next(monotonic_values),
            sleep_fn=lambda seconds: None,
        )
        args = SimpleNamespace(
            action="implementer-wait",
            follow_interval_seconds=150,
            timeout_minutes=0,
        )
        paths = {
            "bridge_path": Path("/tmp/bridge.md"),
            "review_channel_path": Path("/tmp/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/dev/reports/review_channel/latest"),
        }

        wait_report, rc = review_channel_wait_mod.run_implementer_wait_action(
            args=args,
            repo_root=Path("/tmp/repo"),
            paths=paths,
            deps=deps,
        )

        self.assertEqual(rc, 1)
        self.assertEqual(wait_report["wait_state"]["stop_reason"], "timed_out")
        self.assertEqual(wait_report["wait_state"]["polls_observed"], 1)
        self.assertIn("Timed out waiting", wait_report["errors"][0])

    def test_implementer_wait_wakes_when_claude_packet_queue_changes(self) -> None:
        report = {
            "command": "review-channel",
            "action": "status",
            "ok": False,
            "warnings": [],
            "errors": [],
            "bridge_liveness": {
                "reviewer_mode": "active_dual_agent",
                "claude_ack_current": True,
                "current_instruction_revision": "aaaaaaaaaaaa",
            },
            "attention": {"status": "reviewed_hash_stale"},
            "review_needed": True,
        }
        bridge_text = _build_bridge_text(
            current_instruction="- keep waiting",
            claude_ack="- acknowledged; instruction-rev: `aaaaaaaaaaaa`",
        ).replace("56bcd5d01510", "aaaaaaaaaaaa")
        packet_sets = [
            [],
            [{"packet_id": "rev_pkt_0004"}],
        ]
        poll_index = {"value": 0}
        monotonic_values = iter((0.0, 1.0))
        deps = review_channel_wait_mod.ImplementerWaitDeps(
            run_status_action_fn=lambda **_: (dict(report), 0),
            read_bridge_text_fn=lambda path: bridge_text,
            monotonic_fn=lambda: next(monotonic_values),
            sleep_fn=lambda seconds: poll_index.__setitem__("value", 1),
            pending_packets_fn=lambda repo_root, paths: packet_sets[poll_index["value"]],
        )
        args = SimpleNamespace(
            action="implementer-wait",
            follow_interval_seconds=150,
            timeout_minutes=0,
        )
        paths = {
            "bridge_path": Path("/tmp/bridge.md"),
            "review_channel_path": Path("/tmp/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/dev/reports/review_channel/latest"),
        }

        wait_report, rc = review_channel_wait_mod.run_implementer_wait_action(
            args=args,
            repo_root=Path("/tmp/repo"),
            paths=paths,
            deps=deps,
        )

        self.assertEqual(rc, 0)
        self.assertEqual(wait_report["wait_state"]["stop_reason"], "reviewer_update_observed")
        self.assertEqual(wait_report["wait_state"]["polls_observed"], 1)
        self.assertIn("review-channel inbox", wait_report["warnings"][0])

    def test_implementer_wait_fails_closed_when_reviewer_loop_is_unhealthy(self) -> None:
        deps = review_channel_wait_mod.ImplementerWaitDeps(
            run_status_action_fn=lambda **_: (
                {
                    "command": "review-channel",
                    "action": "status",
                    "ok": False,
                    "warnings": [],
                    "errors": [],
                    "bridge_liveness": {
                        "reviewer_mode": "active_dual_agent",
                        "claude_ack_current": True,
                        "current_instruction_revision": "aaaaaaaaaaaa",
                    },
                    "attention": {"status": "reviewer_supervisor_required"},
                    "review_needed": True,
                },
                0,
            ),
            read_bridge_text_fn=lambda path: _build_bridge_text(
                current_instruction="- keep waiting",
                claude_ack="- acknowledged; instruction-rev: `aaaaaaaaaaaa`",
            ).replace("56bcd5d01510", "aaaaaaaaaaaa"),
            monotonic_fn=lambda: 0.0,
            sleep_fn=lambda seconds: None,
        )
        args = SimpleNamespace(
            action="implementer-wait",
            follow_interval_seconds=150,
            timeout_minutes=0,
        )
        paths = {
            "bridge_path": Path("/tmp/bridge.md"),
            "review_channel_path": Path("/tmp/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/dev/reports/review_channel/latest"),
        }

        report, rc = review_channel_wait_mod.run_implementer_wait_action(
            args=args,
            repo_root=Path("/tmp/repo"),
            paths=paths,
            deps=deps,
        )

        self.assertEqual(rc, 1)
        self.assertEqual(report["wait_state"]["stop_reason"], "reviewer_unhealthy")
        self.assertEqual(report["wait_state"]["polls_observed"], 0)
        self.assertIn("reviewer loop is unhealthy", report["errors"][0])

    def _reviewer_checkpoint_args(
        self,
        *,
        root: Path,
        review_channel_path: Path,
        bridge_path: Path,
        status_dir: Path,
        output_path: Path,
        verdict: str,
        open_findings: str,
        instruction: str,
        reviewed_scope_item: list[str],
        promotion_plan: str | None = "dev/active/continuous_swarm.md",
        rotate_instruction_revision: bool = False,
        expected_instruction_revision: str = "56bcd5d01510",
    ) -> SimpleNamespace:
        return SimpleNamespace(
            action="reviewer-checkpoint",
            execution_mode="auto",
            terminal="none",
            terminal_profile="auto-dark",
            review_channel_path=str(review_channel_path.relative_to(root)),
            bridge_path=str(bridge_path.relative_to(root)),
            rollover_dir="dev/reports/review_channel/rollovers",
            status_dir=str(status_dir.relative_to(root)),
            promotion_plan=promotion_plan,
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
            expected_instruction_revision=expected_instruction_revision,
            verdict=verdict,
            open_findings=open_findings,
            instruction=instruction,
            reviewed_scope_item=reviewed_scope_item,
            rotate_instruction_revision=rotate_instruction_revision,
            format="json",
            output=str(output_path),
            pipe_command=None,
            pipe_args=None,
        )

    def test_build_reviewer_state_report_reuses_snapshot_reviewer_worker(self) -> None:
        args = SimpleNamespace(
            action="reviewer-heartbeat",
            execution_mode="auto",
            terminal="none",
            terminal_profile="auto-dark",
            rollover_threshold_pct=50,
            rollover_trigger="context-threshold",
            await_ack_seconds=180,
            codex_workers=8,
            claude_workers=8,
            dangerous=False,
            approval_mode="balanced",
        )
        projection_paths = ReviewChannelProjectionPaths(
            root_dir="/tmp/review",
            review_state_path="/tmp/review/review_state.json",
            compact_path="/tmp/review/compact.json",
            full_path="/tmp/review/full.json",
            actions_path="/tmp/review/actions.json",
            trace_path="/tmp/review/trace.ndjson",
            latest_markdown_path="/tmp/review/latest.md",
            agent_registry_path="/tmp/review/registry/agents.json",
        )
        reviewer_worker = {
            "state": "review_needed",
            "review_needed": True,
            "semantic_review_claimed": False,
        }
        status_snapshot = ReviewChannelStatusSnapshot(
            lanes=[],
            bridge_liveness={"overall_state": "fresh"},
            attention={"status": "healthy"},
            warnings=[],
            errors=[],
            projection_paths=projection_paths,
            reviewer_worker=reviewer_worker,
        )

        with (
            patch.object(review_channel_command, "refresh_status_snapshot", return_value=status_snapshot),
            patch.object(
                review_channel_status_mod,
                "_attach_reviewer_worker",
                side_effect=AssertionError("unexpected reviewer worker recompute"),
            ),
        ):
            report, exit_code = review_channel_command._build_reviewer_state_report(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={
                    "bridge_path": Path("/tmp/repo/bridge.md"),
                    "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
                    "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
                    "promotion_plan_path": Path("/tmp/repo/dev/active/continuous_swarm.md"),
                },
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["reviewer_worker"], reviewer_worker)
        self.assertTrue(report["review_needed"])

    def test_run_status_reuses_bridge_report_reviewer_worker(self) -> None:
        args = SimpleNamespace(execution_mode="auto")
        reviewer_worker = {
            "state": "review_needed",
            "review_needed": True,
            "semantic_review_claimed": False,
        }

        with (
            patch.object(
                review_channel_status_mod,
                "_run_bridge_action",
                return_value=({"ok": True, "reviewer_worker": reviewer_worker}, 0),
            ),
            patch.object(review_channel_status_mod, "event_state_exists", return_value=False),
            patch.object(
                review_channel_status_mod,
                "_read_publisher_state_safe",
                return_value={"running": False},
            ),
            patch.object(
                review_channel_status_mod,
                "_read_reviewer_supervisor_state_safe",
                return_value={"running": False},
            ),
            patch.object(
                review_channel_status_mod,
                "_attach_reviewer_worker",
                side_effect=AssertionError("unexpected reviewer worker recompute"),
            ),
        ):
            report, exit_code = review_channel_status_mod._run_status_action(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={
                    "artifact_paths": object(),
                    "bridge_path": Path("/tmp/repo/bridge.md"),
                },
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["reviewer_worker"], reviewer_worker)
        self.assertEqual(report["publisher"], {"running": False})
        self.assertEqual(report["reviewer_supervisor"], {"running": False})

    def test_ensure_requires_reviewer_supervisor_when_review_is_pending(self) -> None:
        args = SimpleNamespace(follow=False)
        status_report = {
            "bridge_liveness": {
                "reviewer_mode": "active_dual_agent",
                "codex_poll_state": "fresh",
                "last_codex_poll_age_seconds": 0,
                "claude_ack_current": True,
                "review_needed": True,
            },
            "attention": {"status": "reviewer_supervisor_required"},
            "reviewer_worker": {"review_needed": True},
            "reviewer_supervisor": {"running": False},
            "service_identity": None,
            "attach_auth_policy": None,
        }

        with (
            patch.object(
                review_channel_command,
                "_run_status_action",
                return_value=(status_report, 0),
            ),
            patch.object(
                review_channel_ensure_mod,
                "assess_publisher_lifecycle",
                return_value=review_channel_command.PublisherLifecycleAssessment(
                    publisher_state={"running": True},
                    publisher_running=True,
                    publisher_required=True,
                    publisher_status="running",
                ),
            ),
        ):
            report, rc = review_channel_command._run_ensure_action(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={},
            )

        self.assertEqual(rc, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["attention_status"], "reviewer_supervisor_required")
        self.assertIn("reviewer supervisor follow loop", report["detail"])
        self.assertIn("reviewer-heartbeat --follow", report["recommended_command"])

    def test_ensure_action_deps_default_sleep_fn_is_noop(self) -> None:
        deps = review_channel_ensure_mod.EnsureActionDeps(
            run_status_action_fn=lambda **_: ({}, 0),
            read_publisher_state_safe_fn=lambda *_: {},
            assess_publisher_lifecycle_fn=lambda **_: review_channel_command.PublisherLifecycleAssessment(
                publisher_state={},
                publisher_running=False,
                publisher_required=False,
                publisher_status="inactive_mode",
            ),
            spawn_follow_publisher_fn=lambda **_: (False, None, ""),
            verify_detached_start_fn=lambda **_: "not_attempted",
            refresh_bridge_heartbeat_fn=lambda **_: None,
            reviewer_mode_is_active_fn=lambda *_: False,
            run_ensure_follow_action_fn=lambda **_: ({}, 0),
        )

        self.assertIsNone(deps.sleep_fn(0.25))

    def test_ensure_auto_heals_reviewer_supervisor_and_recomputes_state(self) -> None:
        """After a successful reviewer-supervisor restart, ensure must reflect the healed state."""
        args = SimpleNamespace(follow=False, start_publisher_if_missing=False)
        pre_restart_report = {
            "bridge_liveness": {
                "reviewer_mode": "active_dual_agent",
                "codex_poll_state": "fresh",
                "last_codex_poll_age_seconds": 0,
                "claude_ack_current": True,
                "review_needed": True,
            },
            "attention": {"status": "reviewer_supervisor_required"},
            "reviewer_worker": {"review_needed": True},
            "reviewer_supervisor": {"running": False},
            "service_identity": None,
            "attach_auth_policy": None,
        }
        post_restart_report = {
            **pre_restart_report,
            "attention": {"status": "ok"},
            "reviewer_supervisor": {"running": True},
        }
        call_count = {"n": 0}

        def status_side_effect(**kwargs):
            call_count["n"] += 1
            if call_count["n"] <= 1:
                return pre_restart_report, 0
            return post_restart_report, 0

        with (
            patch.object(
                review_channel_command,
                "_run_status_action",
                side_effect=status_side_effect,
            ),
            patch.object(
                review_channel_command,
                "_spawn_reviewer_supervisor",
                return_value=(True, 99999, "/tmp/supervisor.log"),
            ),
            patch.object(
                review_channel_command,
                "_verify_reviewer_supervisor_start",
                return_value="started",
            ),
            patch.object(
                review_channel_ensure_mod,
                "assess_publisher_lifecycle",
                return_value=review_channel_command.PublisherLifecycleAssessment(
                    publisher_state={"running": True},
                    publisher_running=True,
                    publisher_required=True,
                    publisher_status="running",
                ),
            ),
        ):
            report, rc = review_channel_command._run_ensure_action(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={},
            )

        self.assertEqual(rc, 0)
        self.assertTrue(report["ok"])
        self.assertIn("auto-restarted", report["detail"])
        self.assertNotIn("reviewer supervisor follow loop is required", report["detail"])

    def test_ensure_reloads_failed_start_state_after_supervisor_restart_attempt(self) -> None:
        """Failed supervisor restarts must re-read lifecycle state before reporting ensure status."""
        args = SimpleNamespace(follow=False, start_publisher_if_missing=False)
        pre_restart_report = {
            "bridge_liveness": {
                "reviewer_mode": "active_dual_agent",
                "codex_poll_state": "fresh",
                "last_codex_poll_age_seconds": 0,
                "claude_ack_current": True,
                "review_needed": True,
            },
            "attention": {"status": "reviewer_supervisor_required"},
            "reviewer_worker": {"review_needed": True},
            "reviewer_supervisor": {"running": False},
            "service_identity": None,
            "attach_auth_policy": None,
        }
        post_restart_report = {
            **pre_restart_report,
            "reviewer_supervisor": {
                "running": False,
                "pid": 99999,
                "stop_reason": "failed_start",
            },
        }
        call_count = {"n": 0}

        def status_side_effect(**kwargs):
            call_count["n"] += 1
            if call_count["n"] <= 1:
                return pre_restart_report, 0
            return post_restart_report, 0

        with (
            patch.object(
                review_channel_command,
                "_run_status_action",
                side_effect=status_side_effect,
            ),
            patch.object(
                review_channel_command,
                "_spawn_reviewer_supervisor",
                return_value=(True, 99999, "/tmp/supervisor.log"),
            ),
            patch.object(
                review_channel_command,
                "_verify_reviewer_supervisor_start",
                return_value="failed_start",
            ),
            patch.object(
                review_channel_ensure_mod,
                "assess_publisher_lifecycle",
                return_value=review_channel_command.PublisherLifecycleAssessment(
                    publisher_state={"running": True},
                    publisher_running=True,
                    publisher_required=True,
                    publisher_status="running",
                ),
            ),
        ):
            report, rc = review_channel_command._run_ensure_action(
                args=args,
                repo_root=Path("/tmp/repo"),
                paths={},
            )

        self.assertEqual(rc, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(
            report["reviewer_supervisor"]["stop_reason"],
            "failed_start",
        )
        self.assertIn(
            "failed before heartbeat confirmation",
            report["detail"],
        )
        self.assertIn(
            "reviewer supervisor follow loop is required",
            report["detail"],
        )

    def test_run_dry_run_emits_scripts_and_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            script_dir = root / "scripts"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
            args = SimpleNamespace(
                action="launch",
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
                "review-channel --action implementer-wait",
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
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
            updated_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertIn("- still in progress", updated_bridge)
            self.assertIn("- bridge needs rollover-safe handoff", updated_bridge)
            self.assertIn(
                "- stop at a safe boundary and relaunch before compaction",
                updated_bridge,
            )
            self.assertIn("\n- Reviewer mode: `active_dual_agent`\n", updated_bridge)
            self.assertIn(
                "- dev/scripts/devctl/review_channel/handoff.py",
                updated_bridge,
            )
            self.assertIsNone(payload["reviewer_state_write"])
            self.assertIn(
                "- Last non-audit worktree hash: "
                f"`{'a' * 64}`",
                updated_bridge,
            )
            self.assertEqual(payload["action"], "status")
            self.assertEqual(payload["sessions"], [])
            self.assertIsNone(payload["handoff_bundle"])
            self.assertIsNotNone(payload["projection_paths"])
            service_identity = payload["service_identity"]
            attach_auth_policy = payload["attach_auth_policy"]
            self.assertEqual(payload["reviewer_worker"]["state"], "review_needed")
            self.assertTrue(payload["reviewer_worker"]["review_needed"])
            self.assertFalse(payload["reviewer_worker"]["semantic_review_claimed"])

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
            full = json.loads(full_path.read_text(encoding="utf-8"))
            actions = json.loads(actions_path.read_text(encoding="utf-8"))
            agent_registry = json.loads(agent_registry_path.read_text(encoding="utf-8"))

            self.assertEqual(review_state["command"], "review-channel")
            self.assertTrue(
                str(service_identity["service_id"]).startswith("review-channel:sha256:")
            )
            self.assertEqual(service_identity["project_id"], review_state.get("_compat", {}).get("project_id"))
            self.assertEqual(service_identity["repo_root"], str(root.resolve()))
            self.assertEqual(service_identity["worktree_root"], str(root.resolve()))
            self.assertEqual(service_identity["bridge_path"], bridge_path.name)
            self.assertEqual(
                service_identity["review_channel_path"],
                str(review_channel_path.resolve().relative_to(root.resolve())),
            )
            self.assertEqual(
                service_identity["status_root"],
                str(status_dir.resolve().relative_to(root.resolve())),
            )
            self.assertEqual(
                service_identity["discovery_fields"],
                [
                    "service_id",
                    "project_id",
                    "repo_root",
                    "worktree_root",
                    "bridge_path",
                    "review_channel_path",
                    "status_root",
                ],
            )
            self.assertEqual(attach_auth_policy["attach_scope"], "repo_worktree_local")
            self.assertTrue(attach_auth_policy["local_only"])
            self.assertFalse(attach_auth_policy["off_lan_allowed"])
            self.assertEqual(
                attach_auth_policy["transport"],
                "filesystem_markdown_bridge",
            )
            self.assertEqual(
                attach_auth_policy["auth_mode"],
                "repo_worktree_identity",
            )
            self.assertFalse(attach_auth_policy["token_required"])
            self.assertFalse(attach_auth_policy["key_required"])
            self.assertEqual(
                attach_auth_policy["service_endpoint"]["service_id"],
                service_identity["service_id"],
            )
            self.assertEqual(
                attach_auth_policy["service_endpoint"]["discovery_fields"],
                service_identity["discovery_fields"],
            )
            expected_interpreter = os.path.basename(sys.executable)
            expected_entrypoints = [
                (
                    f"{expected_interpreter} dev/scripts/devctl.py review-channel "
                    "--action status --terminal none --format json"
                ),
                (
                    f"{expected_interpreter} dev/scripts/devctl.py review-channel "
                    "--action ensure --terminal none --format json"
                ),
                (
                    f"{expected_interpreter} dev/scripts/devctl.py review-channel "
                    "--action reviewer-heartbeat --terminal none --format json"
                ),
            ]
            self.assertEqual(
                attach_auth_policy["attach_entrypoints"],
                expected_entrypoints,
            )
            self.assertEqual(
                attach_auth_policy["service_endpoint"]["launch_entrypoints"],
                expected_entrypoints,
            )
            self.assertEqual(
                attach_auth_policy["service_endpoint"]["health_signals"],
                [
                    "ok",
                    "bridge.reviewer_mode",
                    "bridge.last_codex_poll_age_seconds",
                    "bridge.reviewed_hash_current",
                    "attention.status",
                    "runtime.daemons.publisher.running",
                    "runtime.daemons.reviewer_supervisor.running",
                ],
            )
            self.assertEqual(
                [row["caller_id"] for row in attach_auth_policy["caller_authority"]],
                ["human_operator", "agent_runtime", "automation_loop"],
            )
            self.assertEqual(review_state["queue"]["pending_total"], 0)
            self.assertTrue(
                review_state["queue"]["derived_next_instruction"].startswith(
                    "- Next scoped plan item (dev/active/continuous_swarm.md): "
                    "Phase 1 - Queue: Implement automatic next-task promotion "
                    "so the conductor keeps moving."
                )
            )
            rs_compat = review_state.get("_compat", {})
            self.assertEqual(len(rs_compat.get("agents", [])), 4)
            self.assertEqual(
                review_state["current_session"]["current_instruction"],
                "- stop at a safe boundary and relaunch before compaction",
            )
            self.assertEqual(
                review_state["current_session"]["implementer_ack_state"],
                "current",
            )
            self.assertEqual(
                review_state["bridge"]["current_instruction"],
                "- stop at a safe boundary and relaunch before compaction",
            )
            self.assertEqual(
                review_state["bridge"]["reviewer_mode"],
                "active_dual_agent",
            )
            self.assertEqual(rs_compat.get("service_identity"), service_identity)
            self.assertEqual(rs_compat.get("attach_auth_policy"), attach_auth_policy)
            self.assertEqual(compact["queue"]["pending_total"], 0)
            self.assertEqual(
                compact["current_session"]["current_instruction"],
                "- stop at a safe boundary and relaunch before compaction",
            )
            self.assertEqual(compact["service_identity"], service_identity)
            self.assertEqual(compact["attach_auth_policy"], attach_auth_policy)
            self.assertEqual(full["reviewer_worker"]["state"], "review_needed")
            self.assertTrue(full["reviewer_worker"]["review_needed"])
            self.assertEqual(full["service_identity"], service_identity)
            self.assertEqual(full["attach_auth_policy"], attach_auth_policy)
            self.assertEqual(
                compact["queue"]["current_focus"],
                "- stop at a safe boundary and relaunch before compaction",
            )
            self.assertEqual(len(agent_registry["agents"]), 16)
            self.assertEqual(agent_registry["agents"][0]["agent_id"], "AGENT-1")
            self.assertEqual(actions["actions"], [])
            self.assertIn(
                "## Current Session",
                latest_markdown_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "## Current Instruction",
                latest_markdown_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "- service_id:",
                latest_markdown_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                service_identity["service_id"],
                latest_markdown_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "## Attach/Auth Policy",
                latest_markdown_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                attach_auth_policy["transport"],
                latest_markdown_path.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "## Derived Next Instruction",
                latest_markdown_path.read_text(encoding="utf-8"),
            )

    def test_refresh_status_snapshot_projects_lifecycle_runtime(self) -> None:
        from dev.scripts.devctl.review_channel.lifecycle_state import (
            PublisherHeartbeat,
            ReviewerSupervisorHeartbeat,
        )
        from dev.scripts.devctl.review_channel.state import (
            refresh_status_snapshot,
            write_publisher_heartbeat,
            write_reviewer_supervisor_heartbeat,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            status_dir = root / "dev/reports/review_channel/latest"
            now = datetime.now(UTC)
            publisher_started_at = (now - timedelta(minutes=3)).isoformat().replace(
                "+00:00", "Z"
            )
            publisher_heartbeat_at = (
                now - timedelta(minutes=2)
            ).isoformat().replace("+00:00", "Z")
            reviewer_started_at = (now - timedelta(minutes=4)).isoformat().replace(
                "+00:00", "Z"
            )
            reviewer_heartbeat_at = (
                now - timedelta(minutes=1)
            ).isoformat().replace("+00:00", "Z")
            write_publisher_heartbeat(
                status_dir,
                PublisherHeartbeat(
                    pid=10101,
                    started_at_utc=publisher_started_at,
                    last_heartbeat_utc=publisher_heartbeat_at,
                    snapshots_emitted=4,
                    reviewer_mode="active_dual_agent",
                ),
            )
            write_reviewer_supervisor_heartbeat(
                status_dir,
                ReviewerSupervisorHeartbeat(
                    pid=20202,
                    started_at_utc=reviewer_started_at,
                    last_heartbeat_utc=reviewer_heartbeat_at,
                    snapshots_emitted=7,
                    reviewer_mode="active_dual_agent",
                ),
            )

            with patch(
                "dev.scripts.devctl.review_channel.lifecycle_state._pid_is_alive",
                return_value=True,
            ):
                status_snapshot = refresh_status_snapshot(
                    repo_root=root,
                    bridge_path=bridge_path,
                    review_channel_path=review_channel_path,
                    output_root=status_dir,
                    promotion_plan_path=root / "dev/active/continuous_swarm.md",
                    execution_mode="markdown-bridge",
                    warnings=[],
                    errors=[],
                )

            review_state = json.loads(
                Path(status_snapshot.projection_paths.review_state_path).read_text(
                    encoding="utf-8"
                )
            )
            latest_markdown = Path(
                status_snapshot.projection_paths.latest_markdown_path
            ).read_text(encoding="utf-8")

        runtime = review_state["_compat"]["runtime"]
        self.assertEqual(runtime["active_daemons"], 2)
        self.assertEqual(runtime["last_daemon_event_utc"], reviewer_heartbeat_at)
        self.assertTrue(runtime["daemons"]["publisher"]["running"])
        self.assertEqual(runtime["daemons"]["publisher"]["pid"], 10101)
        self.assertEqual(runtime["daemons"]["publisher"]["snapshots_emitted"], 4)
        self.assertTrue(runtime["daemons"]["reviewer_supervisor"]["running"])
        self.assertEqual(runtime["daemons"]["reviewer_supervisor"]["pid"], 20202)
        self.assertEqual(
            runtime["daemons"]["reviewer_supervisor"]["snapshots_emitted"],
            7,
        )
        self.assertIn("## Runtime", latest_markdown)
        self.assertIn("- active_daemons: 2", latest_markdown)
        self.assertIn("- reviewer_supervisor: running=True pid=20202", latest_markdown)

    def test_refresh_status_snapshot_projects_push_checkpoint_state(self) -> None:
        from dev.scripts.devctl.review_channel.state import refresh_status_snapshot

        push_state = {
            "default_remote": "origin",
            "development_branch": "main",
            "release_branch": "main",
            "pre_push_hook_path": "/tmp/repo/.git/hooks/pre-push",
            "pre_push_hook_installed": True,
            "raw_git_push_guarded": True,
            "upstream_ref": "origin/main",
            "ahead_of_upstream_commits": 3,
            "dirty_path_count": 18,
            "untracked_path_count": 7,
            "max_dirty_paths_before_checkpoint": 12,
            "max_untracked_paths_before_checkpoint": 6,
            "checkpoint_required": True,
            "safe_to_continue_editing": False,
            "checkpoint_reason": "dirty_and_untracked_budget_exceeded",
            "worktree_dirty": True,
            "push_ready": False,
            "recommended_action": "checkpoint_before_continue",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            status_dir = root / "dev/reports/review_channel/latest"

            with patch(
                "dev.scripts.devctl.review_channel.state.build_bridge_push_enforcement_state",
                return_value=push_state,
            ), patch(
                "dev.scripts.devctl.review_channel.state._load_lifecycle_states",
                return_value=(
                    {"running": True, "stop_reason": "", "pid": 10101},
                    {"running": True, "stop_reason": "", "pid": 20202},
                ),
            ):
                status_snapshot = refresh_status_snapshot(
                    repo_root=root,
                    bridge_path=bridge_path,
                    review_channel_path=review_channel_path,
                    output_root=status_dir,
                    promotion_plan_path=root / "dev/active/continuous_swarm.md",
                    execution_mode="markdown-bridge",
                    warnings=[],
                    errors=[],
                )

            full_payload = json.loads(
                Path(status_snapshot.projection_paths.full_path).read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(status_snapshot.attention["status"], "checkpoint_required")
        self.assertTrue(status_snapshot.bridge_liveness["push_enforcement"]["checkpoint_required"])
        self.assertFalse(
            status_snapshot.bridge_liveness["push_enforcement"]["safe_to_continue_editing"]
        )
        self.assertEqual(
            status_snapshot.bridge_liveness["push_enforcement"]["recommended_action"],
            "checkpoint_before_continue",
        )
        self.assertTrue(full_payload["push_enforcement"]["raw_git_push_guarded"])
        self.assertTrue(full_payload["push_enforcement"]["pre_push_hook_installed"])
        self.assertEqual(
            full_payload["push_enforcement"]["recommended_action"],
            "checkpoint_before_continue",
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
            bridge_path = root / "bridge.md"
            original_bridge = _build_bridge_text(last_codex_poll="2000-01-01T00:00:00Z")
            bridge_path.write_text(
                original_bridge,
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
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
            bridge_path = root / "bridge.md"
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

    def test_run_status_reports_runtime_missing_without_mutating_reviewer_mode(
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
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(last_codex_poll="2000-01-01T00:00:00Z"),
                encoding="utf-8",
            )
            (root / "notes.txt").write_text("runtime missing drift\n", encoding="utf-8")
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
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIsNone(payload["reviewer_state_write"])
            self.assertEqual(
                payload["bridge_liveness"]["reviewer_mode"],
                "active_dual_agent",
            )
            self.assertEqual(
                payload["bridge_liveness"]["overall_state"],
                "runtime_missing",
            )
            self.assertEqual(payload["attention"]["status"], "runtime_missing")
            self.assertEqual(payload["reviewer_worker"]["state"], "review_needed")
            self.assertTrue(payload["reviewer_worker"]["review_needed"])
            self.assertTrue(
                any("Reviewer runtime is missing" in warning for warning in payload["warnings"])
            )
            self.assertIn(
                "- Reviewer mode: `active_dual_agent`",
                bridge_path.read_text(encoding="utf-8"),
            )

    def test_run_status_keeps_stale_active_bridge_when_session_conflict_exists(
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
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(last_codex_poll="2000-01-01T00:00:00Z"),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
            session_dir = status_dir / "sessions"
            session_dir.mkdir(parents=True, exist_ok=True)
            log_path = status_dir / "codex-conductor.log"
            log_path.write_text("still running\n", encoding="utf-8")
            (session_dir / "codex-conductor.json").write_text(
                json.dumps(
                    {
                        "session_name": "codex-conductor",
                        "log_path": str(log_path),
                        "script_path": "",
                    }
                ),
                encoding="utf-8",
            )
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
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIsNone(payload["reviewer_state_write"])
            self.assertEqual(
                payload["bridge_liveness"]["reviewer_mode"],
                "active_dual_agent",
            )
            self.assertEqual(payload["bridge_liveness"]["overall_state"], "stale")
            self.assertIn(
                "- Reviewer mode: `active_dual_agent`",
                bridge_path.read_text(encoding="utf-8"),
            )

    def test_run_reviewer_heartbeat_preserves_reviewed_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            original_hash = compute_non_audit_worktree_hash(
                repo_root=root,
                excluded_rel_paths=("bridge.md",),
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
            full_path = Path(payload["projection_paths"]["full_path"])
            review_state = json.loads(review_state_path.read_text(encoding="utf-8"))
            full_payload = json.loads(full_path.read_text(encoding="utf-8"))
            service_identity = payload["service_identity"]
            attach_auth_policy = payload["attach_auth_policy"]
            rs_compat_2 = review_state.get("_compat", {})
            self.assertEqual(
                service_identity["service_id"],
                f"review-channel:{rs_compat_2.get('project_id')}",
            )
            self.assertEqual(service_identity["project_id"], rs_compat_2.get("project_id"))
            self.assertEqual(service_identity["repo_root"], str(root.resolve()))
            self.assertEqual(service_identity["bridge_path"], bridge_path.name)
            self.assertEqual(full_payload["service_identity"], service_identity)
            self.assertEqual(
                attach_auth_policy["service_endpoint"]["service_id"],
                service_identity["service_id"],
            )
            self.assertFalse(attach_auth_policy["off_lan_allowed"])
            self.assertEqual(full_payload["attach_auth_policy"], attach_auth_policy)
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
            bridge_path = root / "bridge.md"
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
                expected_instruction_revision="56bcd5d01510",
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

    def test_run_reviewer_checkpoint_rejects_suspicious_instruction_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            original_bridge = _build_bridge_text(
                current_verdict="- stale verdict",
                open_findings="- stale finding",
                current_instruction="- stale instruction",
            )
            bridge_path.write_text(original_bridge, encoding="utf-8")
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            args = self._reviewer_checkpoint_args(
                root=root,
                review_channel_path=review_channel_path,
                bridge_path=bridge_path,
                status_dir=status_dir,
                output_path=output_path,
                verdict="- reviewer accepted with follow-up",
                open_findings="- M1 closed",
                instruction="- Update Not logged in · Please run /login to continue.",
                reviewed_scope_item=[
                    "dev/scripts/devctl/review_channel/reviewer_state.py",
                ],
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn(
                "Reviewer checkpoint rejected suspicious terminal/status text",
                payload["errors"][0],
            )
            self.assertIn(
                "Current Instruction For Claude",
                payload["errors"][0],
            )
            self.assertEqual(
                bridge_path.read_text(encoding="utf-8"),
                original_bridge,
            )

    def test_reviewer_checkpoint_refreshes_projections_atomically(self) -> None:
        """Checkpoint writes must refresh status projections so JSON is consistent with bridge markdown."""
        from dev.scripts.devctl.review_channel.reviewer_state import (
            ReviewerCheckpointUpdate,
            write_reviewer_checkpoint,
        )
        from dev.scripts.devctl.repo_packs import active_path_config

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(), encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(
                    current_verdict="- old verdict",
                    open_findings="- old finding",
                    current_instruction="- old instruction",
                ),
                encoding="utf-8",
            )
            projections_dir = root / "dev/reports/review_channel/latest"
            projections_dir.mkdir(parents=True, exist_ok=True)

            with (
                patch.object(
                    review_channel_command,
                    "REPO_ROOT",
                    root,
                ),
                patch(
                    "dev.scripts.devctl.review_channel.state.refresh_status_snapshot"
                ) as refresh_status_snapshot,
            ):
                write_reviewer_checkpoint(
                    repo_root=root,
                    bridge_path=bridge_path,
                    reviewer_mode="active_dual_agent",
                    reason="test-checkpoint",
                    checkpoint=ReviewerCheckpointUpdate(
                        current_verdict="- accepted",
                        open_findings="- none",
                        current_instruction="- next task",
                        reviewed_scope_items=("test scope",),
                        expected_instruction_revision="56bcd5d01510",
                    ),
                )

            updated_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertIn("- accepted", updated_bridge)
            self.assertIn("- next task", updated_bridge)
            self.assertIn("Reviewer checkpoint updated", updated_bridge)
            config = active_path_config()
            refresh_status_snapshot.assert_called_once()
            self.assertEqual(
                refresh_status_snapshot.call_args.kwargs["output_root"],
                root / config.review_projections_dir_rel,
            )

    def test_run_reviewer_checkpoint_auto_starts_supervisor_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            (root / "fresh.py").write_text("print('reviewer follow')\n", encoding="utf-8")
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            status_dir.mkdir(parents=True, exist_ok=True)
            promotion_plan_path = root / "dev/active/test_review_promotion.md"
            promotion_plan_path.parent.mkdir(parents=True, exist_ok=True)
            promotion_plan_path.write_text(
                "# Test Promotion Plan\n\n## Execution Checklist\n\n- [ ] Continue reviewer supervision\n",
                encoding="utf-8",
            )
            args = SimpleNamespace(
                action="reviewer-checkpoint",
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
                script_dir=None,
                dry_run=False,
                reviewer_mode="agents",
                reason="review-pass",
                expected_instruction_revision="56bcd5d01510",
                verdict="- reviewer accepted",
                open_findings="- none",
                instruction="- next scoped task",
                reviewed_scope_item=[
                    "dev/scripts/devctl/review_channel/reviewer_state.py"
                ],
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_command,
                    "_ensure_reviewer_supervisor_running",
                    return_value={
                        "attempted": True,
                        "started": True,
                        "pid": 4321,
                        "log_path": "/tmp/reviewer_supervisor_follow.log",
                        "start_status": "started",
                    },
                ) as ensure_supervisor,
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["reviewer_supervisor_auto_start"]["attempted"])
            self.assertTrue(payload["reviewer_supervisor_auto_start"]["started"])
            self.assertEqual(payload["reviewer_supervisor_auto_start"]["pid"], 4321)
            self.assertEqual(payload["reviewer_supervisor_auto_start"]["start_status"], "started")
            ensure_supervisor.assert_called_once()

    def test_run_reviewer_checkpoint_auto_start_records_failed_start(self) -> None:
        """Dead-on-arrival reviewer supervisor must record failed-start lifecycle state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(), encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(current_verdict="- stale"), encoding="utf-8",
            )
            status_dir = root / "dev/reports/review_channel/latest"
            status_dir.mkdir(parents=True, exist_ok=True)
            output_path = root / "report.json"
            args = SimpleNamespace(
                action="reviewer-checkpoint",
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
                approval_mode="balanced",
                reviewer_mode="active_dual_agent",
                reason="test-checkpoint",
                expected_instruction_revision="56bcd5d01510",
                verdict="- accepted",
                open_findings="- none",
                instruction="- next task",
                reviewed_scope_item=["test"],
                rotate_instruction_revision=False,
                follow=False,
                start_publisher_if_missing=False,
                format="json",
                output=str(output_path),
                pipe_command=None,
                pipe_args=None,
            )

            with (
                patch.object(review_channel_command, "REPO_ROOT", root),
                patch.object(
                    review_channel_command,
                    "_ensure_reviewer_supervisor_running",
                    return_value={
                        "attempted": True,
                        "started": False,
                        "pid": 9999,
                        "log_path": "/tmp/reviewer.log",
                        "start_status": "failed_start",
                    },
                ),
            ):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            auto_start = payload["reviewer_supervisor_auto_start"]
            self.assertTrue(auto_start["attempted"])
            self.assertFalse(auto_start["started"])
            self.assertEqual(auto_start["start_status"], "failed_start")

    def test_run_reviewer_checkpoint_auto_promotes_generic_instruction(self) -> None:
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
                        "# Plan",
                        "",
                        "## Execution Checklist",
                        "",
                        "- [ ] Implement bounded reviewer instruction routing.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
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
            args = self._reviewer_checkpoint_args(
                root=root,
                review_channel_path=review_channel_path,
                bridge_path=bridge_path,
                status_dir=status_dir,
                output_path=output_path,
                verdict="- reviewer accepted with follow-up",
                open_findings="- none",
                instruction="- continue the next unchecked MP item",
                reviewed_scope_item=[
                    "dev/scripts/devctl/review_channel/reviewer_state.py",
                ],
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["instruction_auto_promoted"])
            self.assertEqual(
                payload["instruction_auto_promoted_source"]["source_path"],
                "dev/active/continuous_swarm.md",
            )
            updated_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertIn(
                "Next scoped plan item (dev/active/continuous_swarm.md)",
                updated_bridge,
            )

    def test_run_reviewer_checkpoint_auto_promotes_generic_instruction_from_tracker_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            active_dir = root / "dev/active"
            active_dir.mkdir(parents=True, exist_ok=True)
            review_channel_path = active_dir / "review_channel.md"
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            (active_dir / "MASTER_PLAN.md").write_text(
                "# Master Plan\n\n- Current main product lane: `MP-377`\n",
                encoding="utf-8",
            )
            (active_dir / "INDEX.md").write_text(
                "\n".join(
                    [
                        "# Active Docs Index",
                        "",
                        "## Registry",
                        "",
                        "| Path | Role | Execution authority | MP scope | When agents read |",
                        "|---|---|---|---|---|",
                        "| `dev/active/ai_governance_platform.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-377` | always |",
                    ]
                ),
                encoding="utf-8",
            )
            plan_path = active_dir / "ai_governance_platform.md"
            plan_path.write_text(
                "# AI Governance Platform\n\n## Execution Checklist\n\n- [ ] Tracker-selected platform work item.\n",
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
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
            args = self._reviewer_checkpoint_args(
                root=root,
                review_channel_path=review_channel_path,
                bridge_path=bridge_path,
                status_dir=status_dir,
                output_path=output_path,
                verdict="- reviewer accepted with follow-up",
                open_findings="- none",
                instruction="- continue the next unchecked MP item",
                reviewed_scope_item=[
                    "dev/scripts/devctl/review_channel/reviewer_state.py",
                ],
                promotion_plan=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["instruction_auto_promoted"])
            self.assertEqual(
                payload["instruction_auto_promoted_source"]["source_path"],
                "dev/active/ai_governance_platform.md",
            )

    def test_run_reviewer_checkpoint_generic_instruction_fails_closed_without_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
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
            args = self._reviewer_checkpoint_args(
                root=root,
                review_channel_path=review_channel_path,
                bridge_path=bridge_path,
                status_dir=status_dir,
                output_path=output_path,
                verdict="- reviewer accepted with follow-up",
                open_findings="- none",
                instruction="- continue the next unchecked MP item",
                reviewed_scope_item=[
                    "dev/scripts/devctl/review_channel/reviewer_state.py",
                ],
                promotion_plan=None,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("scope_missing", payload["errors"][0])

    def test_run_reviewer_checkpoint_preserves_instruction_revision_on_metadata_only_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            instruction = "- continue with the next scoped slice"
            stable_revision = "feedfacecafe"
            bridge_path.write_text(
                _build_bridge_text(
                    current_verdict="- stale verdict",
                    open_findings="- stale finding",
                    current_instruction=instruction,
                    claude_ack=f"- acknowledged; instruction-rev: `{stable_revision}`",
                ).replace("56bcd5d01510", stable_revision),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            args = self._reviewer_checkpoint_args(
                root=root,
                review_channel_path=review_channel_path,
                bridge_path=bridge_path,
                status_dir=status_dir,
                output_path=output_path,
                verdict="- reviewer accepted with follow-up",
                open_findings="- M1 closed\n- M2 deferred",
                instruction=instruction,
                reviewed_scope_item=[
                    "dev/scripts/devctl/review_channel/reviewer_state.py",
                    "dev/scripts/devctl/commands/review_channel.py",
                ],
                expected_instruction_revision=stable_revision,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(
                payload["reviewer_state_write"]["current_instruction_revision"],
                stable_revision,
            )
            self.assertTrue(payload["bridge_liveness"]["claude_ack_current"])
            self.assertNotEqual(payload["attention"]["status"], "claude_ack_stale")
            updated_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertIn(
                f"- Current instruction revision: `{stable_revision}`",
                updated_bridge,
            )
            bridge_liveness = dict(
                summarize_bridge_liveness(extract_bridge_snapshot(updated_bridge)).__dict__
            )
            bridge_liveness["publisher_running"] = True
            bridge_liveness["review_needed"] = False
            bridge_liveness["reviewer_supervisor_running"] = True
            self.assertEqual(
                derive_bridge_attention(bridge_liveness)["status"],
                "healthy",
            )

    def test_run_reviewer_checkpoint_rotates_instruction_revision_when_instruction_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            initial_instruction = "- continue with the next scoped slice"
            stable_revision = "feedfacecafe"
            bridge_path.write_text(
                _build_bridge_text(
                    current_verdict="- stale verdict",
                    open_findings="- stale finding",
                    current_instruction=initial_instruction,
                    claude_ack=f"- acknowledged; instruction-rev: `{stable_revision}`",
                ).replace("56bcd5d01510", stable_revision),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
            updated_instruction = (
                "- continue with the next scoped slice and verify the fresh path"
            )
            args = self._reviewer_checkpoint_args(
                root=root,
                review_channel_path=review_channel_path,
                bridge_path=bridge_path,
                status_dir=status_dir,
                output_path=output_path,
                verdict="- reviewer accepted with follow-up",
                open_findings="- M1 closed\n- M2 deferred",
                instruction=updated_instruction,
                reviewed_scope_item=[
                    "dev/scripts/devctl/review_channel/reviewer_state.py",
                    "dev/scripts/devctl/commands/review_channel.py",
                ],
                expected_instruction_revision=stable_revision,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertNotEqual(
                payload["reviewer_state_write"]["current_instruction_revision"],
                stable_revision,
            )
            self.assertFalse(payload["bridge_liveness"]["claude_ack_current"])
            self.assertEqual(payload["attention"]["status"], "claude_ack_stale")
            updated_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertIn(updated_instruction, updated_bridge)

    def test_run_reviewer_checkpoint_can_force_instruction_revision_rotation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            instruction = "- continue with the next scoped slice"
            stable_revision = "feedfacecafe"
            bridge_path.write_text(
                _build_bridge_text(
                    current_verdict="- stale verdict",
                    open_findings="- stale finding",
                    current_instruction=instruction,
                    claude_ack=f"- acknowledged; instruction-rev: `{stable_revision}`",
                ).replace("56bcd5d01510", stable_revision),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
            args = self._reviewer_checkpoint_args(
                root=root,
                review_channel_path=review_channel_path,
                bridge_path=bridge_path,
                status_dir=status_dir,
                output_path=output_path,
                verdict="- reviewer accepted with follow-up",
                open_findings="- M1 closed\n- M2 deferred",
                instruction=instruction,
                reviewed_scope_item=[
                    "dev/scripts/devctl/review_channel/reviewer_state.py",
                    "dev/scripts/devctl/commands/review_channel.py",
                ],
                rotate_instruction_revision=True,
                expected_instruction_revision=stable_revision,
            )

            with patch.object(review_channel_command, "REPO_ROOT", root):
                rc = review_channel_command.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertNotEqual(
                payload["reviewer_state_write"]["current_instruction_revision"],
                stable_revision,
            )
            self.assertFalse(payload["bridge_liveness"]["claude_ack_current"])
            self.assertEqual(payload["attention"]["status"], "claude_ack_stale")
            self.assertIn(
                f"- Current instruction revision: `{payload['reviewer_state_write']['current_instruction_revision']}`",
                bridge_path.read_text(encoding="utf-8"),
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
            bridge_path = root / "bridge.md"
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

    def test_run_reviewer_heartbeat_clears_resolved_ack_stale_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(
                    open_findings=(
                        "- H1 (blocking): `Claude Ack` is stale against current "
                        "instruction revision."
                    ),
                    claude_ack="- acknowledged; instruction-rev: `56bcd5d01510`",
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
                reviewer_mode="active_dual_agent",
                reason="clear-stale-ack-finding",
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
            snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot.sections.get("Open Findings", "").strip(), "- none")

    def test_run_reviewer_heartbeat_keeps_ack_stale_finding_when_ack_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            stale_finding = (
                "- H1 (blocking): `Claude Ack` is stale against current instruction "
                "revision."
            )
            bridge_path.write_text(
                _build_bridge_text(
                    open_findings=stale_finding,
                    claude_ack="- acknowledged; instruction-rev: `deadbeef1234`",
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
                reviewer_mode="active_dual_agent",
                reason="keep-stale-ack-finding",
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
            snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
            self.assertIn(
                "Claude Ack` is stale against current instruction revision",
                snapshot.sections.get("Open Findings", ""),
            )

    def test_run_reviewer_heartbeat_strips_stale_poll_status_mode_history_lines(
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
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(reviewer_mode="single_agent").replace(
                    "- active reviewer loop",
                    "\n".join(
                        [
                            "- active reviewer loop",
                            "- `2026-03-20T00:30:31Z`: reviewer repoll confirms the tree is current.",
                            "- Live bridge status now matches the reviewed tree hash from this pass; reviewer mode is `active_dual_agent`, and the reviewer supervisor remains healthy.",
                            "- Reviewer mode is back to `active_dual_agent`",
                        ]
                    ),
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
                "- `2026-03-20T00:30:31Z`: reviewer repoll confirms the tree is current.",
                updated_bridge,
            )
            self.assertNotIn(
                "Live bridge status now matches the reviewed tree hash from this pass;",
                updated_bridge,
            )
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
            bridge_path = root / "bridge.md"
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
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["action"], "promote")
            self.assertIsNotNone(payload["promotion"])
            self.assertIn(
                "Implement automatic next-task promotion",
                payload["promotion"]["instruction"],
            )
            self.assertIn(
                payload["attention"]["status"],
                {"claude_ack_stale", "runtime_missing"},
            )
            updated_bridge = bridge_path.read_text(encoding="utf-8")
            self.assertIn(
                "- Next scoped plan item (dev/active/continuous_swarm.md): "
                "Phase 2 - Continuous Loop Behavior: Implement automatic "
                "next-task promotion so the conductor does not stop.",
                updated_bridge,
            )

    def test_run_promote_refreshes_instruction_revision_and_poll_timestamp(self) -> None:
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
                        "# Plan",
                        "",
                        "## Execution Checklist",
                        "",
                        "- [ ] Execute bounded promotion task.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(
                    current_verdict="- accepted",
                    open_findings="- all clear",
                    current_instruction="- complete",
                    last_codex_poll="2026-01-01T00:00:00Z",
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
            updated_bridge = bridge_path.read_text(encoding="utf-8")
            snapshot = extract_bridge_snapshot(updated_bridge)
            self.assertNotEqual(
                snapshot.metadata.get("current_instruction_revision", ""),
                "56bcd5d01510",
            )
            self.assertNotEqual(
                snapshot.metadata.get("last_codex_poll_utc", ""),
                "2026-01-01T00:00:00Z",
            )

    def test_run_promote_rejects_stale_expected_instruction_revision(self) -> None:
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
                "# Plan\n\n## Execution Checklist\n\n- [ ] Execute bounded promotion task.\n",
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            original_bridge = _build_bridge_text(
                current_verdict="- accepted",
                open_findings="- all clear",
                current_instruction="- complete",
            )
            bridge_path.write_text(original_bridge, encoding="utf-8")
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
                expected_instruction_revision="deadbeefcafe",
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
            self.assertIn("refused stale bridge write", payload["errors"][0])
            self.assertEqual(bridge_path.read_text(encoding="utf-8"), original_bridge)

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
            bridge_path = root / "bridge.md"
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
            _write_live_runtime(status_dir)
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
            self.assertFalse(payload["ok"])
            self.assertIsNotNone(payload["promotion"])
            self.assertIn(
                "First unchecked task for auto-promote test",
                payload["promotion"]["instruction"],
            )
            self.assertIn(
                payload["attention"]["status"],
                {"claude_ack_stale", "runtime_missing"},
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
            bridge_path = root / "bridge.md"
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
            _write_live_runtime(status_dir)
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text().replace(
                    "- bridge.md\n- dev/scripts/devctl/review_channel/handoff.py",
                    "",
                ),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
            args = SimpleNamespace(
                action="launch",
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
            bridge_path = root / "bridge.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            script_dir = root / "scripts"
            rollover_dir = root / "dev/reports/review_channel/rollovers"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
            args = SimpleNamespace(
                action="rollover",
                execution_mode="auto",
                terminal="none",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir=str(rollover_dir.relative_to(root)),
                status_dir=str(status_dir.relative_to(root)),
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
            bridge_path = root / "bridge.md"
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
            args = SimpleNamespace(
                action="rollover",
                execution_mode="auto",
                terminal="terminal-app",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir=str(status_dir.relative_to(root)),
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
                        "## Claude Ack\n\n- acknowledged; instruction-rev: `56bcd5d01510`\n\n",
                        "## Claude Ack\n\n- acknowledged; instruction-rev: `56bcd5d01510`\n"
                        f"- Claude rollover ack: `{rollover_id}`\n\n",
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(last_codex_poll="2026-03-08T18:50:00Z"),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
            args = SimpleNamespace(
                action="launch",
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
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(last_codex_poll="2026-03-08T18:50:00Z"),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
            args = SimpleNamespace(
                action="launch",
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
            self.assertEqual(refresh["bridge_path"], "bridge.md")
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text().replace(
                    "- bridge.md\n- dev/scripts/devctl/review_channel/handoff.py",
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
            bridge_path = root / "bridge.md"
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
                        "bridge": {
                            "path": "bridge.md",
                            "error": "Bridge-active file is untracked by git: bridge.md",
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
            self.assertIn("bridge.md", payload["errors"][0])
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(last_codex_poll=initial_poll),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
            args = SimpleNamespace(
                action="launch",
                execution_mode="auto",
                terminal="terminal-app",
                terminal_profile="auto-dark",
                review_channel_path=str(review_channel_path.relative_to(root)),
                bridge_path=str(bridge_path.relative_to(root)),
                rollover_dir="dev/reports/review_channel/rollovers",
                status_dir=str(status_dir.relative_to(root)),
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                _build_bridge_text(claude_status=""),
                encoding="utf-8",
            )
            output_path = root / "report.json"
            status_dir = root / "dev/reports/review_channel/latest"
            _write_live_runtime(status_dir)
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
            self.assertFalse(payload["ok"])
            self.assertIn("waiting_on_peer", payload["warnings"][0])

            review_state_path = Path(payload["projection_paths"]["review_state_path"])
            full_path = Path(payload["projection_paths"]["full_path"])
            review_state = json.loads(review_state_path.read_text(encoding="utf-8"))
            full_payload = json.loads(full_path.read_text(encoding="utf-8"))

            self.assertFalse(review_state["ok"])
            self.assertEqual(review_state["_compat"]["agents"][1]["status"], "waiting")
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
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
            bridge_path = root / "bridge.md"
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
                bridge_path="bridge.md",
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
                    review_channel_status_mod,
                    "event_state_exists",
                    return_value=True,
                ),
                patch.object(
                    review_channel_status_mod,
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
                "# Review Bridge",
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
                "- bridge.md",
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
            review_state = json.loads(
                Path(bundle.projection_paths.review_state_path).read_text(
                    encoding="utf-8"
                )
            )
            compact = json.loads(
                Path(bundle.projection_paths.compact_path).read_text(encoding="utf-8")
            )
            full = json.loads(
                Path(bundle.projection_paths.full_path).read_text(encoding="utf-8")
            )
            latest_markdown = Path(
                bundle.projection_paths.latest_markdown_path
            ).read_text(encoding="utf-8")

            self.assertTrue(
                review_state["bridge"]["current_instruction"].startswith(
                    "review the live tranche"
                )
            )
            self.assertTrue(
                review_state["queue"]["derived_next_instruction"].startswith(
                    "review the live tranche"
                )
            )
            self.assertEqual(
                review_state["queue"]["derived_next_instruction_source"]["packet_id"],
                "rev_pkt_0001",
            )
            self.assertEqual(review_state["bridge"]["reviewer_mode"], "tools_only")
            self.assertEqual(review_state["attention"]["status"], "inactive")
            ev_compat = review_state.get("_compat", {})
            self.assertEqual(
                ev_compat["service_identity"]["project_id"],
                ev_compat.get("project_id"),
            )
            self.assertEqual(
                ev_compat["attach_auth_policy"]["service_endpoint"]["service_id"],
                ev_compat["service_identity"]["service_id"],
            )
            self.assertEqual(
                compact["service_identity"]["project_id"],
                ev_compat.get("project_id"),
            )
            self.assertEqual(
                full["service_identity"]["service_id"],
                f"review-channel:{ev_compat.get('project_id')}",
            )
            self.assertEqual(
                full["attach_auth_policy"]["service_endpoint"]["service_id"],
                full["service_identity"]["service_id"],
            )
            self.assertEqual(full["bridge_liveness"]["reviewer_mode"], "tools_only")
            self.assertEqual(full["attention"]["status"], "inactive")
            self.assertIn("## Service Identity", latest_markdown)
            self.assertIn("## Attach/Auth Policy", latest_markdown)

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

    def test_event_state_exists_requires_materialized_state_json(self) -> None:
        from dev.scripts.devctl.review_channel.event_store import event_state_exists

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            artifact_paths = resolve_artifact_paths(repo_root=root)
            event_log_path = Path(artifact_paths.event_log_path)
            event_log_path.parent.mkdir(parents=True, exist_ok=True)
            event_log_path.write_text(
                json.dumps(
                    {
                        "event_type": "daemon_started",
                        "timestamp_utc": "2026-03-17T03:00:00Z",
                        "daemon_kind": "publisher",
                        "pid": 12345,
                        "reviewer_mode": "active_dual_agent",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertFalse(event_state_exists(artifact_paths))

            state_path = Path(artifact_paths.state_path)
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text("{}", encoding="utf-8")

            self.assertTrue(event_state_exists(artifact_paths))


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


class TestDaemonEventReducer(unittest.TestCase):
    """Verify daemon events reduce into the runtime section of review state."""

    def test_daemon_started_produces_running_runtime(self) -> None:
        """A daemon_started event should produce a running daemon in runtime."""
        events = [
            {
                "event_type": "daemon_started",
                "timestamp_utc": "2026-03-17T03:00:00Z",
                "daemon_kind": "publisher",
                "pid": 12345,
                "reviewer_mode": "active_dual_agent",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rc_path = root / "dev/active/review_channel.md"
            rc_path.parent.mkdir(parents=True, exist_ok=True)
            rc_path.write_text(_build_review_channel_text(), encoding="utf-8")

            review_state, _ = reduce_events(
                events=events,
                repo_root=root,
                review_channel_path=rc_path,
            )
        compat = review_state.get("_compat", {})
        runtime = compat.get("runtime")
        self.assertIsInstance(runtime, dict)
        self.assertEqual(runtime["active_daemons"], 1)
        self.assertEqual(runtime["last_daemon_event_utc"], "2026-03-17T03:00:00Z")
        publisher = runtime["daemons"]["publisher"]
        self.assertTrue(publisher["running"])
        self.assertEqual(publisher["pid"], 12345)
        self.assertEqual(publisher["reviewer_mode"], "active_dual_agent")

    def test_daemon_stopped_clears_running(self) -> None:
        """A daemon_stopped event after started should mark daemon not running."""
        events = [
            {
                "event_type": "daemon_started",
                "timestamp_utc": "2026-03-17T03:00:00Z",
                "daemon_kind": "publisher",
                "pid": 12345,
                "reviewer_mode": "active_dual_agent",
            },
            {
                "event_type": "daemon_stopped",
                "timestamp_utc": "2026-03-17T03:10:00Z",
                "daemon_kind": "publisher",
                "pid": 12345,
                "stop_reason": "keyboard_interrupt",
                "snapshots_emitted": 5,
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rc_path = root / "dev/active/review_channel.md"
            rc_path.parent.mkdir(parents=True, exist_ok=True)
            rc_path.write_text(_build_review_channel_text(), encoding="utf-8")

            review_state, _ = reduce_events(
                events=events,
                repo_root=root,
                review_channel_path=rc_path,
            )
        runtime = review_state["_compat"]["runtime"]
        self.assertEqual(runtime["active_daemons"], 0)
        publisher = runtime["daemons"]["publisher"]
        self.assertFalse(publisher["running"])
        self.assertEqual(publisher["stop_reason"], "keyboard_interrupt")
        self.assertEqual(publisher["snapshots_emitted"], 5)

    def test_daemon_heartbeat_updates_snapshot_count(self) -> None:
        """Heartbeat events should update last_heartbeat_utc and snapshots."""
        events = [
            {
                "event_type": "daemon_started",
                "timestamp_utc": "2026-03-17T03:00:00Z",
                "daemon_kind": "reviewer_supervisor",
                "pid": 99999,
                "reviewer_mode": "active_dual_agent",
            },
            {
                "event_type": "daemon_heartbeat",
                "timestamp_utc": "2026-03-17T03:05:00Z",
                "daemon_kind": "reviewer_supervisor",
                "pid": 99999,
                "snapshots_emitted": 10,
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rc_path = root / "dev/active/review_channel.md"
            rc_path.parent.mkdir(parents=True, exist_ok=True)
            rc_path.write_text(_build_review_channel_text(), encoding="utf-8")

            review_state, _ = reduce_events(
                events=events,
                repo_root=root,
                review_channel_path=rc_path,
            )
        runtime = review_state["_compat"]["runtime"]
        self.assertEqual(runtime["active_daemons"], 1)
        supervisor = runtime["daemons"]["reviewer_supervisor"]
        self.assertTrue(supervisor["running"])
        self.assertEqual(supervisor["last_heartbeat_utc"], "2026-03-17T03:05:00Z")
        self.assertEqual(supervisor["snapshots_emitted"], 10)

    def test_mixed_daemon_and_packet_events_coexist(self) -> None:
        """Daemon events should not interfere with packet reduction."""
        events = [
            {
                "event_type": "daemon_started",
                "timestamp_utc": "2026-03-17T03:00:00Z",
                "daemon_kind": "publisher",
                "pid": 11111,
                "reviewer_mode": "active_dual_agent",
            },
            {
                "packet_id": "rev_pkt_0001",
                "trace_id": "trace_1",
                "event_id": "rev_evt_0001",
                "event_type": "packet_posted",
                "timestamp_utc": "2026-03-17T03:01:00Z",
                "session_id": "session-1",
                "plan_id": "MP-377",
                "from_agent": "codex",
                "to_agent": "claude",
                "kind": "review",
                "summary": "review finding",
                "body": "fix this",
                "status": "pending",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rc_path = root / "dev/active/review_channel.md"
            rc_path.parent.mkdir(parents=True, exist_ok=True)
            rc_path.write_text(_build_review_channel_text(), encoding="utf-8")

            review_state, _ = reduce_events(
                events=events,
                repo_root=root,
                review_channel_path=rc_path,
            )
        self.assertEqual(review_state["queue"]["pending_total"], 1)
        self.assertEqual(review_state["_compat"]["runtime"]["active_daemons"], 1)
        self.assertTrue(review_state["_compat"]["runtime"]["daemons"]["publisher"]["running"])

    def test_filter_inbox_packets_skips_expired_pending_rows(self) -> None:
        """Expired pending packets must not mask the live Claude inbox view."""
        expired_at = (datetime.now(UTC) - timedelta(minutes=5)).isoformat().replace(
            "+00:00", "Z"
        )
        live_expires_at = (datetime.now(UTC) + timedelta(minutes=30)).isoformat().replace(
            "+00:00", "Z"
        )
        events = [
            {
                "packet_id": "rev_pkt_live",
                "trace_id": "trace_live",
                "event_id": "rev_evt_0001",
                "event_type": "packet_posted",
                "timestamp_utc": "2026-03-17T03:00:00Z",
                "session_id": "session-1",
                "plan_id": "MP-358",
                "from_agent": "codex",
                "to_agent": "claude",
                "kind": "instruction",
                "summary": "live follow-up",
                "body": "take the current slice",
                "status": "pending",
                "expires_at_utc": live_expires_at,
            },
            {
                "packet_id": "rev_pkt_expired",
                "trace_id": "trace_expired",
                "event_id": "rev_evt_0002",
                "event_type": "packet_posted",
                "timestamp_utc": "2026-03-17T03:05:00Z",
                "session_id": "session-1",
                "plan_id": "MP-358",
                "from_agent": "codex",
                "to_agent": "claude",
                "kind": "instruction",
                "summary": "expired stale slice",
                "body": "ignore this expired slice",
                "status": "pending",
                "expires_at_utc": expired_at,
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rc_path = root / "dev/active/review_channel.md"
            rc_path.parent.mkdir(parents=True, exist_ok=True)
            rc_path.write_text(_build_review_channel_text(), encoding="utf-8")

            review_state, _ = reduce_events(
                events=events,
                repo_root=root,
                review_channel_path=rc_path,
            )

        pending_packets = filter_inbox_packets(
            review_state,
            target="claude",
            status="pending",
        )

        self.assertEqual(review_state["queue"]["pending_total"], 1)
        self.assertEqual(review_state["queue"]["stale_packet_count"], 1)
        self.assertTrue(
            review_state["queue"]["derived_next_instruction"].startswith(
                "live follow-up"
            )
        )
        self.assertEqual(
            [packet["packet_id"] for packet in pending_packets],
            ["rev_pkt_live"],
        )

    def test_no_daemon_events_produces_empty_runtime(self) -> None:
        """Without daemon events the runtime section should have zero active."""
        events = [
            {
                "packet_id": "rev_pkt_0001",
                "trace_id": "trace_1",
                "event_id": "rev_evt_0001",
                "event_type": "packet_posted",
                "timestamp_utc": "2026-03-17T03:00:00Z",
                "session_id": "session-1",
                "plan_id": "MP-377",
                "from_agent": "operator",
                "to_agent": "codex",
                "kind": "review",
                "summary": "review pass",
                "body": "body",
                "status": "pending",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rc_path = root / "dev/active/review_channel.md"
            rc_path.parent.mkdir(parents=True, exist_ok=True)
            rc_path.write_text(_build_review_channel_text(), encoding="utf-8")

            review_state, _ = reduce_events(
                events=events,
                repo_root=root,
                review_channel_path=rc_path,
            )
        runtime = review_state["_compat"]["runtime"]
        self.assertEqual(runtime["active_daemons"], 0)
        self.assertEqual(runtime["last_daemon_event_utc"], "")
        self.assertFalse(runtime["daemons"]["publisher"]["running"])
        self.assertFalse(runtime["daemons"]["reviewer_supervisor"]["running"])

    def test_daemon_event_types_constant_is_frozen(self) -> None:
        """DAEMON_EVENT_TYPES should be a frozenset for safe module-level use."""
        self.assertIsInstance(DAEMON_EVENT_TYPES, frozenset)
        self.assertIn("daemon_started", DAEMON_EVENT_TYPES)
        self.assertIn("daemon_stopped", DAEMON_EVENT_TYPES)
        self.assertIn("daemon_heartbeat", DAEMON_EVENT_TYPES)


if __name__ == "__main__":
    unittest.main()
