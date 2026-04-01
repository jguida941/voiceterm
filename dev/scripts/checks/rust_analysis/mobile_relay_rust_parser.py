"""Rust struct/enum parsing for the mobile relay protocol guard.

Extracts serde-participating structs and tagged enum variants from Rust source
text, mapping wire names to field names via ``#[serde(rename = "...")]``
attributes.
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Compiled patterns for Rust struct/enum/field extraction
# ---------------------------------------------------------------------------

RUST_STRUCT_RE = re.compile(
    r"^\s*(?:pub(?:\([^\)]*\))?\s+)?struct\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b",
    re.MULTILINE,
)
RUST_ENUM_RE = re.compile(
    r"^\s*(?:pub(?:\([^\)]*\))?\s+)?enum\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b",
    re.MULTILINE,
)
RUST_FIELD_RE = re.compile(
    r"^\s*(?:pub(?:\([^\)]*\))?\s+)?(?P<name>[a-z_][a-z0-9_]*)\s*:",
    re.MULTILINE,
)
RUST_SERDE_RENAME_RE = re.compile(
    r'#\s*\[\s*serde\s*\(\s*rename\s*=\s*"(?P<wire>[^"]+)"\s*\)\s*\]'
)
RUST_SERDE_TAG_RE = re.compile(
    r'#\s*\[\s*serde\s*\(\s*tag\s*=\s*"(?P<tag>[^"]+)"'
)
RUST_VARIANT_RENAME_RE = re.compile(
    r'#\s*\[\s*serde\s*\(\s*rename\s*=\s*"(?P<wire>[^"]+)"\s*\)\s*\]\s*\n\s*'
    r"(?P<variant>[A-Za-z_][A-Za-z0-9_]*)"
)
RUST_DERIVE_SERIALIZE_RE = re.compile(
    r"#\s*\[\s*derive\s*\((?P<body>.*?)\)\s*\]",
    re.DOTALL,
)


# ---------------------------------------------------------------------------
# Brace matching (handles Rust-style // and /* */ comments)
# ---------------------------------------------------------------------------


def find_matching_brace(
    text: str,
    open_index: int,
    *,
    handle_comments: bool = True,
) -> int | None:
    """Find the closing brace that matches the opening brace at *open_index*.

    When *handle_comments* is True (default), ``//`` line comments and
    ``/* */`` block comments are respected so that braces inside comments
    are not counted.  Set it to False for languages like Swift that do not
    need comment handling in the protocol files.
    """
    depth = 0
    index = open_index
    in_string = False
    line_comment = False
    block_comment = 0

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if handle_comments and line_comment:
            if char == "\n":
                line_comment = False
            index += 1
            continue
        if handle_comments and block_comment:
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

        if handle_comments and char == "/" and next_char == "/":
            line_comment = True
            index += 2
            continue
        if handle_comments and char == "/" and next_char == "*":
            block_comment = 1
            index += 2
            continue
        if char == '"':
            in_string = True
            index += 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _prelude_text(text: str, match_start: int) -> str:
    """Extract attribute lines above a struct/enum declaration."""
    line_start = text.rfind("\n", 0, match_start)
    if line_start < 0:
        line_start = 0
    block_start = line_start
    while block_start > 0:
        prev_line_end = text.rfind("\n", 0, block_start - 1)
        if prev_line_end < 0:
            prev_line_end = 0
        line = text[prev_line_end:block_start].strip()
        if not line or (not line.startswith("#") and not line.startswith("//")):
            break
        block_start = prev_line_end
    return text[block_start:match_start]


def _has_serialize_or_deserialize(prelude: str) -> bool:
    for m in RUST_DERIVE_SERIALIZE_RE.finditer(prelude):
        members = {tok.strip().rsplit("::", 1)[-1] for tok in m.group("body").split(",")}
        if "Serialize" in members or "Deserialize" in members:
            return True
    return False


def _parse_fields(body: str) -> dict[str, str]:
    """Parse field declarations from a Rust struct/variant body block."""
    fields: dict[str, str] = {}
    prev_end = 0
    for field_m in RUST_FIELD_RE.finditer(body):
        field_name = field_m.group("name")
        attr_window = body[prev_end : field_m.start()]
        rename = RUST_SERDE_RENAME_RE.search(attr_window)
        wire_name = rename.group("wire") if rename else field_name
        fields[wire_name] = field_name
        line_end = body.find("\n", field_m.end())
        prev_end = line_end + 1 if line_end >= 0 else field_m.end()
    return fields


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_rust_structs(text: str) -> dict[str, dict]:
    """Extract serde-participating structs from Rust source text.

    Returns a dict keyed by struct name. Each value has:
      - "fields": dict mapping wire-name -> rust-field-name
      - "line": 1-based line number
    """
    structs: dict[str, dict] = {}
    for match in RUST_STRUCT_RE.finditer(text):
        prelude = _prelude_text(text, match.start())
        if not _has_serialize_or_deserialize(prelude):
            continue

        name = match.group("name")
        brace = text.find("{", match.end())
        if brace < 0:
            continue
        brace_end = find_matching_brace(text, brace)
        if brace_end is None:
            continue
        body = text[brace + 1 : brace_end]
        line = text.count("\n", 0, match.start()) + 1

        structs[name] = {"fields": _parse_fields(body), "line": line}

    return structs


def parse_rust_enum_variants(text: str) -> dict[str, dict]:
    """Extract serde-tagged enum variants and their struct fields.

    Returns a dict keyed by the serde *rename* wire tag (e.g. "agent_spawned").
    Each value has:
      - "variant": Rust variant name
      - "fields": dict mapping wire-name -> field-name
      - "line": 1-based line number
    """
    enums: dict[str, dict] = {}
    for match in RUST_ENUM_RE.finditer(text):
        prelude = _prelude_text(text, match.start())
        if not _has_serialize_or_deserialize(prelude):
            continue
        tag_m = RUST_SERDE_TAG_RE.search(prelude)
        if not tag_m:
            continue

        brace = text.find("{", match.end())
        if brace < 0:
            continue
        brace_end = find_matching_brace(text, brace)
        if brace_end is None:
            continue
        body = text[brace + 1 : brace_end]
        line = text.count("\n", 0, match.start()) + 1

        for variant_m in RUST_VARIANT_RENAME_RE.finditer(body):
            wire_tag = variant_m.group("wire")
            variant_name = variant_m.group("variant")

            variant_brace = body.find("{", variant_m.end())
            variant_fields: dict[str, str] = {}
            if variant_brace >= 0:
                variant_brace_end = find_matching_brace(body, variant_brace)
                if variant_brace_end is not None:
                    variant_body = body[variant_brace + 1 : variant_brace_end]
                    variant_fields = _parse_fields(variant_body)

            enums[wire_tag] = {
                "variant": variant_name,
                "fields": variant_fields,
                "line": line,
            }

    return enums
