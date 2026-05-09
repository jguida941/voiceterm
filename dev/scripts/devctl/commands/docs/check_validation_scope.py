"""Validation-scope helpers for docs-check live gates."""

from __future__ import annotations

from typing import Any

from ...runtime.validation_scope import ValidationScope

PIPELINE_AUTHORIZED_ADVISORY_GATES = frozenset(
    {
        "active_plan_sync",
        "multi_agent_sync",
        "instruction_surface_sync",
    }
)


def validation_scope_args(
    validation_scope: ValidationScope | None,
) -> tuple[str, ...]:
    if validation_scope is None or not validation_scope.pipeline_authorized:
        return ()
    return ("--validation-scope", validation_scope.kind.value)


def pipeline_authorized_advisory_gates(
    validation_scope: ValidationScope,
) -> list[str]:
    if not validation_scope.pipeline_authorized:
        return []
    return sorted(PIPELINE_AUTHORIZED_ADVISORY_GATES)


def scope_pipeline_authorized_gates(
    gate_state: Any,
    *,
    validation_scope: ValidationScope | None,
) -> Any:
    if validation_scope is None or not validation_scope.pipeline_authorized:
        return gate_state
    return type(gate_state)(
        active_plan_sync_ok=True,
        active_plan_sync_report=scope_gate_report(
            gate_state.active_plan_sync_report,
            gate_id="active_plan_sync",
            validation_scope=validation_scope,
        ),
        agents_bundle_render_ok=gate_state.agents_bundle_render_ok,
        agents_bundle_render_report=gate_state.agents_bundle_render_report,
        guide_contract_sync_ok=gate_state.guide_contract_sync_ok,
        guide_contract_sync_report=gate_state.guide_contract_sync_report,
        instruction_surface_sync_ok=True,
        instruction_surface_sync_report=scope_gate_report(
            gate_state.instruction_surface_sync_report,
            gate_id="instruction_surface_sync",
            validation_scope=validation_scope,
        ),
        bundle_workflow_parity_ok=gate_state.bundle_workflow_parity_ok,
        bundle_workflow_parity_report=gate_state.bundle_workflow_parity_report,
        legacy_path_audit_ok=gate_state.legacy_path_audit_ok,
        legacy_path_audit_report=gate_state.legacy_path_audit_report,
        markdown_metadata_header_ok=gate_state.markdown_metadata_header_ok,
        markdown_metadata_header_report=gate_state.markdown_metadata_header_report,
        multi_agent_sync_ok=True,
        multi_agent_sync_report=scope_gate_report(
            gate_state.multi_agent_sync_report,
            gate_id="multi_agent_sync",
            validation_scope=validation_scope,
        ),
        workflow_shell_hygiene_ok=gate_state.workflow_shell_hygiene_ok,
        workflow_shell_hygiene_report=gate_state.workflow_shell_hygiene_report,
    )


def scope_gate_report(
    report: dict | None,
    *,
    gate_id: str,
    validation_scope: ValidationScope,
) -> dict:
    scoped = dict(report or {})
    original_ok = bool(scoped.get("ok", False))
    scoped["live_worktree_ok"] = original_ok
    scoped["ok"] = True
    scoped["validation_scope"] = validation_scope.to_dict()
    scoped["pipeline_authorized_advisory_gate"] = gate_id
    scoped["pipeline_authorized_advisory_reason"] = (
        "live projection subgate is evidence only during governed "
        "pipeline publication validation"
    )
    if not original_ok:
        scoped["pipeline_scope_original_ok"] = False
        scoped["pipeline_scope_original_errors"] = list(scoped.get("errors") or ())
    return scoped


__all__ = [
    "PIPELINE_AUTHORIZED_ADVISORY_GATES",
    "pipeline_authorized_advisory_gates",
    "scope_gate_report",
    "scope_pipeline_authorized_gates",
    "validation_scope_args",
]
