"""Verify that documented CLI flags match the Rust clap schema."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DOC_PATH = REPO_ROOT / "guides/CLI_FLAGS.md"
DEFAULT_SCHEMA_PATHS = (
    REPO_ROOT / "rust/src/config/mod.rs",
    REPO_ROOT / "rust/src/bin/voiceterm/config/cli.rs",
)

DOC_FLAG_RE = re.compile(r"^\|\s*`--([a-z0-9][a-z0-9-]*)\b")
ARG_ATTR_START_RE = re.compile(r"#\s*\[\s*arg\(")
LONG_EXPLICIT_RE = re.compile(r'\blong\s*=\s*"([^"]+)"')
LONG_SHORTHAND_RE = re.compile(r"\blong\b")
FIELD_RE = re.compile(r"\bpub(?:\([^)]*\))?\s+([A-Za-z_][A-Za-z0-9_]*)\s*:")


def _resolve_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def _extract_doc_flags(path: Path) -> set[str]:
    if not path.exists():
        raise FileNotFoundError(f"doc file not found: {path}")
    flags: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = DOC_FLAG_RE.match(line.strip())
        if match:
            flags.add(match.group(1))
    return flags


def _collect_arg_attribute_blocks(text: str) -> list[tuple[str, str | None]]:
    blocks: list[tuple[str, str | None]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not ARG_ATTR_START_RE.search(line):
            index += 1
            continue

        collected = [line]
        depth = line.count("(") - line.count(")")
        cursor = index + 1
        while cursor < len(lines) and depth > 0:
            next_line = lines[cursor]
            collected.append(next_line)
            depth += next_line.count("(") - next_line.count(")")
            cursor += 1

        field_name: str | None = None
        probe = cursor
        while probe < len(lines):
            candidate = lines[probe].strip()
            if not candidate or candidate.startswith("#[") or candidate.startswith("///") or candidate.startswith("//"):
                probe += 1
                continue
            field_match = FIELD_RE.search(lines[probe])
            if field_match:
                field_name = field_match.group(1)
            break

        blocks.append((" ".join(collected), field_name))
        index = cursor
    return blocks


def _extract_schema_flags(path: Path) -> set[str]:
    if not path.exists():
        raise FileNotFoundError(f"schema file not found: {path}")
    flags: set[str] = set()
    text = path.read_text(encoding="utf-8")
    for attr_text, field_name in _collect_arg_attribute_blocks(text):
        explicit = LONG_EXPLICIT_RE.findall(attr_text)
        if explicit:
            flags.update(explicit)
            continue
        if LONG_SHORTHAND_RE.search(attr_text) and field_name:
            flags.add(field_name.replace("_", "-"))
    return flags


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check parity between clap long flags and guides/CLI_FLAGS.md"
    )
    parser.add_argument(
        "--doc",
        default=str(DEFAULT_DOC_PATH),
        help="Path to CLI flags documentation markdown",
    )
    parser.add_argument(
        "--schema",
        action="append",
        default=[],
        help="Rust file containing #[arg(...)] definitions (repeatable)",
    )
    parser.add_argument(
        "--ignore-code-flag",
        action="append",
        default=["help"],
        help="Flag present in clap schema but intentionally omitted in docs",
    )
    parser.add_argument(
        "--ignore-doc-flag",
        action="append",
        default=[],
        help="Flag present in docs but intentionally omitted from clap schema",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    try:
        doc_path = _resolve_path(args.doc)
        schema_paths = [_resolve_path(raw) for raw in (args.schema or [str(path) for path in DEFAULT_SCHEMA_PATHS])]

        doc_flags = _extract_doc_flags(doc_path)
        code_flags: set[str] = set()
        for schema_path in schema_paths:
            code_flags.update(_extract_schema_flags(schema_path))
    except (FileNotFoundError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    ignored_code_flags = set(args.ignore_code_flag)
    ignored_doc_flags = set(args.ignore_doc_flag)

    missing_in_docs = sorted(code_flags - doc_flags - ignored_code_flags)
    missing_in_code = sorted(doc_flags - code_flags - ignored_doc_flags)

    ok = not missing_in_docs and not missing_in_code
    report = {
        "ok": ok,
        "doc_path": str(doc_path.relative_to(REPO_ROOT)),
        "schema_paths": [str(path.relative_to(REPO_ROOT)) for path in schema_paths],
        "doc_flag_count": len(doc_flags),
        "schema_flag_count": len(code_flags),
        "missing_in_docs": missing_in_docs,
        "missing_in_code": missing_in_code,
        "ignored_code_flags": sorted(ignored_code_flags),
        "ignored_doc_flags": sorted(ignored_doc_flags),
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print("# check_cli_flags_parity")
        print(f"- ok: {ok}")
        print(f"- docs flags: {len(doc_flags)}")
        print(f"- schema flags: {len(code_flags)}")
        print(
            "- missing_in_docs: "
            + (", ".join(missing_in_docs) if missing_in_docs else "none")
        )
        print(
            "- missing_in_code: "
            + (", ".join(missing_in_code) if missing_in_code else "none")
        )
        print(
            "- ignored_code_flags: "
            + (", ".join(sorted(ignored_code_flags)) if ignored_code_flags else "none")
        )
        print(
            "- ignored_doc_flags: "
            + (", ".join(sorted(ignored_doc_flags)) if ignored_doc_flags else "none")
        )

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
