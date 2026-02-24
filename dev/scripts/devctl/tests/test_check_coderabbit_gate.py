"""Unit tests for CodeRabbit release gate script behavior."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_coderabbit_gate.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("check_coderabbit_gate_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_coderabbit_gate.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckCodeRabbitGateTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()
        cls.sha = "a" * 40

    def _args(self, **overrides):
        payload = {
            "workflow": self.script.DEFAULT_WORKFLOW,
            "repo": "owner/repo",
            "sha": self.sha,
            "branch": "master",
            "limit": 50,
            "require_conclusion": "success",
        }
        payload.update(overrides)
        return SimpleNamespace(**payload)

    def test_branch_filter_falls_back_to_commit_only_when_no_runs(self) -> None:
        calls: list[list[str]] = []
        run_payload = [
            {
                "status": "completed",
                "conclusion": "success",
                "headSha": self.sha,
                "url": "https://example.invalid/run/1",
                "createdAt": "2026-02-23T20:00:00Z",
            }
        ]

        def fake_run_capture(cmd: list[str]):
            calls.append(cmd)
            if len(calls) == 1:
                return 0, "[]", ""
            if len(calls) == 2:
                return 0, json.dumps(run_payload), ""
            raise AssertionError(f"unexpected command: {cmd}")

        with patch.object(self.script, "_run_capture", side_effect=fake_run_capture):
            report = self.script._build_report(self._args(branch="master"))

        self.assertTrue(report["ok"])
        self.assertTrue(report["fallback_without_branch"])
        self.assertEqual(len(calls), 2)
        self.assertIn("--commit", calls[0])
        self.assertIn(self.sha, calls[0])
        self.assertIn("--branch", calls[0])
        self.assertNotIn("--branch", calls[1])

    def test_sha_like_branch_argument_is_ignored(self) -> None:
        calls: list[list[str]] = []
        run_payload = [
            {
                "status": "completed",
                "conclusion": "success",
                "headSha": self.sha,
                "url": "https://example.invalid/run/2",
                "createdAt": "2026-02-23T20:05:00Z",
            }
        ]

        def fake_run_capture(cmd: list[str]):
            calls.append(cmd)
            return 0, json.dumps(run_payload), ""

        with patch.object(self.script, "_run_capture", side_effect=fake_run_capture):
            report = self.script._build_report(self._args(branch=self.sha))

        self.assertTrue(report["ok"])
        self.assertEqual(len(calls), 1)
        self.assertNotIn("--branch", calls[0])
        warnings = report.get("warnings") or []
        self.assertTrue(any("branch argument resembles a commit SHA" in warning for warning in warnings))

    def test_missing_local_branch_hint_is_non_fatal(self) -> None:
        calls: list[list[str]] = []
        run_payload = [
            {
                "status": "completed",
                "conclusion": "success",
                "headSha": self.sha,
                "url": "https://example.invalid/run/3",
                "createdAt": "2026-02-23T20:10:00Z",
            }
        ]

        def fake_run_capture(cmd: list[str]):
            calls.append(cmd)
            if cmd[:4] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
                return 1, "", "detached head"
            if cmd[:3] == ["git", "branch", "--contains"]:
                return 1, "", "no branch contains sha"
            if cmd[:3] == ["gh", "run", "list"]:
                return 0, json.dumps(run_payload), ""
            raise AssertionError(f"unexpected command: {cmd}")

        with patch.object(self.script, "_run_capture", side_effect=fake_run_capture):
            report = self.script._build_report(self._args(branch=""))

        self.assertTrue(report["ok"])
        warnings = report.get("warnings") or []
        self.assertTrue(any("branch auto-detect skipped" in warning for warning in warnings))
        self.assertEqual(calls[-1][:3], ["gh", "run", "list"])

    def test_missing_workflow_on_other_branch_is_non_blocking_when_defined_locally(self) -> None:
        def fake_run_capture(cmd: list[str]):
            if cmd[:3] == ["gh", "run", "list"]:
                return 1, "", "could not find any workflows named CodeRabbit Triage Bridge"
            if cmd[:4] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
                return 0, "develop\n", ""
            raise AssertionError(f"unexpected command: {cmd}")

        with (
            patch.object(self.script, "_run_capture", side_effect=fake_run_capture),
            patch.object(self.script, "_local_workflow_exists_by_name", return_value=True),
        ):
            report = self.script._build_report(self._args(branch="master"))

        self.assertTrue(report["ok"])
        self.assertEqual(report["reason"], "workflow_not_present_on_target_branch_yet")
        warnings = report.get("warnings") or []
        self.assertTrue(any("treated as non-blocking" in warning for warning in warnings))

    def test_missing_workflow_on_target_branch_still_fails(self) -> None:
        def fake_run_capture(cmd: list[str]):
            if cmd[:3] == ["gh", "run", "list"]:
                return 1, "", "could not find any workflows named CodeRabbit Triage Bridge"
            if cmd[:4] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
                return 0, "master\n", ""
            raise AssertionError(f"unexpected command: {cmd}")

        with (
            patch.object(self.script, "_run_capture", side_effect=fake_run_capture),
            patch.object(self.script, "_local_workflow_exists_by_name", return_value=True),
        ):
            report = self.script._build_report(self._args(branch="master"))

        self.assertFalse(report["ok"])
        self.assertIn("gh_run_list_failed", report["reason"])

    def test_connectivity_error_is_non_blocking_outside_ci(self) -> None:
        def fake_run_capture(cmd: list[str]):
            if cmd[:3] == ["gh", "run", "list"]:
                return 1, "", "error connecting to api.github.com"
            if cmd[:4] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
                return 0, "develop\n", ""
            raise AssertionError(f"unexpected command: {cmd}")

        with (
            patch.object(self.script, "_run_capture", side_effect=fake_run_capture),
            patch.dict("os.environ", {"CI": ""}, clear=False),
        ):
            report = self.script._build_report(self._args(branch="master"))

        self.assertTrue(report["ok"])
        self.assertEqual(report["reason"], "gh_unreachable_local_non_blocking")
        warnings = report.get("warnings") or []
        self.assertTrue(any("non-blocking" in warning for warning in warnings))

    def test_connectivity_error_still_fails_in_ci(self) -> None:
        def fake_run_capture(cmd: list[str]):
            if cmd[:3] == ["gh", "run", "list"]:
                return 1, "", "error connecting to api.github.com"
            if cmd[:4] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
                return 0, "develop\n", ""
            raise AssertionError(f"unexpected command: {cmd}")

        with (
            patch.object(self.script, "_run_capture", side_effect=fake_run_capture),
            patch.dict("os.environ", {"CI": "true"}, clear=False),
        ):
            report = self.script._build_report(self._args(branch="master"))

        self.assertFalse(report["ok"])
        self.assertIn("gh_run_list_failed", report["reason"])
