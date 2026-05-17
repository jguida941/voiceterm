"""Markdown/report rendering helpers for package-layout command output."""

from __future__ import annotations


def _crowding_suffix(crowded: dict) -> str:
    shim_files = int(crowded.get("shim_files", 0) or 0)
    total_files = int(crowded.get("total_files", crowded["current_files"]) or 0)
    if shim_files <= 0:
        return ""
    return f", {shim_files} approved shims excluded, {total_files} total files"


def layout_status(
    *,
    violations: list[dict],
    crowded_directories: list[dict],
    crowded_namespace_families: list[dict],
) -> str:
    """Return the current package-layout status label."""
    if violations:
        return "violations_present"
    if crowded_directories or crowded_namespace_families:
        return "baseline_debt_detected"
    return "clean"


def render_md(report: dict) -> str:
    """Render the package-layout report as markdown."""
    lines = ["# check_package_layout", ""]
    lines.append(f"- status: {report['status']}")
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- layout_clean: {report['layout_clean']}")
    lines.append(
        f"- baseline_layout_debt_detected: {report['baseline_layout_debt_detected']}"
    )
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(
        f"- flat_root_candidates_scanned: {report['flat_root_candidates_scanned']}"
    )
    lines.append(f"- flat_root_violations: {report['flat_root_violations']}")
    lines.append(
        f"- namespace_layout_candidates_scanned: {report['namespace_layout_candidates_scanned']}"
    )
    lines.append(
        f"- namespace_layout_violations: {report['namespace_layout_violations']}"
    )
    lines.append(
        f"- crowded_namespace_families_detected: {len(report['crowded_namespace_families'])}"
    )
    lines.append(
        f"- namespace_docs_candidates_scanned: {report['namespace_docs_candidates_scanned']}"
    )
    lines.append(
        f"- namespace_docs_violations: {report['namespace_docs_violations']}"
    )
    lines.append(
        f"- crowded_directory_candidates_scanned: {report['crowded_directory_candidates_scanned']}"
    )
    lines.append(
        f"- crowded_directory_violations: {report['crowded_directory_violations']}"
    )
    lines.append(
        f"- crowded_directories_detected: {len(report['crowded_directories'])}"
    )
    lines.append(
        f"- organization_review_clean: {report.get('organization_review_clean', True)}"
    )
    lines.append(
        f"- organization_role_debt_detected: {report.get('organization_role_debt_detected', False)}"
    )
    lines.append(
        f"- root_role_rules_scanned: {report.get('root_role_rules_scanned', 0)}"
    )
    lines.append(
        f"- compatibility_redirects_detected: {len(report['compatibility_redirects'])}"
    )
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("baseline_debt_enforced"):
        lines.append("- baseline_debt_enforced: True")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    if report["crowded_directories"]:
        lines.append("")
        lines.append("## Crowded Directories")
        for crowded in report["crowded_directories"]:
            lines.append(
                f"- `{crowded['root']}`: {crowded['current_files']} files "
                f"(max {crowded['max_files']}, mode `{crowded['enforcement_mode']}`"
                f"{_crowding_suffix(crowded)})"
            )

    if report["crowded_namespace_families"]:
        lines.append("")
        lines.append("## Crowded Namespace Families")
        for crowded in report["crowded_namespace_families"]:
            lines.append(
                f"- `{crowded['root']}` + `{crowded['flat_prefix']}*`: "
                f"{crowded['current_files']} files "
                f"(threshold {crowded['min_family_size']}, mode `{crowded['enforcement_mode']}`, "
                f"target `{crowded['root']}/{crowded['namespace_subdir']}`"
                f"{_crowding_suffix(crowded)})"
            )

    if report["compatibility_redirects"]:
        lines.append("")
        lines.append("## Compatibility Redirects")
        for redirect in report["compatibility_redirects"]:
            resolved_suffix = ""
            if (
                redirect["resolved_target"]
                and redirect["resolved_target"] != redirect["target"]
            ):
                resolved_suffix = f" (resolved to `{redirect['resolved_target']}`)"
            lines.append(
                f"- `{redirect['path']}` -> `{redirect['target']}`{resolved_suffix}"
            )

    if report.get("root_role_findings"):
        lines.append("")
        lines.append("## Organization Role Debt (advisory)")
        for finding in report["root_role_findings"]:
            support_examples = ", ".join(
                f"`{path}`" for path in finding.get("support_examples", [])
            )
            implementation_examples = ", ".join(
                f"`{path}`" for path in finding.get("implementation_examples", [])
            )
            detail = (
                f"- `{finding['root']}`: {finding['total_files']} files, "
                f"{finding['compat_shim_files']} compat shims, "
                f"{finding['public_entrypoint_files']} public entrypoints, "
                f"{finding['support_module_files']} support modules "
                f"(max {finding['max_support_modules']}), "
                f"{finding['implementation_module_files']} root implementation modules "
                f"(max {finding['max_implementation_modules']})"
            )
            if support_examples:
                detail += f"; support examples: {support_examples}"
            if implementation_examples:
                detail += f"; implementation examples: {implementation_examples}"
            if finding.get("guidance"):
                detail += f"; guidance: {finding['guidance']}"
            lines.append(detail)

    if report.get("enforced_crowded_directories") or report.get(
        "enforced_crowded_namespace_families"
    ):
        lines.append("")
        lines.append("## Enforced Baseline Debt (blocking)")
        for crowded in report.get("enforced_crowded_directories", []):
            lines.append(
                f"- `{crowded['root']}`: {crowded['current_files']} files "
                f"(max {crowded['max_files']}, mode `{crowded['enforcement_mode']}`"
                f"{_crowding_suffix(crowded)})"
            )
        for crowded in report.get("enforced_crowded_namespace_families", []):
            lines.append(
                f"- `{crowded['root']}` + `{crowded['flat_prefix']}*`: "
                f"{crowded['current_files']} files "
                f"(threshold {crowded['min_family_size']}, mode `{crowded['enforcement_mode']}`"
                f"{_crowding_suffix(crowded)})"
            )

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for violation in report["violations"]:
            lines.append(
                f"- `{violation['path']}` ({violation['reason']}): "
                f"{violation['guidance']} [policy: {violation['policy_source']}]"
            )

    org = report.get("organization")
    if org:
        lines.append("")
        lines.extend(_render_organization_surface(org))

    return "\n".join(lines)


