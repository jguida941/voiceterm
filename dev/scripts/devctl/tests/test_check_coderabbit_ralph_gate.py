"""Unit tests for CodeRabbit Ralph gate script behavior."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.config import REPO_ROOT

SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_coderabbit_ralph_gate.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "check_coderabbit_ralph_gate_script", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_coderabbit_ralph_gate.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckCodeRabbitRalphGateTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def test_parser_defaults_to_ralph_workflow(self) -> None:
        parser = self.script._build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.workflow, "CodeRabbit Ralph Loop")

    def test_normalize_report_renames_pass_reason(self) -> None:
        payload = {
            "ok": True,
            "reason": "coderabbit_gate_passed",
            "workflow": "CodeRabbit Ralph Loop",
        }
        normalized = self.script._normalize_report(payload)
        self.assertEqual(normalized["command"], "check_coderabbit_ralph_gate")
        self.assertEqual(normalized["reason"], "coderabbit_ralph_gate_passed")

    def test_main_returns_nonzero_for_failed_gate(self) -> None:
        args = SimpleNamespace(
            workflow="CodeRabbit Ralph Loop",
            repo="owner/repo",
            sha="a" * 40,
            branch="develop",
            limit=50,
            require_conclusion="success",
            format="json",
        )
        with (
            patch.object(self.script, "_build_parser") as parser_mock,
            patch.object(self.script.gate_core, "_build_report") as build_report_mock,
            patch("builtins.print") as print_mock,
        ):
            parser_mock.return_value.parse_args.return_value = args
            build_report_mock.return_value = {
                "ok": False,
                "workflow": "CodeRabbit Ralph Loop",
                "reason": "no_matching_workflow_runs_for_sha",
            }
            rc = self.script.main()

        self.assertEqual(rc, 1)
        printed = "".join(
            call.args[0] for call in print_mock.call_args_list if call.args
        )
        payload = json.loads(printed)
        self.assertFalse(payload["ok"])


if __name__ == "__main__":
    import unittest

    unittest.main()
