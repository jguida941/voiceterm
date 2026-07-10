"""Reduction helpers for scheduler-facing PlanningIRSnapshot outputs."""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ..runtime.finding_contracts import FindingRecord
from ..runtime.project_governance import PlanRegistryEntry
from ..runtime.review_state_models import ReviewState
from ..runtime.work_intake_models import (
    PlanTargetRef,
    WorkIntakeCoordinationState,
    WorkIntakeOwnershipState,
)
from ..triage.findings_priority_models import RankedFinding
from .planning_ir_priority import (
    best_ranked_finding_for_paths,
    priority_bonus,
)
from .planning_ir_summary import SliceSummaryContext, slice_summary
from .planning_ir_models import (
    ConcurrentWriterConflictRecord,
    NextBestSliceRecord,
    PlanFindingMismatchRecord,
    UnownedHotPathRecord,
)

_MAX_NEXT_BEST_SLICES = 4
_MAX_SLICE_FILES = 3
_MAX_UNOWNED_HOT_PATHS = 6
_MAX_PLAN_FINDING_MISMATCHES = 8


@dataclass(frozen=True, slots=True)
class PlanningReductionContext:
    """Shared reduction inputs used by the scheduler-facing output builders."""

    plan_lookup: Mapping[str, PlanRegistryEntry]
    active_target: PlanTargetRef | None
    live_findings: Sequence[FindingRecord]
    hot_paths: Mapping[str, float]
    plan_to_file_paths: Mapping[str, tuple[str, ...]]
    file_to_plan_paths: Mapping[str, tuple[str, ...]]
    review_state: ReviewState | None
    conflicts: Sequence[ConcurrentWriterConflictRecord]
    coordination: WorkIntakeCoordinationState
    ranked_findings: Sequence[RankedFinding] = ()


def build_conflicts(
    *,
    ownership: WorkIntakeOwnershipState,
    coordination: WorkIntakeCoordinationState,
) -> tuple[ConcurrentWriterConflictRecord, ...]:
    """Project current concurrent-writer and duplicate-worktree signals."""
    conflicts: list[ConcurrentWriterConflictRecord] = []
    if ownership.status == "concurrent_writer_activity":
        conflicts.append(
            ConcurrentWriterConflictRecord(
                conflict_kind="ownership_conflict",
                summary=ownership.summary or "dirty paths overlap live peer activity",
                active_participants=coordination.active_participants
                or ownership.live_agents,
                conflicting_paths=ownership.outside_scope_dirty_paths
                or ownership.dirty_paths,
                recommended_topology="single_agent",
                blocking=True,
            )
        )
    if coordination.duplicate_delegated_worktrees:
        conflicts.append(
            ConcurrentWriterConflictRecord(
                conflict_kind="duplicate_worktree",
                summary="delegated workers share the same worktree",
                active_participants=coordination.active_participants,
                duplicate_worktrees=coordination.duplicate_delegated_worktrees,
                recommended_topology="single_agent",
                blocking=True,
            )
        )
    if (
        coordination.concurrent_writer_conflict_detected
        and not conflicts
        and coordination.active_participants
    ):
        conflicts.append(
            ConcurrentWriterConflictRecord(
                conflict_kind="topology_conflict",
                summary="runtime coordination already reports a concurrent-writer conflict",
                active_participants=coordination.active_participants,
                recommended_topology="single_agent",
                blocking=True,
            )
        )
    return tuple(conflicts)


