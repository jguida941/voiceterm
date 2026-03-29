"""Tests for watchdog probe-gate helpers."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dev.scripts.devctl.watchdog import probe_gate


class ProbeGateTests(unittest.TestCase):
    def test_run_probe_scan_filters_allowlisted_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            runner = root / "run_probe_report.py"
            runner.write_text("print('ok')\n", encoding="utf-8")
            allowlist = root / ".probe-allowlist.json"
            allowlist.write_text(
                json.dumps(
                    {
                        "entries": [{"file": "src/a.py", "symbol": "alpha"}],
                        "suppressed": [],
                    }
                ),
                encoding="utf-8",
            )
            report_payload = [
                {
                    "command": "probe_demo",
                    "files_scanned": 3,
                    "risk_hints": [
                        {
                            "file": "src/a.py",
                            "symbol": "alpha",
                            "severity": "high",
                            "signals": ["allowlisted finding"],
                        },
                        {
                            "file": "src/b.py",
                            "symbol": "beta",
                            "severity": "medium",
                            "signals": ["active finding"],
                        },
                    ],
                }
            ]

            with (
                mock.patch.object(probe_gate, "PROBE_RUNNER", runner),
                mock.patch.object(probe_gate, "ALLOWLIST_PATH", allowlist),
                mock.patch.object(
                    probe_gate.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess(
                        args=["python3", str(runner)],
                        returncode=0,
                        stdout=json.dumps(report_payload),
                        stderr="",
                    ),
                ),
            ):
                result = probe_gate.run_probe_scan()

        self.assertEqual(result.total_findings, 1)
        self.assertEqual(result.high_count, 0)
        self.assertEqual(result.medium_count, 1)
        self.assertEqual(result.files_affected, 1)
        self.assertEqual(result.files_scanned, 3)
        self.assertEqual(result.probes_run, 1)
        self.assertEqual(result.risk, "low")
        self.assertEqual(result.findings[0]["file"], "src/b.py")
        self.assertEqual(result.findings[0]["probe"], "probe_demo")

    def test_run_probe_scan_ignores_invalid_allowlist_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            runner = root / "run_probe_report.py"
            runner.write_text("print('ok')\n", encoding="utf-8")
            allowlist = root / ".probe-allowlist.json"
            allowlist.write_text("{invalid json\n", encoding="utf-8")
            report_payload = [
                {
                    "command": "probe_demo",
                    "files_scanned": 1,
                    "risk_hints": [
                        {
                            "file": "src/a.py",
                            "symbol": "alpha",
                            "severity": "high",
                            "signals": ["still active"],
                        }
                    ],
                }
            ]

            with (
                mock.patch.object(probe_gate, "PROBE_RUNNER", runner),
                mock.patch.object(probe_gate, "ALLOWLIST_PATH", allowlist),
                mock.patch.object(
                    probe_gate.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess(
                        args=["python3", str(runner)],
                        returncode=0,
                        stdout=json.dumps(report_payload),
                        stderr="",
                    ),
                ),
            ):
                result = probe_gate.run_probe_scan()

        self.assertEqual(result.total_findings, 1)
        self.assertEqual(result.high_count, 1)
        self.assertEqual(result.risk, "high")


if __name__ == "__main__":
    unittest.main()
