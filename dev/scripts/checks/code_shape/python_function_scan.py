"""Python function scanning helpers for code-shape checks."""

from __future__ import annotations

import re
import tokenize
from io import StringIO

PYTHON_DEF_PATTERN = re.compile(r"^(\s*)def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _line_closes_python_signature(raw_line: str) -> bool:
    try:
        tokens = list(tokenize.generate_tokens(StringIO(raw_line).readline))
    except tokenize.TokenError:
        return raw_line.rstrip().endswith(":")

    last_code_token = None
    for token in tokens:
        if token.type in {
            tokenize.COMMENT,
            tokenize.DEDENT,
            tokenize.ENDMARKER,
            tokenize.INDENT,
            tokenize.NEWLINE,
            tokenize.NL,
        }:
            if token.type == tokenize.COMMENT:
                break
            continue
        last_code_token = token.string
    return last_code_token == ":"


def scan_python_functions(text: str | None) -> list[dict]:
    """Scan Python source for top-level and method-level def blocks."""
    if not text:
        return []

    functions: list[dict] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        match = PYTHON_DEF_PATTERN.match(lines[i])
        if not match:
            i += 1
            continue
        def_indent = len(match.group(1))
        name = match.group(2)
        start_line = i + 1
        signature_end = i
        while signature_end < len(lines):
            if _line_closes_python_signature(lines[signature_end]):
                break
            signature_end += 1
        i = signature_end + 1
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            if stripped == "" or stripped.startswith("#"):
                i += 1
                continue
            line_indent = len(raw) - len(raw.lstrip())
            if line_indent <= def_indent:
                break
            i += 1
        end_line = min(i, len(lines))
        actual_end = end_line
        while actual_end > start_line and lines[actual_end - 1].strip() == "":
            actual_end -= 1
        functions.append(
            {
                "name": name,
                "start_line": start_line,
                "end_line": actual_end,
                "line_count": actual_end - start_line + 1,
            }
        )

    return functions
