"""Tests for `devctl governance-review` logging and parser wiring."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands.governance import review as governance_review
from dev.scripts.devctl.governance_review_log import build_governance_review_row
from dev.scripts.devctl.governance_review_models import (
    FINDING_REVIEW_CONTRACT_ID,
    FINDING_REVIEW_SCHEMA_VERSION,
    GovernanceReviewInput,
    VALID_FINDING_CLASSES,
    VALID_PREVENTION_SURFACES,
    VALID_RECURRENCE_RISKS,
)


class GovernanceReviewCommandTests(unittest.TestCase):
    def test_schema_template_matches_finding_review_v2_contract(self) -> None:
        schema_path = (
            Path(__file__).resolve().parents[4]
            / "config"
            / "templates"
            / "portable_governance_finding_review.schema.json"
        )
        payload = json.loads(schema_path.read_text(encoding="utf-8"))
        properties = payload["properties"]

        self.assertEqual(properties["schema_version"]["const"], FINDING_REVIEW_SCHEMA_VERSION)
        self.assertEqual(properties["contract_id"]["const"], FINDING_REVIEW_CONTRACT_ID)
        self.assertEqual(
            tuple(properties["finding_class"]["enum"]),
            VALID_FINDING_CLASSES,
        )
        self.assertEqual(
            tuple(properties["recurrence_risk"]["enum"]),
            VALID_RECURRENCE_RISKS,
        )
        self.assertEqual(
            tuple(properties["prevention_surface"]["enum"]),
            VALID_PREVENTION_SURFACES,
        )
        self.assertIn("schema_version", payload["required"])
        self.assertIn("contract_id", payload["required"])
        self.assertIn("finding_class", payload["required"])
        self.assertIn("recurrence_risk", payload["required"])
        self.assertIn("prevention_surface", payload["required"])
        self.assertIn("audit", properties["signal_type"]["enum"])
        self.assertIn("external", properties["scan_mode"]["enum"])

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
                "--finding-class",
                "rule_quality",
                "--recurrence-risk",
                "recurring",
                "--prevention-surface",
                "probe",
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
        self.assertEqual(args.finding_class, "rule_quality")
        self.assertEqual(args.recurrence_risk, "recurring")
        self.assertEqual(args.prevention_surface, "probe")
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
                    "--finding-class",
                    "rule_quality",
                    "--recurrence-risk",
                    "recurring",
                    "--prevention-surface",
                    "probe",
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
                    "--finding-class",
                    "rule_quality",
                    "--recurrence-risk",
                    "recurring",
                    "--prevention-surface",
                    "probe",
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

    def test_record_requires_disposition_fields_even_when_core_fields_exist(self) -> None:
        args = cli.build_parser().parse_args(
            [
                "governance-review",
                "--record",
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

        rc = governance_review.run(args)

        self.assertEqual(rc, 2)

    def test_record_requires_waiver_reason_for_none_surface(self) -> None:
        args = cli.build_parser().parse_args(
            [
                "governance-review",
                "--record",
                "--signal-type",
                "probe",
                "--check-id",
                "probe_exception_quality",
                "--verdict",
                "deferred",
                "--path",
                "demo.py",
                "--line",
                "7",
                "--finding-class",
                "rule_quality",
                "--recurrence-risk",
                "recurring",
                "--prevention-surface",
                "none",
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
                    "--finding-class",
                    "local_defect",
                    "--recurrence-risk",
                    "recurring",
                    "--prevention-surface",
                    "parity_check",
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
        self.assertEqual(
            (payload.get("recent_findings") or [{}])[0].get("prevention_surface"),
            "parity_check",
        )

    def test_review_row_includes_disposition_contract_fields(self) -> None:
        row = build_governance_review_row(
            review_input=GovernanceReviewInput(
                signal_type="probe",
                check_id="probe_exception_quality",
                verdict="fixed",
                file_path="demo.py",
                line=7,
                finding_class="rule_quality",
                recurrence_risk="recurring",
                prevention_surface="probe",
            )
        )

        self.assertEqual(row["schema_version"], FINDING_REVIEW_SCHEMA_VERSION)
        self.assertEqual(row["contract_id"], FINDING_REVIEW_CONTRACT_ID)
        self.assertEqual(row["finding_class"], "rule_quality")
        self.assertEqual(row["recurrence_risk"], "recurring")
        self.assertEqual(row["prevention_surface"], "probe")

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
                finding_class="local_defect",
                recurrence_risk="recurring",
                prevention_surface="regression_test",
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
                finding_class="local_defect",
                recurrence_risk="recurring",
                prevention_surface="regression_test",
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
                    finding_class="local_defect",
                    recurrence_risk="recurring",
                    prevention_surface="regression_test",
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
                    finding_class="local_defect",
                    recurrence_risk="recurring",
                    prevention_surface="regression_test",
                ),
                repo_root=second_root,
            )

            self.assertEqual(row_one["file_path"], "pkg/demo.py")
            self.assertEqual(row_one["finding_id"], row_two["finding_id"])


if __name__ == "__main__":
    unittest.main()
