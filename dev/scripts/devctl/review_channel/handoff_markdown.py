"""Markdown and lane helpers extracted from handoff.py."""

from __future__ import annotations

from ..text_utils import normalize_inline_markdown
from .handoff_constants import MARKDOWN_ITEM_RE, ROLLOVER_ACK_PREFIX

_normalize_inline_markdown = normalize_inline_markdown


def _extract_markdown_items(raw_text: str) -> list[str]:
    items: list[str] = []
    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        match = MARKDOWN_ITEM_RE.match(stripped)
        items.append(
            _normalize_inline_markdown(
                (match.group("value") if match is not None else stripped).strip()
            )
        )
    return items


def _first_markdown_item(raw_text: str) -> str | None:
    items = _extract_markdown_items(raw_text)
    return items[0] if items else None


def _group_owned_lanes(
    lane_assignments: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {p: [] for p in ROLLOVER_ACK_PREFIX}
    for lane in lane_assignments:
        provider = lane.get("provider", "").strip().lower()
        if provider not in grouped:
            continue
        grouped[provider].append(
            {
                "agent_id": _normalize_inline_markdown(lane.get("agent_id", "").strip()),
                "lane": _normalize_inline_markdown(lane.get("lane", "").strip()),
                "worktree": _normalize_inline_markdown(lane.get("worktree", "").strip()),
                "branch": _normalize_inline_markdown(lane.get("branch", "").strip()),
                "mp_scope": _normalize_inline_markdown(lane.get("mp_scope", "").strip()),
            }
        )
    return grouped


def _derive_current_atomic_step(snapshot) -> str | None:
    return (
        _first_markdown_item(snapshot.sections.get("Claude Status", ""))
        or _first_markdown_item(snapshot.sections.get("Current Instruction For Claude", ""))
        or _first_markdown_item(snapshot.sections.get("Last Reviewed Scope", ""))
    )
