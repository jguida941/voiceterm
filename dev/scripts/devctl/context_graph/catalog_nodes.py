"""Supporting node collectors for context-graph construction."""

from __future__ import annotations

import importlib
from pathlib import Path

from ..governance.doc_authority_rules import parse_index_registry
from .models import (
    EDGE_KIND_ROUTES_TO,
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
                metadata={
                    "role": role,
                    "authority": row.get("authority", ""),
                    "scope": scope_raw.replace("`", "").strip().strip(",").strip(),
                    "is_active_plan": is_active_plan,
                },
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
