"""Tests for docs-check constants compatibility exports."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from dev.scripts.devctl.commands import docs_check_constants, docs_check_policy


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
                    policy_path=str(policy_path),
                )
            )
            self.assertTrue(
                docs_check_policy.requires_evolution_update(
                    "ops/review.md",
                    policy_path=str(policy_path),
                )
            )
