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
collect_namespace_docs_sync_violations = import_attr(
    "package_layout.support",
    "collect_namespace_docs_sync_violations",
)
collect_namespace_layout_violations = import_attr(
    "package_layout.support",
    "collect_namespace_layout_violations",
)
list_changed_paths = import_attr("rust_guard_common", "list_changed_paths")
GuardContext = import_attr("rust_guard_common", "GuardContext")

guard = GuardContext(REPO_ROOT)


def _crowding_suffix(crowded: dict) -> str:
    shim_files = int(crowded.get("shim_files", 0) or 0)
    total_files = int(crowded.get("total_files", crowded["current_files"]) or 0)
    if shim_files <= 0:
        return ""
    return f", {shim_files} approved shims excluded, {total_files} total files"


def _render_md(report: dict) -> str:
    lines = ["# check_package_layout", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
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
    lines.append(f"- violations: {len(report['violations'])}")
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

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for violation in report["violations"]:
            lines.append(
                f"- `{violation['path']}` ({violation['reason']}): "
                f"{violation['guidance']} [policy: {violation['policy_source']}]"
            )
    return "\n".join(lines)


def main() -> int:
    args = build_since_ref_format_parser(__doc__ or "").parse_args()
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
    except RuntimeError as exc:
        return emit_runtime_error("check_package_layout", args.format, str(exc))

    violations = [
        *flat_root_violations,
        *layout_violations,
        *docs_sync_violations,
        *crowding_violations,
    ]
    report = {
        "command": "check_package_layout",
        "timestamp": utc_timestamp(),
        "mode": report_mode,
        "since_ref": None if report_mode == "adoption-scan" else args.since_ref,
        "head_ref": None if report_mode == "adoption-scan" else args.head_ref,
        "ok": len(violations) == 0,
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
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
