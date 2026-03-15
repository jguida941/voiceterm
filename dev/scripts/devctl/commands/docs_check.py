"""devctl docs-check command implementation."""

from __future__ import annotations

import json

from ..collect import collect_git_status
from ..common import emit_output, pipe_output, write_output
from ..time_utils import utc_timestamp
from ..config import REPO_ROOT
from ..path_audit import scan_legacy_path_references
from ..policy_gate import run_json_policy_gate
from ..script_catalog import check_script_path
from .docs.check_runtime import (
    DocsEvaluationInput,
    DocsReportPayloadInput,
    StrictToolingGateFns,
    build_report_payload,
    collect_strict_tooling_gates,
    evaluate_docs_state,
)
from .docs_check_policy import (
    resolve_docs_check_policy,
)
from .docs_check_render import render_markdown_report
from .docs_check_support import (
    build_failure_reasons,
    build_next_actions,
    scan_deprecated_references,
)

ACTIVE_PLAN_SYNC_SCRIPT = check_script_path("active_plan_sync")
MULTI_AGENT_SYNC_SCRIPT = check_script_path("multi_agent_sync")
MARKDOWN_METADATA_HEADER_SCRIPT = check_script_path("markdown_metadata_header")
WORKFLOW_SHELL_HYGIENE_SCRIPT = check_script_path("workflow_shell_hygiene")
BUNDLE_WORKFLOW_PARITY_SCRIPT = check_script_path("bundle_workflow_parity")
AGENTS_BUNDLE_RENDER_SCRIPT = check_script_path("agents_bundle_render")
INSTRUCTION_SURFACE_SYNC_SCRIPT = check_script_path("instruction_surface_sync")


def _scan_deprecated_references(*, policy_path: str | None = None) -> list[dict]:
    """Wrapper kept for unit-test patch stability."""
    return scan_deprecated_references(REPO_ROOT, policy_path=policy_path)


def _run_active_plan_sync_gate() -> dict:
    """Run active-plan sync guard and return parsed JSON report."""
    return run_json_policy_gate(ACTIVE_PLAN_SYNC_SCRIPT, "active-plan sync gate")


def _run_multi_agent_sync_gate() -> dict:
    """Run multi-agent board/runbook sync guard and return parsed JSON report."""
    return run_json_policy_gate(MULTI_AGENT_SYNC_SCRIPT, "multi-agent sync gate")


def run_markdown_metadata_header_gate() -> dict:
    """Run markdown metadata-header style guard and return parsed JSON report."""
    return run_json_policy_gate(
        MARKDOWN_METADATA_HEADER_SCRIPT,
        "markdown metadata header gate",
    )


_run_markdown_metadata_header_gate = run_markdown_metadata_header_gate


def run_workflow_shell_hygiene_gate() -> dict:
    """Run workflow-shell hygiene guard and return parsed JSON report."""
    return run_json_policy_gate(
        WORKFLOW_SHELL_HYGIENE_SCRIPT,
        "workflow shell hygiene gate",
    )


_run_workflow_shell_hygiene_gate = run_workflow_shell_hygiene_gate


def run_bundle_workflow_parity_gate() -> dict:
    """Run bundle/workflow parity guard and return parsed JSON report."""
    return run_json_policy_gate(
        BUNDLE_WORKFLOW_PARITY_SCRIPT,
        "bundle/workflow parity gate",
    )


_run_bundle_workflow_parity_gate = run_bundle_workflow_parity_gate


def run_agents_bundle_render_gate() -> dict:
    """Run AGENTS bundle render guard and return parsed JSON report."""
    return run_json_policy_gate(
        AGENTS_BUNDLE_RENDER_SCRIPT,
        "AGENTS bundle render gate",
    )


_run_agents_bundle_render_gate = run_agents_bundle_render_gate


def run_instruction_surface_sync_gate() -> dict:
    """Run instruction-surface sync guard and return parsed JSON report."""
    return run_json_policy_gate(
        INSTRUCTION_SURFACE_SYNC_SCRIPT,
        "instruction surface sync gate",
    )


_run_instruction_surface_sync_gate = run_instruction_surface_sync_gate


