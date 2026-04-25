"""Connectivity-registry markdown helpers for startup-context."""

from __future__ import annotations

from .startup_context_render_format import join_paths as _join_paths


def append_connectivity_registry(lines: list[str], ctx_dict: dict) -> None:
    registry = ctx_dict.get("connectivity_registry", {})
    if not isinstance(registry, dict) or not registry:
        return
    lines.append("## Connectivity Registry")
    contract_id = str(registry.get("contract_id") or "").strip()
    if contract_id:
        lines.append(f"- contract_id: `{contract_id}`")
    lines.append(
        "- source_contract_count: "
        f"{int(registry.get('source_contract_count') or 0)}"
    )
    lines.append(
        "- connected_contract_count: "
        f"{int(registry.get('connected_contract_count') or 0)}"
    )
    lines.append(
        "- source_field_count: "
        f"{int(registry.get('source_field_count') or 0)}"
    )
    lines.append(
        "- zero_reader_field_count: "
        f"{int(registry.get('zero_reader_field_count') or 0)}"
    )
    _append_id_list(lines, registry, key="reader_ids")
    _append_id_list(lines, registry, key="governed_surface_ids")
    lines.append("")


def _append_id_list(lines: list[str], registry: dict, *, key: str) -> None:
    values = registry.get(key)
    if isinstance(values, (list, tuple)) and values:
        lines.append(f"- {key}: {_join_paths(values, limit=6)}")
