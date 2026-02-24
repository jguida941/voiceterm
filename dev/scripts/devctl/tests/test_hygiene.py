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

    def test_hygiene_parser_accepts_fix_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["hygiene", "--fix"])
        self.assertTrue(args.fix)

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
    @mock.patch("dev.scripts.devctl.commands.hygiene.write_output")
    def test_run_with_fix_clears_pycache_warning(
        self,
        write_output_mock: mock.Mock,
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
        self.assertIn("Orphaned voiceterm test binaries detected", report["errors"][0])

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
        self.assertIn("Active voiceterm test binaries detected", report["warnings"][0])

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
            "Stale active voiceterm test binaries detected", report["errors"][0]
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


if __name__ == "__main__":
    unittest.main()
