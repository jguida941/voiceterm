"""Typed bootstrap-command helpers for context-graph startup packets."""

from __future__ import annotations

from pathlib import Path

from ..governance.surfaces import load_surface_policy
from ..governance.system_catalog import build_system_catalog


def load_bootstrap_catalog_context(
    repo_root: Path,
) -> tuple[dict[str, str], list[dict[str, object]], dict[str, str | None]]:
    """Return key commands, typed bootstrap entries, and deep links."""
    command_entries = build_system_catalog().bootstrap_commands
    commands = {entry.command_id: entry.command for entry in command_entries}
    payloads = [_bootstrap_entry_payload(entry) for entry in command_entries]
    return commands, payloads, _load_bootstrap_links(repo_root)


def _bootstrap_entry_payload(entry) -> dict[str, object]:
    """Return a bounded bootstrap payload for startup packets."""
    payload: dict[str, object] = {
        "command_id": entry.command_id,
        "label": entry.label,
        "command_names": list(entry.command_names),
        "contract_ids": list(entry.contract_ids),
        "plan_paths": list(entry.plan_paths),
    }
    _add_preview_fields(payload, "guard", entry.guard_ids)
    _add_preview_fields(payload, "probe", entry.probe_ids)
    _add_preview_fields(payload, "surface", entry.surface_ids)
    return payload


def _add_preview_fields(
    payload: dict[str, object],
    prefix: str,
    values: tuple[str, ...],
) -> None:
    """Attach bounded count/preview metadata for a related inventory."""
    if not values:
        return
    payload[f"{prefix}_count"] = len(values)
    payload[f"{prefix}_ids_preview"] = list(values[:5])


def _load_bootstrap_links(repo_root: Path) -> dict[str, str | None]:
    """Load doc deep links from the governed surface policy."""
    try:
        policy = load_surface_policy(repo_root=repo_root)
        surface_ctx = policy.context
        connectivity_index = _connectivity_index_path(policy.surfaces)
    except (OSError, ValueError):
        surface_ctx = {}
        connectivity_index = ""

    process_doc = str(surface_ctx.get("process_doc", "AGENTS.md"))
    execution_tracker = str(
        surface_ctx.get("execution_tracker_doc", "dev/active/MASTER_PLAN.md")
    )
    active_registry = str(
        surface_ctx.get("active_registry_doc", "dev/active/INDEX.md")
    )
    links = {
        "sdlc_policy": process_doc,
        "execution_state": execution_tracker,
        "plan_registry": active_registry,
    }
    if connectivity_index:
        links["connectivity_index"] = connectivity_index
    return links


def _connectivity_index_path(surfaces: tuple[object, ...]) -> str:
    for surface in surfaces:
        if getattr(surface, "surface_type", "") != "connectivity_index":
            continue
        output_path = str(getattr(surface, "output_path", "") or "").strip()
        if output_path:
            return output_path
    return ""
