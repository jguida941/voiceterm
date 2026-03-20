#!/usr/bin/env python3
"""Guard against source-file shape drift in Rust/Python code."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, import_attr, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, emit_runtime_error, import_attr, utc_timestamp

_ia = import_attr
BEST_PRACTICE_DOCS = _ia("code_shape_policy", "BEST_PRACTICE_DOCS")
FUNCTION_POLICY_EXCEPTIONS = _ia("code_shape_policy", "FUNCTION_POLICY_EXCEPTIONS")
LANGUAGE_POLICIES = _ia("code_shape_policy", "LANGUAGE_POLICIES")
PATH_POLICY_OVERRIDES = _ia("code_shape_policy", "PATH_POLICY_OVERRIDES")
SHAPE_AUDIT_GUIDANCE = _ia("code_shape_policy", "SHAPE_AUDIT_GUIDANCE")
FunctionShapePolicy = _ia("code_shape_policy", "FunctionShapePolicy")
ShapePolicy = _ia("code_shape_policy", "ShapePolicy")
function_policy_for_path = _ia("code_shape_policy", "function_policy_for_path")
policy_for_path = _ia("code_shape_policy", "policy_for_path")
validate_override_caps = _ia("code_shape_policy", "validate_override_caps")
collect_override_cap_records = _ia("code_shape_policy", "collect_override_cap_records")
_build_mixed_concern_violation = _ia(
    "code_shape_support.mixed_concerns", "mixed_concern_violation"
)
_find_function_clusters = _ia(
    "code_shape_support.mixed_concerns", "find_function_clusters"
)
_mixed_concern_threshold = _ia(
    "code_shape_support.mixed_concerns", "CLUSTER_THRESHOLD_MEDIUM"
)
_evaluate_override_cap_violations = _ia("code_shape_support.override_caps", "evaluate_override_cap_violations")
_load_override_cap_baseline_records_impl = _ia("code_shape_support.override_caps", "load_override_cap_baseline_records")
_DocsContext = _ia("code_shape_support.override_caps", "DocsContext")
evaluate_function_shape_impl = _ia("code_shape_function_policy", "evaluate_function_shape")
scan_python_functions_impl = _ia("code_shape_function_policy", "scan_python_functions")
scan_rust_functions_impl = _ia("code_shape_function_policy", "scan_rust_functions")
_scan_rust_functions = scan_rust_functions_impl
_violation = _ia("code_shape_support.evaluators", "violation")
_evaluate_shape = _ia("code_shape_support.evaluators", "evaluate_shape")
_evaluate_absolute_shape = _ia("code_shape_support.evaluators", "evaluate_absolute_shape")
_evaluate_stale_path_override = _ia("code_shape_support.evaluators", "evaluate_stale_path_override")
_recent_history_line_counts = _ia("code_shape_support.evaluators", "recent_history_line_counts")
_render_md = _ia("code_shape_support.render", "render_md")
GuardContext = _ia("rust_guard_common", "GuardContext")
list_changed_paths = _ia("rust_guard_common", "list_changed_paths")

guard = GuardContext(REPO_ROOT)
DEFAULT_STALE_OVERRIDE_REVIEW_WINDOW_DAYS = 30
OVERRIDE_CAP_POLICY_PATH = Path("dev/scripts/checks/code_shape_policy.py")

_SCANNER_BY_EXT = {
    ".rs": scan_rust_functions_impl,
    ".py": scan_python_functions_impl,
}


def _list_all_source_paths() -> list[Path]:
    paths: set[Path] = set()
    for line in guard.run_git(["git", "ls-files"]).stdout.splitlines():
        if not line.strip():
            continue
        path = Path(line.strip())
        policy, _ = policy_for_path(path)
        if policy is not None:
            paths.add(path)

    for line in guard.run_git(
        ["git", "ls-files", "--others", "--exclude-standard"]
    ).stdout.splitlines():
        if not line.strip():
            continue
        path = Path(line.strip())
        policy, _ = policy_for_path(path)
        if policy is not None:
            paths.add(path)

    return sorted(paths)

def _is_test_path(path: Path) -> bool:
    normalized = f"/{path.as_posix()}/"
    name = path.name

    if path.suffix == ".rs":
        return (
            "/tests/" in normalized or name == "tests.rs" or name.endswith("_test.rs")
        )
    if path.suffix == ".py":
        return (
            "/tests/" in normalized
            or name.startswith("test_")
            or name.endswith("_test.py")
        )
    return False


def _should_skip_test_path(path: Path, policy_source: str | None) -> bool:
    if not _is_test_path(path):
        return False
    # Explicit path overrides can opt specific high-signal tests into shape governance.
    return not (policy_source and policy_source.startswith("path_override:"))


def _count_lines(text: str | None) -> int | None:
    if text is None:
        return None
    return len(text.splitlines())


def _evaluate_function_shape(*, path, policy, policy_source, text, today):
    return evaluate_function_shape_impl(
        path=path, policy=policy, policy_source=policy_source, text=text, today=today,
        function_policy_exceptions=FUNCTION_POLICY_EXCEPTIONS,
        best_practice_docs=BEST_PRACTICE_DOCS, scanner=_SCANNER_BY_EXT.get(path.suffix),
    )


def _load_override_cap_baseline_records(ref: str | None) -> list[dict[str, object]]:
    return _load_override_cap_baseline_records_impl(
        ref=ref,
        repo_root=REPO_ROOT,
        policy_path=OVERRIDE_CAP_POLICY_PATH,
        read_text_from_ref=guard.read_text_from_ref,
        collect_override_cap_records=collect_override_cap_records,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--absolute",
        action="store_true",
        help="Scan all tracked/untracked source files against absolute hard limits.",
    )
    parser.add_argument(
        "--stale-override-review-window-days",
        type=int,
        default=DEFAULT_STALE_OVERRIDE_REVIEW_WINDOW_DAYS,
        help=(
            "Review window used to detect stale PATH_POLICY_OVERRIDES entries. "
            "Set to 0 to disable stale-override checks."
        ),
    )
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument(
        "--head-ref", default="HEAD", help="Head ref used with --since-ref"
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    if args.absolute and args.since_ref:
        return emit_runtime_error(
            "check_code_shape",
            args.format,
            "--absolute cannot be combined with --since-ref/--head-ref",
        )

    try:
        if args.absolute:
            changed_paths = _list_all_source_paths()
        else:
            if args.since_ref:
                guard.validate_ref(args.since_ref)
                guard.validate_ref(args.head_ref)
            changed_paths = list_changed_paths(guard.run_git, args.since_ref, args.head_ref)
    except RuntimeError as exc:
        return emit_runtime_error("check_code_shape", args.format, str(exc))

    mode = (
        "absolute"
        if args.absolute
        else ("commit-range" if args.since_ref else "working-tree")
    )
    violations: list[dict] = []
    files_skipped_non_source = 0
    files_skipped_tests = 0
    files_considered = 0
    files_using_path_overrides = 0
    function_policies_applied = 0
    function_exceptions_used = 0
    function_violations = 0
    mixed_concern_violations = 0
    stale_override_review_window_days = max(args.stale_override_review_window_days, 0)
    stale_override_candidates_scanned = 0
    stale_override_candidates_skipped = 0
    override_cap_warnings = validate_override_caps()
    baseline_override_cap_records = _load_override_cap_baseline_records(
        args.since_ref if args.since_ref else "HEAD"
    )
    _docs_ctx = _DocsContext(
        best_practice_docs=BEST_PRACTICE_DOCS,
        shape_audit_guidance=SHAPE_AUDIT_GUIDANCE,
    )
    override_cap_violations = _evaluate_override_cap_violations(
        mode=mode,
        changed_paths=changed_paths,
        current_records=override_cap_warnings,
        baseline_records=baseline_override_cap_records,
        docs=_docs_ctx,
    )
    override_cap_violation_paths = {item["path"] for item in override_cap_violations}
    override_cap_warnings = [
        item for item in override_cap_warnings if item["path"] not in override_cap_violation_paths
    ]
    violations.extend(override_cap_violations)

    for path in changed_paths:
        policy, policy_source = policy_for_path(path)
        if policy is None:
            files_skipped_non_source += 1
            continue
        if _should_skip_test_path(path, policy_source):
            files_skipped_tests += 1
            continue

        files_considered += 1
        if policy_source and policy_source.startswith("path_"):
            files_using_path_overrides += 1

        current_text: str | None
        ps = policy_source or "unknown"
        if args.absolute:
            current_text = guard.read_text_from_worktree(path)
            violation = _evaluate_absolute_shape(
                path=path, policy=policy, policy_source=ps,
                current_lines=_count_lines(current_text),
            )
        else:
            if args.since_ref:
                base_lines = _count_lines(guard.read_text_from_ref(path, args.since_ref))
                current_text = guard.read_text_from_ref(path, args.head_ref)
                current_lines = _count_lines(current_text)
            else:
                base_lines = _count_lines(guard.read_text_from_ref(path, "HEAD"))
                current_text = guard.read_text_from_worktree(path)
                current_lines = _count_lines(current_text)

            violation = _evaluate_shape(
                path=path, policy=policy, policy_source=ps,
                base_lines=base_lines, current_lines=current_lines,
            )
        if violation:
            violations.append(violation)

        if not args.absolute and path.suffix == ".py" and current_text is not None:
            clusters = _find_function_clusters(current_text)
            if len(clusters) >= _mixed_concern_threshold:
                violations.append(
                    _build_mixed_concern_violation(
                        path=path,
                        clusters=clusters,
                        best_practice_docs=BEST_PRACTICE_DOCS,
                        shape_audit_guidance=SHAPE_AUDIT_GUIDANCE,
                    )
                )
                mixed_concern_violations += 1

        function_policy, function_policy_source = function_policy_for_path(path)
        if function_policy is not None:
            function_policies_applied += 1
            function_shape_violations, exception_hits = _evaluate_function_shape(
                path=path, policy=function_policy,
                policy_source=function_policy_source or "unknown",
                text=current_text, today=date.today(),
            )
            function_exceptions_used += exception_hits
            function_violations += len(function_shape_violations)
            violations.extend(function_shape_violations)

    try:
        violation_paths = {item["path"] for item in violations}
        if stale_override_review_window_days <= 0:
            stale_override_candidates_skipped = len(PATH_POLICY_OVERRIDES)
        else:
            for override_path, override_policy in PATH_POLICY_OVERRIDES.items():
                path = Path(override_path)
                default_policy = LANGUAGE_POLICIES.get(path.suffix)
                if default_policy is None:
                    stale_override_candidates_skipped += 1
                    continue
                if override_policy.soft_limit <= default_policy.soft_limit:
                    stale_override_candidates_skipped += 1
                    continue
                stale_override_candidates_scanned += 1
                stale_violation = _evaluate_stale_path_override(
                    path=path, override_policy=override_policy,
                    language_default_policy=default_policy,
                    policy_source=f"path_override:{override_path}",
                    current_lines=_count_lines(guard.read_text_from_worktree(path)),
                    review_window=(
                        stale_override_review_window_days,
                        _recent_history_line_counts(
                            path, stale_override_review_window_days, guard, _count_lines
                        ),
                    ),
                )
                if stale_violation and stale_violation["path"] not in violation_paths:
                    violations.append(stale_violation)
                    violation_paths.add(stale_violation["path"])
    except RuntimeError as exc:
        return emit_runtime_error("check_code_shape", args.format, str(exc))

    report = {
        "command": "check_code_shape",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": args.since_ref if mode == "commit-range" else None,
        "head_ref": args.head_ref if mode == "commit-range" else None,
        "ok": len(violations) == 0,
        "files_changed": len(changed_paths),
        "files_considered": files_considered,
        "files_using_path_overrides": files_using_path_overrides,
        "function_policies_applied": function_policies_applied,
        "function_exceptions_used": function_exceptions_used,
        "function_violations": function_violations,
        "mixed_concern_violations": mixed_concern_violations,
        "stale_override_review_window_days": stale_override_review_window_days,
        "stale_override_candidates_scanned": stale_override_candidates_scanned,
        "stale_override_candidates_skipped": stale_override_candidates_skipped,
        "files_skipped_non_source": files_skipped_non_source,
        "files_skipped_tests": files_skipped_tests,
        "warnings": override_cap_warnings,
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
