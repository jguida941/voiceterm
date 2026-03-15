"""Section renderers for docs-check markdown output."""

from __future__ import annotations


def _append_list_line(lines: list[str], label: str, values: list[str]) -> None:
    lines.append(f"- {label}: {', '.join(values) if values else 'none'}")


def append_header(lines: list[str], report: dict) -> None:
    """Render the top-level report summary."""
    since_ref = report.get("since_ref")
    head_ref = report.get("head_ref", "HEAD")
    if since_ref:
        lines.append(f"- commit_range: {since_ref}...{head_ref}")
    lines.append(f"- changelog_updated: {report.get('changelog_updated')}")
    _append_list_line(lines, "updated_docs", report.get("updated_docs", []))
    if report.get("user_facing"):
        _append_list_line(lines, "missing_docs", report.get("missing_docs", []))
        lines.append(f"- user_facing_ok: {report.get('user_facing_ok')}")


def append_tooling_summary(lines: list[str], report: dict) -> None:
    """Render tooling-policy and evolution summary lines."""
    tooling_changes = report.get("tooling_changes_detected", [])
    _append_list_line(lines, "tooling_changes_detected", tooling_changes)
    _append_list_line(lines, "updated_tooling_docs", report.get("updated_tooling_docs", []))
    _append_list_line(
        lines,
        "evolution_relevant_changes",
        report.get("evolution_relevant_changes", []),
    )
    lines.append(f"- evolution_updated: {report.get('evolution_updated')}")
    if not tooling_changes:
        return
    _append_list_line(
        lines,
        "missing_tooling_docs",
        report.get("missing_tooling_docs", []),
    )
    lines.append(f"- tooling_policy_ok: {report.get('tooling_policy_ok')}")
    _append_list_line(
        lines,
        "matched_tooling_doc_requirement_rules",
        report.get("matched_tooling_doc_requirement_rules", []),
    )
    _append_list_line(
        lines,
        "triggered_tooling_required_docs",
        report.get("triggered_tooling_required_docs", []),
    )
    _append_list_line(
        lines,
        "missing_triggered_tooling_docs",
        report.get("missing_triggered_tooling_docs", []),
    )
    lines.append(
        "- triggered_tooling_doc_policy_ok: "
        + str(report.get("triggered_tooling_doc_policy_ok"))
    )


def append_evolution_gate(lines: list[str], report: dict) -> None:
    """Render evolution gate status when strict tooling is enabled."""
    if report.get("strict_tooling") and report.get("evolution_relevant_changes"):
        lines.append(f"- evolution_policy_ok: {report.get('evolution_policy_ok')}")


def append_active_plan_sync(lines: list[str], report: dict) -> None:
    """Render active-plan sync status and errors."""
    lines.append(f"- active_plan_sync_ok: {report.get('active_plan_sync_ok')}")
    if report.get("active_plan_sync_ok"):
        return
    active_sync_report = report.get("active_plan_sync_report") or {}
    active_sync_errors = active_sync_report.get("errors", [])
    if active_sync_errors:
        lines.append("- active_plan_sync_errors: " + " | ".join(active_sync_errors))
    active_sync_error = active_sync_report.get("error")
    if active_sync_error:
        lines.append(f"- active_plan_sync_error: {active_sync_error}")


def append_multi_agent_sync(lines: list[str], report: dict) -> None:
    """Render multi-agent sync status and errors."""
    lines.append(f"- multi_agent_sync_ok: {report.get('multi_agent_sync_ok')}")
    if report.get("multi_agent_sync_ok"):
        return
    multi_agent_report = report.get("multi_agent_sync_report") or {}
    multi_agent_errors = multi_agent_report.get("errors", [])
    if multi_agent_errors:
        lines.append("- multi_agent_sync_errors: " + " | ".join(multi_agent_errors))
    multi_agent_error = multi_agent_report.get("error")
    if multi_agent_error:
        lines.append(f"- multi_agent_sync_error: {multi_agent_error}")


def append_legacy_path_audit(lines: list[str], report: dict) -> None:
    """Render legacy-path audit status and example violations."""
    lines.append(f"- legacy_path_audit_ok: {report.get('legacy_path_audit_ok')}")
    if report.get("legacy_path_audit_ok"):
        return
    audit_report = report.get("legacy_path_audit_report") or {}
    audit_error = audit_report.get("error")
    if audit_error:
        lines.append(f"- legacy_path_audit_error: {audit_error}")
    violations = audit_report.get("violations", [])
    if not violations:
        return
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


def append_markdown_metadata_header(lines: list[str], report: dict) -> None:
    """Render markdown metadata-header gate status."""
    lines.append(
        "- markdown_metadata_header_ok: "
        + str(report.get("markdown_metadata_header_ok"))
    )
    if report.get("markdown_metadata_header_ok"):
        return
    metadata_report = report.get("markdown_metadata_header_report") or {}
    metadata_error = metadata_report.get("error")
    if metadata_error:
        lines.append(f"- markdown_metadata_header_error: {metadata_error}")
    changed_paths = metadata_report.get("changed_paths", [])
    if not changed_paths:
        return
    lines.append("- markdown_metadata_header_changed_paths: " + ", ".join(changed_paths[:20]))
    if len(changed_paths) > 20:
        lines.append(
            f"- markdown_metadata_header_more_paths: {len(changed_paths) - 20}"
        )


