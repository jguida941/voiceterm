"""Focused tests for artifact-backed context-graph plan nodes."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.context_graph.catalog_nodes import collect_plan_nodes
from dev.scripts.devctl.tests.plan_registry_support import (
    governance_with_entries,
    plan_registry_entry,
)


def test_collect_plan_nodes_uses_typed_plan_registry_when_index_missing(
    tmp_path: Path,
) -> None:
    plan_path = tmp_path / "dev" / "active" / "typed_plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "\n".join(
            [
                "# Typed Plan",
                "",
                "## Execution Checklist",
                "",
                "### Phase One",
                "",
                "Phase metadata: phase_id=MP377-P1; owner_doc=`dev/active/typed_plan.md`; status=in_progress; depends_on=none; summary=test",
                "",
                "- [ ] `MP377-P1-T05` Continue projection work.",
                "      owner_doc: `dev/active/typed_plan.md`",
                "      status: `pending`",
                "      depends_on: `none`",
            ]
        ),
        encoding="utf-8",
    )
    governance = governance_with_entries(
        plan_registry_entry("dev/active/typed_plan.md", "MP-377")
    )
    with patch(
        "dev.scripts.devctl.context_graph.catalog_nodes.scan_repo_governance_safely",
        return_value=governance,
    ):
        nodes, _edges = collect_plan_nodes(tmp_path)
    plan_node = next(node for node in nodes if node.canonical_pointer_ref == "dev/active/typed_plan.md")
    assert plan_node.provenance_ref == "dev/active/INDEX.md"
    assert "MP377-P1-T05" in plan_node.metadata["aliases"]


def test_collect_plan_nodes_harvests_bare_mp_aliases_from_plan_text(
    tmp_path: Path,
) -> None:
    tracker_path = tmp_path / "dev" / "active" / "MASTER_PLAN.md"
    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    tracker_path.write_text(
        "\n".join(
            [
                "# Master Plan",
                "",
                "- 2026-04-18 `MP-395` Structured Checklist Migration For Half-Done Plans",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = tmp_path / "dev" / "active" / "ai_governance_platform.md"
    spec_path.write_text(
        "\n".join(
            [
                "# AI Governance Platform Plan",
                "",
                "## Execution Checklist",
                "",
                "### Phase MP-411 - Portability Audit Closure",
                "",
                "Phase metadata: phase_id=MP411-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=pending; depends_on=none; summary=test",
            ]
        ),
        encoding="utf-8",
    )
    governance = governance_with_entries(
        plan_registry_entry(
            "dev/active/MASTER_PLAN.md",
            "all active MP execution state",
            role="tracker",
            authority="canonical",
        ),
        plan_registry_entry("dev/active/ai_governance_platform.md", "MP-377"),
    )
    with patch(
        "dev.scripts.devctl.context_graph.catalog_nodes.scan_repo_governance_safely",
        return_value=governance,
    ):
        nodes, _edges = collect_plan_nodes(tmp_path)
    tracker_node = next(
        node for node in nodes if node.canonical_pointer_ref == "dev/active/MASTER_PLAN.md"
    )
    plan_node = next(
        node
        for node in nodes
        if node.canonical_pointer_ref == "dev/active/ai_governance_platform.md"
    )
    assert "MP-395" in tracker_node.metadata["aliases"]
    assert "MP-411" in plan_node.metadata["aliases"]


def test_collect_plan_nodes_ignores_body_cross_reference_mp_aliases(
    tmp_path: Path,
) -> None:
    spec_path = tmp_path / "dev" / "active" / "ai_governance_platform.md"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        "\n".join(
            [
                "# AI Governance Platform Plan",
                "",
                "## Execution Checklist",
                "",
                "### Phase MP-411 - Portability Audit Closure",
                "",
                "This paragraph references MP-355 for context only.",
                "",
                "Phase metadata: phase_id=MP411-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=pending; depends_on=none; summary=test",
            ]
        ),
        encoding="utf-8",
    )
    governance = governance_with_entries(
        plan_registry_entry("dev/active/ai_governance_platform.md", "MP-377")
    )
    with patch(
        "dev.scripts.devctl.context_graph.catalog_nodes.scan_repo_governance_safely",
        return_value=governance,
    ):
        nodes, _edges = collect_plan_nodes(tmp_path)
    plan_node = next(
        node
        for node in nodes
        if node.canonical_pointer_ref == "dev/active/ai_governance_platform.md"
    )
    assert "MP-411" in plan_node.metadata["aliases"]
    assert "MP-355" not in plan_node.metadata["aliases"]
