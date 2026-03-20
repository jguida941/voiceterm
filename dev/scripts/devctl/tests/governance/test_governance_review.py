"""Tests for `devctl governance-review` logging and parser wiring."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands.governance import review as governance_review
from dev.scripts.devctl.governance_review_log import build_governance_review_row
from dev.scripts.devctl.governance_review_models import GovernanceReviewInput


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

    def test_default_finding_id_ignores_absolute_repo_path(self) -> None:
        row_one = build_governance_review_row(
            review_input=GovernanceReviewInput(
                signal_type="audit",
                check_id="external_audit.command_source",
                verdict="confirmed_issue",
                file_path="scripts/python_fallback.py",
                repo_name="ci-cd-hub",
                repo_path="/Users/alice/repos/ci-cd-hub",
                line=479,
            )
        )
        row_two = build_governance_review_row(
            review_input=GovernanceReviewInput(
                signal_type="audit",
                check_id="external_audit.command_source",
                verdict="confirmed_issue",
                file_path="scripts/python_fallback.py",
                repo_name="ci-cd-hub",
                repo_path="/tmp/portable/ci-cd-hub",
                line=479,
            )
        )

        self.assertEqual(row_one["finding_id"], row_two["finding_id"])
        self.assertEqual(row_one["repo_path"], "/Users/alice/repos/ci-cd-hub")
        self.assertEqual(row_two["repo_path"], "/tmp/portable/ci-cd-hub")

    def test_review_row_normalizes_absolute_file_path_for_identity(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first_root = Path(first_tmp) / "portable-demo"
            second_root = Path(second_tmp) / "portable-demo"
            first_path = first_root / "pkg" / "demo.py"
            second_path = second_root / "pkg" / "demo.py"
            first_path.parent.mkdir(parents=True, exist_ok=True)
            second_path.parent.mkdir(parents=True, exist_ok=True)
            first_path.write_text("# demo\n", encoding="utf-8")
            second_path.write_text("# demo\n", encoding="utf-8")

            row_one = build_governance_review_row(
                review_input=GovernanceReviewInput(
                    signal_type="audit",
                    check_id="external_audit.command_source",
                    verdict="confirmed_issue",
                    file_path=str(first_path),
                    repo_name="portable-demo",
                    line=12,
                ),
                repo_root=first_root,
            )
            row_two = build_governance_review_row(
                review_input=GovernanceReviewInput(
                    signal_type="audit",
                    check_id="external_audit.command_source",
                    verdict="confirmed_issue",
                    file_path=str(second_path),
                    repo_name="portable-demo",
                    line=12,
                ),
                repo_root=second_root,
            )

            self.assertEqual(row_one["file_path"], "pkg/demo.py")
            self.assertEqual(row_one["finding_id"], row_two["finding_id"])


if __name__ == "__main__":
    unittest.main()
