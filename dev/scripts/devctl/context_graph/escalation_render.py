"""Markdown rendering helpers for bounded context-escalation packets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PacketRenderPayload:
    """Compact input bundle for packet markdown rendering."""

    trigger: str
    query_terms: tuple[str, ...]
    canonical_refs: tuple[str, ...]
    matched_nodes: int
    edge_count: int
    guidance_lines: tuple[str, ...] = ()
    history_lines: tuple[str, ...] = ()
    quality_lines: tuple[str, ...] = ()


def render_packet_markdown(payload: PacketRenderPayload) -> str:
    """Render one bounded prompt-safe context recovery packet."""
    lines = [
        "## Context Recovery Packet",
        "",
        f"- Trigger: `{payload.trigger}`",
        "- Query terms: " + ", ".join(f"`{term}`" for term in payload.query_terms),
        f"- Graph matches: nodes={payload.matched_nodes}, edges={payload.edge_count}",
        "- Canonical refs:",
    ]
    for ref in payload.canonical_refs:
        lines.append(f"  - `{ref}`")
    _append_section(
        lines,
        title="## Probe Guidance",
        intro=(
            "Treat these probe-backed remediation hints as the default repair "
            "plan unless you can justify waiving them."
        ),
        entries=payload.guidance_lines,
    )
    _append_section(
        lines,
        title="## Recent Fix History",
        intro=(
            "Use these adjudicated recent outcomes to reuse proven fixes and "
            "avoid repeating recently waived or deferred patterns."
        ),
        entries=payload.history_lines,
    )
    _append_section(
        lines,
        title="## Repo Quality Feedback",
        intro="Latest governance-quality recommendations relevant to this scope:",
        entries=payload.quality_lines,
    )
    lines.extend(
        [
            "",
            (
                "Read these refs before editing outside the current read set or "
                "when blast radius is unclear."
            ),
        ]
    )
    return "\n".join(lines)


def _append_section(
    lines: list[str],
    *,
    title: str,
    intro: str,
    entries: tuple[str, ...],
) -> None:
    if not entries:
        return
    lines.extend(["", title, "", intro])
    for entry in entries:
        lines.append(f"- {entry}")
