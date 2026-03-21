"""Shared execution-plan contract validation for active docs."""

from __future__ import annotations

import re
from pathlib import Path

REQUIRED_EXECUTION_PLAN_DOCS = [
    "dev/active/theme_upgrade.md",
    "dev/active/ai_governance_platform.md",
    "dev/active/autonomous_control_plane.md",
    "dev/active/code_shape_expansion.md",
    "dev/active/review_channel.md",
    "dev/active/host_process_hygiene.md",
    "dev/active/continuous_swarm.md",
    "dev/active/operator_console.md",
    "dev/active/loop_chat_bridge.md",
    "dev/active/naming_api_cohesion.md",
    "dev/active/ide_provider_modularization.md",
    "dev/active/pre_release_architecture_audit.md",
    "dev/active/platform_authority_loop.md",
    "dev/active/portable_code_governance.md",
    "dev/active/ralph_guardrail_control_plane.md",
    "dev/active/review_probes.md",
    "dev/active/slash_command_standalone.md",
]
EXECUTION_PLAN_MARKER = "Execution plan contract: required"
EXECUTION_PLAN_REQUIRED_SECTIONS = [
    "## Scope",
    "## Execution Checklist",
    "## Progress Log",
    "## Session Resume",
    "## Audit Evidence",
]
_METADATA_HEADER_PATTERNS = (
    re.compile(r"^\*\*Status\*\*:", re.IGNORECASE),
    re.compile(r"^Status:", re.IGNORECASE),
    re.compile(r"^\d{4}-\d{2}-\d{2}\s*\|"),
)


def _has_metadata_header(plan_text: str) -> bool:
    for line in plan_text.splitlines()[:10]:
        stripped = line.strip()
        if not stripped:
            continue
        if any(pattern.search(stripped) for pattern in _METADATA_HEADER_PATTERNS):
            return True
    return False


def validate_execution_plan_contract(
    *,
    repo_root: Path,
    active_markdown_files: list[str],
    registry_by_path: dict[str, dict],
) -> tuple[list[str], list[str], list[str], list[str]]:
    missing_rows: list[str] = []
    missing_markers: list[str] = []
    missing_sections: list[str] = []
    missing_metadata_headers: list[str] = []

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
        if not _has_metadata_header(plan_text):
            missing_metadata_headers.append(relative)
        section_gaps = [
            section
            for section in EXECUTION_PLAN_REQUIRED_SECTIONS
            if section not in plan_text
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
        if relative not in registry_by_path and relative not in missing_rows:
            missing_rows.append(relative)
        if not _has_metadata_header(plan_text):
            missing_metadata_headers.append(relative)
        section_gaps = [
            section
            for section in EXECUTION_PLAN_REQUIRED_SECTIONS
            if section not in plan_text
        ]
        if section_gaps:
            missing_sections.append(f"{relative} missing: {', '.join(section_gaps)}")

    return (
        list(dict.fromkeys(missing_rows)),
        list(dict.fromkeys(missing_markers)),
        list(dict.fromkeys(missing_sections)),
        list(dict.fromkeys(missing_metadata_headers)),
    )
