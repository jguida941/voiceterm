"""Tests for the package-layout organization surface builder and rendering."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from dev.scripts.checks.package_layout.organization import (
    build_organization_surface,
)
from dev.scripts.checks.package_layout.render import render_md
from dev.scripts.checks.package_layout.rule_models import (
    CompatibilityRedirectState,
    LayoutDebtItem,
    OrganizationSurface,
    PackageRoleState,
    RootRoleRule,
)


def _stub_rule(
    root: str = "src",
    max_support: int = 3,
    max_impl: int = 5,
) -> RootRoleRule:
    return RootRoleRule(
        root=Path(root),
        include_globs=("*.py",),
        public_entrypoint_globs=("check_*.py",),
        generated_artifact_globs=("__init__.py",),
        doc_authority_globs=("README.md",),
        support_suffixes=("_support", "_common"),
        max_support_modules=max_support,
        max_implementation_modules=max_impl,
    )


class TestBuildOrganizationSurface:
    """Test the organization surface builder."""

    def test_empty_inputs_produce_valid_surface(self, tmp_path: Path) -> None:
        result = build_organization_surface(
            repo_root=tmp_path,
            compatibility_redirects=[],
            crowded_directories=[],
            crowded_namespace_families=[],
            root_role_findings=[],
            root_role_rules=(),
        )
        assert isinstance(result, dict)
        assert result["total_roles"] == 0
        assert result["total_redirects"] == 0
        assert result["total_debt_items"] == 0
        assert result["package_roles"] == []
        assert result["compatibility_redirects"] == []
        assert result["layout_debt"] == []

    def test_redirects_preserve_metadata(self, tmp_path: Path) -> None:
        redirects = [
            {
                "path": "old.py",
                "target": "new/old.py",
                "resolved_target": "new/old.py",
                "target_exists": True,
                "policy_source": "test",
                "owner": "team/infra",
                "reason": "moved to new package",
                "expiry": "2026-12-31",
            }
        ]
        result = build_organization_surface(
            repo_root=tmp_path,
            compatibility_redirects=redirects,
            crowded_directories=[],
            crowded_namespace_families=[],
            root_role_findings=[],
            root_role_rules=(),
        )
        assert result["total_redirects"] == 1
        r = result["compatibility_redirects"][0]
        assert r["owner"] == "team/infra"
        assert r["reason"] == "moved to new package"
        assert r["expiry"] == "2026-12-31"
        assert r["target_exists"] is True

    def test_missing_target_counted(self, tmp_path: Path) -> None:
        redirects = [
            {
                "path": "a.py",
                "target": "pkg/a.py",
                "resolved_target": "",
                "target_exists": False,
                "policy_source": "test",
            },
            {
                "path": "b.py",
                "target": "pkg/b.py",
                "resolved_target": "pkg/b.py",
                "target_exists": True,
                "policy_source": "test",
            },
        ]
        result = build_organization_surface(
            repo_root=tmp_path,
            compatibility_redirects=redirects,
            crowded_directories=[],
            crowded_namespace_families=[],
            root_role_findings=[],
            root_role_rules=(),
        )
        assert result["redirects_with_missing_targets"] == 1

    def test_crowded_directory_becomes_debt(self, tmp_path: Path) -> None:
        result = build_organization_surface(
            repo_root=tmp_path,
            compatibility_redirects=[],
            crowded_directories=[
                {
                    "root": "src",
                    "current_files": 50,
                    "max_files": 35,
                    "enforcement_mode": "freeze",
                }
            ],
            crowded_namespace_families=[],
            root_role_findings=[],
            root_role_rules=(),
        )
        assert result["total_debt_items"] == 1
        d = result["layout_debt"][0]
        assert d["kind"] == "crowded_directory"
        assert d["root"] == "src"
        assert d["current_files"] == 50
        assert d["max_files"] == 35

    def test_namespace_family_becomes_debt(self, tmp_path: Path) -> None:
        result = build_organization_surface(
            repo_root=tmp_path,
            compatibility_redirects=[],
            crowded_directories=[],
            crowded_namespace_families=[
                {
                    "root": "src",
                    "flat_prefix": "check_",
                    "current_files": 12,
                    "min_family_size": 8,
                    "enforcement_mode": "freeze",
                }
            ],
            root_role_findings=[],
            root_role_rules=(),
        )
        assert result["total_debt_items"] == 1
        d = result["layout_debt"][0]
        assert d["kind"] == "crowded_namespace_family"

    def test_role_finding_becomes_debt(self, tmp_path: Path) -> None:
        result = build_organization_surface(
            repo_root=tmp_path,
            compatibility_redirects=[],
            crowded_directories=[],
            crowded_namespace_families=[],
            root_role_findings=[
                {
                    "root": "src",
                    "support_module_files": 10,
                    "max_support_modules": 5,
                    "implementation_module_files": 3,
                    "max_implementation_modules": 5,
                }
            ],
            root_role_rules=(),
        )
        assert result["total_debt_items"] == 1
        d = result["layout_debt"][0]
        assert d["kind"] == "role_debt"
        assert "10 support" in d["detail"]

    def test_role_census_counts_files(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "check_foo.py").write_text("# entrypoint\n")
        (src / "helper_support.py").write_text("# support\n")
        (src / "widget.py").write_text("# implementation\n")

        result = build_organization_surface(
            repo_root=tmp_path,
            compatibility_redirects=[],
            crowded_directories=[],
            crowded_namespace_families=[],
            root_role_findings=[],
            root_role_rules=(_stub_rule("src"),),
        )
        assert result["total_roles"] == 1
        role = result["package_roles"][0]
        assert role["root"] == "src"
        assert role["total_files"] == 3
        assert role["public_entrypoint_files"] == 1
        assert role["support_module_files"] == 1
        assert role["implementation_module_files"] == 1
        assert role["debt_detected"] is False

    def test_role_debt_detected_when_over_limit(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        for i in range(10):
            (src / f"module_{i}.py").write_text(f"# impl {i}\n")

        result = build_organization_surface(
            repo_root=tmp_path,
            compatibility_redirects=[],
            crowded_directories=[],
            crowded_namespace_families=[],
            root_role_findings=[],
            root_role_rules=(_stub_rule("src", max_impl=5),),
        )
        role = result["package_roles"][0]
        assert role["implementation_module_files"] == 10
        assert role["debt_detected"] is True


class TestOrganizationSurfaceRendering:
    """Test markdown rendering of the organization surface."""

    def test_render_includes_organization_section(self) -> None:
        report = _minimal_report(
            organization={
                "total_roles": 1,
                "total_redirects": 2,
                "total_debt_items": 0,
                "redirects_with_missing_targets": 0,
                "package_roles": [
                    {
                        "root": "src",
                        "total_files": 10,
                        "compat_shim_files": 2,
                        "public_entrypoint_files": 3,
                        "support_module_files": 2,
                        "max_support_modules": 5,
                        "implementation_module_files": 3,
                        "max_implementation_modules": 5,
                        "debt_detected": False,
                    }
                ],
                "compatibility_redirects": [
                    {
                        "path": "old.py",
                        "target": "new/old.py",
                        "target_exists": True,
                        "owner": "team/x",
                        "expiry": "2026-12-31",
                    }
                ],
                "layout_debt": [],
            }
        )
        md = render_md(report)
        assert "## Organization Surface" in md
        assert "total_roles: 1" in md
        assert "`src`:" in md
        assert "### Declared Package Roles" in md
        assert "### Compatibility Redirects" in md
        assert "`old.py` -> `new/old.py`" in md
        assert "[team/x]" in md

    def test_render_debt_section(self) -> None:
        report = _minimal_report(
            organization={
                "total_roles": 0,
                "total_redirects": 0,
                "total_debt_items": 1,
                "redirects_with_missing_targets": 0,
                "package_roles": [],
                "compatibility_redirects": [],
                "layout_debt": [
                    {
                        "kind": "crowded_directory",
                        "root": "src",
                        "detail": "50 files (max 35)",
                    }
                ],
            }
        )
        md = render_md(report)
        assert "### Layout Debt" in md
        assert "[crowded_directory]" in md
        assert "`src`:" in md

    def test_render_without_organization_key(self) -> None:
        report = _minimal_report()
        md = render_md(report)
        assert "Organization Surface" not in md


def _minimal_report(**overrides) -> dict:
    """Build a minimal valid report dict for render_md."""
    base = {
        "command": "check_package_layout",
        "timestamp": "2026-04-06T00:00:00Z",
        "status": "clean",
        "mode": "working-tree",
        "ok": True,
        "layout_clean": True,
        "baseline_layout_debt_detected": False,
        "files_changed": 0,
        "flat_root_candidates_scanned": 0,
        "flat_root_violations": 0,
        "namespace_layout_candidates_scanned": 0,
        "namespace_layout_violations": 0,
        "crowded_namespace_families": [],
        "namespace_docs_candidates_scanned": 0,
        "namespace_docs_violations": 0,
        "crowded_directory_candidates_scanned": 0,
        "crowded_directory_violations": 0,
        "crowded_directories": [],
        "organization_review_clean": True,
        "organization_role_debt_detected": False,
        "root_role_rules_scanned": 0,
        "compatibility_redirects": [],
        "violations": [],
    }
    base.update(overrides)
    return base
