#!/usr/bin/env python3
"""Guard repo package/layout organization using repo-policy rules."""

from __future__ import annotations

import json
import sys

if __package__:
    from .bootstrap import (
        REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_adoption_scan,
        utc_timestamp,
    )
else:  # pragma: no cover - standalone script fallback
    from bootstrap import (
        REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_adoption_scan,
        utc_timestamp,
    )

collect_flat_root_violations = import_attr(
    "package_layout.support",
    "collect_flat_root_violations",
)
collect_directory_crowding_violations = import_attr(
    "package_layout.support",
    "collect_directory_crowding_violations",
)
collect_root_role_findings = import_attr(
    "package_layout.support",
    "collect_root_role_findings",
)
layout_status = import_attr("package_layout.render", "layout_status")
render_md = import_attr("package_layout.render", "render_md")
collect_compatibility_redirects = import_attr(
    "package_layout.compatibility_redirects",
    "collect_compatibility_redirects",
)
resolve_baseline_debt_enforcement = import_attr(
    "package_layout.baseline_debt",
    "resolve_baseline_debt_enforcement",
)
BaselineDebtSnapshot = import_attr(
    "package_layout.baseline_debt",
    "BaselineDebtSnapshot",
)
collect_namespace_docs_sync_violations = import_attr(
    "package_layout.support",
    "collect_namespace_docs_sync_violations",
)
collect_namespace_layout_violations = import_attr(
    "package_layout.support",
    "collect_namespace_layout_violations",
)
resolve_layout_rules = import_attr(
    "package_layout.rule_resolution", "resolve_layout_rules"
)
resolve_root_role_rules = import_attr(
    "package_layout.rule_resolution", "resolve_root_role_rules"
)
list_changed_paths = import_attr("rust_guard_common", "list_changed_paths")
GuardContext = import_attr("rust_guard_common", "GuardContext")

build_organization_surface = import_attr(
    "package_layout.organization", "build_organization_surface"
)
guard = GuardContext(REPO_ROOT)
_layout_status = layout_status
_render_md = render_md


def _path_is_under_any_root(path: str, roots: list[str]) -> bool:
    normalized = path.strip("/")
    for root in roots:
        normalized_root = root.strip("/")
        if normalized == normalized_root or normalized.startswith(
            f"{normalized_root}/"
        ):
            return True
    return False


def _filter_violations_to_roots(
    violations: list[dict],
    *,
    roots: list[str] | None,
) -> list[dict]:
    """Keep package-layout violations only for explicitly enforced roots."""
    if not roots:
        return violations
    return [
        violation
        for violation in violations
        if _path_is_under_any_root(str(violation.get("path", "")), roots)
    ]


def _scope_violation_groups_to_baseline_roots(
    groups: tuple[list[dict], ...],
    *,
    enforce: bool,
    roots: list[str] | None,
) -> tuple[list[dict], ...]:
    """Filter all violation groups when baseline enforcement is root-scoped."""
    if not enforce or not roots:
        return groups
    return tuple(
        _filter_violations_to_roots(group, roots=roots) for group in groups
    )


def _build_report(
    *,
    args,
    report_mode: str,
    data: dict,
) -> dict:
    changed_paths = data["changed_paths"]
    flat_root_violations = data["flat_root_violations"]
    flat_root_candidates_scanned = data["flat_root_candidates_scanned"]
    layout_violations = data["layout_violations"]
    crowded_namespace_families = data["crowded_namespace_families"]
    namespace_layout_candidates_scanned = data[
        "namespace_layout_candidates_scanned"
    ]
    docs_sync_violations = data["docs_sync_violations"]
    namespace_docs_candidates_scanned = data["namespace_docs_candidates_scanned"]
    crowding_violations = data["crowding_violations"]
    crowded_directories = data["crowded_directories"]
    crowded_directory_candidates_scanned = data[
        "crowded_directory_candidates_scanned"
    ]
    root_role_findings = data["root_role_findings"]
    root_role_rules_scanned = data["root_role_rules_scanned"]
    compatibility_redirects = data["compatibility_redirects"]
    baseline_debt_roots = getattr(args, "baseline_debt_roots", None)
    (
        flat_root_violations,
        layout_violations,
        docs_sync_violations,
        crowding_violations,
    ) = _scope_violation_groups_to_baseline_roots(
        (
            flat_root_violations,
            layout_violations,
            docs_sync_violations,
            crowding_violations,
        ),
        enforce=getattr(args, "fail_on_baseline_debt", False),
        roots=baseline_debt_roots,
    )
    violations = [
        *flat_root_violations,
        *layout_violations,
        *docs_sync_violations,
        *crowding_violations,
    ]
    status = _layout_status(
        violations=violations,
        crowded_directories=crowded_directories,
        crowded_namespace_families=crowded_namespace_families,
    )
    baseline_layout_debt_detected = bool(
        crowded_directories or crowded_namespace_families
    )
    baseline_snapshot = BaselineDebtSnapshot(
        detected=baseline_layout_debt_detected,
        roots=baseline_debt_roots,
        crowded_directories=crowded_directories,
        crowded_namespace_families=crowded_namespace_families,
    )
    baseline_debt_enforced, enforced_dirs, enforced_families = (
        resolve_baseline_debt_enforcement(
            repo_root=REPO_ROOT,
            changed_paths=changed_paths,
            fail_on_baseline_debt=getattr(args, "fail_on_baseline_debt", False),
            snapshot=baseline_snapshot,
        )
    )
    report = {
        "command": "check_package_layout",
        "timestamp": utc_timestamp(),
        "status": status,
        "mode": report_mode,
        "since_ref": None if report_mode == "adoption-scan" else args.since_ref,
        "head_ref": None if report_mode == "adoption-scan" else args.head_ref,
        "ok": len(violations) == 0 and not baseline_debt_enforced,
        "layout_clean": status == "clean",
        "baseline_layout_debt_detected": baseline_layout_debt_detected,
        "baseline_debt_enforced": baseline_debt_enforced,
        "files_changed": len(changed_paths),
        "flat_root_candidates_scanned": flat_root_candidates_scanned,
        "flat_root_violations": len(flat_root_violations),
        "namespace_layout_candidates_scanned": namespace_layout_candidates_scanned,
        "namespace_layout_violations": len(layout_violations),
        "crowded_namespace_families": crowded_namespace_families,
        "namespace_docs_candidates_scanned": namespace_docs_candidates_scanned,
        "namespace_docs_violations": len(docs_sync_violations),
        "crowded_directory_candidates_scanned": crowded_directory_candidates_scanned,
        "crowded_directory_violations": len(crowding_violations),
        "crowded_directories": crowded_directories,
        "organization_review_clean": not root_role_findings,
        "organization_role_debt_detected": bool(root_role_findings),
        "root_role_rules_scanned": root_role_rules_scanned,
        "root_role_findings": root_role_findings,
        "compatibility_redirects": compatibility_redirects,
        "violations": violations,
    }
    if baseline_debt_enforced:
        report["enforced_crowded_directories"] = enforced_dirs
        report["enforced_crowded_namespace_families"] = enforced_families
    report["organization"] = build_organization_surface(
        repo_root=REPO_ROOT,
        compatibility_redirects=compatibility_redirects,
        crowded_directories=crowded_directories,
        crowded_namespace_families=crowded_namespace_families,
        root_role_findings=root_role_findings,
    )
    return report


