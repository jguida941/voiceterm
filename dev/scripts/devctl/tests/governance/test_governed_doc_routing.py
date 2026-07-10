"""Tests for governed-doc routing."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.governance.governed_doc_routing import (
    resolve_governed_doc_routing,
)
from dev.scripts.devctl.runtime.project_governance import (
    ArtifactRoots,
    BridgeConfig,
    BundleOverrides,
    DocPolicy,
    DocRegistry,
    DocRegistryEntry,
    EnabledChecks,
    MemoryRoots,
    PathRoots,
    PlanRegistry,
    ProjectGovernance,
    RepoIdentity,
    RepoPackRef,
)


def _write(path: Path, text: str = "# doc\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _governance() -> ProjectGovernance:
    return ProjectGovernance(
        schema_version=1,
        contract_id="ProjectGovernance",
        repo_identity=RepoIdentity(repo_name="governed-doc-routing"),
        repo_pack=RepoPackRef(pack_id="test-pack"),
        path_roots=PathRoots(
            active_docs="docs/plans",
            guides="docs/engineering",
            scripts="tools",
            checks="tools/checks",
            workflows=".github/workflows",
            config="config",
        ),
        plan_registry=PlanRegistry(
            registry_path="docs/plans/INDEX.md",
            tracker_path="docs/plans/MASTER_PLAN.md",
            index_path="docs/plans/INDEX.md",
        ),
        artifact_roots=ArtifactRoots(),
        memory_roots=MemoryRoots(),
        bridge_config=BridgeConfig(),
        enabled_checks=EnabledChecks(),
        bundle_overrides=BundleOverrides(overrides={}),
        doc_policy=DocPolicy(
            docs_authority_path="CONTRIBUTING.md",
            active_docs_root="docs/plans",
            guides_root="docs/engineering",
            governed_doc_roots=("docs/plans", "docs/engineering", "tools"),
            tracker_path="docs/plans/MASTER_PLAN.md",
            index_path="docs/plans/INDEX.md",
        ),
        doc_registry=DocRegistry(
            docs_authority_path="CONTRIBUTING.md",
            index_path="docs/plans/INDEX.md",
            tracker_path="docs/plans/MASTER_PLAN.md",
            entries=(
                DocRegistryEntry(
                    path="CONTRIBUTING.md",
                    doc_class="guide",
                    authority="canonical",
                    lifecycle="active",
                    scope="",
                    artifact_role="docs_authority",
                ),
                DocRegistryEntry(
                    path="docs/engineering/DEVELOPMENT.md",
                    doc_class="guide",
                    authority="canonical",
                    lifecycle="active",
                    scope="",
                ),
                DocRegistryEntry(
                    path="docs/engineering/ARCHITECTURE.md",
                    doc_class="guide",
                    authority="canonical",
                    lifecycle="active",
                    scope="",
                ),
                DocRegistryEntry(
                    path="tools/README.md",
                    doc_class="guide",
                    authority="canonical",
                    lifecycle="active",
                    scope="",
                ),
            ),
        ),
        docs_authority="CONTRIBUTING.md",
    )


class GovernedDocRoutingTests(TestCase):
    def test_prefers_typed_governance_docs_over_stale_policy_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            for relative_path in (
                "CONTRIBUTING.md",
                "docs/plans/INDEX.md",
                "docs/plans/MASTER_PLAN.md",
                "docs/engineering/DEVELOPMENT.md",
                "docs/engineering/ARCHITECTURE.md",
                "tools/README.md",
            ):
                _write(repo_root / relative_path)

            payload = {
                "repo_governance": {
                    "surface_generation": {
                        "context": {
                            "process_doc": "legacy/PROCESS.md",
                            "development_doc": "legacy/DEVELOPMENT.md",
                            "scripts_readme_doc": "legacy/README.md",
                            "architecture_doc": "legacy/ARCHITECTURE.md",
                        }
                    }
                }
            }

            with patch(
                "dev.scripts.devctl.governance.governed_doc_routing.load_repo_policy_payload",
                return_value=(payload, [], repo_root / "policy.json"),
            ), patch(
                "dev.scripts.devctl.governance.draft.scan_repo_governance",
                return_value=_governance(),
            ):
                resolved = resolve_governed_doc_routing(repo_root=repo_root)

        self.assertEqual(resolved.process_doc, "CONTRIBUTING.md")
        self.assertEqual(
            resolved.development_doc,
            "docs/engineering/DEVELOPMENT.md",
        )
        self.assertEqual(resolved.architecture_doc, "docs/engineering/ARCHITECTURE.md")
        self.assertEqual(resolved.scripts_readme_doc, "tools/README.md")
        self.assertEqual(resolved.tracker_path, "docs/plans/MASTER_PLAN.md")
        self.assertEqual(resolved.index_path, "docs/plans/INDEX.md")
        self.assertIn("CONTRIBUTING.md", resolved.governed_tooling_docs)
        self.assertIn("docs/engineering/DEVELOPMENT.md", resolved.governed_tooling_docs)
        self.assertIn("docs/engineering/ARCHITECTURE.md", resolved.governed_tooling_docs)
        self.assertIn("tools/README.md", resolved.governed_tooling_docs)
