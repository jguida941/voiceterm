"""Tests for security Python-scope helper behavior."""

from __future__ import annotations

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.security_python_scope import (
    changed_python_paths,
    resolve_python_scope,
    run_python_core_steps,
)


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "python_scope": "auto",
        "since_ref": None,
        "head_ref": "HEAD",
        "require_optional_tools": False,
        "dry_run": True,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_internal_step(**kwargs):
    step = {
        "name": kwargs["name"],
        "cmd": kwargs["cmd"],
        "returncode": kwargs["returncode"],
        "duration_s": kwargs.get("duration_s", 0.0),
        "skipped": kwargs.get("skipped", False),
    }
    if "error" in kwargs:
        step["error"] = kwargs["error"]
    if "details" in kwargs:
        step["details"] = kwargs["details"]
    return step


def _annotate(step: dict, *, tier: str, blocking: bool) -> dict:
    details = step.get("details", {})
    details["tier"] = tier
    details["blocking"] = blocking
    step["details"] = details
    return step


class SecurityPythonScopeTests(TestCase):
    def test_resolve_python_scope_auto_local_defaults_to_changed(self) -> None:
        with patch("dev.scripts.devctl.security_python_scope.os.environ", {}):
            self.assertEqual(resolve_python_scope(make_args()), "changed")

    def test_resolve_python_scope_auto_in_ci_defaults_to_all(self) -> None:
        with patch(
            "dev.scripts.devctl.security_python_scope.os.environ", {"CI": "true"}
        ):
            self.assertEqual(resolve_python_scope(make_args()), "all")

    @patch("dev.scripts.devctl.security_python_scope.subprocess.run")
    def test_changed_python_paths_all_uses_tracked_files(self, run_mock) -> None:
        run_mock.return_value = SimpleNamespace(
            returncode=0,
            stdout="dev/scripts/devctl/cli.py\ndev/scripts/devctl/collect.py\n",
            stderr="",
        )
        paths, error = changed_python_paths(
            repo_root=".",
            since_ref=None,
            head_ref="HEAD",
            scope="all",
        )
        self.assertIsNone(error)
        self.assertEqual(
            paths,
            ["dev/scripts/devctl/cli.py", "dev/scripts/devctl/collect.py"],
        )

    @patch("dev.scripts.devctl.security_python_scope.changed_python_paths")
    def test_run_python_core_steps_all_scope_uses_ls_files_probe(
        self,
        changed_paths_mock,
    ) -> None:
        changed_paths_mock.return_value = (["dev/scripts/devctl/cli.py"], None)

        def _run_optional_tool_step(**kwargs):
            return (
                {
                    "name": kwargs["name"],
                    "cmd": kwargs["cmd"],
                    "returncode": 0,
                    "duration_s": 0.0,
                    "skipped": kwargs.get("dry_run", False),
                    "details": {"tier": kwargs["tier"], "blocking": kwargs["blocking"]},
                },
                [],
            )

        steps, warnings = run_python_core_steps(
            args=make_args(python_scope="all", dry_run=True),
            repo_root=".",
            env={},
            run_optional_tool_step=_run_optional_tool_step,
            make_internal_step=_make_internal_step,
            annotate_step_metadata=_annotate,
        )

        self.assertEqual(warnings, [])
        self.assertEqual(steps[0]["name"], "python-scope")
        self.assertEqual(steps[0]["cmd"], ["git", "ls-files", "--", "*.py"])
        self.assertEqual(steps[0]["details"]["scope"], "all")
        self.assertEqual(steps[3]["name"], "bandit")
        self.assertEqual(
            steps[3]["cmd"], ["bandit", "-q", "-ll", "-ii", "dev/scripts/devctl/cli.py"]
        )

    @patch("dev.scripts.devctl.security_python_scope.changed_python_paths")
    def test_run_python_core_steps_skips_bandit_when_only_tests_are_selected(
        self,
        changed_paths_mock,
    ) -> None:
        changed_paths_mock.return_value = (
            ["dev/scripts/devctl/tests/test_ship.py"],
            None,
        )

        def _run_optional_tool_step(**kwargs):
            return (
                {
                    "name": kwargs["name"],
                    "cmd": kwargs["cmd"],
                    "returncode": 0,
                    "duration_s": 0.0,
                    "skipped": kwargs.get("dry_run", False),
                    "details": {"tier": kwargs["tier"], "blocking": kwargs["blocking"]},
                },
                [],
            )

        steps, warnings = run_python_core_steps(
            args=make_args(python_scope="changed", dry_run=True),
            repo_root=".",
            env={},
            run_optional_tool_step=_run_optional_tool_step,
            make_internal_step=_make_internal_step,
            annotate_step_metadata=_annotate,
        )

        self.assertEqual(warnings, [])
        self.assertEqual(steps[3]["name"], "bandit")
        self.assertTrue(steps[3]["skipped"])
        self.assertEqual(steps[3]["cmd"], ["bandit", "-q", "-ll", "-ii"])
