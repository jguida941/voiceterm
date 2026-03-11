"""Tests for check_guard_enforcement_inventory guard script."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from conftest import load_repo_module, override_module_attrs
except ModuleNotFoundError:
    from dev.scripts.devctl.tests.conftest import load_repo_module, override_module_attrs

SCRIPT = load_repo_module(
    "check_guard_enforcement_inventory",
    "dev/scripts/checks/check_guard_enforcement_inventory.py",
)


class CheckGuardEnforcementInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        workflow_dir = self.root / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)

    def _write_workflow(self, filename: str, text: str) -> None:
        target = self.root / ".github" / "workflows" / filename
        target.write_text(text, encoding="utf-8")

    def _override_contract(
        self,
        *,
        check_paths: dict[str, str],
        probe_paths: dict[str, str] | None = None,
        bundles: dict[str, tuple[str, ...]],
        exemptions: dict[str, dict] | None = None,
        indirect: dict[str, frozenset[str]] | None = None,
    ) -> None:
        override_module_attrs(
            self,
            SCRIPT,
            REPO_ROOT=self.root,
            WORKFLOWS_DIR=self.root / ".github" / "workflows",
            CHECK_SCRIPT_RELATIVE_PATHS=check_paths,
            PROBE_SCRIPT_RELATIVE_PATHS=probe_paths or {},
            BUNDLE_REGISTRY=bundles,
            ENFORCEMENT_EXEMPTIONS=exemptions or {},
            INDIRECT_DEVCTL_COMMAND_SCRIPT_IDS=indirect
            or {"docs-check": frozenset({"markdown_metadata_header"})},
        )

    def test_report_passes_with_direct_and_indirect_enforcement(self) -> None:
        self._write_workflow(
            "tooling_control_plane.yml",
            (
                "steps:\n"
                "  - run: python3 dev/scripts/checks/check_bundle_registry_dry.py\n"
                "  - run: python3 dev/scripts/checks/check_guard_enforcement_inventory.py\n"
            ),
        )
        self._override_contract(
            check_paths={
                "bootstrap": "dev/scripts/checks/check_bootstrap.py",
                "bundle_registry_dry": "dev/scripts/checks/check_bundle_registry_dry.py",
                "guard_enforcement_inventory": "dev/scripts/checks/check_guard_enforcement_inventory.py",
                "markdown_metadata_header": "dev/scripts/checks/check_markdown_metadata_header.py",
                "repo_url_parity": "dev/scripts/checks/check_repo_url_parity.py",
            },
            bundles={
                "bundle.tooling": (
                    "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                    "python3 dev/scripts/checks/check_guard_enforcement_inventory.py",
                    "python3 dev/scripts/checks/check_repo_url_parity.py",
                )
            },
            exemptions={
                "bootstrap": {
                    "kind": "helper",
                    "reason": "helper entrypoint",
                }
            },
        )

        report = SCRIPT.build_report(repo_root=self.root)

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["tracked_probe_count"], 0)
        markdown_entry = next(
            item
            for item in report["scripts"]
            if item["script_id"] == "markdown_metadata_header"
        )
        self.assertEqual(markdown_entry["direct_bundle_refs"], [])
        self.assertEqual(markdown_entry["direct_workflow_refs"], [])
        self.assertEqual(markdown_entry["indirect_bundle_refs"], ["bundle.tooling"])

    def test_report_fails_when_registered_script_has_no_lane(self) -> None:
        self._write_workflow(
            "tooling_control_plane.yml",
            "steps:\n  - run: python3 dev/scripts/checks/check_guard_enforcement_inventory.py\n",
        )
        self._override_contract(
            check_paths={
                "guard_enforcement_inventory": "dev/scripts/checks/check_guard_enforcement_inventory.py",
                "repo_url_parity": "dev/scripts/checks/check_repo_url_parity.py",
            },
            bundles={
                "bundle.tooling": (
                    "python3 dev/scripts/checks/check_guard_enforcement_inventory.py",
                )
            },
        )

        report = SCRIPT.build_report(repo_root=self.root)

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"],
            [
                {
                    "kind": "check",
                    "script_id": "repo_url_parity",
                    "path": "dev/scripts/checks/check_repo_url_parity.py",
                    "reason": "no bundle/workflow enforcement lane detected",
                }
            ],
        )

    def test_exemptions_prevent_false_positives_for_manual_scripts(self) -> None:
        self._write_workflow(
            "tooling_control_plane.yml",
            "steps:\n  - run: python3 dev/scripts/checks/check_guard_enforcement_inventory.py\n",
        )
        self._override_contract(
            check_paths={
                "guard_enforcement_inventory": "dev/scripts/checks/check_guard_enforcement_inventory.py",
                "mutation_score": "dev/scripts/checks/check_mutation_score.py",
            },
            bundles={
                "bundle.tooling": (
                    "python3 dev/scripts/checks/check_guard_enforcement_inventory.py",
                )
            },
            exemptions={
                "mutation_score": {
                    "kind": "manual",
                    "reason": "manual-only command wrapper",
                }
            },
        )

        report = SCRIPT.build_report(repo_root=self.root)

        self.assertTrue(report["ok"], report["violations"])

    def test_probe_scripts_count_as_enforced_when_probe_report_lane_exists(self) -> None:
        self._write_workflow(
            "tooling_control_plane.yml",
            (
                "steps:\n"
                "  - run: python3 dev/scripts/devctl.py probe-report --format md\n"
                "  - run: python3 dev/scripts/checks/check_guard_enforcement_inventory.py\n"
            ),
        )
        self._override_contract(
            check_paths={
                "guard_enforcement_inventory": "dev/scripts/checks/check_guard_enforcement_inventory.py",
            },
            probe_paths={
                "probe_design_smells": "dev/scripts/checks/probe_design_smells.py",
            },
            bundles={
                "bundle.tooling": (
                    "python3 dev/scripts/devctl.py probe-report --format md",
                    "python3 dev/scripts/checks/check_guard_enforcement_inventory.py",
                )
            },
            indirect={
                "probe-report": frozenset({"probe_design_smells"}),
            },
        )

        report = SCRIPT.build_report(repo_root=self.root)

        self.assertTrue(report["ok"], report["violations"])
        self.assertEqual(report["tracked_probe_count"], 1)
        probe_entry = next(
            item for item in report["scripts"] if item["script_id"] == "probe_design_smells"
        )
        self.assertEqual(probe_entry["kind"], "probe")
        self.assertEqual(probe_entry["indirect_bundle_refs"], ["bundle.tooling"])


if __name__ == "__main__":
    unittest.main()
