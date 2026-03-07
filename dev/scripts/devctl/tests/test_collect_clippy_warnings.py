"""Tests for clippy warning collection helper."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]


def load_module(name: str, relative_path: str):
    """Load a repository script as a module for unit tests."""
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CollectClippyWarningsTests(unittest.TestCase):
    """Protect clippy warning/status summary behavior used by CI."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.collector = load_module(
            "collect_clippy_warnings",
            "dev/scripts/collect_clippy_warnings.py",
        )

    def test_count_warning_messages_ignores_non_warning_entries(self) -> None:
        lines = [
            '{"reason":"compiler-message","message":{"level":"warning"}}\n',
            '{"reason":"compiler-message","message":{"level":"error"}}\n',
            '{"reason":"build-finished","success":true}\n',
            "not-json\n",
        ]
        self.assertEqual(self.collector.count_warning_messages(lines), 1)

    def test_build_summary_success_when_zero_warnings(self) -> None:
        summary = self.collector.build_summary(exit_code=0, warning_count=0)
        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["warnings"], 0)
        self.assertEqual(summary["exit_code"], 0)

    def test_build_summary_failure_when_warnings_present(self) -> None:
        summary = self.collector.build_summary(exit_code=0, warning_count=2)
        self.assertEqual(summary["status"], "failure")
        self.assertEqual(summary["warnings"], 2)

    def test_build_summary_failure_when_exit_nonzero(self) -> None:
        summary = self.collector.build_summary(exit_code=101, warning_count=0)
        self.assertEqual(summary["status"], "failure")
        self.assertEqual(summary["exit_code"], 101)

    def test_collect_warning_lint_counts_tracks_lint_codes(self) -> None:
        lines = [
            (
                '{"reason":"compiler-message","message":{"level":"warning",'
                '"code":{"code":"clippy::unwrap_used"}}}\n'
            ),
            (
                '{"reason":"compiler-message","message":{"level":"warning",'
                '"code":{"code":"clippy::unwrap_used"}}}\n'
            ),
            (
                '{"reason":"compiler-message","message":{"level":"warning",'
                '"code":{"code":"clippy::panic"}}}\n'
            ),
            '{"reason":"compiler-message","message":{"level":"error","code":{"code":"clippy::panic"}}}\n',
            '{"reason":"build-finished","success":true}\n',
            "not-json\n",
        ]
        counts = self.collector.collect_warning_lint_counts(lines)
        self.assertEqual(
            counts,
            {
                "clippy::panic": 1,
                "clippy::unwrap_used": 2,
            },
        )

    def test_write_lints_json_writes_sorted_schema_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "clippy-lints.json"
            self.collector.write_lints_json(
                output_path,
                {
                    "clippy::unwrap_used": 2,
                    "clippy::panic": 1,
                },
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(
            list(payload["lints"].keys()),
            ["clippy::panic", "clippy::unwrap_used"],
        )
        self.assertEqual(payload["lints"]["clippy::panic"], 1)
        self.assertEqual(payload["lints"]["clippy::unwrap_used"], 2)

    def test_build_clippy_command_includes_strict_warning_flag_when_requested(
        self,
    ) -> None:
        command = self.collector.build_clippy_command(deny_warnings=True)
        self.assertIn("-D", command)
        self.assertIn("warnings", command)

    def test_main_propagates_exit_code_when_requested(self) -> None:
        with patch.object(
            self.collector,
            "run_clippy",
            return_value=([], 101),
        ):
            with patch.object(
                self.collector.sys,
                "argv",
                [
                    "collect_clippy_warnings.py",
                    "--working-directory",
                    "rust",
                    "--propagate-exit-code",
                ],
            ):
                rc = self.collector.main()
        self.assertEqual(rc, 101)


if __name__ == "__main__":
    unittest.main()
