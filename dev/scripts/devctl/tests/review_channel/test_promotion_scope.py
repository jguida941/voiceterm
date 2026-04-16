"""Focused regressions for typed scope-to-plan resolution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.review_channel.promotion import resolve_scope_plan_path
from dev.scripts.devctl.tests.plan_registry_support import (
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