def append_workflow_shell_hygiene(lines: list[str], report: dict) -> None:
    """Render workflow-shell hygiene status and example violations."""
    lines.append(
        "- workflow_shell_hygiene_ok: "
        + str(report.get("workflow_shell_hygiene_ok"))
    )
    if report.get("workflow_shell_hygiene_ok"):
        return
    workflow_shell_report = report.get("workflow_shell_hygiene_report") or {}
    workflow_shell_error = workflow_shell_report.get("error")
    if workflow_shell_error:
        lines.append(f"- workflow_shell_hygiene_error: {workflow_shell_error}")
    violations = workflow_shell_report.get("violations", [])
    if not violations:
        return
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


def append_bundle_workflow_parity(lines: list[str], report: dict) -> None:
    """Render bundle/workflow parity status and missing commands."""
    lines.append(
        "- bundle_workflow_parity_ok: "
        + str(report.get("bundle_workflow_parity_ok"))
    )
    if report.get("bundle_workflow_parity_ok"):
        return
    parity_report = report.get("bundle_workflow_parity_report") or {}
    parity_error = parity_report.get("error")
    if parity_error:
        lines.append(f"- bundle_workflow_parity_error: {parity_error}")
    missing_count = 0
    for target in parity_report.get("targets", []):
        missing = target.get("missing_commands", [])
        missing_count += len(missing)
        for command in missing[:5]:
            lines.append(
                "- bundle_workflow_parity_missing: "
                f"{target.get('bundle')} -> `{command}`"
            )
    if missing_count > 5:
        lines.append(f"- bundle_workflow_parity_more_missing: {missing_count - 5}")


def append_agents_bundle_render(lines: list[str], report: dict) -> None:
    """Render AGENTS bundle render status and diff preview."""
    lines.append("- agents_bundle_render_ok: " + str(report.get("agents_bundle_render_ok")))
    if report.get("agents_bundle_render_ok"):
        return
    agents_bundle_report = report.get("agents_bundle_render_report") or {}
    bundle_render_error = agents_bundle_report.get("error")
    if bundle_render_error:
        lines.append(f"- agents_bundle_render_error: {bundle_render_error}")
    if agents_bundle_report.get("changed"):
        lines.append("- agents_bundle_render_changed: True")
    diff_preview = agents_bundle_report.get("diff_preview", [])
    for diff_line in diff_preview[:10]:
        lines.append(f"- agents_bundle_render_diff: `{diff_line}`")
    if len(diff_preview) > 10:
        lines.append(f"- agents_bundle_render_more_diff: {len(diff_preview) - 10}")


def append_instruction_surface_sync(lines: list[str], report: dict) -> None:
    """Render instruction/starter surface sync status and diff preview."""
    lines.append(
        "- instruction_surface_sync_ok: "
        + str(report.get("instruction_surface_sync_ok"))
    )
    if report.get("instruction_surface_sync_ok"):
        return
    surface_report = report.get("instruction_surface_sync_report") or {}
    surface_error = surface_report.get("error")
    if surface_error:
        lines.append(f"- instruction_surface_sync_error: {surface_error}")
    for surface in surface_report.get("surfaces", []):
        if surface.get("ok"):
            continue
        lines.append(
            "- instruction_surface_sync_surface: "
            f"{surface.get('surface_id')} ({surface.get('state')}) -> {surface.get('output_path')}"
        )
        for diff_line in (surface.get("diff_preview") or [])[:4]:
            lines.append(f"- instruction_surface_sync_diff: `{diff_line}`")
        if surface.get("error"):
            lines.append(f"- instruction_surface_sync_surface_error: {surface['error']}")


def append_strict_tooling_sections(lines: list[str], report: dict) -> None:
    """Render strict-tooling-only sections."""
    if not report.get("strict_tooling"):
        return
    append_active_plan_sync(lines, report)
    append_multi_agent_sync(lines, report)
    append_legacy_path_audit(lines, report)
    append_markdown_metadata_header(lines, report)
    append_workflow_shell_hygiene(lines, report)
    append_bundle_workflow_parity(lines, report)
    append_agents_bundle_render(lines, report)
    append_instruction_surface_sync(lines, report)


def append_deprecated_references(lines: list[str], report: dict) -> None:
    """Render deprecated reference findings."""
    lines.append(f"- deprecated_reference_ok: {report.get('deprecated_reference_ok')}")
    deprecated_violations = report.get("deprecated_reference_violations", [])
    if not deprecated_violations:
        return
    lines.extend(["", "## Deprecated references"])
    for violation in deprecated_violations:
        lines.append(
            f"- {violation['file']}:{violation['line']} ({violation['pattern']}) -> use `{violation['replacement']}`"
        )


def append_failure_sections(lines: list[str], report: dict) -> None:
    """Render failure reasons and next actions."""
    if report.get("ok"):
        return
    lines.extend(["", "## Why it failed"])
    for reason in report.get("failure_reasons", []):
        lines.append(f"- {reason}")
    next_actions = report.get("next_actions", [])
    if not next_actions:
        return
    lines.extend(["", "## Next actions"])
    for action in next_actions:
        lines.append(f"- {action}")
