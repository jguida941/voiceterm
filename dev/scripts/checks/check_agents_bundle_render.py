#!/usr/bin/env python3
"""Validate (and optionally rewrite) AGENTS command-bundle reference section."""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.bundle_registry import (  # noqa: E402
    AGENTS_BUNDLE_SECTION_HEADING,
    BUNDLE_AUTHORITY_PATH,
    render_agents_bundle_section_markdown,
)

AGENTS_PATH = REPO_ROOT / "AGENTS.md"
NEXT_HEADING = "## Runtime risk matrix (required add-ons)"
DIFF_PREVIEW_MAX_LINES = 20


def _locate_section(text: str) -> tuple[int, int] | None:
    start = text.find(AGENTS_BUNDLE_SECTION_HEADING)
    if start < 0:
        return None
    end = text.find(NEXT_HEADING, start)
    if end < 0:
        return None
    return start, end


def _diff_preview(expected: str, actual: str) -> list[str]:
    diff = list(
        difflib.unified_diff(
            actual.splitlines(),
            expected.splitlines(),
            fromfile="AGENTS.md (current)",
            tofile=f"AGENTS.md (rendered from {BUNDLE_AUTHORITY_PATH})",
            lineterm="",
        )
    )
    return diff[:DIFF_PREVIEW_MAX_LINES]


def build_report(*, write: bool = False) -> dict:
    report = {
        "command": "check_agents_bundle_render",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "agents_path": "AGENTS.md",
        "bundle_registry": BUNDLE_AUTHORITY_PATH,
        "section_heading": AGENTS_BUNDLE_SECTION_HEADING,
        "next_heading": NEXT_HEADING,
        "write_mode": write,
        "wrote": False,
        "changed": False,
        "ok": True,
        "diff_preview": [],
        "error": None,
    }

    if not AGENTS_PATH.exists():
        report["ok"] = False
        report["error"] = "Missing AGENTS.md file."
        return report

    text = AGENTS_PATH.read_text(encoding="utf-8")
    location = _locate_section(text)
    if location is None:
        report["ok"] = False
        report["error"] = (
            "Unable to locate AGENTS bundle section boundaries "
            f"(`{AGENTS_BUNDLE_SECTION_HEADING}` .. `{NEXT_HEADING}`)."
        )
        return report

    start, end = location
    current_section = text[start:end].strip()
    rendered_section = render_agents_bundle_section_markdown().strip()

    if current_section == rendered_section:
        return report

    report["changed"] = True
    report["diff_preview"] = _diff_preview(rendered_section, current_section)
    if not write:
        report["ok"] = False
        return report

    updated_text = text[:start] + rendered_section + "\n\n" + text[end:]
    AGENTS_PATH.write_text(updated_text, encoding="utf-8")
    report["wrote"] = True
    report["ok"] = True
    report["diff_preview"] = []
    return report


def render_markdown(report: dict) -> str:
    lines = ["# check_agents_bundle_render", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- write_mode: {report.get('write_mode')}")
    lines.append(f"- wrote: {report.get('wrote')}")
    lines.append(f"- changed: {report.get('changed')}")
    lines.append(f"- agents_path: {report.get('agents_path')}")
    lines.append(f"- bundle_registry: {report.get('bundle_registry')}")
    error = report.get("error")
    if error:
        lines.append(f"- error: {error}")
    diff_preview = report.get("diff_preview") or []
    if diff_preview:
        lines.append("")
        lines.append("## Diff preview")
        for line in diff_preview:
            lines.append(f"- `{line}`")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write", action="store_true", help="Rewrite AGENTS bundle section."
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = build_report(write=bool(args.write))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())
