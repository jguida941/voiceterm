"""Focused tests for context-packet operational feedback loaders."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from dev.scripts.devctl.context_graph.operational_feedback import (
    data_science_reliability_lines,
    quality_feedback_lines,
    recent_fix_history_lines,
    watchdog_digest_lines,
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


class WatchdogDigestTests(unittest.TestCase):
    @patch("dev.scripts.devctl.context_graph.operational_feedback._load_json_artifact")
    def test_watchdog_digest_prefers_matching_family(self, load_artifact_mock) -> None:
        load_artifact_mock.return_value = {
            "watchdog_stats": {
                "total_episodes": 12,
                "success_rate_pct": 75.0,
                "false_positive_rate_pct": 8.0,
                "guard_families": [
                    {
                        "guard_family": "rust",
                        "episodes": 9,
                        "success_rate_pct": 77.0,
                        "avg_time_to_green_seconds": 12.4,
                    },
                    {
                        "guard_family": "tooling",
                        "episodes": 3,
                        "success_rate_pct": 66.0,
                        "avg_time_to_green_seconds": 4.2,
                    },
                ],
            }
        }

        lines = watchdog_digest_lines(
            trigger="loop-packet",
            query_terms=("tooling",),
        )

        self.assertEqual(
            lines,
            (
                "`watchdog`: 12 episodes, success 75.0%, false positives 8.0%",
                "`tooling`: 3 episodes, success 66.0%, avg green 4.2s",
            ),
        )

    @patch("dev.scripts.devctl.context_graph.operational_feedback._load_json_artifact")
    def test_watchdog_digest_falls_back_for_global_triggers(self, load_artifact_mock) -> None:
        load_artifact_mock.return_value = {
            "watchdog_stats": {
                "total_episodes": 5,
                "success_rate_pct": 40.0,
                "false_positive_rate_pct": 0.0,
                "guard_families": [
                    {
                        "guard_family": "tooling",
                        "episodes": 5,
                        "success_rate_pct": 40.0,
                        "avg_time_to_green_seconds": 3.5,
                    }
                ],
            }
        }

        lines = watchdog_digest_lines(
            trigger="review-channel-bootstrap",
            query_terms=("MP-377",),
        )

        self.assertEqual(
            lines,
            (
                "`watchdog`: 5 episodes, success 40.0%, false positives 0.0%",
                "`tooling`: 5 episodes, success 40.0%, avg green 3.5s",
            ),
        )


class DataScienceReliabilityTests(unittest.TestCase):
    @patch("dev.scripts.devctl.context_graph.operational_feedback._load_json_artifact")
    def test_data_science_reliability_prefers_matching_command(self, load_artifact_mock) -> None:
        load_artifact_mock.return_value = {
            "event_stats": {
                "total_events": 100,
                "success_rate_pct": 88.0,
                "p95_duration_seconds": 22.5,
                "commands": [
                    {
                        "command": "docs-check",
                        "count": 12,
                        "success_rate_pct": 91.0,
                        "avg_duration_seconds": 2.2,
                    },
                    {
                        "command": "review-channel",
                        "count": 8,
                        "success_rate_pct": 70.0,
                        "avg_duration_seconds": 30.0,
                    },
                ],
            }
        }

        lines = data_science_reliability_lines(
            trigger="ralph-backlog",
            query_terms=("review-channel",),
        )

        self.assertEqual(
            lines,
            (
                "`telemetry`: 100 events, success 88.0%, p95 runtime 22.5s",
                "`review-channel`: success 70.0%, avg runtime 30.0s over 8 runs",
            ),
        )

    @patch("dev.scripts.devctl.context_graph.operational_feedback._load_json_artifact")
    def test_data_science_reliability_falls_back_to_low_reliability_command(self, load_artifact_mock) -> None:
        load_artifact_mock.return_value = {
            "event_stats": {
                "total_events": 80,
                "success_rate_pct": 90.0,
                "p95_duration_seconds": 10.0,
                "commands": [
                    {
                        "command": "check",
                        "count": 20,
                        "success_rate_pct": 45.0,
                        "avg_duration_seconds": 12.0,
                    },
                    {
                        "command": "docs-check",
                        "count": 20,
                        "success_rate_pct": 95.0,
                        "avg_duration_seconds": 1.2,
                    },
                ],
            }
        }

        lines = data_science_reliability_lines(
            trigger="swarm-run",
            query_terms=("MP-377",),
        )

        self.assertEqual(
            lines,
            (
                "`telemetry`: 80 events, success 90.0%, p95 runtime 10.0s",
                "`check`: success 45.0%, avg runtime 12.0s over 20 runs",
            ),
        )


if __name__ == "__main__":
    unittest.main()
