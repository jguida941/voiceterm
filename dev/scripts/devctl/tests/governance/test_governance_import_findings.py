"""Tests for `devctl governance-import-findings` logging and parser wiring."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands import listing
from dev.scripts.devctl.commands.governance import import_findings
from dev.scripts.devctl.commands.governance import review as governance_review


class GovernanceImportFindingsTests(unittest.TestCase):
    def test_cli_parser_accepts_governance_import_findings_command(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "governance-import-findings",
                "--input",
                "/tmp/findings.json",
                "--input-format",
                "json",
                "--run-id",
                "pilot-16-repos",
                "--repo-name",
                "ci-cd-hub",
                "--check-id",
                "external_audit",
                "--signal-type",
                "audit",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "governance-import-findings")
        self.assertEqual(args.input, "/tmp/findings.json")
        self.assertEqual(args.input_format, "json")
        self.assertEqual(args.run_id, "pilot-16-repos")
        self.assertEqual(args.repo_name, "ci-cd-hub")
        self.assertEqual(args.check_id, "external_audit")
        self.assertEqual(args.signal_type, "audit")
        self.assertIs(
            cli.COMMAND_HANDLERS["governance-import-findings"],
            import_findings.run,
        )
        self.assertIn("governance-import-findings", listing.COMMANDS)

    def test_import_updates_summary_and_adjudication_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            input_path = root / "findings.json"
            log_path = root / "external-findings.jsonl"
            review_log_path = root / "reviews.jsonl"
            summary_root = root / "summary"
            review_summary_root = root / "review-summary"
            input_path.write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "repo_name": "alpha",
                                "check_id": "external_audit.command_source",
                                "path": "scripts/python_fallback.py",
                                "line": 479,
                                "title": "Unsafe argv forwarding",
                            },
                            {
                                "repo_name": "beta",
                                "check_id": "external_audit.tarfile",
                                "path": "pypi/src/voiceterm/cli.py",
                                "line": 146,
                                "title": "Tarfile member path risk",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            import_args = cli.build_parser().parse_args(
                [
                    "governance-import-findings",
                    "--input",
                    str(input_path),
                    "--log-path",
                    str(log_path),
                    "--summary-root",
                    str(summary_root),
                    "--governance-review-log",
                    str(review_log_path),
                    "--run-id",
                    "pilot-16-repos",
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(import_findings.run(import_args), 0)

            imported_rows = [
                json.loads(line)
                for line in log_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(imported_rows), 2)

            review_args = cli.build_parser().parse_args(
                [
                    "governance-review",
                    "--record",
                    "--log-path",
                    str(review_log_path),
                    "--summary-root",
                    str(review_summary_root),
                    "--finding-id",
                    str(imported_rows[0]["finding_id"]),
                    "--signal-type",
                    "audit",
                    "--check-id",
                    str(imported_rows[0]["check_id"]),
                    "--verdict",
                    "fixed",
                    "--path",
                    str(imported_rows[0]["file_path"]),
                    "--repo-name",
                    str(imported_rows[0]["repo_name"]),
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(governance_review.run(review_args), 0)

            summary_args = cli.build_parser().parse_args(
                [
                    "governance-import-findings",
                    "--log-path",
                    str(log_path),
                    "--summary-root",
                    str(summary_root),
                    "--governance-review-log",
                    str(review_log_path),
                    "--format",
                    "json",
                ]
            )
            self.assertEqual(import_findings.run(summary_args), 0)

            summary_json = summary_root / "external_findings_summary.json"
            payload = json.loads(summary_json.read_text(encoding="utf-8"))
            stats = payload.get("stats") or {}
            self.assertEqual(stats.get("total_findings"), 2)
            self.assertEqual(stats.get("reviewed_count"), 1)
            self.assertEqual(stats.get("adjudication_coverage_pct"), 50.0)
            self.assertEqual(stats.get("fixed_count"), 1)
            self.assertEqual((stats.get("by_repo") or [])[0]["bucket"], "alpha")

    def test_import_requires_repo_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            input_path = root / "findings.json"
            input_path.write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "check_id": "external_audit",
                                "path": "demo.py",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            args = cli.build_parser().parse_args(
                [
                    "governance-import-findings",
                    "--input",
                    str(input_path),
                    "--format",
                    "json",
                ]
            )

            rc = import_findings.run(args)

            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
