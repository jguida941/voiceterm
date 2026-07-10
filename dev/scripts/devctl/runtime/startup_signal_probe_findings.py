"""Startup probe-finding loaders."""

from __future__ import annotations

from pathlib import Path

from .startup_signal_io import load_json_file


def load_code_shape_clusters(repo_root: Path) -> list[dict[str, object]]:
    payload = load_json_file(
        repo_root / "dev" / "reports" / "probes" / "latest" / "summary.json"
    )
    rows: list[dict[str, object]] = []
    for hint in _risk_hints(payload):
        if str(hint.get("risk_type") or "").strip() != "mixed_concerns":
            continue
        first_signal = str((hint.get("signals") or [""])[0] or "").strip()
        digits = "".join(ch for ch in first_signal if ch.isdigit())
        row: dict[str, object] = {}
        row["file"] = hint.get("file") or hint.get("file_path")
        row["cluster_count"] = int(digits) if digits else None
        row["severity"] = hint.get("severity")
        row["ai_instruction"] = hint.get("ai_instruction")
        rows.append(row)
        if len(rows) >= 3:
            break
    return rows


def load_split_advisor_rows(repo_root: Path) -> list[dict[str, object]]:
    payload = load_json_file(
        repo_root / "dev" / "reports" / "probes" / "latest" / "summary.json"
    )
    rows: list[dict[str, object]] = []
    for hint in _risk_hints(payload):
        if str(hint.get("risk_type") or "").strip() != "split_advisor":
            continue
        instruction = str(hint.get("ai_instruction") or "").strip()
        if not instruction:
            continue
        row: dict[str, object] = {}
        row["file"] = hint.get("file") or hint.get("file_path")
        row["severity"] = hint.get("severity")
        row["ai_instruction"] = instruction
        rows.append(row)
        if len(rows) >= 2:
            break
    return rows


def _risk_hints(payload: object) -> list[dict[str, object]]:
    hints = payload.get("risk_hints") if isinstance(payload, dict) else None
    if not isinstance(hints, list):
        return []
    return [hint for hint in hints if isinstance(hint, dict)]
