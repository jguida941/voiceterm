"""Tests for devctl hygiene auditing."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import hygiene


class HygieneAuditTests(unittest.TestCase):
    """Validate core hygiene audit checks."""

    def setUp(self) -> None:
        self.original_repo_root = hygiene.REPO_ROOT

    def tearDown(self) -> None:
        hygiene.REPO_ROOT = self.original_repo_root

    def test_archive_audit_flags_bad_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_dir = root / "dev/archive"
            archive_dir.mkdir(parents=True)
            (archive_dir / "README.md").write_text("# Archive\n", encoding="utf-8")
            (archive_dir / "bad-name.md").write_text("x", encoding="utf-8")
            hygiene.REPO_ROOT = root

            report = hygiene._audit_archive()

            self.assertTrue(report["errors"])
            self.assertIn("bad-name.md", report["errors"][0])

    def test_adr_audit_flags_index_status_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adr_dir = root / "dev/adr"
            adr_dir.mkdir(parents=True)
            (adr_dir / "0001-example.md").write_text(
                "# ADR 0001: Example\n\nStatus: Accepted\nDate: 2026-02-13\n",
                encoding="utf-8",
            )
            (adr_dir / "README.md").write_text(
                "# ADR Index\n\n| ADR | Title | Status |\n|-----|-------|--------|\n"
                "| [0001](0001-example.md) | Example | Proposed |\n",
                encoding="utf-8",
            )
            hygiene.REPO_ROOT = root

            report = hygiene._audit_adrs()

            self.assertTrue(report["errors"])
            self.assertTrue(
                any("status mismatch" in error for error in report["errors"])
            )

    def test_adr_audit_flags_backlog_scope_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adr_dir = root / "dev/adr"
            adr_dir.mkdir(parents=True)
            (adr_dir / "0001-example.md").write_text(
                "# ADR 0001: Example\n\nStatus: Accepted\nDate: 2026-02-13\n",
                encoding="utf-8",
            )
            (adr_dir / "README.md").write_text(
                "# ADR Index\n\n"
                "| ADR | Title | Status |\n"
                "|-----|-------|--------|\n"
                "| [0001](0001-example.md) | Example | Accepted |\n\n"
                "Retired ADR IDs: none\n"
                "Reserved ADR IDs: 0027-0034\n\n"
                "1. Copy the template and increment the number (next: 0002)\n",
                encoding="utf-8",
            )
            active_dir = root / "dev/active"
            active_dir.mkdir(parents=True)
            (active_dir / "MASTER_PLAN.md").write_text(
                "## ADR Program Backlog (Cross-Plan, Pending)\n"
                "- ADR-0027 placeholder\n",
                encoding="utf-8",
            )
            (active_dir / "autonomous_control_plane.md").write_text(
                "### 3.6 ADR Backlog (Required for Scope Control)\n"
                "- ADR-0028 placeholder\n",
                encoding="utf-8",
            )
            hygiene.REPO_ROOT = root

            report = hygiene._audit_adrs()

            self.assertTrue(report["errors"])
            self.assertTrue(
                any(
                    "backlog scope mismatch" in error.lower()
                    for error in report["errors"]
                )
            )

    def test_adr_audit_flags_backlog_ids_missing_reserved_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adr_dir = root / "dev/adr"
            adr_dir.mkdir(parents=True)
            (adr_dir / "0001-example.md").write_text(
                "# ADR 0001: Example\n\nStatus: Accepted\nDate: 2026-02-13\n",
                encoding="utf-8",
            )
            (adr_dir / "README.md").write_text(
                "# ADR Index\n\n"
                "| ADR | Title | Status |\n"
                "|-----|-------|--------|\n"
                "| [0001](0001-example.md) | Example | Accepted |\n\n"
                "Retired ADR IDs: none\n"
                "Reserved ADR IDs: none\n\n"
                "1. Copy the template and increment the number (next: 0002)\n",
                encoding="utf-8",
            )
            active_dir = root / "dev/active"
            active_dir.mkdir(parents=True)
            backlog = (
                "### 3.6 ADR Backlog (Required for Scope Control)\n"
                "- ADR-0027 placeholder\n"
            )
            (active_dir / "MASTER_PLAN.md").write_text(
                "## ADR Program Backlog (Cross-Plan, Pending)\n"
                "- ADR-0027 placeholder\n",
                encoding="utf-8",
            )
            (active_dir / "autonomous_control_plane.md").write_text(
                backlog,
                encoding="utf-8",
            )
            hygiene.REPO_ROOT = root

            report = hygiene._audit_adrs()

            self.assertTrue(report["errors"])
            self.assertTrue(
                any(
                    "missing from `Reserved ADR IDs`" in error
                    for error in report["errors"]
                )
            )

    def test_adr_audit_flags_unexplained_numbering_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adr_dir = root / "dev/adr"
            adr_dir.mkdir(parents=True)
            (adr_dir / "0001-example.md").write_text(
                "# ADR 0001: Example\n\nStatus: Accepted\nDate: 2026-02-13\n",
                encoding="utf-8",
            )
            (adr_dir / "0003-example.md").write_text(
                "# ADR 0003: Example\n\nStatus: Accepted\nDate: 2026-02-13\n",
                encoding="utf-8",
            )
            (adr_dir / "README.md").write_text(
                "# ADR Index\n\n| ADR | Title | Status |\n|-----|-------|--------|\n"
                "| [0001](0001-example.md) | Example | Accepted |\n"
                "| [0003](0003-example.md) | Example | Accepted |\n\n"
                "next: 0004\n",
                encoding="utf-8",
            )
            hygiene.REPO_ROOT = root

            report = hygiene._audit_adrs()

            self.assertTrue(report["errors"])
            self.assertTrue(
                any(
                    "Unexplained ADR numbering gaps" in error
                    for error in report["errors"]
                )
            )

    def test_adr_audit_allows_governed_numbering_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adr_dir = root / "dev/adr"
            adr_dir.mkdir(parents=True)
            (adr_dir / "0001-example.md").write_text(
                "# ADR 0001: Example\n\nStatus: Accepted\nDate: 2026-02-13\n",
                encoding="utf-8",
            )
            (adr_dir / "0003-example.md").write_text(
                "# ADR 0003: Example\n\nStatus: Accepted\nDate: 2026-02-13\n",
                encoding="utf-8",
            )
            (adr_dir / "README.md").write_text(
                "# ADR Index\n\n| ADR | Title | Status |\n|-----|-------|--------|\n"
                "| [0001](0001-example.md) | Example | Accepted |\n"
                "| [0003](0003-example.md) | Example | Accepted |\n\n"
                "Retired ADR IDs: 0002\n"
                "Reserved ADR IDs: none\n"
                "next: 0004\n",
                encoding="utf-8",
            )
            hygiene.REPO_ROOT = root

            report = hygiene._audit_adrs()

            self.assertFalse(
                any(
                    "Unexplained ADR numbering gaps" in error
                    for error in report["errors"]
                )
            )
            self.assertEqual(report["unexplained_gap_ids"], [])

    def test_adr_audit_flags_next_pointer_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adr_dir = root / "dev/adr"
            adr_dir.mkdir(parents=True)
            (adr_dir / "0001-example.md").write_text(
                "# ADR 0001: Example\n\nStatus: Accepted\nDate: 2026-02-13\n",
                encoding="utf-8",
            )
            (adr_dir / "README.md").write_text(
                "# ADR Index\n\n| ADR | Title | Status |\n|-----|-------|--------|\n"
                "| [0001](0001-example.md) | Example | Accepted |\n\n"
                "next: 0003\n",
                encoding="utf-8",
            )
            hygiene.REPO_ROOT = root

            report = hygiene._audit_adrs()

            self.assertTrue(report["errors"])
            self.assertTrue(
                any("next pointer mismatch" in error for error in report["errors"])
            )

    def test_adr_audit_flags_stale_reference_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adr_dir = root / "dev/adr"
            adr_dir.mkdir(parents=True)
            (adr_dir / "0001-example.md").write_text(
                "# ADR 0001: Example\n\nStatus: Accepted\nDate: 2026-02-13\n",
                encoding="utf-8",
            )
            (adr_dir / "README.md").write_text(
                "# ADR Index\n\n| ADR | Title | Status |\n|-----|-------|--------|\n"
                "| [0001](0001-example.md) | Example | Accepted |\n\n"
                "Retired ADR IDs: none\n"
                "Reserved ADR IDs: none\n"
                "next: 0002\n",
                encoding="utf-8",
            )
            theme_doc = root / "dev/active/theme_upgrade.md"
            theme_doc.parent.mkdir(parents=True)
            theme_doc.write_text(
                "Documentation snapshot: 24 ADRs shipped.\n",
                encoding="utf-8",
            )
            history_doc = root / "dev/history/ENGINEERING_EVOLUTION.md"
            history_doc.parent.mkdir(parents=True)
            history_doc.write_text(
                "See `dev/adr/0001-*.md` through `dev/adr/0023-*.md`.\n",
                encoding="utf-8",
            )
            hygiene.REPO_ROOT = root

            report = hygiene._audit_adrs()

            self.assertTrue(report["errors"])
            self.assertTrue(
                any(
                    "Stale ADR reference patterns detected" in error
                    for error in report["errors"]
                )
            )
            self.assertGreaterEqual(len(report["stale_reference_violations"]), 2)

    def test_scripts_audit_flags_undocumented_top_level_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts_dir = root / "dev/scripts"
            scripts_dir.mkdir(parents=True)
            (scripts_dir / "README.md").write_text("# Scripts\n", encoding="utf-8")
            (scripts_dir / "new_tool.sh").write_text(
                "#!/usr/bin/env bash\n", encoding="utf-8"
            )
            hygiene.REPO_ROOT = root

            report = hygiene._audit_scripts()

            self.assertTrue(report["errors"])
            self.assertIn("new_tool.sh", report["errors"][0])

    @mock.patch(
        "dev.scripts.devctl.commands.hygiene_audits.CHECK_SCRIPT_RELATIVE_PATHS",
        {"sample": "dev/scripts/checks/check_sample.py"},
    )
    def test_scripts_audit_flags_unregistered_check_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts_dir = root / "dev/scripts"
            checks_dir = scripts_dir / "checks"
            catalog_dir = scripts_dir / "devctl"
            checks_dir.mkdir(parents=True)
            catalog_dir.mkdir(parents=True)
            (catalog_dir / "script_catalog.py").write_text(
                "# catalog marker\n", encoding="utf-8"
            )
            (checks_dir / "check_sample.py").write_text(
                "#!/usr/bin/env python3\n", encoding="utf-8"
            )
            (checks_dir / "check_extra.py").write_text(
                "#!/usr/bin/env python3\n", encoding="utf-8"
            )
            (scripts_dir / "README.md").write_text(
                "dev/scripts/checks/check_sample.py\n"
                "dev/scripts/checks/check_extra.py\n",
                encoding="utf-8",
            )
            hygiene.REPO_ROOT = root

            report = hygiene._audit_scripts()

            self.assertTrue(report["errors"])
            self.assertTrue(
                any(
                    "missing from dev/scripts/devctl/script_catalog.py" in error
                    for error in report["errors"]
                )
            )
            self.assertIn(
                "dev/scripts/checks/check_extra.py",
                report["unregistered_checks"],
            )

    @mock.patch(
        "dev.scripts.devctl.commands.hygiene_audits._is_git_ignored",
        return_value=True,
    )
    def test_scripts_audit_ignores_gitignored_pycache_warning(
        self,
        _ignored_mock: mock.Mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts_dir = root / "dev/scripts"
            checks_dir = scripts_dir / "checks"
            scripts_dir.mkdir(parents=True)
            checks_dir.mkdir(parents=True)
            (scripts_dir / "README.md").write_text(
                "dev/scripts/checks/check_sample.py\n",
                encoding="utf-8",
            )
            (checks_dir / "check_sample.py").write_text(
                "#!/usr/bin/env python3\n",
                encoding="utf-8",
            )
            pycache_dir = checks_dir / "__pycache__"
            pycache_dir.mkdir(parents=True)
            (pycache_dir / "cache.pyc").write_bytes(b"cache")
            hygiene.REPO_ROOT = root

            report = hygiene._audit_scripts()

            self.assertIn("dev/scripts/checks/__pycache__", report["pycache_dirs"])
            self.assertIn(
                "dev/scripts/checks/__pycache__",
                report["ignored_pycache_dirs"],
            )
            self.assertFalse(report["actionable_pycache_dirs"])
            self.assertFalse(
                any(
                    "Python cache directories present in repo tree" in warning
                    for warning in report["warnings"]
                )
            )

    def test_hygiene_parser_accepts_fix_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["hygiene", "--fix"])
        self.assertTrue(args.fix)

    def test_hygiene_parser_accepts_strict_warnings_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["hygiene", "--strict-warnings"])
        self.assertTrue(args.strict_warnings)

    def test_fix_pycache_dirs_removes_detected_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts_dir = root / "dev/scripts"
            scripts_dir.mkdir(parents=True)
            (scripts_dir / "README.md").write_text("# Scripts\n", encoding="utf-8")
            pycache_dir = scripts_dir / "__pycache__"
            pycache_dir.mkdir(parents=True)
            (pycache_dir / "cache.pyc").write_bytes(b"cache")
            hygiene.REPO_ROOT = root

            scripts_report = hygiene._audit_scripts()
            fix_report = hygiene._fix_pycache_dirs(scripts_report["pycache_dirs"])

            self.assertIn("dev/scripts/__pycache__", fix_report["removed"])
            self.assertFalse(fix_report["failed"])
            self.assertFalse(pycache_dir.exists())

    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._scan_voiceterm_test_processes",
        return_value=([], []),
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene.build_reports_hygiene_guard",
        return_value={
            "reports_root": "dev/reports",
            "reports_root_exists": True,
            "managed_run_dirs": 0,
            "candidate_count": 0,
            "candidate_reclaim_bytes": 0,
            "candidate_reclaim_human": "0 B",
            "warnings": [],
            "errors": [],
            "subroots": [],
        },
    )
    @mock.patch("dev.scripts.devctl.commands.hygiene.write_output")
    def test_run_with_fix_clears_pycache_warning(
        self,
        write_output_mock: mock.Mock,
        _reports_guard_mock: mock.Mock,
        _scan_mock: mock.Mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts_dir = root / "dev/scripts"
            scripts_dir.mkdir(parents=True)
            (scripts_dir / "README.md").write_text(
                "# Developer Scripts\n\ndev/scripts/checks/check_sample.py\n",
                encoding="utf-8",
            )
            (scripts_dir / "check_sample.py").write_text(
                "#!/usr/bin/env python3\n", encoding="utf-8"
            )
            checks_dir = scripts_dir / "checks"
            checks_dir.mkdir(parents=True)
            (checks_dir / "check_sample.py").write_text(
                "#!/usr/bin/env python3\n", encoding="utf-8"
            )
            pycache_dir = scripts_dir / "__pycache__"
            pycache_dir.mkdir(parents=True)
            (pycache_dir / "cache.pyc").write_bytes(b"cache")

            archive_dir = root / "dev/archive"
            archive_dir.mkdir(parents=True)
            (archive_dir / "README.md").write_text("# Archive\n", encoding="utf-8")

            adr_dir = root / "dev/adr"
            adr_dir.mkdir(parents=True)
            (adr_dir / "README.md").write_text("# ADR Index\n", encoding="utf-8")
            hygiene.REPO_ROOT = root

            args = SimpleNamespace(
                fix=True,
                format="json",
                output=None,
                pipe_command=None,
                pipe_args=None,
            )
            rc = hygiene.run(args)

            self.assertEqual(rc, 0)
            payload = json.loads(write_output_mock.call_args.args[0])
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["fix"]["requested"])
            self.assertEqual(payload["warning_count"], 0)
            self.assertIn("dev/scripts/__pycache__", payload["fix"]["removed"])
            self.assertFalse(pycache_dir.exists())

    @mock.patch("dev.scripts.devctl.commands.hygiene._scan_voiceterm_test_processes")
    def test_runtime_process_audit_flags_orphaned_voiceterm_test_binary(
        self, scan_mock: mock.Mock
    ) -> None:
        scan_mock.return_value = (
            [
                {
                    "pid": 1234,
                    "ppid": 1,
                    "etime": "05:00",
                    "elapsed_seconds": 300,
                    "command": "/tmp/project/target/debug/deps/voiceterm-deadbeef --test-threads=4",
                }
            ],
            [],
        )

        report = hygiene._audit_runtime_processes()

        self.assertEqual(report["total_detected"], 1)
        self.assertTrue(report["errors"])
        self.assertIn("Orphaned voiceterm test processes detected", report["errors"][0])

    @mock.patch("dev.scripts.devctl.commands.hygiene._scan_voiceterm_test_processes")
    def test_runtime_process_audit_warns_for_active_test_binary(
        self, scan_mock: mock.Mock
    ) -> None:
        scan_mock.return_value = (
            [
                {
                    "pid": 2222,
                    "ppid": 777,
                    "etime": "00:10",
                    "elapsed_seconds": 10,
                    "command": "/tmp/project/target/debug/deps/voiceterm-deadbeef",
                }
            ],
            [],
        )

        report = hygiene._audit_runtime_processes()

        self.assertEqual(report["total_detected"], 1)
        self.assertFalse(report["errors"])
        self.assertTrue(report["warnings"])
        self.assertIn("Active voiceterm test processes detected", report["warnings"][0])

    @mock.patch("dev.scripts.devctl.commands.hygiene._scan_voiceterm_test_processes")
    def test_runtime_process_audit_errors_for_stale_active_test_binary(
        self, scan_mock: mock.Mock
    ) -> None:
        scan_mock.return_value = (
            [
                {
                    "pid": 3333,
                    "ppid": 777,
                    "etime": "15:00",
                    "elapsed_seconds": 900,
                    "command": "/tmp/project/target/debug/deps/voiceterm-feedface",
                }
            ],
            [],
        )

        report = hygiene._audit_runtime_processes()

        self.assertEqual(report["total_detected"], 1)
        self.assertTrue(report["errors"])
        self.assertIn(
            "Stale active voiceterm test processes detected", report["errors"][0]
        )

    @mock.patch("dev.scripts.devctl.commands.hygiene._scan_voiceterm_test_processes")
    def test_runtime_process_audit_warns_when_ps_unavailable(
        self, scan_mock: mock.Mock
    ) -> None:
        scan_mock.return_value = (
            [],
            ["Process sweep skipped: unable to execute ps (blocked)"],
        )
        with mock.patch.dict("os.environ", {"CI": ""}, clear=False):
            report = hygiene._audit_runtime_processes()

        self.assertEqual(report["total_detected"], 0)
        self.assertFalse(report["errors"])
        self.assertTrue(report["warnings"])
        self.assertIn("Process sweep skipped", report["warnings"][0])

    @mock.patch("dev.scripts.devctl.commands.hygiene._scan_voiceterm_test_processes")
    def test_runtime_process_audit_ignores_sandbox_ps_permission_warning(
        self, scan_mock: mock.Mock
    ) -> None:
        scan_mock.return_value = (
            [],
            [
                "Process sweep skipped: unable to execute ps ([Errno 1] Operation not permitted: 'ps')"
            ],
        )
        with mock.patch.dict("os.environ", {"CI": ""}, clear=False):
            report = hygiene._audit_runtime_processes()

        self.assertEqual(report["total_detected"], 0)
        self.assertFalse(report["errors"])
        self.assertFalse(report["warnings"])

    @mock.patch("dev.scripts.devctl.commands.hygiene._scan_voiceterm_test_processes")
    def test_runtime_process_audit_errors_when_ps_unavailable_in_ci(
        self, scan_mock: mock.Mock
    ) -> None:
        scan_mock.return_value = (
            [],
            ["Process sweep skipped: unable to execute ps (blocked)"],
        )
        with mock.patch.dict("os.environ", {"CI": "true"}, clear=False):
            report = hygiene._audit_runtime_processes()

        self.assertEqual(report["total_detected"], 0)
        self.assertTrue(report["errors"])
        self.assertIn("Runtime process sweep unavailable in CI", report["errors"][0])

    @mock.patch("dev.scripts.devctl.commands.hygiene.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene.build_reports_hygiene_guard",
        return_value={
            "reports_root": "dev/reports",
            "reports_root_exists": True,
            "managed_run_dirs": 220,
            "candidate_count": 35,
            "candidate_reclaim_bytes": 1048576,
            "candidate_reclaim_human": "1.0 MB",
            "warnings": [
                "Report retention drift: run reports-cleanup --dry-run to review stale artifacts."
            ],
            "errors": [],
            "subroots": [],
        },
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._scan_voiceterm_test_processes",
        return_value=([], []),
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._audit_scripts",
        return_value={
            "top_level_scripts": [],
            "check_scripts": [],
            "pycache_dirs": [],
            "warnings": [],
            "errors": [],
        },
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._audit_adrs",
        return_value={"total_adrs": 0, "warnings": [], "errors": []},
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._audit_archive",
        return_value={"total_entries": 0, "warnings": [], "errors": []},
    )
    def test_hygiene_includes_reports_retention_warning(
        self,
        _archive_mock: mock.Mock,
        _adr_mock: mock.Mock,
        _scripts_mock: mock.Mock,
        _scan_mock: mock.Mock,
        _reports_mock: mock.Mock,
        write_output_mock: mock.Mock,
    ) -> None:
        args = SimpleNamespace(
            fix=False,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        rc = hygiene.run(args)

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertIn("reports", payload)
        self.assertEqual(payload["reports"]["candidate_count"], 35)
        self.assertGreaterEqual(payload["warning_count"], 1)
        self.assertIn("reports-cleanup", payload["reports"]["warnings"][0])

    @mock.patch("dev.scripts.devctl.commands.hygiene.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene.build_reports_hygiene_guard",
        return_value={
            "reports_root": "dev/reports",
            "reports_root_exists": True,
            "managed_run_dirs": 220,
            "candidate_count": 35,
            "candidate_reclaim_bytes": 1048576,
            "candidate_reclaim_human": "1.0 MB",
            "warnings": [
                "Report retention drift: run reports-cleanup --dry-run to review stale artifacts."
            ],
            "errors": [],
            "subroots": [],
        },
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._scan_voiceterm_test_processes",
        return_value=([], []),
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._audit_scripts",
        return_value={
            "top_level_scripts": [],
            "check_scripts": [],
            "pycache_dirs": [],
            "warnings": [],
            "errors": [],
        },
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._audit_adrs",
        return_value={"total_adrs": 0, "warnings": [], "errors": []},
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._audit_archive",
        return_value={"total_entries": 0, "warnings": [], "errors": []},
    )
    def test_hygiene_strict_warnings_promotes_warnings_to_failure(
        self,
        _archive_mock: mock.Mock,
        _adr_mock: mock.Mock,
        _scripts_mock: mock.Mock,
        _scan_mock: mock.Mock,
        _reports_mock: mock.Mock,
        write_output_mock: mock.Mock,
    ) -> None:
        args = SimpleNamespace(
            fix=False,
            strict_warnings=True,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        rc = hygiene.run(args)

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["strict_warnings"])
        self.assertGreaterEqual(payload["warning_count"], 1)
        self.assertEqual(payload["warning_fail_count"], payload["warning_count"])

    @mock.patch("dev.scripts.devctl.commands.hygiene.write_output")
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene.build_reports_hygiene_guard",
        return_value={
            "reports_root": "dev/reports",
            "reports_root_exists": True,
            "managed_run_dirs": 0,
            "candidate_count": 0,
            "candidate_reclaim_bytes": 0,
            "candidate_reclaim_human": "0 B",
            "warnings": [],
            "errors": [],
            "subroots": [],
        },
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._scan_voiceterm_test_processes",
        return_value=([], []),
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._audit_scripts",
        return_value={
            "top_level_scripts": [],
            "check_scripts": [],
            "pycache_dirs": [],
            "warnings": [],
            "errors": [],
        },
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._audit_adrs",
        return_value={
            "total_adrs": 26,
            "missing_sequence_ids": ["0018", "0020", "0027"],
            "retired_ids": ["0018", "0020"],
            "reserved_ids": ["0027"],
            "backlog_master_ids": ["0027", "0028"],
            "backlog_autonomy_ids": ["0027", "0028"],
            "next_pointer_value": "0037",
            "next_pointer_expected": "0037",
            "warnings": [],
            "errors": [],
        },
    )
    @mock.patch(
        "dev.scripts.devctl.commands.hygiene._audit_archive",
        return_value={"total_entries": 0, "warnings": [], "errors": []},
    )
    def test_hygiene_markdown_includes_adr_numbering_context(
        self,
        _archive_mock: mock.Mock,
        _adr_mock: mock.Mock,
        _scripts_mock: mock.Mock,
        _scan_mock: mock.Mock,
        _reports_mock: mock.Mock,
        write_output_mock: mock.Mock,
    ) -> None:
        args = SimpleNamespace(
            fix=False,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        rc = hygiene.run(args)

        self.assertEqual(rc, 0)
        output = write_output_mock.call_args.args[0]
        self.assertIn("- missing_sequence_ids: 0018, 0020, 0027", output)
        self.assertIn("- retired_ids: 0018, 0020", output)
        self.assertIn("- reserved_ids: 0027", output)
        self.assertIn("- backlog_master_ids: 0027, 0028", output)
        self.assertIn("- next_pointer: 0037 (expected 0037)", output)


if __name__ == "__main__":
    unittest.main()
