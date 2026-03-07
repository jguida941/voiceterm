"""Shared text helpers for Rust check scripts."""

from __future__ import annotations

import re

IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _find_matching_delimiter(
    text: str,
    start: int,
    open_char: str,
    close_char: str,
) -> int | None:
    if start >= len(text) or text[start] != open_char:
        return None
    depth = 1
    index = start + 1
    while index < len(text):
        char = text[index]
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _skip_ws(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def mask_rust_comments_and_strings(text: str) -> str:
    """Replace Rust comments/string-literal contents with spaces preserving newlines."""
    chars = list(text)
    length = len(text)
    index = 0
    block_comment_depth = 0
    in_line_comment = False
    in_string = False
    in_raw_string = False
    raw_hashes = 0
    escape_next = False

    while index < length:
        char = text[index]
        next_char = text[index + 1] if index + 1 < length else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            else:
                chars[index] = " "
            index += 1
            continue

        if block_comment_depth > 0:
            if char == "/" and next_char == "*":
                chars[index] = " "
                chars[index + 1] = " "
                block_comment_depth += 1
                index += 2
                continue
            if char == "*" and next_char == "/":
                chars[index] = " "
                chars[index + 1] = " "
                block_comment_depth -= 1
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
                end = index + 1 + raw_hashes
                for probe in range(index + 1, min(end, length)):
                    if chars[probe] != "\n":
                        chars[probe] = " "
                in_raw_string = False
                index = end
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
            block_comment_depth = 1
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
            while probe < length and text[probe] == "#":
                probe += 1
            if probe < length and text[probe] == '"':
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


def _cfg_expr_has_positive_test(expr: str) -> bool:
    """Return True when cfg expression requires a positive `test` token."""
    index = 0
    length = len(expr)
    positive_test = False

    def scan(stop_char: str, negated: bool) -> int:
        nonlocal index, positive_test
        while index < length and not positive_test:
            index = _skip_ws(expr, index)
            if index >= length:
                return index
            char = expr[index]
            if char == stop_char:
                return index
            if char == ",":
                index += 1
                continue
            ident_match = IDENT_RE.match(expr, index)
            if ident_match is None:
                index += 1
                continue
            ident = ident_match.group(0)
            index = ident_match.end()
            index = _skip_ws(expr, index)
            if index < length and expr[index] == "(":
                index += 1
                child_negated = not negated if ident == "not" else negated
                scan(")", child_negated)
                if index < length and expr[index] == ")":
                    index += 1
                continue
            if ident == "test" and not negated:
                positive_test = True
        return index

    scan("\0", False)
    return positive_test


def _attribute_is_cfg_test(attribute_text: str) -> bool:
    start = _skip_ws(attribute_text, 0)
    if not attribute_text.startswith("#[", start):
        return False

    cursor = start + 2
    cursor = _skip_ws(attribute_text, cursor)
    cfg_match = IDENT_RE.match(attribute_text, cursor)
    if cfg_match is None or cfg_match.group(0) != "cfg":
        return False

    cursor = _skip_ws(attribute_text, cfg_match.end())
    if cursor >= len(attribute_text) or attribute_text[cursor] != "(":
        return False
    expr_end = _find_matching_delimiter(attribute_text, cursor, "(", ")")
    if expr_end is None:
        return False
    expression = attribute_text[cursor + 1 : expr_end]
    return _cfg_expr_has_positive_test(expression)


def _next_attribute_range(text: str, start: int) -> tuple[int, int] | None:
    attribute_start = text.find("#[", start)
    if attribute_start < 0:
        return None
    attribute_end = _find_matching_delimiter(text, attribute_start + 1, "[", "]")
    if attribute_end is None:
        return None
    return attribute_start, attribute_end + 1


def _mask_range(chars: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        if chars[index] != "\n":
            chars[index] = " "


def _find_item_end(text: str, start: int) -> int:
    if start >= len(text):
        return start
    index = start
    paren_depth = 0
    bracket_depth = 0
    while index < len(text):
        char = text[index]
        if char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth > 0:
            paren_depth -= 1
        elif char == "[":
            bracket_depth += 1
        elif char == "]" and bracket_depth > 0:
            bracket_depth -= 1
        elif char == "{" and paren_depth == 0 and bracket_depth == 0:
            end = _find_matching_delimiter(text, index, "{", "}")
            if end is None:
                return len(text)
            index = end + 1
            index = _skip_ws(text, index)
            if index < len(text) and text[index] == ";":
                index += 1
            return index
        elif char == ";" and paren_depth == 0 and bracket_depth == 0:
            return index + 1
        index += 1
    return len(text)


def strip_cfg_test_blocks(text: str) -> str:
    """Remove items gated by positive `cfg(test)` expressions."""
    sanitized = mask_rust_comments_and_strings(text)
    output_chars = list(text)

    cursor = 0
    while True:
        attribute_range = _next_attribute_range(sanitized, cursor)
        if attribute_range is None:
            break
        attribute_start, attribute_end = attribute_range
        attribute_text = sanitized[attribute_start:attribute_end]
        if not _attribute_is_cfg_test(attribute_text):
            cursor = attribute_end
            continue

        item_start = attribute_start
        item_cursor = _skip_ws(sanitized, attribute_end)
        while item_cursor < len(sanitized) and sanitized.startswith("#[", item_cursor):
            nested_range = _next_attribute_range(sanitized, item_cursor)
            if nested_range is None:
                break
            _, nested_end = nested_range
            item_cursor = _skip_ws(sanitized, nested_end)
        item_end = _find_item_end(sanitized, item_cursor)
        if item_end <= item_start:
            cursor = attribute_end
            continue

        _mask_range(output_chars, item_start, item_end)
        replacement = "".join(
            "\n" if char == "\n" else " " for char in sanitized[item_start:item_end]
        )
        sanitized = sanitized[:item_start] + replacement + sanitized[item_end:]
        cursor = item_end

    return "".join(output_chars)
