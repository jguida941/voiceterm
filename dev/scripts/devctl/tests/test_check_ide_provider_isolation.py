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
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
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

    def test_allowlist_matches_narrow_runtime_policy_paths(self) -> None:
        self.assertTrue(
            self.script._is_allowlisted_mixed_path(
                "rust/src/bin/voiceterm/runtime_compat.rs"
            )
        )
        self.assertTrue(
            self.script._is_allowlisted_mixed_path(
                "rust/src/bin/voiceterm/writer/state/profile.rs"
            )
        )
        self.assertTrue(
            self.script._is_allowlisted_mixed_path("rust/src/bin/voiceterm/writer/timing.rs")
        )
        self.assertFalse(
            self.script._is_allowlisted_mixed_path("rust/src/bin/voiceterm/event_loop.rs")
        )
        self.assertFalse(
            self.script._is_allowlisted_mixed_path("rust/src/bin/voiceterm/terminal.rs")
        )
        self.assertFalse(
            self.script._is_allowlisted_mixed_path("rust/src/bin/voiceterm/writer/state.rs")
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

    def test_scan_text_detects_host_enum_plus_provider_backend_flag(self) -> None:
        text = "\n".join(
            [
                "let should_refresh = self.terminal_family() == TerminalHost::Cursor && claude_backend;",
                "let plain_cursor_line = cursor_visible;",
            ]
        )
        result = self.script._scan_text("rust/src/bin/voiceterm/writer/state.rs", text)
        self.assertEqual(result["host_signal_lines"], 1)
        self.assertEqual(result["provider_signal_lines"], 1)
        self.assertEqual(result["mixed_signal_lines"], 1)
        self.assertEqual(result["mixed_line_numbers"], [1])

    def test_scan_text_detects_host_enum_plus_provider_helper(self) -> None:
        text = "\n".join(
            [
                "if terminal_host == TerminalHost::JetBrains && is_claude_backend() {",
                "    redraw_status();",
                "}",
            ]
        )
        result = self.script._scan_text("rust/src/bin/voiceterm/writer/state.rs", text)
        self.assertEqual(result["mixed_signal_lines"], 1)
        self.assertEqual(result["mixed_line_numbers"], [1])

    def test_scan_text_detects_split_statement_file_signal_coupling(self) -> None:
        text = "\n".join(
            [
                "let host = runtime_compat::detect_terminal_host();",
                "let provider = is_aider_backend_label(backend_label);",
            ]
        )
        result = self.script._scan_text("rust/src/bin/voiceterm/example.rs", text)
        self.assertEqual(result["mixed_signal_lines"], 0)
        self.assertTrue(result["file_signal_coupling"])
        self.assertEqual(result["host_signal_lines"], 1)
        self.assertEqual(result["provider_signal_lines"], 1)

    def test_scan_text_ignores_claude_hud_debug_literal_without_provider_signal(self) -> None:
        text = "\n".join(
            [
                'log_debug("[claude-hud-debug] transition observed");',
                "let host = TerminalHost::Cursor;",
            ]
        )
        result = self.script._scan_text("rust/src/bin/voiceterm/example.rs", text)
        self.assertEqual(result["provider_signal_lines"], 0)
        self.assertFalse(result["file_signal_coupling"])

    def test_scan_text_ignores_backend_default_assignment_literal(self) -> None:
        text = "\n".join(
            [
                'let backend = "codex".to_string();',
                "let host = TerminalHost::Cursor;",
            ]
        )
        result = self.script._scan_text("rust/src/bin/voiceterm/example.rs", text)
        self.assertEqual(result["provider_signal_lines"], 0)
        self.assertFalse(result["file_signal_coupling"])

    def test_scan_text_ignores_multiline_use_blocks(self) -> None:
        text = "\n".join(
            [
                "use crate::runtime_compat::{",
                "    BackendFamily,",
                "    TerminalHost,",
                "};",
                "let signal = TerminalHost::Cursor;",
            ]
        )
        result = self.script._scan_text("rust/src/bin/voiceterm/example.rs", text)
        self.assertEqual(result["host_signal_lines"], 1)
        self.assertEqual(result["provider_signal_lines"], 0)
        self.assertEqual(result["mixed_signal_lines"], 0)

    def test_scan_text_ignores_cfg_test_blocks(self) -> None:
        text = "\n".join(
            [
                "#[cfg(test)]",
                "mod tests {",
                "    fn fake() {",
                "        let _ = BackendFamily::Claude == BackendFamily::Claude",
                "            && TerminalHost::Cursor == TerminalHost::Cursor;",
                "    }",
                "}",
                "let prod_only = TerminalHost::Cursor;",
            ]
        )
        result = self.script._scan_text("rust/src/bin/voiceterm/example.rs", text)
        self.assertEqual(result["host_signal_lines"], 1)
        self.assertEqual(result["provider_signal_lines"], 0)
        self.assertEqual(result["mixed_signal_lines"], 0)

    def test_scan_text_ignores_cfg_test_multiline_signature_block(self) -> None:
        text = "\n".join(
            [
                "#[cfg(test)]",
                "fn fixture(",
                "    backend: BackendFamily,",
                "    host: TerminalHost,",
                ") -> bool",
                "where",
                "    BackendFamily: Copy,",
                "{",
                "    matches!(backend, BackendFamily::Claude) && host == TerminalHost::Cursor",
                "}",
                "let prod_only = TerminalHost::Cursor;",
            ]
        )
        result = self.script._scan_text("rust/src/bin/voiceterm/example.rs", text)
        self.assertEqual(result["host_signal_lines"], 1)
        self.assertEqual(result["provider_signal_lines"], 0)
        self.assertEqual(result["mixed_signal_lines"], 0)

    def test_scan_text_ignores_cfg_any_test_blocks(self) -> None:
        text = "\n".join(
            [
                '#[cfg(any(test, feature = "mutants"))]',
                "mod tests {",
                "    fn fake() {",
                "        let _ = BackendFamily::Claude == BackendFamily::Claude",
                "            && TerminalHost::Cursor == TerminalHost::Cursor;",
                "    }",
                "}",
                "let prod_only = TerminalHost::Cursor;",
            ]
        )
        result = self.script._scan_text("rust/src/bin/voiceterm/example.rs", text)
        self.assertEqual(result["host_signal_lines"], 1)
        self.assertEqual(result["provider_signal_lines"], 0)
        self.assertEqual(result["mixed_signal_lines"], 0)

    def test_scan_text_does_not_skip_cfg_any_not_test_blocks(self) -> None:
        text = "\n".join(
            [
                '#[cfg(any(not(test), feature = "live"))]',
                "fn runtime_only_path() {",
                "    let _ = BackendFamily::Claude == BackendFamily::Claude",
                "        && TerminalHost::Cursor == TerminalHost::Cursor;",
                "}",
            ]
        )
        result = self.script._scan_text("rust/src/bin/voiceterm/example.rs", text)
        self.assertEqual(result["host_signal_lines"], 1)
        self.assertEqual(result["provider_signal_lines"], 1)
        self.assertEqual(result["mixed_signal_lines"], 1)

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
            code, report = self._run_main_json("--report-only", "--format", "json")
        self.assertEqual(code, 0)
        self.assertTrue(report["ok"])
        self.assertEqual(report["mode"], "report-only")
        self.assertEqual(report["unauthorized_files"], 1)

    def test_blocking_mode_fails_on_unauthorized_violations_by_default(self) -> None:
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
        self.assertEqual(code, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["mode"], "blocking")

    def test_blocking_mode_fails_on_unauthorized_file_signal_violation(self) -> None:
        fake_result = {
            "file": "rust/src/bin/voiceterm/terminal.rs",
            "host_signal_lines": 2,
            "provider_signal_lines": 3,
            "mixed_signal_lines": 0,
            "mixed_line_numbers": [],
            "file_signal_coupling": True,
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
        ), patch.object(
            self.script,
            "_is_allowlisted_file_signal_path",
            return_value=False,
        ):
            code, report = self._run_main_json("--format", "json")
        self.assertEqual(code, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["unauthorized_files"], 1)
        self.assertEqual(report["violations"][0]["violation_types"], ["file-scope"])
