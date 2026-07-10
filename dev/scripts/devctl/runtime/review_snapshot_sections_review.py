"""Reviewer-hints, reasoning, and known-gap builders for ReviewSnapshot."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .review_snapshot_git import RawCommit
from .review_snapshot_hints import build_suggested_commands
from .review_snapshot_models_core import SnapshotDelta
from .review_snapshot_models_quality import SnapshotQualitySignals
from .review_snapshot_models_sections import (
    KnownGapRow,
    ReviewerHintRow,
    SnapshotKnownGaps,
    SnapshotReasoning,
    SnapshotReviewerHints,
    WhyRecord,
)
from .review_snapshot_utils import as_list, as_mapping
from .review_snapshot_why import (
    active_mp_summaries_from_master_plan,
    build_why_record,
    load_evolution_entries,
    load_plan_index,
)


def build_reviewer_hints(*, delta: SnapshotDelta) -> SnapshotReviewerHints:
    """Return the curated reviewer-hints section derived from the delta."""
    hints: list[ReviewerHintRow] = []
    for label in delta.risk_addons_triggered:
        hints.append(
            ReviewerHintRow(
                kind="risk",
                label=label,
                detail="Delta touches a risk-sensitive surface; verify the routed bundle",
                reference="",
            )
        )
    for path in delta.authority_surfaces_touched:
        hints.append(
            ReviewerHintRow(
                kind="authority_surface",
                label="Typed authority surface touched",
                detail="Review contract-level invariants for this file",
                reference=path,
            )
        )
    seen_contracts: set[str] = set()
    for commit in delta.commits:
        for path in commit.contracts_mutated:
            if path in seen_contracts:
                continue
            seen_contracts.add(path)
            hints.append(
                ReviewerHintRow(
                    kind="contract_mutation",
                    label="Contract / typed model mutated",
                    detail=f"Commit {commit.sha_short} changed {path}",
                    reference=path,
                )
            )
    commands = build_suggested_commands(
        bundle_classes_touched=delta.bundle_classes_touched,
        risk_addons_triggered=delta.risk_addons_triggered,
        authority_surfaces_touched=delta.authority_surfaces_touched,
    )
    return SnapshotReviewerHints(
        hints=tuple(hints),
        suggested_commands=commands,
    )


def build_reasoning(
    *,
    repo_root: Path,
    raw_commits: tuple[RawCommit, ...],
) -> SnapshotReasoning:
    """Stitch commit → MP → plan doc → evolution entry for each commit."""
    plan_index = load_plan_index(repo_root)
    evolution_entries = load_evolution_entries(repo_root)
    why_records: list[WhyRecord] = []
    for raw in raw_commits:
        why_records.append(
            build_why_record(
                raw,
                repo_root=repo_root,
                plan_index=plan_index,
                evolution_entries=evolution_entries,
            )
        )
    mp_summaries = active_mp_summaries_from_master_plan(repo_root)
    return SnapshotReasoning(
        commit_why_records=tuple(why_records),
        active_mp_summaries=mp_summaries,
    )


def build_known_gaps(
    *,
    startup: Mapping[str, object],
    governance_summary: Mapping[str, object],
    quality: SnapshotQualitySignals,
) -> SnapshotKnownGaps:
    """Return the honesty block: open findings, advisories, stale warnings."""
    startup_advisory: list[str] = []
    advisory_action = str(startup.get("advisory_action") or "")
    advisory_reason = str(startup.get("advisory_reason") or "")
    if advisory_action and advisory_action != "continue_editing":
        startup_advisory.append(f"{advisory_action}: {advisory_reason}".strip(": "))
    stale: list[str] = []
    for trace in as_list(startup.get("rejected_rule_traces"))[:6]:
        mapping = as_mapping(trace)
        summary = str(mapping.get("summary") or "")
        if summary:
            stale.append(summary)
    gaps: list[KnownGapRow] = []
    for finding in quality.governance_recent_findings[:8]:
        if finding.verdict and finding.verdict != "fixed":
            gaps.append(
                KnownGapRow(
                    kind="governance_open",
                    summary=f"{finding.check_id}: {finding.notes or finding.symbol}",
                    reference=finding.file_path,
                )
            )
    return SnapshotKnownGaps(
        open_governance_findings=quality.governance_open_findings,
        open_mp_blockers=(),
        startup_action_advisories=tuple(startup_advisory),
        stale_warnings=tuple(stale),
        gaps=tuple(gaps),
    )


__all__ = ["build_known_gaps", "build_reasoning", "build_reviewer_hints"]
