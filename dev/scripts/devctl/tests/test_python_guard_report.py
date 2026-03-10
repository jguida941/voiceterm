"""Tests for Python guard backlog aggregation helpers."""

from __future__ import annotations

import json
import subprocess
import unittest
from unittest.mock import patch

from dev.scripts.devctl import python_guard_report


def _completed(payload: dict, *, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["python3", "check.py"],
        returncode=returncode,
        stdout=json.dumps(payload),
        stderr="",
    )


class PythonGuardReportTests(unittest.TestCase):
    def test_collect_python_guard_report_aggregates_hotspots(self) -> None:
        side_effect = [
            _completed(
                {
                    "ok": False,
                    "files_considered": 4,
                    "files_changed": 6,
                    "violations": [
                        {
                            "path": "app/operator_console/views/main_window.py",
                            "growth": {"large_dict_literals": 2},
                        }
                    ],
                },
                returncode=1,
            ),
            _completed(
                {
                    "ok": True,
                    "files_considered": 5,
                    "files_changed": 6,
                    "violations": [],
                }
            ),
            _completed(
                {
                    "ok": False,
                    "files_considered": 5,
                    "files_changed": 6,
                    "violations": [
                        {
                            "path": "app/operator_console/views/main_window.py",
                            "growth": {"high_param_functions": 1},
                        },
                        {
                            "path": "dev/scripts/devctl/review_channel/state.py",
                            "growth": {"high_param_functions": 2},
                        },
                    ],
                },
                returncode=1,
            ),
            _completed(
                {
                    "ok": True,
                    "files_considered": 5,
                    "files_changed": 6,
                    "violations": [],
                }
            ),
            _completed(
                {
                    "ok": False,
                    "files_considered": 5,
                    "files_changed": 6,
                    "violations": [
                        {
                            "path": "dev/scripts/devctl/review_channel/state.py",
                            "growth": {"god_classes": 1},
                        }
                    ],
                },
                returncode=1,
            ),
            _completed(
                {
                    "ok": False,
                    "files_scanned": 5,
                    "files_changed": 6,
                    "violations": [
                        {
                            "path": "dev/scripts/devctl/review_channel/state.py",
                            "line": 19,
                            "kind": "Exception",
                            "reason": "missing rationale",
                        }
                    ],
                },
                returncode=1,
            ),
            _completed(
                {
                    "ok": False,
                    "files_scanned": 8,
                    "files_changed": 6,
                    "violations": [
                        {
                            "path": "dev/scripts/devctl/process_sweep/scans.py",
                            "line": 44,
                            "reason": "subprocess.run call is missing explicit check=",
                        }
                    ],
                },
                returncode=1,
            ),
        ]
        with patch.object(
            python_guard_report.subprocess,
            "run",
            side_effect=side_effect,
        ):
            report = python_guard_report.collect_python_guard_report(
                since_ref="origin/develop",
                head_ref="HEAD",
                top_n=10,
            )

        summary = report["summary"]
        self.assertEqual(report["mode"], "commit-range")
        self.assertEqual(summary["guard_count"], 7)
        self.assertEqual(summary["guard_failures"], 5)
        self.assertEqual(summary["active_paths"], 3)
        self.assertEqual(summary["total_active_findings"], 8)
        self.assertEqual(summary["top_risk_score"], 800)
        hotspots = report["hotspots"]
        self.assertEqual(hotspots[0]["path"], "dev/scripts/devctl/review_channel/state.py")
        self.assertEqual(hotspots[1]["path"], "app/operator_console/views/main_window.py")

    def test_render_python_guard_markdown(self) -> None:
        report = {
            "mode": "working-tree",
            "ok": False,
            "summary": {
                "guard_count": 5,
                "guard_failures": 2,
                "active_paths": 3,
                "total_active_findings": 7,
                "top_risk_score": 620,
            },
            "hotspots": [
                {
                    "path": "app/operator_console/views/main_window.py",
                    "score": 620,
                    "count": 3,
                    "guard_count": 2,
                }
            ],
            "warnings": [],
            "errors": [],
        }
        lines = python_guard_report.render_python_guard_markdown(report)
        rendered = "\n".join(lines)
        self.assertIn("## Python Guard Backlog", rendered)
        self.assertIn("- guard_failures: 2", rendered)
        self.assertIn("main_window.py: score=620", rendered)


if __name__ == "__main__":
    unittest.main()
