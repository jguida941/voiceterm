"""Tests for the typed-seam hard guard."""

from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from dev.scripts.devctl.tests.conftest import load_repo_module

SCRIPT = load_repo_module(
    "check_python_typed_seams_command",
    "dev/scripts/checks/python_typed_seams/command.py",
)


class CheckPythonTypedSeamsTests(unittest.TestCase):
    def test_parse_object_getattr_hits_reports_fixed_shape_attribute_bag(self) -> None:
        source = "\n".join(
            [
                "def choose(push: object) -> str:",
                "    checkpoint_reason = getattr(push, 'checkpoint_reason')",
                "    checkpoint_required = getattr(push, 'checkpoint_required')",
                "    return checkpoint_reason if checkpoint_required else 'clean'",
            ]
        )

        hits = SCRIPT.parse_object_getattr_hits(source)

        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["function_name"], "choose")
        self.assertEqual(hits[0]["param_name"], "push")
        self.assertEqual(hits[0]["getattr_count"], 2)
        self.assertEqual(
            hits[0]["attr_names"],
            ("checkpoint_reason", "checkpoint_required"),
        )

    def test_collect_typed_seam_violations_respects_configured_runtime_globs(self) -> None:
        source = "\n".join(
            [
                "def choose(push: object) -> str:",
                "    checkpoint_reason = getattr(push, 'checkpoint_reason')",
                "    return checkpoint_reason",
            ]
        )
        rules = (
            SCRIPT.TypedSeamRule(
                rule_id="runtime_helpers_no_object_getattr_bags",
                include_globs=("dev/scripts/devctl/runtime/**/*.py",),
                exclude_globs=(),
                min_object_getattr_calls=1,
                guidance="Convert the helper input into a typed runtime contract first.",
            ),
        )

        violations, candidates_scanned = SCRIPT.collect_typed_seam_violations(
            repo_root=Path("."),
            candidate_paths=[
                Path("dev/scripts/devctl/runtime/sample.py"),
                Path("dev/scripts/devctl/tests/test_sample.py"),
            ],
            rules=rules,
            read_text=lambda path: source if path.as_posix() == "dev/scripts/devctl/runtime/sample.py" else "",
        )

        self.assertEqual(candidates_scanned, 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["rule_id"], "runtime_helpers_no_object_getattr_bags")
        self.assertEqual(violations[0]["path"], "dev/scripts/devctl/runtime/sample.py")

    def test_main_emits_json_violation(self) -> None:
        source = "\n".join(
            [
                "def choose(push: object) -> str:",
                "    checkpoint_reason = getattr(push, 'checkpoint_reason')",
                "    checkpoint_required = getattr(push, 'checkpoint_required')",
                "    return checkpoint_reason if checkpoint_required else 'clean'",
            ]
        )

        with patch.object(
            SCRIPT,
            "list_changed_paths",
            return_value=[Path("dev/scripts/devctl/runtime/sample.py")],
        ), patch.object(
            SCRIPT.guard,
            "read_text_from_worktree",
            return_value=source,
        ), patch.object(
            SCRIPT,
            "resolve_guard_config",
            return_value={
                "rules": [
                    {
                        "rule_id": "runtime_helpers_no_object_getattr_bags",
                        "include_globs": ["dev/scripts/devctl/runtime/**/*.py"],
                        "min_object_getattr_calls": 1,
                        "guidance": "Convert the helper input into a typed runtime contract first.",
                    }
                ]
            },
        ), patch.object(
            sys,
            "argv",
            ["check_python_typed_seams.py", "--format", "json"],
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                rc = SCRIPT.main()

        self.assertEqual(rc, 1)
        payload = json.loads(buffer.getvalue())
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["configured_rules"], 1)
        self.assertEqual(len(payload["violations"]), 1)
        self.assertEqual(payload["violations"][0]["function_name"], "choose")


if __name__ == "__main__":
    unittest.main()
