"""Tests for the platform-layer-boundaries guard."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dev.scripts.checks.architecture_boundary import command


def _rules() -> tuple[command.BoundaryRule, ...]:
    return command.coerce_boundary_rules(
        {
            "rules": [
                {
                    "rule_id": "operator_console_frontend_no_devctl_orchestration",
                    "include_globs": ["app/operator_console/**/*.py"],
                    "exclude_globs": ["app/operator_console/tests/**"],
                    "forbidden_import_prefixes": [
                        "dev.scripts.devctl.commands",
                        "dev.scripts.devctl.review_channel",
                        "dev.scripts.devctl.config",
                    ],
                    "guidance": "Use runtime contracts instead of orchestration imports.",
                }
            ]
        }
    )


class PlatformLayerBoundaryTests(unittest.TestCase):
    def test_collect_boundary_violations_flags_review_channel_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            target = root / "app/operator_console/state/example.py"
            target.parent.mkdir(parents=True)
            target.write_text(
                "from dev.scripts.devctl.review_channel.core import DEFAULT_BRIDGE_REL\n",
                encoding="utf-8",
            )

            violations, scanned = command.collect_boundary_violations(
                repo_root=root,
                candidate_paths=[Path("app/operator_console/state/example.py")],
                rules=_rules(),
                read_text=lambda path: (root / path).read_text(encoding="utf-8"),
            )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0]["import_name"],
            "dev.scripts.devctl.review_channel.core.DEFAULT_BRIDGE_REL",
        )

    def test_collect_boundary_violations_allows_runtime_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            target = root / "app/operator_console/state/example.py"
            target.parent.mkdir(parents=True)
            target.write_text(
                "from dev.scripts.devctl.runtime import ControlState\n",
                encoding="utf-8",
            )

            violations, scanned = command.collect_boundary_violations(
                repo_root=root,
                candidate_paths=[Path("app/operator_console/state/example.py")],
                rules=_rules(),
                read_text=lambda path: (root / path).read_text(encoding="utf-8"),
            )

        self.assertEqual(scanned, 1)
        self.assertEqual(violations, [])

    def test_collect_boundary_violations_expands_from_import_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            target = root / "app/operator_console/state/example.py"
            target.parent.mkdir(parents=True)
            target.write_text(
                "from dev.scripts.devctl import commands as devctl_commands\n",
                encoding="utf-8",
            )

            violations, _scanned = command.collect_boundary_violations(
                repo_root=root,
                candidate_paths=[Path("app/operator_console/state/example.py")],
                rules=_rules(),
                read_text=lambda path: (root / path).read_text(encoding="utf-8"),
            )

        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0]["import_name"],
            "dev.scripts.devctl.commands",
        )


if __name__ == "__main__":
    unittest.main()
