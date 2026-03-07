"""Shared parser/helpers for naming consistency checks."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

try:
    from .yaml_json_loader import load_yaml_or_json
except ImportError:  # pragma: no cover
    from yaml_json_loader import load_yaml_or_json

REPO_ROOT = Path(__file__).resolve().parents[3]


def _path_for_report(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _load_module(path: Path, module_name: str) -> tuple[ModuleType | None, str | None]:
    if not path.exists():
        return None, f"missing required module: {_path_for_report(path)}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None, f"failed to load module spec: {_path_for_report(path)}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover
        return None, f"failed to import {_path_for_report(path)}: {exc}"
    return module, None


def _extract_ids(items: object, section: str, errors: list[str]) -> set[str]:
    if not isinstance(items, list):
        errors.append(f"`{section}` must be a list")
        return set()
    values: set[str] = set()
    invalid = 0
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            invalid += 1
            continue
        values.add(item["id"])
    if invalid:
        errors.append(f"`{section}` contains {invalid} entries without a string `id`")
    return values


def _load_matrix_ids(path: Path) -> tuple[set[str], set[str], list[str]]:
    errors: list[str] = []
    if not path.exists():
        return set(), set(), [f"missing matrix file: {_path_for_report(path)}"]
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return set(), set(), [f"failed to read matrix file: {exc}"]
    try:
        payload = load_yaml_or_json(raw, yaml_module=yaml)
    except Exception as exc:
        return set(), set(), [f"failed to parse matrix file: {exc}"]
    if not isinstance(payload, dict):
        return set(), set(), ["matrix root must be an object"]
    return (
        _extract_ids(payload.get("hosts"), "hosts", errors),
        _extract_ids(payload.get("providers"), "providers", errors),
        errors,
    )


def _find_matching_brace(text: str, start: int) -> int | None:
    if start >= len(text) or text[start] != "{":
        return None
    depth = 1
    index = start + 1
    while index < len(text):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _find_matching_bracket(text: str, start: int) -> int | None:
    if start >= len(text) or text[start] != "[":
        return None
    depth = 1
    index = start + 1
    while index < len(text):
        char = text[index]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _mask_line_comments_and_strings(text: str) -> str:
    chars = list(text)
    index = 0
    in_line_comment = False
    in_block_comment = 0
    in_string = False
    in_raw_string = False
    raw_hashes = 0
    escape_next = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            else:
                chars[index] = " "
            index += 1
            continue

        if in_block_comment > 0:
            if char == "/" and next_char == "*":
                chars[index] = " "
                chars[index + 1] = " "
                in_block_comment += 1
                index += 2
                continue
            if char == "*" and next_char == "/":
                chars[index] = " "
                chars[index + 1] = " "
                in_block_comment -= 1
                index += 2
                continue
            if char != "\n":
                chars[index] = " "
            index += 1
            continue

        if in_string:
            if char != "\n":
                chars[index] = " "
            if escape_next:
                escape_next = False
            elif char == "\\":
                escape_next = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if in_raw_string:
            if char == '"' and text.startswith("#" * raw_hashes, index + 1):
                if char != "\n":
                    chars[index] = " "
                for probe in range(index + 1, min(index + 1 + raw_hashes, len(text))):
                    if chars[probe] != "\n":
                        chars[probe] = " "
                in_raw_string = False
                index += 1 + raw_hashes
                continue
            if char != "\n":
                chars[index] = " "
            index += 1
            continue

        if char == "/" and next_char == "/":
            chars[index] = " "
            chars[index + 1] = " "
            in_line_comment = True
            index += 2
            continue
        if char == "/" and next_char == "*":
            chars[index] = " "
            chars[index + 1] = " "
            in_block_comment = 1
            index += 2
            continue
        if char == '"':
            chars[index] = " "
            in_string = True
            escape_next = False
            index += 1
            continue
        if char == "r":
            probe = index + 1
            while probe < len(text) and text[probe] == "#":
                probe += 1
            if probe < len(text) and text[probe] == '"':
                chars[index] = " "
                for hash_index in range(index + 1, probe + 1):
                    if chars[hash_index] != "\n":
                        chars[hash_index] = " "
                in_raw_string = True
                raw_hashes = probe - (index + 1)
                index = probe + 1
                continue
        index += 1
    return "".join(chars)


def _strip_leading_attributes(segment: str) -> str:
    cursor = 0
    while cursor < len(segment):
        while cursor < len(segment) and segment[cursor].isspace():
            cursor += 1
        if not segment.startswith("#[", cursor):
            return segment[cursor:]
        attr_end = _find_matching_bracket(segment, cursor + 1)
        if attr_end is None:
            return segment[cursor:]
        cursor = attr_end + 1
    return ""


def _split_top_level_variants(raw_body: str, masked_body: str) -> list[str]:
    segments: list[str] = []
    start = 0
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    angle_depth = 0
    for index, char in enumerate(masked_body):
        if char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth > 0:
            paren_depth -= 1
        elif char == "[":
            bracket_depth += 1
        elif char == "]" and bracket_depth > 0:
            bracket_depth -= 1
        elif char == "{":
            brace_depth += 1
        elif char == "}" and brace_depth > 0:
            brace_depth -= 1
        elif char == "<":
            angle_depth += 1
        elif char == ">" and angle_depth > 0:
            angle_depth -= 1
        elif char == "," and not any(
            (paren_depth, bracket_depth, brace_depth, angle_depth)
        ):
            segments.append(raw_body[start:index])
            start = index + 1
    if start < len(raw_body):
        segments.append(raw_body[start:])
    return segments


def _parse_enum_ids(path: Path, enum_name: str) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8", errors="replace")
    masked = _mask_line_comments_and_strings(text)
    enum_match = re.search(rf"\benum\s+{enum_name}\b", masked)
    if not enum_match:
        return set()
    body_start = masked.find("{", enum_match.end())
    if body_start < 0:
        return set()
    body_end = _find_matching_brace(masked, body_start)
    if body_end is None:
        return set()
    masked_body = masked[body_start + 1 : body_end]
    ids: set[str] = set()
    for masked_segment in _split_top_level_variants(masked_body, masked_body):
        candidate = _strip_leading_attributes(masked_segment).strip()
        if not candidate:
            continue
        if candidate.startswith("//") or candidate.startswith("/*"):
            continue
        token = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", candidate)
        if token:
            ids.add(token.group(1).lower())
    return ids


def _parse_backend_registry_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8", errors="replace")
    classes = re.findall(r"\bBox::new\(\s*([A-Za-z_][A-Za-z0-9_]*)::new\s*\(", text)
    if not classes:
        classes = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)Backend::new\s*\(", text)
    ids: set[str] = set()
    for class_name in classes:
        base = class_name.removesuffix("Backend")
        ids.add(re.sub(r"(?<!^)(?=[A-Z])", "", base).lower())
    return ids


def _extract_provider_label_tokens(pattern: object) -> set[str]:
    if not isinstance(pattern, str):
        return set()
    grouped = re.search(r"\(\?:([^)]+)\)", pattern)
    source = grouped.group(1) if grouped else pattern
    tokens: set[str] = set()
    for item in source.split("|"):
        candidate = item.strip()
        if re.fullmatch(r"[a-z][a-z0-9]*", candidate):
            tokens.add(candidate)
    return tokens


def _parse_isolation_provider_tokens(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"PROVIDER_LABEL_PATTERN\s*=\s*r?['\"]([^'\"]+)['\"]", text)
    if match:
        return _extract_provider_label_tokens(match.group(1))
    compiled_match = re.search(
        r"PROVIDER_LABEL_PATTERN\s*=\s*re\.compile\(\s*r?['\"]([^'\"]+)['\"]", text
    )
    return (
        _extract_provider_label_tokens(compiled_match.group(1))
        if compiled_match
        else set()
    )


def _expect_str_set(
    value: object, *, label: str, source: Path, errors: list[str]
) -> set[str]:
    if not isinstance(value, (set, frozenset)):
        errors.append(f"{label} in {_path_for_report(source)} must be a set/frozenset")
        return set()
    result = {item for item in value if isinstance(item, str)}
    if len(result) != len(value):
        errors.append(
            f"{label} in {_path_for_report(source)} contains non-string values"
        )
    return result


def _expect_dict_keys(
    value: object, *, label: str, source: Path, errors: list[str]
) -> set[str]:
    if not isinstance(value, dict):
        errors.append(f"{label} in {_path_for_report(source)} must be a dict")
        return set()
    keys = {item for item in value.keys() if isinstance(item, str)}
    if len(keys) != len(value):
        errors.append(f"{label} in {_path_for_report(source)} has non-string keys")
    return keys
