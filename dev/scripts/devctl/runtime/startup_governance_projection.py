"""Bounded startup-friendly projections of ProjectGovernance."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .project_governance import ProjectGovernance

_PUSH_ENFORCEMENT_STARTUP_FIELDS = (
    "checkpoint_required",
    "safe_to_continue_editing",
    "worktree_clean",
    "worktree_dirty",
    "checkpoint_reason",
    "recommended_action",
    "raw_git_push_guarded",
    "current_branch",
    "upstream_ref",
    "current_head_commit",
    "current_worktree_identity",
    "current_approved_target_identity",
    "current_push_authorization_valid",
    "current_push_authorization_id",
    "current_push_authorization_head_commit",
    "managed_projection_drift",
    "managed_projection_dirty_paths",
    "ahead_of_upstream_commits",
    "ahead_of_upstream_source_commits",
    "ahead_of_upstream_managed_receipt_commits",
    "dirty_path_count",
    "staged_path_count",
    "unstaged_path_count",
    "untracked_path_count",
    "publication_backlog_state",
    "publication_backlog_summary",
    "pending_publication_commits",
    "latest_push_report_status",
    "latest_push_report_reason",
    "latest_push_report_matches_current_branch",
    "latest_push_report_matches_current_head",
    "latest_push_report_matches_current_worktree",
    "latest_push_report_matches_current_approved_target",
    "selected_push_report_status",
    "selected_push_report_reason",
    "selected_push_report_matches_current_branch",
    "selected_push_report_matches_current_head",
    "selected_push_report_matches_current_worktree",
    "selected_push_report_matches_current_approved_target",
)


def startup_governance_dict(governance: ProjectGovernance) -> dict[str, Any]:
    """Return the bounded governance projection used by startup-context."""
    shared_backlog_paths = [
        entry.path
        for entry in governance.doc_registry.entries
        if entry.artifact_role == "shared_backlog"
    ]
    payload: dict[str, Any] = {}
    payload["schema_version"] = governance.schema_version
    payload["contract_id"] = governance.contract_id
    payload["repo_identity"] = asdict(governance.repo_identity)
    payload["repo_pack"] = asdict(governance.repo_pack)
    payload["path_roots"] = asdict(governance.path_roots)
    payload["plan_registry"] = {
        "registry_path": governance.plan_registry.registry_path,
        "tracker_path": governance.plan_registry.tracker_path,
        "index_path": governance.plan_registry.index_path,
        "entries": [
            _startup_plan_entry_dict(entry) for entry in governance.plan_registry.entries
        ],
    }
    payload["bridge_config"] = asdict(governance.bridge_config)
    payload["push_enforcement"] = _startup_push_enforcement_dict(
        governance.push_enforcement
    )
    payload["startup_order"] = list(governance.startup_order)
    payload["docs_authority"] = governance.docs_authority
    payload["process_authority_paths"] = list(
        governance.doc_policy.process_authority_paths
    )
    payload["projection_surface_paths"] = list(
        governance.doc_policy.projection_surface_paths
    )
    payload["docs_authority_interpretation"] = (
        "compatibility_startup_path; generated instruction boot cards are "
        "projection-only"
    )
    payload["workflow_profiles"] = list(governance.workflow_profiles)
    payload["command_routing_defaults"] = dict(governance.command_routing_defaults or {})
    payload["enabled_checks_summary"] = dict(
        guard_count=len(governance.enabled_checks.guard_ids),
        probe_count=len(governance.enabled_checks.probe_ids),
    )
    payload["doc_registry_summary"] = dict(
        entry_count=len(governance.doc_registry.entries),
        managed_count=sum(
            1 for entry in governance.doc_registry.entries if entry.registry_managed
        ),
        shared_backlog_count=len(shared_backlog_paths),
    )
    if shared_backlog_paths:
        payload["shared_backlog_paths"] = shared_backlog_paths
    if governance.memory_roots.configured():
        payload["memory_roots"] = governance.memory_roots.to_dict()
    return payload


def _startup_plan_entry_dict(entry) -> dict[str, object]:
    """Bounded plan-registry entry projection for the startup packet.

    The startup packet has a strict token budget (enforced by
    ``test_slim_token_budget``). Plan-registry entries are the dominant
    cost: a typical repo exposes 20+ entries and each additional field
    carries its own key/value/quote overhead, so every field kept here
    multiplies across the whole list. The fields below are the ones
    agent bootstraps actually need — file path, human title, the
    classification that tells them when and why to read the entry —
    and everything else is only available via the live
    ``ProjectGovernance.plan_registry.entries`` dataclass. Rendering
    code and ``governance.to_dict()`` consumers still see the full
    entry, so trimming is scoped to this single projection.

    Assignments are incremental rather than a single dict literal so the
    helper stays consistent with ``bounded_contract_ownership_map`` and
    the governed-projection idiom used elsewhere in this package.
    """
    payload: dict[str, object] = {}
    payload["path"] = entry.path
    payload["title"] = entry.title
    payload["artifact_role"] = entry.artifact_role
    payload["consumer_scope"] = entry.consumer_scope
    payload["when_agents_read"] = entry.when_agents_read
    payload["scope"] = entry.scope
    if entry.session_resume is not None and entry.session_resume.summary:
        payload["session_resume_summary"] = _brief_text(
            entry.session_resume.summary,
            limit=240,
        )
    return payload


def _startup_push_enforcement_dict(push_enforcement: object) -> dict[str, object]:
    payload: dict[str, object] = {}
    for field_name in _PUSH_ENFORCEMENT_STARTUP_FIELDS:
        value = getattr(push_enforcement, field_name, None)
        if value in (None, "", ()):
            continue
        if isinstance(value, tuple):
            payload[field_name] = list(value)
            continue
        payload[field_name] = value
    return payload


def _brief_text(value: str, *, limit: int) -> str:
    compact = " ".join(str(value or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: max(limit - 3, 0)].rstrip() + "..."
