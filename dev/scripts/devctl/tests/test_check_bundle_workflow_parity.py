"""Tests for check_bundle_workflow_parity guard script."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from conftest import load_repo_module, override_module_attrs

SCRIPT = load_repo_module(
    "check_bundle_workflow_parity",
    "dev/scripts/checks/check_bundle_workflow_parity.py",
)

DEFAULT_RELEASE_WORKFLOW = (
    "steps:\n"
    "  - run: python3 dev/scripts/devctl.py check --profile release\n"
)


def _registered_commands(commands_by_bundle: dict[str, list[str]]):
    def loader(bundle_name: str) -> tuple[list[str], str | None]:
        return commands_by_bundle.get(bundle_name, []), None

    return loader


class BundleWorkflowParityTestCase(unittest.TestCase):
    script = SCRIPT

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.workflow_dir = self.root / ".github/workflows"
        self.workflow_dir.mkdir(parents=True)

    def _write_workflow(self, filename: str, text: str) -> None:
        (self.workflow_dir / filename).write_text(text, encoding="utf-8")

    def _build_report(
        self,
        *,
        tooling_workflow: str,
        targets: tuple[dict[str, object], ...],
        commands_by_bundle: dict[str, list[str]],
        release_workflow: str = DEFAULT_RELEASE_WORKFLOW,
    ) -> dict:
        self._write_workflow("tooling_control_plane.yml", tooling_workflow)
        self._write_workflow("release_preflight.yml", release_workflow)
        override_module_attrs(
            self,
            self.script,
            REPO_ROOT=self.root,
            BUNDLE_WORKFLOW_TARGETS=targets,
            _get_registered_bundle_commands=_registered_commands(commands_by_bundle),
        )
        return self.script.build_report()


class CheckBundleWorkflowParityTests(BundleWorkflowParityTestCase):
    """Protect bundle/workflow parity checks."""

    def test_build_report_passes_when_all_bundle_commands_exist(self) -> None:
        report = self._build_report(
            tooling_workflow=(
                "on:\n"
                "  push:\n"
                "    paths:\n"
                "      - \"dev/config/publication_sync_registry.json\"\n"
                "      - \"scripts/operator_console.sh\"\n"
                "  pull_request:\n"
                "    paths:\n"
                "      - \"dev/config/publication_sync_registry.json\"\n"
                "      - \"scripts/operator_console.sh\"\n"
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py docs-check --strict-tooling\n"
                "  - run: python3 dev/scripts/checks/check_publication_sync.py\n"
                "  - run: python3 dev/scripts/checks/check_bundle_workflow_parity.py\n"
            ),
            targets=(
                {
                    "bundle": "bundle.tooling",
                    "workflow": ".github/workflows/tooling_control_plane.yml",
                    "required_extra_commands": (
                        "python3 dev/scripts/checks/check_publication_sync.py",
                    ),
                    "required_path_filters": (
                        "dev/config/publication_sync_registry.json",
                        "scripts/operator_console.sh",
                    ),
                    "required_trigger_events": ("push", "pull_request"),
                },
                {
                    "bundle": "bundle.release",
                    "workflow": ".github/workflows/release_preflight.yml",
                },
            ),
            commands_by_bundle={
                "bundle.tooling": [
                    "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                    "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
                ],
                "bundle.release": [
                    "python3 dev/scripts/devctl.py check --profile release",
                    "python3 dev/scripts/checks/check_coderabbit_gate.py --branch master",
                ],
            },
            release_workflow=(
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py check --profile release\n"
                "  - run: python3 dev/scripts/checks/check_coderabbit_gate.py --branch master\n"
            ),
        )

        self.assertTrue(report["ok"])
        self.assertEqual(len(report["targets"]), 2)
        self.assertEqual(report["targets"][0]["missing_commands"], [])
        self.assertEqual(report["targets"][1]["missing_commands"], [])
        self.assertEqual(report["targets"][0]["missing_extra_commands"], [])
        self.assertEqual(report["targets"][0]["missing_path_filters"], [])
        self.assertEqual(report["targets"][0]["missing_trigger_path_filters"], {})
        self.assertGreater(report["targets"][0]["run_scope_count"], 0)
        self.assertGreater(report["targets"][1]["run_scope_count"], 0)

    def test_build_report_fails_on_missing_workflow_command(self) -> None:
        report = self._build_report(
            tooling_workflow=(
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py docs-check --strict-tooling\n"
            ),
            targets=(
                {
                    "bundle": "bundle.tooling",
                    "workflow": ".github/workflows/tooling_control_plane.yml",
                },
                {
                    "bundle": "bundle.release",
                    "workflow": ".github/workflows/release_preflight.yml",
                },
            ),
            commands_by_bundle={
                "bundle.tooling": [
                    "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                    "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
                ],
                "bundle.release": [
                    "python3 dev/scripts/devctl.py check --profile release",
                ],
            },
        )

        self.assertFalse(report["ok"])
        tooling_target = report["targets"][0]
        self.assertEqual(len(tooling_target["missing_commands"]), 1)
        self.assertIn(
            "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
            tooling_target["missing_commands"],
        )

    def test_build_report_does_not_match_tokens_split_across_run_steps(self) -> None:
        report = self._build_report(
            tooling_workflow=(
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py docs-check\n"
                "  - run: --strict-tooling\n"
            ),
            targets=(
                {
                    "bundle": "bundle.tooling",
                    "workflow": ".github/workflows/tooling_control_plane.yml",
                },
                {
                    "bundle": "bundle.release",
                    "workflow": ".github/workflows/release_preflight.yml",
                },
            ),
            commands_by_bundle={
                "bundle.tooling": [
                    "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                ],
                "bundle.release": [
                    "python3 dev/scripts/devctl.py check --profile release",
                ],
            },
        )

        self.assertFalse(report["ok"])
        tooling_target = report["targets"][0]
        self.assertEqual(
            tooling_target["missing_commands"],
            ["python3 dev/scripts/devctl.py docs-check --strict-tooling"],
        )

    def test_build_report_fails_on_missing_required_extra_command(self) -> None:
        report = self._build_report(
            tooling_workflow=(
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py docs-check --strict-tooling\n"
            ),
            targets=(
                {
                    "bundle": "bundle.tooling",
                    "workflow": ".github/workflows/tooling_control_plane.yml",
                    "required_extra_commands": (
                        "python3 dev/scripts/checks/check_publication_sync.py",
                    ),
                },
                {
                    "bundle": "bundle.release",
                    "workflow": ".github/workflows/release_preflight.yml",
                },
            ),
            commands_by_bundle={
                "bundle.tooling": [
                    "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                ],
                "bundle.release": [
                    "python3 dev/scripts/devctl.py check --profile release",
                ],
            },
        )

        self.assertFalse(report["ok"])
        tooling_target = report["targets"][0]
        self.assertEqual(
            tooling_target["missing_extra_commands"],
            ["python3 dev/scripts/checks/check_publication_sync.py"],
        )

    def test_build_report_fails_on_missing_required_path_filter(self) -> None:
        report = self._build_report(
            tooling_workflow=(
                "on:\n"
                "  push:\n"
                "    paths:\n"
                "      - \"README.md\"\n"
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py docs-check --strict-tooling\n"
            ),
            targets=(
                {
                    "bundle": "bundle.tooling",
                    "workflow": ".github/workflows/tooling_control_plane.yml",
                    "required_path_filters": (
                        "dev/config/publication_sync_registry.json",
                    ),
                },
                {
                    "bundle": "bundle.release",
                    "workflow": ".github/workflows/release_preflight.yml",
                },
            ),
            commands_by_bundle={
                "bundle.tooling": [
                    "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                ],
                "bundle.release": [
                    "python3 dev/scripts/devctl.py check --profile release",
                ],
            },
        )

        self.assertFalse(report["ok"])
        tooling_target = report["targets"][0]
        self.assertEqual(
            tooling_target["missing_path_filters"],
            ["dev/config/publication_sync_registry.json"],
        )

    def test_build_report_requires_path_filters_for_each_trigger_event(self) -> None:
        report = self._build_report(
            tooling_workflow=(
                "on:\n"
                "  push:\n"
                "    paths:\n"
                "      - \"dev/config/publication_sync_registry.json\"\n"
                "      - \"scripts/operator_console.sh\"\n"
                "  pull_request:\n"
                "    paths:\n"
                "      - \"dev/config/publication_sync_registry.json\"\n"
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py docs-check --strict-tooling\n"
                "  - run: python3 dev/scripts/checks/check_publication_sync.py\n"
            ),
            targets=(
                {
                    "bundle": "bundle.tooling",
                    "workflow": ".github/workflows/tooling_control_plane.yml",
                    "required_extra_commands": (
                        "python3 dev/scripts/checks/check_publication_sync.py",
                    ),
                    "required_path_filters": (
                        "dev/config/publication_sync_registry.json",
                        "scripts/operator_console.sh",
                    ),
                    "required_trigger_events": ("push", "pull_request"),
                },
                {
                    "bundle": "bundle.release",
                    "workflow": ".github/workflows/release_preflight.yml",
                },
            ),
            commands_by_bundle={
                "bundle.tooling": [
                    "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                ],
                "bundle.release": [
                    "python3 dev/scripts/devctl.py check --profile release",
                ],
            },
        )

        self.assertFalse(report["ok"])
        tooling_target = report["targets"][0]
        self.assertEqual(tooling_target["missing_path_filters"], [])
        self.assertEqual(
            tooling_target["missing_trigger_path_filters"],
            {"pull_request": ["scripts/operator_console.sh"]},
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
            "python3 dev/scripts/devctl.py docs-check --strict-tooling",
            scopes[0],
        )
        self.assertIn(
            "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
            scopes[0],
        )

    def test_extract_workflow_job_scopes_reads_named_jobs(self) -> None:
        workflow_text = (
            "jobs:\n"
            "  docs-policy:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: python3 dev/scripts/devctl.py docs-check --strict-tooling\n"
            "  operator-console-tests:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: python3 -m pytest app/operator_console/tests/ -q --tb=short\n"
        )
        self.assertEqual(
            self.script._extract_workflow_job_scopes(workflow_text),
            {
                "docs-policy": [
                    "python3 dev/scripts/devctl.py docs-check --strict-tooling"
                ],
                "operator-console-tests": [
                    "python3 -m pytest app/operator_console/tests/ -q --tb=short"
                ],
            },
        )

    def test_extract_workflow_trigger_paths_reads_event_filters(self) -> None:
        workflow_text = (
            "on:\n"
            "  push:\n"
            "    paths:\n"
            "      - \"dev/config/publication_sync_registry.json\"\n"
            "      - \"scripts/operator_console.sh\"\n"
            "  pull_request:\n"
            "    paths:\n"
            "      - \"dev/config/publication_sync_registry.json\"\n"
        )
        self.assertEqual(
            self.script._extract_workflow_trigger_paths(workflow_text),
            {
                "push": [
                    "dev/config/publication_sync_registry.json",
                    "scripts/operator_console.sh",
                ],
                "pull_request": ["dev/config/publication_sync_registry.json"],
            },
        )

    def test_get_registered_bundle_commands_normalizes_leading_env_tokens(self) -> None:
        override_module_attrs(
            self,
            self.script,
            get_bundle_commands=lambda _bundle: [
                "CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master"
            ],
        )
        commands, error = self.script._get_registered_bundle_commands("bundle.release")
        self.assertIsNone(error)
        self.assertEqual(
            commands,
            ["python3 dev/scripts/checks/check_coderabbit_gate.py --branch master"],
        )

    def test_build_report_fails_when_required_job_sequence_is_in_wrong_job(self) -> None:
        report = self._build_report(
            tooling_workflow=(
                "jobs:\n"
                "  docs-policy:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - run: python3 -m pytest app/operator_console/tests/ -q --tb=short\n"
                "  operator-console-tests:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - run: python3 dev/scripts/devctl.py docs-check --strict-tooling\n"
            ),
            targets=(
                {
                    "bundle": "bundle.tooling",
                    "workflow": ".github/workflows/tooling_control_plane.yml",
                    "required_job_sequences": {
                        "docs-policy": {
                            "commands": (
                                "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                            ),
                        },
                        "operator-console-tests": {
                            "commands": (
                                "python3 -m pytest app/operator_console/tests/ -q --tb=short",
                            ),
                        },
                    },
                },
            ),
            commands_by_bundle={
                "bundle.tooling": [
                    "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                    "python3 -m pytest app/operator_console/tests/ -q --tb=short",
                ],
            },
        )

        self.assertFalse(report["ok"])
        tooling_target = report["targets"][0]
        self.assertEqual(
            tooling_target["missing_job_sequences"],
            {
                "docs-policy": [
                    "python3 dev/scripts/devctl.py docs-check --strict-tooling"
                ],
                "operator-console-tests": [
                    "python3 -m pytest app/operator_console/tests/ -q --tb=short"
                ],
            },
        )

    def test_build_report_fails_when_required_job_sequence_is_out_of_order(self) -> None:
        report = self._build_report(
            tooling_workflow=(
                "jobs:\n"
                "  docs-policy:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - run: python3 dev/scripts/checks/check_bundle_workflow_parity.py\n"
                "      - run: python3 dev/scripts/devctl.py docs-check --strict-tooling\n"
            ),
            targets=(
                {
                    "bundle": "bundle.tooling",
                    "workflow": ".github/workflows/tooling_control_plane.yml",
                    "required_job_sequences": {
                        "docs-policy": {
                            "commands": (
                                "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                                "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
                            ),
                        },
                    },
                },
            ),
            commands_by_bundle={
                "bundle.tooling": [
                    "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                    "python3 dev/scripts/checks/check_bundle_workflow_parity.py",
                ],
            },
        )

        self.assertFalse(report["ok"])
        tooling_target = report["targets"][0]
        self.assertEqual(tooling_target["missing_job_sequences"], {})
        self.assertEqual(
            tooling_target["job_sequence_order_errors"],
            {
                "docs-policy": [
                    "python3 dev/scripts/checks/check_bundle_workflow_parity.py"
                ]
            },
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
                (
                    "python3 dev/scripts/devctl.py docs-check --since-ref BASE "
                    "--head-ref HEAD --strict-tooling --format md"
                ),
            )
        )


if __name__ == "__main__":
    unittest.main()
