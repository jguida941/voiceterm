"""Shared helpers for repo-pack surface renderers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..common_io import display_path


def append_surface_lines(lines: list[str], surface: dict[str, Any]) -> None:
    """Append one surface row to a render-surfaces markdown report."""
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
        values = ", ".join(
            f"`{value}`" for value in surface["missing_required_contains"]
        )
        lines.append(f"  - missing_required_contains: {values}")


def base_surface_entry(
    spec: Any,
    output_path: Path,
    source_path: Path | None,
) -> dict[str, Any]:
    """Build the common report entry fields for a surface."""
    entry: dict[str, Any] = {}
    entry["surface_id"] = spec.surface_id
    entry["surface_type"] = spec.surface_type
    entry["renderer"] = spec.renderer
    entry["output_path"] = display_path(output_path)
    entry["template_path"] = (
        display_path(source_path) if source_path is not None else None
    )
    entry["description"] = spec.description
    entry["tracked"] = spec.tracked
    entry["local_only"] = spec.local_only
    entry["source_path"] = display_path(source_path) if source_path else None
    if hasattr(spec, "projection_only"):
        entry["projection_only"] = bool(spec.projection_only)
    return entry


def error_surface_entry(
    spec: Any,
    output_path: Path,
    source_path: Path | None,
    error: str,
) -> dict[str, Any]:
    """Build a common failed surface report entry."""
    entry = base_surface_entry(spec, output_path, source_path)
    entry["ok"] = False
    entry["state"] = "error"
    entry["error"] = error
    return entry


def missing_required_contains(
    rendered_text: str,
    required_contains: tuple[str, ...],
) -> list[str]:
    """Return required snippets that are absent from rendered text."""
    return [snippet for snippet in required_contains if snippet not in rendered_text]


def diff_preview(current_text: str, rendered_text: str) -> list[str]:
    """Return a small line-oriented preview for a drifted surface."""
    current_lines = current_text.splitlines()
    rendered_lines = rendered_text.splitlines()
    preview: list[str] = []
    for index, (current, rendered) in enumerate(
        zip(current_lines, rendered_lines), start=1
    ):
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
