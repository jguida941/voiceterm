"""Shared startup quality-signal summaries for bootstrap and startup-context."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_INTERESTING_COMMANDS = (
    "check",
    "probe-report",
    "governance-review",
    "context-graph",
    "review-channel",
)


def load_startup_quality_signals(repo_root: Path) -> dict[str, object]:
    """Load bounded startup summaries from recent governance artifacts."""
    signals: dict[str, object] = {}
    probe_report = _load_probe_report_summary(repo_root)
    if probe_report:
        signals["probe_report"] = probe_report
    governance_review = _load_governance_review_summary(repo_root)
    if governance_review:
        signals["governance_review"] = governance_review
    guidance_hotspots = _load_guidance_hotspots(repo_root)
    if guidance_hotspots:
        signals["guidance_hotspots"] = guidance_hotspots
    watchdog = _load_watchdog_summary(repo_root)
    if watchdog:
        signals["watchdog"] = watchdog
    command_reliability = _load_command_reliability_summary(repo_root)
    if command_reliability:
        signals["command_reliability"] = command_reliability
    return signals


def _load_probe_report_summary(repo_root: Path) -> dict[str, object] | None:
    payload = _load_json(repo_root / "dev" / "reports" / "probes" / "summary.json")
    summary = payload.get("summary") if isinstance(payload, dict) else None
    if not isinstance(summary, dict):
        return None
    top_files = summary.get("top_files")
    return {
        "generated_at": payload.get("generated_at"),
        "files_with_hints": summary.get("files_with_hints"),
        "risk_hints": summary.get("risk_hints"),
        "top_files": _top_files(top_files),
    }


def _load_governance_review_summary(repo_root: Path) -> dict[str, object] | None:
    payload = _load_json(
        repo_root / "dev" / "reports" / "governance" / "latest" / "review_summary.json"
    )
    stats = payload.get("stats") if isinstance(payload, dict) else None
    if not isinstance(stats, dict):
        return None
    return {
        "generated_at_utc": payload.get("generated_at_utc"),
        "total_findings": stats.get("total_findings"),
        "open_finding_count": stats.get("open_finding_count"),
        "fixed_count": stats.get("fixed_count"),
        "cleanup_rate_pct": stats.get("cleanup_rate_pct"),
    }


def _load_guidance_hotspots(repo_root: Path) -> list[dict[str, object]]:
    payload = _load_json(
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
            if not isinstance(hint, dict):
                continue
            instruction = str(hint.get("ai_instruction") or "").strip()
            if not instruction:
                continue
            guidance.append(
                {
                    "probe": str(hint.get("probe") or "unknown").strip(),
                    "symbol": str(hint.get("symbol") or "(file-level)").strip(),
                    "severity": str(hint.get("severity") or "unknown").strip(),
                    "ai_instruction": instruction,
                }
            )
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


def _load_watchdog_summary(repo_root: Path) -> dict[str, object] | None:
    payload = _load_json(
        repo_root / "dev" / "reports" / "data_science" / "latest" / "summary.json"
    )
    watchdog = payload.get("watchdog_stats") if isinstance(payload, dict) else None
    if not isinstance(watchdog, dict):
        return None
    families = watchdog.get("guard_families")
    top_family = families[0] if isinstance(families, list) and families else None
    return {
        "generated_at": payload.get("generated_at"),
        "total_episodes": watchdog.get("total_episodes"),
        "success_rate_pct": watchdog.get("success_rate_pct"),
        "false_positive_rate_pct": watchdog.get("false_positive_rate_pct"),
        "top_guard_family": (
            top_family.get("guard_family") if isinstance(top_family, dict) else None
        ),
    }


def _load_command_reliability_summary(repo_root: Path) -> dict[str, object] | None:
    payload = _load_json(
        repo_root / "dev" / "reports" / "data_science" / "latest" / "summary.json"
    )
    event_stats = payload.get("event_stats") if isinstance(payload, dict) else None
    if not isinstance(event_stats, dict):
        return None
    rows = event_stats.get("commands")
    commands: list[dict[str, object]] = []
    if isinstance(rows, list):
        selected = [
            row
            for row in rows
            if isinstance(row, dict)
            and str(row.get("command") or "").strip() in _INTERESTING_COMMANDS
        ]
        order = {name: index for index, name in enumerate(_INTERESTING_COMMANDS)}
        selected.sort(key=lambda row: order.get(str(row.get("command")), len(order)))
        commands = [
            {
                "command": row.get("command"),
                "success_rate_pct": row.get("success_rate_pct"),
                "avg_duration_seconds": row.get("avg_duration_seconds"),
            }
            for row in selected[:4]
        ]
    return {
        "generated_at": payload.get("generated_at"),
        "total_events": event_stats.get("total_events"),
        "success_rate_pct": event_stats.get("success_rate_pct"),
        "p95_duration_seconds": event_stats.get("p95_duration_seconds"),
        "commands": commands,
    }


def _top_files(payload: object) -> list[dict[str, object]]:
    if not isinstance(payload, list):
        return []
    return [
        {
            "file": row.get("file"),
            "hint_count": row.get("hint_count"),
        }
        for row in payload[:3]
        if isinstance(row, dict)
    ]


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None