def build_unowned_hot_paths(
    context: PlanningReductionContext,
) -> tuple[UnownedHotPathRecord, ...]:
    """Return the bounded set of hot source files with no plan owner."""
    finding_count_by_file = Counter(finding.file_path for finding in context.live_findings)
    records: list[UnownedHotPathRecord] = []
    for file_path, temperature in sorted(
        context.hot_paths.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        if context.file_to_plan_paths.get(file_path):
            continue
        finding_count = finding_count_by_file.get(file_path, 0)
        summary = "hot path has no scoped_by plan owner"
        if finding_count:
            summary += f"; {finding_count} live finding(s) are already attached"
        records.append(
            UnownedHotPathRecord(
                file_path=file_path,
                temperature=temperature,
                live_finding_count=finding_count,
                summary=summary,
            )
        )
        if len(records) >= _MAX_UNOWNED_HOT_PATHS:
            break
    return tuple(records)


def build_plan_finding_mismatches(
    context: PlanningReductionContext,
) -> tuple[PlanFindingMismatchRecord, ...]:
    """Return live findings whose ownership does not line up with plan state."""
    active_target_path = context.active_target.plan_path if context.active_target else ""
    records: list[PlanFindingMismatchRecord] = []
    for finding in context.live_findings:
        owner_plan_paths = context.file_to_plan_paths.get(finding.file_path, ())
        mismatch_kind = _mismatch_kind(
            owner_plan_paths=owner_plan_paths,
            active_target_path=active_target_path,
        )
        if not mismatch_kind:
            continue
        records.append(
            PlanFindingMismatchRecord(
                finding_id=finding.finding_id,
                check_id=finding.check_id,
                file_path=finding.file_path,
                severity=finding.severity,
                mismatch_kind=mismatch_kind,
                owner_plan_paths=owner_plan_paths,
                active_target_path=active_target_path,
                summary=_mismatch_summary(mismatch_kind),
            )
        )
        if len(records) >= _MAX_PLAN_FINDING_MISMATCHES:
            break
    return tuple(records)


def build_next_best_slices(
    context: PlanningReductionContext,
) -> tuple[NextBestSliceRecord, ...]:
    """Rank a few bounded next-slice suggestions from current plan/runtime state."""
    if not context.plan_lookup:
        return ()

    active_target_path = context.active_target.plan_path if context.active_target else ""
    review_candidate_paths = _review_candidate_paths(context.review_state)
    finding_count_by_file = Counter(finding.file_path for finding in context.live_findings)
    summary_context = SliceSummaryContext(
        active_target_path=active_target_path,
        review_candidate_paths=frozenset(review_candidate_paths),
        finding_count_by_file=finding_count_by_file,
        blocked=bool(context.conflicts),
        hot_paths=context.hot_paths,
    )
    candidate_rows: list[NextBestSliceRecord] = []
    for plan_path, entry in context.plan_lookup.items():
        scored_paths = _score_owned_paths(
            plan_path=plan_path,
            plan_to_file_paths=context.plan_to_file_paths,
            active_target_path=active_target_path,
            review_candidate_paths=review_candidate_paths,
            finding_count_by_file=finding_count_by_file,
            hot_paths=context.hot_paths,
        )
        if not scored_paths:
            continue
        top_files = tuple(
            file_path
            for _score, file_path in scored_paths[:_MAX_SLICE_FILES]
            if "/" in file_path or file_path.endswith(".md")
        )
        best_ranked_finding = best_ranked_finding_for_paths(
            tuple(file_path for _score, file_path in scored_paths),
            context.ranked_findings,
        )
        candidate_rows.append(
            NextBestSliceRecord(
                slice_id=_slice_id(plan_path=plan_path, file_paths=top_files),
                plan_path=plan_path,
                plan_title=entry.title,
                plan_scope=entry.scope,
                file_paths=top_files,
                target_id=context.active_target.target_id
                if active_target_path == plan_path and context.active_target is not None
                else "",
                hot_path_count=sum(
                    1 for _score, file_path in scored_paths if file_path in context.hot_paths
                ),
                live_finding_count=sum(
                    finding_count_by_file.get(file_path, 0)
                    for _score, file_path in scored_paths
                ),
                prioritized_finding_rank=(
                    best_ranked_finding.rank if best_ranked_finding is not None else 0
                ),
                finding_severity_band=(
                    best_ranked_finding.severity
                    if best_ranked_finding is not None
                    else ""
                ),
                total_score=round(
                    sum(score for score, _ in scored_paths)
                    + priority_bonus(best_ranked_finding),
                    2,
                ),
                schedule_state="blocked_by_conflict" if summary_context.blocked else "ready",
                recommended_topology=_recommended_topology(context),
                summary=slice_summary(
                    context=summary_context,
                    plan_path=plan_path,
                    top_files=top_files,
                    scored_paths=scored_paths,
                    best_ranked_finding=best_ranked_finding,
                ),
            )
        )
    candidate_rows.sort(
        key=lambda item: (
            item.prioritized_finding_rank or 10_000,
            -item.total_score,
            item.plan_path,
        )
    )
    return tuple(candidate_rows[:_MAX_NEXT_BEST_SLICES])


def _mismatch_kind(
    *,
    owner_plan_paths: tuple[str, ...],
    active_target_path: str,
) -> str:
    if not owner_plan_paths:
        return "unowned_finding"
    if len(owner_plan_paths) > 1:
        return "multi_plan_finding"
    if active_target_path and active_target_path not in owner_plan_paths:
        return "active_target_not_owner"
    return ""


def _mismatch_summary(mismatch_kind: str) -> str:
    return {
        "unowned_finding": "live finding has no scoped_by plan owner",
        "multi_plan_finding": "live finding maps to multiple scoped plans",
        "active_target_not_owner": "live finding sits outside the current active target",
    }.get(mismatch_kind, "")


def _score_owned_paths(
    *,
    plan_path: str,
    plan_to_file_paths: Mapping[str, tuple[str, ...]],
    active_target_path: str,
    review_candidate_paths: set[str],
    finding_count_by_file: Counter[str],
    hot_paths: Mapping[str, float],
) -> list[tuple[float, str]]:
    owned_paths = set(plan_to_file_paths.get(plan_path, ()))
    if active_target_path == plan_path:
        owned_paths.update(review_candidate_paths)
    scored_paths: list[tuple[float, str]] = []
    for file_path in owned_paths:
        path_score = 0.0
        if finding_count_by_file.get(file_path, 0):
            path_score += finding_count_by_file[file_path] * 10.0
        if file_path in hot_paths:
            path_score += hot_paths[file_path] * 10.0
        if file_path in review_candidate_paths:
            path_score += 2.0
        if path_score > 0:
            scored_paths.append((path_score, file_path))
    scored_paths.sort(key=lambda item: (-item[0], item[1]))
    return scored_paths


def _recommended_topology(context: PlanningReductionContext) -> str:
    if context.conflicts:
        return "single_agent"
    return context.coordination.collaboration_topology or "single_agent"


def _review_candidate_paths(review_state: ReviewState | None) -> set[str]:
    if review_state is None or review_state.review_candidate is None:
        return set()
    candidate = review_state.review_candidate
    if candidate.scope_paths:
        return set(candidate.scope_paths)
    return set(candidate.changed_paths)


def _slice_id(*, plan_path: str, file_paths: Sequence[str]) -> str:
    seed = "|".join((plan_path, *file_paths))
    return f"slice:{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"


__all__ = [
    "PlanningReductionContext",
    "build_conflicts",
    "build_next_best_slices",
    "build_plan_finding_mismatches",
    "build_unowned_hot_paths",
]
