"""Typed dataclasses for the ReviewSnapshot projection surface.

Deterministic projection of repo state for external reviewers, written at
the path resolved from ``ProjectGovernance.artifact_roots.review_snapshot_path``
(default ``dev/audits/REVIEW_SNAPSHOT.md``). Every field is sourced from an
existing typed builder. JSON serialisation helpers live in
``review_snapshot_serialize``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

REVIEW_SNAPSHOT_CONTRACT_ID = "ReviewSnapshot"
REVIEW_SNAPSHOT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class SnapshotIdentity:
    """Repo identity and HEAD metadata that names the snapshot."""

    generation_stamp: str = ""
    generated_at_utc: str = ""
    repo_name: str = ""
    repo_description: str = ""
    product_thesis: str = ""
    remote_url: str = ""
    branch: str = ""
    default_branch: str = ""
    head_sha: str = ""
    head_sha_short: str = ""
    head_subject: str = ""
    head_author: str = ""
    head_timestamp_utc: str = ""
    tree_hash: str = ""
    previous_snapshot_head_sha: str = ""
    commits_since_previous: int = 0


@dataclass(frozen=True, slots=True)
class SnapshotGovernanceState:
    """Typed governance projection: push decision, reviewer runtime, pipeline."""

    push_action: str = ""
    push_reason: str = ""
    push_eligible_now: bool = False
    next_step_command: str = ""
    publication_backlog_state: str = ""
    publication_guidance: str = ""
    interaction_mode: str = "unresolved"
    reviewer_mode: str = ""
    reviewer_freshness: str = "unknown"
    reviewer_publish_clear: bool = False
    reviewer_implementation_blocked: bool = False
    reviewer_block_reason: str = ""
    pipeline_state: str = ""
    pipeline_blocked_reason: str = ""
    pipeline_approval_state: str = ""
    advisory_action: str = ""
    advisory_reason: str = ""
    active_mp_scope: tuple[str, ...] = ()
    active_plan_title: str = ""
    active_plan_path: str = ""
    worktree_clean: bool = False
    checkpoint_required: bool = False


@dataclass(frozen=True, slots=True)
class CommitRow:
    """One commit in the delta range, with derived classification hints."""

    sha: str = ""
    sha_short: str = ""
    subject: str = ""
    author: str = ""
    timestamp_utc: str = ""
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    bundle_class: str = "unknown"
    mp_refs: tuple[str, ...] = ()
    checkpoint_markers: tuple[str, ...] = ()
    risk_addons: tuple[str, ...] = ()
    authority_surfaces_touched: tuple[str, ...] = ()
    contracts_mutated: tuple[str, ...] = ()
    remote_url: str = ""
    body_excerpt: str = ""


@dataclass(frozen=True, slots=True)
class FileStatRow:
    """One file change with typed insertion/deletion counts and bundle class."""

    path: str = ""
    insertions: int = 0
    deletions: int = 0
    change_kind: str = "modified"
    bundle_class: str = "unknown"


@dataclass(frozen=True, slots=True)
class SnapshotDelta:
    """Aggregated 'what changed' block pointing the reviewer at new work."""

    from_sha: str = ""
    to_sha: str = ""
    commit_count: int = 0
    files_changed_count: int = 0
    total_insertions: int = 0
    total_deletions: int = 0
    commits: tuple[CommitRow, ...] = ()
    files: tuple[FileStatRow, ...] = ()
    bundle_classes_touched: tuple[str, ...] = ()
    risk_addons_triggered: tuple[str, ...] = ()
    authority_surfaces_touched: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GuardResultRow:
    """One guard's typed pass/fail row."""

    name: str = ""
    ok: bool = True
    exit_code: int = 0
    summary: str = ""
    violations_count: int = 0


@dataclass(frozen=True, slots=True)
class ProbeFindingRow:
    """One probe finding projected into a reviewer-readable row."""

    probe: str = ""
    review_lens: str = ""
    severity: str = ""
    file: str = ""
    line: int = 0
    rule_id: str = ""
    summary: str = ""


@dataclass(frozen=True, slots=True)
class GovernanceFindingRow:
    """One governance-review record rendered for the external audit surface."""

    finding_id: str = ""
    check_id: str = ""
    file_path: str = ""
    symbol: str = ""
    severity: str = ""
    signal_type: str = ""
    verdict: str = ""
    timestamp_utc: str = ""
    notes: str = ""


@dataclass(frozen=True, slots=True)
class SnapshotQualitySignals:
    """Aggregated quality projection: guards, probes, governance findings."""

    ci_bundle_ok: bool = True
    ci_bundle_summary: str = ""
    ci_total_checks: int = 0
    ci_passed_checks: int = 0
    ci_failed_checks: int = 0
    ci_blocking_failures: tuple[GuardResultRow, ...] = ()
    probe_files_scanned: int = 0
    probe_hints_total: int = 0
    probe_hints_by_severity: dict[str, int] = field(default_factory=dict)
    probe_top_findings: tuple[ProbeFindingRow, ...] = ()
    governance_total_findings: int = 0
    governance_open_findings: int = 0
    governance_fixed_count: int = 0
    governance_false_positive_count: int = 0
    governance_recent_findings: tuple[GovernanceFindingRow, ...] = ()
    quality_policy_guard_count: int = 0
    quality_policy_probe_count: int = 0


