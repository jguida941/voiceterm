"""Focused tests for context-packet operational feedback loaders."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from dev.scripts.devctl.context_graph.operational_feedback import (
    quality_feedback_lines,
    recent_fix_history_lines,
)


class RecentFixHistoryTests(unittest.TestCase):
    @patch("dev.scripts.devctl.context_graph.operational_feedback._load_json_artifact")
    def test_recent_fix_history_prefers_matching_file_scope(self, load_artifact_mock) -> None:
        load_artifact_mock.return_value = {
            "recent_findings": [
                {
                    "check_id": "check_other_guard",
                    "verdict": "fixed",
                    "file_path": "dev/scripts/devctl/other.py",
                    "line": 9,
                },
                {
                    "check_id": "check_code_shape",
                    "verdict": "fixed",
                    "file_path": "dev/scripts/devctl/cli.py",
                    "line": 14,
                    "guidance_id": "probe_design_smells@dev/scripts/devctl/cli.py:14",
                    "guidance_followed": True,
                    "prevention_surface": "regression_test",
                },
            ]
        }

        lines = recent_fix_history_lines(
            trigger="ralph-backlog",
            query_terms=("cli.py",),
            canonical_refs=("dev/scripts/devctl/cli.py",),
        )

        self.assertEqual(
            lines,
            (
                "`check_code_shape` fixed at `dev/scripts/devctl/cli.py:14` "
                "[guidance followed | regression_test]",
            ),
        )

    @patch("dev.scripts.devctl.context_graph.operational_feedback._load_json_artifact")
    def test_recent_fix_history_falls_back_for_global_triggers(self, load_artifact_mock) -> None:
        load_artifact_mock.return_value = {
            "recent_findings": [
                {
                    "check_id": "check_first",
                    "verdict": "fixed",
                    "file_path": "dev/scripts/devctl/first.py",
                    "line": 5,
                },
                {
                    "check_id": "check_second",
                    "verdict": "waived",
                    "file_path": "dev/scripts/devctl/second.py",
                    "line": 11,
                },
            ]
        }

        lines = recent_fix_history_lines(
            trigger="swarm-run",
            query_terms=("MP-377",),
            canonical_refs=(),
            limit=2,
        )

        self.assertEqual(
            lines,
            (
                "`check_second` waived at `dev/scripts/devctl/second.py:11`",
                "`check_first` fixed at `dev/scripts/devctl/first.py:5`",
            ),
        )


class QualityFeedbackTests(unittest.TestCase):
    @patch("dev.scripts.devctl.context_graph.operational_feedback._load_json_artifact")
    def test_quality_feedback_prefers_matching_recommendations(self, load_artifact_mock) -> None:
        load_artifact_mock.return_value = {
            "recommendations": [
                {
                    "priority": 2,
                    "check_id": "cleanup_rate",
                    "action": "Close confirmed findings faster",
                    "estimated_impact": "medium",
                },
                {
                    "priority": 1,
                    "check_id": "check_code_shape",
                    "action": "Break up oversize files first",
                    "estimated_impact": "high",
                },
            ]
        }

        lines = quality_feedback_lines(
            trigger="loop-packet",
            query_terms=("code_shape",),
        )

        self.assertEqual(
            lines,
            ("`check_code_shape`: Break up oversize files first (high impact)",),
        )

    @patch("dev.scripts.devctl.context_graph.operational_feedback._load_json_artifact")
    def test_quality_feedback_falls_back_for_global_triggers(self, load_artifact_mock) -> None:
        load_artifact_mock.return_value = {
            "recommendations": [
                {
                    "priority": 3,
                    "check_id": "cleanup_rate",
                    "action": "Close confirmed findings faster",
                    "estimated_impact": "medium",
                },
                {
                    "priority": 1,
                    "check_id": "check_code_shape",
                    "action": "Break up oversize files first",
                    "estimated_impact": "high",
                },
            ]
        }

        lines = quality_feedback_lines(
            trigger="review-channel-bootstrap",
            query_terms=("MP-355",),
            limit=2,
        )

        self.assertEqual(
            lines,
            (
                "`check_code_shape`: Break up oversize files first (high impact)",
                "`cleanup_rate`: Close confirmed findings faster (medium impact)",
            ),
        )


if __name__ == "__main__":
    unittest.main()
