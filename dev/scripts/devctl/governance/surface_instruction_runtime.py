"""Instruction boot-card surface evaluator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..common_io import resolve_repo_path
from .instruction_boot_card import (
    FORBIDDEN_BOOT_CLAIMS,
    FORBIDDEN_BOOT_ROLE_PLACEHOLDERS,
    INSTRUCTION_BOOT_CARD_CONTRACT_ID,
    REQUIRED_BOOT_COMMANDS,
    REQUIRED_BOOT_ROLE_GUIDANCE,
    REQUIRED_BOOT_SECTIONS,
    REQUIRED_BOOT_SHELL_ESCAPE_GUIDANCE,
    REQUIRED_BOOT_TARGET_KIND_GUIDANCE,
    build_instruction_boot_card,
)
from .surface_runtime_common import (
    base_surface_entry,
    diff_preview,
    error_surface_entry,
    missing_required_contains,
)


def evaluate_instruction_boot_card_surface(
    spec: Any,
    *,
    context: dict[str, str],
    repo_root: Path,
    write: bool,
    allow_missing_local_only: bool,
) -> dict[str, Any]:
    """Evaluate one generated instruction boot-card surface."""
    output_path = resolve_repo_path(spec.output_path, repo_root=repo_root)
    source_path = (
        None
        if spec.source_path is None
        else resolve_repo_path(spec.source_path, repo_root=repo_root)
    )
    if source_path is not None and not source_path.exists():
        if not spec.optional_source:
            return error_surface_entry(
                spec,
                output_path,
                source_path,
                f"source file does not exist: {source_path}",
            )
        source_text = ""
    elif source_path is None:
        source_text = ""
    else:
        source_text = source_path.read_text(encoding="utf-8", errors="replace")

    missing_source_contains = missing_required_contains(
        source_text,
        spec.source_required_contains,
    )
    if missing_source_contains:
        entry = base_surface_entry(spec, output_path, source_path)
        entry["ok"] = False
        entry["state"] = "source-contract-error"
        entry["missing_source_required_contains"] = missing_source_contains
        entry["error"] = "source surface is missing required content"
        return entry

    rendered_text = build_instruction_boot_card(
        surface_id=spec.surface_id,
        output_path=spec.output_path,
        source_path=spec.source_path or "",
        repo_pack_id=context.get("repo_pack_id", ""),
        repo_pack_version=context.get("repo_pack_version", ""),
    )
    contract_error = _instruction_boot_card_contract_error(spec, rendered_text)
    if contract_error:
        entry = base_surface_entry(spec, output_path, source_path)
        entry.update(contract_error)
        return entry

    exists = output_path.exists()
    if not exists and allow_missing_local_only and spec.local_only:
        entry = base_surface_entry(spec, output_path, source_path)
        entry["ok"] = True
        entry["state"] = "missing-local-only"
        entry["exists"] = False
        entry["changed"] = False
        entry["wrote"] = False
        entry["projection_only"] = bool(spec.projection_only)
        return entry

    current_text = output_path.read_text(encoding="utf-8") if exists else ""
    changed = current_text != rendered_text
    wrote = False
    if write and changed:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered_text, encoding="utf-8")
        wrote = True
        changed = False
    entry = base_surface_entry(spec, output_path, source_path)
    entry["ok"] = not changed
    entry["state"] = "in-sync" if not changed else "drifted"
    entry["exists"] = output_path.exists()
    entry["changed"] = changed
    entry["wrote"] = wrote
    entry["projection_only"] = bool(spec.projection_only)
    entry["line_count"] = len(rendered_text.splitlines())
    entry["byte_count"] = len(rendered_text.encode("utf-8"))
    entry["diff_preview"] = (
        diff_preview(current_text, rendered_text)
        if current_text != rendered_text
        else []
    )
    return entry


def _instruction_boot_card_contract_error(
    spec: Any,
    rendered_text: str,
) -> dict[str, Any] | None:
    required_contains = (
        spec.required_contains
        + _instruction_boot_card_required_contains()
    )
    forbidden_contract_contains = (
        FORBIDDEN_BOOT_CLAIMS
        + FORBIDDEN_BOOT_ROLE_PLACEHOLDERS
    )
    missing_contains = missing_required_contains(rendered_text, required_contains)
    forbidden_contains = [
        snippet
        for snippet in spec.forbidden_contains + forbidden_contract_contains
        if snippet in rendered_text
    ]
    line_count = len(rendered_text.splitlines())
    byte_count = len(rendered_text.encode("utf-8"))
    errors: list[str] = []
    if missing_contains:
        errors.append("rendered surface is missing required content")
    if forbidden_contains:
        errors.append("rendered surface contains forbidden content")
    if spec.max_output_lines and line_count > spec.max_output_lines:
        errors.append("rendered surface exceeds max_output_lines")
    if spec.max_output_bytes and byte_count > spec.max_output_bytes:
        errors.append("rendered surface exceeds max_output_bytes")
    if not errors:
        return None
    return {
        "ok": False,
        "state": "render-contract-error",
        "error": "; ".join(errors),
        "missing_required_contains": missing_contains,
        "forbidden_contains": forbidden_contains,
        "line_count": line_count,
        "byte_count": byte_count,
    }


def _instruction_boot_card_required_contains() -> tuple[str, ...]:
    return (
        INSTRUCTION_BOOT_CARD_CONTRACT_ID,
        *REQUIRED_BOOT_SECTIONS,
        *REQUIRED_BOOT_COMMANDS,
        *REQUIRED_BOOT_ROLE_GUIDANCE,
        *REQUIRED_BOOT_TARGET_KIND_GUIDANCE,
        *REQUIRED_BOOT_SHELL_ESCAPE_GUIDANCE,
    )
