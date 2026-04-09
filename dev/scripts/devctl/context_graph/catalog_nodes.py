"""Supporting node collectors for context-graph construction."""

from __future__ import annotations

import importlib
from pathlib import Path

from ..governance.doc_authority_rules import parse_index_registry
from .models import (
    EDGE_KIND_RELATED_TO,
    EDGE_KIND_ROUTES_TO,
    NODE_KIND_CAPABILITY,
    NODE_KIND_COMMAND,
    NODE_KIND_GUIDE,
    NODE_KIND_PLAN,
    GraphEdge,
    GraphNode,
)

_PLAN_CONCEPT_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("review.channel", "dev/scripts/devctl/review_channel"),
    ("review channel", "dev/scripts/devctl/review_channel"),
    ("autonomous", "dev/scripts/devctl/autonomy"),
    ("autonomy", "dev/scripts/devctl/autonomy"),
    ("operator console", "app/operator_console"),
    ("theme", "app/operator_console/theme"),
    ("memory", "rust/src/memory"),
    ("probe", "dev/scripts/checks"),
    ("governance", "dev/scripts/devctl/governance"),
    ("mobile", "app/ios"),
)
_ACTIVE_PLAN_ROLES = {"tracker", "spec"}


def _plan_metadata(
    *,
    role: str,
    authority: str,
    scope_raw: str,
    when_text: str,
    is_active_plan: bool,
) -> dict[str, object]:
    """Build plan-node metadata without a large inline dict literal."""
    metadata: dict[str, object] = {}
    metadata["role"] = role
    metadata["authority"] = authority
    metadata["scope"] = scope_raw.replace("`", "").strip().strip(",").strip()
    metadata["when"] = when_text.strip()
    metadata["is_active_plan"] = is_active_plan
    return metadata


def _bootstrap_command_metadata(entry: object) -> dict[str, object]:
    """Build bootstrap-command metadata without a large inline dict literal."""
    metadata: dict[str, object] = {}
    metadata["capability_kind"] = "bootstrap_command"
    metadata["command"] = entry.command
    metadata["description"] = entry.description
    metadata["command_names"] = list(entry.command_names)
    metadata["guard_ids"] = list(entry.guard_ids)
    metadata["probe_ids"] = list(entry.probe_ids)
    metadata["surface_ids"] = list(entry.surface_ids)
    metadata["contract_ids"] = list(entry.contract_ids)
    metadata["plan_paths"] = list(entry.plan_paths)
    return metadata


def collect_plan_nodes(repo_root: Path) -> tuple[list[GraphNode], list[tuple[str, str]]]:
    from ..repo_packs import active_path_config

    path_config = active_path_config()
    index_path = repo_root / path_config.active_index_doc_rel
    registry = parse_index_registry(index_path)
    nodes: list[GraphNode] = []
    deferred_edges: list[tuple[str, str]] = []
    for path, row in registry.items():
        role = row.get("role", "")
        when = row.get("when", "").lower()
        is_active_plan = role in _ACTIVE_PLAN_ROLES
        if row.get("authority") == "canonical":
            temperature = 0.6
        elif is_active_plan:
            temperature = 0.3
        else:
            temperature = 0.1
        plan_id = f"plan:{path}"
        scope_raw = row.get("scope", "")
        nodes.append(
            GraphNode(
                node_id=plan_id,
                node_kind=NODE_KIND_PLAN,
                label=path,
                canonical_pointer_ref=path,
                provenance_ref=str(index_path.relative_to(repo_root)),
                temperature=temperature,
                metadata=_plan_metadata(
                    role=role,
                    authority=row.get("authority", ""),
                    scope_raw=scope_raw,
                    when_text=when,
                    is_active_plan=is_active_plan,
                ),
            )
        )
        for keyword, concept_dir in _PLAN_CONCEPT_KEYWORDS:
            if keyword in when:
                deferred_edges.append((plan_id, f"concept:{concept_dir}"))
                break
    return nodes, deferred_edges


def collect_guide_nodes(repo_root: Path) -> list[GraphNode]:
    guides_dir = repo_root / "dev" / "guides"
    if not guides_dir.is_dir():
        return []
    nodes: list[GraphNode] = []
    for guide_path in sorted(guides_dir.glob("*.md")):
        rel = guide_path.relative_to(repo_root).as_posix()
        nodes.append(
            GraphNode(
                node_id=f"guide:{rel}",
                node_kind=NODE_KIND_GUIDE,
                label=guide_path.stem,
                canonical_pointer_ref=rel,
                provenance_ref="dev/guides/",
                temperature=0.05,
            )
        )
    return nodes


