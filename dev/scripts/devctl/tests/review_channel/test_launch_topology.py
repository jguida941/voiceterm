"""Focused launch-topology tests for provider-agnostic conductor rosters."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.review_channel.core import LaneAssignment
from dev.scripts.devctl.review_channel.launch import build_launch_sessions
from dev.scripts.devctl.review_channel.launch_records import LaunchSessionRequest
from dev.scripts.devctl.review_channel.launch_topology import (
    build_conductor_launch_specs,
)


def _lane(agent_id: str, provider: str, lane: str) -> LaneAssignment:
    return LaneAssignment(
        agent_id=agent_id,
        provider=provider,
        lane=lane,
        docs="dev/active/review_channel.md",
        mp_scope="MP-355",
        worktree=f"../wt-{agent_id.lower()}",
        branch=f"feature/{agent_id.lower()}",
    )


class LaunchTopologyTests(unittest.TestCase):
    def test_build_conductor_launch_specs_orders_reviewer_before_implementer(self) -> None:
        specs = build_conductor_launch_specs(
            provider_lane_map={
                "claude": (_lane("AGENT-2", "claude", "Claude coding"),),
                "codex": (_lane("AGENT-1", "codex", "Codex review"),),
            },
            requested_worker_budgets={"codex": 0, "claude": 2},
        )

        self.assertEqual([spec.provider for spec in specs], ["codex", "claude"])
        self.assertEqual(specs[0].role, "reviewer")
        self.assertEqual(specs[1].role, "implementer")
        self.assertEqual(specs[0].counterpart_name, "Claude")
        self.assertEqual(specs[1].requested_worker_budget, 2)

    def test_build_launch_sessions_accepts_provider_lane_map_and_writes_role_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
            bridge_path = root / "bridge.md"
            bridge_path.write_text("# Bridge\n", encoding="utf-8")
            status_dir = root / "dev/reports/review_channel/latest"

            sessions = build_launch_sessions(
                request=LaunchSessionRequest(
                    repo_root=root,
                    review_channel_path=review_channel_path,
                    bridge_path=bridge_path,
                    codex_lanes=[],
                    claude_lanes=[],
                    codex_workers=0,
                    claude_workers=0,
                    provider_lane_map={
                        "codex": [_lane("AGENT-1", "codex", "Codex review")],
                        "claude": [_lane("AGENT-2", "claude", "Claude coding")],
                    },
                    requested_worker_budgets={"codex": 0, "claude": 1},
                    rollover_threshold_pct=20,
                    await_ack_seconds=180,
                    retirement_note="bridge-gated",
                    promotion_plan_rel="dev/active/review_channel.md",
                    session_output_root=status_dir,
                ),
                build_conductor_prompt_fn=lambda **_: "prompt",
                resolve_cli_path_fn=lambda provider: provider,
            )

            self.assertEqual(
                [session["provider"] for session in sessions],
                ["codex", "claude"],
            )
            metadata = json.loads(
                Path(str(sessions[0]["metadata_path"])).read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["provider"], "codex")
            self.assertEqual(metadata["role"], "reviewer")
            self.assertEqual(metadata["planned_lane_count"], 1)
            self.assertIsNone(metadata["terminal_window_id"])
            self.assertIsNone(sessions[0]["terminal_window_id"])

    def test_build_launch_sessions_uses_plan_safe_claude_permission_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
            bridge_path = root / "bridge.md"
            bridge_path.write_text("# Bridge\n", encoding="utf-8")

            sessions = build_launch_sessions(
                request=LaunchSessionRequest(
                    repo_root=root,
                    review_channel_path=review_channel_path,
                    bridge_path=bridge_path,
                    codex_lanes=[],
                    claude_lanes=[],
                    codex_workers=0,
                    claude_workers=0,
                    provider_lane_map={
                        "codex": [_lane("AGENT-1", "codex", "Codex review")],
                        "claude": [_lane("AGENT-2", "claude", "Claude coding")],
                    },
                    requested_worker_budgets={"codex": 0, "claude": 0},
                    rollover_threshold_pct=20,
                    await_ack_seconds=180,
                    retirement_note="bridge-gated",
                    promotion_plan_rel="dev/active/review_channel.md",
                ),
                build_conductor_prompt_fn=lambda **_: "prompt",
                resolve_cli_path_fn=lambda provider: provider,
            )

            scripts_by_provider = {
                str(session["provider"]): Path(str(session["script_path"])).read_text(
                    encoding="utf-8"
                )
                for session in sessions
            }

            self.assertIn("--full-auto", scripts_by_provider["codex"])
            self.assertIn("--permission-mode default", scripts_by_provider["claude"])
            self.assertNotIn("--permission-mode auto", scripts_by_provider["claude"])


if __name__ == "__main__":
    unittest.main()
