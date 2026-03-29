"""Support helpers for active-plan sync report construction."""

from __future__ import annotations

import re
from pathlib import Path


def strip_code_ticks(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def parse_registry_rows(index_text: str) -> list[dict]:
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
                "path": strip_code_ticks(columns[0]),
                "role": strip_code_ticks(columns[1]),
                "authority": strip_code_ticks(columns[2]),
                "mp_scope": strip_code_ticks(columns[3]),
                "when_read": strip_code_ticks(columns[4]),
            }
        )
    return rows


def expand_mp_ranges(text: str) -> set[str]:
    mp_ids: set[str] = set()
    for value_s in re.findall(r"MP-(\d{3})", text):
        mp_ids.add(f"MP-{value_s}")
    for start_s, end_s in re.findall(r"MP-(\d{3})\.\.MP-(\d{3})", text):
        start = int(start_s)
        end = int(end_s)
        if start > end:
            start, end = end, start
        for value in range(start, end + 1):
            mp_ids.add(f"MP-{value:03d}")
    return mp_ids


def extract_scope_section(text: str) -> str:
    match = re.search(r"^## Scope\s*$([\s\S]*?)(?=^##\s)", text, re.MULTILINE)
    if match is None:
        return ""
    return match.group(1)


def resolve_spec_range_ids(
    spec_text: str,
    *,
    execution_plan_marker: str,
    index_scope_ids: set[str],
) -> set[str]:
    mirror_marker = "execution mirrored in `dev/active/MASTER_PLAN.md`"
    mirror_line = next(
        (line for line in spec_text.splitlines() if mirror_marker in line),
        "",
    )
    spec_range_ids = expand_mp_ranges(mirror_line)
    if spec_range_ids:
        return spec_range_ids

    scope_section = extract_scope_section(spec_text)
    spec_range_ids = expand_mp_ranges(scope_section)
    if spec_range_ids:
        return spec_range_ids

    if execution_plan_marker in spec_text and index_scope_ids:
        return set(index_scope_ids)

    return expand_mp_ranges(spec_text)


def collect_registry_state(
    registry_rows: list[dict],
    *,
    repo_root: Path,
    allowed_roles: set[str],
    allowed_authorities: set[str],
) -> dict[str, object]:
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
        if row["role"] not in allowed_roles:
            invalid_role_paths.append(f"{path} ({row['role']})")
        if row["authority"] not in allowed_authorities:
            invalid_authority_paths.append(f"{path} ({row['authority']})")
        if not (repo_root / path).exists():
            missing_registry_files.append(path)

    return {
        "registry_by_path": registry_by_path,
        "duplicate_paths": duplicate_paths,
        "invalid_role_paths": invalid_role_paths,
        "invalid_authority_paths": invalid_authority_paths,
        "missing_registry_files": missing_registry_files,
    }


def collect_active_doc_state(
    *,
    repo_root: Path,
    active_dir: Path,
    registry_by_path: dict[str, dict],
) -> dict[str, object]:
    active_markdown_files = sorted(
        str(path.relative_to(repo_root))
        for path in active_dir.glob("*.md")
        if path.name != "INDEX.md"
    )
    registry_paths = sorted(
        path for path in registry_by_path if path != "dev/active/INDEX.md"
    )
    unindexed_active_files = sorted(
        path for path in active_markdown_files if path not in registry_by_path
    )
    registry_paths_not_active = sorted(
        path for path in registry_paths if path not in active_markdown_files
    )
    return {
        "active_markdown_files": active_markdown_files,
        "registry_paths": registry_paths,
        "unindexed_active_files": unindexed_active_files,
        "registry_paths_not_active": registry_paths_not_active,
    }


def validate_required_registry_rows(
    registry_by_path: dict[str, dict],
    *,
    required_registry_rows: dict[str, dict[str, str]],
) -> tuple[list[str], list[str]]:
    missing_required_rows: list[str] = []
    required_row_mismatches: list[str] = []
    for path, expected in required_registry_rows.items():
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
    return missing_required_rows, required_row_mismatches


