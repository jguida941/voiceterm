"""Operational evidence nodes for the generated context graph.

This module widens the existing graph read model over typed authority sources.
It does not own packet, plan, finding, receipt, workflow, config, test, or
contract truth; each node points back to its canonical artifact/provenance.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..platform.planning_ir_plan_content import parse_execution_plan_phases
from ..repo_packs import active_path_config
from ..runtime.governance_scan import scan_repo_governance_safely
from .models import (
    EDGE_KIND_COMMAND_INVOKES,
    EDGE_KIND_CONTAINS,
    EDGE_KIND_CONTRACT_READS,
    EDGE_KIND_CONTRACT_WRITES,
    EDGE_KIND_FINDING_BLOCKS,
    EDGE_KIND_GUARD_CATCHES,
    EDGE_KIND_PACKET_HANDOFF,
    EDGE_KIND_PROBE_FINDS,
    EDGE_KIND_RECEIPT_PROVES,
    EDGE_KIND_RELATED_TO,
    EDGE_KIND_ROUTES_TO,
    EDGE_KIND_SCOPED_BY,
    EDGE_KIND_TEST_COVERS,
    EDGE_KIND_WORKFLOW_RUNS,
    NODE_KIND_AGENT,
    NODE_KIND_CAPABILITY,
    NODE_KIND_COMMAND,
    NODE_KIND_CONFIG,
    NODE_KIND_FINDING,
    NODE_KIND_GUARD,
    NODE_KIND_HANDOFF,
    NODE_KIND_INTENT,
    NODE_KIND_PACKET,
    NODE_KIND_PLAN,
    NODE_KIND_PLAN_ROW,
    NODE_KIND_PROBE,
    NODE_KIND_RECEIPT,
    NODE_KIND_SOURCE,
    NODE_KIND_TEST,
    NODE_KIND_WORKFLOW,
    GraphEdge,
    GraphNode,
)

_MP_TOKEN_RE = re.compile(r"\bMP-?\d+(?:-[A-Z0-9]+)*\b", re.IGNORECASE)
_DEVCTL_COMMAND_RE = re.compile(r"\bdevctl(?:\.py)?\s+([a-z0-9][a-z0-9_-]*)\b")
_REQUESTED_ACTION_COMMANDS = {
    "commit": "commit",
    "push": "push",
    "run_check": "check",
    "stage_commit_pipeline": "commit",
}
_INTENT_COMMAND_MAP: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("heartbeat", ("review-channel", "monitor", "claude-loop")),
    ("live-stream", ("dashboard", "claude-loop", "monitor")),
    ("post-edit-validation", ("check", "check-router", "docs-check", "probe-report")),
    ("dogfood-record", ("dogfood", "governance-review")),
    ("packet-handoff", ("review-channel", "commit")),
    ("graph-navigation", ("context-graph", "graph-walk")),
)
_TEST_FILE_LIMIT = 240
_CONFIG_FILE_LIMIT = 160
_DOGFOOD_ROW_LIMIT = 250
_PACKET_ROW_LIMIT = 400
_HANDOFF_ROW_LIMIT = 120


def collect_operational_nodes(
    repo_root: Path,
    existing_nodes: list[GraphNode],
    existing_edges: list[GraphEdge],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Collect generated graph nodes over existing typed operational evidence."""
    node_by_id = {node.node_id: node for node in existing_nodes}
    edge_keys = {
        (edge.source_id, edge.target_id, edge.edge_kind)
        for edge in existing_edges
    }
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    plan_rows, plan_edges, file_to_plan_rows = _collect_plan_row_nodes(
        repo_root=repo_root,
        existing_nodes=existing_nodes,
    )
    _extend_graph(nodes, edges, plan_rows, plan_edges, node_by_id, edge_keys)

    artifact_nodes, artifact_edges = _collect_static_artifact_nodes(
        repo_root=repo_root,
        node_by_id=node_by_id,
    )
    _extend_graph(nodes, edges, artifact_nodes, artifact_edges, node_by_id, edge_keys)

    intent_nodes, intent_edges = _collect_intent_nodes(node_by_id)
    _extend_graph(nodes, edges, intent_nodes, intent_edges, node_by_id, edge_keys)

    finding_nodes, finding_edges = _collect_finding_nodes(
        repo_root=repo_root,
        node_by_id=node_by_id,
        file_to_plan_rows=file_to_plan_rows,
    )
    _extend_graph(nodes, edges, finding_nodes, finding_edges, node_by_id, edge_keys)

    receipt_nodes, receipt_edges = _collect_dogfood_receipt_nodes(
        repo_root=repo_root,
        node_by_id=node_by_id,
    )
    _extend_graph(nodes, edges, receipt_nodes, receipt_edges, node_by_id, edge_keys)

    packet_nodes, packet_edges = _collect_review_state_nodes(
        repo_root=repo_root,
        node_by_id=node_by_id,
    )
    _extend_graph(nodes, edges, packet_nodes, packet_edges, node_by_id, edge_keys)

    semantic_edges = _collect_contract_semantic_edges(node_by_id)
    _extend_graph(nodes, edges, [], semantic_edges, node_by_id, edge_keys)
    return nodes, edges


