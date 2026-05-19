"""Tests for package-layout guard report wiring."""

from __future__ import annotations

import io
import json
from pathlib import Path
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from dev.scripts.checks.package_layout import command
from dev.scripts.devctl.quality_scan_mode import ADOPTION_BASE_REF, WORKTREE_HEAD_REF


class CheckPackageLayoutCommandTests(unittest.TestCase):
    """Protect adoption-scan report behavior for the package-layout command."""

    @patch.object(command.guard, "validate_ref")
    @patch("dev.scripts.checks.package_layout.command.list_changed_paths", return_value=[])
    @patch(
        "dev.scripts.checks.package_layout.command.collect_flat_root_violations",
        return_value=([], 0),
    )
    @patch(
        "dev.scripts.checks.package_layout.command.collect_namespace_layout_violations",
        return_value=([], [], 0),
    )
    @patch(
        "dev.scripts.checks.package_layout.command.collect_namespace_docs_sync_violations",
        return_value=([], 0),
    )
    @patch(
        "dev.scripts.checks.package_layout.command.collect_directory_crowding_violations",
        return_value=(
            [
                {
                    "path": "dev/scripts/checks",
                    "reason": "crowded_directory_baseline_violation",
                    "guidance": "crowded root",
                    "policy_source": "directory_crowding:dev/scripts/checks",
                }
            ],
            [
                {
                    "root": "dev/scripts/checks",
                    "current_files": 5,
                    "total_files": 7,
                    "shim_files": 2,
                    "max_files": 4,
                    "enforcement_mode": "freeze",
                    "policy_source": "directory_crowding:dev/scripts/checks",
                }
            ],
            5,
        ),
    )
    @patch(
        "dev.scripts.checks.package_layout.command.collect_root_role_findings",
        return_value=(
            [
                {
                    "root": "dev/scripts/devctl",
                    "total_files": 80,
                    "compat_shim_files": 20,
                    "public_entrypoint_files": 7,
                    "support_module_files": 21,
                    "implementation_module_files": 12,
                    "max_support_modules": 8,
                    "max_implementation_modules": 12,
                    "support_examples": [
                        "dev/scripts/devctl/governance_status_parser.py"
                    ],
                    "implementation_examples": [
                        "dev/scripts/devctl/script_catalog.py"
                    ],
                    "guidance": "move helper modules into packages",
                    "policy_source": "root_role:dev/scripts/devctl",
                }
            ],
            1,
        ),
    )
    @patch(
        "dev.scripts.checks.package_layout.command.collect_compatibility_redirects",
        return_value=[
            {
                "path": "dev/scripts/checks/check_package_layout.py",
                "target": "dev/scripts/checks/package_layout/command.py",
                "resolved_target": "dev/scripts/checks/package_layout/command.py",
                "target_exists": True,
                "policy_source": "directory_crowding:dev/scripts/checks",
            }
        ],
    )
    def test_main_reports_adoption_scan_without_ref_fields(
        self,
        _mock_redirects,
        _mock_role_findings,
        _mock_crowding,
        _mock_docs_sync,
        _mock_namespace,
        _mock_flat_root,
        _mock_changed_paths,
        mock_validate_ref,
    ) -> None:
        args = SimpleNamespace(
            since_ref=ADOPTION_BASE_REF,
            head_ref=WORKTREE_HEAD_REF,
            format="json",
        )
        parser = MagicMock()
        parser.parse_args.return_value = args

        with patch(
            "dev.scripts.checks.package_layout.command.build_since_ref_format_parser",
            return_value=parser,
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                rc = command.main()

        self.assertEqual(rc, 1)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "violations_present")
        self.assertEqual(payload["mode"], "adoption-scan")
        self.assertFalse(payload["layout_clean"])
        self.assertTrue(payload["baseline_layout_debt_detected"])
        self.assertFalse(payload["organization_review_clean"])
        self.assertTrue(payload["organization_role_debt_detected"])
        self.assertEqual(payload["root_role_rules_scanned"], 1)
        self.assertEqual(
            payload["compatibility_redirects"][0]["path"],
            "dev/scripts/checks/check_package_layout.py",
        )
        self.assertIsNone(payload["since_ref"])
        self.assertIsNone(payload["head_ref"])
        self.assertEqual(payload["crowded_directories"][0]["shim_files"], 2)
        mock_validate_ref.assert_any_call(ADOPTION_BASE_REF)
        mock_validate_ref.assert_any_call(WORKTREE_HEAD_REF)

    def test_render_markdown_marks_baseline_debt_as_not_clean(self) -> None:
        report = {
            "status": "baseline_debt_detected",
            "mode": "adoption-scan",
            "ok": True,
            "layout_clean": False,
            "baseline_layout_debt_detected": True,
            "organization_review_clean": False,
            "organization_role_debt_detected": True,
            "root_role_rules_scanned": 1,
            "files_changed": 0,
            "flat_root_candidates_scanned": 0,
            "flat_root_violations": 0,
            "namespace_layout_candidates_scanned": 0,
            "namespace_layout_violations": 0,
            "crowded_namespace_families": [
                {
                    "root": "dev/scripts/devctl/commands",
                    "flat_prefix": "check_",
                    "namespace_subdir": "check",
                    "current_files": 6,
                    "total_files": 8,
                    "shim_files": 2,
                    "min_family_size": 4,
                    "enforcement_mode": "freeze",
                }
            ],
            "namespace_docs_candidates_scanned": 0,
            "namespace_docs_violations": 0,
            "crowded_directory_candidates_scanned": 0,
            "crowded_directory_violations": 0,
            "crowded_directories": [],
            "root_role_findings": [
                {
                    "root": "dev/scripts/devctl",
                    "total_files": 80,
                    "compat_shim_files": 20,
                    "public_entrypoint_files": 7,
                    "support_module_files": 21,
                    "implementation_module_files": 12,
                    "max_support_modules": 8,
                    "max_implementation_modules": 12,
                    "support_examples": [
                        "dev/scripts/devctl/governance_status_parser.py"
                    ],
                    "implementation_examples": [
                        "dev/scripts/devctl/script_catalog.py"
                    ],
                    "guidance": "move helper modules into packages",
                }
            ],
            "compatibility_redirects": [
                {
                    "path": "dev/scripts/checks/check_package_layout.py",
                    "target": "dev/scripts/checks/package_layout/command.py",
                    "resolved_target": "dev/scripts/checks/package_layout/command.py",
                    "target_exists": True,
                    "policy_source": "directory_crowding:dev/scripts/checks",
                }
            ],
            "violations": [],
        }

        rendered = command._render_md(report)

        self.assertIn("- status: baseline_debt_detected", rendered)
        self.assertIn("- layout_clean: False", rendered)
        self.assertIn("- baseline_layout_debt_detected: True", rendered)
        self.assertIn("- organization_review_clean: False", rendered)
        self.assertIn("- organization_role_debt_detected: True", rendered)
        self.assertIn("## Organization Role Debt (advisory)", rendered)
        self.assertIn("support modules (max 8)", rendered)
        self.assertIn("## Compatibility Redirects", rendered)
        self.assertIn(
            "`dev/scripts/checks/check_package_layout.py` -> `dev/scripts/checks/package_layout/command.py`",
            rendered,
        )
        self.assertIn("approved shims excluded", rendered)


