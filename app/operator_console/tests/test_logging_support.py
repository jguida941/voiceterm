from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.operator_console.logging_support import (
    OperatorConsoleDiagnostics,
    build_log_paths,
    sanitize_timestamp,
)
from app.operator_console.run import build_parser


class LoggingSupportTests(unittest.TestCase):
    def test_build_log_paths_creates_session_and_latest_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = build_log_paths(
                root,
                root_rel="logs/root",
                timestamp_utc="2026-03-08T21:03:04Z",
            )

        self.assertEqual(paths.session_dir.name, "20260308T210304Z")
        self.assertEqual(paths.root_dir, root / "logs/root")
        self.assertEqual(paths.latest_log_path.name, "latest.operator_console.log")

    def test_operator_console_diagnostics_persists_events_and_raw_command_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            diagnostics = OperatorConsoleDiagnostics.create(root, enabled=True)
            rendered = diagnostics.log(
                level="INFO",
                event="startup",
                message="Operator Console launched",
                details={"repo_root": root, "dev_log": True},
            )
            diagnostics.append_command_output(
                stream_name="stdout",
                text="ok: true\nbridge_active: true\n",
            )

            self.assertIsNotNone(diagnostics.paths)
            latest_log = diagnostics.paths.latest_log_path.read_text(encoding="utf-8")
            latest_events = diagnostics.paths.latest_events_path.read_text(
                encoding="utf-8"
            )
            latest_command_output = diagnostics.paths.latest_command_output_path.read_text(
                encoding="utf-8"
            )

        self.assertIn("startup", rendered)
        self.assertIn("Operator Console launched", latest_log)
        event_line = json.loads(latest_events.strip())
        self.assertEqual(event_line["event"], "startup")
        self.assertEqual(event_line["details"]["dev_log"], True)
        self.assertIn("[STDOUT]", latest_command_output)
        self.assertIn("bridge_active: true", latest_command_output)

    def test_operator_console_diagnostics_disabled_mode_stays_memory_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            diagnostics = OperatorConsoleDiagnostics.create(root, enabled=False)
            diagnostics.log(
                level="INFO",
                event="startup",
                message="Operator Console launched",
            )

        self.assertIsNone(diagnostics.paths)
        self.assertIn("memory-only", diagnostics.destination_summary)

    def test_sanitize_timestamp_removes_filesystem_unsafe_characters(self) -> None:
        sanitized = sanitize_timestamp("2026-03-08T21:03:04.123456Z")
        self.assertEqual(sanitized, "20260308T210304123456Z")


class RunParserTests(unittest.TestCase):
    def test_build_parser_defaults_to_saved_or_default_theme(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])

        self.assertIsNone(args.theme)

    def test_build_parser_supports_dev_log_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--dev-log", "--log-dir", "custom/logs"])

        self.assertTrue(args.dev_log)
        self.assertEqual(args.log_dir, "custom/logs")

    def test_build_parser_supports_pyqt_bootstrap_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--ensure-pyqt6"])

        self.assertTrue(args.ensure_pyqt6)

    def test_build_parser_supports_layout_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--layout", "analytics"])

        self.assertEqual(args.layout, "analytics")

    @patch("app.operator_console.views.main_window.OperatorConsoleWindow")
    @patch("app.operator_console.views.main_window.get_engine")
    @patch("app.operator_console.views.main_window.QApplication")
    def test_run_uses_saved_theme_when_cli_theme_is_omitted(
        self,
        app_mock,
        get_engine_mock,
        window_mock,
    ) -> None:
        from app.operator_console.views.main_window import run as run_window

        app = MagicMock()
        app.exec.return_value = 0
        app_mock.instance.return_value = app

        engine = MagicMock()
        engine.load_saved.return_value = True
        engine.generate_stylesheet.return_value = "sheet"
        get_engine_mock.return_value = engine

        repo_root = Path("/tmp/mock-repo")
        diagnostics = MagicMock()

        result = run_window(
            repo_root,
            diagnostics=diagnostics,
            theme_id=None,
        )

        self.assertEqual(result, 0)
        engine.load_saved.assert_called_once_with()
        engine.apply_builtin_theme.assert_not_called()
        engine.save_current.assert_not_called()
        app.setStyleSheet.assert_called_once_with("sheet")
        self.assertIsNone(window_mock.call_args.kwargs["theme_id"])

    @patch("app.operator_console.views.main_window.OperatorConsoleWindow")
    @patch("app.operator_console.views.main_window.get_engine")
    @patch("app.operator_console.views.main_window.QApplication")
    def test_run_persists_explicit_builtin_theme_override(
        self,
        app_mock,
        get_engine_mock,
        window_mock,
    ) -> None:
        from app.operator_console.views.main_window import run as run_window

        app = MagicMock()
        app.exec.return_value = 0
        app_mock.instance.return_value = app

        engine = MagicMock()
        engine.generate_stylesheet.return_value = "sheet"
        get_engine_mock.return_value = engine

        repo_root = Path("/tmp/mock-repo")
        diagnostics = MagicMock()

        result = run_window(
            repo_root,
            diagnostics=diagnostics,
            theme_id="claude",
        )

        self.assertEqual(result, 0)
        engine.load_saved.assert_not_called()
        engine.apply_builtin_theme.assert_called_once_with("claude")
        engine.save_current.assert_called_once_with()
        app.setStyleSheet.assert_called_once_with("sheet")
        self.assertEqual(window_mock.call_args.kwargs["theme_id"], "claude")

    @patch("app.operator_console.views.main_window.OperatorConsoleWindow")
    @patch("app.operator_console.views.main_window.get_engine")
    @patch("app.operator_console.views.main_window.QApplication")
    def test_run_passes_explicit_layout_mode(
        self,
        app_mock,
        get_engine_mock,
        window_mock,
    ) -> None:
        from app.operator_console.views.main_window import run as run_window

        app = MagicMock()
        app.exec.return_value = 0
        app_mock.instance.return_value = app

        engine = MagicMock()
        engine.load_saved.return_value = True
        engine.generate_stylesheet.return_value = "sheet"
        get_engine_mock.return_value = engine

        repo_root = Path("/tmp/mock-repo")
        diagnostics = MagicMock()

        result = run_window(
            repo_root,
            diagnostics=diagnostics,
            layout_mode="analytics",
        )

        self.assertEqual(result, 0)
        self.assertEqual(window_mock.call_args.kwargs["layout_mode"], "analytics")

    def test_direct_script_invocation_bootstraps_repo_root(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        run_script = repo_root / "app/operator_console/run.py"
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)

        result = subprocess.run(
            [sys.executable, str(run_script), "--help"],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("VoiceTerm Operator Console", result.stdout)
        self.assertIn("Themes", result.stdout)
        self.assertIn("Resources", result.stdout)


if __name__ == "__main__":
    unittest.main()
