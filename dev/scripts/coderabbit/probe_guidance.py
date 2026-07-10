"""Public probe-guidance surface for Ralph remediation prompts."""

from __future__ import annotations

from pathlib import Path

from .probe_guidance_artifacts import load_probe_entries
from .probe_guidance_matching import select_item_probe_guidance

MAX_PROMPT_PROBE_GUIDANCE = 4


def attach_probe_guidance(
    items: list[dict],
    *,
    report_root: str | Path | None = None,
) -> list[dict]:
    entries = load_probe_entries(report_root)
    enriched: list[dict] = []
    for item in items:
        updated = dict(item)
        matched = select_item_probe_guidance(updated, entries)
        if matched:
            updated["probe_guidance"] = matched
        enriched.append(updated)
    return enriched


def load_probe_guidance(
    items: list[dict],
    *,
    report_root: str | Path | None = None,
) -> list[dict[str, object]]:
    flattened: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for item in attach_probe_guidance(items, report_root=report_root):
        guidance = item.get("probe_guidance")
        if not isinstance(guidance, list):
            continue
        for entry in guidance:
            if not isinstance(entry, dict):
                continue
            key = (
                str(entry.get("file_path") or ""),
                str(entry.get("ai_instruction") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            flattened.append(entry)
    return flattened[:MAX_PROMPT_PROBE_GUIDANCE]
