"""Priority ranking over accumulated markdown findings."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Sequence

from ..context_graph.models import EDGE_KIND_IMPORTS, GraphEdge, GraphNode, NODE_KIND_SOURCE
from .enrich import SEVERITY_ORDER, normalize_severity
from .findings_priority_models import AccumulatedFinding, RankedFinding
from .findings_priority_render import (
    build_priority_payload,
    render_priority_markdown,
    render_priority_text,
)

DEFAULT_FINDINGS_LOG_PATH = "dev/audits/LIVE_RUN.md"
_HEADING_RE = re.compile(
    r"^###\s+(?P<title>.+?)\n(?P<body>.*?)(?=^###\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
_QID_RE = re.compile(r"\b(?P<qid>Q\d+)\b")
_PATH_RE = re.compile(
    r"(?P<path>(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.(?:py|rs|sh|md|json|ya?ml|toml))"
    r"(?::\d+(?:[-:]\d+)*)?"
)
_RESOLVED_HINTS = ("fixed", "resolved", "closed", "reverted")
_OPEN_HINTS = (" open", "open ", "unblocked", "structural fix open")
_SUMMARY_LIMIT = 180


def load_accumulated_findings(path: Path) -> tuple[AccumulatedFinding, ...]:
    """Parse the append-only findings markdown log into typed records."""
    text = path.read_text(encoding="utf-8")
    parsed = [
        _parse_section(match.group("title"), match.group("body"))
        for match in _HEADING_RE.finditer(text)
    ]
    findings = [entry for entry in parsed if entry is not None]
    resolved_qids = {entry.qid for entry in findings if _fixed_notice(entry)}
    return tuple(
        _with_resolution_state(entry, resolved_qids=resolved_qids)
        for entry in findings
    )


def rank_accumulated_findings(
    findings: Sequence[AccumulatedFinding],
    *,
    graph_nodes: Sequence[GraphNode],
    graph_edges: Sequence[GraphEdge],
    include_resolved: bool = False,
    top_n: int = 20,
) -> tuple[RankedFinding, ...]:
    """Rank findings by triage severity first, then graph-derived fan-out."""
    fan_out_by_path = _fan_out_by_path(graph_nodes=graph_nodes, graph_edges=graph_edges)
    rows: list[RankedFinding] = []
    for entry in findings:
        if not include_resolved and entry.resolution_state != "open":
            continue
        fan_out_rows = tuple(
            (file_path, fan_out_by_path.get(file_path, 0))
            for file_path in entry.file_refs
        )
        matched_refs = tuple(file_path for file_path, fan_out in fan_out_rows if fan_out > 0)
        primary_file = _primary_file(fan_out_rows, entry.file_refs)
        rows.append(
            RankedFinding(
                rank=0,
                qid=entry.qid,
                heading=entry.heading,
                severity=entry.severity,
                severity_rank=entry.severity_rank,
                status=entry.status,
                summary=entry.summary,
                resolution_state=entry.resolution_state,
                primary_file=primary_file,
                file_refs=entry.file_refs,
                matched_file_refs=matched_refs,
                max_fan_out=max((fan_out for _file_path, fan_out in fan_out_rows), default=0),
                fan_out_by_file=tuple(
                    sorted(fan_out_rows, key=lambda item: (-item[1], item[0]))
                ),
            )
        )
    rows.sort(key=_ranking_sort_key)
    limited = rows[: max(0, top_n)]
    return tuple(_with_rank(row, index + 1) for index, row in enumerate(limited))


def _parse_section(title: str, body: str) -> AccumulatedFinding | None:
    qid = _extract_qid(title)
    if not qid:
        return None
    raw_severity = _field_value(body, "Severity")
    status = _field_value(body, "Status")
    summary = _summary_text(_field_value(body, "Body"), title)
    refs_text = "\n".join(
        value
        for value in (
            title,
            _field_value(body, "Location"),
            _field_value(body, "Body"),
            _field_value(body, "Fix recommendations"),
            _field_value(body, "Interpretation"),
            _field_value(body, "Action"),
        )
        if value
    )
    severity = normalize_severity(raw_severity or title)
    return AccumulatedFinding(
        qid=qid,
        heading=" ".join(title.split()),
        severity=severity,
        severity_rank=SEVERITY_ORDER.get(severity, SEVERITY_ORDER["medium"]),
        raw_severity=raw_severity,
        status=" ".join(status.split()),
        summary=summary,
        file_refs=tuple(_ordered_unique(_extract_paths(refs_text))),
        resolution_state="open",
    )


def _field_value(body: str, field: str) -> str:
    pattern = re.compile(
        rf"^- \*\*{re.escape(field)}\*\*:\s*(?P<value>.*?)(?=^\- \*\*[^*]+\*\*:|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        return ""
    return match.group("value").strip()


def _extract_qid(title: str) -> str:
    match = _QID_RE.search(title)
    return match.group("qid") if match is not None else ""


def _summary_text(body: str, title: str) -> str:
    source = " ".join((body or title).split())
    if len(source) <= _SUMMARY_LIMIT:
        return source
    return source[: _SUMMARY_LIMIT - 3].rstrip() + "..."


def _extract_paths(text: str) -> list[str]:
    return [match.group("path") for match in _PATH_RE.finditer(text)]


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        ordered.append(value)
        seen.add(value)
    return tuple(ordered)


def _with_resolution_state(
    entry: AccumulatedFinding,
    *,
    resolved_qids: set[str],
) -> AccumulatedFinding:
    state = _resolution_state(entry, resolved_qids=resolved_qids)
    return AccumulatedFinding(
        qid=entry.qid,
        heading=entry.heading,
        severity=entry.severity,
        severity_rank=entry.severity_rank,
        raw_severity=entry.raw_severity,
        status=entry.status,
        summary=entry.summary,
        file_refs=entry.file_refs,
        resolution_state=state,
    )


def _resolution_state(entry: AccumulatedFinding, *, resolved_qids: set[str]) -> str:
    if entry.qid in resolved_qids and not _fixed_notice(entry):
        return "superseded"
    text = f"{entry.heading} {entry.status}".lower()
    if any(hint in text for hint in _OPEN_HINTS):
        return "open"
    if any(hint in text for hint in _RESOLVED_HINTS):
        return "resolved"
    return "open"


def _fixed_notice(entry: AccumulatedFinding) -> bool:
    text = f"{entry.heading} {entry.status}".lower()
    return "fixed" in text


def _fan_out_by_path(
    *,
    graph_nodes: Sequence[GraphNode],
    graph_edges: Sequence[GraphEdge],
) -> dict[str, int]:
    source_paths = {
        node.node_id: node.canonical_pointer_ref
        for node in graph_nodes
        if node.node_kind == NODE_KIND_SOURCE
    }
    fan_out_by_path: dict[str, int] = {path: 0 for path in source_paths.values()}
    for edge in graph_edges:
        if edge.edge_kind != EDGE_KIND_IMPORTS:
            continue
        file_path = source_paths.get(edge.source_id)
        if file_path is None:
            continue
        fan_out_by_path[file_path] = fan_out_by_path.get(file_path, 0) + 1
    return fan_out_by_path


def _primary_file(
    fan_out_rows: Sequence[tuple[str, int]],
    file_refs: Sequence[str],
) -> str:
    if fan_out_rows:
        best_file, best_fan_out = max(fan_out_rows, key=lambda item: (item[1], item[0]))
        if best_fan_out > 0:
            return best_file
    return file_refs[0] if file_refs else ""


def _ranking_sort_key(row: RankedFinding) -> tuple[int, int, int, str, str]:
    resolution_rank = {"open": 0, "resolved": 1, "superseded": 2}.get(
        row.resolution_state,
        3,
    )
    return (
        resolution_rank,
        -row.severity_rank,
        -row.max_fan_out,
        row.primary_file or row.qid,
        row.heading,
    )


def _with_rank(row: RankedFinding, rank: int) -> RankedFinding:
    return RankedFinding(
        rank=rank,
        qid=row.qid,
        heading=row.heading,
        severity=row.severity,
        severity_rank=row.severity_rank,
        status=row.status,
        summary=row.summary,
        resolution_state=row.resolution_state,
        primary_file=row.primary_file,
        file_refs=row.file_refs,
        matched_file_refs=row.matched_file_refs,
        max_fan_out=row.max_fan_out,
        fan_out_by_file=row.fan_out_by_file,
    )


__all__ = [
    "AccumulatedFinding",
    "DEFAULT_FINDINGS_LOG_PATH",
    "RankedFinding",
    "build_priority_payload",
    "load_accumulated_findings",
    "rank_accumulated_findings",
    "render_priority_markdown",
    "render_priority_text",
]
