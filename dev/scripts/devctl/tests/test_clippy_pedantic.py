"""Tests for advisory clippy::pedantic artifact classification."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl import clippy_pedantic


class ClippyPedanticTests(unittest.TestCase):
    def test_build_snapshot_classifies_policy_and_unreviewed_lints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            summary_path = root / "summary.json"
            lints_path = root / "lints.json"
            policy_path = root / "policy.json"

            summary_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "generated_at": "2026-03-08T00:00:00Z",
                        "warnings": 9,
                        "exit_code": 0,
                        "status": "failure",
                    }
                ),
                encoding="utf-8",
            )
            lints_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "lints": {
                            "clippy::redundant_else": 4,
                            "clippy::cast_precision_loss": 7,
                            "clippy::missing_panics_doc": 2,
                            "clippy::manual_let_else": 1,
                        },
                    }
                ),
                encoding="utf-8",
            )
            policy_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "default_action": "review",
                        "rules": [
                            {
                                "id": "promote.redundant_else",
                                "match": {"lint": "clippy::redundant_else"},
                                "action": "promote",
                                "bug_risk": "medium",
                                "noise": "low",
                                "fix_cost": "low",
                                "reason": "Good strict-lane candidate.",
                            },
                            {
                                "id": "defer.casts",
                                "match": {"prefix": "clippy::cast_"},
                                "action": "defer",
                                "bug_risk": "medium",
                                "noise": "high",
                                "fix_cost": "high",
                                "reason": "Intentional cast-heavy codebase.",
                            },
                            {
                                "id": "defer.docs",
                                "match": {"pattern": "clippy::missing_*_doc"},
                                "action": "defer",
                                "bug_risk": "low",
                                "noise": "high",
                                "fix_cost": "medium",
                                "reason": "Roll out doc lints by surface area.",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            snapshot = clippy_pedantic.build_snapshot(
                summary_path=str(summary_path),
                lints_path=str(lints_path),
                policy_path=str(policy_path),
            )

        self.assertTrue(snapshot["artifact_found"])
        self.assertEqual(snapshot["observed_lints"], 4)
        self.assertEqual(snapshot["reviewed_lints"], 3)
        self.assertEqual(snapshot["unreviewed_lints"], 1)
        self.assertEqual(
            snapshot["top_promote_candidates"][0]["lint"], "clippy::redundant_else"
        )
        self.assertEqual(
            snapshot["rollup"]["observations_by_action"]["defer"],
            9,
        )
        self.assertTrue(
            any(
                "run failed" in issue["summary"]
                for issue in snapshot["issues"]
            )
        )
        self.assertTrue(
            any(
                "unreviewed lint ids" in issue["summary"]
                for issue in snapshot["issues"]
            )
        )

    def test_build_snapshot_reports_missing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            policy_path = root / "policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "default_action": "review",
                        "rules": [],
                    }
                ),
                encoding="utf-8",
            )

            snapshot = clippy_pedantic.build_snapshot(
                summary_path=str(root / "missing-summary.json"),
                lints_path=str(root / "missing-lints.json"),
                policy_path=str(policy_path),
            )

        self.assertFalse(snapshot["artifact_found"])
        self.assertIn("artifact missing", snapshot["warning"])
        self.assertTrue(snapshot["issues"])
        self.assertIn("artifacts are unavailable", snapshot["issues"][0]["summary"])


if __name__ == "__main__":
    unittest.main()
