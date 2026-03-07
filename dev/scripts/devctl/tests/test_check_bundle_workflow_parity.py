"""Tests for check_bundle_workflow_parity guard script."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from typing import Callable

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


class CheckBundleWorkflowParityTests(unittest.TestCase):
    """Protect bundle/workflow parity checks."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_module(
            "check_bundle_workflow_parity",
            "dev/scripts/checks/check_bundle_workflow_parity.py",
        )

    def test_build_report_passes_when_all_bundle_commands_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".github/workflows").mkdir(parents=True)
            (root / ".github/workflows/tooling_control_plane.yml").write_text(
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py docs-check --strict-tooling\n"
                "  - run: python3 dev/scripts/checks/check_bundle_workflow_parity.py\n",
                encoding="utf-8",
            )
            (root / ".github/workflows/release_preflight.yml").write_text(
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py check --profile release\n"
                "  - run: python3 dev/scripts/checks/check_coderabbit_gate.py --branch master\n",
                encoding="utf-8",
            )

            original_root = self.script.REPO_ROOT
            original_targets = self.script.BUNDLE_WORKFLOW_TARGETS
            original_fetch: Callable[..., tuple[list[str], str | None]] = (
                self.script._get_registered_bundle_commands
            )
            self.addCleanup(setattr, self.script, "REPO_ROOT", original_root)
            self.addCleanup(
                setattr, self.script, "BUNDLE_WORKFLOW_TARGETS", original_targets
            )
            self.addCleanup(
                setattr, self.script, "_get_registered_bundle_commands", original_fetch
            )
            self.script.REPO_ROOT = root
            self.script.BUNDLE_WORKFLOW_TARGETS = (
                {
                    "bundle": "bundle.tooling",
                    "workflow": ".github/workflows/tooling_control_plane.yml",
                },
                {
                    "bundle": "bundle.release",
                    "workflow": ".github/workflows/release_preflight.yml",
                },
            )

            def _registered_commands(bundle_name: str) -> tuple[list[str], str | None]:
                commands = {
                    "bundle.tooling": [
                        "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                        "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
                    ],
                    "bundle.release": [
                        "python3 dev/scripts/devctl.py check --profile release",
                        "python3 dev/scripts/checks/check_coderabbit_gate.py --branch master",
                    ],
                }
                return commands.get(bundle_name, []), None

            self.script._get_registered_bundle_commands = _registered_commands

            report = self.script.build_report()

            self.assertTrue(report["ok"])
            self.assertEqual(len(report["targets"]), 2)
            self.assertEqual(report["targets"][0]["missing_commands"], [])
            self.assertEqual(report["targets"][1]["missing_commands"], [])
            self.assertGreater(report["targets"][0]["run_scope_count"], 0)
            self.assertGreater(report["targets"][1]["run_scope_count"], 0)

    def test_build_report_fails_on_missing_workflow_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".github/workflows").mkdir(parents=True)
            (root / ".github/workflows/tooling_control_plane.yml").write_text(
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py docs-check --strict-tooling\n",
                encoding="utf-8",
            )
            (root / ".github/workflows/release_preflight.yml").write_text(
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py check --profile release\n",
                encoding="utf-8",
            )

            original_root = self.script.REPO_ROOT
            original_targets = self.script.BUNDLE_WORKFLOW_TARGETS
            original_fetch: Callable[..., tuple[list[str], str | None]] = (
                self.script._get_registered_bundle_commands
            )
            self.addCleanup(setattr, self.script, "REPO_ROOT", original_root)
            self.addCleanup(
                setattr, self.script, "BUNDLE_WORKFLOW_TARGETS", original_targets
            )
            self.addCleanup(
                setattr, self.script, "_get_registered_bundle_commands", original_fetch
            )
            self.script.REPO_ROOT = root
            self.script.BUNDLE_WORKFLOW_TARGETS = (
                {
                    "bundle": "bundle.tooling",
                    "workflow": ".github/workflows/tooling_control_plane.yml",
                },
                {
                    "bundle": "bundle.release",
                    "workflow": ".github/workflows/release_preflight.yml",
                },
            )

            def _registered_commands(bundle_name: str) -> tuple[list[str], str | None]:
                commands = {
                    "bundle.tooling": [
                        "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                        "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
                    ],
                    "bundle.release": [
                        "python3 dev/scripts/devctl.py check --profile release",
                    ],
                }
                return commands.get(bundle_name, []), None

            self.script._get_registered_bundle_commands = _registered_commands

            report = self.script.build_report()

            self.assertFalse(report["ok"])
            tooling_target = report["targets"][0]
            self.assertEqual(len(tooling_target["missing_commands"]), 1)
            self.assertIn(
                "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
                tooling_target["missing_commands"],
            )

    def test_build_report_does_not_match_tokens_split_across_run_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".github/workflows").mkdir(parents=True)
            # Older matcher incorrectly passed by walking tokens across full-file text.
            (root / ".github/workflows/tooling_control_plane.yml").write_text(
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py docs-check\n"
                "  - run: --strict-tooling\n",
                encoding="utf-8",
            )
            (root / ".github/workflows/release_preflight.yml").write_text(
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py check --profile release\n",
                encoding="utf-8",
            )

            original_root = self.script.REPO_ROOT
            original_targets = self.script.BUNDLE_WORKFLOW_TARGETS
            original_fetch: Callable[..., tuple[list[str], str | None]] = (
                self.script._get_registered_bundle_commands
            )
            self.addCleanup(setattr, self.script, "REPO_ROOT", original_root)
            self.addCleanup(
                setattr, self.script, "BUNDLE_WORKFLOW_TARGETS", original_targets
            )
            self.addCleanup(
                setattr, self.script, "_get_registered_bundle_commands", original_fetch
            )
            self.script.REPO_ROOT = root
            self.script.BUNDLE_WORKFLOW_TARGETS = (
                {
                    "bundle": "bundle.tooling",
                    "workflow": ".github/workflows/tooling_control_plane.yml",
                },
                {
                    "bundle": "bundle.release",
                    "workflow": ".github/workflows/release_preflight.yml",
                },
            )

            def _registered_commands(bundle_name: str) -> tuple[list[str], str | None]:
                commands = {
                    "bundle.tooling": [
                        "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                    ],
                    "bundle.release": [
                        "python3 dev/scripts/devctl.py check --profile release",
                    ],
                }
                return commands.get(bundle_name, []), None

            self.script._get_registered_bundle_commands = _registered_commands

            report = self.script.build_report()

            self.assertFalse(report["ok"])
            tooling_target = report["targets"][0]
            self.assertEqual(
                tooling_target["missing_commands"],
                ["python3 dev/scripts/devctl.py docs-check --strict-tooling"],
            )

    def test_extract_workflow_run_scopes_reads_multiline_run_blocks(self) -> None:
        workflow_text = (
            "steps:\n"
            "  - name: release governance\n"
            "    run: |\n"
            "      python3 dev/scripts/devctl.py docs-check --strict-tooling\n"
            "      python3 dev/scripts/checks/check_bundle_workflow_parity.py\n"
        )
        scopes = self.script._extract_workflow_run_scopes(workflow_text)
        self.assertEqual(len(scopes), 1)
        self.assertIn(
            "python3 dev/scripts/devctl.py docs-check --strict-tooling", scopes[0]
        )
        self.assertIn(
            "python3 dev/scripts/checks/check_bundle_workflow_parity.py", scopes[0]
        )

    def test_get_registered_bundle_commands_normalizes_leading_env_tokens(self) -> None:
        original = self.script.get_bundle_commands
        self.addCleanup(setattr, self.script, "get_bundle_commands", original)
        self.script.get_bundle_commands = lambda _bundle: [
            "CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master"
        ]
        commands, error = self.script._get_registered_bundle_commands("bundle.release")
        self.assertIsNone(error)
        self.assertEqual(
            commands,
            ["python3 dev/scripts/checks/check_coderabbit_gate.py --branch master"],
        )

    def test_get_registered_bundle_commands_returns_error_when_bundle_missing(
        self,
    ) -> None:
        commands, error = self.script._get_registered_bundle_commands("bundle.missing")
        self.assertEqual(commands, [])
        self.assertIsNotNone(error)

    def test_subsequence_match_accepts_inserted_workflow_flags(self) -> None:
        self.assertTrue(
            self.script._is_token_subsequence(
                "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                "python3 dev/scripts/devctl.py docs-check --since-ref BASE --head-ref HEAD --strict-tooling --format md",
            )
        )


if __name__ == "__main__":
    unittest.main()
