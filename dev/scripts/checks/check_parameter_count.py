#!/usr/bin/env python3
"""Guard against non-regressive growth of high-parameter functions in changed files."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

try:
    from check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
        utc_timestamp,
    )

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")
_is_rust_test_path = import_attr("rust_guard_common", "is_test_path")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = (
    *resolve_quality_scope_roots("rust_guard", repo_root=REPO_ROOT),
    *resolve_quality_scope_roots("python_guard", repo_root=REPO_ROOT),
)

PYTHON_PARAM_THRESHOLD = 6
RUST_PARAM_THRESHOLD = 7

RUST_FN_SIG_RE = re.compile(
    r"\bfn\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:<[^>]*>)?\s*\(([^)]*)\)",
    re.DOTALL,
)
SELF_PARAM_RE = re.compile(r"^\s*&?\s*(?:mut\s+)?self\s*$")


def _is_python_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")


def _count_rust_high_param_fns(text: str | None) -> int:
    if text is None:
        return 0
    text = strip_cfg_test_blocks(text)
    count = 0
    for match in RUST_FN_SIG_RE.finditer(text):
        params_raw = match.group(2).strip()
        if not params_raw:
            continue
        params = [p.strip() for p in params_raw.split(",") if p.strip()]
        params = [p for p in params if not SELF_PARAM_RE.match(p)]
        if len(params) > RUST_PARAM_THRESHOLD:
            count += 1
    return count


def _count_python_high_param_fns(text: str | None) -> int:
    if text is None:
        return 0
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = node.args
        param_count = len(args.args) + len(args.posonlyargs) + len(args.kwonlyargs)
        # Exclude self/cls
        if args.args and args.args[0].arg in ("self", "cls"):
            param_count -= 1
        if param_count > PYTHON_PARAM_THRESHOLD:
            count += 1
    return count


def _count_metrics(
    text: str | None, *, suffix: str = ".rs"
) -> dict[str, int]:
    if suffix == ".rs":
        return {"high_param_functions": _count_rust_high_param_fns(text)}
    if suffix == ".py":
        return {"high_param_functions": _count_python_high_param_fns(text)}
    return {"high_param_functions": 0}


def _growth(base: dict[str, int], current: dict[str, int]) -> dict[str, int]:
    return {key: current[key] - base[key] for key in base}


def _has_positive_growth(growth: dict[str, int]) -> bool:
    return any(value > 0 for value in growth.values())


def _render_md(report: dict) -> str:
    lines = ["# check_parameter_count", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- files_skipped_non_source: {report['files_skipped_non_source']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    totals = report["totals"]
    lines.append(
        "- aggregate_growth: "
        f"high_param_functions {totals['high_param_functions_growth']:+d}"
    )
    lines.append(
        f"- thresholds: python >{PYTHON_PARAM_THRESHOLD}, rust >{RUST_PARAM_THRESHOLD}"
    )

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            f"- Guidance: reduce parameter counts below thresholds "
            f"(Python >{PYTHON_PARAM_THRESHOLD}, Rust >{RUST_PARAM_THRESHOLD}). "
            "Extract parameter groups into dataclasses or structs."
        )
        for item in report["violations"]:
            growth_bits = [
                f"{key} {value:+d}"
                for key, value in item["growth"].items()
                if value > 0
            ]
            lines.append(f"- `{item['path']}`: {', '.join(growth_bits)}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    return build_since_ref_format_parser(__doc__ or "")


def main() -> int:
    args = _build_parser().parse_args()

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, base_map = list_changed_paths_with_base_map(
            guard.run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError as exc:
        return emit_runtime_error(
            "check_parameter_count", args.format, str(exc)
        )

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_source = 0
    files_skipped_tests = 0
    violations: list[dict] = []
    totals = {"high_param_functions_growth": 0}

    for path in changed_paths:
        if path.suffix not in (".rs", ".py"):
            files_skipped_non_source += 1
            continue
        if not is_under_target_roots(
            path, repo_root=REPO_ROOT, target_roots=TARGET_ROOTS
        ):
            files_skipped_non_source += 1
            continue
        if path.suffix == ".rs" and _is_rust_test_path(path):
            files_skipped_tests += 1
            continue
        if path.suffix == ".py" and _is_python_test_path(path):
            files_skipped_tests += 1
            continue

        files_considered += 1

        base_path = base_map.get(path, path)
        if args.since_ref:
            base_text = guard.read_text_from_ref(base_path, args.since_ref)
            current_text = guard.read_text_from_ref(path, args.head_ref)
        else:
            base_text = guard.read_text_from_ref(base_path, "HEAD")
            current_text = guard.read_text_from_worktree(path)

        base = _count_metrics(base_text, suffix=path.suffix)
        current = _count_metrics(current_text, suffix=path.suffix)
        growth = _growth(base, current)

        totals["high_param_functions_growth"] += growth["high_param_functions"]

        if _has_positive_growth(growth):
            violations.append(
                {
                    "path": path.as_posix(),
                    "base": base,
                    "current": current,
                    "growth": growth,
                }
            )

    report = {
        "command": "check_parameter_count",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "ok": len(violations) == 0,
        "files_changed": len(changed_paths),
        "files_considered": files_considered,
        "files_skipped_non_source": files_skipped_non_source,
        "files_skipped_tests": files_skipped_tests,
        "totals": totals,
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