def main() -> int:
    parser = build_since_ref_format_parser(__doc__ or "")
    parser.add_argument(
        "--fail-on-baseline-debt",
        action="store_true",
        help="Exit non-zero when baseline layout debt is detected, even without per-file violations.",
    )
    parser.add_argument(
        "--baseline-debt-root",
        action="append",
        dest="baseline_debt_roots",
        metavar="PATH",
        help="Only enforce baseline-debt failure for this root (repeatable). If omitted, all crowded roots fail.",
    )
    args = parser.parse_args()
    report_mode = (
        "adoption-scan"
        if is_adoption_scan(since_ref=args.since_ref, head_ref=args.head_ref)
        else "commit-range"
        if args.since_ref
        else "working-tree"
    )

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths = list_changed_paths(guard.run_git, args.since_ref, args.head_ref)
        flat_root_violations, flat_root_candidates_scanned = (
            collect_flat_root_violations(
                repo_root=REPO_ROOT,
                changed_paths=changed_paths,
                read_text_from_ref=guard.read_text_from_ref,
                since_ref=args.since_ref,
            )
        )
        (
            layout_violations,
            crowded_namespace_families,
            namespace_layout_candidates_scanned,
        ) = (
            collect_namespace_layout_violations(
                repo_root=REPO_ROOT,
                changed_paths=changed_paths,
                read_text_from_ref=guard.read_text_from_ref,
                since_ref=args.since_ref,
            )
        )
        docs_sync_violations, namespace_docs_candidates_scanned = (
            collect_namespace_docs_sync_violations(
                repo_root=REPO_ROOT,
                changed_paths=changed_paths,
                read_text_from_ref=guard.read_text_from_ref,
                read_text_from_worktree=guard.read_text_from_worktree,
                since_ref=args.since_ref,
            )
        )
        crowding_violations, crowded_directories, crowded_directory_candidates_scanned = (
            collect_directory_crowding_violations(
                repo_root=REPO_ROOT,
                changed_paths=changed_paths,
                read_text_from_ref=guard.read_text_from_ref,
                since_ref=args.since_ref,
            )
        )
        root_role_findings, root_role_rules_scanned = collect_root_role_findings(
            repo_root=REPO_ROOT
        )
        compatibility_redirects = collect_compatibility_redirects(repo_root=REPO_ROOT)
    except RuntimeError as exc:
        return emit_runtime_error("check_package_layout", args.format, str(exc))

    report = _build_report(
        args=args,
        report_mode=report_mode,
        data={
            "changed_paths": changed_paths,
            "flat_root_violations": flat_root_violations,
            "flat_root_candidates_scanned": flat_root_candidates_scanned,
            "layout_violations": layout_violations,
            "crowded_namespace_families": crowded_namespace_families,
            "namespace_layout_candidates_scanned": namespace_layout_candidates_scanned,
            "docs_sync_violations": docs_sync_violations,
            "namespace_docs_candidates_scanned": namespace_docs_candidates_scanned,
            "crowding_violations": crowding_violations,
            "crowded_directories": crowded_directories,
            "crowded_directory_candidates_scanned": crowded_directory_candidates_scanned,
            "root_role_findings": root_role_findings,
            "root_role_rules_scanned": root_role_rules_scanned,
            "compatibility_redirects": compatibility_redirects,
        },
    )

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
