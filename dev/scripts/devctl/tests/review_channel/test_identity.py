"""Tests for portable review-channel identity helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.review_channel.core import (
    project_id_for_repo,
)
from dev.scripts.devctl.review_channel.daemon_events import (
    DaemonEventContext,
    DaemonLifecycleEventRequest,
    append_daemon_lifecycle_event,
)
from dev.scripts.devctl.review_channel.event_store import ReviewChannelArtifactPaths
from dev.scripts.devctl.review_channel.service_identity import (
    build_service_identity,
    repo_identity_for_repo,
)


def _git_remote_result(remote: str) -> SimpleNamespace:
    return SimpleNamespace(returncode=0, stdout=f"{remote}\n", stderr="")


class ReviewChannelIdentityTests(TestCase):
    def test_repo_identity_seed_is_stable_across_checkout_paths(self) -> None:
        remote = "git@github.com:jguida941/codex-voice.git"
        with patch(
            "dev.scripts.devctl.review_channel.service_identity.subprocess.run",
            return_value=_git_remote_result(remote),
        ):
            first_seed = repo_identity_for_repo(Path("/tmp/codex-voice-a"))
            second_seed = repo_identity_for_repo(Path("/opt/codex-voice-b"))
            first_project_id = project_id_for_repo(Path("/tmp/codex-voice-a"))
            second_project_id = project_id_for_repo(Path("/opt/codex-voice-b"))

        self.assertEqual(first_seed, "github.com/jguida941/codex-voice")
        self.assertEqual(first_seed, second_seed)
        self.assertEqual(first_project_id, second_project_id)
        self.assertTrue(first_project_id.startswith("sha256:"))

    def test_service_identity_uses_shared_stable_project_id(self) -> None:
        remote = "https://github.com/jguida941/codex-voice.git"
        with patch(
            "dev.scripts.devctl.review_channel.service_identity.subprocess.run",
            return_value=_git_remote_result(remote),
        ):
            identity = build_service_identity(
                repo_root=Path("/tmp/codex-voice-a"),
                bridge_path=Path("/tmp/codex-voice-a/bridge.md"),
                review_channel_path=Path("/tmp/codex-voice-a/dev/active/review_channel.md"),
                output_root=Path("/tmp/codex-voice-a/dev/reports/review_channel/latest"),
            )
            expected_project_id = project_id_for_repo(Path("/opt/codex-voice-b"))

        self.assertEqual(identity["project_id"], expected_project_id)
        self.assertEqual(
            identity["service_id"], f"review-channel:{expected_project_id}"
        )

    def test_daemon_lifecycle_events_share_the_same_stable_project_id(self) -> None:
        remote = "git@github.com:jguida941/codex-voice.git"
        artifact_paths = ReviewChannelArtifactPaths(
            artifact_root="/tmp/review/artifacts",
            event_log_path="/tmp/review/artifacts/events/trace.ndjson",
            state_path="/tmp/review/state.json",
            projections_root="/tmp/review/projections",
        )
        request = DaemonLifecycleEventRequest(
            event_type="daemon_started",
            reviewer_mode="active_dual_agent",
            timestamp_utc="2026-03-17T00:00:00Z",
        )
        with (
            patch(
                "dev.scripts.devctl.review_channel.service_identity.subprocess.run",
                return_value=_git_remote_result(remote),
            ),
            patch(
                "dev.scripts.devctl.review_channel.daemon_events.load_events",
                return_value=[],
            ),
            patch("dev.scripts.devctl.review_channel.daemon_events.append_event"),
        ):
            first_event = append_daemon_lifecycle_event(
                DaemonEventContext(
                    repo_root=Path("/tmp/codex-voice-a"),
                    artifact_paths=artifact_paths,
                    daemon_kind="publisher",
                    pid=123,
                ),
                request,
            )
            second_event = append_daemon_lifecycle_event(
                DaemonEventContext(
                    repo_root=Path("/opt/codex-voice-b"),
                    artifact_paths=artifact_paths,
                    daemon_kind="publisher",
                    pid=456,
                ),
                request,
            )

        self.assertIsNotNone(first_event)
        self.assertIsNotNone(second_event)
        assert first_event is not None
        assert second_event is not None
        self.assertEqual(first_event["project_id"], second_event["project_id"])
        self.assertTrue(first_event["project_id"].startswith("sha256:"))
    def test_no_remote_fallback_is_collision_resistant(self) -> None:
        """Two repos with the same basename but different parents get distinct IDs."""
        no_remote = SimpleNamespace(returncode=1, stdout="", stderr="")
        with patch(
            "dev.scripts.devctl.review_channel.service_identity.subprocess.run",
            return_value=no_remote,
        ):
            seed_a = repo_identity_for_repo(Path("/home/user/work/myapp"))
            seed_b = repo_identity_for_repo(Path("/home/user/forks/myapp"))

        self.assertTrue(seed_a.startswith("local:"))
        self.assertTrue(seed_b.startswith("local:"))
        self.assertNotEqual(seed_a, seed_b)

    def test_no_remote_fallback_is_stable_for_same_path(self) -> None:
        no_remote = SimpleNamespace(returncode=1, stdout="", stderr="")
        with patch(
            "dev.scripts.devctl.review_channel.service_identity.subprocess.run",
            return_value=no_remote,
        ):
            first = repo_identity_for_repo(Path("/home/user/work/myapp"))
            second = repo_identity_for_repo(Path("/home/user/work/myapp"))

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
