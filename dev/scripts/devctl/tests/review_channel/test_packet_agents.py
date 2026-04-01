"""Packet actor/target validation tests for typed collaboration rosters."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.review_channel.events import post_packet, resolve_artifact_paths
from dev.scripts.devctl.review_channel.packet_contract import PacketPostRequest
from dev.scripts.devctl.review_channel.parser_argument_groups import (
    build_packet_arguments,
)
from dev.scripts.devctl.tests.test_review_channel_context_refs import (
    _review_channel_text,
)


class PacketAgentTests(unittest.TestCase):
    def test_post_packet_accepts_delegated_worker_agent_from_session_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_channel_path = root / "dev/active/review_channel.md"
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
            artifact_paths = resolve_artifact_paths(repo_root=root)
            sessions_dir = Path(artifact_paths.projections_root) / "sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            log_path = sessions_dir / "codex-conductor.log"
            log_path.write_text("live\n", encoding="utf-8")
            (sessions_dir / "codex-conductor.json").write_text(
                json.dumps(
                    {
                        "provider": "codex",
                        "provider_name": "Codex",
                        "session_name": "codex-conductor",
                        "role": "reviewer",
                        "capture_mode": "terminal-script",
                        "approval_mode": "balanced",
                        "planned_lane_count": 1,
                        "requested_worker_budget": 1,
                        "planned_lanes": [
                            {
                                "agent_id": "AGENT-1",
                                "provider": "codex",
                                "lane": "Codex architecture review",
                                "mp_scope": "MP-355",
                                "worktree": "../wt-a1",
                                "branch": "feature/a1",
                            }
                        ],
                        "log_path": str(log_path),
                        "script_path": "",
                    }
                ),
                encoding="utf-8",
            )

            bundle, event = post_packet(
                repo_root=root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketPostRequest(
                    from_agent="codex",
                    to_agent="AGENT-1",
                    kind="question",
                    summary="Need bounded worker follow-up",
                    body="Review the runtime truth projection.",
                ),
            )

            packet = next(
                row
                for row in bundle.review_state["packets"]
                if row["packet_id"] == event["packet_id"]
            )
            self.assertEqual(packet["to_agent"], "AGENT-1")

    def test_packet_arguments_do_not_hardcode_agent_choices(self) -> None:
        arguments = build_packet_arguments(
            lambda *flags, **kwargs: {"flags": flags, **kwargs}
        )
        from_agent = next(
            argument for argument in arguments if argument["flags"] == ("--from-agent",)
        )
        to_agent = next(
            argument for argument in arguments if argument["flags"] == ("--to-agent",)
        )

        self.assertNotIn("choices", from_agent)
        self.assertNotIn("choices", to_agent)


if __name__ == "__main__":
    unittest.main()
