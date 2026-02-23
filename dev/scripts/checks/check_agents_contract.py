#!/usr/bin/env python3
"""Validate the required AGENTS.md structure and core operational contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTS_PATH = REPO_ROOT / "AGENTS.md"

REQUIRED_H2 = [
    "Purpose",
    "Source-of-truth map",
    "Instruction scope and precedence",
    "Mandatory 12-step SOP (always)",
    "Active-plan onboarding (adding files under `dev/active/`)",
    "Task router (pick one class)",
    "Context packs (load only what class needs)",
    "Command bundles (source of truth)",
    "Release SOP (master only)",
    "CI lane mapping (what must be green)",
    "Documentation governance",
    "Tooling inventory",
    "End-of-session checklist",
]

REQUIRED_BUNDLES = [
    "bundle.bootstrap",
    "bundle.runtime",
    "bundle.docs",
    "bundle.tooling",
    "bundle.release",
    "bundle.post-push",
]

REQUIRED_MARKERS = [
    "dev/active/INDEX.md",
    "python3 dev/scripts/checks/check_active_plan_sync.py",
    "python3 dev/scripts/checks/check_release_version_parity.py",
    "python3 dev/scripts/devctl.py docs-check --strict-tooling",
    "python3 dev/scripts/devctl.py status --ci --require-ci --format md",
]

REQUIRED_ROUTER_SNIPPETS = [
    "| Changed runtime behavior under `src/**` | Runtime feature/fix | `bundle.runtime` |",
    "| Changed only user-facing docs | Docs-only | `bundle.docs` |",
    "| Changed tooling/process/CI/governance surfaces | Tooling/process/CI | `bundle.tooling` |",
    "| Preparing/publishing release | Release/tag/distribution | `bundle.release` |",
]


def _extract_h2(text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"^##\s+(.+?)\s*$", text, re.MULTILINE)]


def _build_report() -> dict:
    if not AGENTS_PATH.exists():
        return {
            "command": "check_agents_contract",
            "ok": False,
            "error": f"Missing file: {AGENTS_PATH.relative_to(REPO_ROOT)}",
        }

    text = AGENTS_PATH.read_text(encoding="utf-8")
    h2 = _extract_h2(text)

    missing_h2 = [heading for heading in REQUIRED_H2 if heading not in h2]
    missing_bundles = [bundle for bundle in REQUIRED_BUNDLES if f"`{bundle}`" not in text]
    missing_markers = [marker for marker in REQUIRED_MARKERS if marker not in text]
    missing_router = [row for row in REQUIRED_ROUTER_SNIPPETS if row not in text]

    ok = not (missing_h2 or missing_bundles or missing_markers or missing_router)

    return {
        "command": "check_agents_contract",
        "ok": ok,
        "path": str(AGENTS_PATH.relative_to(REPO_ROOT)),
        "missing_h2": missing_h2,
        "missing_bundles": missing_bundles,
        "missing_markers": missing_markers,
        "missing_router_rows": missing_router,
    }


def _render_md(report: dict) -> str:
    lines = ["# check_agents_contract", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    if "error" in report:
        lines.append(f"- error: {report['error']}")
        return "\n".join(lines)

    lines.append(f"- path: {report['path']}")
    lines.append(
        "- missing_h2: " + (", ".join(report["missing_h2"]) if report["missing_h2"] else "none")
    )
    lines.append(
        "- missing_bundles: "
        + (", ".join(report["missing_bundles"]) if report["missing_bundles"] else "none")
    )
    lines.append(
        "- missing_markers: "
        + (", ".join(report["missing_markers"]) if report["missing_markers"] else "none")
    )
    lines.append(
        "- missing_router_rows: "
        + (", ".join(report["missing_router_rows"]) if report["missing_router_rows"] else "none")
    )
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
