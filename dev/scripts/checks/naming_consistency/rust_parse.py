"""Rust-source parsing helpers for naming-consistency checks."""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path


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


@dataclass
class _MaskState:
    index: int = 0
    in_line_comment: bool = False
    in_block_comment: int = 0
    in_string: bool = False
    in_raw_string: bool = False
    raw_hashes: int = 0
    escape_next: bool = False


def _mask_char_range(chars: list[str], *, start: int, end: int) -> None:
    for index in range(start, min(end, len(chars))):
        if chars[index] != "\n":
            chars[index] = " "


def _consume_line_comment(chars: list[str], text: str, state: _MaskState) -> None:
    char = text[state.index]
    if char == "\n":
        state.in_line_comment = False
    else:
        chars[state.index] = " "
    state.index += 1


def _consume_block_comment(chars: list[str], text: str, state: _MaskState) -> None:
    char = text[state.index]
    next_char = text[state.index + 1] if state.index + 1 < len(text) else ""
    if char == "/" and next_char == "*":
        _mask_char_range(chars, start=state.index, end=state.index + 2)
        state.in_block_comment += 1
        state.index += 2
        return
    if char == "*" and next_char == "/":
        _mask_char_range(chars, start=state.index, end=state.index + 2)
        state.in_block_comment -= 1
        state.index += 2
        return
    if char != "\n":
        chars[state.index] = " "
    state.index += 1


def _consume_string(chars: list[str], text: str, state: _MaskState) -> None:
    char = text[state.index]
    if char != "\n":
        chars[state.index] = " "
    if state.escape_next:
        state.escape_next = False
    elif char == "\\":
        state.escape_next = True
    elif char == '"':
        state.in_string = False
    state.index += 1


def _consume_raw_string(chars: list[str], text: str, state: _MaskState) -> None:
    char = text[state.index]
    if char == '"' and text.startswith("#" * state.raw_hashes, state.index + 1):
        _mask_char_range(
            chars,
            start=state.index,
            end=state.index + 1 + state.raw_hashes,
        )
        state.in_raw_string = False
        state.index += 1 + state.raw_hashes
        return
    if char != "\n":
        chars[state.index] = " "
    state.index += 1


def _start_comment(chars: list[str], text: str, state: _MaskState) -> bool:
    next_char = text[state.index + 1] if state.index + 1 < len(text) else ""
    if text[state.index] == "/" and next_char == "/":
        _mask_char_range(chars, start=state.index, end=state.index + 2)
        state.in_line_comment = True
        state.index += 2
        return True
    if text[state.index] == "/" and next_char == "*":
        _mask_char_range(chars, start=state.index, end=state.index + 2)
        state.in_block_comment = 1
        state.index += 2
        return True
    return False


def _start_string(chars: list[str], text: str, state: _MaskState) -> bool:
    if text[state.index] != '"':
        return False
    chars[state.index] = " "
    state.in_string = True
    state.escape_next = False
    state.index += 1
    return True


def _start_raw_string(chars: list[str], text: str, state: _MaskState) -> bool:
    if text[state.index] != "r":
        return False
    probe = state.index + 1
    while probe < len(text) and text[probe] == "#":
        probe += 1
    if probe >= len(text) or text[probe] != '"':
        return False
    _mask_char_range(chars, start=state.index, end=probe + 1)
    state.in_raw_string = True
    state.raw_hashes = probe - (state.index + 1)
    state.index = probe + 1
    return True


def _mask_line_comments_and_strings(text: str) -> str:
    chars = list(text)
    state = _MaskState()
    while state.index < len(text):
        if state.in_line_comment:
            _consume_line_comment(chars, text, state)
            continue
        if state.in_block_comment > 0:
            _consume_block_comment(chars, text, state)
            continue
        if state.in_string:
            _consume_string(chars, text, state)
            continue
        if state.in_raw_string:
            _consume_raw_string(chars, text, state)
            continue
        if _start_comment(chars, text, state):
            continue
        if _start_string(chars, text, state):
            continue
        if _start_raw_string(chars, text, state):
            continue
        state.index += 1
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
