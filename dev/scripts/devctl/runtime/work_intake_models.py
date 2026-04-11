"""Typed models for startup work-intake packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .finding_contracts import (
    RejectedRuleTraceRecord,
    RuleMatchEvidenceRecord,
)


@dataclass(frozen=True, slots=True)
class PlanTargetRef:
    """Canonical mutable plan target selected for startup continuity."""

    target_id: str
    plan_path: str
    plan_title: str
    plan_scope: str
    target_kind: str
    anchor_ref: str
    expected_revision: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SessionContinuityState:
    """Reconciled continuity state across plan resume and live review state."""

    source_plan_path: str = ""
    source_plan_title: str = ""
    source_scope: str = ""
    summary: str = ""
    current_goal: str = ""
    next_action: str = ""
    review_scope: str = ""
    review_instruction: str = ""
    review_open_findings: str = ""
    implementer_status: str = ""
    alignment_status: str = "missing"
    alignment_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class IntakeRoutingState:
    """Live startup-routing decisions derived from ProjectGovernance."""

    startup_reads: tuple[str, ...] = ()
    workflow_profiles: tuple[str, ...] = ()
    selected_workflow_profile: str = ""
    default_remote: str = ""
    development_branch: str = ""
    preflight_command: str = ""
    post_push_bundle: str = ""
    rule_summary: str = ""
    match_evidence: tuple[RuleMatchEvidenceRecord, ...] = ()
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["startup_reads"] = list(self.startup_reads)
        payload["workflow_profiles"] = list(self.workflow_profiles)
        payload["match_evidence"] = [
            evidence.to_dict() for evidence in self.match_evidence
        ]
        payload["rejected_rule_traces"] = [
            trace.to_dict() for trace in self.rejected_rule_traces
        ]
        return payload


@dataclass(frozen=True, slots=True)
class WorkIntakeOwnershipState:
    """Dirty-path ownership classification for the current startup slice."""

    status: str = "clear"
    summary: str = ""
    scope_source: str = ""
    scope_path_count: int = 0
    dirty_path_count: int = 0
    outside_scope_dirty_path_count: int = 0
    scope_paths: tuple[str, ...] = ()
    dirty_paths: tuple[str, ...] = ()
    in_scope_dirty_paths: tuple[str, ...] = ()
    outside_scope_dirty_paths: tuple[str, ...] = ()
    live_agents: tuple[str, ...] = ()
    live_delegated_agents: tuple[str, ...] = ()
    peer_activity_detected: bool = False
    concurrent_writer_detected: bool = False

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"status": self.status}
        if self.scope_source:
            payload["scope_source"] = self.scope_source
        if self.summary and self.status in {
            "concurrent_writer_activity",
            "scope_unknown_dirty_paths",
        }:
            payload["summary"] = self.summary
        if self.scope_paths:
            payload["scope_paths"] = list(self.scope_paths)
        if self.outside_scope_dirty_paths:
            payload["outside_scope_dirty_paths"] = list(self.outside_scope_dirty_paths)
        if self.live_agents:
            payload["live_agents"] = list(self.live_agents)
        if self.live_delegated_agents:
            payload["live_delegated_agents"] = list(self.live_delegated_agents)
        if self.peer_activity_detected:
            payload["peer_activity_detected"] = True
        if self.concurrent_writer_detected:
            payload["concurrent_writer_detected"] = True
        return payload


@dataclass(frozen=True, slots=True)
class WorkIntakeCoordinationState:
    """Bounded startup-facing reduction of live coordination state."""

    collaboration_topology: str = "single_agent"
    authority_mode: str = "self_directed"
    work_ownership_mode: str = "exclusive_slice"
    sync_cadence_mode: str = "continuous"
    reviewer_mode: str = ""
    effective_reviewer_mode: str = ""
    interaction_mode: str = "unresolved"
    implementation_permission: str = ""
    summary: str = ""
    active_implementation_owner: str = ""
    active_participant_count: int = 0
    live_delegated_worker_count: int = 0
    active_roles: tuple[str, ...] = ()
    active_participants: tuple[str, ...] = ()
    delegated_agents: tuple[str, ...] = ()
    delegated_worktrees: tuple[str, ...] = ()
    duplicate_delegated_worktrees: tuple[str, ...] = ()
    resync_required: bool = False
    concurrent_writer_conflict_detected: bool = False

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "authority_mode": self.authority_mode,
            "work_ownership_mode": self.work_ownership_mode,
            "sync_cadence_mode": self.sync_cadence_mode,
        }
        if self.collaboration_topology != "single_agent":
            payload["collaboration_topology"] = self.collaboration_topology
        if self.interaction_mode and self.interaction_mode != "unresolved":
            payload["interaction_mode"] = self.interaction_mode
        if self.implementation_permission:
            payload["implementation_permission"] = self.implementation_permission
        if self.active_implementation_owner:
            payload["active_implementation_owner"] = self.active_implementation_owner
        if self.active_participant_count:
            payload["active_participant_count"] = self.active_participant_count
        if self.live_delegated_worker_count:
            payload["live_delegated_worker_count"] = self.live_delegated_worker_count
        if self.active_roles:
            payload["active_roles"] = list(self.active_roles)
        if self.active_participants:
            payload["active_participants"] = list(self.active_participants)
        if self.delegated_agents:
            payload["delegated_agents"] = list(self.delegated_agents)
        if self.delegated_worktrees:
            payload["delegated_worktrees"] = list(self.delegated_worktrees)
        if self.duplicate_delegated_worktrees:
            payload["duplicate_delegated_worktrees"] = list(
                self.duplicate_delegated_worktrees
            )
        if self.resync_required:
            payload["resync_required"] = True
        if self.concurrent_writer_conflict_detected:
            payload["concurrent_writer_conflict_detected"] = True
        return payload


def work_intake_coordination_from_mapping(
    value: object,
) -> WorkIntakeCoordinationState | None:
    """Deserialize one coordination-state payload from a JSON-like mapping."""
    if not isinstance(value, dict):
        return None
    return WorkIntakeCoordinationState(
        collaboration_topology=str(
            value.get("collaboration_topology") or "single_agent"
        ).strip(),
        authority_mode=str(value.get("authority_mode") or "self_directed").strip(),
        work_ownership_mode=str(
            value.get("work_ownership_mode") or "exclusive_slice"
        ).strip(),
        sync_cadence_mode=str(
            value.get("sync_cadence_mode") or "continuous"
        ).strip(),
        reviewer_mode=str(value.get("reviewer_mode") or "").strip(),
        effective_reviewer_mode=str(
            value.get("effective_reviewer_mode") or ""
        ).strip(),
        interaction_mode=str(value.get("interaction_mode") or "unresolved").strip(),
        implementation_permission=str(
            value.get("implementation_permission") or ""
        ).strip(),
        summary=str(value.get("summary") or "").strip(),
        active_implementation_owner=str(
            value.get("active_implementation_owner") or ""
        ).strip(),
        active_participant_count=int(value.get("active_participant_count") or 0),
        live_delegated_worker_count=int(
            value.get("live_delegated_worker_count") or 0
        ),
        active_roles=tuple(
            str(item).strip()
            for item in value.get("active_roles", ())
            if str(item).strip()
        ),
        active_participants=tuple(
            str(item).strip()
            for item in value.get("active_participants", ())
            if str(item).strip()
        ),
        delegated_agents=tuple(
            str(item).strip()
            for item in value.get("delegated_agents", ())
            if str(item).strip()
        ),
        delegated_worktrees=tuple(
            str(item).strip()
            for item in value.get("delegated_worktrees", ())
            if str(item).strip()
        ),
        duplicate_delegated_worktrees=tuple(
            str(item).strip()
            for item in value.get("duplicate_delegated_worktrees", ())
            if str(item).strip()
        ),
        resync_required=bool(value.get("resync_required", False)),
        concurrent_writer_conflict_detected=bool(
            value.get("concurrent_writer_conflict_detected", False)
        ),
    )


@dataclass(frozen=True, slots=True)
class SessionPacingState:
    """Bounded research-to-implementation pacing guidance from repo evidence."""

    strategy: str = "bounded_research_then_patch"
    source: str = "unavailable"
    confidence: str = "low"
    complexity_band: str = "unknown"
    complexity_score: int = 0
    research_ref_budget: int = 0
    authority_ref_count: int = 0
    focus_file_count: int = 0
    dependency_edge_count: int = 0
    hot_path_count: int = 0
    live_finding_count: int = 0
    implementation_trigger: str = "patch_after_bounded_refs_or_raise_blocker"
    focus_slice_id: str = ""
    focus_summary: str = ""
    authority_refs: tuple[str, ...] = ()
    implementation_refs: tuple[str, ...] = ()
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["authority_refs"] = list(self.authority_refs)
        payload["implementation_refs"] = list(self.implementation_refs)
        if not self.focus_slice_id:
            payload.pop("focus_slice_id", None)
        if not self.focus_summary:
            payload.pop("focus_summary", None)
        if not self.summary:
            payload.pop("summary", None)
        return payload


def session_pacing_markdown_lines(pacing: object) -> tuple[str, ...]:
    """Render the bounded pacing payload for startup-context markdown."""
    if not isinstance(pacing, dict) or not pacing:
        return ()

    lines = [
        f"- session_pacing: `{pacing.get('complexity_band', 'unknown')}` via `{pacing.get('source', 'unavailable')}`",
        f"- research_ref_budget: {pacing.get('research_ref_budget', 0)}",
        f"- dependency_edge_count: {pacing.get('dependency_edge_count', 0)}",
        f"- implementation_trigger: `{pacing.get('implementation_trigger', '')}`",
    ]
    summary = str(pacing.get("summary") or "").strip()
    if summary:
        lines.append(f"- pacing_summary: {summary}")
    implementation_refs = pacing.get("implementation_refs")
    if isinstance(implementation_refs, list) and implementation_refs:
        joined = ", ".join(f"`{path}`" for path in implementation_refs[:4])
        if len(implementation_refs) > 4:
            joined = f"{joined}, +{len(implementation_refs) - 4} more"
        lines.append(f"- implementation_refs: {joined}")
    return tuple(lines)


@dataclass(frozen=True, slots=True)
class WorkIntakePacket:
    """First bounded startup/work-routing packet for AI sessions."""

    schema_version: int = 1
    contract_id: str = "WorkIntakePacket"
    goal: str = "startup-context"
    advisory_action: str = ""
    advisory_reason: str = ""
    active_target: PlanTargetRef | None = None
    continuity: SessionContinuityState = field(default_factory=SessionContinuityState)
    routing: IntakeRoutingState = field(default_factory=IntakeRoutingState)
    ownership: WorkIntakeOwnershipState = field(default_factory=WorkIntakeOwnershipState)
    coordination: WorkIntakeCoordinationState = field(
        default_factory=WorkIntakeCoordinationState
    )
    session_pacing: SessionPacingState = field(default_factory=SessionPacingState)
    scope_hints: tuple[str, ...] = ()
    warm_refs: tuple[str, ...] = ()
    writeback_sinks: tuple[str, ...] = ()
    confidence: str = "low"
    fallback_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        payload["scope_hints"] = list(self.scope_hints)
        payload["warm_refs"] = list(self.warm_refs)
        payload["writeback_sinks"] = list(self.writeback_sinks)
        payload["confidence"] = self.confidence
        if self.active_target is not None:
            payload["active_target"] = self.active_target.to_dict()
        payload["continuity"] = self.continuity.to_dict()
        payload["routing"] = self.routing.to_dict()
        payload["ownership"] = self.ownership.to_dict()
        payload["coordination"] = self.coordination.to_dict()
        payload["session_pacing"] = self.session_pacing.to_dict()
        if self.fallback_reason:
            payload["fallback_reason"] = self.fallback_reason
        return payload


__all__ = [
    "IntakeRoutingState",
    "PlanTargetRef",
    "SessionPacingState",
    "SessionContinuityState",
    "WorkIntakeCoordinationState",
    "WorkIntakeOwnershipState",
    "WorkIntakePacket",
    "work_intake_coordination_from_mapping",
    "session_pacing_markdown_lines",
]
