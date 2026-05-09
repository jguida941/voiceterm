"""Docs-check report payload assembly."""

from __future__ import annotations

from ...runtime.validation_scope import validation_scope_from_args
from ...time_utils import utc_timestamp
from .check_runtime import DocsReportPayloadInput
from .check_validation_scope import pipeline_authorized_advisory_gates


def build_report_payload(context: DocsReportPayloadInput) -> dict:
    """Build the serializable docs-check report payload."""
    args = context.args
    docs_policy = context.docs_policy
    evaluation = context.evaluation
    gate_state = context.gate_state
    validation_scope = validation_scope_from_args(args)
    ok = (
        evaluation.user_facing_ok
        and evaluation.tooling_policy_ok
        and evaluation.triggered_tooling_doc_policy_ok
        and evaluation.evolution_policy_ok
        and evaluation.deprecated_ok
        and gate_state.active_plan_sync_ok
        and gate_state.multi_agent_sync_ok
        and gate_state.legacy_path_audit_ok
        and gate_state.markdown_metadata_header_ok
        and gate_state.workflow_shell_hygiene_ok
        and gate_state.bundle_workflow_parity_ok
        and gate_state.agents_bundle_render_ok
        and gate_state.guide_contract_sync_ok
        and gate_state.instruction_surface_sync_ok
    )
    payload = {
        "command": "docs-check",
        "timestamp": utc_timestamp(),
        "policy_path": docs_policy.policy_path,
        "policy_warnings": list(docs_policy.warnings),
        "since_ref": context.since_ref,
    }
    payload.update(
        {
            "head_ref": context.head_ref,
            "user_facing": args.user_facing,
            "strict": args.strict,
            "strict_tooling": getattr(args, "strict_tooling", False),
        }
    )
    payload.update(
        {
            "empty_commit_range": context.empty_commit_range,
            "validation_scope": validation_scope.to_dict(),
            "pipeline_authorized_advisory_gates": pipeline_authorized_advisory_gates(
                validation_scope
            ),
        }
    )
    payload.update(
        {
            "changelog_updated": evaluation.changelog_updated,
            "user_facing_ok": evaluation.user_facing_ok,
            "updated_docs": evaluation.updated_docs,
            "missing_docs": evaluation.missing_docs,
            "tooling_changes_detected": evaluation.tooling_changes_detected,
        }
    )
    payload.update(
        {
            "updated_tooling_docs": evaluation.updated_tooling_docs,
            "missing_tooling_docs": evaluation.missing_tooling_docs,
            "tooling_policy_ok": evaluation.tooling_policy_ok,
            "matched_tooling_doc_requirement_rules": evaluation.matched_tooling_doc_requirement_rules,
        }
    )
    payload.update(
        {
            "triggered_tooling_required_docs": evaluation.triggered_tooling_required_docs,
            "updated_triggered_tooling_docs": evaluation.updated_triggered_tooling_docs,
            "missing_triggered_tooling_docs": evaluation.missing_triggered_tooling_docs,
            "triggered_tooling_doc_policy_ok": evaluation.triggered_tooling_doc_policy_ok,
        }
    )
    payload.update(
        {
            "evolution_doc": context.evolution_doc,
            "evolution_relevant_changes": evaluation.evolution_relevant_changes,
            "evolution_updated": evaluation.evolution_updated,
            "evolution_policy_ok": evaluation.evolution_policy_ok,
        }
    )
    payload.update(
        {
            "active_plan_sync_ok": gate_state.active_plan_sync_ok,
            "active_plan_sync_report": gate_state.active_plan_sync_report,
            "multi_agent_sync_ok": gate_state.multi_agent_sync_ok,
            "multi_agent_sync_report": gate_state.multi_agent_sync_report,
        }
    )
    payload.update(
        {
            "legacy_path_audit_ok": gate_state.legacy_path_audit_ok,
            "legacy_path_audit_report": gate_state.legacy_path_audit_report,
            "markdown_metadata_header_ok": gate_state.markdown_metadata_header_ok,
            "markdown_metadata_header_report": gate_state.markdown_metadata_header_report,
        }
    )
    payload.update(
        {
            "workflow_shell_hygiene_ok": gate_state.workflow_shell_hygiene_ok,
            "workflow_shell_hygiene_report": gate_state.workflow_shell_hygiene_report,
            "bundle_workflow_parity_ok": gate_state.bundle_workflow_parity_ok,
            "bundle_workflow_parity_report": gate_state.bundle_workflow_parity_report,
        }
    )
    payload.update(
        {
            "agents_bundle_render_ok": gate_state.agents_bundle_render_ok,
            "agents_bundle_render_report": gate_state.agents_bundle_render_report,
            "guide_contract_sync_ok": gate_state.guide_contract_sync_ok,
            "guide_contract_sync_report": gate_state.guide_contract_sync_report,
        }
    )
    payload.update(
        {
            "instruction_surface_sync_ok": gate_state.instruction_surface_sync_ok,
            "instruction_surface_sync_report": gate_state.instruction_surface_sync_report,
            "deprecated_reference_ok": evaluation.deprecated_ok,
            "deprecated_reference_violations": context.deprecated_violations,
        }
    )
    payload.update(
        {
            "failure_reasons": context.failure_reasons,
            "next_actions": context.next_actions,
        }
    )
    payload["ok"] = ok
    return payload


__all__ = ["build_report_payload"]
