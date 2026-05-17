"""Connectivity-registry markdown helpers for session-resume rendering."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session_resume_support import SessionCachePacket


def connectivity_registry_lines(packet: "SessionCachePacket") -> list[str]:
    registry = packet.connectivity_registry
    if not isinstance(registry, dict) or not registry:
        return []
    lines = ["", "### Connectivity Registry"]
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
    lines.append(
        "- aspirational_gap_count: "
        f"{int(registry.get('aspirational_gap_count') or 0)}"
    )
    _append_registry_id_lines(lines, registry)
    return lines


def connectivity_registry_summary_line(packet: "SessionCachePacket") -> str:
    registry = packet.connectivity_registry
    if not isinstance(registry, dict) or not registry:
        return "connectivity_registry=none"
    return (
        "connectivity_registry="
        f"{registry.get('connected_contract_count', 0)} contracts/"
        f"{registry.get('source_field_count', 0)} fields/"
        f"{registry.get('zero_reader_field_count', 0)} zero-reader/"
        f"{registry.get('aspirational_gap_count', 0)} aspirational-gap"
    )


def _append_registry_id_lines(lines: list[str], registry: dict[str, object]) -> None:
    reader_ids = registry.get("reader_ids")
    if isinstance(reader_ids, (list, tuple)) and reader_ids:
        shown = ", ".join(f"`{reader}`" for reader in reader_ids[:6])
        more = f", +{len(reader_ids) - 6} more" if len(reader_ids) > 6 else ""
        lines.append(f"- reader_ids: {shown}{more}")
    governed_surfaces = registry.get("governed_surface_ids")
    if isinstance(governed_surfaces, (list, tuple)) and governed_surfaces:
        shown = ", ".join(f"`{surface}`" for surface in governed_surfaces[:6])
        more = (
            f", +{len(governed_surfaces) - 6} more"
            if len(governed_surfaces) > 6
            else ""
        )
        lines.append(f"- governed_surface_ids: {shown}{more}")
