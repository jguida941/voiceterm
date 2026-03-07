"""Unit tests for periodic jscpd duplication-audit wrapper."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.config import REPO_ROOT

SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_duplication_audit.py"


def _load_script_module():
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(
        "check_duplication_audit_script", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_duplication_audit.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_report(path: Path, *, percent: float, duplicates: int = 0) -> None:
    payload = {
        "statistics": {"total": {"percentage": percent}},
        "duplicates": [{} for _ in range(duplicates)],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class CheckDuplicationAuditTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def _run(self, *argv: str) -> tuple[int, dict]:
        out = io.StringIO()
        with patch.object(
            sys, "argv", ["check_duplication_audit.py", "--format", "json", *argv]
        ):
            with redirect_stdout(out):
                exit_code = self.script.main()
        return exit_code, json.loads(out.getvalue())

    def test_missing_report_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            report_path = Path(temp_dir) / "missing.json"
            exit_code, report = self._run("--report-path", str(report_path))

        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "missing_report")
        self.assertFalse(report["blocked_by_tooling"])
        self.assertTrue(any("missing report file" in err for err in report["errors"]))
        self.assertEqual(report["jscpd_status"], "not_requested")

    def test_duplication_percent_threshold_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            report_path = Path(temp_dir) / "dup.json"
            _write_report(report_path, percent=25.0, duplicates=3)
            exit_code, report = self._run(
                "--report-path",
                str(report_path),
                "--max-duplication-percent",
                "10.0",
            )

        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertTrue(
            any(
                "duplication percent exceeds threshold" in err
                for err in report["errors"]
            )
        )

    def test_fresh_report_passes(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            report_path = Path(temp_dir) / "dup.json"
            _write_report(report_path, percent=2.5, duplicates=1)
            exit_code, report = self._run(
                "--report-path",
                str(report_path),
                "--max-duplication-percent",
                "10.0",
            )

        self.assertEqual(exit_code, 0)
        self.assertTrue(report["ok"])
        self.assertEqual(report["status"], "ok")
        self.assertFalse(report["blocked_by_tooling"])
        self.assertEqual(report["duplication_percent"], 2.5)
        self.assertEqual(report["duplicates_count"], 1)
        self.assertEqual(report["jscpd_status"], "not_requested")

    def test_run_jscpd_missing_binary_fails(self) -> None:
        script = self.script
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            report_path = Path(temp_dir) / "dup.json"
            _write_report(report_path, percent=1.0, duplicates=0)
            out = io.StringIO()
            with patch.object(script.shutil, "which", return_value=None), patch.object(
                sys,
                "argv",
                [
                    "check_duplication_audit.py",
                    "--format",
                    "json",
                    "--run-jscpd",
                    "--report-path",
                    str(report_path),
                    "--jscpd-bin",
                    "jscpd",
                ],
            ):
                with redirect_stdout(out):
                    exit_code = script.main()
            report = json.loads(out.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "error")
        self.assertFalse(report["blocked_by_tooling"])
        self.assertTrue(
            any("jscpd binary not found" in err for err in report["errors"])
        )
        self.assertTrue(any("--allow-missing-tool" in err for err in report["errors"]))
        self.assertEqual(report["jscpd_status"], "missing_tool")

    def test_run_jscpd_missing_binary_warns_when_allow_missing_tool(self) -> None:
        script = self.script
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            report_path = Path(temp_dir) / "dup.json"
            _write_report(report_path, percent=1.0, duplicates=0)
            out = io.StringIO()
            with patch.object(script.shutil, "which", return_value=None), patch.object(
                sys,
                "argv",
                [
                    "check_duplication_audit.py",
                    "--format",
                    "json",
                    "--run-jscpd",
                    "--allow-missing-tool",
                    "--report-path",
                    str(report_path),
                    "--jscpd-bin",
                    "jscpd",
                ],
            ):
                with redirect_stdout(out):
                    exit_code = script.main()
            report = json.loads(out.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertTrue(report["ok"])
        self.assertEqual(report["status"], "ok_with_warnings")
        self.assertFalse(report["blocked_by_tooling"])
        self.assertEqual(report["errors"], [])
        self.assertTrue(
            any("jscpd binary not found" in warning for warning in report["warnings"])
        )
        self.assertEqual(report["jscpd_status"], "missing_tool")

    def test_allow_missing_tool_does_not_hide_missing_report_failure(self) -> None:
        script = self.script
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            report_path = Path(temp_dir) / "missing.json"
            out = io.StringIO()
            with patch.object(script.shutil, "which", return_value=None), patch.object(
                sys,
                "argv",
                [
                    "check_duplication_audit.py",
                    "--format",
                    "json",
                    "--run-jscpd",
                    "--allow-missing-tool",
                    "--report-path",
                    str(report_path),
                    "--jscpd-bin",
                    "jscpd",
                ],
            ):
                with redirect_stdout(out):
                    exit_code = script.main()
            report = json.loads(out.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "blocked_by_tooling")
        self.assertTrue(report["blocked_by_tooling"])
        self.assertTrue(any("missing report file" in err for err in report["errors"]))
        self.assertTrue(
            any("jscpd binary not found" in warning for warning in report["warnings"])
        )
        self.assertEqual(report["jscpd_status"], "missing_tool")

    def test_run_python_fallback_generates_report_when_jscpd_missing(self) -> None:
        script = self.script
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            source_root = Path(temp_dir) / "src"
            source_root.mkdir(parents=True, exist_ok=True)
            (source_root / "a.rs").write_text(
                "\n".join(f"line-{index:03d}" for index in range(60)) + "\n",
                encoding="utf-8",
            )
            report_path = Path(temp_dir) / "dup.json"
            out = io.StringIO()
            with patch.object(script.shutil, "which", return_value=None), patch.object(
                sys,
                "argv",
                [
                    "check_duplication_audit.py",
                    "--format",
                    "json",
                    "--run-jscpd",
                    "--allow-missing-tool",
                    "--run-python-fallback",
                    "--source-root",
                    str(source_root),
                    "--report-path",
                    str(report_path),
                    "--jscpd-bin",
                    "jscpd",
                ],
            ):
                with redirect_stdout(out):
                    exit_code = script.main()
            report = json.loads(out.getvalue())
            report_exists_on_disk = report_path.exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(report["ok"])
        self.assertEqual(report["status"], "ok_with_warnings")
        self.assertFalse(report["blocked_by_tooling"])
        self.assertTrue(report["report_exists"])
        self.assertEqual(report["jscpd_status"], "python_fallback")
        self.assertGreaterEqual(report["duplication_percent"], 0.0)
        self.assertTrue(report_exists_on_disk)

    def test_run_python_fallback_obeys_duplication_threshold(self) -> None:
        script = self.script
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            source_root = Path(temp_dir) / "src"
            source_root.mkdir(parents=True, exist_ok=True)
            shared = "\n".join(f"shared-{index:02d}" for index in range(12)) + "\n"
            (source_root / "a.rs").write_text(shared + "tail-a\n", encoding="utf-8")
            (source_root / "b.rs").write_text(shared + "tail-b\n", encoding="utf-8")
            report_path = Path(temp_dir) / "dup.json"
            out = io.StringIO()
            with patch.object(script.shutil, "which", return_value=None), patch.object(
                sys,
                "argv",
                [
                    "check_duplication_audit.py",
                    "--format",
                    "json",
                    "--run-jscpd",
                    "--allow-missing-tool",
                    "--run-python-fallback",
                    "--source-root",
                    str(source_root),
                    "--report-path",
                    str(report_path),
                    "--max-duplication-percent",
                    "1.0",
                    "--jscpd-bin",
                    "jscpd",
                ],
            ):
                with redirect_stdout(out):
                    exit_code = script.main()
            report = json.loads(out.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "duplication_threshold_exceeded")
        self.assertFalse(report["blocked_by_tooling"])
        self.assertEqual(report["jscpd_status"], "python_fallback")
        self.assertTrue(
            any(
                "duplication percent exceeds threshold" in err
                for err in report["errors"]
            )
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
