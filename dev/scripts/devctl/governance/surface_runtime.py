"""Runtime/render helpers for repo-pack surface generation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from dev.scripts.checks import check_agents_bundle_render
except ImportError:  # pragma: no cover - standalone script fallback
    from checks import check_agents_bundle_render

from ..common_io import display_path, resolve_repo_path

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
    surfaces = report.get("surfaces") or []
    if surfaces:
        lines.extend(["", "## Surfaces"])
        for surface in surfaces:
            _append_surface_lines(lines, surface)
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
    if spec.renderer == "agents_bundle_section":
        return _evaluate_agents_bundle_surface(spec, repo_root=repo_root, write=write)
    if spec.renderer == "template_file":
        return _evaluate_template_surface(
            spec,
            context=context,
            repo_root=repo_root,
            write=write,
            allow_missing_local_only=allow_missing_local_only,
        )
    entry = _base_surface_entry(
        spec,
        repo_root / spec.output_path,
        None if spec.template_path is None else repo_root / spec.template_path,
    )
    entry["ok"] = False
    entry["state"] = "unsupported-renderer"
    entry["error"] = f"unsupported renderer `{spec.renderer}`"
    return entry


def _append_surface_lines(lines: list[str], surface: dict[str, Any]) -> None:
    state = surface.get("state", "unknown")
    lines.append(
        "- {surface_id}: type={surface_type}; renderer={renderer}; state={state}; ok={ok}; output={output_path}".format(
            surface_id=surface.get("surface_id"),
            surface_type=surface.get("surface_type"),
            renderer=surface.get("renderer"),
            state=state,
            ok=surface.get("ok"),
            output_path=surface.get("output_path"),
        )
    )
    if surface.get("template_path"):
        lines.append(f"  - template: {surface['template_path']}")
    if surface.get("description"):
        lines.append(f"  - description: {surface['description']}")
    if surface.get("diff_preview"):
        for diff_line in surface["diff_preview"][:6]:
            lines.append(f"  - diff: `{diff_line}`")
    if surface.get("error"):
        lines.append(f"  - error: {surface['error']}")
    if surface.get("missing_context_keys"):
        keys = ", ".join(surface["missing_context_keys"])
        lines.append(f"  - missing_context_keys: {keys}")
    if surface.get("missing_required_contains"):
        values = ", ".join(f"`{value}`" for value in surface["missing_required_contains"])
        lines.append(f"  - missing_required_contains: {values}")


def _evaluate_agents_bundle_surface(
    spec: Any,
    *,
    repo_root: Path,
    write: bool,
) -> dict[str, Any]:
    report = check_agents_bundle_render.build_report(write=write)
    entry = _base_surface_entry(spec, repo_root / spec.output_path, None)
    entry["ok"] = bool(report.get("ok", False))
    entry["state"] = (
        "in-sync" if report.get("ok", False) and not report.get("changed") else "drifted"
    )
    entry["changed"] = bool(report.get("changed", False))
    entry["wrote"] = bool(report.get("wrote", False))
    entry["diff_preview"] = list(report.get("diff_preview", []))
    entry["error"] = report.get("error")
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
        return _error_surface_entry(
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
        entry = _base_surface_entry(spec, output_path, template_path)
        entry["ok"] = False
        entry["state"] = "template-error"
        entry["missing_context_keys"] = missing_context_keys
        entry["error"] = "template references missing context key(s)"
        return entry
    missing_required_contains = _missing_required_contains(
        rendered_text,
        spec.required_contains,
    )
    if missing_required_contains:
        entry = _base_surface_entry(spec, output_path, template_path)
        entry["ok"] = False
        entry["state"] = "render-contract-error"
        entry["missing_required_contains"] = missing_required_contains
        entry["error"] = "rendered surface is missing required content"
        return entry
    exists = output_path.exists()
    if not exists and allow_missing_local_only and spec.local_only:
        entry = _base_surface_entry(spec, output_path, template_path)
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
    entry = _base_surface_entry(spec, output_path, template_path)
    entry["ok"] = not changed
    entry["state"] = "in-sync" if not changed else "drifted"
    entry["exists"] = exists
    entry["changed"] = changed
    entry["wrote"] = wrote
    entry["diff_preview"] = (
        _diff_preview(current_text, rendered_text) if current_text != rendered_text else []
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


def _missing_required_contains(
    rendered_text: str,
    required_contains: tuple[str, ...],
) -> list[str]:
    return [snippet for snippet in required_contains if snippet not in rendered_text]


def _diff_preview(current_text: str, rendered_text: str) -> list[str]:
    current_lines = current_text.splitlines()
    rendered_lines = rendered_text.splitlines()
    preview: list[str] = []
    for index, (current, rendered) in enumerate(zip(current_lines, rendered_lines), start=1):
        if current != rendered:
            preview.append(f"L{index}: - {current}")
            preview.append(f"L{index}: + {rendered}")
        if len(preview) >= 6:
            return preview[:6]
    if len(current_lines) != len(rendered_lines):
        preview.append(
            f"line-count: current={len(current_lines)} rendered={len(rendered_lines)}"
        )
    return preview[:6]


def _base_surface_entry(
    spec: Any,
    output_path: Path,
    template_path: Path | None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {}
    entry["surface_id"] = spec.surface_id
    entry["surface_type"] = spec.surface_type
    entry["renderer"] = spec.renderer
    entry["output_path"] = display_path(output_path)
    entry["template_path"] = (
        display_path(template_path) if template_path is not None else None
    )
    entry["description"] = spec.description
    entry["tracked"] = spec.tracked
    entry["local_only"] = spec.local_only
    return entry


def _error_surface_entry(
    spec: Any,
    output_path: Path,
    template_path: Path | None,
    error: str,
) -> dict[str, Any]:
    entry = _base_surface_entry(spec, output_path, template_path)
    entry["ok"] = False
    entry["state"] = "error"
    entry["error"] = error
    return entry
