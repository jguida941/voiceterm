"""Shared YAML/JSON loader with a minimal YAML fallback parser."""

from __future__ import annotations

import json
import re

try:
    import yaml as _yaml
except ModuleNotFoundError:  # pragma: no cover
    _yaml = None


class YamlFallbackParseError(ValueError):
    """Raised when the minimal YAML fallback parser cannot decode input."""


_NUMBER_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


def _parse_scalar(value: str) -> object:
    token = value.strip()
    if token == "":
        return ""
    if token == "[]":
        return []
    if token == "{}":
        return {}
    if token.startswith('"') and token.endswith('"'):
        return json.loads(token)
    if token.startswith("'") and token.endswith("'"):
        return token[1:-1]
    lowered = token.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    if _NUMBER_RE.match(token):
        if "." in token:
            return float(token)
        return int(token)
    if token.startswith("[") or token.startswith("{"):
        try:
            return json.loads(token)
        except Exception as exc:
            raise YamlFallbackParseError(
                f"invalid inline collection scalar: {token}"
            ) from exc
    return token


def _collect_content_lines(raw: str) -> list[tuple[int, str, int]]:
    lines: list[tuple[int, str, int]] = []
    for line_no, raw_line in enumerate(raw.splitlines(), start=1):
        line = raw_line.rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.lstrip(" ")
        if content.startswith("#"):
            continue
        lines.append((indent, content, line_no))
    return lines


def _parse_block(
    lines: list[tuple[int, str, int]], index: int, indent: int
) -> tuple[object, int]:
    if index >= len(lines):
        raise YamlFallbackParseError("unexpected end of input")
    line_indent, line_text, line_no = lines[index]
    if line_indent != indent:
        raise YamlFallbackParseError(
            f"line {line_no}: expected indent {indent}, found {line_indent}"
        )
    if line_text.startswith("- "):
        return _parse_list(lines, index, indent)
    if line_text == "-":
        return _parse_list(lines, index, indent)
    return _parse_dict(lines, index, indent)


def _parse_dict(
    lines: list[tuple[int, str, int]], index: int, indent: int
) -> tuple[dict[str, object], int]:
    result: dict[str, object] = {}
    while index < len(lines):
        line_indent, line_text, line_no = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise YamlFallbackParseError(
                f"line {line_no}: unexpected indentation ({line_indent})"
            )
        if line_text.startswith("- "):
            break
        if ":" not in line_text:
            raise YamlFallbackParseError(f"line {line_no}: expected key/value mapping")
        key, value = line_text.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise YamlFallbackParseError(f"line {line_no}: empty mapping key")
        index += 1
        if value:
            result[key] = _parse_scalar(value)
            continue
        if index < len(lines) and lines[index][0] > indent:
            nested_indent = lines[index][0]
            nested_value, index = _parse_block(lines, index, nested_indent)
            result[key] = nested_value
            continue
        result[key] = None
    return result, index


def _parse_list(
    lines: list[tuple[int, str, int]], index: int, indent: int
) -> tuple[list[object], int]:
    values: list[object] = []
    while index < len(lines):
        line_indent, line_text, line_no = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise YamlFallbackParseError(
                f"line {line_no}: unexpected indentation ({line_indent})"
            )
        if line_text == "-":
            item_prefix = ""
        elif line_text.startswith("- "):
            item_prefix = line_text[2:].strip()
        else:
            break
        index += 1
        if item_prefix == "":
            if index < len(lines) and lines[index][0] > indent:
                nested_indent = lines[index][0]
                nested_value, index = _parse_block(lines, index, nested_indent)
                values.append(nested_value)
            else:
                values.append(None)
            continue
        if ":" in item_prefix:
            key, value = item_prefix.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                raise YamlFallbackParseError(
                    f"line {line_no}: list mapping item missing key"
                )
            item: dict[str, object] = {}
            if value:
                item[key] = _parse_scalar(value)
            elif index < len(lines) and lines[index][0] > indent:
                nested_indent = lines[index][0]
                nested_value, index = _parse_block(lines, index, nested_indent)
                item[key] = nested_value
            else:
                item[key] = None
            if index < len(lines) and lines[index][0] > indent:
                nested_indent = lines[index][0]
                extra, index = _parse_block(lines, index, nested_indent)
                if not isinstance(extra, dict):
                    raise YamlFallbackParseError(
                        f"line {line_no}: expected mapping continuation for list item"
                    )
                item.update(extra)
            values.append(item)
            continue
        values.append(_parse_scalar(item_prefix))
        if index < len(lines) and lines[index][0] > indent:
            next_line_no = lines[index][2]
            raise YamlFallbackParseError(
                f"line {next_line_no}: unexpected nested block after scalar list item"
            )
    return values, index


def _parse_minimal_yaml(raw: str) -> object:
    lines = _collect_content_lines(raw)
    if not lines:
        return None
    first_indent = lines[0][0]
    parsed, index = _parse_block(lines, 0, first_indent)
    if index != len(lines):
        line_no = lines[index][2]
        raise YamlFallbackParseError(
            f"line {line_no}: trailing content could not be parsed"
        )
    return parsed


def load_yaml_or_json(raw: str, *, yaml_module: object | None = _yaml) -> object:
    """Load YAML if available, else JSON, else a minimal YAML subset parser."""
    if yaml_module is not None:
        return yaml_module.safe_load(raw)
    try:
        return json.loads(raw)
    except Exception:
        return _parse_minimal_yaml(raw)
