"""Bundle-path helpers for `devctl triage` artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from .config import REPO_ROOT


def resolve_emit_dir(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def write_bundle(report: dict, emit_dir: Path, prefix: str, *, markdown: str) -> dict:
    emit_dir.mkdir(parents=True, exist_ok=True)
    base = emit_dir / prefix
    md_path = base.with_suffix(".md")
    ai_path = base.with_suffix(".ai.json")
    md_path.write_text(markdown, encoding="utf-8")
    ai_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {
        "written": True,
        "markdown_path": str(md_path),
        "ai_json_path": str(ai_path),
    }
