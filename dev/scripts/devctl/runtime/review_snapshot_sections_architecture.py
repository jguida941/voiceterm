"""Architecture section builders for ReviewSnapshot."""

from __future__ import annotations

from collections.abc import Mapping

from .review_snapshot_models_sections import (
    ContractOwnershipRow,
    HotspotRow,
    SnapshotArchitecture,
)
from .review_snapshot_utils import as_list, as_mapping, coerce_int, coerce_str_tuple


def build_architecture(
    *,
    startup: Mapping[str, object],
    graph_bootstrap: Mapping[str, object],
    governance_contract: object | None = None,
) -> SnapshotArchitecture:
    """Return the architecture section from startup + graph bootstrap payloads."""
    ownership_rows = _build_ownership_rows(startup)
    hotspots = _build_hotspots(graph_bootstrap)
    active_plans = _build_active_plans(graph_bootstrap)
    snapshot_block = as_mapping(graph_bootstrap.get("snapshot"))
    return SnapshotArchitecture(
        contract_ownership_map=ownership_rows,
        hotspots=hotspots,
        active_plans=active_plans,
        graph_node_count=coerce_int(snapshot_block.get("node_count")),
        graph_edge_count=coerce_int(snapshot_block.get("edge_count")),
        graph_source_mode=str(snapshot_block.get("source_mode") or ""),
        key_doc_paths=_resolve_key_doc_paths(governance_contract),
    )


def _build_ownership_rows(
    startup: Mapping[str, object],
) -> tuple[ContractOwnershipRow, ...]:
    ownership_raw = as_mapping(startup.get("contract_ownership_map"))
    rows: list[ContractOwnershipRow] = []
    for contract_id, payload in ownership_raw.items():
        mapping = as_mapping(payload)
        rows.append(
            ContractOwnershipRow(
                contract_id=str(contract_id),
                owner_layer=str(mapping.get("owner_layer") or ""),
                runtime_model=str(mapping.get("runtime_model") or ""),
                startup_surface_tokens=coerce_str_tuple(
                    mapping.get("startup_surface_tokens")
                ),
            )
        )
    return tuple(rows)


def _build_hotspots(
    graph_bootstrap: Mapping[str, object],
) -> tuple[HotspotRow, ...]:
    rows: list[HotspotRow] = []
    for row in as_list(graph_bootstrap.get("hotspots"))[:12]:
        mapping = as_mapping(row)
        rows.append(
            HotspotRow(
                path=str(mapping.get("path") or ""),
                risk_level=str(mapping.get("risk_level") or ""),
                reasons=coerce_str_tuple(mapping.get("reasons")),
            )
        )
    return tuple(rows)


def _build_active_plans(graph_bootstrap: Mapping[str, object]) -> tuple[str, ...]:
    plans: list[str] = []
    for entry in as_list(graph_bootstrap.get("active_plans"))[:12]:
        mapping = as_mapping(entry)
        title = str(mapping.get("title") or mapping.get("id") or "")
        if title:
            plans.append(title)
    return tuple(plans)


def _resolve_key_doc_paths(governance: object | None) -> tuple[str, ...]:
    """Resolve reviewer key-doc pointers via ProjectGovernance typed fields."""
    if governance is None:
        return ()
    doc_policy = getattr(governance, "doc_policy", None)
    path_roots = getattr(governance, "path_roots", None)
    paths: list[str] = []
    if doc_policy is not None:
        for attr in ("docs_authority_path", "tracker_path", "index_path"):
            value = str(getattr(doc_policy, attr, "") or "").strip()
            if value and value not in paths:
                paths.append(value)
    if path_roots is not None:
        guides_root = str(getattr(path_roots, "guides", "") or "").strip()
        if guides_root:
            candidate = f"{guides_root.rstrip('/')}/AI_GOVERNANCE_PLATFORM.md"
            if candidate not in paths:
                paths.append(candidate)
    return tuple(paths)


__all__ = ["build_architecture"]
