#!/usr/bin/env python3
"""Fail when conflicting child patches lack typed merge-conflict disposition.

G37 Multi-Actor Merge Conflict Guard. Sits inside the A18 multi-actor
coordination contract together with G30-G39. When two or more child actors
submit patches for the same PlanRow that overlap in write scope (path,
symbol, packet target, receipt target, worktree, or branch), the merge must
carry a typed ``conflict_disposition``, a ``merge_coordinator_id`` for the
parent role coordinator that owned the merge, the ``lease_refs`` that the
child patches held when they made the change, and a ``post_merge_proof``
receipt. Without those four typed fields a merge cannot promote child
patches into the role-level proof chain.

Acceptance (delete_after_ingest.md G37):

* When two or more child patches overlap or conflict, every conflict row
  must declare a typed ``conflict_disposition`` from the allowed vocabulary.
* Each conflict row must reference the ``merge_coordinator_id`` (the parent
  role coordinator actor) that owned the merge decision.
* Each conflict row must carry the typed write-lease references held by the
  conflicting child patches, so the lease audit chain stays intact.
* Each conflict row must carry a ``post_merge_proof`` receipt id so the
  merge result is provable after the fact.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        matches_row as _matches_row,
        packet_row_id as _packet_row_id,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        matches_row as _matches_row,
        packet_row_id as _packet_row_id,
        utc_timestamp,
    )


COMMAND = "check_multi_actor_merge_conflict"
CONTRACT_ID = "MultiActorMergeConflictGuard"

# Rule identifiers for typed violations.
RULE_CONFLICTING_PATCHES_NO_DISPOSITION = "conflicting_patches_no_disposition"
RULE_MISSING_MERGE_COORDINATOR_ID = "missing_merge_coordinator_id"
RULE_MISSING_LEASE_REFS = "missing_lease_refs"
RULE_MISSING_POST_MERGE_PROOF = "missing_post_merge_proof"

DISPLAY_TEXT = (
    "Multi-actor merge-conflict violation. Conflicting child patches must "
    "carry a typed conflict disposition, a merge coordinator id, lease "
    "refs, and a post-merge proof receipt before the merge can promote "
    "into the role-level proof chain."
)

# Conflict disposition vocabulary accepted by the role coordinator.
SUPPORTED_DISPOSITIONS: frozenset[str] = frozenset(
    {
        "accept_a_reject_b",
        "accept_b_reject_a",
        "accept_both_merged",
        "reject_both",
        "supersede_by_third_patch",
        "split_scope_no_overlap",
        "escalate_to_human",
    }
)

# Write-scope keys evaluated for overlap between child patches.
OVERLAP_SCOPE_FIELDS: tuple[str, ...] = (
    "paths",
    "symbols",
    "packet_targets",
    "receipt_targets",
    "worktrees",
    "branches",
)


@dataclass(frozen=True, slots=True)
class MergeConflictViolation:
    """Typed violation row for the G37 guard."""

    rule_id: str
    conflict_id: str
    detail: str
    remediation: str
    child_patch_ids: tuple[str, ...] = ()
    overlap_fields: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "conflict_id": self.conflict_id,
            "detail": self.detail,
            "remediation": self.remediation,
            "child_patch_ids": list(self.child_patch_ids),
            "overlap_fields": list(self.overlap_fields),
        }


def build_report(
    *,
    child_patches: Sequence[Mapping[str, object]] | None = None,
    merge_records: Sequence[Mapping[str, object]] | None = None,
    merge_state_path: Path | None = None,
    current_row_id: str = "",
) -> dict[str, object]:
    """Assemble the typed report for the G37 guard.

    Parameters
    ----------
    child_patches:
        Iterable of typed child-patch submission rows. Each row should carry
        ``patch_id``, ``plan_id`` (or ``target_ref``), ``actor`` /
        ``actor_role``, and the write-scope fields listed in
        ``OVERLAP_SCOPE_FIELDS``.
    merge_records:
        Iterable of typed merge-conflict records produced by the parent role
        coordinator after observing the child patches. Each record should
        carry ``conflict_id``, ``child_patch_ids``,
        ``conflict_disposition``, ``merge_coordinator_id``, ``lease_refs``,
        and ``post_merge_proof``.
    merge_state_path:
        Override for the default merge-state projection path.
    current_row_id:
        When set, only evaluate child patches and merge records whose
        ``target_ref`` or ``plan_id`` matches the current PlanRow id.
    """
    warnings: list[str] = []
    checked_surfaces: list[str] = []
    source_path: Path | None = None
    if child_patches is None or merge_records is None:
        source_path = merge_state_path or _default_merge_state_path()
        checked_surfaces.append(str(source_path))
        loaded_patches, loaded_records = _load_merge_state(source_path, warnings)
        if child_patches is None:
            child_patches = loaded_patches
        if merge_records is None:
            merge_records = loaded_records
    else:
        child_patches = tuple(child_patches)
        merge_records = tuple(merge_records)

    scoped_patches = tuple(
        patch
        for patch in child_patches
        if _matches_row(patch, current_row_id)
    )
    scoped_records = tuple(
        record
        for record in merge_records
        if _matches_row(record, current_row_id)
    )

    overlaps = _detect_overlapping_patches(scoped_patches)
    violations: list[MergeConflictViolation] = []
    record_by_patches = _index_records_by_child_patches(scoped_records)

    # Rule 1: every overlapping pair must have a typed merge record with a
    # supported conflict_disposition.
    for overlap in overlaps:
        record = _find_matching_record(record_by_patches, overlap.patch_ids)
        if record is None or not _has_supported_disposition(record):
            violations.append(
                MergeConflictViolation(
                    rule_id=RULE_CONFLICTING_PATCHES_NO_DISPOSITION,
                    conflict_id=_conflict_id(record),
                    detail=(
                        "child patches "
                        f"{sorted(overlap.patch_ids)!r} overlap on "
                        f"{sorted(overlap.overlap_fields)!r} but no typed "
                        "conflict_disposition is recorded for the merge"
                    ),
                    remediation=(
                        "Emit a typed merge-conflict record with "
                        "conflict_disposition drawn from "
                        f"{sorted(SUPPORTED_DISPOSITIONS)!r} before the "
                        "merge can promote into the role-level proof chain."
                    ),
                    child_patch_ids=tuple(sorted(overlap.patch_ids)),
                    overlap_fields=tuple(sorted(overlap.overlap_fields)),
                )
            )

    # Rules 2/3/4: per-record completeness for the typed merge surface.
    # Records may legitimately exist without an upstream overlap row when the
    # coordinator pre-emptively splits scope, so we evaluate every record
    # that claims a disposition in scope.
    for record in scoped_records:
        if not _has_supported_disposition(record):
            # Already caught (or n/a) by Rule 1 when there is an overlap row;
            # otherwise the record itself is malformed and missing fields
            # below are derivative, so skip it for the per-record sweep.
            continue
        conflict_id = _conflict_id(record)
        child_patch_ids = tuple(_record_child_patch_ids(record))

        if not _coordinator_id(record):
            violations.append(
                MergeConflictViolation(
                    rule_id=RULE_MISSING_MERGE_COORDINATOR_ID,
                    conflict_id=conflict_id,
                    detail=(
                        f"merge record conflict_id={conflict_id!r} carries "
                        "a typed conflict_disposition but no "
                        "merge_coordinator_id for the parent role coordinator"
                    ),
                    remediation=(
                        "Set merge_coordinator_id to the live parent role "
                        "coordinator actor id that owned the merge decision."
                    ),
                    child_patch_ids=child_patch_ids,
                )
            )

        if not _lease_refs(record):
            violations.append(
                MergeConflictViolation(
                    rule_id=RULE_MISSING_LEASE_REFS,
                    conflict_id=conflict_id,
                    detail=(
                        f"merge record conflict_id={conflict_id!r} carries "
                        "a typed conflict_disposition but no lease_refs for "
                        "the write leases the conflicting children held"
                    ),
                    remediation=(
                        "Carry the typed write-lease references that the "
                        "conflicting child patches held so the lease audit "
                        "chain stays intact across the merge."
                    ),
                    child_patch_ids=child_patch_ids,
                )
            )

        if not _post_merge_proof(record):
            violations.append(
                MergeConflictViolation(
                    rule_id=RULE_MISSING_POST_MERGE_PROOF,
                    conflict_id=conflict_id,
                    detail=(
                        f"merge record conflict_id={conflict_id!r} carries "
                        "a typed conflict_disposition but no "
                        "post_merge_proof receipt"
                    ),
                    remediation=(
                        "Attach a post_merge_proof receipt id so the merge "
                        "outcome is provable after the fact."
                    ),
                    child_patch_ids=child_patch_ids,
                )
            )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "current_row_id": current_row_id,
        "checked_surfaces": checked_surfaces,
        "merge_state_path": str(source_path) if source_path is not None else "",
        "checked_patch_count": len(scoped_patches),
        "checked_record_count": len(scoped_records),
        "overlap_count": len(overlaps),
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


@dataclass(frozen=True, slots=True)
class _PatchOverlap:
    patch_ids: frozenset[str]
    overlap_fields: frozenset[str]


def _detect_overlapping_patches(
    patches: Sequence[Mapping[str, object]],
) -> tuple[_PatchOverlap, ...]:
    """Return overlapping child-patch pairs grouped by PlanRow."""
    by_row: dict[str, list[Mapping[str, object]]] = {}
    for patch in patches:
        row_id = _packet_row_id(patch)
        if not row_id:
            continue
        by_row.setdefault(row_id, []).append(patch)

    overlaps: list[_PatchOverlap] = []
    for row_patches in by_row.values():
        for i, patch_a in enumerate(row_patches):
            id_a = _patch_id(patch_a)
            if not id_a:
                continue
            for patch_b in row_patches[i + 1 :]:
                id_b = _patch_id(patch_b)
                if not id_b or id_b == id_a:
                    continue
                overlap_fields = _overlap_fields(patch_a, patch_b)
                if overlap_fields:
                    overlaps.append(
                        _PatchOverlap(
                            patch_ids=frozenset({id_a, id_b}),
                            overlap_fields=frozenset(overlap_fields),
                        )
                    )
    return tuple(overlaps)


def _overlap_fields(
    patch_a: Mapping[str, object],
    patch_b: Mapping[str, object],
) -> tuple[str, ...]:
    out: list[str] = []
    for field in OVERLAP_SCOPE_FIELDS:
        a_values = _string_set(patch_a.get(field))
        b_values = _string_set(patch_b.get(field))
        if a_values & b_values:
            out.append(field)
    return tuple(out)


def _string_set(value: object) -> frozenset[str]:
    if value is None:
        return frozenset()
    if isinstance(value, str):
        stripped = value.strip()
        return frozenset({stripped}) if stripped else frozenset()
    if isinstance(value, Mapping):
        return frozenset()
    if isinstance(value, Sequence):
        return frozenset(
            str(item).strip()
            for item in value
            if isinstance(item, (str, int))
            and str(item).strip()
        )
    return frozenset()


def _index_records_by_child_patches(
    records: Sequence[Mapping[str, object]],
) -> dict[frozenset[str], Mapping[str, object]]:
    indexed: dict[frozenset[str], Mapping[str, object]] = {}
    for record in records:
        key = frozenset(_record_child_patch_ids(record))
        if not key:
            continue
        indexed[key] = record
    return indexed


def _find_matching_record(
    indexed: dict[frozenset[str], Mapping[str, object]],
    patch_ids: frozenset[str],
) -> Mapping[str, object] | None:
    if patch_ids in indexed:
        return indexed[patch_ids]
    for key, record in indexed.items():
        if patch_ids.issubset(key):
            return record
    return None


def _has_supported_disposition(record: Mapping[str, object]) -> bool:
    disposition = str(record.get("conflict_disposition") or "").strip().lower()
    return disposition in SUPPORTED_DISPOSITIONS


def _conflict_id(record: Mapping[str, object] | None) -> str:
    if record is None:
        return ""
    return str(record.get("conflict_id") or "").strip()


def _coordinator_id(record: Mapping[str, object]) -> str:
    return str(record.get("merge_coordinator_id") or "").strip()


def _lease_refs(record: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(_string_set(record.get("lease_refs")))


def _post_merge_proof(record: Mapping[str, object]) -> str:
    return str(record.get("post_merge_proof") or "").strip()


def _record_child_patch_ids(record: Mapping[str, object]) -> tuple[str, ...]:
    raw = record.get("child_patch_ids")
    return tuple(sorted(_string_set(raw)))


def _patch_id(patch: Mapping[str, object]) -> str:
    return str(patch.get("patch_id") or "").strip()


def _load_merge_state(
    path: Path, warnings: list[str]
) -> tuple[tuple[Mapping[str, object], ...], tuple[Mapping[str, object], ...]]:
    if not path.exists():
        warnings.append(f"merge state missing: {path}")
        return ((), ())
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"merge state load failed: {exc}")
        return ((), ())
    if not isinstance(payload, Mapping):
        return ((), ())
    raw_patches = payload.get("child_patches")
    raw_records = payload.get("merge_records")
    patches = tuple(p for p in (raw_patches or []) if isinstance(p, Mapping))
    records = tuple(r for r in (raw_records or []) if isinstance(r, Mapping))
    return patches, records


def _default_merge_state_path() -> Path:
    return (
        REPO_ROOT
        / "dev/reports/review_channel/projections/latest/multi_actor_merge_state.json"
    )


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- current_row_id: `{report.get('current_row_id')}`")
    lines.append(f"- checked_patch_count: {report.get('checked_patch_count')}")
    lines.append(f"- checked_record_count: {report.get('checked_record_count')}")
    lines.append(f"- overlap_count: {report.get('overlap_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    if report.get("display_text"):
        lines.extend(("", str(report["display_text"])))
    violations = report.get("violations")
    if (
        isinstance(violations, Sequence)
        and not isinstance(violations, (str, bytes))
        and violations
    ):
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('rule_id')}: "
                f"conflict={violation.get('conflict_id')!r} -- "
                f"{violation.get('detail')}"
            )
    warnings = report.get("warnings")
    if (
        isinstance(warnings, Sequence)
        and not isinstance(warnings, (str, bytes))
        and warnings
    ):
        lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--merge-state-path",
        type=Path,
        default=_default_merge_state_path(),
        help="Path to multi_actor_merge_state.json projection",
    )
    parser.add_argument(
        "--row-id",
        default="",
        help=(
            "If set, only evaluate child patches and merge records whose "
            "target_ref or plan_id matches this row id."
        ),
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            merge_state_path=args.merge_state_path,
            current_row_id=args.row_id,
        )
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
