"""Unit tests for IDE/provider isolation guard script."""

from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import sys
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_ide_provider_isolation.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("check_ide_provider_isolation_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_ide_provider_isolation.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckIdeProviderIsolationTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def _run_main_json(self, *argv: str) -> tuple[int, dict]:
        buffer = io.StringIO()
        with patch.object(sys, "argv", ["check_ide_provider_isolation.py", *argv]):
            with redirect_stdout(buffer):
                exit_code = self.script.main()
        return exit_code, json.loads(buffer.getvalue())

    def test_scan_text_counts_host_provider_and_mixed_signals(self) -> None:
        text = "\n".join(
            [
                "// comment-only line should be ignored",
                "let host = TerminalHost::Cursor;",
                "if matches!(backend, BackendFamily::Claude) {",
                "    apply(TerminalFamily::JetBrains, BackendFamily::Codex);",
                "}",
            ]
        )
        result = self.script._scan_text("rust/src/bin/voiceterm/example.rs", text)
        self.assertEqual(result["host_signal_lines"], 2)
        self.assertEqual(result["provider_signal_lines"], 2)
        self.assertEqual(result["mixed_signal_lines"], 1)
        self.assertEqual(result["mixed_line_numbers"], [4])

    def test_allowlist_matches_runtime_hotspot_prefixes(self) -> None:
        self.assertTrue(
            self.script._is_allowlisted_mixed_path("rust/src/bin/voiceterm/writer/state.rs")
        )
        self.assertTrue(
            self.script._is_allowlisted_mixed_path(
                "rust/src/bin/voiceterm/event_loop/output_dispatch.rs"
            )
        )
        self.assertTrue(
            self.script._is_allowlisted_mixed_path("rust/src/bin/voiceterm/event_loop.rs")
        )
        self.assertTrue(
            self.script._is_allowlisted_mixed_path("rust/src/bin/voiceterm/terminal.rs")
        )
        self.assertFalse(
            self.script._is_allowlisted_mixed_path("rust/src/bin/voiceterm/theme/detect.rs")
        )

    def test_scan_text_detects_multiline_statement_coupling(self) -> None:
        text = "\n".join(
            [
                "if BackendFamily::from_label(backend_label) == BackendFamily::Claude",
                "    && runtime_compat::detect_terminal_host() == TerminalHost::Cursor {",
                "    keep_status_line();",
                "}",
            ]
        )
        result = self.script._scan_text("rust/src/bin/voiceterm/event_loop.rs", text)
        self.assertEqual(result["mixed_signal_lines"], 1)
        self.assertEqual(result["mixed_line_numbers"], [1])

    def test_report_only_mode_returns_success_with_violations(self) -> None:
        fake_result = {
            "file": "rust/src/bin/voiceterm/terminal.rs",
            "host_signal_lines": 1,
            "provider_signal_lines": 1,
            "mixed_signal_lines": 1,
            "mixed_line_numbers": [12],
        }
        with patch.object(
            self.script,
            "_iter_source_paths",
            return_value=[REPO_ROOT / "rust/src/bin/voiceterm/terminal.rs"],
        ), patch.object(
            self.script,
            "_scan_text",
            return_value=fake_result,
        ), patch.object(
            self.script,
            "_is_allowlisted_mixed_path",
            return_value=False,
        ):
            code, report = self._run_main_json("--format", "json")
        self.assertEqual(code, 0)
        self.assertTrue(report["ok"])
        self.assertEqual(report["mode"], "report-only")
        self.assertEqual(report["unauthorized_files"], 1)

    def test_blocking_mode_fails_on_unauthorized_violations(self) -> None:
        fake_result = {
            "file": "rust/src/bin/voiceterm/terminal.rs",
            "host_signal_lines": 1,
            "provider_signal_lines": 1,
            "mixed_signal_lines": 1,
            "mixed_line_numbers": [12],
        }
        with patch.object(
            self.script,
            "_iter_source_paths",
            return_value=[REPO_ROOT / "rust/src/bin/voiceterm/terminal.rs"],
        ), patch.object(
            self.script,
            "_scan_text",
            return_value=fake_result,
        ), patch.object(
            self.script,
            "_is_allowlisted_mixed_path",
            return_value=False,
        ):
            code, report = self._run_main_json("--fail-on-violations", "--format", "json")
        self.assertEqual(code, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["mode"], "blocking")
