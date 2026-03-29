"""Tests for the mixed-concerns review probe."""

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
    "probe_mixed_concerns",
    "dev/scripts/checks/code_shape_support/probe_mixed_concerns.py",
)


class MixedConcernsProbeTests(unittest.TestCase):
    def test_find_function_clusters_detects_three_independent_groups(self) -> None:
        source = "\n".join(
            [
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

        clusters = SCRIPT.find_function_clusters(source)

        self.assertEqual(len(clusters), 3)
        self.assertEqual({len(cluster) for cluster in clusters}, {2})

    def test_main_emits_risk_hints_for_mixed_concern_files(self) -> None:
        source = "\n".join(
            [
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

        with patch.object(
            SCRIPT,
            "list_changed_paths_with_base_map",
            return_value=([Path("dev/scripts/devctl/sample.py")], {}),
        ), patch.object(
            SCRIPT,
            "load_probe_text",
            return_value=source,
        ), patch.object(
            sys,
            "argv",
            ["probe_mixed_concerns.py", "--format", "json"],
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                rc = SCRIPT.main()

        self.assertEqual(rc, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["command"], "probe_mixed_concerns")
        self.assertEqual(payload["files_scanned"], 1)
        self.assertEqual(payload["files_with_hints"], 1)
        self.assertEqual(len(payload["risk_hints"]), 1)
        hint = payload["risk_hints"][0]
        self.assertEqual(hint["risk_type"], "mixed_concerns")
        self.assertEqual(hint["severity"], "medium")
        self.assertIn("independent function groups", hint["signals"][0])


if __name__ == "__main__":
    unittest.main()
