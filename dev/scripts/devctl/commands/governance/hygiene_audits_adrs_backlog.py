"""ADR numbering/backlog governance checks for hygiene audits."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
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


@dataclass
class AdrSequenceAnalysis:
    missing_sequence_ids: list[int] = field(default_factory=list)
    retired_ids: list[int] = field(default_factory=list)
    reserved_ids: list[int] = field(default_factory=list)
    unexplained_gap_ids: list[int] = field(default_factory=list)
    stale_governed_ids: list[int] = field(default_factory=list)
    retired_ids_set: set[int] = field(default_factory=set, repr=False)
    reserved_ids_set: set[int] = field(default_factory=set, repr=False)


@dataclass
class AdrBacklogAnalysis:
    backlog_master_ids: list[int] = field(default_factory=list)
    backlog_autonomy_ids: list[int] = field(default_factory=list)
    backlog_missing_reserved_ids: list[int] = field(default_factory=list)
    backlog_existing_ids: list[int] = field(default_factory=list)
    reserved_not_backlog_ids: list[int] = field(default_factory=list)
    backlog_scope_mismatch: bool = False


@dataclass
class AdrGovernanceResult:
    missing_sequence_ids: list[int] = field(default_factory=list)
    retired_ids: list[int] = field(default_factory=list)
    reserved_ids: list[int] = field(default_factory=list)
    unexplained_gap_ids: list[int] = field(default_factory=list)
    stale_governed_ids: list[int] = field(default_factory=list)
    backlog_master_ids: list[int] = field(default_factory=list)
    backlog_autonomy_ids: list[int] = field(default_factory=list)
    backlog_missing_reserved_ids: list[int] = field(default_factory=list)
    backlog_existing_ids: list[int] = field(default_factory=list)
    reserved_not_backlog_ids: list[int] = field(default_factory=list)
    backlog_scope_mismatch: bool = False
    next_pointer_value: int | None = None
    next_pointer_expected: int | None = None
    stale_reference_violations: list[dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _analyze_sequence_gaps(
    *,
    tracked_ids_int: list[int],
    index_text: str,
    errors: list[str],
    warnings: list[str],
) -> AdrSequenceAnalysis:
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

    return AdrSequenceAnalysis(
        missing_sequence_ids=missing_sequence_ids,
        retired_ids=sorted(retired_ids_set),
        reserved_ids=sorted(reserved_ids_set),
        unexplained_gap_ids=unexplained_gap_ids,
        stale_governed_ids=stale_governed_ids,
        retired_ids_set=retired_ids_set,
        reserved_ids_set=reserved_ids_set,
    )


def _validate_next_pointer(
    *,
    tracked_ids_int: list[int],
    index_text: str,
    errors: list[str],
) -> tuple[int | None, int]:
    next_pointer_expected = tracked_ids_int[-1] + 1
    next_match = ADR_NEXT_RE.search(index_text)
    next_pointer_value: int | None = None
    if not next_match:
        errors.append(
            "ADR index missing `next: NNNN` process pointer in `dev/adr/README.md`."
        )
        return None, next_pointer_expected
    next_pointer_value = int(next_match.group(1))
    if next_pointer_value != next_pointer_expected:
        errors.append(
            "ADR index next pointer mismatch: expected "
            f"{next_pointer_expected:04d}, found {next_pointer_value:04d}."
        )
    return next_pointer_value, next_pointer_expected


def _load_backlog_scope_ids(repo_root: Path) -> tuple[set[int], set[int]]:
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
    return master_backlog_ids_set, autonomy_backlog_ids_set


def _analyze_backlog_scope(
    *,
    tracked_ids_set: set[int],
    reserved_ids_set: set[int],
    master_backlog_ids_set: set[int],
    autonomy_backlog_ids_set: set[int],
    errors: list[str],
    warnings: list[str],
) -> AdrBacklogAnalysis:
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

    return AdrBacklogAnalysis(
        backlog_master_ids=sorted(master_backlog_ids_set),
        backlog_autonomy_ids=sorted(autonomy_backlog_ids_set),
        backlog_missing_reserved_ids=backlog_missing_reserved_ids,
        backlog_existing_ids=backlog_existing_ids,
        reserved_not_backlog_ids=reserved_not_backlog_ids,
        backlog_scope_mismatch=backlog_scope_mismatch,
    )


def _record_stale_reference_violations(
    *,
    repo_root: Path,
    errors: list[str],
) -> list[dict[str, object]]:
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
    return stale_reference_violations


def analyze_adr_id_governance(
    *,
    tracked_ids_int: list[int],
    index_text: str,
    repo_root: Path,
    errors: list[str],
    warnings: list[str],
) -> dict:
    """Analyze ADR numbering gaps, backlog sync, and stale reference patterns."""
    result = AdrGovernanceResult()
    if not tracked_ids_int:
        return result.to_dict()

    sequence = _analyze_sequence_gaps(
        tracked_ids_int=tracked_ids_int,
        index_text=index_text,
        errors=errors,
        warnings=warnings,
    )
    tracked_ids_set = set(tracked_ids_int)
    next_pointer_value, next_pointer_expected = _validate_next_pointer(
        tracked_ids_int=tracked_ids_int,
        index_text=index_text,
        errors=errors,
    )
    master_backlog_ids_set, autonomy_backlog_ids_set = _load_backlog_scope_ids(repo_root)
    backlog = _analyze_backlog_scope(
        tracked_ids_set=tracked_ids_set,
        reserved_ids_set=sequence.reserved_ids_set,
        master_backlog_ids_set=master_backlog_ids_set,
        autonomy_backlog_ids_set=autonomy_backlog_ids_set,
        errors=errors,
        warnings=warnings,
    )
    stale_reference_violations = _record_stale_reference_violations(
        repo_root=repo_root,
        errors=errors,
    )

    result.missing_sequence_ids = sequence.missing_sequence_ids
    result.retired_ids = sequence.retired_ids
    result.reserved_ids = sequence.reserved_ids
    result.unexplained_gap_ids = sequence.unexplained_gap_ids
    result.stale_governed_ids = sequence.stale_governed_ids
    result.backlog_master_ids = backlog.backlog_master_ids
    result.backlog_autonomy_ids = backlog.backlog_autonomy_ids
    result.backlog_missing_reserved_ids = backlog.backlog_missing_reserved_ids
    result.backlog_existing_ids = backlog.backlog_existing_ids
    result.reserved_not_backlog_ids = backlog.reserved_not_backlog_ids
    result.backlog_scope_mismatch = backlog.backlog_scope_mismatch
    result.next_pointer_value = next_pointer_value
    result.next_pointer_expected = next_pointer_expected
    result.stale_reference_violations = stale_reference_violations
    return result.to_dict()
