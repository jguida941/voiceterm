"""Normalize markdown Status/Last updated/Owner metadata headers."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PATHS = (".",)
DEFAULT_EXCLUDES = (
    "integrations/**",
    "dev/archive/**",
)
CANONICAL_TEMPLATE = (
    "**Status**: {status}  |  **Last updated**: {last_updated} | **Owner:** {owner}"
)


def _resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else REPO_ROOT / path


def _relative_posix(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def _is_excluded(relative_path: str, excludes: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(relative_path, pattern) for pattern in excludes)


def _collect_markdown_paths(
    raw_paths: list[str],
    excludes: list[str],
) -> list[Path]:
    collected: set[Path] = set()
    for raw_path in raw_paths:
        target = _resolve_path(raw_path)
        if not target.exists():
            raise FileNotFoundError(f"path not found: {raw_path}")
        if target.is_file():
            if target.suffix.lower() == ".md":
                relative_path = _relative_posix(target)
                if not _is_excluded(relative_path, excludes):
                    collected.add(target.resolve())
            continue
        for candidate in target.rglob("*.md"):
            relative_path = _relative_posix(candidate)
            if _is_excluded(relative_path, excludes):
                continue
            collected.add(candidate.resolve())
    return sorted(collected)


def _strip_prefix_markup(line: str) -> str:
    value = line.strip()
    if value.startswith(">"):
        value = value[1:].lstrip()
    if value.startswith("- "):
        value = value[2:].lstrip()
    return value.replace("**", "")


def _parse_single_field(line: str) -> tuple[str, str] | None:
    value = _strip_prefix_markup(line)
    if "|" in value:
        return None

    lower_value = value.lower()
    prefixes = (
        ("Status", "status:"),
        ("Last updated", "last updated:"),
        ("Owner", "owner:"),
    )
    for key, prefix in prefixes:
        if lower_value.startswith(prefix):
            field_value = value[len(prefix) :].strip()
            if field_value:
                return key, field_value
            return None
    return None


def _parse_inline_triplet(line: str) -> tuple[str, str, str] | None:
    value = _strip_prefix_markup(line)
    if "|" not in value:
        return None

    parts = [part.strip() for part in value.split("|")]
    if len(parts) != 3:
        return None

    parsed_parts: list[tuple[str, str]] = []
    for part in parts:
        parsed = _parse_single_field(part)
        if not parsed:
            return None
        parsed_parts.append(parsed)

    expected_order = ["Status", "Last updated", "Owner"]
    keys = [key for key, _ in parsed_parts]
    if keys != expected_order:
        return None

    status = parsed_parts[0][1]
    last_updated = parsed_parts[1][1]
    owner = parsed_parts[2][1]
    return status, last_updated, owner


def _metadata_line(status: str, last_updated: str, owner: str) -> str:
    return CANONICAL_TEMPLATE.format(
        status=status.strip(),
        last_updated=last_updated.strip(),
        owner=owner.strip(),
    )


def _normalize_file(path: Path, max_scan_lines: int, apply_fix: bool) -> tuple[bool, bool]:
    original_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if not original_lines:
        return False, False

    lines = list(original_lines)
    metadata_found = False
    changed = False

    scan_limit = min(len(lines), max_scan_lines)
    for index in range(1, scan_limit):
        if lines[index].lstrip().startswith("## "):
            scan_limit = index
            break

    index = 0
    while index < scan_limit:
        line = lines[index]

        inline_triplet = _parse_inline_triplet(line)
        if inline_triplet:
            metadata_found = True
            canonical = _metadata_line(*inline_triplet)
            current = line.rstrip("\n").rstrip()
            if canonical != current:
                changed = True
                if apply_fix:
                    lines[index] = canonical + ("\n" if line.endswith("\n") else "")
            index += 1
            continue

        parsed_status = _parse_single_field(line)
        if not parsed_status or parsed_status[0] != "Status":
            index += 1
            continue

        cursor = index + 1
        while cursor < scan_limit and lines[cursor].strip() == "":
            cursor += 1
        if cursor >= scan_limit:
            index += 1
            continue

        parsed_updated = _parse_single_field(lines[cursor])
        if not parsed_updated or parsed_updated[0] != "Last updated":
            index += 1
            continue

        cursor_owner = cursor + 1
        while cursor_owner < scan_limit and lines[cursor_owner].strip() == "":
            cursor_owner += 1
        if cursor_owner >= scan_limit:
            index += 1
            continue

        parsed_owner = _parse_single_field(lines[cursor_owner])
        if not parsed_owner or parsed_owner[0] != "Owner":
            index += 1
            continue

        metadata_found = True
        canonical = _metadata_line(
            parsed_status[1],
            parsed_updated[1],
            parsed_owner[1],
        )
        existing_block = "".join(lines[index : cursor_owner + 1]).strip()
        if existing_block != canonical:
            changed = True
            if apply_fix:
                newline = "\n" if lines[cursor_owner].endswith("\n") else ""
                lines[index : cursor_owner + 1] = [canonical + newline]
                removed_count = cursor_owner - index
                scan_limit -= removed_count
        index += 1

    if apply_fix and changed and lines != original_lines:
        path.write_text("".join(lines), encoding="utf-8")

    return metadata_found, changed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Enforce canonical markdown metadata header style."
    )
    parser.add_argument(
        "--path",
        action="append",
        default=None,
        help="File or directory to scan (repeatable).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="Glob pattern to skip (repeatable, repo-relative).",
    )
    parser.add_argument(
        "--max-scan-lines",
        type=int,
        default=80,
        help="Only scan metadata blocks inside the first N lines of each file.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Rewrite files to canonical metadata format.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    raw_paths = args.path if args.path else list(DEFAULT_PATHS)
    excludes = args.exclude if args.exclude else list(DEFAULT_EXCLUDES)

    try:
        paths = _collect_markdown_paths(raw_paths, excludes)
    except (FileNotFoundError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    matched_paths: list[str] = []
    changed_paths: list[str] = []

    for path in paths:
        metadata_found, changed = _normalize_file(
            path,
            max_scan_lines=args.max_scan_lines,
            apply_fix=args.fix,
        )
        relative_path = _relative_posix(path)
        if metadata_found:
            matched_paths.append(relative_path)
        if changed:
            changed_paths.append(relative_path)

    ok = not changed_paths or args.fix
    report = {
        "ok": ok,
        "mode": "fix" if args.fix else "check",
        "scanned_files": len(paths),
        "matched_files": len(matched_paths),
        "changed_files": len(changed_paths),
        "matched_paths": matched_paths,
        "changed_paths": changed_paths,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print("# check_markdown_metadata_header")
        print(f"- ok: {ok}")
        print(f"- mode: {report['mode']}")
        print(f"- scanned_files: {report['scanned_files']}")
        print(f"- matched_files: {report['matched_files']}")
        print(f"- changed_files: {report['changed_files']}")
        if changed_paths:
            print("- changed_paths:")
            for relative_path in changed_paths:
                print(f"  - {relative_path}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