@dataclass(frozen=True, slots=True)
class ContractOwnershipRow:
    """One contract row from StartupContext.contract_ownership_map."""

    contract_id: str = ""
    owner_layer: str = ""
    runtime_model: str = ""
    startup_surface_tokens: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class HotspotRow:
    """One hotspot from the context-graph bootstrap payload."""

    path: str = ""
    risk_level: str = ""
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SnapshotArchitecture:
    """Slim architecture surface: contracts, hotspots, graph metrics, plans."""

    contract_ownership_map: tuple[ContractOwnershipRow, ...] = ()
    hotspots: tuple[HotspotRow, ...] = ()
    active_plans: tuple[str, ...] = ()
    graph_node_count: int = 0
    graph_edge_count: int = 0
    graph_source_mode: str = ""
    key_doc_paths: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReviewerHintRow:
    """One curated hint derived from the delta + risk classification."""

    kind: str = ""
    label: str = ""
    detail: str = ""
    reference: str = ""


@dataclass(frozen=True, slots=True)
class SnapshotReviewerHints:
    """Typed reviewer-action surface: what to verify and how to verify it."""

    hints: tuple[ReviewerHintRow, ...] = ()
    suggested_commands: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WhyRecord:
    """Structured 'why' for one commit: MP refs, plan links, evolution notes."""

    commit_sha: str = ""
    commit_sha_short: str = ""
    subject: str = ""
    mp_refs: tuple[str, ...] = ()
    checkpoint_markers: tuple[str, ...] = ()
    body_excerpt: str = ""
    linked_plan_docs: tuple[str, ...] = ()
    evolution_rationale: str = ""
    summary: str = ""


@dataclass(frozen=True, slots=True)
class SnapshotReasoning:
    """Why the delta landed, stitched across commits, plans, and evolution."""

    commit_why_records: tuple[WhyRecord, ...] = ()
    active_mp_summaries: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class KnownGapRow:
    """One known unresolved gap, blocker, or advisory warning."""

    kind: str = ""
    summary: str = ""
    reference: str = ""


@dataclass(frozen=True, slots=True)
class SnapshotKnownGaps:
    """Open findings, MP blockers, startup advisories, and stale warnings."""

    open_governance_findings: int = 0
    open_mp_blockers: tuple[str, ...] = ()
    startup_action_advisories: tuple[str, ...] = ()
    stale_warnings: tuple[str, ...] = ()
    gaps: tuple[KnownGapRow, ...] = ()


@dataclass(frozen=True, slots=True)
class ReviewSnapshot:
    """Canonical typed projection of repo state for the external review surface."""

    schema_version: int = REVIEW_SNAPSHOT_SCHEMA_VERSION
    contract_id: str = REVIEW_SNAPSHOT_CONTRACT_ID
    identity: SnapshotIdentity = field(default_factory=SnapshotIdentity)
    governance_state: SnapshotGovernanceState = field(
        default_factory=SnapshotGovernanceState
    )
    delta: SnapshotDelta = field(default_factory=SnapshotDelta)
    quality: SnapshotQualitySignals = field(default_factory=SnapshotQualitySignals)
    architecture: SnapshotArchitecture = field(default_factory=SnapshotArchitecture)
    reviewer_hints: SnapshotReviewerHints = field(
        default_factory=SnapshotReviewerHints
    )
    reasoning: SnapshotReasoning = field(default_factory=SnapshotReasoning)
    known_gaps: SnapshotKnownGaps = field(default_factory=SnapshotKnownGaps)

    def to_dict(self) -> dict[str, object]:
        """Render the typed snapshot into a JSON-serialisable mapping."""
        # Late import avoids a circular dependency: review_snapshot_serialize
        # imports the dataclasses from this module.
        from .review_snapshot_serialize import (
            architecture_to_dict,
            delta_to_dict,
            governance_state_to_dict,
            known_gaps_to_dict,
            quality_to_dict,
            reasoning_to_dict,
            reviewer_hints_to_dict,
        )

        return {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "identity": asdict(self.identity),
            "governance_state": governance_state_to_dict(self.governance_state),
            "delta": delta_to_dict(self.delta),
            "quality": quality_to_dict(self.quality),
            "architecture": architecture_to_dict(self.architecture),
            "reviewer_hints": reviewer_hints_to_dict(self.reviewer_hints),
            "reasoning": reasoning_to_dict(self.reasoning),
            "known_gaps": known_gaps_to_dict(self.known_gaps),
        }


__all__ = [
    "REVIEW_SNAPSHOT_CONTRACT_ID",
    "REVIEW_SNAPSHOT_SCHEMA_VERSION",
    "CommitRow",
    "ContractOwnershipRow",
    "FileStatRow",
    "GovernanceFindingRow",
    "GuardResultRow",
    "HotspotRow",
    "KnownGapRow",
    "ProbeFindingRow",
    "ReviewSnapshot",
    "ReviewerHintRow",
    "SnapshotArchitecture",
    "SnapshotDelta",
    "SnapshotGovernanceState",
    "SnapshotIdentity",
    "SnapshotKnownGaps",
    "SnapshotQualitySignals",
    "SnapshotReasoning",
    "SnapshotReviewerHints",
    "WhyRecord",
]
