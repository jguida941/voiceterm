"""Startup probe-summary loaders."""

from __future__ import annotations

from pathlib import Path

from .startup_signal_io import load_json_file


def load_probe_report_summary(repo_root: Path) -> dict[str, object] | None:
    payload = load_json_file(
        repo_root / "dev" / "reports" / "probes" / "latest" / "summary.json"
    )
    summary = payload.get("summary") if isinstance(payload, dict) else None
    if not isinstance(summary, dict):
        return None
    return {
        "generated_at": payload.get("generated_at"),
        "files_with_hints": summary.get("files_with_hints"),
        "risk_hints": summary.get("risk_hints"),
        "top_files": _top_files(summary.get("top_files")),
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
