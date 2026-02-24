"""Policy helpers for external integration federation commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .mutation_loop_policy import load_policy


DEFAULT_ALLOWED_DESTINATION_ROOTS = ["dev/integrations/imports"]
DEFAULT_AUDIT_LOG_PATH = "dev/reports/integration_import_audit.jsonl"
POLICY_KEY = "integration_federation"


def load_federation_policy(repo_root: Path) -> dict[str, Any]:
    """Return the `integration_federation` policy section (or empty dict)."""
    payload = load_policy(repo_root)
    section = payload.get(POLICY_KEY)
    if isinstance(section, dict):
        return section
    return {}


def federation_sources(policy_section: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return source-name -> source-config map from policy."""
    raw = policy_section.get("sources")
    if not isinstance(raw, dict):
        return {}
    sources: dict[str, dict[str, Any]] = {}
    for name, value in raw.items():
        source_name = str(name).strip()
        if not source_name or not isinstance(value, dict):
            continue
        sources[source_name] = value
    return sources


def federation_audit_log_path(repo_root: Path, policy_section: dict[str, Any]) -> Path:
    """Resolve audit-log path from policy with safe fallback."""
    raw = str(policy_section.get("audit_log_path") or "").strip()
    relative = raw or DEFAULT_AUDIT_LOG_PATH
    return repo_root / relative


def federation_max_files(policy_section: dict[str, Any], fallback: int = 1200) -> int:
    """Resolve maximum files allowed per import action."""
    raw = policy_section.get("max_files_per_import")
    if isinstance(raw, int) and raw > 0:
        return raw
    return fallback


def federation_allowed_destination_roots(
    repo_root: Path,
    policy_section: dict[str, Any],
) -> list[Path]:
    """Resolve allowlisted destination roots for import operations."""
    raw = policy_section.get("allowed_destination_roots")
    values: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            candidate = str(item).strip()
            if candidate:
                values.append(candidate)
    if not values:
        values = list(DEFAULT_ALLOWED_DESTINATION_ROOTS)
    return [repo_root / item for item in values]


def source_repo_path(repo_root: Path, source_cfg: dict[str, Any]) -> Path | None:
    """Resolve source repo path from one policy source entry."""
    raw = str(source_cfg.get("path") or "").strip()
    if not raw:
        return None
    return repo_root / raw
