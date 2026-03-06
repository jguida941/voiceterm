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

        lines.append(
            "- workflow_shell_hygiene_ok: "
            + str(report.get("workflow_shell_hygiene_ok"))
        )
        workflow_shell_report = report.get("workflow_shell_hygiene_report") or {}
        if not report.get("workflow_shell_hygiene_ok"):
            workflow_shell_error = workflow_shell_report.get("error")
            if workflow_shell_error:
                lines.append(f"- workflow_shell_hygiene_error: {workflow_shell_error}")
            violations = workflow_shell_report.get("violations", [])
            if violations:
                lines.append("- workflow_shell_hygiene_violations:")
                for violation in violations[:10]:
                    lines.append(
                        "  - {file}:{line} [{rule}] `{line_text}`".format(
                            file=violation.get("file"),
                            line=violation.get("line"),
                            rule=violation.get("rule"),
                            line_text=violation.get("line_text"),
                        )
                    )
                if len(violations) > 10:
                    lines.append(
                        f"- workflow_shell_hygiene_more_violations: {len(violations) - 10}"
                    )

        lines.append(
            "- bundle_workflow_parity_ok: "
            + str(report.get("bundle_workflow_parity_ok"))
        )
        parity_report = report.get("bundle_workflow_parity_report") or {}
        if not report.get("bundle_workflow_parity_ok"):
            parity_error = parity_report.get("error")
            if parity_error:
                lines.append(f"- bundle_workflow_parity_error: {parity_error}")
            parity_targets = parity_report.get("targets", [])
            missing_count = 0
            for target in parity_targets:
                missing = target.get("missing_commands", [])
                missing_count += len(missing)
                for command in missing[:5]:
                    lines.append(
                        "- bundle_workflow_parity_missing: "
                        f"{target.get('bundle')} -> `{command}`"
                    )
            if missing_count > 5:
                lines.append(
                    f"- bundle_workflow_parity_more_missing: {missing_count - 5}"
                )

        lines.append(
            "- agents_bundle_render_ok: "
            + str(report.get("agents_bundle_render_ok"))
        )
        agents_bundle_report = report.get("agents_bundle_render_report") or {}
        if not report.get("agents_bundle_render_ok"):
            bundle_render_error = agents_bundle_report.get("error")
            if bundle_render_error:
                lines.append(f"- agents_bundle_render_error: {bundle_render_error}")
            if agents_bundle_report.get("changed"):
                lines.append("- agents_bundle_render_changed: True")
            diff_preview = agents_bundle_report.get("diff_preview", [])
            for diff_line in diff_preview[:10]:
                lines.append(f"- agents_bundle_render_diff: `{diff_line}`")
            if len(diff_preview) > 10:
                lines.append(
                    f"- agents_bundle_render_more_diff: {len(diff_preview) - 10}"
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
