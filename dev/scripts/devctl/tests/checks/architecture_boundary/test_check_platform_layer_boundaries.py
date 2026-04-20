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
                },
                {
                    "rule_id": "startup_authority_runtime_no_review_channel_orchestration",
                    "include_globs": [
                        "dev/scripts/devctl/runtime/conductor_capability.py",
                        "dev/scripts/devctl/runtime/reviewer_gate_logic.py",
                        "dev/scripts/devctl/runtime/startup_context.py",
                        "dev/scripts/devctl/commands/governance/startup_context.py",
                    ],
                    "forbidden_import_prefixes": [
                        "dev.scripts.devctl.review_channel",
                    ],
                    "guidance": (
                        "Startup authority and typed conductor capability must "
                        "consume runtime-owned contracts, not review-channel "
                        "orchestration."
                    ),
                },
                {
                    "rule_id": "projection_support_no_world_building_imports",
                    "include_globs": [
                        "dev/scripts/devctl/review_channel/*support.py",
                        "dev/scripts/devctl/review_channel/*context.py",
                    ],
                    "forbidden_import_prefixes": [
                        "dev.scripts.devctl.commands",
                        "dev.scripts.devctl.context_graph.snapshot_payload",
                        "dev.scripts.devctl.context_graph.snapshot_store",
                        "dev.scripts.devctl.runtime.governance_scan",
                        "dev.scripts.devctl.config",
                    ],
                    "guidance": (
                        "Projection support/context modules must stay pure "
                        "lowerers over typed inputs."
                    ),
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

    def test_collect_boundary_violations_flags_startup_runtime_import_leak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            target = root / "dev/scripts/devctl/runtime/startup_context.py"
            target.parent.mkdir(parents=True)
            target.write_text(
                "from dev.scripts.devctl.review_channel.prompt import build_conductor_prompt\n",
                encoding="utf-8",
            )

            violations, scanned = command.collect_boundary_violations(
                repo_root=root,
                candidate_paths=[Path("dev/scripts/devctl/runtime/startup_context.py")],
                rules=_rules(),
                read_text=lambda path: (root / path).read_text(encoding="utf-8"),
            )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0]["import_name"],
            "dev.scripts.devctl.review_channel.prompt.build_conductor_prompt",
        )
        self.assertEqual(
            violations[0]["rule_id"],
            "startup_authority_runtime_no_review_channel_orchestration",
        )

    def test_collect_boundary_violations_flags_relative_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            target = root / "dev/scripts/devctl/runtime/startup_context.py"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "from ..review_channel.prompt import build_conductor_prompt\n",
                encoding="utf-8",
            )

            violations, scanned = command.collect_boundary_violations(
                repo_root=root,
                candidate_paths=[Path("dev/scripts/devctl/runtime/startup_context.py")],
                rules=_rules(),
                read_text=lambda path: (root / path).read_text(encoding="utf-8"),
            )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0]["import_name"],
            "dev.scripts.devctl.review_channel.prompt.build_conductor_prompt",
        )
        self.assertEqual(
            violations[0]["rule_id"],
            "startup_authority_runtime_no_review_channel_orchestration",
        )

    def test_collect_boundary_violations_flags_projection_context_world_building(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            target = root / "dev/scripts/devctl/review_channel/event_projection_context.py"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "from ..context_graph.snapshot_store import load_context_graph_snapshot\n",
                encoding="utf-8",
            )

            violations, scanned = command.collect_boundary_violations(
                repo_root=root,
                candidate_paths=[
                    Path("dev/scripts/devctl/review_channel/event_projection_context.py")
                ],
                rules=_rules(),
                read_text=lambda path: (root / path).read_text(encoding="utf-8"),
            )

        self.assertEqual(scanned, 1)
        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0]["import_name"],
            "dev.scripts.devctl.context_graph.snapshot_store.load_context_graph_snapshot",
        )
        self.assertEqual(
            violations[0]["rule_id"],
            "projection_support_no_world_building_imports",
        )

    def test_repo_policy_includes_startup_runtime_boundary_rule(self) -> None:
        rules = command.coerce_boundary_rules(
            command.resolve_guard_config(
                "platform_layer_boundaries",
                repo_root=command.REPO_ROOT,
            )
        )

        by_id = {rule.rule_id: rule for rule in rules}
        self.assertIn(
            "startup_authority_runtime_no_review_channel_orchestration",
            by_id,
        )
        self.assertEqual(
            by_id[
                "startup_authority_runtime_no_review_channel_orchestration"
            ].forbidden_import_prefixes,
            ("dev.scripts.devctl.review_channel",),
        )
        self.assertIn("projection_support_no_world_building_imports", by_id)


if __name__ == "__main__":
    unittest.main()