def _collect_plan_row_nodes(
    *,
    repo_root: Path,
    existing_nodes: list[GraphNode],
) -> tuple[list[GraphNode], list[GraphEdge], dict[str, list[str]]]:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    row_node_by_id: dict[str, str] = {}
    file_to_plan_rows: dict[str, list[str]] = {}
    plan_nodes = [node for node in existing_nodes if node.node_kind == NODE_KIND_PLAN]
    plan_node_ids = {node.node_id for node in plan_nodes}

    for plan_node in plan_nodes:
        plan_ref = plan_node.canonical_pointer_ref
        plan_path = repo_root / plan_ref
        if not plan_path.is_file():
            continue
        try:
            phases = parse_execution_plan_phases(plan_path.read_text(encoding="utf-8"))
        except OSError:
            continue
        for phase in phases:
            phase_key = phase.phase_id or _stable_key(phase.title)
            phase_node_id = _plan_row_node_id(plan_ref, "phase", phase_key)
            row_node_by_id[phase.phase_id] = phase_node_id
            nodes.append(
                GraphNode(
                    node_id=phase_node_id,
                    node_kind=NODE_KIND_PLAN_ROW,
                    label=phase.phase_id or phase.title,
                    canonical_pointer_ref=f"{plan_ref}#{phase.anchor_ref or phase_key}",
                    provenance_ref="planning_ir_plan_content",
                    temperature=_status_temperature(phase.status),
                    metadata={
                        "row_kind": "phase",
                        "plan_path": plan_ref,
                        "phase_id": phase.phase_id,
                        "title": phase.title,
                        "summary": phase.summary,
                        "owner_doc": phase.owner_doc,
                        "status": phase.status,
                        "dependencies": [item.dependency_id for item in phase.dependencies],
                        "aliases": _plan_row_aliases(phase.phase_id, phase.title, phase.summary),
                    },
                )
            )
            if plan_node.node_id in plan_node_ids:
                edges.append(GraphEdge(plan_node.node_id, phase_node_id, EDGE_KIND_CONTAINS))
            _append_owner_doc_edge(
                edges,
                source_id=phase_node_id,
                owner_doc=phase.owner_doc,
                known_node_ids={node.node_id for node in existing_nodes},
            )

            for task in phase.tasks:
                task_node_id = _plan_row_node_id(plan_ref, "task", task.task_id)
                row_node_by_id[task.task_id] = task_node_id
                nodes.append(
                    GraphNode(
                        node_id=task_node_id,
                        node_kind=NODE_KIND_PLAN_ROW,
                        label=task.task_id,
                        canonical_pointer_ref=f"{plan_ref}#{task.anchor_ref or task.task_id}",
                        provenance_ref="planning_ir_plan_content",
                        temperature=_status_temperature(task.status),
                        metadata={
                            "row_kind": "task",
                            "plan_path": plan_ref,
                            "phase_id": task.phase_id,
                            "phase_title": task.phase_title,
                            "task_id": task.task_id,
                            "summary": task.summary,
                            "owner_doc": task.owner_doc,
                            "status": task.status,
                            "dependencies": [
                                item.dependency_id for item in task.dependencies
                            ],
                            "aliases": _plan_row_aliases(
                                task.task_id,
                                task.phase_id,
                                task.summary,
                                task.owner_doc,
                            ),
                        },
                    )
                )
                edges.append(GraphEdge(phase_node_id, task_node_id, EDGE_KIND_CONTAINS))
                if plan_node.node_id in plan_node_ids:
                    edges.append(GraphEdge(plan_node.node_id, task_node_id, EDGE_KIND_CONTAINS))
                _append_owner_doc_edge(
                    edges,
                    source_id=task_node_id,
                    owner_doc=task.owner_doc,
                    known_node_ids={node.node_id for node in existing_nodes},
                )
                if task.owner_doc:
                    file_to_plan_rows.setdefault(_normalize_rel(task.owner_doc), []).append(
                        task_node_id
                    )

    for node in nodes:
        dependencies = node.metadata.get("dependencies")
        if not isinstance(dependencies, list):
            continue
        for raw_dependency in dependencies:
            dependency_id = str(raw_dependency).strip()
            target_id = row_node_by_id.get(dependency_id)
            if target_id:
                edges.append(GraphEdge(node.node_id, target_id, EDGE_KIND_RELATED_TO))
    return nodes, edges, file_to_plan_rows


