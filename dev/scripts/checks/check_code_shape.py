#!/usr/bin/env python3
"""Guard against source-file shape drift in Rust/Python code."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

try:
    from check_bootstrap import emit_runtime_error, import_attr, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import emit_runtime_error, import_attr, utc_timestamp

BEST_PRACTICE_DOCS = import_attr("code_shape_policy", "BEST_PRACTICE_DOCS")
FUNCTION_POLICY_EXCEPTIONS = import_attr(
    "code_shape_policy", "FUNCTION_POLICY_EXCEPTIONS"
)
LANGUAGE_POLICIES = import_attr("code_shape_policy", "LANGUAGE_POLICIES")
PATH_POLICY_OVERRIDES = import_attr("code_shape_policy", "PATH_POLICY_OVERRIDES")
SHAPE_AUDIT_GUIDANCE = import_attr("code_shape_policy", "SHAPE_AUDIT_GUIDANCE")
FunctionShapePolicy = import_attr("code_shape_policy", "FunctionShapePolicy")
ShapePolicy = import_attr("code_shape_policy", "ShapePolicy")
function_policy_for_path = import_attr("code_shape_policy", "function_policy_for_path")
policy_for_path = import_attr("code_shape_policy", "policy_for_path")
evaluate_function_shape_impl = import_attr(
    "code_shape_function_policy", "evaluate_function_shape"
)
scan_python_functions_impl = import_attr(
    "code_shape_function_policy", "scan_python_functions"
)
scan_rust_functions_impl = import_attr(
    "code_shape_function_policy", "scan_rust_functions"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")
list_changed_paths = import_attr("rust_guard_common", "list_changed_paths")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)
DEFAULT_STALE_OVERRIDE_REVIEW_WINDOW_DAYS = 30


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


def _scan_rust_functions(text: str | None) -> list[dict]:
    return scan_rust_functions_impl(text)


_SCANNER_BY_EXT = {
    ".rs": scan_rust_functions_impl,
    ".py": scan_python_functions_impl,
}


def _evaluate_function_shape(
    *,
    path: Path,
    policy: FunctionShapePolicy,
    policy_source: str,
    text: str | None,
    today: date,
) -> tuple[list[dict], int]:
    return evaluate_function_shape_impl(
        path=path,
        policy=policy,
        policy_source=policy_source,
        text=text,
        today=today,
        function_policy_exceptions=FUNCTION_POLICY_EXCEPTIONS,
        best_practice_docs=BEST_PRACTICE_DOCS,
        scanner=_SCANNER_BY_EXT.get(path.suffix),
    )


def _violation(
    *,
    path: Path,
    reason: str,
    guidance: str,
    policy: ShapePolicy,
    policy_source: str,
    base_lines: int | None,
    current_lines: int,
) -> dict:
    growth = None if base_lines is None else current_lines - base_lines
    docs_refs = BEST_PRACTICE_DOCS.get(path.suffix, ())
    guidance_parts = [guidance]
    if reason != "current_file_missing":
        guidance_parts.append(SHAPE_AUDIT_GUIDANCE)
    if docs_refs:
        guidance_parts.append("Best-practice refs: " + ", ".join(docs_refs))
    return {
        "path": path.as_posix(),
        "reason": reason,
        "guidance": " ".join(guidance_parts),
        "best_practice_refs": list(docs_refs),
        "base_lines": base_lines,
        "current_lines": current_lines,
        "growth": growth,
        "policy": {
            "soft_limit": policy.soft_limit,
            "hard_limit": policy.hard_limit,
            "oversize_growth_limit": policy.oversize_growth_limit,
            "hard_lock_growth_limit": policy.hard_lock_growth_limit,
        },
        "policy_source": policy_source,
    }


def _evaluate_shape(
    *,
    path: Path,
    policy: ShapePolicy,
    policy_source: str,
    base_lines: int | None,
    current_lines: int | None,
) -> dict | None:
    if current_lines is None:
        return _violation(
            path=path,
            reason="current_file_missing",
            guidance="File is missing in current tree; rerun after resolving rename/delete state.",
            policy=policy,
            policy_source=policy_source,
            base_lines=base_lines,
            current_lines=0,
        )

    if base_lines is None:
        if current_lines > policy.soft_limit:
            return _violation(
                path=path,
                reason="new_file_exceeds_soft_limit",
                guidance="Split the new file before merge or keep it under the soft limit.",
                policy=policy,
                policy_source=policy_source,
                base_lines=base_lines,
                current_lines=current_lines,
            )
        return None

    growth = current_lines - base_lines
    if base_lines <= policy.soft_limit and current_lines > policy.soft_limit:
        return _violation(
            path=path,
            reason="crossed_soft_limit",
            guidance="Refactor into smaller modules before crossing the soft limit.",
            policy=policy,
            policy_source=policy_source,
            base_lines=base_lines,
            current_lines=current_lines,
        )

    if (
        base_lines <= policy.hard_limit
        and current_lines > policy.hard_limit
        and growth > 0
    ):
        return _violation(
            path=path,
            reason="crossed_hard_limit",
            guidance="Hard limit exceeded; split and reduce file size before merge.",
            policy=policy,
            policy_source=policy_source,
            base_lines=base_lines,
            current_lines=current_lines,
        )

    if base_lines > policy.hard_limit and growth > policy.hard_lock_growth_limit:
        return _violation(
            path=path,
            reason="hard_locked_file_grew",
            guidance="File is already above hard limit; do not grow it further.",
            policy=policy,
            policy_source=policy_source,
            base_lines=base_lines,
            current_lines=current_lines,
        )

    if base_lines > policy.soft_limit and growth > policy.oversize_growth_limit:
        return _violation(
            path=path,
            reason="oversize_file_growth_exceeded_budget",
            guidance=(
                "File is already above soft limit; keep growth within budget or decompose first."
            ),
            policy=policy,
            policy_source=policy_source,
            base_lines=base_lines,
            current_lines=current_lines,
        )

    return None


def _evaluate_absolute_shape(
    *,
    path: Path,
    policy: ShapePolicy,
    policy_source: str,
    current_lines: int | None,
) -> dict | None:
    if current_lines is None:
        return _violation(
            path=path,
            reason="current_file_missing",
            guidance="File is missing in current tree; rerun after resolving rename/delete state.",
            policy=policy,
            policy_source=policy_source,
            base_lines=None,
            current_lines=0,
        )

    if current_lines > policy.hard_limit:
        return _violation(
            path=path,
            reason="absolute_hard_limit_exceeded",
            guidance="File exceeds absolute hard limit; split modules or lower file size before merge.",
            policy=policy,
            policy_source=policy_source,
            base_lines=None,
            current_lines=current_lines,
        )

    return None


def _recent_history_line_counts(path: Path, review_window_days: int) -> list[int]:
    if review_window_days <= 0:
        return []
    since_value = f"{review_window_days}.days"
    commits = guard.run_git(
        ["git", "log", "--since", since_value, "--format=%H", "--", path.as_posix()]
    ).stdout.splitlines()
    line_counts: list[int] = []
    seen: set[str] = set()
    for commit in commits:
        ref = commit.strip()
        if not ref or ref in seen:
            continue
        seen.add(ref)
        lines = _count_lines(guard.read_text_from_ref(path, ref))
        if lines is not None:
            line_counts.append(lines)
    return line_counts


def _evaluate_stale_path_override(
    *,
    path: Path,
    override_policy: ShapePolicy,
    language_default_policy: ShapePolicy,
    policy_source: str,
    current_lines: int | None,
    review_window_days: int,
    review_window_line_counts: list[int],
) -> dict | None:
    if current_lines is None:
        return None
    if override_policy.soft_limit <= language_default_policy.soft_limit:
        return None

    max_recent_lines = max(
        [current_lines, *review_window_line_counts], default=current_lines
    )
    if max_recent_lines > language_default_policy.soft_limit:
        return None

    return _violation(
        path=path,
        reason="stale_path_override_below_default_soft_limit",
        guidance=(
            "PATH_POLICY_OVERRIDES entry is looser than the language default and the file stayed "
            f"at or below the language soft limit for {review_window_days} days. "
            "Remove the override or tighten it to a stricter-than-default budget."
        ),
        policy=override_policy,
        policy_source=policy_source,
        base_lines=max_recent_lines,
        current_lines=current_lines,
    )


def _render_md(report: dict) -> str:
    lines = ["# check_code_shape", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(
        f"- files_using_path_overrides: {report['files_using_path_overrides']}"
    )
    lines.append(f"- function_policies_applied: {report['function_policies_applied']}")
    lines.append(f"- function_exceptions_used: {report['function_exceptions_used']}")
    lines.append(f"- function_violations: {report['function_violations']}")
    lines.append(
        f"- stale_override_review_window_days: {report['stale_override_review_window_days']}"
    )
    lines.append(
        f"- stale_override_candidates_scanned: {report['stale_override_candidates_scanned']}"
    )
    lines.append(
        f"- stale_override_candidates_skipped: {report['stale_override_candidates_skipped']}"
    )
    lines.append(f"- files_skipped_non_source: {report['files_skipped_non_source']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for violation in report["violations"]:
            if "function_name" in violation:
                lines.append(
                    f"- `{violation['path']}::{violation['function_name']}` "
                    f"({violation['reason']}): {violation['guidance']} "
                    f"[policy: {violation['policy_source']}]"
                )
                continue
            growth = violation["growth"]
            growth_label = "n/a" if growth is None else f"{growth:+d}"
            lines.append(
                f"- `{violation['path']}` ({violation['reason']}): "
                f"{violation['base_lines']} -> {violation['current_lines']} "
                f"(growth {growth_label}); {violation['guidance']} "
                f"[policy: {violation['policy_source']}]"
            )
    return "\n".join(lines)


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
    stale_override_review_window_days = max(args.stale_override_review_window_days, 0)
    stale_override_candidates_scanned = 0
    stale_override_candidates_skipped = 0

    for path in changed_paths:
        policy, policy_source = policy_for_path(path)
        if policy is None:
            files_skipped_non_source += 1
            continue
        if _should_skip_test_path(path, policy_source):
            files_skipped_tests += 1
            continue

        files_considered += 1
        if policy_source and policy_source.startswith("path_override:"):
            files_using_path_overrides += 1

        current_text: str | None
        if args.absolute:
            current_text = guard.read_text_from_worktree(path)
            violation = _evaluate_absolute_shape(
                path=path,
                policy=policy,
                policy_source=policy_source or "unknown",
                current_lines=_count_lines(current_text),
            )
        else:
            if args.since_ref:
                base_lines = _count_lines(
                    guard.read_text_from_ref(path, args.since_ref)
                )
                current_text = guard.read_text_from_ref(path, args.head_ref)
                current_lines = _count_lines(current_text)
            else:
                base_lines = _count_lines(guard.read_text_from_ref(path, "HEAD"))
                current_text = guard.read_text_from_worktree(path)
                current_lines = _count_lines(current_text)

            violation = _evaluate_shape(
                path=path,
                policy=policy,
                policy_source=policy_source or "unknown",
                base_lines=base_lines,
                current_lines=current_lines,
            )
        if violation:
            violations.append(violation)

        function_policy, function_policy_source = function_policy_for_path(path)
        if function_policy is not None:
            function_policies_applied += 1
            function_shape_violations, exception_hits = _evaluate_function_shape(
                path=path,
                policy=function_policy,
                policy_source=function_policy_source or "unknown",
                text=current_text,
                today=date.today(),
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
                    path=path,
                    override_policy=override_policy,
                    language_default_policy=default_policy,
                    policy_source=f"path_override:{override_path}",
                    current_lines=_count_lines(guard.read_text_from_worktree(path)),
                    review_window_days=stale_override_review_window_days,
                    review_window_line_counts=_recent_history_line_counts(
                        path, stale_override_review_window_days
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
        "stale_override_review_window_days": stale_override_review_window_days,
        "stale_override_candidates_scanned": stale_override_candidates_scanned,
        "stale_override_candidates_skipped": stale_override_candidates_skipped,
        "files_skipped_non_source": files_skipped_non_source,
        "files_skipped_tests": files_skipped_tests,
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
