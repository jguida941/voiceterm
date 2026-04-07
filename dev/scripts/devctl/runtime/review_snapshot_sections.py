"""Section builders for ReviewSnapshot (non-delta sections).

Delta section lives in ``review_snapshot_delta`` so each builder module
stays under the code-shape soft limit. This file owns quality, architecture,
reviewer-hints, reasoning, and known-gaps.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .review_snapshot_delta import build_delta
from .review_snapshot_git import RawCommit
from .review_snapshot_hints import build_suggested_commands
from .review_snapshot_models import (
    ContractOwnershipRow,
    GovernanceFindingRow,
    HotspotRow,
    KnownGapRow,
    ProbeFindingRow,
    ReviewerHintRow,
    SnapshotArchitecture,
    SnapshotDelta,
    SnapshotKnownGaps,
    SnapshotQualitySignals,
    SnapshotReasoning,
    SnapshotReviewerHints,
    WhyRecord,
)
from .review_snapshot_why import (
    active_mp_summaries_from_master_plan,
    build_why_record,
    load_evolution_entries,
    load_plan_index,
)


def build_quality(
    *,
    governance_summary: Mapping[str, object],
    probe_summary: Mapping[str, object],
) -> SnapshotQualitySignals:
    """Return quality signals aggregated from governance + probe reports."""
    gov_stats = _as_mapping(governance_summary.get("stats"))
    probe_block = _as_mapping(probe_summary.get("summary"))
    hints_by_severity_raw = _as_mapping(probe_block.get("hints_by_severity"))
    return SnapshotQualitySignals(
        ci_bundle_ok=bool(governance_summary.get("ok", True)),
        ci_bundle_summary="",
        ci_total_checks=0,
        ci_passed_checks=0,
        ci_failed_checks=0,
        ci_blocking_failures=(),
        probe_files_scanned=_coerce_int(probe_block.get("files_scanned")),
        probe_hints_total=_coerce_int(probe_block.get("risk_hints")),
        probe_hints_by_severity={
            str(k): _coerce_int(v) for k, v in hints_by_severity_raw.items()
        },
        probe_top_findings=_build_probe_findings(probe_summary),
        governance_total_findings=_coerce_int(gov_stats.get("total_findings")),
        governance_open_findings=_coerce_int(gov_stats.get("open_finding_count")),
        governance_fixed_count=_coerce_int(gov_stats.get("fixed_count")),
        governance_false_positive_count=_coerce_int(
            gov_stats.get("false_positive_count")
        ),
        governance_recent_findings=_build_governance_findings(governance_summary),
        quality_policy_guard_count=0,
        quality_policy_probe_count=0,
    )


def _build_probe_findings(
    probe_summary: Mapping[str, object],
) -> tuple[ProbeFindingRow, ...]:
    rows: list[ProbeFindingRow] = []
    for hint in _as_list(probe_summary.get("enriched_hints"))[:10]:
        row = _as_mapping(hint)
        rows.append(
            ProbeFindingRow(
                probe=str(row.get("probe") or ""),
                review_lens=str(row.get("review_lens") or ""),
                severity=str(row.get("severity") or ""),
                file=str(row.get("file") or row.get("file_path") or ""),
                line=_coerce_int(row.get("line")),
                rule_id=str(row.get("rule_id") or ""),
                summary=str(row.get("summary") or row.get("message") or ""),
            )
        )
    return tuple(rows)


def _build_governance_findings(
    governance_summary: Mapping[str, object],
) -> tuple[GovernanceFindingRow, ...]:
    rows: list[GovernanceFindingRow] = []
    for row in _as_list(governance_summary.get("recent_findings"))[:15]:
        mapping = _as_mapping(row)
        rows.append(
            GovernanceFindingRow(
                finding_id=str(mapping.get("finding_id") or ""),
                check_id=str(mapping.get("check_id") or ""),
                file_path=str(mapping.get("file_path") or ""),
                symbol=str(mapping.get("symbol") or ""),
                severity=str(mapping.get("severity") or ""),
                signal_type=str(mapping.get("signal_type") or ""),
                verdict=str(mapping.get("verdict") or ""),
                timestamp_utc=str(mapping.get("timestamp_utc") or ""),
                notes=str(mapping.get("notes") or ""),
            )
        )
    return tuple(rows)


def build_architecture(
    *,
    startup: Mapping[str, object],
    graph_bootstrap: Mapping[str, object],
    governance_contract: object | None = None,
) -> SnapshotArchitecture:
    """Return the architecture section from startup + graph bootstrap payloads."""
    ownership_rows = _build_ownership_rows(startup)
    hotspots = _build_hotspots(graph_bootstrap)
    active_plans = _build_active_plans(graph_bootstrap)
    snapshot_block = _as_mapping(graph_bootstrap.get("snapshot"))
    return SnapshotArchitecture(
        contract_ownership_map=ownership_rows,
        hotspots=hotspots,
        active_plans=active_plans,
        graph_node_count=_coerce_int(snapshot_block.get("node_count")),
        graph_edge_count=_coerce_int(snapshot_block.get("edge_count")),
        graph_source_mode=str(snapshot_block.get("source_mode") or ""),
        key_doc_paths=_resolve_key_doc_paths(governance_contract),
    )


def _build_ownership_rows(
    startup: Mapping[str, object],
) -> tuple[ContractOwnershipRow, ...]:
    ownership_raw = _as_mapping(startup.get("contract_ownership_map"))
    rows: list[ContractOwnershipRow] = []
    for contract_id, payload in ownership_raw.items():
        mapping = _as_mapping(payload)
        rows.append(
            ContractOwnershipRow(
                contract_id=str(contract_id),
                owner_layer=str(mapping.get("owner_layer") or ""),
                runtime_model=str(mapping.get("runtime_model") or ""),
                startup_surface_tokens=_coerce_str_tuple(
                    mapping.get("startup_surface_tokens")
                ),
            )
        )
    return tuple(rows)


def _build_hotspots(
    graph_bootstrap: Mapping[str, object],
) -> tuple[HotspotRow, ...]:
    rows: list[HotspotRow] = []
    for row in _as_list(graph_bootstrap.get("hotspots"))[:12]:
        mapping = _as_mapping(row)
        rows.append(
            HotspotRow(
                path=str(mapping.get("path") or ""),
                risk_level=str(mapping.get("risk_level") or ""),
                reasons=_coerce_str_tuple(mapping.get("reasons")),
            )
        )
    return tuple(rows)


def _build_active_plans(graph_bootstrap: Mapping[str, object]) -> tuple[str, ...]:
    plans: list[str] = []
    for entry in _as_list(graph_bootstrap.get("active_plans"))[:12]:
        mapping = _as_mapping(entry)
        title = str(mapping.get("title") or mapping.get("id") or "")
        if title:
            plans.append(title)
    return tuple(plans)


def _resolve_key_doc_paths(governance: object | None) -> tuple[str, ...]:
    """Resolve reviewer key-doc pointers via ProjectGovernance typed fields."""
    if governance is None:
        return ()
    doc_policy = getattr(governance, "doc_policy", None)
    path_roots = getattr(governance, "path_roots", None)
    paths: list[str] = []
    if doc_policy is not None:
        for attr in ("docs_authority_path", "tracker_path", "index_path"):
            value = str(getattr(doc_policy, attr, "") or "").strip()
            if value and value not in paths:
                paths.append(value)
    if path_roots is not None:
        guides_root = str(getattr(path_roots, "guides", "") or "").strip()
        if guides_root:
            candidate = f"{guides_root.rstrip('/')}/AI_GOVERNANCE_PLATFORM.md"
            if candidate not in paths:
                paths.append(candidate)
    return tuple(paths)


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
    for trace in _as_list(startup.get("rejected_rule_traces"))[:6]:
        mapping = _as_mapping(trace)
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


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _coerce_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _coerce_str_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if item)
    return ()


__all__ = [
    "build_architecture",
    "build_delta",
    "build_known_gaps",
    "build_quality",
    "build_reasoning",
    "build_reviewer_hints",
]
