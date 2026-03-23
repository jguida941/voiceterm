"""Bounded context-escalation helpers built on the repo context graph."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

try:
    from dev.scripts.coderabbit.probe_guidance_artifacts import guidance_ref, load_probe_entries
except ModuleNotFoundError:  # broad-except: allow reason=devctl CLI runs from dev/scripts
    from coderabbit.probe_guidance_artifacts import guidance_ref, load_probe_entries

from .operational_feedback import (
    data_science_reliability_lines,
    quality_feedback_lines,
    recent_fix_history_lines,
    watchdog_digest_lines,
)
from .escalation_render import PacketRenderPayload, render_packet_markdown
from .builder import build_context_graph
from .models import GraphEdge, GraphNode
from .query import query_context_graph

_FILE_TERM_RE = re.compile(
    r"\b(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:py|rs|md|json|ya?ml|toml|sh)\b"
)
_MP_TERM_RE = re.compile(r"\bMP-\d+\b", re.IGNORECASE)
_COMMAND_TERM_RE = re.compile(
    r"(?:dev/scripts/devctl\.py|devctl)\s+([a-z0-9][a-z0-9_-]*)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ContextEscalationPacket:
    """A bounded, prompt-safe context recovery packet."""

    trigger: str
    query_terms: tuple[str, ...]
    matched_nodes: int
    edge_count: int
    canonical_refs: tuple[str, ...]
    evidence: tuple[str, ...]
    markdown: str
    guidance_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextEscalationOptions:
    """Small tuning knob set for bounded escalation packets."""

    max_terms: int = 4
    max_refs: int = 6
    max_chars: int = 1600


def append_context_packet_markdown(
    text: str,
    packet: ContextEscalationPacket | None,
) -> str:
    """Append packet markdown to instruction/prompt text when present."""
    base_text = str(text or "").strip()
    if packet is None:
        return base_text
    packet_markdown = packet.markdown.strip()
    if not packet_markdown:
        return base_text
    if not base_text:
        return packet_markdown
    return f"{base_text}\n\n{packet_markdown}"


def _clean_term(raw_value: Any) -> str:
    text = str(raw_value or "").strip()
    while text and text[0] in "\"'`([{":
        text = text[1:]
    while text and text[-1] in "\"'`)]}.,:;":
        text = text[:-1]
    return text.strip()


def normalize_query_terms(
    terms: Iterable[Any],
    *,
    max_terms: int = 4,
) -> tuple[str, ...]:
    """Normalize, dedupe, and cap query terms while preserving order."""
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_term in terms:
        term = _clean_term(raw_term)
        if not term:
            continue
        key = term.lower().replace("-", "_")
        if key in seen:
            continue
        seen.add(key)
        normalized.append(term)
        if len(normalized) >= max_terms:
            break
    return tuple(normalized)


def extract_query_terms_from_text(
    text: Any,
    *,
    max_terms: int = 4,
) -> tuple[str, ...]:
    """Extract stable query terms from free text."""
    raw_text = str(text or "")
    terms: list[str] = []
    for match in _MP_TERM_RE.finditer(raw_text):
        terms.append(match.group(0).upper())
    for match in _FILE_TERM_RE.finditer(raw_text):
        terms.append(match.group(0))
    for match in _COMMAND_TERM_RE.finditer(raw_text):
        terms.append(match.group(1))
    return normalize_query_terms(terms, max_terms=max_terms)


def collect_query_terms(
    values: Iterable[Any],
    *,
    max_terms: int = 4,
) -> tuple[str, ...]:
    """Collect bounded context-graph query terms from mixed inputs."""
    collected: list[str] = []
    for value in values:
        if isinstance(value, str):
            collected.extend(extract_query_terms_from_text(value, max_terms=max_terms))
            continue
        if isinstance(value, dict):
            for item in value.values():
                collected.extend(extract_query_terms_from_text(item, max_terms=max_terms))
            continue
        if isinstance(value, list | tuple | set):
            for item in value:
                collected.extend(extract_query_terms_from_text(item, max_terms=max_terms))
            continue
        collected.extend(extract_query_terms_from_text(value, max_terms=max_terms))
    return normalize_query_terms(collected, max_terms=max_terms)


def _guidance_match_score(
    entry: dict[str, object],
    *,
    query_terms: tuple[str, ...],
    canonical_refs: tuple[str, ...],
) -> tuple[int, int, str]:
    file_path = str(entry.get("file_path") or "").strip()
    symbol = str(entry.get("symbol") or "").strip()
    probe = str(entry.get("probe") or "").strip()
    haystack = " ".join((file_path, symbol, probe)).lower()
    exact_ref_rank = 0 if file_path and file_path in canonical_refs else 1
    lowered_terms = tuple(term.lower() for term in query_terms)
    term_rank = 0 if any(term in haystack for term in lowered_terms) else 1
    severity_rank = {"high": 0, "medium": 1, "low": 2}.get(
        str(entry.get("severity") or "medium"),
        3,
    )
    return (exact_ref_rank, term_rank, f"{severity_rank}:{file_path}:{probe}:{symbol}")


def _select_probe_guidance(
    *,
    query_terms: tuple[str, ...],
    canonical_refs: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    matched: list[dict[str, object]] = []
    seen: set[str] = set()
    ordered = sorted(
        load_probe_entries(),
        key=lambda entry: _guidance_match_score(
            entry,
            query_terms=query_terms,
            canonical_refs=canonical_refs,
        ),
    )
    for entry in ordered:
        instruction = str(entry.get("ai_instruction") or "").strip()
        if not instruction:
            continue
        exact_ref_rank, term_rank, _sort_tail = _guidance_match_score(
            entry,
            query_terms=query_terms,
            canonical_refs=canonical_refs,
        )
        if exact_ref_rank != 0 and term_rank != 0:
            continue
        ref = guidance_ref(entry)
        if ref in seen:
            continue
        seen.add(ref)
        matched.append(entry)
        if len(matched) >= 3:
            break
    return tuple(matched)


def _decision_constraint_lines(
    guidance_entries: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    lines: list[str] = []
    seen: set[str] = set()
    for entry in guidance_entries:
        decision_mode = str(entry.get("decision_mode") or "").strip()
        if not decision_mode or decision_mode == "recommend_only":
            continue
        ref = guidance_ref(entry)
        if ref in seen:
            continue
        seen.add(ref)
        rationale = str(entry.get("decision_rationale") or "").strip()
        if decision_mode == "approval_required":
            line = f"`{ref}` requires approval before mutation."
        elif decision_mode == "auto_apply":
            line = f"`{ref}` may auto-apply after verification."
        else:
            line = f"`{ref}` uses decision mode `{decision_mode}`."
        if rationale:
            line += f" Rationale: {rationale}"
        lines.append(line)
    return tuple(lines)


def build_context_escalation_packet(
    *,
    trigger: str,
    query_terms: Iterable[Any],
    options: ContextEscalationOptions | dict[str, int] | None = None,
    graph: tuple[list[GraphNode], list[GraphEdge]] | None = None,
) -> ContextEscalationPacket | None:
    """Query the graph with bounded terms and return a compact recovery packet."""
    resolved_options = _resolve_options(options)
    normalized_terms = normalize_query_terms(
        query_terms,
        max_terms=resolved_options.max_terms,
    )
    if not normalized_terms:
        return None

    if graph is None:
        nodes, edges = build_context_graph()
    else:
        nodes, edges = graph

    matched_nodes: dict[str, GraphNode] = {}
    matched_edges: dict[tuple[str, str, str], GraphEdge] = {}
    evidence: list[str] = []
    for term in normalized_terms:
        result = query_context_graph(term, nodes, edges)
        evidence.append(
            f"{term}: nodes={len(result.matched_nodes)}, edges={len(result.edges)}"
        )
        for node in result.matched_nodes:
            matched_nodes[node.node_id] = node
        for edge in result.edges:
            matched_edges[(edge.source_id, edge.target_id, edge.edge_kind)] = edge

    if not matched_nodes:
        return None

    ordered_nodes = sorted(
        matched_nodes.values(),
        key=lambda node: (-node.temperature, node.node_kind, node.node_id),
    )
    canonical_refs = tuple(
        node.canonical_pointer_ref
        for node in ordered_nodes[: resolved_options.max_refs]
    )
    guidance_entries = _select_probe_guidance(
        query_terms=normalized_terms,
        canonical_refs=canonical_refs,
    )
    history_lines = recent_fix_history_lines(
        trigger=trigger,
        query_terms=normalized_terms,
        canonical_refs=canonical_refs,
    )
    quality_lines = quality_feedback_lines(
        trigger=trigger,
        query_terms=normalized_terms,
    )
    watchdog_lines = watchdog_digest_lines(
        trigger=trigger,
        query_terms=normalized_terms,
    )
    reliability_lines = data_science_reliability_lines(
        trigger=trigger,
        query_terms=normalized_terms,
    )
    guidance_lines = tuple(
        (
            str(entry.get("ai_instruction") or "").strip()
            + f" ({guidance_ref(entry)})"
        )
        for entry in guidance_entries
    )
    decision_lines = _decision_constraint_lines(guidance_entries)
    markdown = render_packet_markdown(
        PacketRenderPayload(
            trigger=trigger,
            query_terms=normalized_terms,
            canonical_refs=canonical_refs,
            matched_nodes=len(ordered_nodes),
            edge_count=len(matched_edges),
            guidance_lines=guidance_lines,
            decision_lines=decision_lines,
            history_lines=history_lines,
            watchdog_lines=watchdog_lines,
            reliability_lines=reliability_lines,
            quality_lines=quality_lines,
        )
    )
    if len(markdown) > resolved_options.max_chars:
        markdown = (
            markdown[: max(0, resolved_options.max_chars - 3)].rstrip() + "..."
        )

    return ContextEscalationPacket(
        trigger=trigger,
        query_terms=normalized_terms,
        matched_nodes=len(ordered_nodes),
        edge_count=len(matched_edges),
        canonical_refs=canonical_refs,
        evidence=tuple(evidence),
        markdown=markdown,
        guidance_refs=tuple(guidance_ref(entry) for entry in guidance_entries),
    )


def _resolve_options(
    options: ContextEscalationOptions | dict[str, int] | None,
) -> ContextEscalationOptions:
    if isinstance(options, ContextEscalationOptions):
        return options
    if isinstance(options, dict):
        return ContextEscalationOptions(
            max_terms=int(options.get("max_terms", 4)),
            max_refs=int(options.get("max_refs", 6)),
            max_chars=int(options.get("max_chars", 1200)),
        )
    return ContextEscalationOptions()
