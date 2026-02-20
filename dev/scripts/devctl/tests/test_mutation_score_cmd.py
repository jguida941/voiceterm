"""Tests for mutation-score command wiring."""

import unittest

from dev.scripts.devctl.commands.mutation_score import build_mutation_score_cmd


class MutationScoreCommandTests(unittest.TestCase):
    """Validate command argument construction for freshness controls."""

    def test_build_cmd_includes_warn_age_by_default(self) -> None:
        cmd = build_mutation_score_cmd("/tmp/outcomes.json", 0.8, None, 24.0)
        self.assertEqual(
            cmd,
            [
                "python3",
                "dev/scripts/check_mutation_score.py",
                "--path",
                "/tmp/outcomes.json",
                "--threshold",
                "0.80",
                "--warn-age-hours",
                "24.0",
            ],
        )

    def test_build_cmd_includes_max_age_when_provided(self) -> None:
        cmd = build_mutation_score_cmd("/tmp/outcomes.json", 0.9, 48.0, 12.0)
        self.assertEqual(
            cmd,
            [
                "python3",
                "dev/scripts/check_mutation_score.py",
                "--path",
                "/tmp/outcomes.json",
                "--threshold",
                "0.90",
                "--warn-age-hours",
                "12.0",
                "--max-age-hours",
                "48.0",
            ],
        )


if __name__ == "__main__":
    unittest.main()
