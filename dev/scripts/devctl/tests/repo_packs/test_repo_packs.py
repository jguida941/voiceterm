"""Focused tests for repo-pack review payload helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.repo_packs.review_helpers import MobileReviewStateResult
from dev.scripts.devctl.repo_packs.voiceterm import (
    RepoPathConfig,
    load_review_payload_from_bridge,
)


class VoiceTermReviewPayloadTests(unittest.TestCase):
    def test_load_review_payload_from_bridge_uses_shared_mobile_review_loader(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            config = RepoPathConfig(
                review_channel_rel="custom/review_channel.md",
                bridge_rel="custom/bridge.md",
                review_status_dir_rel="custom/review-status",
            )
            review_channel_path = repo_root / config.review_channel_rel
            bridge_path = repo_root / config.bridge_rel
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            bridge_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
            bridge_path.write_text("# Review Bridge\n", encoding="utf-8")

            result = MobileReviewStateResult(
                review_payload={"review_state": {"bridge": {"reviewer_mode": "active_dual_agent"}}},
                warnings=["fresh cache"],
            )

            with patch(
                "dev.scripts.devctl.repo_packs.review_helpers.load_mobile_review_state",
                return_value=result,
            ) as load_mobile_review_state_mock:
                payload, warnings = load_review_payload_from_bridge(
                    repo_root,
                    path_config=config,
                )

        load_mobile_review_state_mock.assert_called_once_with(
            repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            review_status_dir=repo_root / config.review_status_dir_rel,
            execution_mode="auto",
        )
        self.assertEqual(payload, result.review_payload)
        self.assertEqual(warnings, ("fresh cache",))

    def test_load_review_payload_from_bridge_refreshes_full_projection_when_loader_returns_typed_state(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            config = RepoPathConfig(
                review_channel_rel="custom/review_channel.md",
                bridge_rel="custom/bridge.md",
                review_status_dir_rel="custom/review-status",
            )
            review_channel_path = repo_root / config.review_channel_rel
            bridge_path = repo_root / config.bridge_rel
            status_root = repo_root / config.review_status_dir_rel
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            bridge_path.parent.mkdir(parents=True, exist_ok=True)
            status_root.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
            bridge_path.write_text("# Review Bridge\n", encoding="utf-8")
            full_path = status_root / "full.json"
            full_path.write_text(
                '{"bridge_liveness":{"overall_state":"fresh"},"review_state":{"bridge":{"current_instruction":"Use the full bundle."}}}',
                encoding="utf-8",
            )

            result = MobileReviewStateResult(
                review_payload={"current_session": {"current_instruction": "typed only"}},
                review_full_path=status_root / "review_state.json",
                warnings=["typed cache reused"],
            )

            snapshot = type(
                "Snapshot",
                (),
                {
                    "warnings": ["refreshed full bundle"],
                    "projection_paths": type("Paths", (), {"full_path": str(full_path)})(),
                },
            )()

            with patch(
                "dev.scripts.devctl.repo_packs.review_helpers.load_mobile_review_state",
                return_value=result,
            ) as load_mobile_review_state_mock, patch(
                "dev.scripts.devctl.review_channel.state.refresh_status_snapshot",
                return_value=snapshot,
            ) as refresh_status_snapshot_mock:
                payload, warnings = load_review_payload_from_bridge(
                    repo_root,
                    path_config=config,
                )

        load_mobile_review_state_mock.assert_called_once_with(
            repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            review_status_dir=status_root,
            execution_mode="auto",
        )
        refresh_status_snapshot_mock.assert_called_once_with(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=status_root,
        )
        self.assertEqual(payload["bridge_liveness"]["overall_state"], "fresh")
        self.assertEqual(
            payload["review_state"]["bridge"]["current_instruction"],
            "Use the full bundle.",
        )
        self.assertEqual(warnings, ("typed cache reused", "refreshed full bundle"))


if __name__ == "__main__":
    unittest.main()
