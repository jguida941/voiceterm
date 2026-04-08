"""JSON-serialisation helpers for ReviewSnapshot dataclasses.

Split out of ``review_snapshot_models.py`` so the typed-record module stays
under the code-shape soft limit. Each helper here flattens one snapshot
section into a dict whose values are JSON-safe (str, int, bool, list, dict),
so ``json.dumps`` succeeds without custom encoders.
"""

from __future__ import annotations

from dataclasses import asdict

from .review_snapshot_models import (
    CommitRow,
    FileStatRow,
    SnapshotArchitecture,
    SnapshotDelta,
    SnapshotGovernanceState,
    SnapshotKnownGaps,
    SnapshotQualitySignals,
    SnapshotReasoning,
    SnapshotReviewerHints,
    WhyRecord,
)


def governance_state_to_dict(state: SnapshotGovernanceState) -> dict[str, object]:
    payload = asdict(state)
    payload["active_mp_scope"] = list(state.active_mp_scope)
    return payload


def delta_to_dict(delta: SnapshotDelta) -> dict[str, object]:
    return {
        "from_sha": delta.from_sha,
        "to_sha": delta.to_sha,
        "commit_count": delta.commit_count,
        "files_changed_count": delta.files_changed_count,
        "total_insertions": delta.total_insertions,
        "total_deletions": delta.total_deletions,
        "commits": [commit_to_dict(c) for c in delta.commits],
        "files": [file_stat_to_dict(f) for f in delta.files],
        "bundle_classes_touched": list(delta.bundle_classes_touched),
        "risk_addons_triggered": list(delta.risk_addons_triggered),
        "authority_surfaces_touched": list(delta.authority_surfaces_touched),
    }


def commit_to_dict(commit: CommitRow) -> dict[str, object]:
    payload = asdict(commit)
    payload["mp_refs"] = list(commit.mp_refs)
    payload["checkpoint_markers"] = list(commit.checkpoint_markers)
    payload["risk_addons"] = list(commit.risk_addons)
    payload["authority_surfaces_touched"] = list(commit.authority_surfaces_touched)
    payload["contracts_mutated"] = list(commit.contracts_mutated)
    return payload


def file_stat_to_dict(file_stat: FileStatRow) -> dict[str, object]:
    return asdict(file_stat)


def quality_to_dict(quality: SnapshotQualitySignals) -> dict[str, object]:
    return {
        "ci_bundle_ok": quality.ci_bundle_ok,
        "ci_bundle_summary": quality.ci_bundle_summary,
        "ci_total_checks": quality.ci_total_checks,
        "ci_passed_checks": quality.ci_passed_checks,
        "ci_failed_checks": quality.ci_failed_checks,
        "ci_blocking_failures": [asdict(row) for row in quality.ci_blocking_failures],
        "probe_run_state": quality.probe_run_state,
        "probe_run_mode": quality.probe_run_mode,
        "probe_generated_at": quality.probe_generated_at,
        "probe_warning_count": quality.probe_warning_count,
        "probe_error_count": quality.probe_error_count,
        "probe_summary_json_path": quality.probe_summary_json_path,
        "probe_summary_md_path": quality.probe_summary_md_path,
        "probe_files_scanned": quality.probe_files_scanned,
        "probe_hints_total": quality.probe_hints_total,
        "probe_hints_by_severity": dict(quality.probe_hints_by_severity),
        "probe_top_findings": [asdict(row) for row in quality.probe_top_findings],
        "governance_total_findings": quality.governance_total_findings,
        "governance_open_findings": quality.governance_open_findings,
        "governance_fixed_count": quality.governance_fixed_count,
        "governance_false_positive_count": quality.governance_false_positive_count,
        "governance_recent_findings": [
            asdict(row) for row in quality.governance_recent_findings
        ],
        "quality_policy_guard_count": quality.quality_policy_guard_count,
        "quality_policy_probe_count": quality.quality_policy_probe_count,
    }


def architecture_to_dict(arch: SnapshotArchitecture) -> dict[str, object]:
    return {
        "contract_ownership_map": [
            {
                "contract_id": row.contract_id,
                "owner_layer": row.owner_layer,
                "runtime_model": row.runtime_model,
                "startup_surface_tokens": list(row.startup_surface_tokens),
            }
            for row in arch.contract_ownership_map
        ],
        "hotspots": [
            {
                "path": row.path,
                "risk_level": row.risk_level,
                "reasons": list(row.reasons),
            }
            for row in arch.hotspots
        ],
        "active_plans": list(arch.active_plans),
        "graph_node_count": arch.graph_node_count,
        "graph_edge_count": arch.graph_edge_count,
        "graph_source_mode": arch.graph_source_mode,
        "key_doc_paths": list(arch.key_doc_paths),
    }


def reviewer_hints_to_dict(hints: SnapshotReviewerHints) -> dict[str, object]:
    return {
        "hints": [asdict(h) for h in hints.hints],
        "suggested_commands": list(hints.suggested_commands),
    }


def reasoning_to_dict(reasoning: SnapshotReasoning) -> dict[str, object]:
    return {
        "commit_why_records": [
            why_record_to_dict(r) for r in reasoning.commit_why_records
        ],
        "active_mp_summaries": list(reasoning.active_mp_summaries),
    }


def why_record_to_dict(record: WhyRecord) -> dict[str, object]:
    payload = asdict(record)
    payload["mp_refs"] = list(record.mp_refs)
    payload["checkpoint_markers"] = list(record.checkpoint_markers)
    payload["linked_plan_docs"] = list(record.linked_plan_docs)
    return payload


def known_gaps_to_dict(gaps: SnapshotKnownGaps) -> dict[str, object]:
    return {
        "open_governance_findings": gaps.open_governance_findings,
        "open_mp_blockers": list(gaps.open_mp_blockers),
        "startup_action_advisories": list(gaps.startup_action_advisories),
        "stale_warnings": list(gaps.stale_warnings),
        "gaps": [asdict(g) for g in gaps.gaps],
    }


__all__ = [
    "architecture_to_dict",
    "commit_to_dict",
    "delta_to_dict",
    "file_stat_to_dict",
    "governance_state_to_dict",
    "known_gaps_to_dict",
    "quality_to_dict",
    "reasoning_to_dict",
    "reviewer_hints_to_dict",
    "why_record_to_dict",
]
