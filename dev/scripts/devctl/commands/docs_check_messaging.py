"""Failure-reason and next-action builders for docs-check."""

from __future__ import annotations

from .docs.messaging_helpers import (
    ToolingDocReasonInputs,
    build_gate_reason,
    build_tooling_doc_reasons,
    build_user_doc_reasons,
    collect_gate_messages,
)
from .docs_check_policy import (
    ACTIVE_PLAN_SYNC_SCRIPT_REL,
    AGENTS_BUNDLE_RENDER_SCRIPT_REL,
    BUNDLE_WORKFLOW_PARITY_SCRIPT_REL,
    EVOLUTION_DOC,
    GUIDE_CONTRACT_SYNC_SCRIPT_REL,
    INSTRUCTION_SURFACE_SYNC_SCRIPT_REL,
    MARKDOWN_METADATA_HEADER_SCRIPT_REL,
    MULTI_AGENT_SYNC_SCRIPT_REL,
    TOOLING_REQUIRED_DOCS,
    USER_DOCS,
    WORKFLOW_SHELL_HYGIENE_SCRIPT_REL,
)


def build_failure_reasons(
    *,
    user_facing_enabled: bool,
    strict_user_docs: bool,
    changelog_updated: bool,
    updated_docs: list[str],
    missing_docs: list[str],
    tooling_changes_detected: list[str],
    updated_tooling_docs: list[str],
    strict_tooling: bool,
    missing_tooling_docs: list[str],
    matched_tooling_doc_requirement_rules: list[str],
    missing_triggered_tooling_docs: list[str],
    evolution_relevant_changes: list[str],
    evolution_policy_ok: bool,
    active_plan_sync_ok: bool,
    active_plan_sync_report: dict | None,
    multi_agent_sync_ok: bool,
    multi_agent_sync_report: dict | None,
    legacy_path_audit_ok: bool,
    legacy_path_audit_report: dict | None,
    markdown_metadata_header_ok: bool,
    markdown_metadata_header_report: dict | None,
    workflow_shell_hygiene_ok: bool,
    workflow_shell_hygiene_report: dict | None,
    bundle_workflow_parity_ok: bool,
    bundle_workflow_parity_report: dict | None,
    agents_bundle_render_ok: bool,
    agents_bundle_render_report: dict | None,
    guide_contract_sync_ok: bool,
    guide_contract_sync_report: dict | None,
    instruction_surface_sync_ok: bool,
    instruction_surface_sync_report: dict | None,
    deprecated_violations: list[dict],
    user_docs: tuple[str, ...] | list[str] | None = None,
    tooling_required_docs: tuple[str, ...] | list[str] | None = None,
    evolution_doc: str | None = None,
) -> list[str]:
    """Build user-facing failure reasons for docs-check output."""
    user_docs = tuple(user_docs or USER_DOCS)
    tooling_required_docs = tuple(tooling_required_docs or TOOLING_REQUIRED_DOCS)
    evolution_doc = evolution_doc or EVOLUTION_DOC
    reasons = build_user_doc_reasons(
        user_facing_enabled=user_facing_enabled,
        changelog_updated=changelog_updated,
        strict_user_docs=strict_user_docs,
        missing_docs=missing_docs,
        updated_docs=updated_docs,
        user_docs=user_docs,
    )
    reasons.extend(
        build_tooling_doc_reasons(
            ToolingDocReasonInputs(
                tooling_changes_detected=tooling_changes_detected,
                strict_tooling=strict_tooling,
                missing_tooling_docs=missing_tooling_docs,
                updated_tooling_docs=updated_tooling_docs,
                tooling_required_docs=tooling_required_docs,
                missing_triggered_tooling_docs=missing_triggered_tooling_docs,
                matched_tooling_doc_requirement_rules=matched_tooling_doc_requirement_rules,
            )
        )
    )

    if strict_tooling and evolution_relevant_changes and not evolution_policy_ok:
        reasons.append(
            f"Engineering evolution log is required for this scope; missing `{evolution_doc}` update."
        )

    if strict_tooling:
        gate_specs = (
            (
                active_plan_sync_ok,
                "Active-plan sync gate failed",
                active_plan_sync_report,
                ".",
            ),
            (
                multi_agent_sync_ok,
                "Multi-agent sync gate failed",
                multi_agent_sync_report,
                ".",
            ),
            (
                legacy_path_audit_ok,
                "Legacy path audit failed",
                legacy_path_audit_report,
                "; legacy script paths need migration.",
            ),
            (
                markdown_metadata_header_ok,
                "Markdown metadata header gate failed",
                markdown_metadata_header_report,
                "; run the metadata header formatter.",
            ),
            (
                workflow_shell_hygiene_ok,
                "Workflow shell hygiene gate failed",
                workflow_shell_hygiene_report,
                "; inline shell anti-patterns need bridge extraction.",
            ),
            (
                bundle_workflow_parity_ok,
                "Bundle/workflow parity gate failed",
                bundle_workflow_parity_report,
                "; registry bundle commands drifted from workflow run steps.",
            ),
            (
                agents_bundle_render_ok,
                "AGENTS bundle render gate failed",
                agents_bundle_render_report,
                "; AGENTS rendered bundle reference drifted from registry output.",
            ),
            (
                guide_contract_sync_ok,
                "Guide contract sync gate failed",
                guide_contract_sync_report,
                "; durable guide coverage drifted from repo-owned requirements.",
            ),
            (
                instruction_surface_sync_ok,
                "Instruction surface sync gate failed",
                instruction_surface_sync_report,
                "; generated instruction/starter surfaces drifted from policy-owned templates.",
            ),
        )
        for ok, label, report, fallback in gate_specs:
            if reason := build_gate_reason(
                ok=ok,
                label=label,
                report=report,
                fallback=fallback,
            ):
                reasons.append(reason)

    if deprecated_violations:
        reasons.append(
            f"Deprecated script references detected in governed docs/files ({len(deprecated_violations)})."
        )
    return reasons


