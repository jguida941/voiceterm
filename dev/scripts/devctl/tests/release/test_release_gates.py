"""Unit tests for devctl release-gates command."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.commands import release_gates


def _args(**overrides):
    payload = {
        "branch": "master",
        "sha": "a" * 40,
        "repo": None,
        "wait_seconds": 1800,
        "poll_seconds": 20,
        "preflight_workflow": "release_preflight.yml",
        "skip_preflight": False,
        "allow_branch_fallback": False,
        "format": "json",
        "output": None,
        "dry_run": False,
        "pipe_command": None,
        "pipe_args": None,
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


class ReleaseGatesCommandTests(TestCase):
    @staticmethod
    def _step(name: str, returncode: int, *, failure_output: str | None = None) -> dict:
        payload = {
            "name": name,
            "cmd": ["python3", "dev/scripts/checks/check_placeholder.py"],
            "cwd": str(release_gates.REPO_ROOT),
            "returncode": returncode,
            "duration_s": 0.01,
            "skipped": False,
        }
        if failure_output is not None:
            payload["failure_output"] = failure_output
        return payload

    def test_run_executes_all_gates_by_default(self) -> None:
        runs = [
            self._step("coderabbit-gate", 0),
            self._step("release-preflight-gate", 0),
            self._step("coderabbit-ralph-gate", 0),
        ]

        with (
            patch.object(release_gates, "run_cmd", side_effect=runs) as run_mock,
            patch.object(release_gates, "write_output") as write_output_mock,
        ):
            rc = release_gates.run(_args())

        self.assertEqual(rc, 0)
        self.assertEqual(run_mock.call_count, 3)
        call_names = [call.args[0] for call in run_mock.call_args_list]
        self.assertEqual(
            call_names,
            ["coderabbit-gate", "release-preflight-gate", "coderabbit-ralph-gate"],
        )
        first_cmd = run_mock.call_args_list[0].args[1]
        self.assertIn("check_coderabbit_gate.py", " ".join(first_cmd))
        second_cmd = run_mock.call_args_list[1].args[1]
        self.assertIn("--workflow", second_cmd)
        self.assertIn("release_preflight.yml", second_cmd)
        third_cmd = run_mock.call_args_list[2].args[1]
        self.assertIn("check_coderabbit_ralph_gate.py", " ".join(third_cmd))
        written = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(written["ok"])
        self.assertEqual(len(written["steps"]), 3)

    def test_run_skips_preflight_when_requested(self) -> None:
        runs = [
            self._step("coderabbit-gate", 0),
            self._step("coderabbit-ralph-gate", 0),
        ]

        with (
            patch.object(release_gates, "run_cmd", side_effect=runs) as run_mock,
            patch.object(release_gates, "write_output"),
        ):
            rc = release_gates.run(_args(skip_preflight=True))

        self.assertEqual(rc, 0)
        self.assertEqual(run_mock.call_count, 2)
        call_names = [call.args[0] for call in run_mock.call_args_list]
        self.assertEqual(call_names, ["coderabbit-gate", "coderabbit-ralph-gate"])

    def test_run_fails_when_any_gate_fails(self) -> None:
        runs = [
            self._step("coderabbit-gate", 0),
            self._step("release-preflight-gate", 1, failure_output="gate failed"),
        ]

        with (
            patch.object(release_gates, "run_cmd", side_effect=runs) as run_mock,
            patch.object(release_gates, "write_output") as write_output_mock,
        ):
            rc = release_gates.run(_args())

        self.assertEqual(rc, 1)
        self.assertEqual(run_mock.call_count, 2)
        written = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(written["ok"])
        self.assertEqual(written["failure_reason"], "release-preflight-gate failed")
