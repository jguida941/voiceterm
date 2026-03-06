"""End-to-end checks for check_mutation_score.py freshness behavior."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_mutation_score.py"


def write_outcomes(path: Path, caught: int, missed: int, timeout: int, unviable: int) -> None:
    payload = {
        "caught": caught,
        "missed": missed,
        "timeout": timeout,
        "unviable": unviable,
        "outcomes": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class MutationScoreScriptTests(unittest.TestCase):
    """Validate freshness visibility and stale-age gating."""

    def test_prints_source_metadata_for_single_outcomes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            outcomes = Path(tmpdir) / "outcomes.json"
            write_outcomes(outcomes, caught=8, missed=1, timeout=0, unviable=0)

            proc = subprocess.run(
                [
                    "python3",
                    str(SCRIPT_PATH),
                    "--path",
                    str(outcomes),
                    "--threshold",
                    "0.80",
                    "--warn-age-hours",
                    "999",
                ],
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )

        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("Outcome file:", proc.stdout)
        self.assertIn("Mutation score:", proc.stdout)

    def test_fails_when_outcomes_are_older_than_max_age(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            outcomes = Path(tmpdir) / "outcomes.json"
            write_outcomes(outcomes, caught=8, missed=1, timeout=0, unviable=0)
            two_days_ago = int((Path(outcomes).stat().st_mtime) - (48 * 3600))
            os.utime(outcomes, (two_days_ago, two_days_ago))

            proc = subprocess.run(
                [
                    "python3",
                    str(SCRIPT_PATH),
                    "--path",
                    str(outcomes),
                    "--threshold",
                    "0.80",
                    "--warn-age-hours",
                    "-1",
                    "--max-age-hours",
                    "1",
                ],
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )

        self.assertEqual(proc.returncode, 1, msg=proc.stdout + proc.stderr)
        self.assertIn("FAIL: mutation outcomes exceed max age threshold", proc.stdout)

    def test_report_only_warns_when_outcomes_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "outcomes.json"
            proc = subprocess.run(
                [
                    "python3",
                    str(SCRIPT_PATH),
                    "--path",
                    str(missing),
                    "--threshold",
                    "0.80",
                    "--report-only",
                ],
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )

        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("WARN: outcomes file not found", proc.stdout)
        self.assertIn("post-release follow-up", proc.stdout)

    def test_report_only_warns_when_score_is_below_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            outcomes = Path(tmpdir) / "outcomes.json"
            write_outcomes(outcomes, caught=1, missed=9, timeout=0, unviable=0)
            proc = subprocess.run(
                [
                    "python3",
                    str(SCRIPT_PATH),
                    "--path",
                    str(outcomes),
                    "--threshold",
                    "0.80",
                    "--report-only",
                ],
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )

        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("WARN: mutation score", proc.stdout)
        self.assertIn("post-release follow-up", proc.stdout)


if __name__ == "__main__":
    unittest.main()
