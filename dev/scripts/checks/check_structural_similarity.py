#!/usr/bin/env python3
"""Guard against non-regressive growth of structurally similar function pairs across files.

Unlike check_function_duplication (which catches identical normalized bodies),
this guard detects functions with the same control-flow shape but different
variable names — a common pattern when AI agents copy-paste and rename.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
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
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
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
_is_rust_test_path = import_attr("rust_guard_common", "is_test_path")
scan_rust_functions = import_attr("code_shape_function_policy", "scan_rust_functions")
scan_python_functions = import_attr("code_shape_function_policy", "scan_python_functions")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")
mask_rust_comments_and_strings = import_attr(
    "rust_check_text_utils", "mask_rust_comments_and_strings"
)

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = (
    Path("rust/src"),
    Path("dev/scripts/devctl"),
    Path("app/operator_console"),
)

MIN_BODY_LINES = 8
IDENT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
NUMBER_RE = re.compile(r"\b\d+\b")
STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')


def _is_python_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")


def _normalize_python_body(text: str, func: dict) -> str | None:
    """Normalize a Python function body by replacing identifiers and literals."""
    lines = text.splitlines()
    start = func["start_line"]  # 1-based
    end = func["end_line"]
    body_lines = lines[start:end]  # skip the def line
    if len(body_lines) < MIN_BODY_LINES:
        return None
    body = "\n".join(body_lines)
    body = STRING_RE.sub('""', body)
    body = NUMBER_RE.sub("0", body)
    body = IDENT_RE.sub("_", body)
    return body.strip()


def _normalize_rust_body(text: str, func: dict) -> str | None:
    """Normalize a Rust function body by replacing identifiers and literals."""
    lines = text.splitlines()
    start = func["start_line"]  # 1-based
    end = func["end_line"]
    body_lines = lines[start:end]  # skip the fn signature line
    if len(body_lines) < MIN_BODY_LINES:
        return None
    body = "\n".join(body_lines)
    body = NUMBER_RE.sub("0", body)
    body = IDENT_RE.sub("_", body)
    return body.strip()


def _structural_hash(normalized_body: str) -> str:
    return hashlib.sha256(normalized_body.encode("utf-8")).hexdigest()[:16]


def _collect_fingerprints(
    text: str | None, *, suffix: str, path_str: str
) -> list[dict]:
    """Return structural fingerprints for functions in a single file."""
    if text is None:
        return []
    if suffix == ".rs":
        text = strip_cfg_test_blocks(text)
        masked = mask_rust_comments_and_strings(text)
        functions = scan_rust_functions(masked)
        normalizer = _normalize_rust_body
        source = masked
    elif suffix == ".py":
        functions = scan_python_functions(text)
        normalizer = _normalize_python_body
        source = text
    else:
        return []
    fingerprints = []
    for func in functions:
        normalized = normalizer(source, func)
        if normalized is None:
            continue
        fingerprints.append({
            "path": path_str,
            "name": func["name"],
            "hash": _structural_hash(normalized),
            "lines": func["line_count"],
        })
    return fingerprints


def _count_cross_file_similar_pairs(
    all_fingerprints: list[dict],
) -> int:
    """Count function pairs across different files with matching structural hashes."""
    by_hash: dict[str, list[dict]] = {}
    for fp in all_fingerprints:
        by_hash.setdefault(fp["hash"], []).append(fp)
    count = 0
    for group in by_hash.values():
        paths = {fp["path"] for fp in group}
        if len(paths) > 1:
            count += len(group) - 1
    return count


def _count_metrics(
    all_fingerprints: list[dict],
) -> dict[str, int]:
    return {
        "structural_similar_pairs": _count_cross_file_similar_pairs(all_fingerprints),
    }


def _growth(base: dict[str, int], current: dict[str, int]) -> dict[str, int]:
    return {key: current[key] - base[key] for key in base}


def _has_positive_growth(growth: dict[str, int]) -> bool:
    return any(value > 0 for value in growth.values())


def _render_md(report: dict) -> str:
    lines = ["# check_structural_similarity", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- files_skipped_non_source: {report['files_skipped_non_source']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- functions_fingerprinted: {report['functions_fingerprinted']}")
    lines.append(
        "- aggregate_growth: structural_similar_pairs "
        f"{report['totals']['structural_similar_pairs_growth']:+d}"
    )
    lines.append(f"- min_body_lines: {MIN_BODY_LINES}")

    if report.get("similar_groups"):
        lines.append("")
        lines.append("## Similar Groups")
        lines.append(
            "- Guidance: functions with identical control-flow structure across "
            "different files suggest copy-paste. Extract shared logic to a "
            "common helper module."
        )
        for group in report["similar_groups"]:
            members = ", ".join(
                f"`{fp['path']}::{fp['name']}`" for fp in group
            )
            lines.append(f"- [{members}]")
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
            "check_structural_similarity", args.format, str(exc)
        )

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_source = 0
    files_skipped_tests = 0

    base_fingerprints: list[dict] = []
    current_fingerprints: list[dict] = []

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

        base_fingerprints.extend(
            _collect_fingerprints(base_text, suffix=path.suffix, path_str=path.as_posix())
        )
        current_fingerprints.extend(
            _collect_fingerprints(current_text, suffix=path.suffix, path_str=path.as_posix())
        )

    base_metrics = _count_metrics(base_fingerprints)
    current_metrics = _count_metrics(current_fingerprints)
    growth = _growth(base_metrics, current_metrics)

    # Collect similar groups for reporting
    by_hash: dict[str, list[dict]] = {}
    for fp in current_fingerprints:
        by_hash.setdefault(fp["hash"], []).append(fp)
    similar_groups = [
        group for group in by_hash.values()
        if len({fp["path"] for fp in group}) > 1
    ]

    report = {
        "command": "check_structural_similarity",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "ok": not _has_positive_growth(growth),
        "files_changed": len(changed_paths),
        "files_considered": files_considered,
        "files_skipped_non_source": files_skipped_non_source,
        "files_skipped_tests": files_skipped_tests,
        "functions_fingerprinted": len(current_fingerprints),
        "totals": {
            "structural_similar_pairs_growth": growth["structural_similar_pairs"],
        },
        "similar_groups": similar_groups if similar_groups else [],
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