def collect_spec_sync_issues(
    *,
    repo_root: Path,
    spec_range_paths: list[str],
    registry_by_path: dict[str, dict],
    master_plan_text: str,
    execution_plan_marker: str,
    phase_heading_pattern: re.Pattern[str],
) -> dict[str, list[str]]:
    issues = {
        "spec_missing_mirror_markers": [],
        "spec_missing_ranges": [],
        "spec_range_drift": [],
        "index_scope_missing": [],
        "index_scope_drift": [],
        "spec_missing_phase_headings": [],
        "spec_missing_master_links": [],
    }
    mirror_marker = "execution mirrored in `dev/active/MASTER_PLAN.md`"

    for relative in spec_range_paths:
        spec_path = repo_root / relative
        if not spec_path.exists():
            continue
        spec_text = spec_path.read_text(encoding="utf-8")
        if mirror_marker not in spec_text and execution_plan_marker not in spec_text:
            issues["spec_missing_mirror_markers"].append(relative)
        if not phase_heading_pattern.search(spec_text):
            issues["spec_missing_phase_headings"].append(relative)
        if relative not in master_plan_text:
            issues["spec_missing_master_links"].append(relative)

        index_row = registry_by_path.get(relative)
        index_scope_ids = (
            expand_mp_ranges(index_row.get("mp_scope", "")) if index_row else set()
        )
        spec_range_ids = resolve_spec_range_ids(
            spec_text,
            execution_plan_marker=execution_plan_marker,
            index_scope_ids=index_scope_ids,
        )
        if not spec_range_ids:
            issues["spec_missing_ranges"].append(relative)
            continue

        missing_from_master = sorted(
            mp_id for mp_id in spec_range_ids if mp_id not in master_plan_text
        )
        if missing_from_master:
            issues["spec_range_drift"].append(
                f"{relative} -> missing in MASTER_PLAN: {', '.join(missing_from_master)}"
            )

        if not index_row:
            continue
        if not index_scope_ids:
            issues["index_scope_missing"].append(relative)
            continue
        if index_scope_ids != spec_range_ids:
            details: list[str] = []
            spec_only = sorted(spec_range_ids - index_scope_ids)
            index_only = sorted(index_scope_ids - spec_range_ids)
            if spec_only:
                details.append("missing_in_index=" + ",".join(spec_only))
            if index_only:
                details.append("index_extra=" + ",".join(index_only))
            issues["index_scope_drift"].append(f"{relative} ({'; '.join(details)})")

    return issues


def collect_discovery_gaps(
    *,
    repo_root: Path,
    required_discovery_refs: list[dict[str, list[str] | str]],
    required_agent_markers: list[str],
) -> tuple[list[str], list[str]]:
    missing_discovery_refs: list[str] = []
    for ref in required_discovery_refs:
        path = repo_root / str(ref["path"])
        if not path.exists():
            missing_discovery_refs.append(f"{ref['path']} (file missing)")
            continue
        text = path.read_text(encoding="utf-8")
        tokens = [str(token) for token in ref["tokens"]]
        if not any(token in text for token in tokens):
            missing_discovery_refs.append(str(ref["path"]))

    agent_marker_gaps: list[str] = []
    agents_path = repo_root / "AGENTS.md"
    if not agents_path.exists():
        missing_discovery_refs.append("AGENTS.md (file missing)")
        return missing_discovery_refs, agent_marker_gaps

    agents_text = agents_path.read_text(encoding="utf-8")
    for marker in required_agent_markers:
        if marker not in agents_text:
            agent_marker_gaps.append(marker)
    return missing_discovery_refs, agent_marker_gaps


def append_issue_message(
    bucket: list[str],
    issues: list[str],
    *,
    prefix: str,
    joiner: str = ", ",
) -> None:
    if issues:
        bucket.append(prefix + joiner.join(issues))
