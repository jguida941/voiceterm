#!/usr/bin/env python3
"""Validate dev/active plan registry and cross-doc synchronization contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys

try:
    from dev.scripts.checks.active_plan.contract import (
        EXECUTION_PLAN_MARKER,
        validate_execution_plan_contract,
    )
    from dev.scripts.checks.active_plan.sync_report import (
        append_issue_message,
        collect_active_doc_state,
        collect_discovery_gaps,
        collect_registry_state,
        collect_spec_sync_issues,
        parse_registry_rows,
        validate_required_registry_rows,
    )
    from dev.scripts.checks.active_plan.snapshot import (
        latest_git_semver_tag,
        parse_master_plan_snapshot,
        read_cargo_release_tag,
        read_master_plan_text,
        validate_snapshot_policy,
    )
except ModuleNotFoundError:
    from active_plan.contract import (
        EXECUTION_PLAN_MARKER,
        validate_execution_plan_contract,
    )
    from active_plan.sync_report import (
        append_issue_message,
        collect_active_doc_state,
        collect_discovery_gaps,
        collect_registry_state,
        collect_spec_sync_issues,
        parse_registry_rows,
        validate_required_registry_rows,
    )
    from active_plan.snapshot import (
        latest_git_semver_tag,
        parse_master_plan_snapshot,
        read_cargo_release_tag,
        read_master_plan_text,
        validate_snapshot_policy,
    )

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
ACTIVE_DIR = REPO_ROOT / "dev/active"
INDEX_PATH = ACTIVE_DIR / "INDEX.md"
MASTER_PLAN_PATH = ACTIVE_DIR / "MASTER_PLAN.md"

ALLOWED_ROLES = {"tracker", "spec", "runbook", "reference"}
ALLOWED_AUTHORITIES = {
    "canonical",
    "mirrored in MASTER_PLAN",
    "supporting",
    "reference-only",
}

REQUIRED_REGISTRY_ROWS = {
    "dev/active/MASTER_PLAN.md": {"role": "tracker", "authority": "canonical"},
    "dev/active/theme_upgrade.md": {
        "role": "spec",
        "authority": "mirrored in MASTER_PLAN",
    },
    "dev/active/memory_studio.md": {
        "role": "spec",
        "authority": "mirrored in MASTER_PLAN",
    },
    "dev/active/devctl_reporting_upgrade.md": {
        "role": "spec",
        "authority": "mirrored in MASTER_PLAN",
    },
    "dev/active/autonomous_control_plane.md": {
        "role": "spec",
        "authority": "mirrored in MASTER_PLAN",
    },
    "dev/active/loop_chat_bridge.md": {"role": "runbook", "authority": "supporting"},
    "dev/active/naming_api_cohesion.md": {
        "role": "spec",
        "authority": "mirrored in MASTER_PLAN",
    },
    "dev/active/ide_provider_modularization.md": {
        "role": "spec",
        "authority": "mirrored in MASTER_PLAN",
    },
    "dev/active/review_channel.md": {
        "role": "spec",
        "authority": "mirrored in MASTER_PLAN",
    },
    "dev/active/host_process_hygiene.md": {
        "role": "spec",
        "authority": "mirrored in MASTER_PLAN",
    },
    "dev/active/continuous_swarm.md": {
        "role": "spec",
        "authority": "mirrored in MASTER_PLAN",
    },
    "dev/active/operator_console.md": {
        "role": "spec",
        "authority": "mirrored in MASTER_PLAN",
    },
    "dev/active/pre_release_architecture_audit.md": {
        "role": "spec",
        "authority": "mirrored in MASTER_PLAN",
    },
    "dev/active/slash_command_standalone.md": {
        "role": "spec",
        "authority": "mirrored in MASTER_PLAN",
    },
    "dev/active/phase2.md": {"role": "reference", "authority": "reference-only"},
}

REQUIRED_DISCOVERY_REFERENCES = [
    {"path": "AGENTS.md", "tokens": ["dev/active/INDEX.md"]},
    {"path": "dev/README.md", "tokens": ["active/INDEX.md", "dev/active/INDEX.md"]},
]

REQUIRED_AGENT_MARKERS = [
    "## Active-plan onboarding (adding files under `dev/active/`)",
    "Add an entry in `dev/active/INDEX.md`",
    "Run `python3 dev/scripts/checks/check_active_plan_sync.py`",
]
SPEC_RANGE_PATHS = [
    "dev/active/theme_upgrade.md",
    "dev/active/memory_studio.md",
    "dev/active/devctl_reporting_upgrade.md",
    "dev/active/autonomous_control_plane.md",
    "dev/active/host_process_hygiene.md",
    "dev/active/continuous_swarm.md",
    "dev/active/operator_console.md",
    "dev/active/naming_api_cohesion.md",
    "dev/active/ide_provider_modularization.md",
    "dev/active/pre_release_architecture_audit.md",
    "dev/active/review_channel.md",
    "dev/active/slash_command_standalone.md",
]

EXPECTED_ACTIVE_DEVELOPMENT_BRANCH = "develop"
EXPECTED_RELEASE_BRANCH = "master"
SEMVER_TAG_PATTERN = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
PHASE_HEADING_PATTERN = re.compile(
    r"^##+\s+.*\bPhas(?:e|ed)\b", re.IGNORECASE | re.MULTILINE
)

def _build_report() -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if not INDEX_PATH.exists():
        return {
            "command": "check_active_plan_sync",
            "ok": False,
            "error": f"Missing file: {INDEX_PATH.relative_to(REPO_ROOT)}",
        }

    index_text = INDEX_PATH.read_text(encoding="utf-8")
    registry_rows = parse_registry_rows(index_text)
    if not registry_rows:
        errors.append("No registry rows found in dev/active/INDEX.md.")
    registry_state = collect_registry_state(
        registry_rows,
        repo_root=REPO_ROOT,
        allowed_roles=ALLOWED_ROLES,
        allowed_authorities=ALLOWED_AUTHORITIES,
    )
    registry_by_path = registry_state["registry_by_path"]
    active_doc_state = collect_active_doc_state(
        repo_root=REPO_ROOT,
        active_dir=ACTIVE_DIR,
        registry_by_path=registry_by_path,
    )
    active_markdown_files = active_doc_state["active_markdown_files"]
    registry_paths = active_doc_state["registry_paths"]

    tracker_paths = sorted(
        row["path"] for row in registry_rows if row["role"] == "tracker"
    )
    if len(tracker_paths) != 1 or tracker_paths[0] != "dev/active/MASTER_PLAN.md":
        errors.append(
            "Registry must declare exactly one tracker and it must be dev/active/MASTER_PLAN.md."
        )

    missing_required_rows, required_row_mismatches = validate_required_registry_rows(
        registry_by_path,
        required_registry_rows=REQUIRED_REGISTRY_ROWS,
    )
    master_plan_text, master_plan_errors = read_master_plan_text(MASTER_PLAN_PATH)
    errors.extend(master_plan_errors)

    snapshot_values: dict[str, str | None] = {
        "status_date": None,
        "last_tagged_release": None,
        "last_tagged_release_date": None,
        "current_release_target": None,
        "active_development_branch": None,
        "release_branch": None,
    }
    cargo_release_tag = read_cargo_release_tag(REPO_ROOT / "rust/Cargo.toml")
    latest_git_tag = None
    if master_plan_text:
        snapshot_values, snapshot_errors = parse_master_plan_snapshot(master_plan_text)
        errors.extend(snapshot_errors)
        latest_git_tag, git_tag_error = latest_git_semver_tag(
            REPO_ROOT, SEMVER_TAG_PATTERN
        )
        if git_tag_error:
            warnings.append(f"Unable to read latest git release tag: {git_tag_error}")
        snapshot_policy_errors, snapshot_policy_warnings = validate_snapshot_policy(
            snapshot_values,
            expected_active_development_branch=EXPECTED_ACTIVE_DEVELOPMENT_BRANCH,
            expected_release_branch=EXPECTED_RELEASE_BRANCH,
            latest_git_tag=latest_git_tag,
            cargo_release_tag=cargo_release_tag,
        )
        errors.extend(snapshot_policy_errors)
        warnings.extend(snapshot_policy_warnings)

    spec_issues = collect_spec_sync_issues(
        repo_root=REPO_ROOT,
        spec_range_paths=SPEC_RANGE_PATHS,
        registry_by_path=registry_by_path,
        master_plan_text=master_plan_text,
        execution_plan_marker=EXECUTION_PLAN_MARKER,
        phase_heading_pattern=PHASE_HEADING_PATTERN,
    )

    (
        execution_plan_missing_rows,
        execution_plan_missing_markers,
        execution_plan_missing_sections,
        execution_plan_missing_metadata_headers,
    ) = validate_execution_plan_contract(
        repo_root=REPO_ROOT,
        active_markdown_files=active_markdown_files,
        registry_by_path=registry_by_path,
    )

    missing_discovery_refs, agent_marker_gaps = collect_discovery_gaps(
        repo_root=REPO_ROOT,
        required_discovery_refs=REQUIRED_DISCOVERY_REFERENCES,
        required_agent_markers=REQUIRED_AGENT_MARKERS,
    )

    append_issue_message(
        errors,
        sorted(set(registry_state["duplicate_paths"])),
        prefix="Duplicate registry rows: ",
    )
    append_issue_message(
        errors,
        sorted(registry_state["invalid_role_paths"]),
        prefix="Invalid registry roles: ",
    )
    append_issue_message(
        errors,
        sorted(registry_state["invalid_authority_paths"]),
        prefix="Invalid registry authorities: ",
    )
    append_issue_message(
        errors,
        sorted(registry_state["missing_registry_files"]),
        prefix="Registry references missing files: ",
    )
    append_issue_message(
        errors,
        active_doc_state["unindexed_active_files"],
        prefix="Active markdown files missing from registry: ",
    )
    append_issue_message(
        errors,
        active_doc_state["registry_paths_not_active"],
        prefix="Registry includes non-active paths: ",
    )
    append_issue_message(
        errors,
        missing_required_rows,
        prefix="Missing required registry rows: ",
    )
    append_issue_message(
        errors,
        required_row_mismatches,
        prefix="Required row mismatches: ",
        joiner="; ",
    )
    append_issue_message(
        errors,
        spec_issues["spec_missing_mirror_markers"],
        prefix="Spec docs missing master-plan mirror marker or execution-plan contract marker: ",
    )
    append_issue_message(
        errors,
        spec_issues["spec_missing_phase_headings"],
        prefix="Spec docs missing phase-structured headings: ",
    )
    append_issue_message(
        errors,
        spec_issues["spec_missing_master_links"],
        prefix="Spec docs missing explicit MASTER_PLAN links: ",
    )
    append_issue_message(
        warnings,
        spec_issues["spec_missing_ranges"],
        prefix="Spec docs missing MP scope declarations: ",
    )
    append_issue_message(
        errors,
        spec_issues["spec_range_drift"],
        prefix="Spec MP ranges not found in MASTER_PLAN: ",
        joiner=" | ",
    )
    append_issue_message(
        errors,
        spec_issues["index_scope_missing"],
        prefix="INDEX rows missing MP ranges for spec docs: ",
    )
    append_issue_message(
        errors,
        spec_issues["index_scope_drift"],
        prefix="INDEX MP scope drift vs spec docs: ",
        joiner=" | ",
    )
    append_issue_message(
        errors,
        execution_plan_missing_rows,
        prefix="Required execution-plan docs missing from INDEX registry: ",
    )
    append_issue_message(
        errors,
        execution_plan_missing_markers,
        prefix="Execution-plan marker missing in required docs: ",
    )
    append_issue_message(
        errors,
        sorted(set(execution_plan_missing_sections)),
        prefix="Execution-plan required sections missing: ",
        joiner=" | ",
    )
    append_issue_message(
        errors,
        sorted(set(execution_plan_missing_metadata_headers)),
        prefix="Execution-plan metadata headers missing: ",
    )
    append_issue_message(
        errors,
        missing_discovery_refs,
        prefix="Missing active-index discovery references: ",
    )
    append_issue_message(
        errors,
        agent_marker_gaps,
        prefix="AGENTS active-plan onboarding markers missing: ",
    )

    return {
        "command": "check_active_plan_sync",
        "ok": not errors,
        "index_path": str(INDEX_PATH.relative_to(REPO_ROOT)),
        "active_markdown_files": active_markdown_files,
        "registry_paths": registry_paths,
        "tracker_paths": tracker_paths,
        "snapshot": snapshot_values,
        "latest_git_tag": latest_git_tag,
        "cargo_release_tag": cargo_release_tag,
        "errors": errors,
        "warnings": warnings,
    }


def _render_md(report: dict) -> str:
    lines = ["# check_active_plan_sync", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    if "error" in report:
        lines.append(f"- error: {report['error']}")
        return "\n".join(lines)

    lines.append(f"- index: {report['index_path']}")
    lines.append(
        f"- active_markdown_files: {len(report.get('active_markdown_files', []))}"
    )
    lines.append(f"- registry_paths: {len(report.get('registry_paths', []))}")
    lines.append(
        "- tracker_paths: " + (", ".join(report.get("tracker_paths", [])) or "none")
    )
    snapshot = report.get("snapshot", {})
    for key in (
        "last_tagged_release",
        "current_release_target",
        "active_development_branch",
        "release_branch",
    ):
        lines.append(f"- snapshot_{key}: {snapshot.get(key) or 'missing'}")
    lines.append("- latest_git_tag: " + (report.get("latest_git_tag") or "none"))
    lines.append("- cargo_release_tag: " + (report.get("cargo_release_tag") or "none"))
    lines.append(
        "- warnings: "
        + (", ".join(report.get("warnings", [])) if report.get("warnings") else "none")
    )
    lines.append(
        "- errors: "
        + (", ".join(report.get("errors", [])) if report.get("errors") else "none")
    )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = _build_report()

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())