class BaselineDebtEnforcementTests(unittest.TestCase):
    """Tests for --fail-on-baseline-debt and --baseline-debt-root flags."""

    _CROWDED_DIRS = [
        {
            "root": "dev/scripts/devctl/commands",
            "current_files": 92,
            "total_files": 95,
            "shim_files": 3,
            "max_files": 48,
            "enforcement_mode": "strict",
            "policy_source": "directory_crowding:dev/scripts/devctl/commands",
        },
        {
            "root": "dev/scripts/checks",
            "current_files": 90,
            "total_files": 117,
            "shim_files": 27,
            "max_files": 40,
            "enforcement_mode": "strict",
            "policy_source": "directory_crowding:dev/scripts/checks",
        },
    ]
    _CROWDED_FAMILIES = [
        {
            "root": "dev/scripts/devctl/commands",
            "flat_prefix": "check_",
            "namespace_subdir": "check",
            "current_files": 12,
            "total_files": 12,
            "shim_files": 0,
            "min_family_size": 6,
            "enforcement_mode": "strict",
            "policy_source": "namespace_family:dev/scripts/devctl/commands:check_",
        },
    ]

    @patch.object(command.guard, "validate_ref")
    @patch("dev.scripts.checks.package_layout.command.list_changed_paths", return_value=[])
    @patch(
        "dev.scripts.checks.package_layout.command.collect_flat_root_violations",
        return_value=([], 0),
    )
    @patch(
        "dev.scripts.checks.package_layout.command.collect_namespace_layout_violations",
    )
    @patch(
        "dev.scripts.checks.package_layout.command.collect_namespace_docs_sync_violations",
        return_value=([], 0),
    )
    @patch(
        "dev.scripts.checks.package_layout.command.collect_directory_crowding_violations",
    )
    @patch(
        "dev.scripts.checks.package_layout.command.collect_root_role_findings",
        return_value=([], 0),
    )
    @patch(
        "dev.scripts.checks.package_layout.command.collect_compatibility_redirects",
        return_value=[],
    )
    def _run_main(
        self,
        args_ns,
        _mock_redirects,
        _mock_role_findings,
        mock_crowding,
        _mock_docs_sync,
        mock_namespace,
        _mock_flat_root,
        _mock_changed_paths,
        _mock_validate_ref,
        *,
        changed_paths: list[Path] | None = None,
        flat_root_violations: list[dict] | None = None,
        crowding_violations: list[dict] | None = None,
    ):
        _mock_changed_paths.return_value = [] if changed_paths is None else changed_paths
        _mock_flat_root.return_value = (
            [] if flat_root_violations is None else flat_root_violations,
            0,
        )
        mock_crowding.return_value = (
            [] if crowding_violations is None else crowding_violations,
            self._CROWDED_DIRS,
            0,
        )
        mock_namespace.return_value = ([], self._CROWDED_FAMILIES, 0)

        parser = MagicMock()
        parser.parse_args.return_value = args_ns

        with patch(
            "dev.scripts.checks.package_layout.command.build_since_ref_format_parser",
            return_value=parser,
        ):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                rc = command.main()
        return rc, json.loads(buffer.getvalue())

    def test_targeted_root_fails_on_matching_commands_dir(self) -> None:
        args = SimpleNamespace(
            since_ref=None,
            head_ref="HEAD",
            format="json",
            fail_on_baseline_debt=True,
            baseline_debt_roots=["dev/scripts/devctl/commands"],
        )
        rc, payload = self._run_main(args)

        self.assertEqual(rc, 1)
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["baseline_debt_enforced"])
        enforced_dirs = payload.get("enforced_crowded_directories", [])
        self.assertEqual(len(enforced_dirs), 1)
        self.assertEqual(enforced_dirs[0]["root"], "dev/scripts/devctl/commands")
        enforced_families = payload.get("enforced_crowded_namespace_families", [])
        self.assertEqual(len(enforced_families), 1)
        self.assertEqual(enforced_families[0]["flat_prefix"], "check_")

    def test_non_matching_root_passes(self) -> None:
        args = SimpleNamespace(
            since_ref=None,
            head_ref="HEAD",
            format="json",
            fail_on_baseline_debt=True,
            baseline_debt_roots=["dev/scripts/devctl/tests"],
        )
        rc, payload = self._run_main(args)

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["baseline_debt_enforced"])
        self.assertNotIn("enforced_crowded_directories", payload)

    def test_targeted_root_passes_when_changed_paths_do_not_touch_root(self) -> None:
        args = SimpleNamespace(
            since_ref=None,
            head_ref="HEAD",
            format="json",
            fail_on_baseline_debt=True,
            baseline_debt_roots=["dev/scripts/devctl/commands"],
        )
        rc, payload = self._run_main(args, changed_paths=[Path("bridge.md")])

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["baseline_debt_enforced"])
        self.assertNotIn("enforced_crowded_directories", payload)

    def test_targeted_root_filters_non_matching_root_violations(self) -> None:
        args = SimpleNamespace(
            since_ref=None,
            head_ref="HEAD",
            format="json",
            fail_on_baseline_debt=True,
            baseline_debt_roots=["dev/scripts/devctl/commands"],
        )
        rc, payload = self._run_main(
            args,
            changed_paths=[Path("dev/scripts/checks/check_new_guard.py")],
            flat_root_violations=[
                {
                    "path": "dev/scripts/checks/check_new_guard.py",
                    "reason": "new_flat_root_module_not_allowed",
                    "guidance": "move into a namespace",
                    "policy_source": "flat_root:dev/scripts/checks",
                }
            ],
            crowding_violations=[
                {
                    "path": "dev/scripts/checks/check_new_guard.py",
                    "reason": "new_file_in_crowded_directory",
                    "guidance": "move into a namespace",
                    "policy_source": "directory_crowding:dev/scripts/checks",
                }
            ],
        )

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["flat_root_violations"], 0)
        self.assertEqual(payload["crowded_directory_violations"], 0)
        self.assertFalse(payload["baseline_debt_enforced"])

    def test_targeted_root_passes_when_changed_paths_touch_namespace_child(self) -> None:
        args = SimpleNamespace(
            since_ref=None,
            head_ref="HEAD",
            format="json",
            fail_on_baseline_debt=True,
            baseline_debt_roots=["dev/scripts/devctl/commands"],
        )
        rc, payload = self._run_main(
            args,
            changed_paths=[Path("dev/scripts/devctl/commands/review_channel/status.py")],
        )

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["baseline_debt_enforced"])
        self.assertNotIn("enforced_crowded_directories", payload)

    def test_targeted_root_fails_when_changed_paths_touch_flat_root_file(self) -> None:
        args = SimpleNamespace(
            since_ref=None,
            head_ref="HEAD",
            format="json",
            fail_on_baseline_debt=True,
            baseline_debt_roots=["dev/scripts/devctl/commands"],
        )
        rc, payload = self._run_main(
            args,
            changed_paths=[Path("dev/scripts/devctl/commands/triage_loop.py")],
        )

        self.assertEqual(rc, 1)
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["baseline_debt_enforced"])
        enforced_dirs = payload.get("enforced_crowded_directories", [])
        self.assertEqual(len(enforced_dirs), 1)
        self.assertEqual(enforced_dirs[0]["root"], "dev/scripts/devctl/commands")

    def test_targeted_root_passes_when_changed_flat_file_is_compat_shim(self) -> None:
        args = SimpleNamespace(
            since_ref=None,
            head_ref="HEAD",
            format="json",
            fail_on_baseline_debt=True,
            baseline_debt_roots=["dev/scripts/devctl/commands"],
        )
        rc, payload = self._run_main(
            args,
            changed_paths=[Path("dev/scripts/devctl/commands/dashboard_utils.py")],
        )

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["baseline_debt_enforced"])

    def test_all_roots_pass_when_changed_paths_only_touch_namespace_child(self) -> None:
        args = SimpleNamespace(
            since_ref=None,
            head_ref="HEAD",
            format="json",
            fail_on_baseline_debt=True,
            baseline_debt_roots=None,
        )
        rc, payload = self._run_main(
            args,
            changed_paths=[Path("dev/scripts/devctl/commands/vcs/push.py")],
        )

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["baseline_debt_enforced"])

    def test_flag_disabled_passes_even_with_debt(self) -> None:
        args = SimpleNamespace(
            since_ref=None,
            head_ref="HEAD",
            format="json",
            fail_on_baseline_debt=False,
            baseline_debt_roots=None,
        )
        rc, payload = self._run_main(args)

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["baseline_debt_enforced"])

    def test_all_roots_fail_when_no_filter(self) -> None:
        args = SimpleNamespace(
            since_ref=None,
            head_ref="HEAD",
            format="json",
            fail_on_baseline_debt=True,
            baseline_debt_roots=None,
        )
        rc, payload = self._run_main(args)

        self.assertEqual(rc, 1)
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["baseline_debt_enforced"])
        enforced_dirs = payload.get("enforced_crowded_directories", [])
        self.assertEqual(len(enforced_dirs), 2)

    def test_render_md_includes_enforced_section(self) -> None:
        report = {
            "status": "baseline_debt_detected",
            "mode": "working-tree",
            "ok": False,
            "layout_clean": False,
            "baseline_layout_debt_detected": True,
            "organization_review_clean": True,
            "organization_role_debt_detected": False,
            "root_role_rules_scanned": 0,
            "baseline_debt_enforced": True,
            "files_changed": 0,
            "flat_root_candidates_scanned": 0,
            "flat_root_violations": 0,
            "namespace_layout_candidates_scanned": 0,
            "namespace_layout_violations": 0,
            "crowded_namespace_families": self._CROWDED_FAMILIES,
            "namespace_docs_candidates_scanned": 0,
            "namespace_docs_violations": 0,
            "crowded_directory_candidates_scanned": 0,
            "crowded_directory_violations": 0,
            "crowded_directories": self._CROWDED_DIRS,
            "root_role_findings": [],
            "compatibility_redirects": [],
            "violations": [],
            "enforced_crowded_directories": [self._CROWDED_DIRS[0]],
            "enforced_crowded_namespace_families": self._CROWDED_FAMILIES,
        }

        rendered = command._render_md(report)

        self.assertIn("## Enforced Baseline Debt (blocking)", rendered)
        self.assertIn("baseline_debt_enforced: True", rendered)
        self.assertIn("`dev/scripts/devctl/commands`: 92 files", rendered)
        self.assertIn("`dev/scripts/devctl/commands` + `check_*`: 12 files", rendered)


if __name__ == "__main__":
    unittest.main()
