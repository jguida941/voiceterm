#!/usr/bin/env python3
"""Review probe: detect Python files that mix multiple independent concerns.

A file has mixed concerns when it contains 3+ top-level functions that form
independent call-graph clusters. Each cluster is a separate concern that
should usually live in its own module.

This probe always exits 0 and emits structured risk hints for review.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the checks root is on sys.path so sibling modules are importable
_CHECKS_ROOT = str(Path(__file__).resolve().parent.parent)
if _CHECKS_ROOT not in sys.path:
    sys.path.insert(0, _CHECKS_ROOT)

try:
    from check_bootstrap import (
        REPO_ROOT,
        import_attr,
        resolve_quality_scope_roots,
    )
    from probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        import_attr,
        resolve_quality_scope_roots,
    )
    from dev.scripts.checks.probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )

from code_shape_probes.common import load_probe_text, should_scan_python_probe_path

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")
is_review_probe_test_path = import_attr(
    "probe_path_filters", "is_review_probe_test_path"
)
_cluster_signals_impl = import_attr(
    "code_shape_support.mixed_concerns", "cluster_signals"
)
CLUSTER_THRESHOLD_MEDIUM = import_attr(
    "code_shape_support.mixed_concerns", "CLUSTER_THRESHOLD_MEDIUM"
)
CLUSTER_THRESHOLD_HIGH = import_attr(
    "code_shape_support.mixed_concerns", "CLUSTER_THRESHOLD_HIGH"
)
find_function_clusters_impl = import_attr(
    "code_shape_support.mixed_concerns", "find_function_clusters"
)

guard = GuardContext(REPO_ROOT)
TARGET_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)
REVIEW_LENS = "design_quality"

AI_INSTRUCTIONS = {
    "medium": (
        "This file contains {cluster_count} independent top-level function "
        "groups. Split each cluster into its own module so one file owns one "
        "concern."
    ),
    "high": (
        "This file contains {cluster_count} independent top-level function "
        "groups. It is acting like a multi-concern bundle; split each cluster "
        "into its own module before the file becomes a hidden God file."
    ),
}


def find_function_clusters(source: str) -> list[set[str]]:
    return find_function_clusters_impl(source)


def _cluster_signals(clusters: list[set[str]]) -> list[str]:
    return _cluster_signals_impl(clusters)


def _build_risk_hint(path: Path, clusters: list[set[str]]) -> RiskHint:
    severity = "high" if len(clusters) >= CLUSTER_THRESHOLD_HIGH else "medium"
    return RiskHint(
        file=path.as_posix(),
        symbol=path.stem,
        risk_type="mixed_concerns",
        severity=severity,
        signals=_cluster_signals(clusters),
        ai_instruction=AI_INSTRUCTIONS[severity].format(cluster_count=len(clusters)),
        review_lens=REVIEW_LENS,
        attach_docs=[
            "dev/guides/DEVELOPMENT.md#what-checks-protect-us",
            "dev/scripts/README.md#probe-report",
        ],
    )


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_mixed_concerns")

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, _base_map = list_changed_paths_with_base_map(
            guard.run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError:
        return emit_probe_report(report, output_format=args.format)

    report.mode = "commit-range" if args.since_ref else "working-tree"
    report.since_ref = args.since_ref
    report.head_ref = args.head_ref
    files_with_hints: set[str] = set()

    for path in changed_paths:
        if not should_scan_python_probe_path(
            path,
            target_roots=TARGET_ROOTS,
            is_review_probe_test_path=is_review_probe_test_path,
        ):
            continue

        report.files_scanned += 1
        text = load_probe_text(
            path,
            guard=guard,
            since_ref=args.since_ref,
            head_ref=args.head_ref,
        )
        if text is None:
            continue

        clusters = find_function_clusters(text)
        if len(clusters) < CLUSTER_THRESHOLD_MEDIUM:
            continue

        files_with_hints.add(path.as_posix())
        report.risk_hints.append(_build_risk_hint(path, clusters))

    report.files_with_hints = len(files_with_hints)
    return emit_probe_report(report, output_format=args.format)


if __name__ == "__main__":
    sys.exit(main())