def _render_organization_surface(org: dict) -> list[str]:
    """Render the unified organization surface section."""
    lines = [
        "## Organization Surface",
        "",
        f"- total_roles: {org.get('total_roles', 0)}",
        f"- total_redirects: {org.get('total_redirects', 0)}",
        f"- total_debt_items: {org.get('total_debt_items', 0)}",
        f"- redirects_with_missing_targets: {org.get('redirects_with_missing_targets', 0)}",
    ]

    roles = org.get("package_roles") or []
    if roles:
        lines.append("")
        lines.append("### Declared Package Roles")
        for role in roles:
            debt_marker = " **[DEBT]**" if role.get("debt_detected") else ""
            lines.append(
                f"- `{role['root']}`: {role['total_files']} files"
                f" ({role['compat_shim_files']} shims,"
                f" {role['public_entrypoint_files']} entrypoints,"
                f" {role['support_module_files']}/{role['max_support_modules']} support,"
                f" {role['implementation_module_files']}/{role['max_implementation_modules']} impl)"
                f"{debt_marker}"
            )

    redirects = org.get("compatibility_redirects") or []
    if redirects:
        lines.append("")
        lines.append("### Compatibility Redirects")
        for r in redirects:
            target_ok = "ok" if r.get("target_exists") else "MISSING"
            expiry = f", expires {r['expiry']}" if r.get("expiry") else ""
            owner = f" [{r['owner']}]" if r.get("owner") else ""
            lines.append(
                f"- `{r['path']}` -> `{r['target']}` ({target_ok}{expiry}){owner}"
            )

    debt = org.get("layout_debt") or []
    if debt:
        lines.append("")
        lines.append("### Layout Debt")
        for d in debt:
            lines.append(f"- [{d['kind']}] `{d['root']}`: {d['detail']}")

    return lines
