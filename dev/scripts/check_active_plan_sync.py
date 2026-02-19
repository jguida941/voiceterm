#!/usr/bin/env python3
"""Validate dev/active plan registry and cross-doc synchronization contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ACTIVE_DIR = REPO_ROOT / "dev/active"
INDEX_PATH = ACTIVE_DIR / "INDEX.md"
MASTER_PLAN_PATH = ACTIVE_DIR / "MASTER_PLAN.md"

ALLOWED_ROLES = {"tracker", "spec", "runbook", "reference"}
ALLOWED_AUTHORITIES = {"canonical", "mirrored in MASTER_PLAN", "supporting", "reference-only"}

REQUIRED_REGISTRY_ROWS = {
    "dev/active/MASTER_PLAN.md": {"role": "tracker", "authority": "canonical"},
    "dev/active/theme_upgrade.md": {"role": "spec", "authority": "mirrored in MASTER_PLAN"},
    "dev/active/memory_studio.md": {"role": "spec", "authority": "mirrored in MASTER_PLAN"},
    "dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md": {"role": "runbook"},
    "dev/active/overlay.md": {"role": "reference"},
}

REQUIRED_DISCOVERY_REFERENCES = [
    {"path": "AGENTS.md", "tokens": ["dev/active/INDEX.md"]},
    {"path": "DEV_INDEX.md", "tokens": ["dev/active/INDEX.md"]},
    {"path": "dev/README.md", "tokens": ["active/INDEX.md", "dev/active/INDEX.md"]},
]

REQUIRED_AGENT_MARKERS = [
    "## Active-plan onboarding (adding files under `dev/active/`)",
    "Add an entry in `dev/active/INDEX.md`",
    "Run `python3 dev/scripts/check_active_plan_sync.py`",
]

SPEC_RANGE_PATHS = [
    "dev/active/theme_upgrade.md",
    "dev/active/memory_studio.md",
]


def _strip_code_ticks(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def _parse_registry_rows(index_text: str) -> list[dict]:
    rows: list[dict] = []
    for line in index_text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        columns = [col.strip() for col in line.strip().split("|")[1:-1]]
        if len(columns) < 5:
            continue
        first = columns[0].lower()
        if first == "path" or set(first) <= {"-", ":"}:
            continue
        rows.append(
            {
                "path": _strip_code_ticks(columns[0]),
                "role": _strip_code_ticks(columns[1]),
                "authority": _strip_code_ticks(columns[2]),
                "mp_scope": _strip_code_ticks(columns[3]),
                "when_read": _strip_code_ticks(columns[4]),
            }
        )
    return rows


def _expand_mp_ranges(text: str) -> set[str]:
    mp_ids: set[str] = set()
    for start_s, end_s in re.findall(r"MP-(\d{3})\.\.MP-(\d{3})", text):
        start = int(start_s)
        end = int(end_s)
        if start > end:
            start, end = end, start
        for value in range(start, end + 1):
            mp_ids.add(f"MP-{value:03d}")
    return mp_ids


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
    registry_rows = _parse_registry_rows(index_text)

    if not registry_rows:
        errors.append("No registry rows found in dev/active/INDEX.md.")

    registry_by_path: dict[str, dict] = {}
    duplicate_paths: list[str] = []
    invalid_role_paths: list[str] = []
    invalid_authority_paths: list[str] = []
    missing_registry_files: list[str] = []

    for row in registry_rows:
        path = row["path"]
        if path in registry_by_path:
            duplicate_paths.append(path)
        registry_by_path[path] = row
        if row["role"] not in ALLOWED_ROLES:
            invalid_role_paths.append(f"{path} ({row['role']})")
        if row["authority"] not in ALLOWED_AUTHORITIES:
            invalid_authority_paths.append(f"{path} ({row['authority']})")
        target = REPO_ROOT / path
        if not target.exists():
            missing_registry_files.append(path)

    active_markdown_files = sorted(
        str(path.relative_to(REPO_ROOT))
        for path in ACTIVE_DIR.glob("*.md")
        if path.name != "INDEX.md"
    )
    registry_paths = sorted(path for path in registry_by_path if path != "dev/active/INDEX.md")

    unindexed_active_files = sorted(path for path in active_markdown_files if path not in registry_by_path)
    registry_paths_not_active = sorted(path for path in registry_paths if path not in active_markdown_files)

    tracker_paths = sorted(
        row["path"] for row in registry_rows if row["role"] == "tracker"
    )
    if len(tracker_paths) != 1 or tracker_paths[0] != "dev/active/MASTER_PLAN.md":
        errors.append(
            "Registry must declare exactly one tracker and it must be dev/active/MASTER_PLAN.md."
        )

    missing_required_rows: list[str] = []
    required_row_mismatches: list[str] = []
    for path, expected in REQUIRED_REGISTRY_ROWS.items():
        row = registry_by_path.get(path)
        if not row:
            missing_required_rows.append(path)
            continue
        for key, expected_value in expected.items():
            actual_value = row.get(key)
            if actual_value != expected_value:
                required_row_mismatches.append(
                    f"{path} expected {key}={expected_value}, found {actual_value}"
                )

    if not MASTER_PLAN_PATH.exists():
        errors.append("Missing dev/active/MASTER_PLAN.md.")
        master_plan_text = ""
    else:
        master_plan_text = MASTER_PLAN_PATH.read_text(encoding="utf-8")

    spec_missing_mirror_markers: list[str] = []
    spec_missing_ranges: list[str] = []
    spec_range_drift: list[str] = []
    mirror_marker = "execution mirrored in `dev/active/MASTER_PLAN.md`"

    for relative in SPEC_RANGE_PATHS:
        spec_path = REPO_ROOT / relative
        if not spec_path.exists():
            continue
        spec_text = spec_path.read_text(encoding="utf-8")
        if mirror_marker not in spec_text:
            spec_missing_mirror_markers.append(relative)
        range_ids = _expand_mp_ranges(spec_text)
        if not range_ids:
            spec_missing_ranges.append(relative)
            continue
        missing_from_master = sorted(mp_id for mp_id in range_ids if mp_id not in master_plan_text)
        if missing_from_master:
            spec_range_drift.append(f"{relative} -> missing in MASTER_PLAN: {', '.join(missing_from_master)}")

    missing_discovery_refs: list[str] = []
    for ref in REQUIRED_DISCOVERY_REFERENCES:
        path = REPO_ROOT / ref["path"]
        if not path.exists():
            missing_discovery_refs.append(f"{ref['path']} (file missing)")
            continue
        text = path.read_text(encoding="utf-8")
        if not any(token in text for token in ref["tokens"]):
            missing_discovery_refs.append(ref["path"])

    agent_marker_gaps: list[str] = []
    agents_path = REPO_ROOT / "AGENTS.md"
    if agents_path.exists():
        agents_text = agents_path.read_text(encoding="utf-8")
        for marker in REQUIRED_AGENT_MARKERS:
            if marker not in agents_text:
                agent_marker_gaps.append(marker)
    else:
        missing_discovery_refs.append("AGENTS.md (file missing)")

    if duplicate_paths:
        errors.append(f"Duplicate registry rows: {', '.join(sorted(set(duplicate_paths)))}")
    if invalid_role_paths:
        errors.append(f"Invalid registry roles: {', '.join(sorted(invalid_role_paths))}")
    if invalid_authority_paths:
        errors.append(f"Invalid registry authorities: {', '.join(sorted(invalid_authority_paths))}")
    if missing_registry_files:
        errors.append(f"Registry references missing files: {', '.join(sorted(missing_registry_files))}")
    if unindexed_active_files:
        errors.append(f"Active markdown files missing from registry: {', '.join(unindexed_active_files)}")
    if registry_paths_not_active:
        errors.append(f"Registry includes non-active paths: {', '.join(registry_paths_not_active)}")
    if missing_required_rows:
        errors.append(f"Missing required registry rows: {', '.join(missing_required_rows)}")
    if required_row_mismatches:
        errors.append(f"Required row mismatches: {'; '.join(required_row_mismatches)}")
    if spec_missing_mirror_markers:
        errors.append(
            "Spec docs missing master-plan mirror marker: " + ", ".join(spec_missing_mirror_markers)
        )
    if spec_missing_ranges:
        warnings.append("Spec docs missing MP range declarations: " + ", ".join(spec_missing_ranges))
    if spec_range_drift:
        errors.append("Spec MP ranges not found in MASTER_PLAN: " + " | ".join(spec_range_drift))
    if missing_discovery_refs:
        errors.append("Missing active-index discovery references: " + ", ".join(missing_discovery_refs))
    if agent_marker_gaps:
        errors.append("AGENTS active-plan onboarding markers missing: " + ", ".join(agent_marker_gaps))

    return {
        "command": "check_active_plan_sync",
        "ok": not errors,
        "index_path": str(INDEX_PATH.relative_to(REPO_ROOT)),
        "active_markdown_files": active_markdown_files,
        "registry_paths": registry_paths,
        "tracker_paths": tracker_paths,
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
    lines.append(f"- active_markdown_files: {len(report.get('active_markdown_files', []))}")
    lines.append(f"- registry_paths: {len(report.get('registry_paths', []))}")
    lines.append(
        "- tracker_paths: "
        + (", ".join(report.get("tracker_paths", [])) or "none")
    )
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

