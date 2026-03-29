"""Runtime evaluation helpers for docs-check."""

from __future__ import annotations

from dataclasses import dataclass

from ...time_utils import utc_timestamp
from .policy_runtime import (
    is_tooling_change,
    requires_evolution_update,
    resolve_tooling_doc_requirements,
)


@dataclass(frozen=True, slots=True)
class DocsEvaluationInput:
    """Typed inputs used to evaluate docs-governance state."""

    changed: set[str]
    user_facing: bool
    strict: bool
    strict_tooling: bool
    policy_path: str | None
    user_docs: list[str]
    tooling_required_docs: list[str]
    evolution_doc: str
    empty_commit_range: bool
    deprecated_violations: list[dict]


@dataclass(frozen=True, slots=True)
class DocsEvaluation:
    """Evaluated docs-governance state derived from changed paths."""

    changelog_updated: bool
    deprecated_ok: bool
    evolution_policy_ok: bool
    evolution_relevant_changes: list[str]
    evolution_updated: bool
    matched_tooling_doc_requirement_rules: list[str]
    missing_docs: list[str]
    missing_tooling_docs: list[str]
    missing_triggered_tooling_docs: list[str]
    tooling_changes_detected: list[str]
    tooling_policy_ok: bool
    triggered_tooling_doc_policy_ok: bool
    triggered_tooling_required_docs: list[str]
    updated_docs: list[str]
    updated_tooling_docs: list[str]
    updated_triggered_tooling_docs: list[str]
    user_facing_enabled: bool
    user_facing_ok: bool


@dataclass(frozen=True, slots=True)
class StrictToolingGateFns:
    """Strict-tooling gate callables injected from docs_check.py."""

    active_plan_sync_fn: object
    multi_agent_sync_fn: object
    legacy_path_audit_fn: object
    markdown_metadata_header_fn: object
    workflow_shell_hygiene_fn: object
    bundle_workflow_parity_fn: object
    agents_bundle_render_fn: object
    guide_contract_sync_fn: object
    instruction_surface_sync_fn: object


@dataclass(frozen=True, slots=True)
class StrictToolingGateState:
    """Reports and booleans returned by strict-tooling guard fan-out."""

    active_plan_sync_ok: bool = True
    active_plan_sync_report: dict | None = None
    agents_bundle_render_ok: bool = True
    agents_bundle_render_report: dict | None = None
    guide_contract_sync_ok: bool = True
    guide_contract_sync_report: dict | None = None
    instruction_surface_sync_ok: bool = True
    instruction_surface_sync_report: dict | None = None
    bundle_workflow_parity_ok: bool = True
    bundle_workflow_parity_report: dict | None = None
    legacy_path_audit_ok: bool = True
    legacy_path_audit_report: dict | None = None
    markdown_metadata_header_ok: bool = True
    markdown_metadata_header_report: dict | None = None
    multi_agent_sync_ok: bool = True
    multi_agent_sync_report: dict | None = None
    workflow_shell_hygiene_ok: bool = True
    workflow_shell_hygiene_report: dict | None = None


@dataclass(frozen=True, slots=True)
class DocsReportPayloadInput:
    """Typed inputs for the final docs-check payload builder."""

    args: object
    docs_policy: object
    since_ref: str | None
    head_ref: str
    empty_commit_range: bool
    evaluation: DocsEvaluation
    gate_state: StrictToolingGateState
    deprecated_violations: list[dict]
    failure_reasons: list[str]
    next_actions: list[str]
    evolution_doc: str


def evaluate_docs_state(context: DocsEvaluationInput) -> DocsEvaluation:
    """Evaluate docs-governance state from the changed path set."""
    updated_docs = [doc for doc in context.user_docs if doc in context.changed]
    changelog_updated = "dev/CHANGELOG.md" in context.changed
    missing_docs = [doc for doc in context.user_docs if doc not in context.changed]

    user_facing_enabled = context.user_facing and not context.empty_commit_range
    user_facing_ok = True
    if user_facing_enabled:
        if not changelog_updated:
            user_facing_ok = False
        elif context.strict and missing_docs:
            user_facing_ok = False
        elif not context.strict and not updated_docs:
            user_facing_ok = False

    tooling_changes_detected = sorted(
        path
        for path in context.changed
        if is_tooling_change(path, policy_path=context.policy_path)
    )
    matched_rules, triggered_tooling_required_docs = resolve_tooling_doc_requirements(
        tooling_changes_detected,
        policy_path=context.policy_path,
    )
    updated_tooling_docs = [
        doc for doc in context.tooling_required_docs if doc in context.changed
    ]
    missing_tooling_docs = [
        doc for doc in context.tooling_required_docs if doc not in context.changed
    ]
    updated_triggered_tooling_docs = [
        doc for doc in triggered_tooling_required_docs if doc in context.changed
    ]
    missing_triggered_tooling_docs = [
        doc for doc in triggered_tooling_required_docs if doc not in context.changed
    ]

    evolution_relevant_changes = sorted(
        path
        for path in context.changed
        if requires_evolution_update(path, policy_path=context.policy_path)
    )
    evolution_updated = context.evolution_doc in context.changed

    tooling_policy_ok = True
    if tooling_changes_detected:
        tooling_policy_ok = (
            not missing_tooling_docs
            if context.strict_tooling
            else bool(updated_tooling_docs)
        )

    return DocsEvaluation(
        changelog_updated=changelog_updated,
        deprecated_ok=not context.deprecated_violations,
        evolution_policy_ok=not (
            context.strict_tooling
            and evolution_relevant_changes
            and not evolution_updated
        ),
        evolution_relevant_changes=evolution_relevant_changes,
        evolution_updated=evolution_updated,
        matched_tooling_doc_requirement_rules=list(matched_rules),
        missing_docs=missing_docs,
        missing_tooling_docs=missing_tooling_docs,
        missing_triggered_tooling_docs=missing_triggered_tooling_docs,
        tooling_changes_detected=tooling_changes_detected,
        tooling_policy_ok=tooling_policy_ok,
        triggered_tooling_doc_policy_ok=not missing_triggered_tooling_docs,
        triggered_tooling_required_docs=list(triggered_tooling_required_docs),
        updated_docs=updated_docs,
        updated_tooling_docs=updated_tooling_docs,
        updated_triggered_tooling_docs=updated_triggered_tooling_docs,
        user_facing_enabled=user_facing_enabled,
        user_facing_ok=user_facing_ok,
    )


