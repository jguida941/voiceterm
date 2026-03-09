#!/usr/bin/env python3
"""Guard Python tooling subprocess.run calls to require explicit check=."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

try:
    from check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - package-style fallback for tests
    from dev.scripts.checks.check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        utc_timestamp,
    )

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = (
    Path("dev/scripts"),
    Path("app/operator_console"),
)


def _is_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")
def _collect_python_paths(
    *,
    repo_root: Path,
    candidate_paths: list[Path] | None = None,
) -> tuple[list[Path], int]:
    paths: set[Path] = set()
    skipped_tests = 0

    if candidate_paths is None:
        for relative_root in TARGET_ROOTS:
            root = repo_root / relative_root
            if not root.is_dir():
                continue
            for path in root.rglob("*.py"):
                relative = path.relative_to(repo_root)
                if _is_test_path(relative):
                    skipped_tests += 1
                    continue
                paths.add(path)
        return sorted(paths), skipped_tests

    for candidate in candidate_paths:
        if candidate.suffix != ".py":
            continue
        if not is_under_target_roots(
            candidate, repo_root=repo_root, target_roots=TARGET_ROOTS
        ):
            continue
        relative = (
            candidate.relative_to(repo_root)
            if candidate.is_absolute()
            else candidate
        )
        if _is_test_path(relative):
            skipped_tests += 1
            continue
        paths.add(repo_root / candidate if not candidate.is_absolute() else candidate)

    return sorted(paths), skipped_tests


def _collect_run_bindings(tree: ast.AST) -> tuple[set[str], set[str]]:
    subprocess_module_names = {"subprocess"}
    subprocess_run_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    subprocess_module_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                if alias.name == "run":
                    subprocess_run_names.add(alias.asname or alias.name)
    return subprocess_module_names, subprocess_run_names


def _call_uses_subprocess_run(
    node: ast.Call,
    *,
    subprocess_module_names: set[str],
    subprocess_run_names: set[str],
) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr == "run":
        return isinstance(func.value, ast.Name) and func.value.id in subprocess_module_names
    if isinstance(func, ast.Name):
        return func.id in subprocess_run_names
    return False


def _find_run_calls_without_explicit_check(text: str) -> tuple[int, list[int]]:
    tree = ast.parse(text)
    subprocess_module_names, subprocess_run_names = _collect_run_bindings(tree)
    total_calls = 0
    violation_lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not _call_uses_subprocess_run(
            node,
            subprocess_module_names=subprocess_module_names,
            subprocess_run_names=subprocess_run_names,
        ):
            continue
        total_calls += 1
        if any(keyword.arg == "check" for keyword in node.keywords):
            continue
        violation_lines.append(node.lineno)
    return total_calls, violation_lines


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    candidate_paths: list[Path] | None = None,
    mode: str = "working-tree",
    since_ref: str | None = None,
    head_ref: str | None = None,
) -> dict:
    files, skipped_tests = _collect_python_paths(
        repo_root=repo_root,
        candidate_paths=candidate_paths,
    )
    violations: list[dict] = []
    parse_errors: list[dict] = []
    subprocess_run_calls = 0

    for path in files:
        relative_path = path.relative_to(repo_root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
            call_count, violation_lines = _find_run_calls_without_explicit_check(text)
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            parse_errors.append({"path": relative_path, "error": str(exc)})
            continue

        subprocess_run_calls += call_count
        for line in violation_lines:
            violations.append(
                {
                    "path": relative_path,
                    "line": line,
                    "reason": "subprocess.run call is missing explicit check=",
                }
            )

    return {
        "command": "check_python_subprocess_policy",
        "timestamp": utc_timestamp(),
        "ok": not violations and not parse_errors,
        "mode": mode,
        "since_ref": since_ref,
        "head_ref": head_ref,
        "files_scanned": len(files),
        "files_skipped_tests": skipped_tests,
        "subprocess_run_calls": subprocess_run_calls,
        "violations": violations,
        "parse_errors": parse_errors,
        "target_roots": [path.as_posix() for path in TARGET_ROOTS],
    }


def _render_md(report: dict) -> str:
    lines = ["# check_python_subprocess_policy", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_scanned: {report['files_scanned']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- subprocess_run_calls: {report['subprocess_run_calls']}")
    lines.append(f"- violations: {len(report['violations'])}")
    lines.append(f"- parse_errors: {len(report['parse_errors'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    if report["parse_errors"]:
        lines.append("")
        lines.append("## Parse errors")
        for item in report["parse_errors"]:
            lines.append(f"- `{item['path']}`: {item['error']}")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: every repo-owned `subprocess.run(...)` call in tooling/app "
            "code must pass `check=` explicitly so failure semantics are intentional."
        )
        for item in report["violations"]:
            lines.append(
                f"- `{item['path']}:{item['line']}`: {item['reason']}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    return build_since_ref_format_parser(__doc__ or "")


def main() -> int:
    args = _build_parser().parse_args()
    try:
        changed_paths: list[Path] | None = None
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
            changed_paths, _base_map = list_changed_paths_with_base_map(
                guard.run_git,
                args.since_ref,
                args.head_ref,
            )
        report = build_report(
            repo_root=REPO_ROOT,
            candidate_paths=changed_paths,
            mode="commit-range" if args.since_ref else "working-tree",
            since_ref=args.since_ref,
            head_ref=args.head_ref,
        )
    except RuntimeError as exc:
        return emit_runtime_error("check_python_subprocess_policy", args.format, str(exc))

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
