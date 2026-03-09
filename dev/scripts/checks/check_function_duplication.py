#!/usr/bin/env python3
"""Growth-based guard against duplicated function bodies across source files.

Detects when a changed file introduces a function whose normalized body is
identical to a function in another file.  Only bodies >= MIN_BODY_LINES are
considered to avoid flagging trivial one-liner helpers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from check_bootstrap import emit_runtime_error, import_attr, utc_timestamp
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import (
        emit_runtime_error,
        import_attr,
        utc_timestamp,
    )

GuardContext = import_attr("rust_guard_common", "GuardContext")
list_changed_paths = import_attr("rust_guard_common", "list_changed_paths")
scan_rust_functions = import_attr("code_shape_function_policy", "scan_rust_functions")
scan_python_functions = import_attr(
    "code_shape_function_policy", "scan_python_functions"
)

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

MIN_BODY_LINES = 6
SUPPORTED_EXTENSIONS = frozenset({".rs", ".py"})
_SCANNER_BY_EXT = {".rs": scan_rust_functions, ".py": scan_python_functions}

# Strip comments for normalization
_RS_LINE_COMMENT = re.compile(r"//.*$", re.MULTILINE)
_PY_LINE_COMMENT = re.compile(r"#.*$", re.MULTILINE)
_WHITESPACE_RUN = re.compile(r"\s+")


def _normalize_body(text: str, ext: str) -> str:
    """Strip comments, collapse whitespace for stable hashing."""
    if ext == ".rs":
        text = _RS_LINE_COMMENT.sub("", text)
    elif ext == ".py":
        text = _PY_LINE_COMMENT.sub("", text)
    return _WHITESPACE_RUN.sub(" ", text).strip()


def _body_hash(text: str, ext: str) -> str:
    normalized = _normalize_body(text, ext)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _extract_function_hashes(
    source_text: str | None, ext: str, *, min_lines: int = MIN_BODY_LINES
) -> list[dict]:
    """Return list of {name, hash, line_count, start_line, end_line}."""
    if source_text is None:
        return []
    scanner = _SCANNER_BY_EXT.get(ext)
    if scanner is None:
        return []
    lines = source_text.splitlines()
    results = []
    for fn in scanner(source_text):
        body_lines = lines[fn["start_line"] - 1 : fn["end_line"]]
        if len(body_lines) < min_lines:
            continue
        # Hash only the body (skip first line which contains the fn signature)
        # so that functions with identical bodies but different names are caught.
        body_only = body_lines[1:] if len(body_lines) > 1 else body_lines
        body_text = "\n".join(body_only)
        results.append(
            {
                "name": fn["name"],
                "hash": _body_hash(body_text, ext),
                "line_count": fn["line_count"],
                "start_line": fn["start_line"],
                "end_line": fn["end_line"],
            }
        )
    return results


def _list_all_source_paths(ext: str) -> list[Path]:
    """List all tracked + untracked source files with the given extension."""
    paths: set[Path] = set()
    for cmd in (
        ["git", "ls-files"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ):
        for line in guard.run_git(cmd).stdout.splitlines():
            p = Path(line.strip())
            if p.suffix == ext:
                paths.add(p)
    return sorted(paths)


def _build_global_hash_index(
    ext: str, *, exclude_paths: set[str], min_lines: int = MIN_BODY_LINES
) -> dict[str, list[tuple[str, str]]]:
    """Build hash → [(file_path, function_name)] for all source files."""
    index: dict[str, list[tuple[str, str]]] = {}
    for path in _list_all_source_paths(ext):
        if path.as_posix() in exclude_paths:
            continue
        text = guard.read_text_from_worktree(path)
        for fn_info in _extract_function_hashes(text, ext, min_lines=min_lines):
            index.setdefault(fn_info["hash"], []).append(
                (path.as_posix(), fn_info["name"])
            )
    return index


def _render_md(report: dict) -> str:
    lines = ["# check_function_duplication", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- functions_scanned: {report['functions_scanned']}")
    lines.append(f"- duplicates_found: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")
    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        for v in report["violations"]:
            matches = ", ".join(
                f"`{m['path']}::{m['name']}`" for m in v["matches"]
            )
            lines.append(
                f"- `{v['path']}::{v['function_name']}` "
                f"({v['line_count']} lines, L{v['start_line']}-{v['end_line']}): "
                f"identical body found in {matches}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument(
        "--head-ref", default="HEAD", help="Head ref used with --since-ref"
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument(
        "--min-body-lines",
        type=int,
        default=MIN_BODY_LINES,
        help="Minimum function body lines to consider for duplication",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    min_lines = args.min_body_lines

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths = list_changed_paths(
            guard.run_git, args.since_ref, args.head_ref
        )
    except RuntimeError as exc:
        return emit_runtime_error(
            "check_function_duplication", args.format, str(exc)
        )

    mode = "commit-range" if args.since_ref else "working-tree"
    violations: list[dict] = []
    functions_scanned = 0

    # Filter to supported extensions
    source_paths = [p for p in changed_paths if p.suffix in SUPPORTED_EXTENSIONS]
    changed_posix = {p.as_posix() for p in source_paths}

    # Process each extension separately to build targeted indexes
    for ext in SUPPORTED_EXTENSIONS:
        ext_paths = [p for p in source_paths if p.suffix == ext]
        if not ext_paths:
            continue

        # Build global hash index (excluding changed files to avoid self-match)
        global_index = _build_global_hash_index(
            ext, exclude_paths=changed_posix, min_lines=min_lines
        )

        # Also index changed files against each other
        changed_index: dict[str, list[tuple[str, str]]] = {}
        changed_fn_data: dict[str, list[dict]] = {}
        for path in ext_paths:
            text = (
                guard.read_text_from_worktree(path)
                if not args.since_ref
                else guard.read_text_from_ref(path, args.head_ref)
            )
            fn_hashes = _extract_function_hashes(text, ext, min_lines=min_lines)
            changed_fn_data[path.as_posix()] = fn_hashes
            for fn_info in fn_hashes:
                changed_index.setdefault(fn_info["hash"], []).append(
                    (path.as_posix(), fn_info["name"])
                )

        # Check each changed file's functions for duplicates
        for path in ext_paths:
            path_str = path.as_posix()
            # Get base hashes to detect only NEW duplicates
            base_text = (
                guard.read_text_from_ref(path, args.since_ref or "HEAD")
            )
            base_hashes = {
                fn["hash"]
                for fn in _extract_function_hashes(base_text, ext, min_lines=min_lines)
            }

            for fn_info in changed_fn_data.get(path_str, []):
                functions_scanned += 1
                h = fn_info["hash"]

                # Skip if this hash existed in the base version (not a new dup)
                if h in base_hashes:
                    continue

                # Check global index for matches in unchanged files
                matches = []
                for match_path, match_name in global_index.get(h, []):
                    if match_path != path_str:
                        matches.append({"path": match_path, "name": match_name})

                # Check other changed files
                for match_path, match_name in changed_index.get(h, []):
                    if match_path != path_str:
                        matches.append({"path": match_path, "name": match_name})

                if matches:
                    # Deduplicate matches
                    seen = set()
                    unique_matches = []
                    for m in matches:
                        key = (m["path"], m["name"])
                        if key not in seen:
                            seen.add(key)
                            unique_matches.append(m)
                    violations.append(
                        {
                            "path": path_str,
                            "function_name": fn_info["name"],
                            "line_count": fn_info["line_count"],
                            "start_line": fn_info["start_line"],
                            "end_line": fn_info["end_line"],
                            "body_hash": h,
                            "matches": unique_matches,
                        }
                    )

    report = {
        "command": "check_function_duplication",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": args.since_ref if mode == "commit-range" else None,
        "head_ref": args.head_ref if mode == "commit-range" else None,
        "ok": len(violations) == 0,
        "files_changed": len(source_paths),
        "functions_scanned": functions_scanned,
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
