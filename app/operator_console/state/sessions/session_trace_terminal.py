"""Terminal-screen rendering helpers for session traces."""

from __future__ import annotations

import re
from dataclasses import dataclass

_ANSI_CSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_ANSI_OSC_RE = re.compile(r"\x1b\].*?(?:\x07|\x1b\\)")
_ANSI_SEQUENCE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\].*?(?:\x07|\x1b\\))")


@dataclass
class CursorState:
    """Mutable terminal cursor position and backing grid for screen rendering."""

    row: int
    col: int
    rows: int
    cols: int
    grid: list[list[str]]


def _sanitize_terminal_screen(text: str, *, max_lines: int) -> str:
    try:
        screen_lines = _render_terminal_screen(text)
    except ValueError:
        return ""
    if not screen_lines:
        return ""
    return "\n".join(screen_lines[-max_lines:])


def _render_terminal_screen(
    text: str,
    *,
    rows: int = 120,
    cols: int = 240,
) -> list[str]:
    if "\x1b" not in text and "\r" not in text:
        return []
    cursor = CursorState(
        row=0,
        col=0,
        rows=rows,
        cols=cols,
        grid=[[" "] * cols for _ in range(rows)],
    )
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\x1b":
            next_index = _consume_escape(text, index=index, cursor=cursor)
            index = index + 1 if next_index == index else next_index
            continue
        if char == "\r":
            cursor.col = 0
            index += 1
            continue
        if char == "\n":
            cursor.row, cursor.grid = _newline(
                cursor.grid,
                row=cursor.row,
                rows=cursor.rows,
            )
            index += 1
            continue
        if char == "\b":
            cursor.col = max(0, cursor.col - 1)
            index += 1
            continue
        if char == "\t":
            spaces = 4 - (cursor.col % 4)
            for _ in range(spaces):
                if cursor.col >= cursor.cols:
                    break
                cursor.grid[cursor.row][cursor.col] = " "
                cursor.col += 1
            index += 1
            continue
        if _is_printable(char):
            if cursor.col >= cursor.cols:
                cursor.row, cursor.grid = _newline(
                    cursor.grid,
                    row=cursor.row,
                    rows=cursor.rows,
                )
                cursor.col = 0
            cursor.grid[cursor.row][cursor.col] = char
            cursor.col += 1
        index += 1

    lines = []
    for raw_line in ("".join(line).rstrip() for line in cursor.grid):
        if not raw_line.strip():
            continue
        if raw_line.startswith("Script started on ") or raw_line.startswith("Script done on "):
            continue
        if _looks_like_noise(raw_line):
            continue
        lines.append(raw_line)
    return lines


def _consume_escape(text: str, *, index: int, cursor: CursorState) -> int:
    """Consume an escape sequence starting at *index* and update *cursor*."""
    if index + 1 >= len(text):
        return index + 1
    leader = text[index + 1]
    if leader == "[":
        match = _ANSI_CSI_RE.match(text, index)
        if match is None:
            return index + 1
        params = match.group()[2:-1]
        final = match.group()[-1]
        _apply_csi(params=params, final=final, cursor=cursor)
        return match.end()
    if leader == "]":
        match = _ANSI_OSC_RE.match(text, index)
        if match is None:
            return index + 1
        return match.end()
    return index + 2


def _apply_csi(*, params: str, final: str, cursor: CursorState) -> None:
    values = _parse_csi_values(params)
    row, col = cursor.row, cursor.col
    rows, cols, grid = cursor.rows, cursor.cols, cursor.grid

    if final in {"m", "h", "l", "t"}:
        return
    if final in {"H", "f"}:
        target_row = (values[0] if len(values) >= 1 and values[0] > 0 else 1) - 1
        target_col = (values[1] if len(values) >= 2 and values[1] > 0 else 1) - 1
        cursor.row = _clamp(target_row, rows)
        cursor.col = _clamp(target_col, cols)
        return
    if final == "A":
        cursor.row = max(0, row - (values[0] if values else 1))
        return
    if final == "B":
        cursor.row = min(rows - 1, row + (values[0] if values else 1))
        return
    if final == "C":
        cursor.col = min(cols - 1, col + (values[0] if values else 1))
        return
    if final == "D":
        cursor.col = max(0, col - (values[0] if values else 1))
        return
    if final == "G":
        amount = values[0] if values and values[0] > 0 else 1
        cursor.col = min(cols - 1, amount - 1)
        return
    if final == "K":
        _erase_in_line(grid[row], col=col, mode=(values[0] if values else 0))
        return
    if final == "J":
        _erase_in_display(grid, row=row, col=col, mode=(values[0] if values else 0))
        return
    if final == "P":
        _delete_chars(grid[row], col=col, amount=(values[0] if values and values[0] > 0 else 1))
        return
    if final == "X":
        _erase_chars(grid[row], col=col, amount=(values[0] if values and values[0] > 0 else 1))


def _erase_in_line(line: list[str], *, col: int, mode: int) -> None:
    if mode == 1:
        start, end = 0, col + 1
    elif mode == 2:
        start, end = 0, len(line)
    else:
        start, end = col, len(line)
    for index in range(max(0, start), min(len(line), end)):
        line[index] = " "


def _erase_in_display(
    grid: list[list[str]],
    *,
    row: int,
    col: int,
    mode: int,
) -> None:
    if mode == 2:
        for row_index in range(len(grid)):
            _erase_in_line(grid[row_index], col=0, mode=2)
        return
    if mode == 1:
        for row_index in range(0, row):
            _erase_in_line(grid[row_index], col=0, mode=2)
        _erase_in_line(grid[row], col=col, mode=1)
        return
    _erase_in_line(grid[row], col=col, mode=0)
    for row_index in range(row + 1, len(grid)):
        _erase_in_line(grid[row_index], col=0, mode=2)


def _delete_chars(line: list[str], *, col: int, amount: int) -> None:
    amount = max(1, amount)
    del line[col : min(len(line), col + amount)]
    line.extend([" "] * amount)


def _erase_chars(line: list[str], *, col: int, amount: int) -> None:
    for index in range(col, min(len(line), col + max(1, amount))):
        line[index] = " "


def _newline(
    grid: list[list[str]],
    *,
    row: int,
    rows: int,
) -> tuple[int, list[list[str]]]:
    if row < rows - 1:
        return row + 1, grid
    grid.pop(0)
    grid.append([" "] * len(grid[0]))
    return rows - 1, grid


def _clamp(value: int, maximum: int) -> int:
    return min(max(value, 0), maximum - 1)


def _parse_csi_values(params: str) -> list[int]:
    normalized = params.lstrip("?<>")
    if not normalized:
        return []
    values: list[int] = []
    for value in normalized.split(";"):
        token = value.strip()
        if not token:
            values.append(0)
            continue
        match = re.search(r"-?\d+", token)
        values.append(int(match.group()) if match is not None else 0)
    return values


def _is_printable(char: str) -> bool:
    codepoint = ord(char)
    return codepoint == 9 or codepoint >= 32


def _looks_like_noise(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if re.fullmatch(r"\d+m", stripped):
        return True
    if len(stripped) <= 3 and all(ch.isdigit() or ch in "·✢✳✶✻✽•" for ch in stripped):
        return True
    if len(stripped) <= 8 and _ANSI_SEQUENCE_RE.sub("", stripped) == stripped:
        symbols = sum(1 for ch in stripped if not ch.isalnum())
        if symbols == len(stripped):
            return True
    return False
