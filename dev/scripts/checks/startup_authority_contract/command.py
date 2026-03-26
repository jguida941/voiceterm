#!/usr/bin/env python3
"""Validate startup-authority invariants from the live ProjectGovernance payload.

Ensures that the repo-configured bootstrap authority files exist, required
path roots resolve, and repo identity / plan registry fields are populated.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runtime_checks import (
    collect_checkpoint_budget_errors,
    collect_import_index_atomicity_findings,
    collect_push_decision_contract_errors,
    collect_reviewer_loop_block_errors,
)

try:
    from check_bootstrap import REPO_ROOT, import_repo_module
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, import_repo_module

_COMMAND = "check_startup_authority_contract"

# Canonical startup authority files (relative to repo root).
def _build_report(repo_root: Path | None = None) -> dict:
    root = repo_root or REPO_ROOT
    draft_mod = import_repo_module(
        "dev.scripts.devctl.governance.draft", repo_root=root,
    )
    scan_repo_governance = draft_mod.scan_repo_governance

    gov = scan_repo_governance(root)

    errors: list[str] = []
    warnings: list[str] = []
    checks_run = 0
    checks_passed = 0

    startup_authority = gov.docs_authority
    plan_registry = gov.plan_registry.registry_path
    plan_tracker = gov.plan_registry.tracker_path

    # --- 1. Startup authority file exists ---
    checks_run += 1
    if startup_authority and (root / startup_authority).is_file():
        checks_passed += 1
    else:
        errors.append(
            "Missing startup authority file: "
            f"{startup_authority or '(unconfigured)'}"
        )

    # --- 2. Active-plan registry file exists ---
    checks_run += 1
    if plan_registry and (root / plan_registry).is_file():
        checks_passed += 1
    else:
        errors.append(
            "Missing active-plan registry: "
            f"{plan_registry or '(unconfigured)'}"
        )

    # --- 3. Plan tracker file exists ---
    checks_run += 1
    if plan_tracker and (root / plan_tracker).is_file():
        checks_passed += 1
    else:
        errors.append(
            f"Missing plan tracker: {plan_tracker or '(unconfigured)'}"
        )

    # --- 4. Path roots: active_docs and scripts must resolve to directories ---
    checks_run += 1
    if gov.path_roots.active_docs and (root / gov.path_roots.active_docs).is_dir():
        checks_passed += 1
    else:
        errors.append(
            "path_roots.active_docs is missing or not a directory "
            f"({gov.path_roots.active_docs or '(unconfigured)'})"
        )

    checks_run += 1
    if gov.path_roots.scripts and (root / gov.path_roots.scripts).is_dir():
        checks_passed += 1
    else:
        errors.append(
            "path_roots.scripts is missing or not a directory "
            f"({gov.path_roots.scripts or '(unconfigured)'})"
        )

    # --- 5. repo_identity.repo_name is non-empty ---
    checks_run += 1
    if gov.repo_identity.repo_name:
        checks_passed += 1
    else:
        errors.append("repo_identity.repo_name is empty")

    # --- 6. plan_registry.registry_path is configured ---
    checks_run += 1
    if gov.plan_registry.registry_path:
        checks_passed += 1
    else:
        errors.append("plan_registry.registry_path is empty (INDEX.md not found)")

    # --- 7. plan_registry.tracker_path is configured ---
    checks_run += 1
    if gov.plan_registry.tracker_path:
        checks_passed += 1
    else:
        errors.append("plan_registry.tracker_path is empty (MASTER_PLAN.md not found)")

    # --- 8. checkpoint budget is fail-closed for startup authority ---
    checks_run += 1
    checkpoint_errors = collect_checkpoint_budget_errors(gov)
    if checkpoint_errors:
        errors.extend(checkpoint_errors)
    else:
        checks_passed += 1

    # --- 9. active reviewer loop cannot start a fresh implementation slice when stale ---
    checks_run += 1
    reviewer_loop_errors = collect_reviewer_loop_block_errors(root, gov)
    if reviewer_loop_errors:
        errors.extend(reviewer_loop_errors)
    else:
        checks_passed += 1

    # --- 10. repo-local Python imports resolve in the git index, not only on disk ---
    checks_run += 1
    import_atomicity_errors, import_atomicity_warnings = (
        collect_import_index_atomicity_findings(root)
    )
    warnings.extend(import_atomicity_warnings)
    if import_atomicity_errors:
        errors.extend(import_atomicity_errors)
    else:
        checks_passed += 1

    # --- 11. startup push decision must emit a coherent next-step contract ---
    checks_run += 1
    push_contract_errors = collect_push_decision_contract_errors(root, gov)
    if push_contract_errors:
        errors.extend(push_contract_errors)
    else:
        checks_passed += 1

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
        "checkpoint_required": gov.push_enforcement.checkpoint_required,
        "safe_to_continue_editing": gov.push_enforcement.safe_to_continue_editing,
        "checkpoint_reason": gov.push_enforcement.checkpoint_reason,
        "reviewer_loop_blocked": bool(reviewer_loop_errors),
        "import_index_atomicity_violations": len(import_atomicity_errors),
    }


def _render_md(report: dict) -> str:
    lines = [f"# {_COMMAND}", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- checks: {report['checks_passed']}/{report['checks_run']}")
    lines.append(f"- repo_name: {report['repo_name']}")
    lines.append(f"- startup_order: {', '.join(report['startup_order']) or '(none)'}")
    lines.append(f"- checkpoint_required: {report['checkpoint_required']}")
    lines.append(
        f"- safe_to_continue_editing: {report['safe_to_continue_editing']}"
    )
    lines.append(f"- checkpoint_reason: {report['checkpoint_reason']}")
    lines.append(
        "- import_index_atomicity_violations: "
        f"{report['import_index_atomicity_violations']}"
    )
    lines.append(f"- reviewer_loop_blocked: {report['reviewer_loop_blocked']}")
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
