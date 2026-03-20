#!/usr/bin/env python3
"""Guard that validates wire-protocol compatibility between Rust daemon types and iOS Swift models.

Parses struct/field definitions from both sides and flags mismatches that would
cause silent runtime decoding failures.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        utc_timestamp,
    )

if __package__:
    from .mobile_relay_protocol.support import (
        _DEFAULT_RUST_TYPES,
        _DEFAULT_SWIFT_DAEMON,
        _DEFAULT_SWIFT_RELAY,
        compare_fields,
        match_struct_pairs,
        resolve_protocol_paths as _resolve_protocol_paths,
    )
else:
    from mobile_relay_protocol.support import (
        _DEFAULT_RUST_TYPES,
        _DEFAULT_SWIFT_DAEMON,
        _DEFAULT_SWIFT_RELAY,
        compare_fields,
        match_struct_pairs,
        resolve_protocol_paths as _resolve_protocol_paths,
    )

RUST_TYPES_PATH = Path(_DEFAULT_RUST_TYPES)
SWIFT_MODELS_PATH = Path(_DEFAULT_SWIFT_RELAY)
SWIFT_DAEMON_PATH = Path(_DEFAULT_SWIFT_DAEMON)

# ---------------------------------------------------------------------------
# Rust parsing
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

def _find_matching_brace(text: str, open_index: int) -> int | None:
    """Find the closing brace that matches the opening brace at open_index."""
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
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None

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
        brace_end = _find_matching_brace(text, brace)
        if brace_end is None:
            continue
        body = text[brace + 1 : brace_end]
        line = text.count("\n", 0, match.start()) + 1

        fields: dict[str, str] = {}
        prev_field_end = 0
        for field_match in RUST_FIELD_RE.finditer(body):
            field_name = field_match.group("name")
            # Only search for serde(rename) between the end of the previous
            # field and the start of this one, so renames never leak across
            attr_window = body[prev_field_end : field_match.start()]
            rename = RUST_SERDE_RENAME_RE.search(attr_window)
            wire_name = rename.group("wire") if rename else field_name
            fields[wire_name] = field_name
            # Advance past this field's line for the next iteration
            line_end = body.find("\n", field_match.end())
            prev_field_end = line_end + 1 if line_end >= 0 else field_match.end()

        structs[name] = {"fields": fields, "line": line}

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
        brace_end = _find_matching_brace(text, brace)
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
                variant_brace_end = _find_matching_brace(body, variant_brace)
                if variant_brace_end is not None:
                    variant_body = body[variant_brace + 1 : variant_brace_end]
                    prev_end = 0
                    for field_m in RUST_FIELD_RE.finditer(variant_body):
                        fname = field_m.group("name")
                        attr_window = variant_body[prev_end : field_m.start()]
                        rename = RUST_SERDE_RENAME_RE.search(attr_window)
                        wire_name = rename.group("wire") if rename else fname
                        variant_fields[wire_name] = fname
                        line_end = variant_body.find("\n", field_m.end())
                        prev_end = (
                            line_end + 1 if line_end >= 0 else field_m.end()
                        )

            enums[wire_tag] = {
                "variant": variant_name,
                "fields": variant_fields,
                "line": line,
            }

    return enums

# ---------------------------------------------------------------------------
# Swift parsing
# ---------------------------------------------------------------------------

SWIFT_STRUCT_RE = re.compile(
    r"^\s*public\s+struct\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*:",
    re.MULTILINE,
)
SWIFT_PROPERTY_RE = re.compile(
    r"^\s*public\s+(?:let|var)\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*:",
    re.MULTILINE,
)
SWIFT_CODING_KEY_RE = re.compile(
    r'case\s+(?P<swift>[a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"(?P<wire>[^"]+)"',
)
SWIFT_CODING_KEY_PLAIN_RE = re.compile(
    r"case\s+(?P<swift>[a-zA-Z_][a-zA-Z0-9_]*)\s*$",
    re.MULTILINE,
)
SWIFT_CODING_KEYS_BLOCK_RE = re.compile(
    r"enum\s+CodingKeys\s*:\s*String\s*,\s*CodingKey\s*\{",
)

def _find_swift_brace_end(text: str, open_index: int) -> int | None:
    """Find matching closing brace in Swift source."""
    depth = 0
    index = open_index
    in_string = False

    while index < len(text):
        char = text[index]
        if in_string:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_string = False
            index += 1
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

def parse_swift_structs(text: str) -> dict[str, dict]:
    """Extract Codable structs from Swift source text.

    Returns a dict keyed by struct name. Each value has:
      - "fields": dict mapping wire-name -> swift-property-name
      - "line": 1-based line number
    """
    structs: dict[str, dict] = {}
    for match in SWIFT_STRUCT_RE.finditer(text):
        name = match.group("name")
        protocols_end = text.find("{", match.end())
        if protocols_end < 0:
            continue
        # Only process structs that conform to Codable
        protocol_line = text[match.end() : protocols_end]
        if "Codable" not in protocol_line:
            continue

        brace_end = _find_swift_brace_end(text, protocols_end)
        if brace_end is None:
            continue
        body = text[protocols_end + 1 : brace_end]
        line = text.count("\n", 0, match.start()) + 1

        # Collect swift property names
        swift_props: list[str] = []
        for prop_m in SWIFT_PROPERTY_RE.finditer(body):
            swift_props.append(prop_m.group("name"))

        # Build wire-name mapping from CodingKeys if present
        coding_keys: dict[str, str] = {}
        ck_match = SWIFT_CODING_KEYS_BLOCK_RE.search(body)
        if ck_match:
            ck_brace_end = _find_swift_brace_end(body, ck_match.end() - 1)
            if ck_brace_end is not None:
                ck_body = body[ck_match.end() : ck_brace_end]
                for ck_m in SWIFT_CODING_KEY_RE.finditer(ck_body):
                    coding_keys[ck_m.group("swift")] = ck_m.group("wire")
                for ck_m in SWIFT_CODING_KEY_PLAIN_RE.finditer(ck_body):
                    swift_name = ck_m.group("swift")
                    if swift_name not in coding_keys:
                        coding_keys[swift_name] = swift_name

        # Map wire-name -> swift-property-name
        fields: dict[str, str] = {}
        for prop in swift_props:
            wire = coding_keys.get(prop, prop)
            fields[wire] = prop

        structs[name] = {"fields": fields, "line": line}

    return structs

# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------

# Mapping from Rust struct name to expected Swift struct name. Only entries
# where the names differ need to be listed; identical names are matched
# automatically.
# ---------------------------------------------------------------------------
# Report building
# ---------------------------------------------------------------------------

_UNSET = object()


@dataclass(frozen=True)
class ProtocolReportRequest:
    repo_root: Path = REPO_ROOT
    rust_text: str | None | object = _UNSET
    swift_text: str | None | object = _UNSET
    mode: str = "full"
    since_ref: str | None = None
    head_ref: str | None = None
    changed_paths: list[Path] | None = None


@dataclass(frozen=True)
class ProtocolSourceRequest:
    repo_root: Path
    rust_path: Path
    swift_path: Path
    swift_daemon_path: Path
    rust_text: str | None | object
    swift_text: str | None | object
    mode: str
    since_ref: str | None
    head_ref: str | None

def _load_protocol_sources(
    request: ProtocolSourceRequest,
) -> tuple[str | None, str | None, dict | None]:
    """Read Rust/Swift sources from disk when not provided. Return early-exit report if missing."""
    rust_text = request.rust_text
    swift_text = request.swift_text
    if rust_text is _UNSET:
        rust_file = request.repo_root / request.rust_path
        rust_text = rust_file.read_text(encoding="utf-8") if rust_file.exists() else None
    if swift_text is _UNSET:
        swift_file = request.repo_root / request.swift_path
        swift_text = swift_file.read_text(encoding="utf-8") if swift_file.exists() else None
        daemon_file = request.repo_root / request.swift_daemon_path
        if daemon_file.exists() and swift_text is not None:
            daemon_text = daemon_file.read_text(encoding="utf-8")
            swift_text = swift_text + "\n" + daemon_text
    missing = []
    if rust_text is None:
        missing.append(request.rust_path.as_posix())
    if swift_text is None:
        missing.append(request.swift_path.as_posix())
    if missing:
        return None, None, {
            "command": "check_mobile_relay_protocol", "timestamp": utc_timestamp(),
            "ok": True, "mode": request.mode, "since_ref": request.since_ref, "head_ref": request.head_ref,
            "skipped": True, "reason": f"protocol files not found: {', '.join(missing)}",
            "violations": [],
        }
    return rust_text, swift_text, None


def _field_mismatch(
    rust_name: str, swift_name: str, wire: str,
    *, field_value: str, side: str,
) -> dict:
    """Build a single field-mismatch violation dict."""
    if side == "rust_only":
        reason = f"field '{wire}' exists in Rust `{rust_name}` but is missing from Swift `{swift_name}`"
        return {"rust_struct": rust_name, "swift_struct": swift_name,
                "wire_name": wire, "rust_field": field_value, "side": side, "reason": reason}
    reason = f"field '{wire}' exists in Swift `{swift_name}` but is missing from Rust `{rust_name}`"
    return {"rust_struct": rust_name, "swift_struct": swift_name,
            "wire_name": wire, "swift_field": field_value, "side": side, "reason": reason}


def build_report(request: ProtocolReportRequest | None = None) -> dict:
    """Build the protocol compatibility report.

    When ``changed_paths`` is provided (since-ref mode), only produce
    violations if one of the two protocol files was modified.

    Pass ``rust_text``/``swift_text`` explicitly to override file reading.
    Pass ``None`` to simulate a missing file. Omit to read from disk.
    """
    request = request or ProtocolReportRequest()
    repo_root = request.repo_root
    # Read protocol boundary config from repo policy
    cfg_rust, cfg_swift_relay, cfg_swift_daemon, cfg_name_map, cfg_computed = (
        _resolve_protocol_paths(repo_root) if repo_root else
        (Path(_DEFAULT_RUST_TYPES), Path(_DEFAULT_SWIFT_RELAY), Path(_DEFAULT_SWIFT_DAEMON), {}, set())
    )
    rust_path = cfg_rust
    swift_path = cfg_swift_relay

    # Growth-based scoping: skip if no protocol file changed
    protocol_paths = {rust_path.as_posix(), swift_path.as_posix(), cfg_swift_daemon.as_posix()}
    if request.changed_paths is not None:
        changed_posix = {p.as_posix() for p in request.changed_paths}
        if not (protocol_paths & changed_posix):
            return {
                "command": "check_mobile_relay_protocol",
                "timestamp": utc_timestamp(),
                "ok": True,
                "mode": request.mode,
                "since_ref": request.since_ref,
                "head_ref": request.head_ref,
                "skipped": True,
                "reason": "neither protocol file was modified",
                "violations": [],
            }

    rust_text, swift_text, early_return = _load_protocol_sources(
        ProtocolSourceRequest(
            repo_root=repo_root,
            rust_path=rust_path,
            swift_path=swift_path,
            swift_daemon_path=cfg_swift_daemon,
            rust_text=request.rust_text,
            swift_text=request.swift_text,
            mode=request.mode,
            since_ref=request.since_ref,
            head_ref=request.head_ref,
        )
    )
    if early_return is not None:
        return early_return

    rust_structs = parse_rust_structs(rust_text)
    swift_structs = parse_swift_structs(swift_text)
    rust_enum_variants = parse_rust_enum_variants(rust_text)

    pairs = match_struct_pairs(rust_structs, swift_structs, name_map=cfg_name_map)
    violations: list[dict] = []

    if not pairs and rust_structs and swift_structs:
        violations.append(
            {
                "rust_struct": "",
                "swift_struct": "",
                "wire_name": "",
                "side": "no_shared_structs",
                "reason": (
                    "Rust and Swift protocol models parsed successfully but no "
                    "shared struct names matched; the compatibility map is empty."
                ),
            }
        )

    for rust_name, swift_name in pairs:
        rust_fields = rust_structs[rust_name]["fields"]
        swift_fields = swift_structs[swift_name]["fields"]
        rust_only, swift_only = compare_fields(
            rust_fields, swift_fields, computed_properties=cfg_computed,
        )
        for wire in rust_only:
            violations.append(_field_mismatch(
                rust_name, swift_name, wire,
                field_value=rust_fields[wire], side="rust_only",
            ))
        for wire in swift_only:
            violations.append(_field_mismatch(
                rust_name, swift_name, wire,
                field_value=swift_fields[wire], side="swift_only",
            ))

    return {
        "command": "check_mobile_relay_protocol",
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "mode": request.mode,
        "since_ref": request.since_ref,
        "head_ref": request.head_ref,
        "rust_structs_parsed": len(rust_structs),
        "swift_structs_parsed": len(swift_structs),
        "rust_enum_variants_parsed": len(rust_enum_variants),
        "matched_pairs": len(pairs),
        "violations": violations,
    }

def _render_md(report: dict) -> str:
    lines = ["# check_mobile_relay_protocol", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    if report.get("skipped"):
        lines.append(f"- skipped: {report.get('reason', 'true')}")
        return "\n".join(lines)
    lines.append(f"- rust_structs_parsed: {report.get('rust_structs_parsed', 0)}")
    lines.append(f"- swift_structs_parsed: {report.get('swift_structs_parsed', 0)}")
    lines.append(f"- matched_pairs: {report.get('matched_pairs', 0)}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")
    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: every field in the Rust daemon types must have a "
            "matching wire-name in the Swift Codable models (and vice versa). "
            "Add the missing field or update CodingKeys to align."
        )
        for item in report["violations"]:
            lines.append(
                f"- `{item['rust_struct']}` / `{item['swift_struct']}`: "
                f"wire name `{item['wire_name']}` ({item['side']})"
            )
    return "\n".join(lines)

def _build_parser() -> argparse.ArgumentParser:
    return build_since_ref_format_parser(__doc__ or "")

def main() -> int:
    args = _build_parser().parse_args()
    try:
        changed_paths: list[Path] | None = None
        if args.since_ref:
            from check_bootstrap import import_attr

            list_changed_paths_with_base_map = import_attr(
                "git_change_paths", "list_changed_paths_with_base_map"
            )
            GuardContext = import_attr("rust_guard_common", "GuardContext")
            guard = GuardContext(REPO_ROOT)
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
            paths, _base_map = list_changed_paths_with_base_map(
                guard.run_git,
                args.since_ref,
                args.head_ref,
            )
            changed_paths = paths
    except (OSError, RuntimeError) as exc:
        return emit_runtime_error(
            "check_mobile_relay_protocol", args.format, str(exc)
        )

    report = build_report(
        ProtocolReportRequest(
            repo_root=REPO_ROOT,
            mode="commit-range" if args.since_ref else "full",
            since_ref=args.since_ref,
            head_ref=args.head_ref,
            changed_paths=changed_paths,
        )
    )
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1

if __name__ == "__main__":
    sys.exit(main())
