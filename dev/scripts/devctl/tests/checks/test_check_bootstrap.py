"""Tests for shared check bootstrap helpers."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from dev.scripts.checks import check_bootstrap


class CheckBootstrapTests(unittest.TestCase):
    """Protect shared helper behavior used by standalone check scripts."""

    def test_utc_timestamp_uses_z_suffix(self) -> None:
        timestamp = check_bootstrap.utc_timestamp()
        self.assertTrue(timestamp.endswith("Z"))
        self.assertNotIn("+00:00", timestamp)

    def test_emit_runtime_error_json_uses_utc_timestamp(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            rc = check_bootstrap.emit_runtime_error("demo-check", "json", "boom")

        self.assertEqual(rc, 2)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["command"], "demo-check")
        self.assertEqual(payload["error"], "boom")
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["timestamp"].endswith("Z"))

    @patch("dev.scripts.checks.check_bootstrap.importlib.import_module")
    @patch("dev.scripts.checks.check_bootstrap.ensure_repo_root_on_syspath")
    def test_import_local_or_repo_module_repairs_repo_imports_once(
        self,
        mock_ensure_repo_root,
        mock_import_module,
    ) -> None:
        expected_module = object()
        local_missing = ModuleNotFoundError("No module named 'package_layout'")
        local_missing.name = "package_layout"
        mock_import_module.side_effect = [
            local_missing,
            expected_module,
        ]

        result = check_bootstrap.import_local_or_repo_module(
            "package_layout.rules",
            "dev.scripts.checks.package_layout.rules",
            repo_root=Path("/tmp/repo"),
        )

        self.assertIs(result, expected_module)
        mock_ensure_repo_root.assert_called_once_with(Path("/tmp/repo"))
        self.assertEqual(
            [call.args[0] for call in mock_import_module.call_args_list],
            [
                "package_layout.rules",
                "dev.scripts.checks.package_layout.rules",
            ],
        )

    @patch("dev.scripts.checks.check_bootstrap.importlib.import_module")
    def test_import_local_or_repo_module_does_not_mask_nested_missing_imports(
        self,
        mock_import_module,
    ) -> None:
        nested_missing = ModuleNotFoundError("No module named 'tomllib'")
        nested_missing.name = "tomllib"
        mock_import_module.side_effect = nested_missing

        with self.assertRaises(ModuleNotFoundError):
            check_bootstrap.import_local_or_repo_module(
                "package_layout.rules",
                "dev.scripts.checks.package_layout.rules",
                repo_root=Path("/tmp/repo"),
            )


if __name__ == "__main__":
    unittest.main()