def build_next_actions(
    *,
    failure_reasons: list[str],
    user_facing_enabled: bool,
    strict_user_docs: bool,
    missing_docs: list[str],
    tooling_changes_detected: list[str],
    strict_tooling: bool,
    missing_tooling_docs: list[str],
    matched_tooling_doc_requirement_rules: list[str],
    missing_triggered_tooling_docs: list[str],
    evolution_relevant_changes: list[str],
    evolution_policy_ok: bool,
    active_plan_sync_ok: bool,
    multi_agent_sync_ok: bool,
    legacy_path_audit_ok: bool,
    markdown_metadata_header_ok: bool,
    workflow_shell_hygiene_ok: bool,
    bundle_workflow_parity_ok: bool,
    agents_bundle_render_ok: bool,
    guide_contract_sync_ok: bool,
    instruction_surface_sync_ok: bool,
    deprecated_violations: list[dict],
    user_docs: tuple[str, ...] | list[str] | None = None,
    evolution_doc: str | None = None,
) -> list[str]:
    """Return actionable follow-up steps when docs-check fails."""
    user_docs = tuple(user_docs or USER_DOCS)
    evolution_doc = evolution_doc or EVOLUTION_DOC
    if not failure_reasons:
        return []
    actions: list[str] = []
    if user_facing_enabled and missing_docs:
        if strict_user_docs:
            actions.append(
                "Update all missing user docs: " + ", ".join(missing_docs) + "."
            )
        else:
            actions.append(
                "Update at least one user doc from the canonical set: "
                + ", ".join(user_docs)
                + "."
            )
    if tooling_changes_detected and missing_tooling_docs and strict_tooling:
        actions.append(
            "Update missing maintainer docs: " + ", ".join(missing_tooling_docs) + "."
        )
    if missing_triggered_tooling_docs:
        actions.append(
            "Update canonical plan docs required by this tooling scope"
            + (
                f" ({', '.join(matched_tooling_doc_requirement_rules)})"
                if matched_tooling_doc_requirement_rules
                else ""
            )
            + ": "
            + ", ".join(missing_triggered_tooling_docs)
            + "."
        )
    if strict_tooling and evolution_relevant_changes and not evolution_policy_ok:
        actions.append(f"Update `{evolution_doc}` with this tooling/process change.")
    if strict_tooling and not active_plan_sync_ok:
        actions.append(
            f"Fix active-plan sync drift: `python3 {ACTIVE_PLAN_SYNC_SCRIPT_REL}`."
        )
    if strict_tooling and not multi_agent_sync_ok:
        actions.append(
            f"Fix multi-agent board/runbook drift: `python3 {MULTI_AGENT_SYNC_SCRIPT_REL}`."
        )
    if strict_tooling and not legacy_path_audit_ok:
        actions.append(
            "Preview/apply path migrations: `python3 dev/scripts/devctl.py path-rewrite --dry-run` then `python3 dev/scripts/devctl.py path-rewrite`."
        )
    if strict_tooling and not markdown_metadata_header_ok:
        actions.append(
            "Normalize metadata headers: "
            f"`python3 {MARKDOWN_METADATA_HEADER_SCRIPT_REL} --fix`."
        )
    if strict_tooling and not workflow_shell_hygiene_ok:
        actions.append(
            "Resolve workflow shell anti-patterns: "
            f"`python3 {WORKFLOW_SHELL_HYGIENE_SCRIPT_REL}`."
        )
    if strict_tooling and not bundle_workflow_parity_ok:
        actions.append(
            "Align registry bundle commands with workflow steps: "
            f"`python3 {BUNDLE_WORKFLOW_PARITY_SCRIPT_REL}`."
        )
    if strict_tooling and not agents_bundle_render_ok:
        actions.append(
            "Regenerate AGENTS rendered bundle section from registry: "
            f"`python3 {AGENTS_BUNDLE_RENDER_SCRIPT_REL} --write`."
        )
    if strict_tooling and not guide_contract_sync_ok:
        actions.append(
            "Update the repo-owned durable guide coverage contract and inspect "
            f"`python3 {GUIDE_CONTRACT_SYNC_SCRIPT_REL} --format md`."
        )
    if strict_tooling and not instruction_surface_sync_ok:
        actions.append(
            "Regenerate policy-owned instruction/starter surfaces: "
            "`python3 dev/scripts/devctl.py render-surfaces --write --format md` "
            f"or inspect `python3 {INSTRUCTION_SURFACE_SYNC_SCRIPT_REL} --format md`."
        )
    if deprecated_violations:
        actions.append(
            "Replace deprecated release helper paths with `devctl` equivalents."
        )
    actions.append(
        "Generate triage snapshot for owner routing: `python3 dev/scripts/devctl.py triage --ci --no-cihub --emit-bundle --bundle-dir dev/reports/failures/local --bundle-prefix docs-check-failure --format md --output dev/reports/failures/local/docs-check-failure-summary.md`."
    )
    rerun_command = (
        "python3 dev/scripts/devctl.py docs-check --strict-tooling --format md"
        if strict_tooling
        else "python3 dev/scripts/devctl.py docs-check --user-facing --strict --format md"
    )
    actions.append(f"Re-run the failing gate with details: `{rerun_command}`.")
    return actions
