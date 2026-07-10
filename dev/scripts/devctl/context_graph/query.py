"""Query and bootstrap surfaces over the built context graph."""

from __future__ import annotations

import subprocess
from typing import Any

from ..config import get_repo_root
from ..governance.push_policy import detect_push_enforcement_state, load_push_policy
from ..runtime.control_plane_sources import artifact_paths, read_json_artifact
from ..runtime.key_surfaces import load_startup_key_surfaces
from ..runtime.review_state_parser import review_state_from_payload
from ..runtime.startup_continuity import (
    startup_continuity_attention,
    startup_packet_continuity_index,
    startup_packet_carry_forward_debt,
    startup_runtime_spine_closure,
)
from .models import (
    NODE_KIND_GUARD,
    NODE_KIND_PLAN,
    NODE_KIND_PROBE,
    NODE_KIND_SOURCE,
    BootstrapContext,
    GraphEdge,
    GraphNode,
    GraphSize,
)
from .bootstrap_catalog import load_bootstrap_catalog_context
from .query_search import query_context_graph
from ..runtime.startup_signals import compact_startup_quality_signals
from .startup_signals import load_bootstrap_quality_signals

_USAGE = (
    "Start from this packet for repo-level orientation. "
    "Follow bootstrap_links when the task requires full authority from "
    "the canonical docs. Use `context-graph --query <term>` for targeted "
    "subgraphs on specific files, MPs, guards, or subsystems."
)


def _current_branch(repo_root) -> str:
    """Detect the current git branch."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=repo_root, timeout=5,
            check=False,
        )
        return result.stdout.strip() or "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def _detect_bridge_liveness(repo_root) -> bool:
    """Check real bridge liveness via reviewer mode, not just file existence."""
    bridge_path = repo_root / "bridge.md"
    if not bridge_path.exists():
        return False
    try:
        from ..review_channel.peer_liveness import reviewer_mode_is_active
        from ..review_channel.handoff import extract_bridge_snapshot, summarize_bridge_liveness

        text = bridge_path.read_text(encoding="utf-8")
        snapshot = extract_bridge_snapshot(text)
        liveness = summarize_bridge_liveness(snapshot)
        return reviewer_mode_is_active(liveness.reviewer_mode)
    except (OSError, ImportError, ValueError):
        return False


def build_bootstrap_context(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> BootstrapContext:
    """Build a slim startup context packet for AI agent bootstrap.

    Provides repo identity, active plans with MP scopes, hotspot files,
    key commands (from governance policy), and deep links. Uses real bridge
    liveness detection instead of file existence.
    """
    repo_root = get_repo_root()
    bridge_active = _detect_bridge_liveness(repo_root)

    plan_nodes = [
        n for n in nodes
        if n.node_kind == NODE_KIND_PLAN and n.metadata.get("is_active_plan")
    ]
    top_hotspots = sorted(
        [n for n in nodes if n.node_kind == NODE_KIND_SOURCE and n.temperature >= 0.3],
        key=lambda n: -n.temperature,
    )[:6]

    policy_commands, bootstrap_commands, policy_links = load_bootstrap_catalog_context(
        repo_root
    )
    bootstrap_commands = bootstrap_commands[:8]
    if bootstrap_commands:
        command_ids = {
            str(entry.get("command_id") or "").strip()
            for entry in bootstrap_commands
        }
        policy_commands = {
            key: value for key, value in policy_commands.items()
            if key in command_ids
        }
    policy_links["bridge"] = "bridge.md" if bridge_active else None
    push_enforcement = detect_push_enforcement_state(
        load_push_policy(repo_root=repo_root),
        repo_root=repo_root,
    )
    quality_signals = compact_startup_quality_signals(
        load_bootstrap_quality_signals(repo_root)
    )
    key_surfaces = load_startup_key_surfaces(repo_root)
    review_state = _load_context_graph_review_state(repo_root)
    runtime_spine_closure = startup_runtime_spine_closure(repo_root)
    packet_carry_forward_debt = startup_packet_carry_forward_debt(
        repo_root=repo_root,
        review_state=review_state,
    )
    packet_continuity_index = startup_packet_continuity_index(review_state, limit=4)
    continuity_attention = startup_continuity_attention(
        runtime_spine_closure=runtime_spine_closure,
        packet_carry_forward_debt=packet_carry_forward_debt,
        packet_continuity_index=packet_continuity_index,
    )

    return BootstrapContext(
        repo=repo_root.name,
        branch=_current_branch(repo_root),
        bridge_active=bridge_active,
        graph_size=GraphSize(
            source_files=sum(1 for n in nodes if n.node_kind == NODE_KIND_SOURCE),
            guards=sum(1 for n in nodes if n.node_kind == NODE_KIND_GUARD),
            probes=sum(1 for n in nodes if n.node_kind == NODE_KIND_PROBE),
            active_plans=len(plan_nodes),
            edges=len(edges),
        ),
        active_plans=_plan_summaries(plan_nodes),
        hotspots=_hotspot_summaries(top_hotspots),
        key_commands=policy_commands,
        bootstrap_links=policy_links,
        push_enforcement=push_enforcement,
        usage=_USAGE,
        bootstrap_commands=bootstrap_commands,
        quality_signals=quality_signals,
        key_surfaces=key_surfaces,
        runtime_spine_closure=runtime_spine_closure,
        packet_continuity_index=packet_continuity_index,
        packet_carry_forward_debt=packet_carry_forward_debt,
        continuity_attention=continuity_attention,
    )


def _load_context_graph_review_state(repo_root):
    """Load typed review state for graph bootstrap without refreshing/writing it."""
    try:
        paths = artifact_paths(repo_root)
        payload = read_json_artifact(paths["review_state"])
    except (OSError, KeyError, TypeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    try:
        return review_state_from_payload(payload)
    except (TypeError, ValueError):
        return None


def _plan_summaries(plan_nodes: list[GraphNode]) -> list[dict[str, object]]:
    return [
        {
            "path": p.canonical_pointer_ref,
            "role": p.metadata.get("role", ""),
            "authority": p.metadata.get("authority", ""),
            "scope": p.metadata.get("scope", ""),
        }
        for p in plan_nodes
    ]


def _hotspot_summaries(hotspots: list[GraphNode]) -> list[dict[str, object]]:
    return [
        {
            "file": n.canonical_pointer_ref,
            "temperature": n.temperature,
            "fan_in": n.metadata.get("fan_in", 0),
            "fan_out": n.metadata.get("fan_out", 0),
            "ranking_summary": _bootstrap_hotspot_ranking_summary(n),
        }
        for n in hotspots
    ]


def _bootstrap_hotspot_ranking_summary(node: GraphNode) -> str:
    fan_in = int(node.metadata.get("fan_in", 0) or 0)
    fan_out = int(node.metadata.get("fan_out", 0) or 0)
    changed = bool(node.metadata.get("changed"))
    suffix = " while the file is currently changed" if changed else ""
    return (
        f"Ranked as a connected neighbor with temperature {node.temperature:.3f}, "
        f"fan-in {fan_in}, fan-out {fan_out}{suffix}. "
        "Edge details suppressed."
    )
