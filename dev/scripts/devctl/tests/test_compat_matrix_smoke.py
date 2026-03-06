"""Unit tests for compatibility matrix smoke script helpers."""

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


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/compat_matrix_smoke.py"


def _load_script_module():
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("compat_matrix_smoke_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load compat_matrix_smoke.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines), encoding="utf-8")


class CompatMatrixSmokeTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def _run_main_json(self, matrix_path: Path, *argv: str) -> tuple[int, dict]:
        buffer = io.StringIO()
        with patch.object(self.script, "MATRIX_PATH", matrix_path), patch.object(
            sys, "argv", ["compat_matrix_smoke.py", *argv]
        ):
            with redirect_stdout(buffer):
                exit_code = self.script.main()
        return exit_code, json.loads(buffer.getvalue())

    def test_load_matrix_accepts_yaml_map_syntax(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            matrix_path = Path(temp_dir) / "matrix.yaml"
            _write_lines(
                matrix_path,
                [
                    "hosts:",
                    "  - id: cursor",
                    "providers: []",
                    "matrix: []",
                ],
            )
            with patch.object(self.script, "yaml", None):
                payload, error = self.script._load_matrix(matrix_path)
        self.assertIsNone(error)
        self.assertIsInstance(payload, dict)
        assert payload is not None
        self.assertEqual(payload["hosts"][0]["id"], "cursor")

    def test_parse_backend_registry_names_reads_boxed_constructors(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            registry_path = Path(temp_dir) / "backend_mod.rs"
            _write_lines(
                registry_path,
                [
                    "mod codex;",
                    "mod claude;",
                    "mod custom;",
                    "",
                    "impl BackendRegistry {",
                    "    pub fn new() -> Self {",
                    "        Self {",
                    "            backends: vec![",
                    "                Box::new(CodexBackend::new()),",
                    "                Box::new(ClaudeBackend::new()),",
                    "                Box::new(OpenCodeBackend::new()),",
                    "            ],",
                    "        }",
                    "    }",
                    "}",
                ],
            )
            names = self.script._parse_backend_registry_names(registry_path)
        self.assertEqual(names, ["claude", "codex", "opencode"])

    def test_parse_backend_registry_names_handles_non_vector_constructor_layout(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            registry_path = Path(temp_dir) / "backend_mod.rs"
            _write_lines(
                registry_path,
                [
                    "impl BackendRegistry {",
                    "    pub fn new() -> Self {",
                    "        let primary = Box::new(CodexBackend::new());",
                    "        let fallback = Box::new(ClaudeBackend::new());",
                    "        Self::from_parts(primary, fallback, Box::new(GeminiBackend::new()))",
                    "    }",
                    "}",
                ],
            )
            names = self.script._parse_backend_registry_names(registry_path)
        self.assertEqual(names, ["claude", "codex", "gemini"])

    def test_load_matrix_missing_file_outside_repo_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing_matrix.yaml"
            payload, error = self.script._load_matrix(missing_path)
        self.assertIsNone(payload)
        self.assertIsNotNone(error)
        assert error is not None
        self.assertIn("missing matrix file", error)
        self.assertIn(missing_path.as_posix(), error)

    def test_main_reports_schema_errors_for_non_list_sections(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            matrix_path = Path(temp_dir) / "matrix.yaml"
            _write_lines(
                matrix_path,
                [
                    "hosts: {}",
                    "providers: {}",
                    "matrix: {}",
                ],
            )
            exit_code, report = self._run_main_json(matrix_path, "--format", "json")
        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertIn("`hosts` must be a list", report["errors"])
        self.assertIn("`providers` must be a list", report["errors"])
        self.assertIn("`matrix` must be a list", report["errors"])

    def test_main_enforces_new_runtime_host_variants_in_matrix(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            matrix_path = Path(temp_dir) / "matrix.yaml"
            _write_lines(
                matrix_path,
                [
                    "hosts:",
                    "  - id: cursor",
                    "providers:",
                    "  - id: codex",
                    "    ipc_mode: ipc",
                    "matrix:",
                    "  - host: cursor",
                    "    provider: codex",
                    "    compat: supported",
                ],
            )

            def fake_parse_enum_variants(_path: Path, enum_name: str) -> list[str]:
                if enum_name == "TerminalHost":
                    return ["Cursor", "NewHost"]
                if enum_name == "BackendFamily":
                    return ["Codex"]
                if enum_name == "Provider":
                    return ["Codex"]
                return []

            with patch.object(
                self.script, "_parse_enum_variants", side_effect=fake_parse_enum_variants
            ), patch.object(self.script, "_parse_backend_registry_names", return_value=["codex"]):
                exit_code, report = self._run_main_json(matrix_path, "--format", "json")

        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertTrue(any("newhost" in msg for msg in report["errors"]))

    def test_main_fails_closed_when_runtime_discovery_is_empty(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            matrix_path = Path(temp_dir) / "matrix.yaml"
            _write_lines(
                matrix_path,
                [
                    "hosts:",
                    "  - id: cursor",
                    "  - id: jetbrains",
                    "  - id: other",
                    "providers:",
                    "  - id: codex",
                    "    ipc_mode: ipc",
                    "  - id: claude",
                    "    ipc_mode: ipc",
                    "  - id: gemini",
                    "    ipc_mode: overlay-only-experimental",
                    "  - id: aider",
                    "    ipc_mode: overlay-only-non-ipc",
                    "  - id: opencode",
                    "    ipc_mode: overlay-only-non-ipc",
                    "  - id: custom",
                    "    ipc_mode: overlay-only-non-ipc",
                    "matrix: []",
                ],
            )

            with patch.object(self.script, "_parse_enum_variants", return_value=[]), patch.object(
                self.script, "_parse_backend_registry_names", return_value=[]
            ):
                exit_code, report = self._run_main_json(matrix_path, "--format", "json")

        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertTrue(
            any("failed to discover runtime host variants" in msg for msg in report["errors"])
        )
        self.assertTrue(
            any("failed to discover backend registry entries" in msg for msg in report["errors"])
        )
