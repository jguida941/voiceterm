"""Tests for docs-check constants compatibility exports."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.commands import docs_check_constants, docs_check_policy
from dev.scripts.devctl.governance.governed_doc_routing import GovernedDocRouting


class DocsCheckConstantsCompatibilityTests(TestCase):
    def test_reexported_constants_share_policy_objects(self) -> None:
        self.assertIs(docs_check_constants.USER_DOCS, docs_check_policy.USER_DOCS)
        self.assertIs(
            docs_check_constants.TOOLING_REQUIRED_DOCS,
            docs_check_policy.TOOLING_REQUIRED_DOCS,
        )
        self.assertIs(
            docs_check_constants.TOOLING_REQUIRED_DOC_ALIASES,
            docs_check_policy.TOOLING_REQUIRED_DOC_ALIASES,
        )
        self.assertIs(
            docs_check_constants.EVOLUTION_DOC, docs_check_policy.EVOLUTION_DOC
        )
        self.assertIs(
            docs_check_constants.INSTRUCTION_SURFACE_SYNC_SCRIPT_REL,
            docs_check_policy.INSTRUCTION_SURFACE_SYNC_SCRIPT_REL,
        )
        self.assertIs(
            docs_check_constants.DEPRECATED_REFERENCE_PATTERNS,
            docs_check_policy.DEPRECATED_REFERENCE_PATTERNS,
        )

    def test_reexported_helpers_share_policy_callables(self) -> None:
        self.assertIs(
            docs_check_constants.is_tooling_change,
            docs_check_policy.is_tooling_change,
        )
        self.assertIs(
            docs_check_constants.requires_evolution_update,
            docs_check_policy.requires_evolution_update,
        )
        self.assertIs(
            docs_check_constants.scan_deprecated_references,
            docs_check_policy.scan_deprecated_references,
        )

    def test_policy_override_can_replace_tooling_and_evolution_paths(self) -> None:
        policy_payload = {
            "schema_version": 1,
            "repo_governance": {
                "docs_check": {
                    "tooling_change_prefixes": ["ops/"],
                    "evolution_change_exact": ["ops/review.md"],
                }
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = Path(tmpdir) / "policy.json"
            policy_path.write_text(json.dumps(policy_payload), encoding="utf-8")

            self.assertTrue(
                docs_check_policy.is_tooling_change(
                    "ops/runbook.md",
                    repo_root=Path(tmpdir),
                    policy_path=str(policy_path),
                )
            )
            self.assertTrue(
                docs_check_policy.requires_evolution_update(
                    "ops/review.md",
                    repo_root=Path(tmpdir),
                    policy_path=str(policy_path),
                )
            )

    def test_empty_policy_does_not_revive_voiceterm_docs_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            policy_path = repo_root / "policy.json"
            policy_path.write_text("{}", encoding="utf-8")

            resolved = docs_check_policy.resolve_docs_check_policy(
                repo_root=repo_root,
                policy_path=str(policy_path),
            )

            self.assertEqual(resolved.user_docs, ())
            self.assertEqual(resolved.tooling_required_docs, ())
            self.assertEqual(resolved.evolution_doc, "")
            self.assertFalse(
                docs_check_policy.is_tooling_change(
                    "AGENTS.md",
                    repo_root=repo_root,
                    policy_path=str(policy_path),
                )
            )

    def test_policy_without_docs_check_derives_tooling_docs_from_governance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "docs" / "plans").mkdir(parents=True)
            (repo_root / "docs" / "engineering").mkdir(parents=True)
            (repo_root / "tools").mkdir(parents=True)
            (repo_root / ".github" / "workflows").mkdir(parents=True)

            (repo_root / "CONTRIBUTING.md").write_text("# Process\n", encoding="utf-8")
            (repo_root / "docs" / "plans" / "INDEX.md").write_text(
                "# Index\n"
                "| `docs/plans/MASTER_PLAN.md` | `tracker` | `canonical` | all active execution | always |\n",
                encoding="utf-8",
            )
            (repo_root / "docs" / "plans" / "MASTER_PLAN.md").write_text(
                "# Master Plan\n"
                "Execution plan contract: required\n"
                "## Scope\ntext\n"
                "## Execution Checklist\n- [ ] item\n"
                "## Progress Log\n- started\n"
                "## Session Resume\n- next\n"
                "## Audit Evidence\n- proof\n",
                encoding="utf-8",
            )
            (repo_root / "docs" / "engineering" / "DEVELOPMENT.md").write_text(
                "# Development\n",
                encoding="utf-8",
            )
            (repo_root / "tools" / "README.md").write_text(
                "# Tooling\n",
                encoding="utf-8",
            )

            policy_payload = {
                "schema_version": 1,
                "repo_governance": {
                    "surface_generation": {
                        "context": {
                            "process_doc": "CONTRIBUTING.md",
                            "execution_tracker_doc": "docs/plans/MASTER_PLAN.md",
                            "active_registry_doc": "docs/plans/INDEX.md",
                            "development_doc": "docs/engineering/DEVELOPMENT.md",
                            "scripts_readme_doc": "tools/README.md",
                            "python_tooling": "tools/",
                            "ci_workflows_doc": ".github/workflows/README.md",
                        }
                    }
                },
            }
            policy_path = repo_root / "policy.json"
            policy_path.write_text(json.dumps(policy_payload), encoding="utf-8")

            resolved = docs_check_policy.resolve_docs_check_policy(
                repo_root=repo_root,
                policy_path=str(policy_path),
            )

            self.assertEqual(
                resolved.tooling_required_docs,
                (
                    "CONTRIBUTING.md",
                    "docs/engineering/DEVELOPMENT.md",
                    "tools/README.md",
                    "docs/plans/MASTER_PLAN.md",
                ),
            )
            self.assertTrue(
                docs_check_policy.is_tooling_change(
                    "tools/checks/guard.py",
                    repo_root=repo_root,
                    policy_path=str(policy_path),
                )
            )

    def test_resolved_policy_is_cached_per_repo_and_policy_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            policy_path = repo_root / "policy.json"
            policy_path.write_text("{}", encoding="utf-8")
            routing = GovernedDocRouting(
                process_doc="",
                development_doc="",
                scripts_readme_doc="",
                architecture_doc="",
                tracker_path="",
                index_path="",
                governed_tooling_docs=(),
                governed_tooling_prefixes=(),
                tooling_change_prefixes=("tools/",),
            )

            with patch(
                "dev.scripts.devctl.commands.docs.policy_runtime.resolve_governed_doc_routing",
                return_value=routing,
            ) as routing_mock:
                first = docs_check_policy.resolve_docs_check_policy(
                    repo_root=repo_root,
                    policy_path=str(policy_path),
                )
                second = docs_check_policy.resolve_docs_check_policy(
                    repo_root=repo_root,
                    policy_path=str(policy_path),
                )

                self.assertIs(first, second)
                self.assertTrue(
                    docs_check_policy.is_tooling_change(
                        "tools/checks/guard.py",
                        repo_root=repo_root,
                        policy_path=str(policy_path),
                    )
                )
                self.assertFalse(
                    docs_check_policy.requires_evolution_update(
                        "notes.txt",
                        repo_root=repo_root,
                        policy_path=str(policy_path),
                    )
                )

            self.assertEqual(routing_mock.call_count, 1)
