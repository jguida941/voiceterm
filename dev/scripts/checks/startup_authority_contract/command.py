#!/usr/bin/env python3
"""Validate startup-authority invariants from the live ProjectGovernance payload.

Ensures that the three bootstrap authority files exist, required path roots
are populated, and repo identity / plan registry fields are non-empty.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, import_repo_module
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, import_repo_module

_COMMAND = "check_startup_authority_contract"

# Canonical startup authority files (relative to repo root).
_STARTUP_AUTHORITY = "AGENTS.md"
_PLAN_REGISTRY = "dev/active/INDEX.md"
_PLAN_TRACKER = "dev/active/MASTER_PLAN.md"


def _build_report(repo_root: Path | None = None) -> dict:
    root = repo_root or REPO_ROOT
    draft_mod = import_repo_module(
        "dev.scripts.devctl.governance.draft", repo_root=root,
    )
    scan_repo_governance = draft_mod.scan_repo_governance

    gov = scan_repo_governance(root, policy={})

    errors: list[str] = []
    warnings: list[str] = []
    checks_run = 0
    checks_passed = 0

    # --- 1. Startup authority file exists ---
    checks_run += 1
    if (root / _STARTUP_AUTHORITY).is_file():
        checks_passed += 1
    else:
        errors.append(f"Missing startup authority file: {_STARTUP_AUTHORITY}")

    # --- 2. Active-plan registry file exists ---
    checks_run += 1
    if (root / _PLAN_REGISTRY).is_file():
        checks_passed += 1
    else:
        errors.append(f"Missing active-plan registry: {_PLAN_REGISTRY}")

    # --- 3. Plan tracker file exists ---
    checks_run += 1
    if (root / _PLAN_TRACKER).is_file():
        checks_passed += 1
    else:
        errors.append(f"Missing plan tracker: {_PLAN_TRACKER}")

    # --- 4. Path roots: active_docs and scripts must be non-empty ---
    checks_run += 1
    if gov.path_roots.active_docs:
        checks_passed += 1
    else:
        errors.append("path_roots.active_docs is empty (directory missing)")

    checks_run += 1
    if gov.path_roots.scripts:
        checks_passed += 1
    else:
        errors.append("path_roots.scripts is empty (directory missing)")

    # --- 5. repo_identity.repo_name is non-empty ---
    checks_run += 1
    if gov.repo_identity.repo_name:
        checks_passed += 1
    else:
        errors.append("repo_identity.repo_name is empty")

    # --- 6. plan_registry.registry_path is non-empty ---
    checks_run += 1
    if gov.plan_registry.registry_path:
        checks_passed += 1
    else:
        errors.append("plan_registry.registry_path is empty (INDEX.md not found)")

    # --- 7. plan_registry.tracker_path is non-empty ---
    checks_run += 1
    if gov.plan_registry.tracker_path:
        checks_passed += 1
    else:
        errors.append("plan_registry.tracker_path is empty (MASTER_PLAN.md not found)")

    ok = len(errors) == 0
    return {
        "command": _COMMAND,
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
        "checks_run": checks_run,
        "checks_passed": checks_passed,
        "repo_name": gov.repo_identity.repo_name,
        "startup_order": list(gov.startup_order),
    }


def _render_md(report: dict) -> str:
    lines = [f"# {_COMMAND}", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- checks: {report['checks_passed']}/{report['checks_run']}")
    lines.append(f"- repo_name: {report['repo_name']}")
    lines.append(f"- startup_order: {', '.join(report['startup_order']) or '(none)'}")
    if report["errors"]:
        lines.append("")
        lines.append("## Errors")
        for err in report["errors"]:
            lines.append(f"- {err}")
    if report["warnings"]:
        lines.append("")
        lines.append("## Warnings")
        for warn in report["warnings"]:
            lines.append(f"- {warn}")
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

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
