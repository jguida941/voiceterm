"""Shared helpers for review-channel context-pack attachments."""

from __future__ import annotations

from pathlib import Path

from ..common import display_path, read_json_object, resolve_repo_path

CONTEXT_PACK_KIND_ALIASES = {"session_handoff": "handoff_pack"}
VALID_CONTEXT_PACK_KINDS = {"task_pack", "handoff_pack", "survival_index"}
VALID_CONTEXT_PACK_ADAPTER_PROFILES = {"canonical", "codex", "claude", "gemini"}


def normalize_context_pack_refs(context_pack_refs: object) -> list[dict[str, str]]:
    """Return a compact list of valid context-pack attachment objects."""
    if not isinstance(context_pack_refs, list):
        return []
    rows: list[dict[str, str]] = []
    for row in context_pack_refs:
        if not isinstance(row, dict):
            continue
        pack_kind = str(row.get("pack_kind") or "").strip()
        pack_ref = str(row.get("pack_ref") or "").strip()
        if not pack_kind or not pack_ref:
            continue
        normalized = {
            "pack_kind": pack_kind,
            "pack_ref": pack_ref,
        }
        adapter_profile = str(row.get("adapter_profile") or "").strip()
        if adapter_profile:
            normalized["adapter_profile"] = adapter_profile
        generated_at_utc = str(row.get("generated_at_utc") or "").strip()
        if generated_at_utc:
            normalized["generated_at_utc"] = generated_at_utc
        rows.append(normalized)
    return rows


def context_pack_ref_summary(context_pack_refs: object) -> str:
    """Return a short comma-separated summary for attached context packs."""
    normalized = normalize_context_pack_refs(context_pack_refs)
    if not normalized:
        return ""
    return ", ".join(str(ref["pack_kind"]) for ref in normalized)


def resolve_context_pack_refs(args, repo_root: Path) -> list[dict[str, str]]:
    """Resolve CLI `--context-pack-ref` values into canonical packet attachments."""
    raw_refs = list(getattr(args, "context_pack_ref", []) or [])
    if not raw_refs:
        return []
    adapter_profile = str(
        getattr(args, "context_pack_adapter_profile", "canonical") or "canonical"
    ).strip()
    if adapter_profile not in VALID_CONTEXT_PACK_ADAPTER_PROFILES:
        raise ValueError(
            "--context-pack-adapter-profile must be one of: "
            + ", ".join(sorted(VALID_CONTEXT_PACK_ADAPTER_PROFILES))
        )
    resolved_refs: list[dict[str, str]] = []
    for raw_ref in raw_refs:
        resolved_ref = _resolve_one_context_pack_ref(
            raw_ref=str(raw_ref),
            adapter_profile=adapter_profile,
            repo_root=repo_root,
        )
        if resolved_ref not in resolved_refs:
            resolved_refs.append(resolved_ref)
    return resolved_refs


def _resolve_one_context_pack_ref(
    *,
    raw_ref: str,
    adapter_profile: str,
    repo_root: Path,
) -> dict[str, str]:
    pack_kind_raw, separator, pack_ref_raw = raw_ref.partition(":")
    if not separator or not pack_ref_raw.strip():
        raise ValueError(
            "--context-pack-ref must use kind:path form, for example "
            "task_pack:.voiceterm/memory/exports/task_pack.json"
        )
    pack_kind = CONTEXT_PACK_KIND_ALIASES.get(
        pack_kind_raw.strip(),
        pack_kind_raw.strip(),
    )
    if pack_kind not in VALID_CONTEXT_PACK_KINDS:
        raise ValueError(
            "--context-pack-ref kind must be one of: "
            + ", ".join(sorted(VALID_CONTEXT_PACK_KINDS | set(CONTEXT_PACK_KIND_ALIASES)))
        )
    resolved_path = resolve_repo_path(pack_ref_raw.strip(), repo_root=repo_root)
    pack_ref = display_path(resolved_path, repo_root=repo_root)
    if pack_ref.startswith("..") or Path(pack_ref).is_absolute():
        raise ValueError(
            "--context-pack-ref must stay inside the repo and use a repo-visible path."
        )
    if resolved_path.suffix != ".json":
        raise ValueError("--context-pack-ref must point to a JSON export artifact.")
    if not resolved_path.is_file():
        raise ValueError(
            f"--context-pack-ref target does not exist: {display_path(resolved_path, repo_root=repo_root)}"
        )
    payload, error = read_json_object(
        resolved_path,
        missing_message="missing context-pack export: {path}",
        invalid_message="invalid context-pack export JSON ({error})",
        object_message="context-pack export must be a JSON object",
    )
    if payload is None:
        raise ValueError(error or "unable to load context-pack export")
    generated_at = str(payload.get("generated_at_utc") or payload.get("generated_at") or "").strip()
    resolved_ref: dict[str, str] = {
        "pack_kind": pack_kind,
        "pack_ref": pack_ref,
        "adapter_profile": adapter_profile,
    }
    if generated_at:
        resolved_ref["generated_at_utc"] = generated_at
    return resolved_ref
