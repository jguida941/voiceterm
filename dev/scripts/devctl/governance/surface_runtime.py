"""Runtime/render helpers for repo-pack surface generation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..common_io import resolve_repo_path
from .surface_instruction_runtime import evaluate_instruction_boot_card_surface
from .surface_runtime_common import (
    append_surface_lines,
    base_surface_entry,
    diff_preview,
    error_surface_entry,
    missing_required_contains,
)

_TOKEN_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def render_surface_report_markdown(report: dict[str, Any]) -> str:
    """Render one markdown report for `render-surfaces`."""
    lines = ["# devctl render-surfaces", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- repo_pack_id: {report.get('repo_pack_id', '(unknown)')}")
    lines.append(f"- repo_pack_version: {report.get('repo_pack_version', '(unknown)')}")
    lines.append(f"- policy_path: {report.get('policy_path')}")
    lines.append(f"- surface_count: {report.get('surface_count', 0)}")
    error = report.get("error")
    if error:
        lines.append(f"- error: {error}")
    warnings = report.get("warnings") or []
    if warnings:
        lines.extend(["", "## Warnings"])
        for warning in warnings:
            lines.append(f"- {warning}")
    registry = report.get("connectivity_registry")
    if isinstance(registry, dict) and registry:
        lines.extend(["", "## Connectivity Registry"])
        lines.append(f"- contract_id: `{registry.get('contract_id', '')}`")
        lines.append(
            "- connected_contract_count: "
            f"{registry.get('connected_contract_count', 0)}"
        )
        lines.append(
            "- source_field_count: "
            f"{registry.get('source_field_count', 0)}"
        )
        lines.append(
            "- zero_reader_field_count: "
            f"{registry.get('zero_reader_field_count', 0)}"
        )
    surfaces = report.get("surfaces") or []
    if surfaces:
        lines.extend(["", "## Surfaces"])
        for surface in surfaces:
            append_surface_lines(lines, surface)
    return "\n".join(lines)


def evaluate_surface(
    spec: Any,
    *,
    context: dict[str, str],
    repo_root: Path,
    write: bool,
    allow_missing_local_only: bool,
) -> dict[str, Any]:
    """Evaluate one governed surface and return its report entry."""
    if spec.renderer == "instruction_boot_card":
        return evaluate_instruction_boot_card_surface(
            spec,
            context=context,
            repo_root=repo_root,
            write=write,
            allow_missing_local_only=allow_missing_local_only,
        )
    if spec.renderer == "template_file":
        return _evaluate_template_surface(
            spec,
            context=context,
            repo_root=repo_root,
            write=write,
            allow_missing_local_only=allow_missing_local_only,
        )
    if spec.renderer == "system_map_renderer":
        return _evaluate_system_map_surface(spec, repo_root=repo_root, write=write)
    entry = base_surface_entry(
        spec,
        repo_root / spec.output_path,
        None if spec.template_path is None else repo_root / spec.template_path,
    )
    entry["ok"] = False
    entry["state"] = "unsupported-renderer"
    entry["error"] = f"unsupported renderer `{spec.renderer}`"
    return entry


def _evaluate_system_map_surface(
    spec: Any,
    *,
    repo_root: Path,
    write: bool,
) -> dict[str, Any]:
    from ..platform.connectivity_registry import summarize_connectivity_registry
    from ..platform.system_map import (
        build_system_map_snapshot,
        render_system_map_document,
    )

    output_path = resolve_repo_path(spec.output_path, repo_root=repo_root)
    current_text = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    snapshot = build_system_map_snapshot(repo_root=repo_root)
    rendered_text = render_system_map_document(current_text, snapshot)
    missing_contains = missing_required_contains(
        rendered_text,
        spec.required_contains,
    )
    if missing_contains:
        entry = base_surface_entry(spec, output_path, None)
        entry["ok"] = False
        entry["state"] = "render-contract-error"
        entry["missing_required_contains"] = missing_contains
        entry["error"] = "rendered surface is missing required content"
        return entry
    changed = current_text != rendered_text
    wrote = False
    if write and changed:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered_text, encoding="utf-8")
        wrote = True
        changed = False
    entry = base_surface_entry(spec, output_path, None)
    entry["ok"] = not changed
    entry["state"] = "in-sync" if not changed else "drifted"
    entry["exists"] = output_path.exists()
    entry["changed"] = changed
    entry["wrote"] = wrote
    entry["connectivity_registry"] = summarize_connectivity_registry(
        snapshot.connectivity_registry
    ).to_dict()
    entry["diff_preview"] = (
        diff_preview(current_text, rendered_text)
        if current_text != rendered_text
        else []
    )
    return entry

def _evaluate_template_surface(
    spec: Any,
    *,
    context: dict[str, str],
    repo_root: Path,
    write: bool,
    allow_missing_local_only: bool,
) -> dict[str, Any]:
    output_path = resolve_repo_path(spec.output_path, repo_root=repo_root)
    template_path = resolve_repo_path(spec.template_path, repo_root=repo_root)
    if not template_path.exists():
        return error_surface_entry(
            spec,
            output_path,
            template_path,
            f"template file does not exist: {template_path}",
        )
    rendered_text, missing_context_keys = _render_template_text(
        template_path.read_text(encoding="utf-8"),
        context,
    )
    if missing_context_keys:
        entry = base_surface_entry(spec, output_path, template_path)
        entry["ok"] = False
        entry["state"] = "template-error"
        entry["missing_context_keys"] = missing_context_keys
        entry["error"] = "template references missing context key(s)"
        return entry
    missing_contains = missing_required_contains(
        rendered_text,
        spec.required_contains,
    )
    if missing_contains:
        entry = base_surface_entry(spec, output_path, template_path)
        entry["ok"] = False
        entry["state"] = "render-contract-error"
        entry["missing_required_contains"] = missing_contains
        entry["error"] = "rendered surface is missing required content"
        return entry
    exists = output_path.exists()
    if not exists and allow_missing_local_only and spec.local_only:
        entry = base_surface_entry(spec, output_path, template_path)
        entry["ok"] = True
        entry["state"] = "missing-local-only"
        entry["exists"] = False
        entry["changed"] = False
        entry["wrote"] = False
        return entry
    current_text = output_path.read_text(encoding="utf-8") if exists else ""
    changed = current_text != rendered_text
    wrote = False
    if write and changed:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered_text, encoding="utf-8")
        wrote = True
        changed = False
    entry = base_surface_entry(spec, output_path, template_path)
    entry["ok"] = not changed
    entry["state"] = "in-sync" if not changed else "drifted"
    entry["exists"] = exists
    entry["changed"] = changed
    entry["wrote"] = wrote
    entry["diff_preview"] = (
        diff_preview(current_text, rendered_text) if current_text != rendered_text else []
    )
    return entry


def _render_template_text(
    template_text: str,
    context: dict[str, str],
) -> tuple[str, list[str]]:
    missing: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            missing.add(key)
            return match.group(0)
        return context[key]

    rendered = _TOKEN_RE.sub(replace, template_text)
    return rendered, sorted(missing)
