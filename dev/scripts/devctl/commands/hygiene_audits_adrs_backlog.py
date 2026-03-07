"""ADR numbering/backlog governance checks for hygiene audits."""

from __future__ import annotations

from pathlib import Path

from .hygiene_audits_adrs_metadata import (
    ADR_NEXT_RE,
    ADR_REF_RE,
    AUTONOMY_ADR_BACKLOG_HEADING,
    MASTER_ADR_BACKLOG_HEADING,
    extract_markdown_section,
    format_adr_ids,
    parse_governed_adr_ids,
    scan_stale_adr_reference_patterns,
)


def analyze_adr_id_governance(
    *,
    tracked_ids_int: list[int],
    index_text: str,
    repo_root: Path,
    errors: list[str],
    warnings: list[str],
) -> dict:
    """Analyze ADR numbering gaps, backlog sync, and stale reference patterns."""
    result = {
        "missing_sequence_ids": [],
        "retired_ids": [],
        "reserved_ids": [],
        "unexplained_gap_ids": [],
        "stale_governed_ids": [],
        "backlog_master_ids": [],
        "backlog_autonomy_ids": [],
        "backlog_missing_reserved_ids": [],
        "backlog_existing_ids": [],
        "reserved_not_backlog_ids": [],
        "backlog_scope_mismatch": False,
        "next_pointer_value": None,
        "next_pointer_expected": None,
        "stale_reference_violations": [],
    }
    if not tracked_ids_int:
        return result

    tracked_ids_set = set(tracked_ids_int)
    missing_sequence_ids = [
        adr_id
        for adr_id in range(tracked_ids_int[0], tracked_ids_int[-1] + 1)
        if adr_id not in tracked_ids_set
    ]
    retired_ids_set = parse_governed_adr_ids(
        index_text,
        label="Retired ADR IDs",
        errors=errors,
    )
    reserved_ids_set = parse_governed_adr_ids(
        index_text,
        label="Reserved ADR IDs",
        errors=errors,
    )
    overlap = sorted(retired_ids_set & reserved_ids_set)
    if overlap:
        errors.append(
            "ADR id governance overlap between Retired and Reserved sets: "
            + format_adr_ids(overlap)
        )

    unexplained_gap_ids: list[int] = []
    stale_governed_ids: list[int] = []
    if missing_sequence_ids:
        unexplained_gap_ids = sorted(
            set(missing_sequence_ids) - retired_ids_set - reserved_ids_set
        )
        stale_governed_ids = sorted(
            (retired_ids_set | reserved_ids_set) - set(missing_sequence_ids)
        )
    if unexplained_gap_ids:
        errors.append(
            "Unexplained ADR numbering gaps detected (document as `Retired ADR IDs` or "
            "`Reserved ADR IDs` in `dev/adr/README.md`): "
            + format_adr_ids(unexplained_gap_ids)
        )
    if stale_governed_ids:
        warnings.append(
            "ADR id governance metadata lists ids that are no longer gaps: "
            + format_adr_ids(stale_governed_ids)
        )

    next_pointer_expected = tracked_ids_int[-1] + 1
    next_match = ADR_NEXT_RE.search(index_text)
    next_pointer_value: int | None = None
    if not next_match:
        errors.append(
            "ADR index missing `next: NNNN` process pointer in `dev/adr/README.md`."
        )
    else:
        next_pointer_value = int(next_match.group(1))
        if next_pointer_value != next_pointer_expected:
            errors.append(
                "ADR index next pointer mismatch: expected "
                f"{next_pointer_expected:04d}, found {next_pointer_value:04d}."
            )

    master_plan_path = repo_root / "dev/active/MASTER_PLAN.md"
    autonomy_plan_path = repo_root / "dev/active/autonomous_control_plane.md"
    master_backlog_ids_set: set[int] = set()
    autonomy_backlog_ids_set: set[int] = set()
    if master_plan_path.exists():
        master_text = master_plan_path.read_text(encoding="utf-8")
        master_backlog_ids_set = {
            int(match.group(1))
            for match in ADR_REF_RE.finditer(
                extract_markdown_section(master_text, MASTER_ADR_BACKLOG_HEADING)
            )
        }
    if autonomy_plan_path.exists():
        autonomy_text = autonomy_plan_path.read_text(encoding="utf-8")
        autonomy_backlog_ids_set = {
            int(match.group(1))
            for match in ADR_REF_RE.finditer(
                extract_markdown_section(autonomy_text, AUTONOMY_ADR_BACKLOG_HEADING)
            )
        }

    backlog_scope_mismatch = False
    if master_backlog_ids_set and autonomy_backlog_ids_set:
        backlog_scope_mismatch = master_backlog_ids_set != autonomy_backlog_ids_set
        if backlog_scope_mismatch:
            master_only = sorted(master_backlog_ids_set - autonomy_backlog_ids_set)
            autonomy_only = sorted(autonomy_backlog_ids_set - master_backlog_ids_set)
            detail_parts: list[str] = []
            if master_only:
                detail_parts.append("MASTER_PLAN-only: " + format_adr_ids(master_only))
            if autonomy_only:
                detail_parts.append(
                    "autonomous_control_plane-only: " + format_adr_ids(autonomy_only)
                )
            errors.append("ADR backlog scope mismatch: " + "; ".join(detail_parts))

    backlog_ids_set = master_backlog_ids_set or autonomy_backlog_ids_set
    backlog_existing_ids = sorted(backlog_ids_set & tracked_ids_set)
    if backlog_existing_ids:
        errors.append(
            "ADR backlog lists ids that already exist as ADR files: "
            + format_adr_ids(backlog_existing_ids)
        )
    backlog_missing_reserved_ids = sorted(
        (backlog_ids_set - tracked_ids_set) - reserved_ids_set
    )
    if backlog_missing_reserved_ids:
        errors.append(
            "ADR backlog ids are missing from `Reserved ADR IDs`: "
            + format_adr_ids(backlog_missing_reserved_ids)
        )
    reserved_not_backlog_ids = sorted(
        reserved_ids_set - (backlog_ids_set - tracked_ids_set)
    )
    if reserved_not_backlog_ids:
        warnings.append(
            "Reserved ADR IDs not present in current backlog scope: "
            + format_adr_ids(reserved_not_backlog_ids)
        )

    stale_reference_violations = scan_stale_adr_reference_patterns(repo_root)
    if stale_reference_violations:
        preview = ", ".join(
            f"{item['file']}:{item['line']} [{item['rule']}]"
            for item in stale_reference_violations[:8]
        )
        remainder = len(stale_reference_violations) - 8
        if remainder > 0:
            preview = f"{preview}, +{remainder} more"
        errors.append(
            "Stale ADR reference patterns detected in governance docs: "
            + preview
            + ". Replace hard-coded ADR counts/ranges with ADR index links or generic wording."
        )

    result.update(
        {
            "missing_sequence_ids": missing_sequence_ids,
            "retired_ids": sorted(retired_ids_set),
            "reserved_ids": sorted(reserved_ids_set),
            "unexplained_gap_ids": unexplained_gap_ids,
            "stale_governed_ids": stale_governed_ids,
            "backlog_master_ids": sorted(master_backlog_ids_set),
            "backlog_autonomy_ids": sorted(autonomy_backlog_ids_set),
            "backlog_missing_reserved_ids": backlog_missing_reserved_ids,
            "backlog_existing_ids": backlog_existing_ids,
            "reserved_not_backlog_ids": reserved_not_backlog_ids,
            "backlog_scope_mismatch": backlog_scope_mismatch,
            "next_pointer_value": next_pointer_value,
            "next_pointer_expected": next_pointer_expected,
            "stale_reference_violations": stale_reference_violations,
        }
    )
    return result
