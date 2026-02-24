"""Shared execution-plan contract validation for active docs."""

from __future__ import annotations

from pathlib import Path

REQUIRED_EXECUTION_PLAN_DOCS = ["dev/active/autonomous_control_plane.md"]
EXECUTION_PLAN_MARKER = "Execution plan contract: required"
EXECUTION_PLAN_REQUIRED_SECTIONS = [
    "## Scope",
    "## Execution Checklist",
    "## Progress Log",
    "## Audit Evidence",
]


def validate_execution_plan_contract(
    *,
    repo_root: Path,
    active_markdown_files: list[str],
    registry_by_path: dict[str, dict],
) -> tuple[list[str], list[str], list[str]]:
    missing_rows: list[str] = []
    missing_markers: list[str] = []
    missing_sections: list[str] = []

    for relative in REQUIRED_EXECUTION_PLAN_DOCS:
        if relative not in registry_by_path:
            missing_rows.append(relative)
            continue
        plan_path = repo_root / relative
        if not plan_path.exists():
            continue
        plan_text = plan_path.read_text(encoding="utf-8")
        if EXECUTION_PLAN_MARKER not in plan_text:
            missing_markers.append(relative)
        section_gaps = [
            section for section in EXECUTION_PLAN_REQUIRED_SECTIONS if section not in plan_text
        ]
        if section_gaps:
            missing_sections.append(f"{relative} missing: {', '.join(section_gaps)}")

    for relative in active_markdown_files:
        if relative == "dev/active/INDEX.md":
            continue
        plan_path = repo_root / relative
        plan_text = plan_path.read_text(encoding="utf-8")
        if EXECUTION_PLAN_MARKER not in plan_text:
            continue
        section_gaps = [
            section for section in EXECUTION_PLAN_REQUIRED_SECTIONS if section not in plan_text
        ]
        if section_gaps:
            missing_sections.append(f"{relative} missing: {', '.join(section_gaps)}")

    return missing_rows, missing_markers, missing_sections