def collect_command_nodes(node_ids: set[str]) -> tuple[list[GraphNode], list[GraphEdge]]:
    try:
        cli_mod = importlib.import_module("dev.scripts.devctl.cli")
        handlers = getattr(cli_mod, "COMMAND_HANDLERS", {})
    except (ImportError, ModuleNotFoundError):
        handlers = {}

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    for cmd_name, handler in sorted(handlers.items()):
        normalized = cmd_name.replace("-", "_")
        handler_module = getattr(handler, "__module__", "") or ""
        if handler_module.startswith("dev.scripts.devctl."):
            suffix = handler_module[len("dev.scripts.devctl."):]
        elif handler_module.startswith("devctl."):
            suffix = handler_module[len("devctl."):]
        else:
            suffix = handler_module
        handler_path = "dev/scripts/devctl/" + suffix.replace(".", "/") + ".py"
        init_path = handler_path.replace(".py", "/__init__.py")
        if f"src:{init_path}" in node_ids and f"src:{handler_path}" not in node_ids:
            handler_path = init_path
        node_id = f"cmd:{cmd_name}"
        nodes.append(
            GraphNode(
                node_id=node_id,
                node_kind=NODE_KIND_COMMAND,
                label=cmd_name,
                canonical_pointer_ref=f"devctl {cmd_name}",
                provenance_ref="cli.COMMAND_HANDLERS",
                temperature=0.05,
                metadata={
                    "aliases": [normalized, cmd_name],
                    "handler_module": handler_module,
                },
            )
        )
        src_nid = f"src:{handler_path}"
        if src_nid in node_ids:
            edges.append(
                GraphEdge(
                    source_id=node_id,
                    target_id=src_nid,
                    edge_kind=EDGE_KIND_ROUTES_TO,
                )
            )
    return nodes, edges


def collect_capability_nodes(
    node_ids: set[str],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Build capability nodes from the SystemCatalog for discoverability.

    Surface and bootstrap-command entries become capability nodes. Guard,
    probe, plan, and command nodes are already in the graph from their own
    collectors, so this adds the catalog-backed discoverability layer and
    related typed edges.
    """
    try:
        from ..governance.system_catalog import build_system_catalog
        catalog = build_system_catalog()
    # broad-except: allow reason=SystemCatalog may fail on partial repos or missing policy files fallback=return empty capability nodes gracefully.
    except Exception:
        return [], []

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    for surface in catalog.surfaces:
        nid = f"capability:{surface.surface_id}"
        nodes.append(
            GraphNode(
                node_id=nid,
                node_kind=NODE_KIND_CAPABILITY,
                label=surface.surface_id,
                canonical_pointer_ref=f"surface:{surface.surface_id}",
                provenance_ref="system_catalog.surfaces",
                temperature=0.05,
                metadata={
                    "capability_kind": "surface",
                    "authority": surface.authority,
                    "consumes_contracts": list(surface.consumes_contracts),
                },
            )
        )
    surface_node_ids = {f"capability:{surface.surface_id}" for surface in catalog.surfaces}
    all_node_ids = set(node_ids) | surface_node_ids
    for entry in catalog.bootstrap_commands:
        nid = f"capability:{entry.command_id}"
        nodes.append(
            GraphNode(
                node_id=nid,
                node_kind=NODE_KIND_CAPABILITY,
                label=entry.label,
                canonical_pointer_ref=f"bootstrap_command:{entry.command_id}",
                provenance_ref="system_catalog.bootstrap_commands",
                temperature=0.05,
                metadata=_bootstrap_command_metadata(entry),
            )
        )
        for command_name in entry.command_names:
            target_id = f"cmd:{command_name}"
            if target_id in all_node_ids:
                edges.append(
                    GraphEdge(
                        source_id=nid,
                        target_id=target_id,
                        edge_kind=EDGE_KIND_ROUTES_TO,
                    )
                )
        for guard_id in entry.guard_ids:
            target_id = f"guard:{guard_id}"
            if target_id in all_node_ids:
                edges.append(
                    GraphEdge(
                        source_id=nid,
                        target_id=target_id,
                        edge_kind=EDGE_KIND_RELATED_TO,
                    )
                )
        for probe_id in entry.probe_ids:
            target_id = f"probe:{probe_id}"
            if target_id in all_node_ids:
                edges.append(
                    GraphEdge(
                        source_id=nid,
                        target_id=target_id,
                        edge_kind=EDGE_KIND_RELATED_TO,
                    )
                )
        for surface_id in entry.surface_ids:
            target_id = f"capability:{surface_id}"
            if target_id in all_node_ids:
                edges.append(
                    GraphEdge(
                        source_id=nid,
                        target_id=target_id,
                        edge_kind=EDGE_KIND_RELATED_TO,
                    )
                )
        for plan_path in entry.plan_paths:
            target_id = f"plan:{plan_path}"
            if target_id in all_node_ids:
                edges.append(
                    GraphEdge(
                        source_id=nid,
                        target_id=target_id,
                        edge_kind=EDGE_KIND_RELATED_TO,
                    )
                )
    return nodes, edges
