"""Tests for `devctl governance-review` logging and parser wiring."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands.governance import review as governance_review


class GovernanceReviewCommandTests(unittest.TestCase):
    def test_cli_parser_accepts_governance_review_command(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "governance-review",
                "--record",
                "--log-path",
                "/tmp/reviews.jsonl",
                "--summary-root",
                "/tmp/review-summary",
                "--finding-id",
                "finding-1",
                "--signal-type",
                "probe",
                "--check-id",
                "probe_single_use_helpers",
                "--verdict",
                "false_positive",
                "--path",
                "demo.py",
                "--line",
                "14",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "governance-review")
        self.assertTrue(args.record)
        self.assertEqual(args.log_path, "/tmp/reviews.jsonl")
        self.assertEqual(args.summary_root, "/tmp/review-summary")
        self.assertEqual(args.finding_id, "finding-1")
        self.assertEqual(args.signal_type, "probe")
        self.assertEqual(args.check_id, "probe_single_use_helpers")
        self.assertEqual(args.verdict, "false_positive")
        self.assertEqual(args.path, "demo.py")
        self.assertEqual(args.line, 14)
        self.assertIs(cli.COMMAND_HANDLERS["governance-review"], governance_review.run)

    def test_record_updates_latest_finding_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            log_path = root / "finding_reviews.jsonl"
            summary_root = root / "summary"

            first_args = cli.build_parser().parse_args(
                [
                    "governance-review",
                    "--record",
                    "--log-path",
                    str(log_path),
                    "--summary-root",
                    str(summary_root),
                    "--finding-id",
                    "finding-1",
                    "--signal-type",
                    "probe",
                    "--check-id",
                    "probe_exception_quality",
                    "--verdict",
                    "false_positive",
                    "--path",
                    "demo.py",
                    "--line",
                    "7",
                    "--format",
                    "json",
                ]
            )
            second_args = cli.build_parser().parse_args(
                [
                    "governance-review",
                    "--record",
                    "--log-path",
                    str(log_path),
                    "--summary-root",
                    str(summary_root),
                    "--finding-id",
                    "finding-1",
                    "--signal-type",
                    "probe",
                    "--check-id",
                    "probe_exception_quality",
                    "--verdict",
                    "fixed",
                    "--path",
                    "demo.py",
                    "--line",
                    "7",
                    "--format",
                    "json",
                ]
            )

            self.assertEqual(governance_review.run(first_args), 0)
            self.assertEqual(governance_review.run(second_args), 0)

            summary_json = summary_root / "review_summary.json"
            payload = json.loads(summary_json.read_text(encoding="utf-8"))
            stats = payload.get("stats") or {}

            self.assertEqual(stats.get("total_rows"), 2)
            self.assertEqual(stats.get("total_findings"), 1)
            self.assertEqual(stats.get("false_positive_count"), 0)
            self.assertEqual(stats.get("fixed_count"), 1)
            self.assertEqual(stats.get("cleanup_rate_pct"), 100.0)
            self.assertEqual(
                (payload.get("recent_findings") or [{}])[-1].get("verdict"),
                "fixed",
            )

    def test_record_requires_mandatory_fields(self) -> None:
        args = cli.build_parser().parse_args(
            [
                "governance-review",
                "--record",
                "--signal-type",
                "probe",
                "--format",
                "json",
            ]
        )

        rc = governance_review.run(args)

        self.assertEqual(rc, 2)

    def test_record_accepts_audit_signal_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            log_path = root / "finding_reviews.jsonl"
            summary_root = root / "summary"

            args = cli.build_parser().parse_args(
                [
                    "governance-review",
                    "--record",
                    "--log-path",
                    str(log_path),
                    "--summary-root",
                    str(summary_root),
                    "--signal-type",
                    "audit",
                    "--check-id",
                    "external_audit.command_source",
                    "--verdict",
                    "confirmed_issue",
                    "--path",
                    "scripts/python_fallback.py",
                    "--repo-name",
                    "ci-cd-hub",
                    "--line",
                    "479",
                    "--format",
                    "json",
                ]
            )

            self.assertEqual(governance_review.run(args), 0)
            payload = json.loads(
                (summary_root / "review_summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(payload["stats"]["total_findings"], 1)
            self.assertEqual(
                (payload.get("recent_findings") or [{}])[0].get("signal_type"),
                "audit",
            )


if __name__ == "__main__":
    unittest.main()
