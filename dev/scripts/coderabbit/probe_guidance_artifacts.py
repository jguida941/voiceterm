"""Probe artifact readers for Ralph remediation guidance."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.repo_packs import active_path_config

DEFAULT_PROBE_REPORT_ROOT = Path(active_path_config().probe_report_output_root_rel)


def resolve_probe_report_root(report_root: str | Path | None = None) -> Path:
    if report_root is not None:
        return Path(report_root)
    env_root = os.environ.get("RALPH_PROBE_REPORT_ROOT", "").strip()
    if env_root:
        return Path(env_root)
    return REPO_ROOT / DEFAULT_PROBE_REPORT_ROOT


def _read_probe_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[ralph-ai-fix] failed to read probe artifact {path}: {exc}", file=sys.stderr)
        return None
    return payload if isinstance(payload, dict) else None


def _guidance_entry_from_finding(finding: dict, *, file_path: str = "") -> dict[str, object] | None:
    ai_instruction = str(finding.get("ai_instruction") or "").strip()
    if not ai_instruction:
        return None
    resolved_path = str(finding.get("file_path") or finding.get("file") or file_path or "").strip()
    return {
        "file_path": resolved_path,
        "symbol": str(finding.get("symbol") or "").strip(),
        "probe": str(finding.get("check_id") or finding.get("probe") or "").strip(),
        "severity": str(finding.get("severity") or "medium").strip(),
        "ai_instruction": ai_instruction,
        "line": finding.get("line"),
        "end_line": finding.get("end_line"),
    }


def _entries_from_rows(
    rows: object,
    *,
    file_path: str = "",
) -> list[dict[str, object]]:
    if not isinstance(rows, list):
        return []
    entries: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        entry = _guidance_entry_from_finding(row, file_path=file_path)
        if entry is not None:
            entries.append(entry)
    return entries


def _load_review_target_entries(root: Path) -> list[dict[str, object]]:
    review_targets = _read_probe_json(root / "review_targets.json")
    if not isinstance(review_targets, dict):
        return []
    return _entries_from_rows(review_targets.get("findings"))


def _load_review_packet_entries(root: Path) -> list[dict[str, object]]:
    review_packet = _read_probe_json(root / "latest" / "review_packet.json")
    if not isinstance(review_packet, dict):
        return []
    hotspots = review_packet.get("hotspots")
    if not isinstance(hotspots, list):
        return []
    entries: list[dict[str, object]] = []
    for hotspot in hotspots:
        if not isinstance(hotspot, dict):
            continue
        entries.extend(
            _entries_from_rows(
                hotspot.get("representative_hints"),
                file_path=str(hotspot.get("file") or "").strip(),
            )
        )
    return entries


def load_probe_entries(report_root: str | Path | None = None) -> list[dict[str, object]]:
    root = resolve_probe_report_root(report_root)
    entries = _load_review_target_entries(root)
    if entries:
        return entries
    return _load_review_packet_entries(root)
