"""Unit tests for active-plan execution-contract validation."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

from dev.scripts.checks.active_plan.contract import validate_execution_plan_contract
from dev.scripts.checks.active_plan.typed_phase_contract import (
    validate_typed_phase_plan_contract,
)


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

    def test_typed_phase_contract_accepts_phase_and_task_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            plan_path = repo_root / "dev/active/ai_governance_platform.md"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(
                "\n".join(
                    [
                        "# AI Governance Platform",
                        "",
                        "## Execution Checklist",
                        "",
                        "### Phase P0 - Findings Spine",
                        "Phase metadata: phase_id=MP377-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=in_progress; depends_on=none; summary=Close the findings spine.",
                        "- [ ] `MP377-P0-T01` Land the canonical backlog reader/writer.",
                        "      owner_doc: `dev/active/platform_authority_loop.md`",
                        "      status: `in_progress`",
                        "      depends_on: none",
                        "",
                        "### Phase P1 - Typed Ingestion",
                        "Phase metadata: phase_id=MP377-P1; owner_doc=`dev/active/ai_governance_platform.md`; status=pending; depends_on=`MP377-P0`; summary=Route startup from typed phases.",
                        "- [ ] `MP377-P1-T01` Feed typed plan routing into startup receipts.",
                        "      owner_doc: `dev/active/platform_authority_loop.md`",
                        "      status: `pending`",
                        "      depends_on: `MP377-P0-T01`",
                    ]
                ),
                encoding="utf-8",
            )

            issues = validate_typed_phase_plan_contract(
                repo_root=repo_root,
                required_plan_paths=("dev/active/ai_governance_platform.md",),
            )

            self.assertEqual(issues, [])

    def test_typed_phase_contract_reports_missing_owner_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            plan_path = repo_root / "dev/active/ai_governance_platform.md"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(
                "\n".join(
                    [
                        "# AI Governance Platform",
                        "",
                        "## Execution Checklist",
                        "",
                        "### Phase P0 - Findings Spine",
                        "Phase metadata: phase_id=MP377-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=in_progress; depends_on=none; summary=Close the findings spine.",
                        "- [ ] `MP377-P0-T01` Land the canonical backlog reader/writer.",
                        "      status: `pending`",
                        "      depends_on: none",
                    ]
                ),
                encoding="utf-8",
            )

            issues = validate_typed_phase_plan_contract(
                repo_root=repo_root,
                required_plan_paths=("dev/active/ai_governance_platform.md",),
            )

            self.assertIn(
                "dev/active/ai_governance_platform.md task `MP377-P0-T01` missing owner_doc",
                issues,
            )

    def test_typed_phase_contract_imports_in_local_script_mode(self) -> None:
        repo_root = Path(__file__).resolve().parents[4]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "dev/scripts/checks")

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from active_plan.typed_phase_contract import "
                    "validate_typed_phase_plan_contract; "
                    "print(callable(validate_typed_phase_plan_contract))"
                ),
            ],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "True")
