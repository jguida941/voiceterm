"""Startup probe-guidance loaders."""

from __future__ import annotations

from pathlib import Path

from .startup_signal_io import load_json_file


def load_guidance_hotspots(repo_root: Path) -> list[dict[str, object]]:
    payload = load_json_file(
        repo_root / "dev" / "reports" / "probes" / "latest" / "review_packet.json"
    )
    summary = payload.get("summary") if isinstance(payload, dict) else None
    top_hotspot = summary.get("top_hotspot") if isinstance(summary, dict) else None
    if not isinstance(top_hotspot, dict):
        return []
    hints = top_hotspot.get("representative_hints")
    guidance = []
    if isinstance(hints, list):
        for hint in hints[:2]:
            entry = _guidance_entry(hint)
            if entry is not None:
                guidance.append(entry)
    if not guidance:
        return []
    return [
        {
            "file": top_hotspot.get("file"),
            "hint_count": top_hotspot.get("hint_count"),
            "bounded_next_slice": top_hotspot.get("bounded_next_slice"),
            "guidance": guidance,
        }
    ]


def _guidance_entry(hint: object) -> dict[str, object] | None:
    if not isinstance(hint, dict):
        return None
    instruction = str(hint.get("ai_instruction") or "").strip()
    if not instruction:
        return None
    entry: dict[str, object] = {}
    entry["probe"] = str(hint.get("probe") or "unknown").strip()
    entry["symbol"] = str(hint.get("symbol") or "(file-level)").strip()
    entry["severity"] = str(hint.get("severity") or "unknown").strip()
    entry["ai_instruction"] = instruction
    entry["practice_title"] = str(hint.get("practice_title") or "").strip()
    entry["practice_explanation"] = str(hint.get("practice_explanation") or "").strip()
    return entry
