"""Repo-policy surface helpers for governed-markdown discovery."""

from __future__ import annotations

from typing import Any

from ..runtime.project_governance import RepoPackRef


def repo_governance_payload(policy: dict[str, Any]) -> dict[str, Any]:
    payload = policy.get("repo_governance")
    return payload if isinstance(payload, dict) else {}


def surface_generation_payload(policy: dict[str, Any]) -> dict[str, Any]:
    """Return repo_governance.surface_generation with legacy fallback."""
    governance = repo_governance_payload(policy)
    nested = governance.get("surface_generation")
    if isinstance(nested, dict):
        return nested
    legacy = policy.get("surface_generation")
    return legacy if isinstance(legacy, dict) else {}


def surface_generation_context(policy: dict[str, Any]) -> dict[str, Any]:
    context = surface_generation_payload(policy).get("context")
    return context if isinstance(context, dict) else {}


def check_router_payload(policy: dict[str, Any]) -> dict[str, Any]:
    payload = repo_governance_payload(policy).get("check_router")
    return payload if isinstance(payload, dict) else {}


def scan_repo_pack_ref(policy: dict[str, Any]) -> RepoPackRef:
    """Build RepoPackRef from repo-policy surface-generation metadata."""
    surface_gen = surface_generation_payload(policy)
    meta = surface_gen.get("repo_pack_metadata")
    meta = meta if isinstance(meta, dict) else {}
    pack_id = str(meta.get("pack_id", "")) or str(
        policy.get("repo_name", "")
    ).lower().replace(" ", "_")
    return RepoPackRef(
        pack_id=pack_id,
        pack_version=str(meta.get("pack_version", "")),
        description=str(meta.get("description", "")),
    )


__all__ = [
    "check_router_payload",
    "repo_governance_payload",
    "scan_repo_pack_ref",
    "surface_generation_context",
    "surface_generation_payload",
]
