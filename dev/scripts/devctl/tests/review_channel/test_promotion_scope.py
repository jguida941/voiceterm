"""Focused regressions for typed scope-to-plan resolution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.review_channel.promotion import resolve_scope_plan_path
from dev.scripts.devctl.tests.plan_registry_support import (
    doc_registry_entry,
    governance_with_entries,
    plan_registry_entry,
)


def test_resolve_scope_plan_path_uses_typed_plan_registry(tmp_path: Path) -> None:
    plan_path = tmp_path / "dev" / "active" / "typed_scope.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text("# Typed Scope\n", encoding="utf-8")
    governance = governance_with_entries(
        plan_registry_entry("dev/active/typed_scope.md", "MP-377")
    )
    with patch(
        "dev.scripts.devctl.review_channel.promotion.scan_repo_governance_safely",
        return_value=governance,
    ):
        resolved = resolve_scope_plan_path(
            repo_root=tmp_path,
            scope_value="MP-377",
        )
    assert resolved == plan_path


def test_resolve_scope_plan_path_uses_typed_doc_registry_reference_fallback(
    tmp_path: Path,
) -> None:
    companion_path = tmp_path / "dev" / "active" / "platform_authority_loop.md"
    companion_path.parent.mkdir(parents=True, exist_ok=True)
    companion_path.write_text("# Platform Authority Loop\n", encoding="utf-8")
    governance = governance_with_entries(
        plan_registry_entry("dev/active/review_channel.md", "MP-355"),
        doc_entries=(
            doc_registry_entry(
                "dev/active/platform_authority_loop.md",
                "MP-377",
            ),
        ),
    )
    with patch(
        "dev.scripts.devctl.review_channel.promotion.scan_repo_governance_safely",
        return_value=governance,
    ):
        resolved = resolve_scope_plan_path(
            repo_root=tmp_path,
            scope_value="MP-377",
        )
    assert resolved == companion_path
