"""Markdown rendering helpers for docs-check output."""


def render_markdown_report(report: dict) -> str:
    """Render docs-check report payload in markdown format."""
    lines = ["# devctl docs-check", ""]
    since_ref = report.get("since_ref")
    head_ref = report.get("head_ref", "HEAD")
    if since_ref:
        lines.append(f"- commit_range: {since_ref}...{head_ref}")
    lines.append(f"- changelog_updated: {report.get('changelog_updated')}")
    updated_docs = report.get("updated_docs", [])
    lines.append(f"- updated_docs: {', '.join(updated_docs) if updated_docs else 'none'}")
    if report.get("user_facing"):
        missing_docs = report.get("missing_docs", [])
        lines.append(f"- missing_docs: {', '.join(missing_docs) if missing_docs else 'none'}")
        lines.append(f"- user_facing_ok: {report.get('user_facing_ok')}")

    tooling_changes = report.get("tooling_changes_detected", [])
    updated_tooling_docs = report.get("updated_tooling_docs", [])
    evolution_changes = report.get("evolution_relevant_changes", [])
    lines.append(
        "- tooling_changes_detected: "
        + (", ".join(tooling_changes) if tooling_changes else "none")
    )
    lines.append(
        "- updated_tooling_docs: "
        + (", ".join(updated_tooling_docs) if updated_tooling_docs else "none")
    )
    lines.append(
        "- evolution_relevant_changes: "
        + (", ".join(evolution_changes) if evolution_changes else "none")
    )
    lines.append(f"- evolution_updated: {report.get('evolution_updated')}")

    if tooling_changes:
        missing_tooling_docs = report.get("missing_tooling_docs", [])
        lines.append(
            "- missing_tooling_docs: "
            + (", ".join(missing_tooling_docs) if missing_tooling_docs else "none")
        )
        lines.append(f"- tooling_policy_ok: {report.get('tooling_policy_ok')}")
    if report.get("strict_tooling") and evolution_changes:
        lines.append(f"- evolution_policy_ok: {report.get('evolution_policy_ok')}")
    if report.get("strict_tooling"):
        lines.append(f"- active_plan_sync_ok: {report.get('active_plan_sync_ok')}")
        active_sync_report = report.get("active_plan_sync_report") or {}
        if not report.get("active_plan_sync_ok"):
            active_sync_errors = active_sync_report.get("errors", [])
            if active_sync_errors:
                lines.append("- active_plan_sync_errors: " + " | ".join(active_sync_errors))
            active_sync_error = active_sync_report.get("error")
            if active_sync_error:
                lines.append(f"- active_plan_sync_error: {active_sync_error}")

        lines.append(f"- multi_agent_sync_ok: {report.get('multi_agent_sync_ok')}")
        multi_agent_report = report.get("multi_agent_sync_report") or {}
        if not report.get("multi_agent_sync_ok"):
            multi_agent_errors = multi_agent_report.get("errors", [])
            if multi_agent_errors:
                lines.append("- multi_agent_sync_errors: " + " | ".join(multi_agent_errors))
            multi_agent_error = multi_agent_report.get("error")
            if multi_agent_error:
                lines.append(f"- multi_agent_sync_error: {multi_agent_error}")

        lines.append(f"- legacy_path_audit_ok: {report.get('legacy_path_audit_ok')}")
        audit_report = report.get("legacy_path_audit_report") or {}
        if not report.get("legacy_path_audit_ok"):
            audit_error = audit_report.get("error")
            if audit_error:
                lines.append(f"- legacy_path_audit_error: {audit_error}")
            violations = audit_report.get("violations", [])
            if violations:
                lines.append("- legacy_path_audit_violations:")
                for violation in violations[:10]:
                    lines.append(
                        "  - {file}:{line} references `{legacy}` -> `{replacement}`".format(
                            file=violation["file"],
                            line=violation["line"],
                            legacy=violation["legacy_path"],
                            replacement=violation["replacement_path"],
                        )
                    )
                lines.append(
                    "- legacy_path_audit_hint: run `python3 dev/scripts/devctl.py path-rewrite --dry-run` to preview fixes, then `python3 dev/scripts/devctl.py path-rewrite` to apply."
                )

        lines.append(
            "- markdown_metadata_header_ok: "
            + str(report.get("markdown_metadata_header_ok"))
        )
        metadata_report = report.get("markdown_metadata_header_report") or {}
        if not report.get("markdown_metadata_header_ok"):
            metadata_error = metadata_report.get("error")
            if metadata_error:
                lines.append(f"- markdown_metadata_header_error: {metadata_error}")
            changed_paths = metadata_report.get("changed_paths", [])
            if changed_paths:
                lines.append(
                    "- markdown_metadata_header_changed_paths: "
                    + ", ".join(changed_paths[:20])
                )
                if len(changed_paths) > 20:
                    lines.append(
                        f"- markdown_metadata_header_more_paths: {len(changed_paths) - 20}"
                    )

    lines.append(f"- deprecated_reference_ok: {report.get('deprecated_reference_ok')}")
    deprecated_violations = report.get("deprecated_reference_violations", [])
    if deprecated_violations:
        lines.extend(["", "## Deprecated references"])
        for violation in deprecated_violations:
            lines.append(
                f"- {violation['file']}:{violation['line']} ({violation['pattern']}) -> use `{violation['replacement']}`"
            )

    if not report.get("ok"):
        lines.extend(["", "## Why it failed"])
        for reason in report.get("failure_reasons", []):
            lines.append(f"- {reason}")
        next_actions = report.get("next_actions", [])
        if next_actions:
            lines.extend(["", "## Next actions"])
            for action in next_actions:
                lines.append(f"- {action}")
    lines.append(f"- ok: {report.get('ok')}")
    return "\n".join(lines)