def run(args) -> int:
    """Check docs coverage and maintainer tooling policy alignment."""
    since_ref = getattr(args, "since_ref", None)
    head_ref = getattr(args, "head_ref", "HEAD")
    policy_path = getattr(args, "quality_policy", None)
    docs_policy = resolve_docs_check_policy(policy_path=policy_path)
    user_docs = list(docs_policy.user_docs)
    tooling_required_docs = list(docs_policy.tooling_required_docs)
    evolution_doc = docs_policy.evolution_doc
    git_info = collect_git_status(since_ref, head_ref)
    if "error" in git_info:
        output = json.dumps({"error": git_info["error"]}, indent=2)
        emit_output(
            output,
            output_path=args.output,
            pipe_command=None,
            pipe_args=None,
            writer=write_output,
            piper=pipe_output,
        )
        return 2

    changed = {entry["path"] for entry in git_info.get("changes", [])}
    empty_commit_range = bool(since_ref and not changed)
    strict_tooling = getattr(args, "strict_tooling", False)

    deprecated_violations = _scan_deprecated_references(policy_path=policy_path)
    evaluation = evaluate_docs_state(
        DocsEvaluationInput(
            changed=changed,
            user_facing=args.user_facing,
            strict=args.strict,
            strict_tooling=strict_tooling,
            policy_path=policy_path,
            user_docs=user_docs,
            tooling_required_docs=tooling_required_docs,
            evolution_doc=evolution_doc,
            empty_commit_range=empty_commit_range,
            deprecated_violations=deprecated_violations,
        )
    )
    gate_state = collect_strict_tooling_gates(
        StrictToolingGateFns(
            active_plan_sync_fn=_run_active_plan_sync_gate,
            multi_agent_sync_fn=_run_multi_agent_sync_gate,
            legacy_path_audit_fn=scan_legacy_path_references,
            markdown_metadata_header_fn=_run_markdown_metadata_header_gate,
            workflow_shell_hygiene_fn=_run_workflow_shell_hygiene_gate,
            bundle_workflow_parity_fn=_run_bundle_workflow_parity_gate,
            agents_bundle_render_fn=_run_agents_bundle_render_gate,
            instruction_surface_sync_fn=_run_instruction_surface_sync_gate,
        ),
        strict_tooling=strict_tooling,
    )
    failure_reasons = build_failure_reasons(
        user_facing_enabled=evaluation.user_facing_enabled,
        strict_user_docs=args.strict,
        changelog_updated=evaluation.changelog_updated,
        updated_docs=evaluation.updated_docs,
        missing_docs=evaluation.missing_docs,
        tooling_changes_detected=evaluation.tooling_changes_detected,
        updated_tooling_docs=evaluation.updated_tooling_docs,
        strict_tooling=strict_tooling,
        missing_tooling_docs=evaluation.missing_tooling_docs,
        matched_tooling_doc_requirement_rules=evaluation.matched_tooling_doc_requirement_rules,
        missing_triggered_tooling_docs=evaluation.missing_triggered_tooling_docs,
        evolution_relevant_changes=evaluation.evolution_relevant_changes,
        evolution_policy_ok=evaluation.evolution_policy_ok,
        active_plan_sync_ok=gate_state.active_plan_sync_ok,
        active_plan_sync_report=gate_state.active_plan_sync_report,
        multi_agent_sync_ok=gate_state.multi_agent_sync_ok,
        multi_agent_sync_report=gate_state.multi_agent_sync_report,
        legacy_path_audit_ok=gate_state.legacy_path_audit_ok,
        legacy_path_audit_report=gate_state.legacy_path_audit_report,
        markdown_metadata_header_ok=gate_state.markdown_metadata_header_ok,
        markdown_metadata_header_report=gate_state.markdown_metadata_header_report,
        workflow_shell_hygiene_ok=gate_state.workflow_shell_hygiene_ok,
        workflow_shell_hygiene_report=gate_state.workflow_shell_hygiene_report,
        bundle_workflow_parity_ok=gate_state.bundle_workflow_parity_ok,
        bundle_workflow_parity_report=gate_state.bundle_workflow_parity_report,
        agents_bundle_render_ok=gate_state.agents_bundle_render_ok,
        agents_bundle_render_report=gate_state.agents_bundle_render_report,
        instruction_surface_sync_ok=gate_state.instruction_surface_sync_ok,
        instruction_surface_sync_report=gate_state.instruction_surface_sync_report,
        deprecated_violations=deprecated_violations,
        user_docs=user_docs,
        tooling_required_docs=tooling_required_docs,
        evolution_doc=evolution_doc,
    )
    next_actions = build_next_actions(
        failure_reasons=failure_reasons,
        user_facing_enabled=evaluation.user_facing_enabled,
        strict_user_docs=args.strict,
        missing_docs=evaluation.missing_docs,
        tooling_changes_detected=evaluation.tooling_changes_detected,
        strict_tooling=strict_tooling,
        missing_tooling_docs=evaluation.missing_tooling_docs,
        matched_tooling_doc_requirement_rules=evaluation.matched_tooling_doc_requirement_rules,
        missing_triggered_tooling_docs=evaluation.missing_triggered_tooling_docs,
        evolution_relevant_changes=evaluation.evolution_relevant_changes,
        evolution_policy_ok=evaluation.evolution_policy_ok,
        active_plan_sync_ok=gate_state.active_plan_sync_ok,
        multi_agent_sync_ok=gate_state.multi_agent_sync_ok,
        legacy_path_audit_ok=gate_state.legacy_path_audit_ok,
        markdown_metadata_header_ok=gate_state.markdown_metadata_header_ok,
        workflow_shell_hygiene_ok=gate_state.workflow_shell_hygiene_ok,
        bundle_workflow_parity_ok=gate_state.bundle_workflow_parity_ok,
        agents_bundle_render_ok=gate_state.agents_bundle_render_ok,
        instruction_surface_sync_ok=gate_state.instruction_surface_sync_ok,
        deprecated_violations=deprecated_violations,
        user_docs=user_docs,
        evolution_doc=evolution_doc,
    )
    report = build_report_payload(
        DocsReportPayloadInput(
            args=args,
            docs_policy=docs_policy,
            since_ref=since_ref,
            head_ref=head_ref,
            empty_commit_range=empty_commit_range,
            evaluation=evaluation,
            gate_state=gate_state,
            deprecated_violations=deprecated_violations,
            failure_reasons=failure_reasons,
            next_actions=next_actions,
            evolution_doc=evolution_doc,
        )
    )

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = render_markdown_report(report)

    return_code = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    if return_code != 0:
        return return_code
    return 0 if report["ok"] else 1
