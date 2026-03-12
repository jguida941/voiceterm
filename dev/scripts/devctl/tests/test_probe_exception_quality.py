"""Tests for probe_exception_quality review probe."""

from __future__ import annotations

import unittest
from pathlib import Path

from dev.scripts.devctl.tests.conftest import init_python_guard_repo_root, load_repo_module

SCRIPT = load_repo_module(
    "probe_exception_quality",
    "dev/scripts/checks/probe_exception_quality.py",
)


class ProbeExceptionQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_python_guard_repo_root(self)

    def _write(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_flags_silent_suppressive_broad_handler(self) -> None:
        path = self._write(
            "dev/scripts/example.py",
            (
                "def load_value() -> str | None:\n"
                "    try:\n"
                "        return fetch()\n"
                "    except Exception:\n"
                "        return None\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            current_text_by_path={"dev/scripts/example.py": path.read_text(encoding="utf-8")},
            mode="working-tree",
        )

        self.assertEqual(report.files_scanned, 1)
        self.assertEqual(len(report.risk_hints), 1)
        self.assertEqual(report.risk_hints[0].severity, "high")
        self.assertIn("suppressive broad handler", report.risk_hints[0].signals[0])

    def test_flags_context_free_exception_translation(self) -> None:
        path = self._write(
            "app/operator_console/example.py",
            (
                "def parse_config(path: str) -> None:\n"
                "    try:\n"
                "        load(path)\n"
                "    except OSError as exc:\n"
                "        raise RuntimeError('failed to load config') from exc\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            current_text_by_path={"app/operator_console/example.py": path.read_text(encoding="utf-8")},
            mode="working-tree",
        )

        self.assertEqual(len(report.risk_hints), 1)
        self.assertEqual(report.risk_hints[0].severity, "medium")
        self.assertIn(
            "translated exception without runtime context",
            report.risk_hints[0].signals[0],
        )

    def test_ignores_exception_translation_with_runtime_context(self) -> None:
        path = self._write(
            "dev/scripts/contextful.py",
            (
                "def parse_config(path: str) -> None:\n"
                "    try:\n"
                "        load(path)\n"
                "    except OSError as exc:\n"
                "        raise RuntimeError(f'failed to load config at {path}') from exc\n"
            ),
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            current_text_by_path={"dev/scripts/contextful.py": path.read_text(encoding="utf-8")},
            mode="working-tree",
        )

        self.assertEqual(report.files_scanned, 1)
        self.assertEqual(report.risk_hints, [])


if __name__ == "__main__":
    unittest.main()
