"""Tests for package-layout guard report wiring."""

from __future__ import annotations

import io
import json
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
        "dev.scripts.checks.package_layout.command.collect_compatibility_redirects",
        return_value=[],
    )
    def _run_main(
        self,
        args_ns,
        _mock_redirects,
        mock_crowding,
        _mock_docs_sync,
        mock_namespace,
        _mock_flat_root,
        _mock_changed_paths,
        _mock_validate_ref,
    ):
        mock_crowding.return_value = ([], self._CROWDED_DIRS, 0)
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
