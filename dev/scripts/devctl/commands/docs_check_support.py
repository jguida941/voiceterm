"""Shared helpers for the docs-check command."""

from __future__ import annotations

import re
from pathlib import Path

from ..script_catalog import check_script_relative_path

USER_DOCS = [
    "README.md",
    "QUICK_START.md",
    "guides/USAGE.md",
    "guides/CLI_FLAGS.md",
    "guides/INSTALL.md",
    "guides/TROUBLESHOOTING.md",
]

TOOLING_CHANGE_PREFIXES = (
    "dev/scripts/",
    "scripts/macro-packs/",
    ".github/workflows/",
)
TOOLING_CHANGE_EXACT = {
    "Makefile",
    "AGENTS.md",
    "dev/DEVELOPMENT.md",
    "dev/scripts/README.md",
}
TOOLING_REQUIRED_DOCS = [
    "AGENTS.md",
    "dev/DEVELOPMENT.md",
    "dev/scripts/README.md",
    "dev/active/MASTER_PLAN.md",
]
EVOLUTION_DOC = "dev/history/ENGINEERING_EVOLUTION.md"
EVOLUTION_CHANGE_PREFIXES = (
    "dev/scripts/",
    ".github/workflows/",
)
EVOLUTION_CHANGE_EXACT = {
    "AGENTS.md",
    "dev/ARCHITECTURE.md",
    "dev/DEVELOPMENT.md",
    "dev/scripts/README.md",
    "dev/active/MASTER_PLAN.md",
}

DEPRECATED_REFERENCE_TARGETS = [
    "AGENTS.md",
    "dev/DEVELOPMENT.md",
    "dev/scripts/README.md",
    "scripts/macro-packs/full-dev.yaml",
    "Makefile",
]
DEPRECATED_REFERENCE_PATTERNS = [
    {
        "name": "release-script",
        "regex": re.compile(r"\./dev/scripts/release\.sh\b"),
        "replacement": "python3 dev/scripts/devctl.py release --version <version>",
    },
    {
        "name": "homebrew-script",
        "regex": re.compile(r"\./dev/scripts/update-homebrew\.sh\b"),
        "replacement": "python3 dev/scripts/devctl.py homebrew --version <version>",
    },
    {
        "name": "pypi-script",
        "regex": re.compile(r"\./dev/scripts/publish-pypi\.sh\b"),
        "replacement": "python3 dev/scripts/devctl.py pypi --upload",
    },
    {
        "name": "notes-script",
        "regex": re.compile(r"\./dev/scripts/generate-release-notes\.sh\b"),
        "replacement": "python3 dev/scripts/devctl.py release-notes --version <version>",
    },
]

ACTIVE_PLAN_SYNC_SCRIPT_REL = check_script_relative_path("active_plan_sync")
MULTI_AGENT_SYNC_SCRIPT_REL = check_script_relative_path("multi_agent_sync")
MARKDOWN_METADATA_HEADER_SCRIPT_REL = check_script_relative_path(
    "markdown_metadata_header"
)


def is_tooling_change(path: str) -> bool:
    """Return True when the changed path is considered tooling/process scope."""
    return path in TOOLING_CHANGE_EXACT or path.startswith(TOOLING_CHANGE_PREFIXES)


def requires_evolution_update(path: str) -> bool:
    """Return True when a path requires an engineering-evolution log update."""
    return path in EVOLUTION_CHANGE_EXACT or path.startswith(EVOLUTION_CHANGE_PREFIXES)


def scan_deprecated_references(repo_root: Path) -> list[dict]:
    """Find legacy helper-script references in governance-controlled files."""
    violations = []
    for relative in DEPRECATED_REFERENCE_TARGETS:
        path = repo_root / relative
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for spec in DEPRECATED_REFERENCE_PATTERNS:
                if spec["regex"].search(line):
                    violations.append(
                        {
                            "file": relative,
                            "line": lineno,
                            "pattern": spec["name"],
                            "line_text": line.strip(),
                            "replacement": spec["replacement"],
                        }
                    )
    return violations


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
    deprecated_violations: list[dict],
) -> list[str]:
    """Build user-facing failure reasons for docs-check output."""
    reasons: list[str] = []
    if user_facing_enabled:
        if not changelog_updated:
            reasons.append("Missing required `dev/CHANGELOG.md` update for user-facing changes.")
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
            "Active-plan sync gate failed" + (": " + " | ".join(gate_messages) if gate_messages else ".")
        )

    if strict_tooling and not multi_agent_sync_ok:
        gate_messages = collect_gate_messages(multi_agent_sync_report)
        reasons.append(
            "Multi-agent sync gate failed" + (": " + " | ".join(gate_messages) if gate_messages else ".")
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
    deprecated_violations: list[dict],
) -> list[str]:
    """Return actionable follow-up steps when docs-check fails."""
    if not failure_reasons:
        return []
    actions: list[str] = []
    if user_facing_enabled and missing_docs:
        if strict_user_docs:
            actions.append("Update all missing user docs: " + ", ".join(missing_docs) + ".")
        else:
            actions.append("Update at least one user doc from the canonical set in USER_DOCS.")
    if tooling_changes_detected and missing_tooling_docs and strict_tooling:
        actions.append("Update missing maintainer docs: " + ", ".join(missing_tooling_docs) + ".")
    if strict_tooling and evolution_relevant_changes and not evolution_policy_ok:
        actions.append(f"Update `{EVOLUTION_DOC}` with this tooling/process change.")
    if strict_tooling and not active_plan_sync_ok:
        actions.append(f"Fix active-plan sync drift: `python3 {ACTIVE_PLAN_SYNC_SCRIPT_REL}`.")
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
    if deprecated_violations:
        actions.append("Replace deprecated release helper paths with `devctl` equivalents.")
    actions.append(
        "Generate triage snapshot for owner routing: `python3 dev/scripts/devctl.py triage --ci --no-cihub --emit-bundle --bundle-dir dev/reports/failures/local --bundle-prefix docs-check-failure --format md --output dev/reports/failures/local/docs-check-failure-summary.md`."
    )
    actions.append(
        "Re-run the failing gate with details: `python3 dev/scripts/devctl.py docs-check --user-facing --strict --format md`."
    )
    return actions
