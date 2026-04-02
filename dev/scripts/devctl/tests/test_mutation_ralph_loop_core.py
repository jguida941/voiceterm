"""Unit tests for mutation Ralph loop core helpers."""

from __future__ import annotations

import importlib
from unittest import TestCase
from unittest.mock import patch

def _load_script_module():
    return importlib.import_module(
        "dev.scripts.checks.mutation_ralph_loop.core"
    )


class MutationRalphLoopCoreTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def test_execute_loop_report_only_returns_below_threshold_reason(self) -> None:
        with (
            patch.object(
                self.script,
                "wait_for_latest_completed",
                return_value=(
                    {
                        "databaseId": 222,
                        "status": "completed",
                        "conclusion": "success",
                        "headSha": "a" * 40,
                        "url": "https://example.invalid/runs/222",
                    },
                    None,
                ),
            ),
            patch.object(
                self.script,
                "load_attempt_outcome",
                return_value=(
                    {
                        "score": 0.62,
                        "counts": {
                            "caught": 10,
                            "missed": 6,
                            "timeout": 0,
                            "unviable": 0,
                            "other": 0,
                        },
                        "hotspots": [{"path": "src/foo.rs", "survivors": 4}],
                        "freshness": [],
                    },
                    None,
                    None,
                ),
            ),
        ):
            report = self.script.execute_loop(
                repo="owner/repo",
                branch="develop",
                workflow="Mutation Testing",
                mode="report-only",
                max_attempts=1,
                run_list_limit=20,
                poll_seconds=5,
                timeout_seconds=60,
                threshold=0.80,
                fix_command=None,
            )

        self.assertFalse(report["ok"])
        self.assertEqual(report["reason"], "report_only_below_threshold")
        self.assertEqual(report["attempts"][0]["status"], "reported")

    def test_execute_loop_policy_block_sets_reason(self) -> None:
        with (
            patch.object(
                self.script,
                "wait_for_latest_completed",
                return_value=(
                    {
                        "databaseId": 301,
                        "status": "completed",
                        "conclusion": "success",
                        "headSha": "b" * 40,
                        "url": "https://example.invalid/runs/301",
                    },
                    None,
                ),
            ),
            patch.object(
                self.script,
                "load_attempt_outcome",
                return_value=(
                    {
                        "score": 0.50,
                        "counts": {
                            "caught": 5,
                            "missed": 5,
                            "timeout": 0,
                            "unviable": 0,
                            "other": 0,
                        },
                        "hotspots": [],
                        "freshness": [],
                    },
                    None,
                    None,
                ),
            ),
        ):
            report = self.script.execute_loop(
                repo="owner/repo",
                branch="develop",
                workflow="Mutation Testing",
                mode="plan-then-fix",
                max_attempts=1,
                run_list_limit=20,
                poll_seconds=5,
                timeout_seconds=60,
                threshold=0.80,
                fix_command="python3 dev/scripts/devctl.py check --profile ci",
                fix_block_reason="policy denied",
            )

        self.assertFalse(report["ok"])
        self.assertEqual(report["reason"], "fix_command_policy_blocked")
        self.assertEqual(report["attempts"][0]["status"], "blocked")
