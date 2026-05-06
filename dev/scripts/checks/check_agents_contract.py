#!/usr/bin/env python3
"""Validate AGENTS.md as a generated projection-only boot card."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.governance.instruction_boot_card import (  # noqa: E402
    FORBIDDEN_BOOT_CLAIMS,
    INSTRUCTION_BOOT_CARD_CONTRACT_ID,
    REQUIRED_BOOT_COMMANDS,
    REQUIRED_BOOT_SECTIONS,
)

AGENTS_PATH = REPO_ROOT / "AGENTS.md"
MAX_BOOT_CARD_LINES = 200
MAX_BOOT_CARD_BYTES = 32768


def _extract_h2(text: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE)
    ]


def _contains_command_token(text: str, command: str) -> bool:
    pattern = rf"(?<![A-Za-z0-9_-]){re.escape(command)}(?![A-Za-z0-9_-])"
    return re.search(pattern, text) is not None


def _build_report() -> dict:
    if not AGENTS_PATH.exists():
        return {
            "command": "check_agents_contract",
            "ok": False,
            "error": f"Missing file: {AGENTS_PATH.relative_to(REPO_ROOT)}",
        }

    text = AGENTS_PATH.read_text(encoding="utf-8")
    h2 = _extract_h2(text)
    line_count = len(text.splitlines())
    byte_count = len(text.encode("utf-8"))

    missing_h2 = [heading for heading in REQUIRED_BOOT_SECTIONS if heading not in h2]
    missing_markers = [
        marker
        for marker in (
            "This is projection-only",
            INSTRUCTION_BOOT_CARD_CONTRACT_ID,
            "projection_only: true",
            "SurfaceProvenance",
        )
        if marker not in text
    ]
    missing_commands = [
        command
        for command in REQUIRED_BOOT_COMMANDS
        if not _contains_command_token(text, command)
    ]
    forbidden_claims = [claim for claim in FORBIDDEN_BOOT_CLAIMS if claim in text]
    over_line_budget = line_count > MAX_BOOT_CARD_LINES
    over_byte_budget = byte_count > MAX_BOOT_CARD_BYTES

    ok = not (
        missing_h2
        or missing_markers
        or missing_commands
        or forbidden_claims
        or over_line_budget
        or over_byte_budget
    )

    return {
        "command": "check_agents_contract",
        "ok": ok,
        "path": str(AGENTS_PATH.relative_to(REPO_ROOT)),
        "contract_id": INSTRUCTION_BOOT_CARD_CONTRACT_ID,
        "line_count": line_count,
        "byte_count": byte_count,
        "max_line_count": MAX_BOOT_CARD_LINES,
        "max_byte_count": MAX_BOOT_CARD_BYTES,
        "missing_h2": missing_h2,
        "missing_markers": missing_markers,
        "missing_commands": missing_commands,
        "forbidden_claims": forbidden_claims,
        "over_line_budget": over_line_budget,
        "over_byte_budget": over_byte_budget,
    }


def _render_md(report: dict) -> str:
    lines = ["# check_agents_contract", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    if "error" in report:
        lines.append(f"- error: {report['error']}")
        return "\n".join(lines)

    lines.append(f"- path: {report['path']}")
    lines.append(f"- contract_id: {report['contract_id']}")
    lines.append(f"- lines: {report['line_count']} / {report['max_line_count']}")
    lines.append(f"- bytes: {report['byte_count']} / {report['max_byte_count']}")
    for key in (
        "missing_h2",
        "missing_markers",
        "missing_commands",
        "forbidden_claims",
    ):
        value = report[key]
        lines.append(f"- {key}: " + (", ".join(value) if value else "none"))
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = _build_report()

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())
