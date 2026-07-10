"""Mixed-concern detection helpers shared by code-shape guard and probe."""

from __future__ import annotations

import ast
from pathlib import Path

CLUSTER_THRESHOLD_MEDIUM = 3
CLUSTER_THRESHOLD_HIGH = 4
MIN_CLUSTER_SIZE = 2
MIN_FUNCTIONS_FOR_CHECK = 6
HUB_THRESHOLD = 3


def find_function_clusters(source: str) -> list[set[str]]:
    """Find independent top-level function-call clusters in Python source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    top_level_funcs: dict[str, set[str]] = {}
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        calls: set[str] = set()
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            if isinstance(child.func, ast.Name):
                calls.add(child.func.id)
            elif isinstance(child.func, ast.Attribute) and isinstance(child.func.value, ast.Name):
                if child.func.value.id == "self":
                    calls.add(child.func.attr)
        top_level_funcs[node.name] = calls

    if len(top_level_funcs) < MIN_FUNCTIONS_FOR_CHECK:
        return []

    func_names = set(top_level_funcs)
    dispatchers = {
        name
        for name, calls in top_level_funcs.items()
        if len(calls & func_names) >= HUB_THRESHOLD
    }

    callee_counts: dict[str, int] = {name: 0 for name in func_names}
    for calls in top_level_funcs.values():
        for called in calls & func_names:
            callee_counts[called] = callee_counts.get(called, 0) + 1
    shared_utilities = {
        name for name, count in callee_counts.items() if count >= HUB_THRESHOLD
    }
    hubs = dispatchers | shared_utilities

    adjacency: dict[str, set[str]] = {name: set() for name in func_names}
    for name, calls in top_level_funcs.items():
        if name in hubs:
            continue
        for called in calls & func_names:
            if called in hubs:
                continue
            adjacency[name].add(called)
            adjacency[called].add(name)

    visited: set[str] = set()
    clusters: list[set[str]] = []
    for name in sorted(func_names):
        if name in visited:
            continue
        cluster: set[str] = set()
        stack = [name]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            cluster.add(current)
            stack.extend(adjacency[current] - visited)
        if len(cluster) >= MIN_CLUSTER_SIZE:
            clusters.append(cluster)

    return clusters


def cluster_signals(clusters: list[set[str]]) -> list[str]:
    """Render short signal previews for the largest detected clusters."""
    signals = [f"{len(clusters)} independent function groups in one file"]
    ordered = sorted(
        clusters,
        key=lambda cluster: (-len(cluster), tuple(sorted(cluster))),
    )
    for index, cluster in enumerate(ordered[:3], start=1):
        preview = ", ".join(sorted(cluster)[:5])
        signals.append(f"cluster {index} ({len(cluster)} funcs): {preview}")
    return signals


def mixed_concern_violation(
    *,
    path: Path,
    clusters: list[set[str]],
    best_practice_docs: dict[str, tuple[str, ...]],
    shape_audit_guidance: str,
) -> dict[str, object]:
    """Build a touched-file guard violation for mixed concerns."""
    docs_refs = list(best_practice_docs.get(path.suffix, ()))
    guidance_parts = [
        (
            f"Touched file still mixes {len(clusters)} independent function groups. "
            "Split each cluster into its own module before merge."
        ),
        shape_audit_guidance,
    ]
    if docs_refs:
        guidance_parts.append("Best-practice refs: " + ", ".join(docs_refs))
    return {
        "path": path.as_posix(),
        "violation_family": "mixed_concerns",
        "reason": "mixed_concerns_on_touched_file",
        "guidance": " ".join(guidance_parts),
        "best_practice_refs": docs_refs,
        "policy_source": "probe_mixed_concerns:touched_file",
        "cluster_count": len(clusters),
        "signals": cluster_signals(clusters),
    }
