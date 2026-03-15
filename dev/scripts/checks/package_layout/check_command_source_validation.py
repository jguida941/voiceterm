#!/usr/bin/env python3
"""Guard Python command construction against unvalidated argv/env passthrough."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - package-style fallback for tests
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
        utc_timestamp,
    )

if __package__:
    from .command_source_validation_core import analyze_python_text
else:  # pragma: no cover - standalone script fallback
    from command_source_validation_core import analyze_python_text

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")

guard = GuardContext(REPO_ROOT)
TARGET_ROOTS = (*resolve_quality_scope_roots("python_guard", repo_root=REPO_ROOT),)


@dataclass(frozen=True)
class ScanContext:
    mode: str = "working-tree"
    since_ref: str | None = None
    head_ref: str | None = None


def _is_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")


def _collect_python_paths(
    *,
    repo_root: Path,
    candidate_paths: list[Path] | None = None,
    target_roots: tuple[Path, ...] | tuple[str, ...] = TARGET_ROOTS,
) -> tuple[list[Path], int]:
    paths: set[Path] = set()
    skipped_tests = 0

    if candidate_paths is None:
        for relative_root in target_roots:
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
        if not is_under_target_roots(candidate, repo_root=repo_root, target_roots=target_roots):
            continue
        relative = candidate.relative_to(repo_root) if candidate.is_absolute() else candidate
        if _is_test_path(relative):
            skipped_tests += 1
            continue
        paths.add(repo_root / candidate if not candidate.is_absolute() else candidate)

    return sorted(paths), skipped_tests


def _scan_file(path: Path, *, repo_root: Path) -> dict[str, object]:
    relative_path = path.relative_to(repo_root).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
        command_call_count, violations = analyze_python_text(text)
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        return {
            "path": relative_path,
            "command_call_count": 0,
            "violations": [],
            "parse_error": str(exc),
        }

    return {
        "path": relative_path,
        "command_call_count": command_call_count,
        "violations": violations,
        "parse_error": None,
    }


def _build_report_payload(
    *,
    files_scanned: int,
    files_skipped_tests: int,
    command_calls: int,
    violations: list[dict[str, object]],
    parse_errors: list[dict[str, str]],
    scan_context: ScanContext,
) -> dict[str, object]:
    files_with_violations = {str(item["path"]) for item in violations}
    return {
        "command": "check_command_source_validation",
        "timestamp": utc_timestamp(),
        "ok": not violations and not parse_errors,
        "mode": scan_context.mode,
        "since_ref": scan_context.since_ref,
        "head_ref": scan_context.head_ref,
        "files_scanned": files_scanned,
        "files_skipped_tests": files_skipped_tests,
        "command_calls": command_calls,
        "violations": violations,
        "parse_errors": parse_errors,
        "files_with_violations": len(files_with_violations),
        "target_roots": [path.as_posix() for path in TARGET_ROOTS],
    }


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    candidate_paths: list[Path] | None = None,
    target_roots: tuple[Path, ...] | tuple[str, ...] | None = None,
    scan_context: ScanContext | None = None,
) -> dict[str, object]:
    """Build the guard report for the selected Python files."""
    selected_paths = candidate_paths
    resolved_target_roots = target_roots or TARGET_ROOTS
    active_scan_context = scan_context or ScanContext()
    files, skipped_tests = _collect_python_paths(
        repo_root=repo_root,
        candidate_paths=selected_paths,
        target_roots=resolved_target_roots,
    )
    command_calls = 0
    violations: list[dict[str, object]] = []
    parse_errors: list[dict[str, str]] = []

    for path in files:
        result = _scan_file(path, repo_root=repo_root)
        command_calls += int(result["command_call_count"])
        parse_error = result["parse_error"]
        if parse_error is not None:
            parse_errors.append({"path": str(result["path"]), "error": str(parse_error)})
            continue
        for violation in result["violations"]:
            violations.append(
                {
                    "path": str(result["path"]),
                    "line": int(violation["line"]),
                    "reason": str(violation["reason"]),
                }
            )

    return _build_report_payload(
        files_scanned=len(files),
        files_skipped_tests=skipped_tests,
        command_calls=command_calls,
        violations=violations,
        parse_errors=parse_errors,
        scan_context=active_scan_context,
    )


def _render_md(report: dict[str, object]) -> str:
    lines = ["# check_command_source_validation", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_scanned: {report['files_scanned']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- command_calls: {report['command_calls']}")
    lines.append(f"- violations: {len(report['violations'])}")
    lines.append(f"- files_with_violations: {report['files_with_violations']}")
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
            "- Guidance: command construction must not pass free-form CLI/env/config "
            "strings or raw `sys.argv` directly into subprocess argv without a "
            "validator or structured allowlist."
        )
        for item in report["violations"]:
            lines.append(f"- `{item['path']}:{item['line']}`: {item['reason']}")
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
            scan_context=ScanContext(
                mode="commit-range" if args.since_ref else "working-tree",
                since_ref=args.since_ref,
                head_ref=args.head_ref,
            ),
        )
    except RuntimeError as exc:
        return emit_runtime_error("check_command_source_validation", args.format, str(exc))

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
