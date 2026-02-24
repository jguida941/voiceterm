"""Unit tests for mutation Ralph loop core helpers."""

from __future__ import annotations

import importlib.util
import sys
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.config import REPO_ROOT

SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/mutation_ralph_loop_core.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "mutation_ralph_loop_core_script", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load mutation_ralph_loop_core.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
            patch.object(self.script, "download_run_artifacts", return_value=None),
            patch.object(
                self.script,
                "aggregate_outcomes",
                return_value=(
                    {
                        "score": 0.62,
                        "counts": {"caught": 10, "missed": 6, "timeout": 0, "unviable": 0, "other": 0},
                        "hotspots": [{"path": "src/foo.rs", "survivors": 4}],
                        "freshness": [],
                    },
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
            patch.object(self.script, "download_run_artifacts", return_value=None),
            patch.object(
                self.script,
                "aggregate_outcomes",
                return_value=(
                    {
                        "score": 0.50,
                        "counts": {"caught": 5, "missed": 5, "timeout": 0, "unviable": 0, "other": 0},
                        "hotspots": [],
                        "freshness": [],
                    },
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
