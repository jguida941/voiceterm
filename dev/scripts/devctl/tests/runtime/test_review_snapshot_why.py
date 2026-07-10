"""Focused tests for artifact-backed review-snapshot plan indexing."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.tests.plan_registry_support import (
    governance_with_entries,
    plan_registry_entry,
)
from dev.scripts.devctl.runtime.review_snapshot_why import load_plan_index


def test_load_plan_index_prefers_typed_plan_registry(tmp_path: Path) -> None:
    governance = governance_with_entries(
        plan_registry_entry("dev/active/alpha.md", "MP-377, MP-400"),
        plan_registry_entry("dev/active/beta.md", "MP-400"),
    )
    with patch(
        "dev.scripts.devctl.runtime.review_snapshot_why.scan_repo_governance_safely",
        return_value=governance,
    ):
        plan_index = load_plan_index(tmp_path)
    assert plan_index["MP-377"] == ("dev/active/alpha.md",)
    assert plan_index["MP-400"] == (
        "dev/active/alpha.md",
        "dev/active/beta.md",
    )
