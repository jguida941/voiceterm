"""Repo-owned mutation-bypass proof over the bounded codeshape graph."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..config import get_repo_root
from ..context_graph.codeshape import (
    DEFAULT_CODESHAPE_SCOPE_PATHS,
    build_codeshape_subgraph,
)
from ..context_graph.models import EDGE_KIND_CALLS, EDGE_KIND_CONTAINS, NODE_KIND_MUTATION_CALLSITE
from ..context_graph.traversal import contains_parents, edge_adjacency, shortest_paths

GOVERNED_ANCHOR_POINTER = (
    "dev/scripts/devctl/commands/vcs/governed_executor.py::GovernedVcsExecutor.execute"
)
DEFAULT_ENTRYPOINT_POINTERS = (
    "dev/scripts/devctl/commands/vcs/commit.py::run_commit",
    "dev/scripts/devctl/commands/vcs/push.py::run_push_action",
    GOVERNED_ANCHOR_POINTER,
)
DEFAULT_PROOF_ARTIFACT = "dev/reports/governance/mutation_bypass_proof.json"
HOOK_SCOPE_PATHS = (
    "dev/config/git_hooks/pre-commit-review-snapshot.sh",
    "dev/config/git_hooks/pre-push-governed-push.sh",
)
TEST_HELPER_SCOPE_PATHS = (
    "dev/scripts/devctl/tests/vcs/_git_helpers.py",
)

_HOOK_MUTATION_PATTERN = re.compile(r"\bgit\s+(add|commit|push|tag|reset|rebase|stash)\b")
_TEST_HELPER_PATTERN = re.compile(r"\[\s*[\"']git[\"']\s*,\s*\*args")


def build_report(
    *,
    repo_root: Path | None = None,
    proof_output_path: Path | None = None,
    entrypoint_pointers: tuple[str, ...] = DEFAULT_ENTRYPOINT_POINTERS,
    governed_anchor_pointer: str = GOVERNED_ANCHOR_POINTER,
    scope_paths: tuple[str, ...] = DEFAULT_CODESHAPE_SCOPE_PATHS,
) -> dict[str, object]:
    """Build and persist the current mutation-bypass proof report."""
    effective_repo_root = (repo_root or get_repo_root()).resolve()
    codeshape_graph = build_codeshape_subgraph(
        repo_root=effective_repo_root,
        scope_paths=scope_paths,
    )
    return build_report_from_codeshape_graph(
        codeshape_graph=codeshape_graph,
        repo_root=effective_repo_root,
        proof_output_path=proof_output_path,
        entrypoint_pointers=entrypoint_pointers,
        governed_anchor_pointer=governed_anchor_pointer,
        scope_paths=scope_paths,
    )


def build_report_from_codeshape_graph(
    *,
    codeshape_graph,
    repo_root: Path,
    proof_output_path: Path | None = None,
    entrypoint_pointers: tuple[str, ...] = DEFAULT_ENTRYPOINT_POINTERS,
    governed_anchor_pointer: str = GOVERNED_ANCHOR_POINTER,
    scope_paths: tuple[str, ...] = DEFAULT_CODESHAPE_SCOPE_PATHS,
) -> dict[str, object]:
    """Build a mutation-bypass proof from one prebuilt codeshape graph."""
    node_by_id = {node.node_id: node for node in codeshape_graph.nodes}
    node_by_pointer = {
        node.canonical_pointer_ref: node
        for node in codeshape_graph.nodes
    }
    calls_adjacency = edge_adjacency(
        codeshape_graph.edges,
        edge_kind=EDGE_KIND_CALLS,
    )
    callsite_parents = contains_parents(
        codeshape_graph.edges,
        child_prefix="mutation:",
    )

    entrypoint_ids = {
        pointer: node_by_pointer[pointer].node_id
        for pointer in entrypoint_pointers
        if pointer in node_by_pointer
    }
    reachable_paths = {
        pointer: shortest_paths(entry_id, calls_adjacency)
        for pointer, entry_id in entrypoint_ids.items()
    }
    anchor_node_id = entrypoint_ids.get(governed_anchor_pointer, "")

    mutation_callsites: list[dict[str, object]] = []
    bypasses: list[dict[str, object]] = []
    for node in codeshape_graph.nodes:
        if node.node_kind != NODE_KIND_MUTATION_CALLSITE:
            continue
        parent_id = callsite_parents.get(node.node_id, "")
        if not parent_id:
            continue
        callsite = _render_callsite(
            node,
            parent_id=parent_id,
            node_by_id=node_by_id,
            entrypoint_paths=reachable_paths,
            anchor_node_id=anchor_node_id,
        )
        mutation_callsites.append(callsite)
        if callsite["classification"] == "ungoverned":
            bypasses.append(callsite)

    classified_debt = {
        "hook_owned": _scan_hook_mutations(repo_root),
        "test_helpers": _scan_test_helper_mutations(repo_root),
    }
    report: dict[str, object] = {
        "command": "check_mutation_bypass_graph_closure",
        "ok": not bypasses and not codeshape_graph.parse_errors,
        "repo_root": str(repo_root),
        "scope_paths": list(scope_paths),
        "entrypoints": list(entrypoint_pointers),
    }
    report["governed_anchor"] = governed_anchor_pointer
    report["node_count"] = len(codeshape_graph.nodes)
    report["edge_count"] = len(codeshape_graph.edges)
    report["parse_errors"] = list(codeshape_graph.parse_errors)
    report["mutation_callsites"] = mutation_callsites
    report["bypasses"] = bypasses
    report["classified_debt"] = classified_debt

    output_path = proof_output_path or (repo_root / DEFAULT_PROOF_ARTIFACT)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report["proof_artifact"] = _relative_path(output_path, repo_root)
    return report


def _render_callsite(
    node,
    *,
    parent_id: str,
    node_by_id: dict[str, object],
    entrypoint_paths: dict[str, dict[str, tuple[str, ...]]],
    anchor_node_id: str,
) -> dict[str, object]:
    parent_node = node_by_id[parent_id]
    paths = []
    for entrypoint_pointer, reachable in entrypoint_paths.items():
        function_path = reachable.get(parent_id)
        if function_path is None:
            continue
        paths.append(
            {
                "entrypoint": entrypoint_pointer,
                "path": [
                    node_by_id[node_id].canonical_pointer_ref
                    for node_id in function_path
                ],
                "includes_governed_anchor": bool(anchor_node_id and anchor_node_id in function_path),
            }
        )
    classification = "governed"
    if paths and any(not path["includes_governed_anchor"] for path in paths):
        classification = "ungoverned"
    elif not paths:
        classification = "unreachable"
    metadata = node.metadata
    return _build_callsite_payload(
        metadata=metadata,
        containing_function=parent_node.canonical_pointer_ref,
        classification=classification,
        reachable_entrypoints=paths,
    )


def _scan_hook_mutations(repo_root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for rel_path in HOOK_SCOPE_PATHS:
        path = repo_root / rel_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = _HOOK_MUTATION_PATTERN.search(line)
            if match is None:
                continue
            findings.append(
                {
                    "path": rel_path,
                    "line": line_number,
                    "git_verb": match.group(1),
                    "classification": "hook_owned",
                    "command_literal": line.strip(),
                }
            )
    return findings


def _scan_test_helper_mutations(repo_root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for rel_path in TEST_HELPER_SCOPE_PATHS:
        path = repo_root / rel_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if _TEST_HELPER_PATTERN.search(line) is None:
                continue
            findings.append(
                {
                    "path": rel_path,
                    "line": line_number,
                    "git_verb": "dynamic",
                    "classification": "test_helper",
                    "command_literal": line.strip(),
                }
            )
    return findings


def _relative_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def _build_callsite_payload(
    *,
    metadata: dict[str, object],
    containing_function: str,
    classification: str,
    reachable_entrypoints: list[dict[str, object]],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "path": metadata.get("path", ""),
        "qualname": metadata.get("qualname", ""),
        "line": metadata.get("line", 0),
        "column": metadata.get("column", 0),
        "git_verb": metadata.get("git_verb", ""),
    }
    payload["command_source"] = metadata.get("command_source", "")
    payload["command_literal"] = metadata.get("command_literal", "")
    payload["containing_function"] = containing_function
    payload["classification"] = classification
    payload["reachable_entrypoints"] = reachable_entrypoints
    return payload
