"""Focused regressions for prepared launch-authority continuity."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.review_channel.launch_authority import (
    assess_prepared_launch_authority,
)


def _gov(mode: str) -> SimpleNamespace:
    return SimpleNamespace(
        bridge_config=SimpleNamespace(operator_interaction_mode=mode)
    )


class AssessPreparedLaunchAuthorityTests(unittest.TestCase):
    def test_head_drift_downgrades_to_refresh_recommended_with_typed_remote_control(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            review_state_path = repo_root / "review_state.json"
            review_state_path.write_text(
                json.dumps(
                    {
                        "review": {"session_id": "markdown-bridge"},
                        "bridge": {"reviewer_mode": "active_dual_agent"},
                        "reviewer_runtime": {
                            "remote_control_attachment": {
                                "provider": "claude",
                                "session_name": "claude-remote-control",
                                "status": "attached",
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"DEVCTL_OPERATOR_INTERACTION_MODE": ""},
                ),
                patch(
                    "dev.scripts.devctl.review_channel.launch_authority.current_head_sha",
                    return_value="head-current",
                ),
                patch(
                    "dev.scripts.devctl.runtime.governance_scan.scan_repo_governance_safely",
                    return_value=_gov("local_terminal"),
                ),
            ):
                result = assess_prepared_launch_authority(
                    repo_root=repo_root,
                    workspace_root=None,
                    review_state_path=review_state_path,
                    prepared_head_sha="head-before-commit",
                    prepared_instruction_revision="",
                    prepared_session_token="",
                )

        self.assertEqual(result.state, "refresh_recommended")
        self.assertIn("remote_control mode", result.reason)

    def test_head_drift_stays_stale_without_remote_control_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            review_state_path = repo_root / "review_state.json"
            review_state_path.write_text(
                json.dumps(
                    {
                        "review": {"session_id": "markdown-bridge"},
                        "bridge": {"reviewer_mode": "active_dual_agent"},
                    }
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"DEVCTL_OPERATOR_INTERACTION_MODE": ""},
                ),
                patch(
                    "dev.scripts.devctl.review_channel.launch_authority.current_head_sha",
                    return_value="head-current",
                ),
                patch(
                    "dev.scripts.devctl.runtime.governance_scan.scan_repo_governance_safely",
                    return_value=_gov("local_terminal"),
                ),
            ):
                result = assess_prepared_launch_authority(
                    repo_root=repo_root,
                    workspace_root=None,
                    review_state_path=review_state_path,
                    prepared_head_sha="head-before-commit",
                    prepared_instruction_revision="",
                    prepared_session_token="",
                )

        self.assertEqual(result.state, "stale")
        self.assertIn("no longer matches", result.reason)

    def test_head_drift_env_override_takes_precedence_over_typed_remote_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            review_state_path = repo_root / "review_state.json"
            review_state_path.write_text(
                json.dumps(
                    {
                        "review": {"session_id": "markdown-bridge"},
                        "bridge": {"reviewer_mode": "active_dual_agent"},
                        "reviewer_runtime": {
                            "remote_control_attachment": {
                                "provider": "claude",
                                "session_name": "claude-remote-control",
                                "status": "attached",
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            with (
                patch.dict(
                    "os.environ",
                    {"DEVCTL_OPERATOR_INTERACTION_MODE": "local_terminal"},
                ),
                patch(
                    "dev.scripts.devctl.review_channel.launch_authority.current_head_sha",
                    return_value="head-current",
                ),
                patch(
                    "dev.scripts.devctl.runtime.governance_scan.scan_repo_governance_safely",
                    return_value=_gov("remote_control"),
                ),
            ):
                result = assess_prepared_launch_authority(
                    repo_root=repo_root,
                    workspace_root=None,
                    review_state_path=review_state_path,
                    prepared_head_sha="head-before-commit",
                    prepared_instruction_revision="",
                    prepared_session_token="",
                )

        self.assertEqual(result.state, "stale")


if __name__ == "__main__":
    unittest.main()
