"""devctl docs-check command implementation."""

from __future__ import annotations

import json
from datetime import datetime

from ..collect import collect_git_status
from ..common import pipe_output, write_output
from ..config import REPO_ROOT
from ..path_audit import scan_legacy_path_references
from ..policy_gate import run_json_policy_gate
from ..script_catalog import check_script_path
from .docs_check_render import render_markdown_report
from .docs_check_support import (
    EVOLUTION_DOC,
    TOOLING_REQUIRED_DOCS,
    USER_DOCS,
    build_failure_reasons,
    build_next_actions,
    is_tooling_change,
    requires_evolution_update,
    scan_deprecated_references,
)

ACTIVE_PLAN_SYNC_SCRIPT = check_script_path("active_plan_sync")
MULTI_AGENT_SYNC_SCRIPT = check_script_path("multi_agent_sync")

def _scan_deprecated_references() -> list[dict]:
    """Wrapper kept for unit-test patch stability."""
    return scan_deprecated_references(REPO_ROOT)


def _run_active_plan_sync_gate() -> dict:
    """Run active-plan sync guard and return parsed JSON report."""
    return run_json_policy_gate(ACTIVE_PLAN_SYNC_SCRIPT, "active-plan sync gate")


def _run_multi_agent_sync_gate() -> dict:
    """Run multi-agent board/runbook sync guard and return parsed JSON report."""
    return run_json_policy_gate(MULTI_AGENT_SYNC_SCRIPT, "multi-agent sync gate")


def run(args) -> int:
    """Check docs coverage and maintainer tooling policy alignment."""
    since_ref = getattr(args, "since_ref", None)
    head_ref = getattr(args, "head_ref", "HEAD")
    git_info = collect_git_status(since_ref, head_ref)
    if "error" in git_info:
        output = json.dumps({"error": git_info["error"]}, indent=2)
        write_output(output, args.output)
        return 2

    changed = {entry["path"] for entry in git_info.get("changes", [])}
    strict_tooling = getattr(args, "strict_tooling", False)

    updated_docs = [doc for doc in USER_DOCS if doc in changed]
    changelog_updated = "dev/CHANGELOG.md" in changed
    missing_docs = [doc for doc in USER_DOCS if doc not in changed]

    user_facing_ok = True
    if args.user_facing:
        if not changelog_updated:
            user_facing_ok = False
        if args.strict:
            if missing_docs:
                user_facing_ok = False
        elif not updated_docs:
            user_facing_ok = False

    tooling_changes_detected = sorted(path for path in changed if is_tooling_change(path))
    updated_tooling_docs = [doc for doc in TOOLING_REQUIRED_DOCS if doc in changed]
    missing_tooling_docs = [doc for doc in TOOLING_REQUIRED_DOCS if doc not in changed]
    evolution_relevant_changes = sorted(
        path for path in changed if requires_evolution_update(path)
    )
    evolution_updated = EVOLUTION_DOC in changed

    tooling_policy_ok = True
    if tooling_changes_detected:
        if strict_tooling:
            tooling_policy_ok = not missing_tooling_docs
        else:
            tooling_policy_ok = bool(updated_tooling_docs)

    evolution_policy_ok = True
    if strict_tooling and evolution_relevant_changes:
        evolution_policy_ok = evolution_updated

    deprecated_violations = _scan_deprecated_references()
    deprecated_ok = not deprecated_violations

    active_plan_sync_report = None
    active_plan_sync_ok = True
    multi_agent_sync_report = None
    multi_agent_sync_ok = True
    legacy_path_audit_report = None
    legacy_path_audit_ok = True
    if strict_tooling:
        active_plan_sync_report = _run_active_plan_sync_gate()
        active_plan_sync_ok = bool(active_plan_sync_report.get("ok", False))
        multi_agent_sync_report = _run_multi_agent_sync_gate()
        multi_agent_sync_ok = bool(multi_agent_sync_report.get("ok", False))
        legacy_path_audit_report = scan_legacy_path_references()
        legacy_path_audit_ok = bool(legacy_path_audit_report.get("ok", False))

    ok = (
        user_facing_ok
        and tooling_policy_ok
        and evolution_policy_ok
        and deprecated_ok
        and active_plan_sync_ok
        and multi_agent_sync_ok
        and legacy_path_audit_ok
    )
    failure_reasons = build_failure_reasons(
        user_facing_enabled=args.user_facing,
        strict_user_docs=args.strict,
        changelog_updated=changelog_updated,
        updated_docs=updated_docs,
        missing_docs=missing_docs,
        tooling_changes_detected=tooling_changes_detected,
        updated_tooling_docs=updated_tooling_docs,
        strict_tooling=strict_tooling,
        missing_tooling_docs=missing_tooling_docs,
        evolution_relevant_changes=evolution_relevant_changes,
        evolution_policy_ok=evolution_policy_ok,
        active_plan_sync_ok=active_plan_sync_ok,
        active_plan_sync_report=active_plan_sync_report,
        multi_agent_sync_ok=multi_agent_sync_ok,
        multi_agent_sync_report=multi_agent_sync_report,
        legacy_path_audit_ok=legacy_path_audit_ok,
        legacy_path_audit_report=legacy_path_audit_report,
        deprecated_violations=deprecated_violations,
    )
    next_actions = build_next_actions(
        failure_reasons=failure_reasons,
        user_facing_enabled=args.user_facing,
        strict_user_docs=args.strict,
        missing_docs=missing_docs,
        tooling_changes_detected=tooling_changes_detected,
        strict_tooling=strict_tooling,
        missing_tooling_docs=missing_tooling_docs,
        evolution_relevant_changes=evolution_relevant_changes,
        evolution_policy_ok=evolution_policy_ok,
        active_plan_sync_ok=active_plan_sync_ok,
        multi_agent_sync_ok=multi_agent_sync_ok,
        legacy_path_audit_ok=legacy_path_audit_ok,
        deprecated_violations=deprecated_violations,
    )

    report = {
        "command": "docs-check",
        "timestamp": datetime.now().isoformat(),
        "since_ref": since_ref,
        "head_ref": head_ref,
        "user_facing": args.user_facing,
        "strict": args.strict,
        "strict_tooling": strict_tooling,
        "changelog_updated": changelog_updated,
        "user_facing_ok": user_facing_ok,
        "updated_docs": updated_docs,
        "missing_docs": missing_docs,
        "tooling_changes_detected": tooling_changes_detected,
        "updated_tooling_docs": updated_tooling_docs,
        "missing_tooling_docs": missing_tooling_docs,
        "tooling_policy_ok": tooling_policy_ok,
        "evolution_doc": EVOLUTION_DOC,
        "evolution_relevant_changes": evolution_relevant_changes,
        "evolution_updated": evolution_updated,
        "evolution_policy_ok": evolution_policy_ok,
        "active_plan_sync_ok": active_plan_sync_ok,
        "active_plan_sync_report": active_plan_sync_report,
        "multi_agent_sync_ok": multi_agent_sync_ok,
        "multi_agent_sync_report": multi_agent_sync_report,
        "legacy_path_audit_ok": legacy_path_audit_ok,
        "legacy_path_audit_report": legacy_path_audit_report,
        "deprecated_reference_ok": deprecated_ok,
        "deprecated_reference_violations": deprecated_violations,
        "failure_reasons": failure_reasons,
        "next_actions": next_actions,
        "ok": ok,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = render_markdown_report(report)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0 if ok else 1
