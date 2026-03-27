"""Bounded startup-friendly projections of ProjectGovernance."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .project_governance import ProjectGovernance


def startup_governance_dict(governance: ProjectGovernance) -> dict[str, Any]:
    """Return the bounded governance projection used by startup-context."""
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
    payload["push_enforcement"] = asdict(governance.push_enforcement)
    payload["startup_order"] = list(governance.startup_order)
    payload["docs_authority"] = governance.docs_authority
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
    )
    if governance.memory_roots.configured():
        payload["memory_roots"] = governance.memory_roots.to_dict()
    return payload


def _startup_plan_entry_dict(entry) -> dict[str, object]:
    payload: dict[str, object] = {}
    payload["path"] = entry.path
    payload["role"] = entry.role
    payload["artifact_role"] = entry.artifact_role
    payload["authority_kind"] = entry.authority_kind
    payload["system_scope"] = entry.system_scope
    payload["consumer_scope"] = entry.consumer_scope
    payload["authority"] = entry.authority
    payload["scope"] = entry.scope
    payload["when_agents_read"] = entry.when_agents_read
    payload["title"] = entry.title
    payload["lifecycle"] = entry.lifecycle
    payload["has_execution_plan_contract"] = entry.has_execution_plan_contract
    if entry.session_resume is not None and entry.session_resume.summary:
        payload["session_resume_summary"] = entry.session_resume.summary
    return payload
