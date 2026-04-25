"""Policy-backed active-plan scope edges for context graph."""

from __future__ import annotations

from collections import defaultdict

from ..commands.docs.policy_runtime import resolve_docs_check_policy
from .models import EDGE_KIND_SCOPED_BY, GraphEdge, GraphNode


def collect_plan_scope_edges(
    source_nodes: list[GraphNode],
    plan_nodes: list[GraphNode],
) -> list[GraphEdge]:
    """Emit policy-backed active-plan->source scoped_by edges.

    Only uses explicit docs-policy trigger prefixes. Keyword/word-overlap
    heuristics are deliberately excluded: scoped_by is a typed ownership
    edge, and the MP-377 contract requires registry-backed authority, not
    filename guessing.
    """
    policy_prefixes = _plan_scope_rule_prefixes()
    edge_keys: set[tuple[str, str]] = set()
    for plan_node in plan_nodes:
        prefixes = list(policy_prefixes.get(plan_node.canonical_pointer_ref, ()))
        if not prefixes:
            continue
        for source_node in source_nodes:
            ref = source_node.canonical_pointer_ref
            if any(_matches_repo_prefix(ref, prefix) for prefix in prefixes):
                edge_keys.add((plan_node.node_id, source_node.node_id))

    return [
        GraphEdge(source_id=source_id, target_id=target_id, edge_kind=EDGE_KIND_SCOPED_BY)
        for source_id, target_id in sorted(edge_keys)
    ]


def _plan_scope_rule_prefixes() -> dict[str, tuple[str, ...]]:
    """Return docs-policy trigger prefixes keyed by required active-plan doc."""
    policy = resolve_docs_check_policy()
    prefixes_by_doc: dict[str, list[str]] = defaultdict(list)
    for rule in policy.tooling_doc_requirement_rules:
        candidate_prefixes = (*rule.trigger_prefixes, *sorted(rule.trigger_exact_paths))
        for required_doc in rule.required_docs:
            bucket = prefixes_by_doc[required_doc]
            for raw_prefix in candidate_prefixes:
                prefix = str(raw_prefix).replace("\\", "/").strip().strip("/")
                if not prefix or prefix in bucket:
                    continue
                bucket.append(prefix)
    return {doc: tuple(prefixes) for doc, prefixes in prefixes_by_doc.items()}


def _matches_repo_prefix(rel_path: str, prefix: str) -> bool:
    normalized = prefix.strip().strip("/")
    if not normalized or normalized == ".":
        return True
    return rel_path == normalized or rel_path.startswith(f"{normalized}/")
