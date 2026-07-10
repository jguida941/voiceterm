"""Unit tests for compatibility matrix validator script."""

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
from dev.scripts.devctl.tests.checks.compat_matrix_test_support import (
    assert_load_matrix_accepts_yaml_map_syntax,
    assert_missing_file_outside_repo_returns_error,
    write_lines,
)

SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/compat_matrix/check_compat_matrix.py"


def _load_script_module():
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(
        "check_compat_matrix_script", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_compat_matrix.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckCompatMatrixTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def _run_main_json(self, matrix_path: Path, *argv: str) -> tuple[int, dict]:
        buffer = io.StringIO()
        with patch.object(self.script, "MATRIX_PATH", matrix_path), patch.object(
            sys, "argv", ["check_compat_matrix.py", *argv]
        ):
            with redirect_stdout(buffer):
                exit_code = self.script.main()
        return exit_code, json.loads(buffer.getvalue())

    def test_load_matrix_accepts_yaml_map_syntax(self) -> None:
        assert_load_matrix_accepts_yaml_map_syntax(
            script=self.script,
            repo_root=REPO_ROOT,
        )

    def test_load_matrix_returns_parse_error_for_invalid_yaml(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            matrix_path = Path(temp_dir) / "matrix.yaml"
            matrix_path.write_text("hosts: [\n", encoding="utf-8")
            payload, error = self.script._load_matrix(matrix_path)
        self.assertIsNone(payload)
        self.assertIsNotNone(error)
        assert error is not None
        self.assertIn("failed to parse matrix file", error)

    def test_load_matrix_missing_file_outside_repo_returns_error(self) -> None:
        assert_missing_file_outside_repo_returns_error(script=self.script)

    def test_main_detects_duplicate_host_and_provider_ids(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            matrix_path = Path(temp_dir) / "matrix.yaml"
            write_lines(
                matrix_path,
                [
                    "hosts:",
                    "  - id: cursor",
                    "  - id: cursor",
                    "providers:",
                    "  - id: codex",
                    "    ipc_mode: ipc",
                    "  - id: codex",
                    "    ipc_mode: ipc",
                    "matrix:",
                    "  - host: cursor",
                    "    provider: codex",
                    "    compat: supported",
                ],
            )
            exit_code, report = self._run_main_json(matrix_path, "--format", "json")
        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["duplicate_host_ids"], ["cursor"])
        self.assertEqual(report["duplicate_provider_ids"], ["codex"])
        self.assertTrue(any("duplicate host ids" in msg for msg in report["errors"]))
        self.assertTrue(
            any("duplicate provider ids" in msg for msg in report["errors"])
        )

    def test_main_fails_when_hosts_or_providers_entries_miss_string_id(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            matrix_path = Path(temp_dir) / "matrix.yaml"
            write_lines(
                matrix_path,
                [
                    "hosts:",
                    "  - id: cursor",
                    "  - label: missing-id",
                    "providers:",
                    "  - id: codex",
                    "    ipc_mode: ipc",
                    "  - name: missing-id",
                    "matrix:",
                    "  - host: cursor",
                    "    provider: codex",
                    "    compat: supported",
                ],
            )
            exit_code, report = self._run_main_json(matrix_path, "--format", "json")
        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertTrue(
            any(
                "`hosts` contains 1 entries without a string `id`" in msg
                for msg in report["errors"]
            )
        )
        self.assertTrue(
            any(
                "`providers` contains 1 entries without a string `id`" in msg
                for msg in report["errors"]
            )
        )
