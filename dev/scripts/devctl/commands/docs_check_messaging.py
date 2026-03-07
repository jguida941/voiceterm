"""Failure-reason and next-action builders for docs-check."""

from __future__ import annotations

from .docs_check_policy import (
    ACTIVE_PLAN_SYNC_SCRIPT_REL,
    AGENTS_BUNDLE_RENDER_SCRIPT_REL,
    BUNDLE_WORKFLOW_PARITY_SCRIPT_REL,
    EVOLUTION_DOC,
    MARKDOWN_METADATA_HEADER_SCRIPT_REL,
    MULTI_AGENT_SYNC_SCRIPT_REL,
    TOOLING_REQUIRED_DOCS,
    USER_DOCS,
    WORKFLOW_SHELL_HYGIENE_SCRIPT_REL,
)


def collect_gate_messages(report: dict | None) -> list[str]:
    """Extract normalized error messages from a policy-gate report payload."""
    if not isinstance(report, dict):
        return []
    messages: list[str] = []
    errors = report.get("errors")
    if isinstance(errors, list):
        messages.extend(str(item) for item in errors if item)
    single_error = report.get("error")
    if single_error:
        messages.append(str(single_error))
    return messages


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
    deprecated_violations: list[dict],
) -> list[str]:
    """Build user-facing failure reasons for docs-check output."""
    reasons: list[str] = []
    if user_facing_enabled:
        if not changelog_updated:
            reasons.append(
                "Missing required `dev/CHANGELOG.md` update for user-facing changes."
            )
        if strict_user_docs and missing_docs:
            reasons.append(
                "Strict user-facing docs mode requires all canonical docs; missing: "
                + ", ".join(missing_docs)
                + "."
            )
        elif not strict_user_docs and not updated_docs:
            reasons.append(
                "User-facing docs mode requires at least one updated doc in: "
                + ", ".join(USER_DOCS)
                + "."
            )

    if tooling_changes_detected:
        if strict_tooling and missing_tooling_docs:
            reasons.append(
                "Strict tooling docs mode requires maintainer docs; missing: "
                + ", ".join(missing_tooling_docs)
                + "."
            )
        elif not strict_tooling and not updated_tooling_docs:
            reasons.append(
                "Tooling changes detected without maintainer docs updates; expected one of: "
                + ", ".join(TOOLING_REQUIRED_DOCS)
                + "."
            )

    if strict_tooling and evolution_relevant_changes and not evolution_policy_ok:
        reasons.append(
            f"Engineering evolution log is required for this scope; missing `{EVOLUTION_DOC}` update."
        )

    if strict_tooling and not active_plan_sync_ok:
        gate_messages = collect_gate_messages(active_plan_sync_report)
        reasons.append(
            "Active-plan sync gate failed"
            + (": " + " | ".join(gate_messages) if gate_messages else ".")
        )

    if strict_tooling and not multi_agent_sync_ok:
        gate_messages = collect_gate_messages(multi_agent_sync_report)
        reasons.append(
            "Multi-agent sync gate failed"
            + (": " + " | ".join(gate_messages) if gate_messages else ".")
        )

    if strict_tooling and not legacy_path_audit_ok:
        legacy_messages = collect_gate_messages(legacy_path_audit_report)
        reasons.append(
            "Legacy path audit failed"
            + (
                ": " + " | ".join(legacy_messages)
                if legacy_messages
                else "; legacy script paths need migration."
            )
        )

    if strict_tooling and not markdown_metadata_header_ok:
        metadata_messages = collect_gate_messages(markdown_metadata_header_report)
        reasons.append(
            "Markdown metadata header gate failed"
            + (
                ": " + " | ".join(metadata_messages)
                if metadata_messages
                else "; run the metadata header formatter."
            )
        )

    if strict_tooling and not workflow_shell_hygiene_ok:
        workflow_shell_messages = collect_gate_messages(workflow_shell_hygiene_report)
        reasons.append(
            "Workflow shell hygiene gate failed"
            + (
                ": " + " | ".join(workflow_shell_messages)
                if workflow_shell_messages
                else "; inline shell anti-patterns need bridge extraction."
            )
        )

    if strict_tooling and not bundle_workflow_parity_ok:
        parity_messages = collect_gate_messages(bundle_workflow_parity_report)
        reasons.append(
            "Bundle/workflow parity gate failed"
            + (
                ": " + " | ".join(parity_messages)
                if parity_messages
                else "; registry bundle commands drifted from workflow run steps."
            )
        )

    if strict_tooling and not agents_bundle_render_ok:
        render_messages = collect_gate_messages(agents_bundle_render_report)
        reasons.append(
            "AGENTS bundle render gate failed"
            + (
                ": " + " | ".join(render_messages)
                if render_messages
                else "; AGENTS rendered bundle reference drifted from registry output."
            )
        )

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
    evolution_relevant_changes: list[str],
    evolution_policy_ok: bool,
    active_plan_sync_ok: bool,
    multi_agent_sync_ok: bool,
    legacy_path_audit_ok: bool,
    markdown_metadata_header_ok: bool,
    workflow_shell_hygiene_ok: bool,
    bundle_workflow_parity_ok: bool,
    agents_bundle_render_ok: bool,
    deprecated_violations: list[dict],
) -> list[str]:
    """Return actionable follow-up steps when docs-check fails."""
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
                "Update at least one user doc from the canonical set in USER_DOCS."
            )
    if tooling_changes_detected and missing_tooling_docs and strict_tooling:
        actions.append(
            "Update missing maintainer docs: " + ", ".join(missing_tooling_docs) + "."
        )
    if strict_tooling and evolution_relevant_changes and not evolution_policy_ok:
        actions.append(f"Update `{EVOLUTION_DOC}` with this tooling/process change.")
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
