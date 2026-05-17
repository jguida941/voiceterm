"""Shared docs-check failure-reason helper builders."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolingDocReasonInputs:
    """Tooling-doc rule inputs grouped to keep helper interfaces compact."""

    tooling_changes_detected: list[str]
    strict_tooling: bool
    missing_tooling_docs: list[str]
    updated_tooling_docs: list[str]
    tooling_required_docs: tuple[str, ...]
    missing_triggered_tooling_docs: list[str]
    matched_tooling_doc_requirement_rules: list[str]


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


def build_gate_reason(
    *,
    ok: bool,
    label: str,
    report: dict | None,
    fallback: str,
) -> str | None:
    """Return one normalized strict-tooling gate failure reason."""
    if ok:
        return None
    gate_messages = collect_gate_messages(report)
    return label + (
        ": " + " | ".join(gate_messages) if gate_messages else fallback
    )


def build_user_doc_reasons(
    *,
    user_facing_enabled: bool,
    changelog_updated: bool,
    strict_user_docs: bool,
    missing_docs: list[str],
    updated_docs: list[str],
    user_docs: tuple[str, ...],
) -> list[str]:
    """Return user-doc-specific failure reasons."""
    reasons: list[str] = []
    if not user_facing_enabled:
        return reasons
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
            + ", ".join(user_docs)
            + "."
        )
    return reasons


def build_tooling_doc_reasons(inputs: ToolingDocReasonInputs) -> list[str]:
    """Return tooling-doc-specific failure reasons."""
    reasons: list[str] = []
    if inputs.tooling_changes_detected:
        if inputs.strict_tooling and inputs.missing_tooling_docs:
            reasons.append(
                "Strict tooling docs mode requires maintainer docs; missing: "
                + ", ".join(inputs.missing_tooling_docs)
                + "."
            )
        elif not inputs.strict_tooling and not inputs.updated_tooling_docs:
            reasons.append(
                "Tooling changes detected without maintainer docs updates; expected one of: "
                + ", ".join(inputs.tooling_required_docs)
                + "."
            )
    if inputs.missing_triggered_tooling_docs:
        reasons.append(
            "Tooling scope requires canonical plan updates"
            + (
                f" for rule(s) {', '.join(inputs.matched_tooling_doc_requirement_rules)}"
                if inputs.matched_tooling_doc_requirement_rules
                else ""
            )
            + "; missing: "
            + ", ".join(inputs.missing_triggered_tooling_docs)
            + "."
        )
    return reasons
