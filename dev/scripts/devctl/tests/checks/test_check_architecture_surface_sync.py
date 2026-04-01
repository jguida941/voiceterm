"""Tests for check_architecture_surface_sync guard script."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from conftest import load_repo_module
except ModuleNotFoundError:
    from dev.scripts.devctl.tests.conftest import load_repo_module

SCRIPT = load_repo_module(
    "check_architecture_surface_sync",
    "dev/scripts/checks/check_architecture_surface_sync.py",
)


class CheckArchitectureSurfaceSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self._write_common_files()

    def _write(self, relative_path: str, text: str = "") -> None:
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def _write_common_files(self) -> None:
        self._write("dev/active/INDEX.md", "# index\n")
        self._write("dev/active/MASTER_PLAN.md", "# master plan\n")
        self._write("AGENTS.md", "# agents\n")
        self._write("dev/README.md", "# dev readme\n")
        self._write(
            "dev/scripts/devctl/script_catalog.py",
            "CHECK_SCRIPT_FILES = {}\n",
        )
        self._write(
            "dev/scripts/devctl/bundle_registry.py",
            "BUNDLE_REGISTRY = {}\n",
        )
        self._write(
            "dev/scripts/devctl/cli.py",
            "from .commands import (\n)\n\nCOMMAND_HANDLERS = {}\n",
        )
        self._write(
            "dev/scripts/devctl/commands/listing.py",
            "COMMANDS = []\n",
        )
        self._write("dev/scripts/README.md", "# scripts\n")
        self._write(".github/workflows/README.md", "# workflows\n")
        self._write(
            ".github/workflows/tooling_control_plane.yml",
            "steps:\n  - run: python3 -V\n",
        )
        self._write(
            ".github/workflows/release_preflight.yml",
            "steps:\n  - run: python3 -V\n",
        )

    def test_active_plan_requires_index_master_plan_and_discovery_links(self) -> None:
        self._write("dev/active/new_scope.md", "# new plan\n")

        report = SCRIPT.build_report(
            repo_root=self.root,
            explicit_paths=["dev/active/new_scope.md"],
        )

        self.assertFalse(report["ok"])
        rules = {(item["zone"], item["rule"]) for item in report["violations"]}
        self.assertIn(("active-plan", "missing-index-reference"), rules)
        self.assertIn(("active-plan", "missing-master-plan-reference"), rules)
        self.assertIn(("active-plan", "missing-discovery-reference"), rules)

    def test_check_script_passes_when_catalog_bundle_and_workflow_are_wired(self) -> None:
        script_path = "dev/scripts/checks/check_new_guard.py"
        self._write(script_path, "def main():\n    return 0\n")
        self._write(
            "dev/scripts/devctl/script_catalog.py",
            'CHECK_SCRIPT_FILES = {"new_guard": "check_new_guard.py"}\n',
        )
        self._write(
            "dev/scripts/devctl/bundle_registry.py",
            f'BUNDLE_REGISTRY = {{"bundle.tooling": ("python3 {script_path}",)}}\n',
        )
        self._write(
            ".github/workflows/tooling_control_plane.yml",
            f"steps:\n  - run: python3 {script_path}\n",
        )

        report = SCRIPT.build_report(repo_root=self.root, explicit_paths=[script_path])

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["violations"], [])

    def test_check_script_allowlist_permits_intentionally_local_guard(self) -> None:
        script_path = "dev/scripts/checks/check_command_source_validation.py"
        self._write(script_path, "def main():\n    return 0\n")
        self._write(
            "dev/scripts/devctl/script_catalog.py",
            'CHECK_SCRIPT_FILES = {"command_source_validation": "check_command_source_validation.py"}\n',
        )

        report = SCRIPT.build_report(repo_root=self.root, explicit_paths=[script_path])

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["violations"], [])

    def test_devctl_command_requires_cli_listing_and_docs(self) -> None:
        command_path = "dev/scripts/devctl/commands/new_command.py"
        self._write(
            command_path,
            "def run(args):\n    return 0\n",
        )

        report = SCRIPT.build_report(repo_root=self.root, explicit_paths=[command_path])

        self.assertFalse(report["ok"])
        rules = {(item["zone"], item["rule"]) for item in report["violations"]}
        self.assertIn(("devctl-command", "missing-cli-import"), rules)
        self.assertIn(("devctl-command", "missing-command-handler"), rules)

    def test_nested_devctl_command_passes_with_alias_import_and_handler(self) -> None:
        command_path = "dev/scripts/devctl/commands/governance/bootstrap.py"
        self._write(command_path, "def run(args):\n    return 0\n")
        self._write(
            "dev/scripts/devctl/cli.py",
            "from .commands.governance import (\n"
            "    bootstrap as governance_bootstrap,\n"
            ")\n\n"
            "COMMAND_HANDLERS = {\n"
            '    "governance-bootstrap": governance_bootstrap.run,\n'
            "}\n",
        )
        self._write(
            "dev/scripts/devctl/commands/listing.py",
            'COMMANDS = ["governance-bootstrap"]\n',
        )
        self._write(
            "dev/scripts/README.md",
            "python3 dev/scripts/devctl.py governance-bootstrap --format md\n",
        )

        report = SCRIPT.build_report(repo_root=self.root, explicit_paths=[command_path])

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["violations"], [])

    def test_nested_devctl_command_alias_import_still_requires_handler(self) -> None:
        command_path = "dev/scripts/devctl/commands/governance/bootstrap.py"
        self._write(command_path, "def run(args):\n    return 0\n")
        self._write(
            "dev/scripts/devctl/cli.py",
            "from .commands.governance import (\n"
            "    bootstrap as governance_bootstrap,\n"
            ")\n\n"
            "COMMAND_HANDLERS = {}\n",
        )

        report = SCRIPT.build_report(repo_root=self.root, explicit_paths=[command_path])

        self.assertFalse(report["ok"])
        rules = {(item["zone"], item["rule"]) for item in report["violations"]}
        self.assertNotIn(("devctl-command", "missing-cli-import"), rules)
        self.assertIn(("devctl-command", "missing-command-handler"), rules)

    def test_helper_command_module_without_run_entrypoint_is_skipped(self) -> None:
        helper_path = "dev/scripts/devctl/commands/check_support.py"
        self._write(helper_path, "def helper():\n    return 0\n")

        report = SCRIPT.build_report(repo_root=self.root, explicit_paths=[helper_path])

        self.assertTrue(report["ok"])
        self.assertEqual(report["checked_path_count"], 0)
        self.assertEqual(report["violations"], [])

    def test_app_surface_passes_when_active_plan_mentions_parent_surface(self) -> None:
        app_path = "app/operator_console/ui.py"
        self._write(app_path, "class Dummy:\n    pass\n")
        self._write(
            "dev/active/operator_console.md",
            "Owning plan for app/operator_console UI.\n",
        )

        report = SCRIPT.build_report(repo_root=self.root, explicit_paths=[app_path])

        self.assertTrue(report["ok"], report["violations"])

    def test_workflow_requires_readme_entry(self) -> None:
        workflow_path = ".github/workflows/new_lane.yml"
        self._write(workflow_path, "steps:\n  - run: python3 -V\n")

        report = SCRIPT.build_report(repo_root=self.root, explicit_paths=[workflow_path])

        self.assertFalse(report["ok"])
        self.assertEqual(
            {(item["zone"], item["rule"]) for item in report["violations"]},
            {("workflow", "missing-workflow-readme-reference")},
        )


if __name__ == "__main__":
    unittest.main()
