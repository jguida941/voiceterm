"""Tests for the standalone run_probe_report fallback runner."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.tests.conftest import load_repo_module

SCRIPT = load_repo_module(
    "run_probe_report",
    "dev/scripts/checks/run_probe_report.py",
)


class RunProbeReportTests(unittest.TestCase):
    @patch.object(SCRIPT, "_run_probe")
    @patch.object(SCRIPT, "resolve_review_probe_script_ids")
    def test_main_resolves_registered_probes_from_quality_policy(
        self,
        mock_resolve_probe_ids,
        mock_run_probe,
    ) -> None:
        mock_resolve_probe_ids.return_value = ("probe_design_smells",)
        mock_run_probe.return_value = {
            "command": "probe_design_smells",
            "files_scanned": 1,
            "risk_hints": [],
        }

        with patch.object(
            sys,
            "argv",
            [
                "run_probe_report.py",
                "--format",
                "json",
                "--quality-policy",
                "/tmp/pilot-policy.json",
            ],
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                rc = SCRIPT.main()

        self.assertEqual(rc, 0)
        mock_resolve_probe_ids.assert_called_once_with(
            policy_path="/tmp/pilot-policy.json"
        )
        mock_run_probe.assert_called_once_with(
            "probe_design_smells",
            since_ref=None,
            head_ref="HEAD",
            policy_path="/tmp/pilot-policy.json",
        )
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload[0]["command"], "probe_design_smells")

    @patch.object(SCRIPT, "probe_script_cmd")
    @patch.object(SCRIPT.subprocess, "run")
    def test_run_probe_exports_quality_policy_env(
        self,
        mock_subprocess_run,
        mock_probe_script_cmd,
    ) -> None:
        mock_probe_script_cmd.return_value = [
            "python3",
            "dev/scripts/checks/probe_design_smells.py",
            "--format",
            "json",
        ]
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=["python3"],
            returncode=0,
            stdout=json.dumps({"command": "probe_design_smells", "risk_hints": []}),
            stderr="",
        )

        SCRIPT._run_probe(
            "probe_design_smells",
            since_ref=None,
            head_ref="HEAD",
            policy_path="/tmp/pilot-policy.json",
        )

        env = mock_subprocess_run.call_args.kwargs["env"]
        self.assertEqual(
            env[SCRIPT.QUALITY_POLICY_ENV_VAR],
            str(Path("/tmp/pilot-policy.json").expanduser()),
        )


if __name__ == "__main__":
    unittest.main()
