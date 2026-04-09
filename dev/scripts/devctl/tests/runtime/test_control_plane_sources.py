"""Tests for shared control-plane artifact loading."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.runtime.control_plane_sources import load_sources


class ControlPlaneSourcesTests(unittest.TestCase):
    """Verify live review-state loading does not regress to stale fallbacks."""

    def test_load_sources_does_not_fallback_to_stale_review_state_when_live_refresh_is_required(
        self,
    ) -> None:
        repo_root = Path("/tmp/repo")
        review_state_path = repo_root / "custom" / "review_state.json"
        stale_review_state = {"bridge": {"current_instruction": "stale"}}
        fake_paths = {
            "receipt": repo_root / "receipt.json",
            "review_state": review_state_path,
            "push_report": repo_root / "push_report.json",
            "publisher_hb": repo_root / "publisher.json",
            "supervisor_hb": repo_root / "supervisor.json",
            "codex_conductor": repo_root / "codex.json",
            "claude_conductor": repo_root / "claude.json",
            "full_json": repo_root / "full.json",
            "compact_json": repo_root / "compact.json",
        }

        with (
            patch(
                "dev.scripts.devctl.runtime.control_plane_sources.artifact_paths",
                return_value=fake_paths,
            ),
            patch(
                "dev.scripts.devctl.runtime.control_plane_sources.load_conductor_sources",
                return_value={},
            ),
            patch(
                "dev.scripts.devctl.runtime.control_plane_sources.read_json_artifact",
                side_effect=lambda path: stale_review_state if path == review_state_path else None,
            ),
            patch(
                "dev.scripts.devctl.runtime.review_state_locator.load_current_review_state_payload",
                return_value=None,
            ),
            patch(
                "dev.scripts.devctl.runtime.review_state_locator.live_review_state_freshness_paths",
                return_value=(repo_root / "bridge.md", repo_root / "dev/active/review_channel.md"),
            ),
        ):
            sources = load_sources(repo_root)

        self.assertIsNone(sources["review_state"])

    def test_load_sources_keeps_legacy_review_state_fallback_when_no_live_freshness_paths(
        self,
    ) -> None:
        repo_root = Path("/tmp/repo")
        review_state_path = repo_root / "custom" / "review_state.json"
        cached_review_state = {"bridge": {"current_instruction": "cached"}}
        fake_paths = {
            "receipt": repo_root / "receipt.json",
            "review_state": review_state_path,
            "push_report": repo_root / "push_report.json",
            "publisher_hb": repo_root / "publisher.json",
            "supervisor_hb": repo_root / "supervisor.json",
            "codex_conductor": repo_root / "codex.json",
            "claude_conductor": repo_root / "claude.json",
            "full_json": repo_root / "full.json",
            "compact_json": repo_root / "compact.json",
        }

        with (
            patch(
                "dev.scripts.devctl.runtime.control_plane_sources.artifact_paths",
                return_value=fake_paths,
            ),
            patch(
                "dev.scripts.devctl.runtime.control_plane_sources.load_conductor_sources",
                return_value={},
            ),
            patch(
                "dev.scripts.devctl.runtime.control_plane_sources.read_json_artifact",
                side_effect=lambda path: cached_review_state if path == review_state_path else None,
            ),
            patch(
                "dev.scripts.devctl.runtime.review_state_locator.load_current_review_state_payload",
                return_value=None,
            ),
            patch(
                "dev.scripts.devctl.runtime.review_state_locator.live_review_state_freshness_paths",
                return_value=(),
            ),
        ):
            sources = load_sources(repo_root)

        self.assertEqual(sources["review_state"], cached_review_state)