def collect_strict_tooling_gates(
    gate_fns: StrictToolingGateFns,
    *,
    strict_tooling: bool,
) -> StrictToolingGateState:
    """Run strict tooling gates and return reports plus status flags."""
    if not strict_tooling:
        return StrictToolingGateState()

    active_plan_sync_report = gate_fns.active_plan_sync_fn()
    multi_agent_sync_report = gate_fns.multi_agent_sync_fn()
    legacy_path_audit_report = gate_fns.legacy_path_audit_fn()
    markdown_metadata_header_report = gate_fns.markdown_metadata_header_fn()
    workflow_shell_hygiene_report = gate_fns.workflow_shell_hygiene_fn()
    bundle_workflow_parity_report = gate_fns.bundle_workflow_parity_fn()
    agents_bundle_render_report = gate_fns.agents_bundle_render_fn()
    guide_contract_sync_report = gate_fns.guide_contract_sync_fn()
    instruction_surface_sync_report = gate_fns.instruction_surface_sync_fn()
    return StrictToolingGateState(
        active_plan_sync_ok=bool(active_plan_sync_report.get("ok", False)),
        active_plan_sync_report=active_plan_sync_report,
        agents_bundle_render_ok=bool(agents_bundle_render_report.get("ok", False)),
        agents_bundle_render_report=agents_bundle_render_report,
        guide_contract_sync_ok=bool(guide_contract_sync_report.get("ok", False)),
        guide_contract_sync_report=guide_contract_sync_report,
        instruction_surface_sync_ok=bool(
            instruction_surface_sync_report.get("ok", False)
        ),
        instruction_surface_sync_report=instruction_surface_sync_report,
        bundle_workflow_parity_ok=bool(bundle_workflow_parity_report.get("ok", False)),
        bundle_workflow_parity_report=bundle_workflow_parity_report,
        legacy_path_audit_ok=bool(legacy_path_audit_report.get("ok", False)),
        legacy_path_audit_report=legacy_path_audit_report,
        markdown_metadata_header_ok=bool(
            markdown_metadata_header_report.get("ok", False)
        ),
        markdown_metadata_header_report=markdown_metadata_header_report,
        multi_agent_sync_ok=bool(multi_agent_sync_report.get("ok", False)),
        multi_agent_sync_report=multi_agent_sync_report,
        workflow_shell_hygiene_ok=bool(
            workflow_shell_hygiene_report.get("ok", False)
        ),
        workflow_shell_hygiene_report=workflow_shell_hygiene_report,
    )


def build_report_payload(context: DocsReportPayloadInput) -> dict:
    """Build the serializable docs-check report payload."""
    args = context.args
    docs_policy = context.docs_policy
    evaluation = context.evaluation
    gate_state = context.gate_state
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
            "empty_commit_range": context.empty_commit_range,
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
            "triggered_tooling_required_docs": evaluation.triggered_tooling_required_docs,
        }
    )
    payload.update(
        {
            "updated_triggered_tooling_docs": evaluation.updated_triggered_tooling_docs,
            "missing_triggered_tooling_docs": evaluation.missing_triggered_tooling_docs,
            "triggered_tooling_doc_policy_ok": evaluation.triggered_tooling_doc_policy_ok,
            "evolution_doc": context.evolution_doc,
            "evolution_relevant_changes": evaluation.evolution_relevant_changes,
        }
    )
    payload.update(
        {
            "evolution_updated": evaluation.evolution_updated,
            "evolution_policy_ok": evaluation.evolution_policy_ok,
            "active_plan_sync_ok": gate_state.active_plan_sync_ok,
            "active_plan_sync_report": gate_state.active_plan_sync_report,
            "multi_agent_sync_ok": gate_state.multi_agent_sync_ok,
        }
    )
    payload.update(
        {
            "multi_agent_sync_report": gate_state.multi_agent_sync_report,
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
            "agents_bundle_render_ok": gate_state.agents_bundle_render_ok,
        }
    )
    payload.update(
        {
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
        }
    )
    payload.update(
        {
            "deprecated_reference_violations": context.deprecated_violations,
            "failure_reasons": context.failure_reasons,
            "next_actions": context.next_actions,
        }
    )
    payload["ok"] = ok
    return payload
