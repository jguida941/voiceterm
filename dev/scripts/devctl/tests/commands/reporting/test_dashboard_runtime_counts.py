"""Focused dashboard runtime-count coverage for operator-facing reporting."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.commands import dashboard
from dev.scripts.devctl.commands import dashboard_render


def _write_artifact(root: Path, rel_path: str, payload: object) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _minimal_bridge_text() -> str:
    return "\n".join(
        [
            "# Review Bridge",
            "",
            "## Start-Of-Conversation Rules",
            "",
            "- Last Codex poll: `2026-04-04T03:00:00Z`",
            "- Reviewer mode: `active_dual_agent`",
            "- Last non-audit worktree hash: `" + ("a" * 64) + "`",
            "- Current instruction revision: `rev-123456789abc`",
            "",
            "## Poll Status",
            "",
            "- active reviewer loop",
            "",
            "## Current Verdict",
            "",
            "- accepted",
            "",
            "## Open Findings",
            "",
            "- none",
            "",
            "## Current Instruction For Claude",
            "",
            "- keep the dashboard truthful",
            "",
            "## Claude Status",
            "",
            "- pending",
            "",
            "## Claude Questions",
            "",
            "- none",
            "",
            "## Claude Ack",
            "",
            "- pending",
            "",
            "## Last Reviewed Scope",
            "",
            "- dev/scripts/devctl/commands/dashboard.py",
            "",
        ]
    )


def _minimal_review_state() -> dict[str, object]:
    return {
        "current_session": {
            "current_instruction": "- keep the dashboard truthful",
            "current_instruction_revision": "rev-123456789abc",
            "implementer_status": "- pending",
            "implementer_ack_state": "current",
            "open_findings": "- none",
            "last_reviewed_scope": "- dev/scripts/devctl/commands/dashboard.py",
            "implementer_state_hash": "hash-123",
        },
        "reviewer_runtime": {
            "doctor": {
                "status": "healthy",
                "summary": "all checks passing",
                "blocked_reason": "",
                "publisher_running": True,
                "reviewer_supervisor_running": False,
            },
            "review_acceptance": {
                "current_verdict": "- accepted",
            },
        },
        "attention": {
            "status": "healthy",
            "owner": "reviewer",
            "summary": "all clear",
            "recommended_action": "",
            "recommended_command": "",
        },
        "packets": [],
        "bridge": {
            "reviewer_mode": "active_dual_agent",
            "codex_conductor_active": True,
            "claude_conductor_active": True,
            "active_conductor_providers": ["codex", "claude"],
            "publisher_running": True,
            "reviewer_supervisor_running": False,
        },
        "collaboration": {
            "participants": [
                {
                    "agent_id": "codex",
                    "provider": "codex",
                    "role": "reviewer",
                    "live": True,
                    "planned_lane_count": 8,
                    "requested_worker_budget": 0,
                },
                {
                    "agent_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "live": True,
                    "planned_lane_count": 8,
                    "requested_worker_budget": 0,
                },
            ],
            "delegated_work": [
                {
                    "receipt_id": "receipt_001",
                    "provider": "claude",
                    "role": "implementer",
                    "status": "planned",
                    "live": False,
                }
            ],
        },
    }


class DashboardRuntimeCountTests(unittest.TestCase):
    def test_runtime_counts_flow_into_coordination_and_terminal_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_artifact(
                root,
                "dev/reports/review_channel/state/latest.json",
                _minimal_review_state(),
            )
            bridge = root / "bridge.md"
            bridge.write_text(_minimal_bridge_text(), encoding="utf-8")

            with patch.object(dashboard, "_git_short", return_value={
                "branch": "main",
                "head": "abc",
                "dirty": "CLEAN",
            }), patch.object(dashboard, "_repo_name", return_value="test"):
                snapshot = dashboard.build_snapshot(repo_root=root)

        coord = snapshot["coordination"]
        health_counts = snapshot["health"]["agent_counts"]
        self.assertEqual(coord["active_conductors"], 2)
        self.assertEqual(coord["live_agents"], 2)
        self.assertEqual(coord["live_reviewers"], 1)
        self.assertEqual(coord["live_implementers"], 1)
        self.assertEqual(coord["running_daemons"], 1)
        self.assertEqual(coord["delegated_agents"], 1)
        self.assertEqual(coord["planned_lanes"], 16)
        self.assertEqual(coord["requested_worker_budget"], 0)
        self.assertEqual(health_counts["live_participants_total"], 2)
        self.assertEqual(health_counts["planned_lane_total"], 16)

        terminal = dashboard_render.render_terminal(snapshot, no_color=True)
        self.assertIn("Active agents", terminal)
        self.assertIn("2 live", terminal)
        self.assertIn("Planned / budget", terminal)
