"""Focused tests for typed execution-plan phase/task parsing."""

from __future__ import annotations

from dev.scripts.devctl.platform.planning_ir_plan_content import (
    first_actionable_task,
    parse_execution_plan_phases,
)


def test_parse_execution_plan_phases_reads_typed_metadata() -> None:
    phases = parse_execution_plan_phases(
        "\n".join(
            (
                "# Demo Plan",
                "",
                "## Execution Checklist",
                "",
                "### Phase P0 - Findings Spine",
                "Phase metadata: phase_id=MP377-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=in_progress; depends_on=none; summary=Collapse plan authority.",
                "- [ ] `MP377-P0-T01` Implement the canonical backlog reader/writer.",
                "      owner_doc: `dev/active/platform_authority_loop.md`",
                "      status: `in_progress`",
                "      depends_on: none",
                "- [ ] `MP377-P0-T02` Shrink the execution-owner registry.",
                "      owner_doc: `dev/active/ai_governance_platform.md`",
                "      status: `pending`",
                "      depends_on: `MP377-P0-T01`",
                "",
                "### Phase P1 - Portable Proof",
                "Phase metadata: phase_id=MP377-P1; owner_doc=`dev/active/portable_code_governance.md`; status=pending; depends_on=`MP377-P0`; summary=Validate the reduced owner set on another repo.",
                "- [ ] `MP377-P1-T01` Validate the reduced owner-doc set on a second repo.",
                "      owner_doc: `dev/active/portable_code_governance.md`",
                "      status: `pending`",
                "      depends_on: `MP377-P0-T02`",
            )
        )
    )

    assert tuple(phase.phase_id for phase in phases) == ("MP377-P0", "MP377-P1")
    assert phases[0].owner_doc == "dev/active/ai_governance_platform.md"
    assert phases[0].status == "in_progress"
    assert phases[0].summary == "Collapse plan authority."
    assert phases[1].dependencies[0].dependency_id == "MP377-P0"
    assert phases[1].dependencies[0].dependency_kind == "phase"

    task = phases[0].tasks[0]
    assert task.task_id == "MP377-P0-T01"
    assert task.owner_doc == "dev/active/platform_authority_loop.md"
    assert task.status == "in_progress"
    assert task.phase_id == "MP377-P0"
    assert task.anchor_ref == "checklist:MP377-P0-T01"

    dependent_task = phases[0].tasks[1]
    assert dependent_task.dependencies[0].dependency_id == "MP377-P0-T01"
    assert dependent_task.dependencies[0].dependency_kind == "task"


def test_first_actionable_task_prefers_in_progress_before_pending() -> None:
    phases = parse_execution_plan_phases(
        "\n".join(
            (
                "# Demo Plan",
                "",
                "## Execution Checklist",
                "",
                "### Phase P0 - Findings Spine",
                "Phase metadata: phase_id=MP377-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=in_progress; depends_on=none; summary=Close the findings spine.",
                "- [ ] `MP377-P0-T01` Land the first task.",
                "      owner_doc: `dev/active/ai_governance_platform.md`",
                "      status: `pending`",
                "      depends_on: none",
                "",
                "### Phase P1 - Typed Ingestion",
                "Phase metadata: phase_id=MP377-P1; owner_doc=`dev/active/ai_governance_platform.md`; status=in_progress; depends_on=`MP377-P0`; summary=Add typed routing.",
                "- [ ] `MP377-P1-T01` Route startup receipts from typed phases.",
                "      owner_doc: `dev/active/platform_authority_loop.md`",
                "      status: `in_progress`",
                "      depends_on: `MP377-P0-T01`",
            )
        )
    )

    task = first_actionable_task(phases)

    assert task is not None
    assert task.task_id == "MP377-P1-T01"
    assert task.owner_doc == "dev/active/platform_authority_loop.md"
