"""Unit tests for host/provider naming consistency check script."""

from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import sys
import tempfile
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_naming_consistency.py"


def _load_script_module():
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(
        "check_naming_consistency_script", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_naming_consistency.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines), encoding="utf-8")


def _matrix_lines() -> list[str]:
    return [
        "hosts:",
        "  - id: cursor",
        "  - id: jetbrains",
        "  - id: other",
        "providers:",
        "  - id: codex",
        "  - id: claude",
        "  - id: gemini",
        "  - id: aider",
        "  - id: opencode",
        "  - id: custom",
        "matrix: []",
    ]


def _runtime_tokens() -> dict[str, set[str]]:
    backend_ids = {"codex", "claude", "gemini", "aider", "opencode"}
    return {
        "runtime_host_ids": {"cursor", "jetbrains", "other"},
        "runtime_provider_ids": {"codex", "claude", "gemini"},
        "runtime_backend_ids": set(backend_ids),
        "ipc_provider_ids": {"codex", "claude"},
    }


def _tooling_tokens() -> dict[str, set[str]]:
    providers = {"codex", "claude", "gemini", "aider", "opencode", "custom"}
    return {
        "required_host_ids": {"cursor", "jetbrains", "other"},
        "required_provider_ids": set(providers),
        "required_ipc_provider_ids": {"codex", "claude"},
        "required_overlay_experimental_provider_ids": {"gemini"},
        "required_overlay_non_ipc_provider_ids": {"aider", "opencode", "custom"},
        "expected_non_ipc_mode_provider_ids": {"gemini", "aider", "opencode", "custom"},
        "isolation_provider_tokens": set(providers),
    }


class CheckNamingConsistencyTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def _run_main_json(
        self,
        matrix_path: Path,
        *,
        runtime_tokens: dict[str, set[str]] | None = None,
        tooling_tokens: dict[str, set[str]] | None = None,
        runtime_errors: list[str] | None = None,
        tooling_errors: list[str] | None = None,
    ) -> tuple[int, dict]:
        buffer = io.StringIO()
        runtime_tokens = runtime_tokens if runtime_tokens is not None else _runtime_tokens()
        tooling_tokens = tooling_tokens if tooling_tokens is not None else _tooling_tokens()
        runtime_errors = runtime_errors if runtime_errors is not None else []
        tooling_errors = tooling_errors if tooling_errors is not None else []

        with patch.object(self.script, "MATRIX_PATH", matrix_path), patch.object(
            self.script,
            "_collect_runtime_tokens",
            return_value=(runtime_tokens, runtime_errors),
        ), patch.object(
            self.script,
            "_collect_tooling_tokens",
            return_value=(tooling_tokens, tooling_errors),
        ), patch.object(
            sys, "argv", ["check_naming_consistency.py", "--format", "json"]
        ):
            with redirect_stdout(buffer):
                exit_code = self.script.main()
        return exit_code, json.loads(buffer.getvalue())

    def test_extract_provider_label_tokens_parses_grouped_pattern(self) -> None:
        tokens = self.script._extract_provider_label_tokens(
            r"(?:claude|codex|gemini|aider|opencode|custom)"
        )
        self.assertEqual(
            tokens,
            {"claude", "codex", "gemini", "aider", "opencode", "custom"},
        )

    def test_main_passes_when_tokens_are_consistent(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            matrix_path = Path(temp_dir) / "matrix.yaml"
            _write_lines(matrix_path, _matrix_lines())
            with patch.object(self.script._core, "yaml", None):
                exit_code, report = self._run_main_json(matrix_path)

        self.assertEqual(exit_code, 0)
        self.assertTrue(report["ok"])
        self.assertEqual(report["errors"], [])

    def test_main_fails_when_runtime_host_ids_drift_from_matrix(self) -> None:
        runtime_tokens = _runtime_tokens()
        runtime_tokens["runtime_host_ids"] = {"cursor", "jetbrains", "antigravity"}
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            matrix_path = Path(temp_dir) / "matrix.yaml"
            _write_lines(matrix_path, _matrix_lines())
            exit_code, report = self._run_main_json(
                matrix_path, runtime_tokens=runtime_tokens
            )

        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertTrue(
            any(
                "host ids" in message and "runtime host enum" in message
                for message in report["errors"]
            )
        )

    def test_main_fails_when_isolation_provider_tokens_drift(self) -> None:
        tooling_tokens = _tooling_tokens()
        tooling_tokens["isolation_provider_tokens"] = {
            "codex",
            "claude",
            "gemini",
            "aider",
            "opencode",
        }
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            matrix_path = Path(temp_dir) / "matrix.yaml"
            _write_lines(matrix_path, _matrix_lines())
            exit_code, report = self._run_main_json(
                matrix_path, tooling_tokens=tooling_tokens
            )

        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertTrue(
            any(
                "PROVIDER_LABEL_PATTERN" in message
                for message in report["errors"]
            )
        )

    def test_parse_enum_ids_handles_struct_variants_and_attributes(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            enum_path = Path(temp_dir) / "runtime_compat.rs"
            _write_lines(
                enum_path,
                [
                    "enum TerminalHost {",
                    "    Cursor,",
                    "    #[cfg(feature = \"jetbrains\")]",
                    "    JetBrains { source: u8, label: &'static str },",
                    "    Other,",
                    "}",
                ],
            )
            ids = self.script._parse_enum_ids(enum_path, "TerminalHost")

        self.assertEqual(ids, {"cursor", "jetbrains", "other"})

    def test_parse_enum_ids_ignores_comments_and_string_literals(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            enum_path = Path(temp_dir) / "runtime_compat.rs"
            _write_lines(
                enum_path,
                [
                    "enum BackendFamily {",
                    "    Codex,",
                    "    // not_a_variant,",
                    "    Claude,",
                    "    #[doc = \"Gemini, still a real variant\"]",
                    "    Gemini,",
                    "}",
                ],
            )
            ids = self.script._parse_enum_ids(enum_path, "BackendFamily")

        self.assertEqual(ids, {"codex", "claude", "gemini"})
