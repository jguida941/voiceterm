#!/usr/bin/env python3
"""Guard tagged Rust Deserialize enums without explicit serde compatibility policy."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from check_bootstrap import (
    REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import (
    REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        utc_timestamp,
    )

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")
_is_test_path = import_attr("rust_guard_common", "is_test_path")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

guard = GuardContext(REPO_ROOT)

ENUM_DECL_RE = re.compile(
    r"^\s*(?:pub(?:\([^\)]*\))?\s+)?(?:crate\s+)?enum\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b",
    re.MULTILINE,
)
DERIVE_DESERIALIZE_RE = re.compile(
    r"#\s*\[\s*derive\s*\((?P<body>.*?)\)\s*\]",
    re.DOTALL,
)
SERDE_ATTR_RE = re.compile(r"#\s*\[\s*serde\s*\((?P<body>.*?)\)\s*\]", re.DOTALL)
SERDE_OTHER_RE = re.compile(r"#\s*\[\s*serde\s*\(\s*other\s*\)\s*\]")
SERDE_COMPAT_ALLOW_RE = re.compile(
    r"serde-compat:\s*allow\b.*\breason\s*=",
    re.IGNORECASE,
)

def _collect_rust_paths(
    *,
    repo_root: Path,
    candidate_paths: list[Path],
) -> tuple[list[Path], int]:
    files: list[Path] = []
    skipped_tests = 0
    for candidate in candidate_paths:
        relative = candidate.relative_to(repo_root) if candidate.is_absolute() else candidate
        if relative.suffix != ".rs":
            continue
        if _is_test_path(relative):
            skipped_tests += 1
            continue
        files.append(repo_root / relative)
    return sorted(files), skipped_tests

def _find_matching_brace(text: str, open_index: int) -> int | None:
    depth = 0
    index = open_index
    in_string = False
    line_comment = False
    block_comment = 0

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if line_comment:
            if char == "\n":
                line_comment = False
            index += 1
            continue
        if block_comment:
            if char == "/" and next_char == "*":
                block_comment += 1
                index += 2
                continue
            if char == "*" and next_char == "/":
                block_comment -= 1
                index += 2
                continue
            index += 1
            continue
        if in_string:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_string = False
            index += 1
            continue

        if char == "/" and next_char == "/":
            line_comment = True
            index += 2
            continue
        if char == "/" and next_char == "*":
            block_comment = 1
            index += 2
            continue
        if char == '"':
            in_string = True
            index += 1
            continue
        if char == "{":
            depth += 1
            index += 1
            continue
        if char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None

def _enum_prelude(lines: list[str], enum_line_index: int) -> str:
    start = enum_line_index
    while start > 0 and lines[start - 1].strip():
        start -= 1
    return "\n".join(lines[start:enum_line_index])

def _normalize_derive_member(token: str) -> str:
    """Strip optional path qualifiers so ``serde::Deserialize`` becomes ``Deserialize``."""
    name = token.strip()
    # Handle qualified paths: ``::serde::Deserialize`` or ``serde::Deserialize``
    if "::" in name:
        name = name.rsplit("::", 1)[-1]
    return name

def _has_deserialize_derive(prelude: str) -> bool:
    for match in DERIVE_DESERIALIZE_RE.finditer(prelude):
        members = {_normalize_derive_member(tok) for tok in match.group("body").split(",")}
        if "Deserialize" in members:
            return True
    return False

def _tag_style(prelude: str) -> str | None:
    for match in SERDE_ATTR_RE.finditer(prelude):
        body = match.group("body")
        if "tag" not in body or "untagged" in body:
            continue
        return "adjacent" if "content" in body else "internal"
    return None

def _collect_tagged_deserialize_enums(text: str | None) -> list[dict]:
    if text is None:
        return []
    text = strip_cfg_test_blocks(text)
    lines = text.splitlines()
    findings: list[dict] = []

    for match in ENUM_DECL_RE.finditer(text):
        line_number = text.count("\n", 0, match.start()) + 1
        prelude = _enum_prelude(lines, line_number - 1)
        if not _has_deserialize_derive(prelude):
            continue
        tag_style = _tag_style(prelude)
        if tag_style is None:
            continue

        body_start = text.find("{", match.end())
        if body_start < 0:
            continue
        body_end = _find_matching_brace(text, body_start)
        if body_end is None:
            continue
        body = text[body_start : body_end + 1]
        findings.append(
            {
                "name": match.group("name"),
                "line": line_number,
                "tag_style": tag_style,
                "has_other": bool(SERDE_OTHER_RE.search(body)),
                "documented_strictness": bool(SERDE_COMPAT_ALLOW_RE.search(prelude)),
            }
        )
    return findings

def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    candidate_paths: list[Path],
    base_text_by_path: dict[str, str | None],
    mode: str,
    since_ref: str | None = None,
    head_ref: str | None = None,
) -> dict:
    files, skipped_tests = _collect_rust_paths(
        repo_root=repo_root,
        candidate_paths=candidate_paths,
    )
    violations: list[dict] = []
    tagged_deserialize_enums = 0
    documented_strict_enums = 0
    enums_with_other = 0

    for path in files:
        relative_path = path.relative_to(repo_root).as_posix()
        current_text = path.read_text(encoding="utf-8")
        current_enums = _collect_tagged_deserialize_enums(current_text)
        base_enums = _collect_tagged_deserialize_enums(base_text_by_path.get(relative_path))
        base_missing = {
            enum["name"]
            for enum in base_enums
            if not enum["has_other"] and not enum["documented_strictness"]
        }

        tagged_deserialize_enums += len(current_enums)
        documented_strict_enums += sum(
            1 for enum in current_enums if enum["documented_strictness"]
        )
        enums_with_other += sum(1 for enum in current_enums if enum["has_other"])

        for enum in current_enums:
            if enum["has_other"] or enum["documented_strictness"]:
                continue
            if enum["name"] in base_missing:
                continue
            violations.append(
                {
                    "path": relative_path,
                    "enum": enum["name"],
                    "line": enum["line"],
                    "tag_style": enum["tag_style"],
                    "reason": (
                        "tagged `Deserialize` enum is missing either a "
                        "`#[serde(other)]` fallback variant or a nearby "
                        "`serde-compat: allow reason=...` comment"
                    ),
                }
            )

    return {
        "command": "check_serde_compatibility",
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "mode": mode,
        "since_ref": since_ref,
        "head_ref": head_ref,
        "files_scanned": len(files),
        "files_skipped_tests": skipped_tests,
        "tagged_deserialize_enums": tagged_deserialize_enums,
        "documented_strict_enums": documented_strict_enums,
        "enums_with_other": enums_with_other,
        "violations": violations,
    }

def _render_md(report: dict) -> str:
    lines = ["# check_serde_compatibility", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_scanned: {report['files_scanned']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- tagged_deserialize_enums: {report['tagged_deserialize_enums']}")
    lines.append(f"- enums_with_other: {report['enums_with_other']}")
    lines.append(f"- documented_strict_enums: {report['documented_strict_enums']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")
    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: newly added internally/adjacently tagged Rust "
            "`Deserialize` enums should either define a `#[serde(other)]` "
            "fallback variant or document intentional strictness with a nearby "
            "`serde-compat: allow reason=...` comment."
        )
        for item in report["violations"]:
            lines.append(
                f"- `{item['path']}:{item['line']}` `{item['enum']}` "
                f"({item['tag_style']})"
            )
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
        base_text_by_path = {}
        for path in changed_paths:
            if path.suffix != ".rs" or _is_test_path(path):
                continue
            base_path = base_map.get(path, path)
            base_text_by_path[path.as_posix()] = (
                guard.read_text_from_ref(base_path, args.since_ref)
                if args.since_ref
                else guard.read_text_from_ref(base_path, "HEAD")
            )
    except (OSError, RuntimeError) as exc:
        return emit_runtime_error("check_serde_compatibility", args.format, str(exc))

    report = build_report(
        repo_root=REPO_ROOT,
        candidate_paths=changed_paths,
        base_text_by_path=base_text_by_path,
        mode="commit-range" if args.since_ref else "working-tree",
        since_ref=args.since_ref,
        head_ref=args.head_ref,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1

if __name__ == "__main__":
    sys.exit(main())
