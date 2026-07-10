"""Tests for the split-advisor review probe."""

from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.tests.conftest import load_repo_module

SCRIPT = load_repo_module(
    "probe_split_advisor",
    "dev/scripts/checks/code_shape_support/probe_split_advisor.py",
)


class SplitAdvisorProbeTests(unittest.TestCase):
    def test_main_emits_hotspot_aware_split_recommendation(self) -> None:
        sample_source = "\n".join(
            [
                "import helper",
                "",
                "def alpha():",
                "    beta()",
                "",
                "def beta():",
                "    alpha()",
                "",
                "def gamma():",
                "    delta()",
                "",
                "def delta():",
                "    gamma()",
                "",
                "def epsilon():",
                "    zeta()",
                "",
                "def zeta():",
                "    epsilon()",
            ]
        )
        helper_source = "\n".join(
            [
                "def utility():",
                "    return 1",
            ]
        )
        changed_paths = [
            Path("dev/scripts/devctl/sample.py"),
            Path("dev/scripts/devctl/helper.py"),
        ]
        current_text_by_path = {
            "dev/scripts/devctl/sample.py": sample_source,
            "dev/scripts/devctl/helper.py": helper_source,
        }
        hotspot_index = {
            "dev/scripts/devctl/sample.py": SCRIPT.HotspotContext(
                temperature=0.82,
                rank=2,
                connected_files=("dev/scripts/devctl/runtime/work_intake.py",),
            )
        }

        with patch.object(
            SCRIPT,
            "TARGET_ROOTS",
            (Path("dev/scripts/devctl"),),
        ), patch.object(
            SCRIPT,
            "list_changed_paths_with_base_map",
            return_value=(changed_paths, {}),
        ), patch.object(
            SCRIPT,
            "load_current_text_by_path",
            return_value=current_text_by_path,
        ), patch.object(
            SCRIPT,
            "_load_hotspot_context",
            return_value=hotspot_index,
        ), patch.object(
            sys,
            "argv",
            ["probe_split_advisor.py", "--format", "json"],
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                rc = SCRIPT.main()

        self.assertEqual(rc, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["command"], "probe_split_advisor")
        self.assertEqual(payload["files_scanned"], 2)
        self.assertEqual(payload["files_with_hints"], 1)
        self.assertEqual(len(payload["risk_hints"]), 1)
        hint = payload["risk_hints"][0]
        self.assertEqual(hint["risk_type"], "split_advisor")
        self.assertEqual(hint["severity"], "high")
        self.assertIn("changed-file import coupling", " ".join(hint["signals"]))
        self.assertIn("context hotspot rank 2", " ".join(hint["signals"]))
        self.assertIn("helper.py", hint["ai_instruction"])
        self.assertIn("context-graph rank 2", hint["ai_instruction"])


if __name__ == "__main__":
    unittest.main()