def _append_owner_doc_edge(
    edges: list[GraphEdge],
    *,
    source_id: str,
    owner_doc: str,
    known_node_ids: set[str],
) -> None:
    owner = _normalize_rel(owner_doc)
    if not owner:
        return
    plan_id = f"plan:{owner}"
    source_file_id = f"src:{owner}"
    if plan_id in known_node_ids:
        edges.append(GraphEdge(source_id, plan_id, EDGE_KIND_SCOPED_BY))
    elif source_file_id in known_node_ids:
        edges.append(GraphEdge(source_id, source_file_id, EDGE_KIND_SCOPED_BY))


def _collect_static_artifact_nodes(
    *,
    repo_root: Path,
    node_by_id: dict[str, GraphNode],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    governance = scan_repo_governance_safely(repo_root)
    path_roots = governance.path_roots if governance is not None else None
    workflow_root = Path(getattr(path_roots, "workflows", ".github/workflows"))
    config_root = Path(getattr(path_roots, "config", "dev/config"))
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    for workflow_path in _iter_existing_files(
        repo_root / workflow_root,
        suffixes=(".yml", ".yaml"),
    ):
        rel = workflow_path.relative_to(repo_root).as_posix()
        node_id = f"workflow:{rel}"
        nodes.append(
            GraphNode(
                node_id=node_id,
                node_kind=NODE_KIND_WORKFLOW,
                label=workflow_path.name,
                canonical_pointer_ref=rel,
                provenance_ref="ProjectGovernance.path_roots.workflows",
                temperature=0.12,
                metadata={"aliases": [workflow_path.stem, rel]},
            )
        )
        for command_name in _commands_mentioned_by_file(workflow_path):
            command_id = f"cmd:{command_name}"
            if command_id in node_by_id:
                edges.append(GraphEdge(node_id, command_id, EDGE_KIND_WORKFLOW_RUNS))
                edges.append(GraphEdge(command_id, node_id, EDGE_KIND_COMMAND_INVOKES))

    for config_path in _iter_existing_files(
        repo_root / config_root,
        suffixes=(".json", ".toml", ".yaml", ".yml"),
        limit=_CONFIG_FILE_LIMIT,
    ):
        rel = config_path.relative_to(repo_root).as_posix()
        nodes.append(
            GraphNode(
                node_id=f"config:{rel}",
                node_kind=NODE_KIND_CONFIG,
                label=config_path.name,
                canonical_pointer_ref=rel,
                provenance_ref="ProjectGovernance.path_roots.config",
                temperature=0.06,
                metadata={"aliases": [config_path.stem, rel]},
            )
        )

    test_root = repo_root / "dev" / "scripts" / "devctl" / "tests"
    for test_path in _iter_existing_files(
        test_root,
        suffixes=(".py",),
        limit=_TEST_FILE_LIMIT,
    ):
        rel = test_path.relative_to(repo_root).as_posix()
        node_id = f"test:{rel}"
        nodes.append(
            GraphNode(
                node_id=node_id,
                node_kind=NODE_KIND_TEST,
                label=test_path.name,
                canonical_pointer_ref=rel,
                provenance_ref="devctl_test_inventory",
                temperature=0.08,
                metadata={"aliases": _test_aliases(test_path, rel)},
            )
        )
        edges.extend(_test_cover_edges(node_id, test_path, rel, node_by_id))
    return nodes, edges


def _collect_intent_nodes(
    node_by_id: dict[str, GraphNode],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Build generated concept anchors for common AI navigation intents."""
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    for intent_id, command_names in _INTENT_COMMAND_MAP:
        existing_commands = [
            command_name for command_name in command_names
            if f"cmd:{command_name}" in node_by_id
        ]
        if not existing_commands:
            continue
        node_id = f"concept:intent:{intent_id}"
        nodes.append(
            GraphNode(
                node_id=node_id,
                node_kind=NODE_KIND_INTENT,
                label=intent_id,
                canonical_pointer_ref=f"intent:{intent_id}",
                provenance_ref="context_graph.intent_seed",
                temperature=0.14,
                metadata={
                    "aliases": [
                        intent_id,
                        intent_id.replace("-", " "),
                        f"concept:{intent_id}",
                    ],
                    "generated_navigation_only": True,
                    "command_names": list(existing_commands),
                },
            )
        )
        for command_name in existing_commands:
            edges.append(GraphEdge(node_id, f"cmd:{command_name}", EDGE_KIND_ROUTES_TO))
    return nodes, edges


def _collect_finding_nodes(
    *,
    repo_root: Path,
    node_by_id: dict[str, GraphNode],
    file_to_plan_rows: dict[str, list[str]],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    path_config = active_path_config()
    finding_log_path = repo_root / path_config.governance_review_log_rel
    latest_by_id: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl_rows(finding_log_path):
        finding_id = str(row.get("finding_id") or "").strip()
        if finding_id:
            latest_by_id[finding_id] = row

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    for finding_id, row in sorted(latest_by_id.items()):
        file_path = _normalize_rel(row.get("file_path"))
        check_id = str(row.get("check_id") or "").strip()
        node_id = f"finding:{finding_id}"
        nodes.append(
            GraphNode(
                node_id=node_id,
                node_kind=NODE_KIND_FINDING,
                label=finding_id,
                canonical_pointer_ref=f"{path_config.governance_review_log_rel}#{finding_id}",
                provenance_ref="FindingReview",
                temperature=_finding_temperature(row),
                metadata={
                    "finding_id": finding_id,
                    "check_id": check_id,
                    "file_path": file_path,
                    "verdict": row.get("verdict", ""),
                    "signal_type": row.get("signal_type", ""),
                    "finding_class": row.get("finding_class", ""),
                    "prevention_surface": row.get("prevention_surface", ""),
                    "recurrence_risk": row.get("recurrence_risk", ""),
                    "aliases": [finding_id, check_id, file_path],
                },
            )
        )
        source_id = f"src:{file_path}"
        if file_path and source_id in node_by_id:
            edges.append(GraphEdge(node_id, source_id, EDGE_KIND_RELATED_TO))
        detector_id, detector_edge_kind = _detector_edge(check_id, row, node_by_id)
        if detector_id:
            edges.append(GraphEdge(detector_id, node_id, detector_edge_kind))
        for plan_row_id in file_to_plan_rows.get(file_path, ()):
            edges.append(GraphEdge(node_id, plan_row_id, EDGE_KIND_FINDING_BLOCKS))
    return nodes, edges


def _collect_dogfood_receipt_nodes(
    *,
    repo_root: Path,
    node_by_id: dict[str, GraphNode],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    path_config = active_path_config()
    dogfood_log_path = repo_root / path_config.dogfood_log_rel
    rows = _read_jsonl_rows(dogfood_log_path)[-_DOGFOOD_ROW_LIMIT:]
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    for row in rows:
        record_id = str(row.get("record_id") or "").strip()
        if not record_id:
            continue
        target_kind = str(row.get("target_kind") or "").strip()
        target_id = str(row.get("target_id") or "").strip()
        node_id = f"receipt:dogfood:{record_id}"
        nodes.append(
            GraphNode(
                node_id=node_id,
                node_kind=NODE_KIND_RECEIPT,
                label=record_id,
                canonical_pointer_ref=f"{path_config.dogfood_log_rel}#{record_id}",
                provenance_ref="DogfoodRun",
                temperature=_receipt_temperature(row),
                metadata={
                    "receipt_kind": "dogfood_run",
                    "target_kind": target_kind,
                    "target_id": target_id,
                    "status": row.get("status", ""),
                    "timestamp_utc": row.get("timestamp_utc", ""),
                    "source_command": row.get("source_command", ""),
                    "aliases": [record_id, target_id, str(row.get("source_command") or "")],
                },
            )
        )
        target_node_id = _target_node_id(target_kind, target_id)
        if target_node_id in node_by_id:
            edges.append(GraphEdge(node_id, target_node_id, EDGE_KIND_RECEIPT_PROVES))
        command_name = _command_from_source_command(row.get("source_command"))
        if command_name:
            command_id = f"cmd:{command_name}"
            if command_id in node_by_id:
                edges.append(GraphEdge(command_id, node_id, EDGE_KIND_COMMAND_INVOKES))
        for finding_id in _string_list(row.get("governance_finding_ids")):
            edges.append(GraphEdge(node_id, f"finding:{finding_id}", EDGE_KIND_RECEIPT_PROVES))
    return nodes, edges


def _collect_review_state_nodes(
    *,
    repo_root: Path,
    node_by_id: dict[str, GraphNode],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    path_config = active_path_config()
    review_state_path = repo_root / path_config.review_state_json_rel
    payload = _load_json(review_state_path)
    if not isinstance(payload, dict):
        return [], []
    packet_rows, handoff_rows = _collect_packet_rows(payload)
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    agent_ids = sorted(
        {
            agent
            for row in (*packet_rows, *handoff_rows)
            for agent in (
                str(row.get("from_agent") or "").strip(),
                str(row.get("to_agent") or "").strip(),
            )
            if agent
        }
    )
    for agent_id in agent_ids:
        nodes.append(
            GraphNode(
                node_id=f"agent:{agent_id}",
                node_kind=NODE_KIND_AGENT,
                label=agent_id,
                canonical_pointer_ref=f"ReviewState.agent:{agent_id}",
                provenance_ref="ReviewState",
                temperature=0.05,
                metadata={"capability_kind": "agent", "aliases": [agent_id]},
            )
        )
    for row in packet_rows:
        packet_id = str(row.get("packet_id") or "").strip()
        if not packet_id:
            continue
        node_id = f"packet:{packet_id}"
        nodes.append(_packet_node(node_id=node_id, packet_id=packet_id, row=row))
        _append_packet_edges(edges, node_id=node_id, row=row, node_by_id=node_by_id)
    packet_node_ids = {node.node_id for node in nodes if node.node_kind == NODE_KIND_PACKET}
    for row in handoff_rows:
        packet_id = str(row.get("handoff_packet_id") or "").strip()
        if not packet_id:
            continue
        node_id = f"handoff:{packet_id}"
        nodes.append(
            GraphNode(
                node_id=node_id,
                node_kind=NODE_KIND_HANDOFF,
                label=packet_id,
                canonical_pointer_ref=f"{path_config.review_state_json_rel}#handoff:{packet_id}",
                provenance_ref="ReviewState.session_outcomes",
                temperature=0.18,
                metadata={
                    "packet_id": packet_id,
                    "requested_action": row.get("handoff_requested_action", ""),
                    "outcome": row.get("outcome", ""),
                    "provider": row.get("provider", ""),
                    "session_id": row.get("session_id", ""),
                    "aliases": [packet_id, str(row.get("handoff_requested_action") or "")],
                },
            )
        )
        packet_node_id = f"packet:{packet_id}"
        if packet_node_id in packet_node_ids:
            edges.append(GraphEdge(node_id, packet_node_id, EDGE_KIND_PACKET_HANDOFF))
    return nodes, edges


def _packet_node(*, node_id: str, packet_id: str, row: Mapping[str, Any]) -> GraphNode:
    path_config = active_path_config()
    return GraphNode(
        node_id=node_id,
        node_kind=NODE_KIND_PACKET,
        label=packet_id,
        canonical_pointer_ref=f"{path_config.review_state_json_rel}#packet:{packet_id}",
        provenance_ref="ReviewState.packets",
        temperature=_packet_temperature(row),
        metadata={
            "packet_id": packet_id,
            "kind": row.get("kind", ""),
            "from_agent": row.get("from_agent", ""),
            "to_agent": row.get("to_agent", ""),
            "requested_action": row.get("requested_action", ""),
            "summary": row.get("summary", ""),
            "lifecycle_current_state": row.get("lifecycle_current_state", ""),
            "status": row.get("status", ""),
            "aliases": [
                packet_id,
                str(row.get("kind") or ""),
                str(row.get("requested_action") or ""),
                str(row.get("summary") or ""),
            ],
        },
    )


def _append_packet_edges(
    edges: list[GraphEdge],
    *,
    node_id: str,
    row: Mapping[str, Any],
    node_by_id: dict[str, GraphNode],
) -> None:
    to_agent = str(row.get("to_agent") or "").strip()
    if to_agent:
        edges.append(GraphEdge(node_id, f"agent:{to_agent}", EDGE_KIND_PACKET_HANDOFF))
    from_agent = str(row.get("from_agent") or "").strip()
    if from_agent:
        edges.append(GraphEdge(f"agent:{from_agent}", node_id, EDGE_KIND_PACKET_HANDOFF))
    requested_action = str(row.get("requested_action") or "").strip()
    command_name = _REQUESTED_ACTION_COMMANDS.get(
        requested_action,
        requested_action.replace("_", "-"),
    )
    command_id = f"cmd:{command_name}"
    if command_name and command_id in node_by_id:
        edges.append(GraphEdge(node_id, command_id, EDGE_KIND_ROUTES_TO))


def _collect_contract_semantic_edges(
    node_by_id: dict[str, GraphNode],
) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    for node in node_by_id.values():
        if node.node_kind not in {"typed_contract", "dataclass_field"}:
            continue
        metadata = node.metadata if isinstance(node.metadata, dict) else {}
        source_path = _normalize_rel(metadata.get("source_path"))
        if source_path and f"src:{source_path}" in node_by_id:
            edges.append(GraphEdge(f"src:{source_path}", node.node_id, EDGE_KIND_CONTRACT_WRITES))
        for reader_id in _string_list(metadata.get("reader_ids")):
            capability_id = f"capability:{reader_id}"
            if capability_id in node_by_id:
                edges.append(GraphEdge(capability_id, node.node_id, EDGE_KIND_CONTRACT_READS))
    return edges


def _collect_packet_rows(payload: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    packet_rows: dict[str, dict[str, Any]] = {}
    handoff_rows: dict[str, dict[str, Any]] = {}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            packet_id = str(value.get("packet_id") or "").strip()
            if packet_id:
                packet_rows[packet_id] = dict(value)
            handoff_packet_id = str(value.get("handoff_packet_id") or "").strip()
            if handoff_packet_id:
                handoff_rows[handoff_packet_id] = dict(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return (
        list(packet_rows.values())[:_PACKET_ROW_LIMIT],
        list(handoff_rows.values())[:_HANDOFF_ROW_LIMIT],
    )


def _detector_edge(
    check_id: str,
    row: Mapping[str, Any],
    node_by_id: dict[str, GraphNode],
) -> tuple[str, str] | tuple[str, str]:
    candidates = _detector_candidates(check_id)
    signal_type = str(row.get("signal_type") or "").lower()
    preferred_kinds = (NODE_KIND_PROBE, NODE_KIND_GUARD)
    if "guard" in signal_type:
        preferred_kinds = (NODE_KIND_GUARD, NODE_KIND_PROBE)
    for kind in preferred_kinds:
        prefix = f"{kind}:"
        for candidate in candidates:
            node_id = f"{prefix}{candidate}"
            if node_id in node_by_id:
                edge_kind = EDGE_KIND_PROBE_FINDS if kind == NODE_KIND_PROBE else EDGE_KIND_GUARD_CATCHES
                return node_id, edge_kind
    return "", ""


def _detector_candidates(check_id: str) -> tuple[str, ...]:
    raw = check_id.strip()
    if not raw:
        return ()
    variants = [raw, raw.replace("-", "_"), raw.replace("_", "-")]
    if raw.startswith("dogfood.command."):
        variants.append(raw.removeprefix("dogfood.command."))
    if raw.endswith("-guard"):
        variants.append(raw[: -len("-guard")])
    if raw.endswith("_guard"):
        variants.append(raw[: -len("_guard")])
    result: list[str] = []
    for variant in variants:
        if variant and variant not in result:
            result.append(variant)
    return tuple(result)


def _target_node_id(target_kind: str, target_id: str) -> str:
    normalized_kind = target_kind.strip().lower()
    if normalized_kind == "command":
        return f"cmd:{target_id}"
    if normalized_kind == "guard":
        return f"guard:{target_id}"
    if normalized_kind == "probe":
        return f"probe:{target_id}"
    return f"{normalized_kind}:{target_id}"


def _test_cover_edges(
    node_id: str,
    test_path: Path,
    rel: str,
    node_by_id: dict[str, GraphNode],
) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    module_name = test_path.stem.removeprefix("test_")
    matching_sources = [
        source.node_id
        for source in node_by_id.values()
        if source.node_kind == NODE_KIND_SOURCE
        and (
            source.canonical_pointer_ref.endswith(f"/{module_name}.py")
            or source.canonical_pointer_ref.endswith(f"/{module_name}/__init__.py")
        )
    ]
    if len(matching_sources) == 1:
        edges.append(GraphEdge(node_id, matching_sources[0], EDGE_KIND_TEST_COVERS))
        return edges
    parts = rel.split("/")
    try:
        package = parts[parts.index("tests") + 1]
    except (ValueError, IndexError):
        return edges
    concept_candidates = (
        f"concept:dev/scripts/devctl/{package}",
        f"concept:dev/scripts/devctl/commands/{package}",
        f"concept:dev/scripts/devctl/runtime/{package}",
    )
    for concept_id in concept_candidates:
        if concept_id in node_by_id:
            edges.append(GraphEdge(node_id, concept_id, EDGE_KIND_TEST_COVERS))
            break
    return edges


def _commands_mentioned_by_file(path: Path) -> tuple[str, ...]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ()
    result: list[str] = []
    for match in _DEVCTL_COMMAND_RE.finditer(text):
        command_name = match.group(1)
        if command_name not in result:
            result.append(command_name)
    return tuple(result)


def _command_from_source_command(value: object) -> str:
    text = str(value or "")
    match = _DEVCTL_COMMAND_RE.search(text)
    return match.group(1) if match is not None else ""


def _iter_existing_files(
    root: Path,
    *,
    suffixes: tuple[str, ...],
    limit: int | None = None,
) -> Iterable[Path]:
    if not root.is_dir():
        return ()
    paths = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix in suffixes
    ]
    return tuple(sorted(paths)[:limit])


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _extend_graph(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    new_nodes: list[GraphNode],
    new_edges: list[GraphEdge],
    node_by_id: dict[str, GraphNode],
    edge_keys: set[tuple[str, str, str]],
) -> None:
    for node in new_nodes:
        if node.node_id in node_by_id:
            continue
        nodes.append(node)
        node_by_id[node.node_id] = node
    for edge in new_edges:
        key = (edge.source_id, edge.target_id, edge.edge_kind)
        if key in edge_keys:
            continue
        if edge.source_id not in node_by_id or edge.target_id not in node_by_id:
            continue
        edges.append(edge)
        edge_keys.add(key)


def _plan_row_node_id(plan_ref: str, row_kind: str, row_id: str) -> str:
    return f"plan_row:{_node_token(plan_ref)}:{row_kind}:{_node_token(row_id)}"


def _node_token(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.:/-]+", "_", str(value).strip()).strip("_")
    if cleaned and len(cleaned) <= 140:
        return cleaned
    prefix = cleaned[:96] if cleaned else "row"
    return f"{prefix}:{_stable_key(value)}"


def _stable_key(value: object) -> str:
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()
    return digest[:12]


def _normalize_rel(value: object) -> str:
    return str(value or "").replace("\\", "/").strip().strip("/")


def _string_list(value: object) -> tuple[str, ...]:
    if isinstance(value, list | tuple):
        return tuple(str(item).strip() for item in value if str(item).strip())
    text = str(value or "").strip()
    return (text,) if text else ()


def _plan_row_aliases(*values: object) -> list[str]:
    aliases: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in aliases:
            aliases.append(text)
        for match in _MP_TOKEN_RE.finditer(text):
            token = match.group(0).upper()
            if token not in aliases:
                aliases.append(token)
    return aliases


def _test_aliases(test_path: Path, rel: str) -> list[str]:
    stem = test_path.stem
    aliases = [stem, stem.removeprefix("test_"), rel]
    return [alias for alias in aliases if alias]


def _status_temperature(status: object) -> float:
    normalized = str(status or "").strip().lower()
    return {
        "in_progress": 0.55,
        "blocked": 0.5,
        "queued": 0.35,
        "pending": 0.3,
        "done": 0.08,
        "complete": 0.08,
    }.get(normalized, 0.18)


def _finding_temperature(row: Mapping[str, Any]) -> float:
    verdict = str(row.get("verdict") or "").lower()
    recurrence = str(row.get("recurrence_risk") or "").lower()
    score = 0.12
    if verdict in {"confirmed_issue", "open"}:
        score += 0.28
    if recurrence == "recurring":
        score += 0.15
    return min(round(score, 3), 1.0)


def _receipt_temperature(row: Mapping[str, Any]) -> float:
    status = str(row.get("status") or "").lower()
    if status == "failed":
        return 0.35
    if status == "blocked":
        return 0.32
    if status == "passed":
        return 0.12
    return 0.18


def _packet_temperature(row: Mapping[str, Any]) -> float:
    state = str(row.get("lifecycle_current_state") or row.get("status") or "").lower()
    kind = str(row.get("kind") or "").lower()
    score = 0.15
    if kind == "action_request":
        score += 0.18
    if state in {"pending", "acknowledged", "execution_pending", "in_progress"}:
        score += 0.18
    if state in {"failed", "blocked"}:
        score += 0.2
    return min(round(score, 3), 1.0)


__all__ = ["collect_operational_nodes"]
