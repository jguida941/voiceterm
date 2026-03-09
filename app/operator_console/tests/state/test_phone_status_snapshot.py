from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.operator_console.state.phone_status_snapshot import (
    DEFAULT_BRIDGE_REL,
    DEFAULT_MOBILE_STATUS_REL,
    DEFAULT_PHONE_STATUS_REL,
    DEFAULT_REVIEW_CHANNEL_REL,
    load_phone_control_snapshot,
)


class PhoneStatusSnapshotTests(unittest.TestCase):
    def test_load_phone_control_snapshot_returns_unavailable_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot = load_phone_control_snapshot(Path(tmp_dir))

        self.assertFalse(snapshot.available)
        self.assertEqual(snapshot.phase, "offline")
        self.assertIn("no phone-status artifact", snapshot.note or "")

    def test_load_phone_control_snapshot_projects_compact_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            phone_path = repo_root / DEFAULT_PHONE_STATUS_REL
            phone_path.parent.mkdir(parents=True, exist_ok=True)
            phone_path.write_text(
                json.dumps(
                    {
                        "phase": "running",
                        "reason": "round_active",
                        "controller": {
                            "plan_id": "acp-1",
                            "controller_run_id": "run-1",
                            "branch_base": "develop",
                            "mode_effective": "report-only",
                            "resolved": False,
                            "rounds_completed": 2,
                            "max_rounds": 6,
                            "tasks_completed": 5,
                            "max_tasks": 24,
                            "latest_working_branch": "feature/mobile",
                        },
                        "loop": {
                            "unresolved_count": 3,
                            "risk": "medium",
                            "next_actions": ["refresh-status", "dispatch-report-only"],
                        },
                        "terminal": {"trace": [], "draft_text": "draft"},
                        "source_run": {"run_url": "https://example.invalid/run/1"},
                        "warnings": [],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )

            snapshot = load_phone_control_snapshot(repo_root)

        self.assertTrue(snapshot.available)
        self.assertEqual(snapshot.phase, "running")
        self.assertEqual(snapshot.mode_effective, "report-only")
        self.assertEqual(snapshot.unresolved_count, 3)
        self.assertEqual(snapshot.risk, "medium")
        self.assertEqual(snapshot.latest_working_branch, "feature/mobile")
        self.assertEqual(
            snapshot.next_actions,
            ("refresh-status", "dispatch-report-only"),
        )

    def test_load_phone_control_snapshot_prefers_merged_mobile_view(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            phone_path = repo_root / DEFAULT_PHONE_STATUS_REL
            phone_path.parent.mkdir(parents=True, exist_ok=True)
            phone_path.write_text(
                json.dumps(
                    {
                        "phase": "blocked",
                        "reason": "review_follow_up_required",
                        "controller": {
                            "plan_id": "MP-340",
                            "controller_run_id": "run-1",
                            "branch_base": "develop",
                            "mode_effective": "report-only",
                            "resolved": False,
                            "rounds_completed": 1,
                            "max_rounds": 6,
                            "tasks_completed": 2,
                            "max_tasks": 9,
                            "latest_working_branch": "feature/mobile",
                        },
                        "loop": {
                            "unresolved_count": 2,
                            "risk": "high",
                            "next_actions": ["refresh-status"],
                        },
                        "terminal": {"trace": [], "draft_text": "draft"},
                        "source_run": {"run_url": "https://example.invalid/run/1"},
                        "warnings": [],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )
            review_channel_path = repo_root / DEFAULT_REVIEW_CHANNEL_REL
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                "\n".join(
                    [
                        "# Review Channel + Shared Screen Plan",
                        "",
                        "## Transitional Markdown Bridge (Current Operating Mode)",
                        "",
                        "| Agent | Lane | Primary active docs | MP scope | Worktree | Branch |",
                        "|---|---|---|---|---|---|",
                        "| `AGENT-1` | Codex architecture review | `dev/active/review_channel.md` | `MP-340, MP-355` | `../codex-voice-wt-a1` | `feature/a1` |",
                        "| `AGENT-9` | Claude implementation fixes | `dev/active/review_channel.md` | `MP-340, MP-355` | `../codex-voice-wt-a9` | `feature/a9` |",
                    ]
                ),
                encoding="utf-8",
            )
            bridge_path = repo_root / DEFAULT_BRIDGE_REL
            bridge_path.write_text(
                "\n".join(
                    [
                        "# Code Audit Channel",
                        "",
                        "- Last Codex poll: `2026-03-09T04:12:49Z`",
                        "- Last non-audit worktree hash: `fdc8bee2b634384ac5e1affbe030881c838b4a187267c04772494dce5161cca3`",
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
                        "- keep the next slice bounded",
                        "",
                        "## Claude Status",
                        "",
                        "- implementing",
                        "",
                        "## Claude Questions",
                        "",
                        "- none",
                        "",
                        "## Claude Ack",
                        "",
                        "- acknowledged",
                        "",
                        "## Last Reviewed Scope",
                        "",
                        "- code_audit.md",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            snapshot = load_phone_control_snapshot(repo_root)

        self.assertTrue(snapshot.available)
        self.assertEqual(snapshot.review_bridge_state, "stale")
        self.assertEqual(snapshot.current_instruction, "- keep the next slice bounded")
        self.assertEqual(
            snapshot.last_worktree_hash,
            "fdc8bee2b634384ac5e1affbe030881c838b4a187267c04772494dce5161cca3",
        )

    def test_load_phone_control_snapshot_prefers_mobile_projection_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            mobile_projection_path = repo_root / DEFAULT_MOBILE_STATUS_REL
            mobile_projection_path.parent.mkdir(parents=True, exist_ok=True)
            mobile_projection_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "command": "mobile-status",
                        "controller_payload": {
                            "phase": "running",
                            "reason": "round_active",
                            "controller": {
                                "plan_id": "MP-340",
                                "controller_run_id": "run-projection",
                                "branch_base": "develop",
                                "mode_effective": "operate",
                                "resolved": False,
                                "rounds_completed": 3,
                                "max_rounds": 6,
                                "tasks_completed": 4,
                                "max_tasks": 8,
                                "latest_working_branch": "feature/phone-bundle",
                            },
                            "loop": {
                                "unresolved_count": 1,
                                "risk": "medium",
                                "next_actions": ["refresh-mobile-status", "review-status"],
                            },
                            "source_run": {
                                "run_url": "https://example.invalid/run/projection"
                            },
                            "warnings": [],
                            "errors": [],
                        },
                        "review_payload": {
                            "bridge_liveness": {
                                "overall_state": "fresh",
                                "codex_poll_state": "fresh",
                            },
                            "review_state": {
                                "bridge": {
                                    "current_instruction": "Use the emitted bundle first.",
                                    "open_findings": "none",
                                    "last_worktree_hash": "projection-hash",
                                }
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            snapshot = load_phone_control_snapshot(repo_root)

        self.assertTrue(snapshot.available)
        self.assertEqual(snapshot.phase, "running")
        self.assertEqual(snapshot.mode_effective, "operate")
        self.assertEqual(snapshot.review_bridge_state, "fresh")
        self.assertEqual(snapshot.current_instruction, "Use the emitted bundle first.")
        self.assertEqual(snapshot.last_worktree_hash, "projection-hash")
        self.assertEqual(snapshot.next_actions, ("refresh-mobile-status", "review-status"))
        self.assertIn("mobile-status projection bundle", snapshot.note or "")

    def test_load_phone_control_snapshot_falls_back_when_projection_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            mobile_projection_path = repo_root / DEFAULT_MOBILE_STATUS_REL
            mobile_projection_path.parent.mkdir(parents=True, exist_ok=True)
            mobile_projection_path.write_text("{not-json", encoding="utf-8")
            phone_path = repo_root / DEFAULT_PHONE_STATUS_REL
            phone_path.parent.mkdir(parents=True, exist_ok=True)
            phone_path.write_text(
                json.dumps(
                    {
                        "phase": "running",
                        "reason": "round_active",
                        "controller": {
                            "mode_effective": "report-only",
                            "latest_working_branch": "feature/fallback",
                        },
                        "loop": {
                            "unresolved_count": 0,
                            "risk": "low",
                            "next_actions": ["refresh-status"],
                        },
                        "warnings": [],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )

            snapshot = load_phone_control_snapshot(repo_root)

        self.assertTrue(snapshot.available)
        self.assertEqual(snapshot.phase, "running")
        self.assertEqual(snapshot.latest_working_branch, "feature/fallback")
        self.assertIn("projection JSON is invalid", snapshot.note or "")
