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


def _lane(agent_id: str, provider: str, lane: str, *, role: str | None = None) -> LaneAssignment:
    return LaneAssignment(
        agent_id=agent_id,
        provider=provider,
        role=role or "",
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

    def test_build_conductor_launch_specs_respects_explicit_lane_roles(self) -> None:
        specs = build_conductor_launch_specs(
            provider_lane_map={
                "claude": (
                    _lane(
                        "AGENT-1",
                        "claude",
                        "Claude architecture contract review",
                        role="reviewer",
                    ),
                ),
                "codex": (
                    _lane(
                        "AGENT-9",
                        "codex",
                        "Codex bridge fixes",
                        role="implementer",
                    ),
                ),
            },
            requested_worker_budgets={"claude": 0, "codex": 1},
        )

        self.assertEqual([spec.provider for spec in specs], ["claude", "codex"])
        self.assertEqual(specs[0].role, "reviewer")
        self.assertEqual(specs[0].counterpart_provider, "codex")
        self.assertEqual(specs[1].role, "implementer")
        self.assertEqual(specs[1].counterpart_provider, "claude")
        self.assertEqual(specs[1].requested_worker_budget, 1)

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

    def test_build_launch_sessions_records_workspace_root_and_passes_it_to_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
            bridge_path = root / "bridge.md"
            bridge_path.write_text("# Bridge\n", encoding="utf-8")
            status_dir = root / "dev/reports/review_channel/latest"
            worker_root = (root / "../wt-agent-1").resolve()
            prompt_calls: list[dict[str, object]] = []

            def _prompt(**kwargs) -> str:
                prompt_calls.append(kwargs)
                return "prompt"

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
                    },
                    requested_worker_budgets={"codex": 0},
                    rollover_threshold_pct=20,
                    await_ack_seconds=180,
                    retirement_note="bridge-gated",
                    promotion_plan_rel="dev/active/review_channel.md",
                    session_output_root=status_dir,
                ),
                build_conductor_prompt_fn=_prompt,
                resolve_cli_path_fn=lambda provider: provider,
            )

            self.assertEqual(prompt_calls[0]["workspace_root"], worker_root)
            metadata = json.loads(
                Path(str(sessions[0]["metadata_path"])).read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["workspace_root"], str(worker_root))
            self.assertEqual(sessions[0]["workspace_root"], str(worker_root))
            script_text = Path(str(sessions[0]["script_path"])).read_text(encoding="utf-8")
            self.assertIn(
                f"REVIEW_CHANNEL_WORKSPACE_ROOT={worker_root}",
                script_text,
            )

    def test_build_launch_sessions_preserves_swapped_role_metadata(self) -> None:
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
                    codex_workers=1,
                    claude_workers=0,
                    provider_lane_map={
                        "claude": [
                            _lane(
                                "AGENT-1",
                                "claude",
                                "Claude reviewer",
                                role="reviewer",
                            )
                        ],
                        "codex": [
                            _lane(
                                "AGENT-9",
                                "codex",
                                "Codex coding",
                                role="implementer",
                            )
                        ],
                    },
                    requested_worker_budgets={"claude": 0, "codex": 1},
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
                [(session["provider"], session["role"]) for session in sessions],
                [("claude", "reviewer"), ("codex", "implementer")],
            )

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

    def test_build_launch_sessions_fails_closed_on_provider_worktree_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
            bridge_path = root / "bridge.md"
            bridge_path.write_text("# Bridge\n", encoding="utf-8")

            lane_a = _lane("AGENT-1", "codex", "Codex review")
            lane_b = _lane("AGENT-2", "codex", "Codex review")

            with self.assertRaisesRegex(ValueError, "multiple worktrees"):
                build_launch_sessions(
                    request=LaunchSessionRequest(
                        repo_root=root,
                        review_channel_path=review_channel_path,
                        bridge_path=bridge_path,
                        codex_lanes=[],
                        claude_lanes=[],
                        codex_workers=0,
                        claude_workers=0,
                        provider_lane_map={"codex": [lane_a, lane_b]},
                        requested_worker_budgets={"codex": 0},
                        rollover_threshold_pct=20,
                        await_ack_seconds=180,
                        retirement_note="bridge-gated",
                        promotion_plan_rel="dev/active/review_channel.md",
                    ),
                    build_conductor_prompt_fn=lambda **_: "prompt",
                    resolve_cli_path_fn=lambda provider: provider,
                )


if __name__ == "__main__":
    unittest.main()
