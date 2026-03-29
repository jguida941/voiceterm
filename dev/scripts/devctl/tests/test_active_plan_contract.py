"""Unit tests for active-plan execution-contract validation."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase

from dev.scripts.checks.active_plan.contract import validate_execution_plan_contract


class ActivePlanContractTests(TestCase):
    def test_execution_plan_marker_without_registry_row_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            plan_path = repo_root / "dev/active/custom_execution_plan.md"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(
                "\n".join(
                    [
                        "Status: active",
                        "Execution plan contract: required",
                        "## Scope",
                        "## Execution Checklist",
                        "## Progress Log",
                        "## Session Resume",
                        "## Audit Evidence",
                    ]
                ),
                encoding="utf-8",
            )

            (
                missing_rows,
                missing_markers,
                missing_sections,
                missing_metadata_headers,
            ) = (
                validate_execution_plan_contract(
                    repo_root=repo_root,
                    active_markdown_files=["dev/active/custom_execution_plan.md"],
                    registry_by_path={},
                )
            )

            self.assertIn("dev/active/custom_execution_plan.md", missing_rows)
            self.assertEqual(missing_markers, [])
            self.assertEqual(missing_sections, [])
            self.assertEqual(missing_metadata_headers, [])

    def test_missing_metadata_header_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            plan_path = repo_root / "dev/active/theme_upgrade.md"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(
                "\n".join(
                    [
                        "Execution plan contract: required",
                        "## Scope",
                        "## Execution Checklist",
                        "## Progress Log",
                        "## Session Resume",
                        "## Audit Evidence",
                    ]
                ),
                encoding="utf-8",
            )

            (
                _missing_rows,
                _missing_markers,
                _missing_sections,
                missing_metadata_headers,
            ) = validate_execution_plan_contract(
                repo_root=repo_root,
                active_markdown_files=["dev/active/theme_upgrade.md"],
                registry_by_path={"dev/active/theme_upgrade.md": {"role": "spec"}},
            )

            self.assertEqual(
                missing_metadata_headers,
                ["dev/active/theme_upgrade.md"],
            )

    def test_missing_session_resume_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            plan_path = repo_root / "dev/active/theme_upgrade.md"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(
                "\n".join(
                    [
                        "Status: active",
                        "Execution plan contract: required",
                        "## Scope",
                        "## Execution Checklist",
                        "## Progress Log",
                        "## Audit Evidence",
                    ]
                ),
                encoding="utf-8",
            )

            (
                _missing_rows,
                _missing_markers,
                missing_sections,
                _missing_metadata_headers,
            ) = validate_execution_plan_contract(
                repo_root=repo_root,
                active_markdown_files=["dev/active/theme_upgrade.md"],
                registry_by_path={"dev/active/theme_upgrade.md": {"role": "spec"}},
            )

            self.assertEqual(
                missing_sections,
                ["dev/active/theme_upgrade.md missing: ## Session Resume"],
            )
