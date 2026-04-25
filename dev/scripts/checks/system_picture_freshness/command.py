#!/usr/bin/env python3
"""Fail when the generated system-picture has stale navigation sections."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_SCRIPTS_ROOT = REPO_ROOT / "dev" / "scripts"
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

_REQUIRED_CURRENT_SECTIONS = frozenset({"startup", "graph"})


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    snapshot_override: Any | None = None,
    required_current_sections: frozenset[str] = _REQUIRED_CURRENT_SECTIONS,
) -> dict[str, object]:
    """Return a typed freshness report for the current SystemPicture snapshot."""
    snapshot = snapshot_override if snapshot_override is not None else _build_snapshot(repo_root)
    sections = [section.to_dict() for section in getattr(snapshot, "sections", ())]
    stale_sections = [
        section
        for section in sections
        if str(section.get("status", "")).strip() == "stale"
    ]
    required_not_current = [
        section
        for section in sections
        if str(section.get("section_id", "")).strip() in required_current_sections
        and str(section.get("status", "")).strip() != "current"
    ]
    errors = _stale_section_errors(stale_sections)
    errors.extend(_required_section_errors(required_not_current))

    return {
        "command": "check_system_picture_freshness",
        "ok": len(errors) == 0,
        "repo_root": str(repo_root),
        "snapshot_id": str(getattr(snapshot, "snapshot_id", "") or ""),
        "head_commit_sha": str(getattr(snapshot, "head_commit_sha", "") or ""),
        "current_section_count": int(
            getattr(snapshot, "current_section_count", 0) or 0
        ),
        "stale_section_count": int(getattr(snapshot, "stale_section_count", 0) or 0),
        "missing_section_count": int(
            getattr(snapshot, "missing_section_count", 0) or 0
        ),
        "required_current_sections": sorted(required_current_sections),
        "stale_sections": [
            _section_summary(section) for section in stale_sections
        ],
        "required_not_current_sections": [
            _section_summary(section) for section in required_not_current
        ],
        "errors": errors,
    }


def _build_snapshot(repo_root: Path):
    try:
        from devctl.platform.system_picture import build_system_picture_snapshot
    except Exception as exc:  # broad-except: allow reason=guard entrypoint import must surface a typed report instead of traceback fallback=raise runtime error with import detail
        raise RuntimeError(f"system_picture_import_failed: {exc}") from exc
    return build_system_picture_snapshot(repo_root=repo_root)


def _section_summary(section: dict[str, object]) -> dict[str, object]:
    return {
        "section_id": str(section.get("section_id", "") or ""),
        "title": str(section.get("title", "") or ""),
        "status": str(section.get("status", "") or ""),
        "source_path": str(section.get("source_path", "") or ""),
        "source_command": str(section.get("source_command", "") or ""),
        "notes": list(section.get("notes", ()) or ()),
    }


def _stale_section_errors(sections: list[dict[str, object]]) -> list[str]:
    return [
        _section_error("stale_section", section)
        for section in sections
    ]


def _required_section_errors(sections: list[dict[str, object]]) -> list[str]:
    errors: list[str] = []
    for section in sections:
        if str(section.get("status", "")).strip() == "stale":
            continue
        errors.append(_section_error("required_section_not_current", section))
    return errors


def _section_error(reason: str, section: dict[str, object]) -> str:
    section_id = str(section.get("section_id", "") or "unknown")
    status = str(section.get("status", "") or "unknown")
    command = str(section.get("source_command", "") or "").strip()
    suffix = f"; refresh with `{command}`" if command else ""
    return f"{reason}: {section_id} status={status}{suffix}"


def _render_report(report: dict[str, object]) -> str:
    lines = ["# check_system_picture_freshness", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- snapshot_id: {report.get('snapshot_id') or 'unknown'}")
    lines.append(f"- head_commit_sha: {report.get('head_commit_sha') or 'unknown'}")
    lines.append(f"- current_sections: {report.get('current_section_count')}")
    lines.append(f"- stale_sections: {report.get('stale_section_count')}")
    lines.append(f"- missing_sections: {report.get('missing_section_count')}")
    errors = report.get("errors") or []
    if errors:
        lines.append("")
        lines.append("## Errors")
        for error in errors:
            lines.append(f"- {error}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()
    try:
        report = build_report()
    except Exception as exc:  # broad-except: allow reason=guard failures should print structured output for CI fallback=typed failure report
        report = {
            "command": "check_system_picture_freshness",
            "ok": False,
            "errors": [str(exc)],
        }
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_report(report))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
