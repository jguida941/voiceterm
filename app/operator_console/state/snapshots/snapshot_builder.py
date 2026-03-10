"""Snapshot assembly for the Operator Console."""

from __future__ import annotations

import json
from pathlib import Path

from ..bridge.bridge_sections import (
    DEFAULT_BRIDGE_REL,
    extract_bridge_metadata,
    parse_markdown_sections,
)
from ..bridge.lane_builder import (
    build_claude_lane,
    build_codex_lane,
    build_cursor_lane,
    build_operator_lane,
)
from ..core.models import OperatorConsoleSnapshot
from .quality_snapshot import collect_quality_backlog_snapshot
from ..review.review_state import (
    find_review_full_path,
    find_review_state_path,
    load_json_object,
    load_pending_approvals,
    parse_pending_approvals,
)
from ..sessions.session_builder import (
    build_claude_session_surface,
    build_codex_session_surface,
    build_cursor_session_surface,
)
from ..sessions.session_trace_reader import load_live_session_trace


def build_operator_console_snapshot(
    repo_root: Path,
    *,
    bridge_rel: str = DEFAULT_BRIDGE_REL,
    review_state_path: Path | None = None,
) -> OperatorConsoleSnapshot:
    """Load bridge/review files and build a shared-screen snapshot."""
    bridge_path = repo_root / bridge_rel
    warnings: list[str] = []
    if bridge_path.exists():
        raw_bridge_text = bridge_path.read_text(encoding="utf-8")
    else:
        raw_bridge_text = ""
        warnings.append(f"Bridge file is missing: {bridge_path}")

    sections = parse_markdown_sections(raw_bridge_text)
    metadata = extract_bridge_metadata(raw_bridge_text)

    resolved_review_state = review_state_path or find_review_state_path(repo_root)
    resolved_review_full = find_review_full_path(repo_root)
    review_projection: dict[str, object] | None = None
    if resolved_review_full is not None:
        try:
            review_projection = load_json_object(resolved_review_full)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            warnings.append(f"Could not load review-channel full projection: {exc}")

    pending_approvals = ()
    if resolved_review_state is not None:
        try:
            pending_approvals = load_pending_approvals(resolved_review_state)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            warnings.append(f"Could not load review_state JSON: {exc}")
    elif isinstance(review_projection, dict):
        nested_review_state = review_projection.get("review_state")
        if isinstance(nested_review_state, dict):
            try:
                pending_approvals = parse_pending_approvals(nested_review_state)
            except ValueError as exc:
                warnings.append(f"Could not parse nested review_state approvals: {exc}")

    codex_panel_text = _format_panel(
        "Codex Lane",
        [
            ("Last Codex poll", metadata.last_codex_poll or "(unknown)"),
            ("Last worktree hash", metadata.last_worktree_hash or "(unknown)"),
            ("Poll Status", sections.get("Poll Status", "(missing)")),
            ("Current Verdict", sections.get("Current Verdict", "(missing)")),
            ("Open Findings", sections.get("Open Findings", "(missing)")),
        ],
    )
    claude_panel_text = _format_panel(
        "Claude Lane",
        [
            ("Claude Status", sections.get("Claude Status", "(missing)")),
            ("Claude Questions", sections.get("Claude Questions", "(missing)")),
            ("Claude Ack", sections.get("Claude Ack", "(missing)")),
        ],
    )
    cursor_panel_text = _format_panel(
        "Cursor Lane",
        [
            ("Cursor Status", sections.get("Cursor Status", "(missing)")),
            ("Cursor Focus", sections.get("Cursor Focus", "(missing)")),
        ],
    )
    operator_panel_text = _format_operator_panel(
        sections=sections,
        pending_approvals=pending_approvals,
        review_state_path=resolved_review_state,
    )
    codex_live_trace = load_live_session_trace(
        repo_root,
        provider="codex",
        review_full_path=resolved_review_full,
    )
    claude_live_trace = load_live_session_trace(
        repo_root,
        provider="claude",
        review_full_path=resolved_review_full,
    )
    cursor_live_trace = load_live_session_trace(
        repo_root,
        provider="cursor",
        review_full_path=resolved_review_full,
    )

    codex_lane = build_codex_lane(
        sections,
        metadata.last_codex_poll,
        metadata.last_worktree_hash,
        live_trace=codex_live_trace,
    )
    claude_lane = build_claude_lane(sections, live_trace=claude_live_trace)
    cursor_lane = build_cursor_lane(sections, live_trace=cursor_live_trace)
    operator_lane = build_operator_lane(
        sections, pending_approvals, resolved_review_state
    )
    codex_session_surface = build_codex_session_surface(
        live_trace=codex_live_trace,
        lane=codex_lane,
        sections=sections,
        last_codex_poll=metadata.last_codex_poll,
        last_worktree_hash=metadata.last_worktree_hash,
        review_projection=review_projection,
    )
    claude_session_surface = build_claude_session_surface(
        live_trace=claude_live_trace,
        lane=claude_lane,
        sections=sections,
        review_projection=review_projection,
    )
    cursor_session_surface = build_cursor_session_surface(
        live_trace=cursor_live_trace,
        lane=cursor_lane,
        sections=sections,
        review_projection=review_projection,
    )
    quality_backlog = collect_quality_backlog_snapshot(repo_root)

    return OperatorConsoleSnapshot(
        codex_panel_text=codex_panel_text,
        claude_panel_text=claude_panel_text,
        operator_panel_text=operator_panel_text,
        cursor_panel_text=cursor_panel_text,
        codex_session_text=codex_session_surface.terminal_text,
        claude_session_text=claude_session_surface.terminal_text,
        cursor_session_text=cursor_session_surface.terminal_text,
        raw_bridge_text=raw_bridge_text,
        review_mode=metadata.review_mode,
        last_codex_poll=metadata.last_codex_poll,
        last_worktree_hash=metadata.last_worktree_hash,
        pending_approvals=pending_approvals,
        warnings=tuple(warnings),
        review_state_path=(
            str(resolved_review_state) if resolved_review_state is not None else None
        ),
        codex_lane=codex_lane,
        claude_lane=claude_lane,
        cursor_lane=cursor_lane,
        operator_lane=operator_lane,
        codex_session_stats_text=codex_session_surface.stats_text,
        codex_session_registry_text=codex_session_surface.registry_text,
        claude_session_stats_text=claude_session_surface.stats_text,
        claude_session_registry_text=claude_session_surface.registry_text,
        cursor_session_stats_text=cursor_session_surface.stats_text,
        cursor_session_registry_text=cursor_session_surface.registry_text,
        quality_backlog=quality_backlog,
    )


def _format_operator_panel(
    *,
    sections: dict[str, str],
    pending_approvals: tuple[object, ...],
    review_state_path: Path | None,
) -> str:
    rows = [
        (
            "Current Instruction For Claude",
            sections.get("Current Instruction For Claude", "(missing)"),
        ),
        ("Last Reviewed Scope", sections.get("Last Reviewed Scope", "(missing)")),
        (
            "Structured review_state",
            str(review_state_path)
            if review_state_path is not None
            else "(not found; markdown bridge only)",
        ),
        ("Pending approvals", str(len(pending_approvals))),
    ]
    panel_text = _format_panel("Review / Operator", rows)
    if not pending_approvals:
        return panel_text
    approval_lines = [
        f"- {approval.packet_id}: {approval.summary} [{approval.policy_hint}]"
        for approval in pending_approvals
    ]
    return f"{panel_text}\n\nPending approval queue:\n" + "\n".join(approval_lines)


def _format_panel(title: str, rows: list[tuple[str, str]]) -> str:
    lines = [title, "=" * len(title)]
    for label, value in rows:
        lines.append("")
        lines.append(f"{label}:")
        lines.append(value.strip() or "(empty)")
    return "\n".join(lines)
