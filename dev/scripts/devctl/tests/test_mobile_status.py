"""Tests for devctl mobile-status parser and command behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import COMMAND_HANDLERS, build_parser
from dev.scripts.devctl.commands import mobile_status


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "phone_json": "dev/reports/autonomy/queue/phone/latest.json",
        "review_channel_path": "dev/active/review_channel.md",
        "bridge_path": "bridge.md",
        "review_status_dir": "dev/reports/review_channel/latest",
        "approval_mode": "balanced",
        "view": "compact",
        "emit_projections": None,
        "format": "json",
        "output": None,
        "json_output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _build_review_channel_text() -> str:
    return "\n".join(
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
    )


def _build_bridge_text() -> str:
    return "\n".join(
        [
            "# Review Bridge",
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
            "- keep the next slice bounded and refresh the status bundle",
            "",
            "## Claude Status",
            "",
            "- implementing the next fix slice",
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
            "- bridge.md",
            "",
        ]
    )


class MobileStatusParserTests(unittest.TestCase):
    def test_cli_accepts_mobile_status_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "mobile-status",
                "--phone-json",
                "/tmp/phone.json",
                "--review-channel-path",
                "/tmp/review_channel.md",
                "--bridge-path",
                "/tmp/bridge.md",
                "--review-status-dir",
                "/tmp/review-status",
                "--view",
                "alert",
                "--approval-mode",
                "trusted",
                "--emit-projections",
                "/tmp/mobile",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "mobile-status")
        self.assertEqual(args.phone_json, "/tmp/phone.json")
        self.assertEqual(args.review_channel_path, "/tmp/review_channel.md")
        self.assertEqual(args.bridge_path, "/tmp/bridge.md")
        self.assertEqual(args.review_status_dir, "/tmp/review-status")
        self.assertEqual(args.approval_mode, "trusted")
        self.assertEqual(args.view, "alert")
        self.assertEqual(args.emit_projections, "/tmp/mobile")
        self.assertEqual(args.format, "json")

    def test_cli_dispatch_uses_mobile_status_handler(self) -> None:
        self.assertIs(COMMAND_HANDLERS["mobile-status"], mobile_status.run)


class MobileStatusCommandTests(unittest.TestCase):
    def test_command_merges_controller_and_review_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            phone_json = root / "phone.json"
            review_channel_path = root / "review_channel.md"
            bridge_path = root / "bridge.md"
            review_status_dir = root / "review-status"
            projection_dir = root / "mobile"
            output_json = root / "report.json"

            phone_json.write_text(
                json.dumps(
                    {
                        "command": "autonomy-phone-status",
                        "phase": "blocked",
                        "reason": "review_follow_up_required",
                        "controller": {
                            "plan_id": "MP-340",
                            "controller_run_id": "run-123",
                            "branch_base": "develop",
                            "mode_effective": "report-only",
                            "resolved": False,
                            "rounds_completed": 2,
                            "max_rounds": 6,
                            "tasks_completed": 3,
                            "max_tasks": 9,
                            "latest_working_branch": "feature/mobile-status",
                        },
                        "loop": {
                            "unresolved_count": 3,
                            "risk": "high",
                            "next_actions": [
                                "Refresh review-channel status",
                                "Send a bounded fix slice",
                            ],
                        },
                        "terminal": {
                            "trace": ["round=1", "round=2"],
                            "draft_text": "candidate patch",
                            "auto_send": False,
                        },
                        "source_run": {
                            "run_id": 99,
                            "run_sha": "deadbeef",
                            "run_url": "https://example.invalid/runs/99",
                        },
                        "warnings": [],
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")

            args = make_args(
                phone_json=str(phone_json),
                review_channel_path=str(review_channel_path),
                bridge_path=str(bridge_path),
                review_status_dir=str(review_status_dir),
                view="alert",
                emit_projections=str(projection_dir),
                output=str(output_json),
            )
            rc = mobile_status.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["approval_mode"], "balanced")
            self.assertIn("control_state", json.loads((projection_dir / "full.json").read_text(encoding="utf-8")))
            self.assertEqual(
                payload["view_payload"]["approval_mode"],
                "balanced",
            )
            self.assertEqual(payload["view"], "alert")
            self.assertEqual(payload["view_payload"]["severity"], "critical")
            self.assertIn("review bridge is", payload["view_payload"]["why"][0])
            self.assertIn("review_projection_files", payload)
            self.assertTrue(
                Path(payload["review_projection_files"]["full_path"]).exists()
            )
            projection_files = payload.get("projection_files", {})
            for key in (
                "full_json",
                "compact_json",
                "alert_json",
                "actions_json",
                "latest_md",
            ):
                self.assertIn(key, projection_files)
                self.assertTrue(Path(projection_files[key]).exists())

    def test_command_uses_review_only_live_data_when_phone_input_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            review_channel_path = root / "review_channel.md"
            bridge_path = root / "bridge.md"
            review_status_dir = root / "review-status"
            projection_dir = root / "mobile"
            output_json = root / "report.json"
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            args = make_args(
                phone_json=str(root / "missing.json"),
                review_channel_path=str(review_channel_path),
                bridge_path=str(bridge_path),
                review_status_dir=str(review_status_dir),
                emit_projections=str(projection_dir),
                output=str(output_json),
            )
            rc = mobile_status.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["approval_mode"], "balanced")
            compact_payload = json.loads(
                (projection_dir / "compact.json").read_text(encoding="utf-8")
            )
            self.assertEqual(compact_payload["review_bridge_state"], "runtime_missing")
            self.assertTrue(
                any(
                    "phone status artifact not found" in row
                    for row in payload.get("warnings", [])
                )
            )
            self.assertEqual(payload["view_payload"]["codex_status"], "inactive")
            self.assertTrue(Path(payload["projection_files"]["full_json"]).exists())

    def test_command_reuses_existing_review_projection_without_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            review_channel_path = root / "review_channel.md"
            bridge_path = root / "bridge.md"
            review_status_dir = root / "review-status"
            output_json = root / "report.json"
            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            review_status_dir.mkdir(parents=True)
            (review_status_dir / "full.json").write_text(
                json.dumps(
                    {
                        "review_state": {
                            "review": {"plan_id": "MP-355"},
                            "queue": {"pending_total": 1},
                            "bridge": {
                                "last_codex_poll_utc": "2026-03-09T04:12:49Z",
                                "last_worktree_hash": "abc123",
                                "current_instruction": "keep the next slice bounded",
                                "open_findings": "- bridge needs rollover-safe handoff",
                                "claude_status": "- implementing the next fix slice",
                                "claude_ack": "- acknowledged",
                            },
                            "agents": [
                                {"agent_id": "codex", "status": "stale", "role": "reviewer"},
                                {"agent_id": "claude", "status": "active", "role": "implementer"},
                            ],
                        },
                        "bridge_liveness": {
                            "overall_state": "stale",
                            "codex_poll_state": "stale",
                            "reviewer_freshness": "overdue",
                        },
                    }
                ),
                encoding="utf-8",
            )

            args = make_args(
                phone_json=str(root / "missing.json"),
                review_channel_path=str(review_channel_path),
                bridge_path=str(bridge_path),
                review_status_dir=str(review_status_dir),
                output=str(output_json),
            )
            fake_model = SimpleNamespace(
                resolved_phase="reviewing",
                top_blocker="await_review",
                next_action="review_follow_up_required",
                next_command="python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
                push_eligible=False,
                review_accepted=False,
                reviewer_mode="active_dual_agent",
                operator_interaction_mode="remote_control",
                last_guard_ok=True,
                pending_action_requests=1,
            )

            with (
                patch(
                    "dev.scripts.devctl.commands.mobile_status.build_control_plane_read_model",
                    return_value=fake_model,
                ),
                patch(
                    "dev.scripts.devctl.review_channel.state.refresh_status_snapshot",
                    side_effect=AssertionError("should not refresh review-channel state"),
                ),
            ):
                rc = mobile_status.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["view_payload"]["codex_status"], "stale")
            self.assertTrue(
                payload["review_projection_files"]["full_path"].endswith("full.json")
            )

    def test_command_uses_existing_typed_review_state_without_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            review_channel_path = root / "review_channel.md"
            bridge_path = root / "bridge.md"
            review_status_dir = root / "review-status"
            output_json = root / "report.json"

            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            review_status_dir.mkdir(parents=True)
            (review_status_dir / "review_state.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "contract_id": "ReviewState",
                        "command": "review-channel",
                        "action": "status",
                        "timestamp": "2026-03-09T04:12:49Z",
                        "ok": False,
                        "review": {"plan_id": "MP-355"},
                        "queue": {"pending_total": 1},
                        "bridge": {
                            "overall_state": "stale",
                            "codex_poll_state": "stale",
                            "reviewer_freshness": "overdue",
                            "last_codex_poll_utc": "2026-03-09T04:12:49Z",
                            "last_worktree_hash": "abc123",
                            "current_instruction": "keep the next slice bounded",
                            "open_findings": "- bridge needs rollover-safe handoff",
                            "claude_status": "- implementing the next fix slice",
                            "claude_ack": "- acknowledged",
                        },
                        "registry": {
                            "timestamp": "2026-03-09T04:12:49Z",
                            "agents": [
                                {
                                    "agent_id": "codex",
                                    "job_state": "stale",
                                    "current_job": "reviewer",
                                },
                                {
                                    "agent_id": "claude",
                                    "job_state": "active",
                                    "current_job": "implementer",
                                },
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            args = make_args(
                phone_json=str(root / "missing.json"),
                review_channel_path=str(review_channel_path),
                bridge_path=str(bridge_path),
                review_status_dir=str(review_status_dir),
                output=str(output_json),
                repo_root=str(root),
            )
            fake_model = SimpleNamespace(
                resolved_phase="reviewing",
                top_blocker="await_review",
                next_action="review_follow_up_required",
                next_command="python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
                push_eligible=False,
                review_accepted=False,
                reviewer_mode="active_dual_agent",
                operator_interaction_mode="remote_control",
                last_guard_ok=True,
                pending_action_requests=1,
            )

            with (
                patch(
                    "dev.scripts.devctl.commands.mobile_status.build_control_plane_read_model",
                    return_value=fake_model,
                ),
                patch(
                    "dev.scripts.devctl.review_channel.state.refresh_status_snapshot",
                    side_effect=AssertionError("should not refresh review-channel state"),
                ),
            ):
                rc = mobile_status.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["view_payload"]["codex_status"], "stale")
            self.assertTrue(
                payload["review_projection_files"]["review_state_path"].endswith("review_state.json")
            )

    def test_command_prefers_existing_projection_over_event_artifacts_in_auto_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            review_channel_path = root / "review_channel.md"
            bridge_path = root / "bridge.md"
            review_status_dir = root / "review-status"
            output_json = root / "report.json"

            review_channel_path.write_text(
                _build_review_channel_text(),
                encoding="utf-8",
            )
            bridge_path.write_text(_build_bridge_text(), encoding="utf-8")
            args = make_args(
                phone_json=str(root / "missing.json"),
                review_channel_path=str(review_channel_path),
                bridge_path=str(bridge_path),
                review_status_dir=str(review_status_dir),
                output=str(output_json),
            )

            with patch(
                "dev.scripts.devctl.review_channel.events.event_state_exists",
                return_value=True,
            ):
                rc = mobile_status.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["view_payload"]["codex_status"], "inactive")
            self.assertTrue(
                payload["review_projection_files"]["full_path"].endswith("full.json")
            )

    def test_command_fails_when_all_live_inputs_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            output_json = root / "report.json"
            args = make_args(
                phone_json=str(root / "missing.json"),
                review_channel_path=str(root / "missing_review_channel.md"),
                bridge_path=str(root / "missing_bridge.md"),
                review_status_dir=str(root / "missing-review-status"),
                repo_root=str(root),
                output=str(output_json),
            )
            rc = mobile_status.run(args)

            self.assertEqual(rc, 1)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertFalse(payload["ok"])
            self.assertTrue(
                any(
                    "no live mobile data sources were available" in row
                    for row in payload.get("errors", [])
                )
            )


if __name__ == "__main__":
    unittest.main()
