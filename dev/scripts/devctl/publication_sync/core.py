"""Shared external-publication sync helpers for devctl governance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..common import normalize_string_field, resolve_repo_path
from ..config import REPO_ROOT
from ..repo_packs.voiceterm import VOICETERM_PATH_CONFIG
from .git import (
    display_path,
    list_changed_paths,
    list_dirty_paths,
    normalize_watched_path,
    path_matches_watch,
    resolve_git_ref,
)
from ..time_utils import utc_timestamp

# Backward-compat alias sourced from repo-pack config
DEFAULT_PUBLICATION_SYNC_REGISTRY_REL = VOICETERM_PATH_CONFIG.publication_sync_registry_rel
DEFAULT_PUBLICATION_SYNC_REGISTRY = REPO_ROOT / DEFAULT_PUBLICATION_SYNC_REGISTRY_REL
PUBLICATION_SYNC_SCHEMA_VERSION = 1


def resolve_registry_path(
    registry_path: str | Path | None,
    *,
    repo_root: Path = REPO_ROOT,
) -> Path:
    """Resolve a registry path relative to repo root when needed."""
    return resolve_repo_path(
        registry_path,
        DEFAULT_PUBLICATION_SYNC_REGISTRY,
        repo_root=repo_root,
    )


def _read_registry_payload(
    registry_path: Path,
    *,
    allow_missing: bool,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not registry_path.is_file():
        if allow_missing:
            return {
                "schema_version": PUBLICATION_SYNC_SCHEMA_VERSION,
                "publications": [],
            }, errors
        return {}, [f"publication registry not found: {registry_path}"]

    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"unable to read publication registry {registry_path}: {exc}"]

    if not isinstance(payload, dict):
        return {}, ["publication registry must be a JSON object"]
    schema_version = payload.get("schema_version")
    if schema_version != PUBLICATION_SYNC_SCHEMA_VERSION:
        errors.append(
            "publication registry schema_version must be "
            f"{PUBLICATION_SYNC_SCHEMA_VERSION}, found {schema_version!r}"
        )
    publications = payload.get("publications")
    if not isinstance(publications, list):
        errors.append("publication registry field `publications` must be a list")
        publications = []
    return {
        "schema_version": schema_version,
        "publications": publications,
    }, errors


def _normalize_publication_entry(
    raw: Any,
    *,
    entry_index: int,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(raw, dict):
        return {"id": f"entry-{entry_index}"}, ["publication entry must be an object"]

    watched_raw = raw.get("watched_paths")
    watched_paths: list[str] = []
    if isinstance(watched_raw, list):
        watched_paths = [
            normalize_watched_path(item)
            for item in watched_raw
            if str(item).strip()
        ]
    else:
        errors.append("field `watched_paths` must be a non-empty list")

    entry = {
        "id": normalize_string_field(raw, "id"),
        "title": normalize_string_field(raw, "title"),
        "type": normalize_string_field(raw, "type", "generic"),
        "public_url": normalize_string_field(raw, "public_url"),
        "external_repo": normalize_string_field(raw, "external_repo"),
        "external_branch": normalize_string_field(raw, "external_branch"),
        "source_ref": normalize_string_field(raw, "source_ref"),
        "external_ref": normalize_string_field(raw, "external_ref"),
        "last_synced_at": normalize_string_field(raw, "last_synced_at"),
        "notes": normalize_string_field(raw, "notes"),
        "watched_paths": watched_paths,
    }
    for field_name in ("id", "title", "public_url", "external_repo", "source_ref"):
        if not entry[field_name]:
            errors.append(f"field `{field_name}` is required")
    if not watched_paths:
        errors.append("field `watched_paths` must contain at least one path")
    return entry, errors


def _evaluate_publication_entry(
    entry: dict[str, Any],
    *,
    entry_errors: list[str],
    repo_root: Path,
    resolved_head_ref: str,
    dirty_paths: list[str],
) -> dict[str, Any]:
    resolved_source_ref = ""
    changed_paths: list[str] = []
    impacted_paths: list[str] = []
    dirty_impacted_paths: list[str] = []
    if not entry_errors and resolved_head_ref:
        try:
            resolved_source_ref = resolve_git_ref(repo_root, entry["source_ref"])
            changed_paths = list_changed_paths(
                repo_root,
                resolved_source_ref,
                resolved_head_ref,
            )
            impacted_paths, dirty_impacted_paths = _resolve_impacted_paths(
                entry,
                changed_paths=changed_paths,
                dirty_paths=dirty_paths,
            )
        except ValueError as exc:
            entry_errors.append(str(exc))

    return {
        **entry,
        "errors": entry_errors,
        "resolved_source_ref": resolved_source_ref,
        "resolved_head_ref": resolved_head_ref,
        "changed_path_count": len(changed_paths),
        "impacted_path_count": len(impacted_paths),
        "impacted_paths": impacted_paths,
        "dirty_impacted_paths": dirty_impacted_paths,
        "stale": bool(impacted_paths),
    }


def _resolve_impacted_paths(
    entry: dict[str, Any],
    *,
    changed_paths: list[str],
    dirty_paths: list[str],
) -> tuple[list[str], list[str]]:
    committed_impacted = {
        path
        for path in changed_paths
        if _path_matches_entry_watch(path, entry)
    }
    dirty_impacted_paths = sorted(
        path
        for path in dirty_paths
        if path not in committed_impacted and _path_matches_entry_watch(path, entry)
    )
    impacted_paths = sorted(committed_impacted | set(dirty_impacted_paths))
    return impacted_paths, dirty_impacted_paths


def _path_matches_entry_watch(path: str, entry: dict[str, Any]) -> bool:
    return any(
        path_matches_watch(path, watched_path) for watched_path in entry["watched_paths"]
    )


def _selected_entry_matches(
    entry: dict[str, Any],
    *,
    selected_publication_id: str,
) -> bool:
    return not selected_publication_id or entry["id"] == selected_publication_id


def build_publication_sync_report(
    *,
    repo_root: Path = REPO_ROOT,
    registry_path: str | Path | None = None,
    publication_id: str | None = None,
    head_ref: str = "HEAD",
    allow_missing_registry: bool = False,
) -> dict[str, Any]:
    """Build one publication drift report from the tracked registry."""
    resolved_registry_path = resolve_registry_path(registry_path, repo_root=repo_root)
    payload, errors = _read_registry_payload(
        resolved_registry_path,
        allow_missing=allow_missing_registry,
    )
    publications_raw = payload.get("publications", [])

    resolved_head_ref = ""
    dirty_paths: list[str] = []
    if not errors:
        try:
            resolved_head_ref = resolve_git_ref(repo_root, head_ref)
        except ValueError as exc:
            errors.append(str(exc))
        dirty_paths = list_dirty_paths(repo_root)

    normalized_publications: list[dict[str, Any]] = []
    selected_publication_id = (publication_id or "").strip()
    seen_ids: set[str] = set()
    publication_found = not selected_publication_id

    for index, raw_entry in enumerate(publications_raw):
        entry, entry_errors = _normalize_publication_entry(raw_entry, entry_index=index)
        if not _selected_entry_matches(
            entry,
            selected_publication_id=selected_publication_id,
        ):
            continue
        publication_found = publication_found or entry["id"] == selected_publication_id

        if entry["id"] in seen_ids:
            entry_errors.append(f"duplicate publication id `{entry['id']}`")
        seen_ids.add(entry["id"])

        for watched_path in entry["watched_paths"]:
            candidate = repo_root / watched_path
            if not candidate.exists():
                entry_errors.append(
                    f"watched path `{watched_path}` does not exist under repo root"
                )

        normalized_publications.append(
            _evaluate_publication_entry(
                entry,
                entry_errors=entry_errors,
                repo_root=repo_root,
                resolved_head_ref=resolved_head_ref,
                dirty_paths=dirty_paths,
            )
        )

    if selected_publication_id and not publication_found:
        errors.append(f"publication `{selected_publication_id}` is not registered")

    publication_error_count = sum(
        len(item.get("errors", [])) for item in normalized_publications
    )
    stale_publication_count = sum(
        1 for item in normalized_publications if item.get("stale", False)
    )
    ok = (
        not errors
        and publication_error_count == 0
        and stale_publication_count == 0
    )

    return {
        "ok": ok,
        "registry_path": display_path(resolved_registry_path, repo_root=repo_root),
        "schema_version": payload.get("schema_version"),
        "head_ref": str(head_ref).strip() or "HEAD",
        "resolved_head_ref": resolved_head_ref,
        "publication_filter": selected_publication_id or None,
        "publication_count": len(normalized_publications),
        "stale_publication_count": stale_publication_count,
        "error_count": len(errors) + publication_error_count,
        "errors": errors,
        "publications": normalized_publications,
    }


def record_publication_sync(
    *,
    publication_id: str,
    source_ref: str,
    external_ref: str | None = None,
    synced_at: str | None = None,
    repo_root: Path = REPO_ROOT,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Update a publication entry after an external sync has completed."""
    resolved_registry_path = resolve_registry_path(registry_path, repo_root=repo_root)
    payload, errors = _read_registry_payload(
        resolved_registry_path,
        allow_missing=False,
    )
    if errors:
        raise ValueError("; ".join(errors))

    publications = payload["publications"]
    selected_id = str(publication_id).strip()
    if not selected_id:
        raise ValueError("publication_id is required")

    target_entry = _find_publication_entry(publications, selected_id)
    if target_entry is None:
        raise ValueError(f"publication `{selected_id}` is not registered")

    resolved_source_ref = resolve_git_ref(repo_root, source_ref)
    target_entry["source_ref"] = resolved_source_ref
    target_entry["last_synced_at"] = str(synced_at).strip() if synced_at else utc_timestamp()
    if external_ref is not None:
        target_entry["external_ref"] = str(external_ref).strip()

    resolved_registry_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_registry_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "publication": selected_id,
        "source_ref": resolved_source_ref,
        "external_ref": normalize_string_field(target_entry, "external_ref"),
        "last_synced_at": normalize_string_field(target_entry, "last_synced_at"),
        "registry_path": display_path(resolved_registry_path, repo_root=repo_root),
    }


def _find_publication_entry(
    publications: list[Any],
    selected_id: str,
) -> dict[str, Any] | None:
    for entry in publications:
        if not isinstance(entry, dict):
            continue
        if normalize_string_field(entry, "id") == selected_id:
            return entry
    return None
