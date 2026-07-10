"""Tests for the term-consistency review probe."""

from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.tests.conftest import init_python_guard_repo_root, load_repo_module

SCRIPT = load_repo_module(
    "probe_term_consistency_command",
    "dev/scripts/checks/term_consistency/command.py",
)


class ProbeTermConsistencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = init_python_guard_repo_root(self)
        (self.root / "dev/config").mkdir(parents=True, exist_ok=True)
        (self.root / "dev/config/devctl_repo_policy.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "capabilities": {"python": True, "rust": False},
                    "guard_configs": {
                        "probe_term_consistency": {
                            "include_globs": [
                                "dev/scripts/devctl/**/*.py",
                                "dev/guides/**/*.md"
                            ],
                            "exclude_globs": [
                                "dev/scripts/devctl/tests/**"
                            ],
                            "rules": [
                                {
                                    "id": "bridge_name",
                                    "canonical": "bridge",
                                    "aliases": ["code_audit"],
                                    "severity": "medium",
                                    "match_mode": "prefer_canonical"
                                },
                                {
                                    "id": "transport_family",
                                    "canonical": "bridge",
                                    "aliases": ["channel"],
                                    "severity": "low",
                                    "match_mode": "no_mixed_terms",
                                    "include_globs": [
                                        "dev/guides/**/*.md"
                                    ]
                                }
                            ]
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

    def _write(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_flags_introduced_legacy_bridge_term(self) -> None:
        path = self._write(
            "dev/scripts/devctl/example.py",
            "BRIDGE_FILE = 'code_audit.md'\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            base_text_by_path={path.relative_to(self.root).as_posix(): ""},
            current_text_by_path={path.relative_to(self.root).as_posix(): path.read_text(encoding="utf-8")},
            mode="working-tree",
        )

        self.assertEqual(report.files_scanned, 1)
        self.assertEqual(report.files_with_hints, 1)
        self.assertEqual(len(report.risk_hints), 1)
        self.assertIn("inventory: legacy terminology for `bridge`", report.risk_hints[0].signals[0])
        self.assertIn("delta: introduced alias debt for `bridge`", report.risk_hints[0].signals[1])
        self.assertEqual(report.risk_hints[0].severity, "medium")

    def test_reports_unchanged_debt_without_marking_it_worse(self) -> None:
        path = self._write(
            "dev/scripts/devctl/example.py",
            "BRIDGE_FILE = 'code_audit.md'\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            base_text_by_path={path.relative_to(self.root).as_posix(): "BRIDGE_FILE = 'code_audit.md'\n"},
            current_text_by_path={path.relative_to(self.root).as_posix(): path.read_text(encoding="utf-8")},
            mode="working-tree",
        )

        self.assertEqual(len(report.risk_hints), 1)
        self.assertIn("delta: unchanged alias debt for `bridge`", report.risk_hints[0].signals[1])
        self.assertEqual(report.risk_hints[0].severity, "low")

    def test_reports_worsened_debt_when_alias_count_rises(self) -> None:
        path = self._write(
            "dev/scripts/devctl/example.py",
            "BRIDGE_FILE = 'code_audit.md'; LEGACY = 'code_audit.md'\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            base_text_by_path={path.relative_to(self.root).as_posix(): "BRIDGE_FILE = 'code_audit.md'\n"},
            current_text_by_path={path.relative_to(self.root).as_posix(): path.read_text(encoding="utf-8")},
            mode="working-tree",
        )

        self.assertEqual(len(report.risk_hints), 1)
        self.assertIn("delta: worsened alias debt for `bridge`", report.risk_hints[0].signals[1])
        self.assertEqual(report.risk_hints[0].severity, "medium")

    def test_resolved_debt_drops_out_of_risk_hints(self) -> None:
        path = self._write(
            "dev/scripts/devctl/example.py",
            "BRIDGE_FILE = 'bridge.md'\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            base_text_by_path={path.relative_to(self.root).as_posix(): "BRIDGE_FILE = 'code_audit.md'\n"},
            current_text_by_path={path.relative_to(self.root).as_posix(): path.read_text(encoding="utf-8")},
            mode="working-tree",
        )

        self.assertEqual(report.files_scanned, 1)
        self.assertEqual(report.files_with_hints, 0)
        self.assertEqual(report.risk_hints, [])

    def test_adoption_scan_reports_inventory_only(self) -> None:
        path = self._write(
            "dev/guides/bridge.md",
            "The bridge channel remains the bridge channel.\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            base_text_by_path={path.relative_to(self.root).as_posix(): None},
            current_text_by_path={path.relative_to(self.root).as_posix(): "bridge channel bridge\n"},
            mode="adoption-scan",
        )

        self.assertEqual(len(report.risk_hints), 1)
        self.assertEqual(len(report.risk_hints[0].signals), 1)
        self.assertIn("inventory: mixed term family for `bridge`", report.risk_hints[0].signals[0])

    def test_main_uses_base_map_for_renamed_files(self) -> None:
        current_path = Path("dev/scripts/devctl/renamed_example.py")
        base_map = {current_path: Path("dev/scripts/devctl/legacy_example.py")}

        def read_text(path: Path, ref: str) -> str | None:
            if ref == "main" and path == Path("dev/scripts/devctl/legacy_example.py"):
                return "BRIDGE_FILE = 'code_audit.md'\n"
            if ref == "HEAD" and path == current_path:
                return "BRIDGE_FILE = 'code_audit.md'\n"
            return None

        with patch.object(
            SCRIPT,
            "list_changed_paths_with_base_map",
            return_value=([current_path], base_map),
        ), patch.object(
            SCRIPT.guard,
            "validate_ref",
            return_value=None,
        ), patch.object(
            SCRIPT.guard,
            "read_text_from_ref",
            side_effect=read_text,
        ), patch.object(
            sys,
            "argv",
            ["probe_term_consistency.py", "--since-ref", "main", "--format", "json"],
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                rc = SCRIPT.main()

        self.assertEqual(rc, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["files_scanned"], 1)
        self.assertEqual(len(payload["risk_hints"]), 1)
        self.assertIn("delta: unchanged alias debt for `bridge`", payload["risk_hints"][0]["signals"][1])

    def test_ignores_files_outside_probe_scope(self) -> None:
        path = self._write(
            "dev/scripts/devctl/tests/test_sample.py",
            "LEGACY = 'code_audit.md'\n",
        )

        report = SCRIPT.build_report(
            repo_root=self.root,
            candidate_paths=[path.relative_to(self.root)],
            base_text_by_path={path.relative_to(self.root).as_posix(): ""},
            current_text_by_path={path.relative_to(self.root).as_posix(): path.read_text(encoding="utf-8")},
            mode="working-tree",
        )

        self.assertEqual(report.files_scanned, 0)
        self.assertEqual(report.files_with_hints, 0)
        self.assertEqual(report.risk_hints, [])


if __name__ == "__main__":
    unittest.main()
