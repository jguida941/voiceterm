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


if __name__ == "__main__":
    unittest.main()
