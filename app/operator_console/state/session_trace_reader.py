"""Read live review-channel session traces for the Operator Console."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SESSION_TRACE_DIR_CANDIDATES = (
    "dev/reports/review_channel/projections/latest/sessions",
    "dev/reports/review_channel/latest/sessions",
)
DEFAULT_SESSION_NAME_SUFFIX = "-conductor"
_ANSI_CSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_ANSI_OSC_RE = re.compile(r"\x1b\].*?(?:\x07|\x1b\\)")
_ANSI_SEQUENCE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\].*?(?:\x07|\x1b\\))")


@dataclass(frozen=True)
class SessionTraceSnapshot:
    """One live review-channel session trace discovered on disk."""

    provider: str
    session_name: str
    capture_mode: str | None
    prepared_at: str | None
    updated_at: str | None
    metadata_path: str | None
    log_path: str
    tail_text: str


def load_live_session_trace(
    repo_root: Path,
    *,
    provider: str,
    review_full_path: Path | None = None,
    max_bytes: int = 256_000,
    max_lines: int = 160,
) -> SessionTraceSnapshot | None:
    """Return the latest tailed session trace when a real log exists."""
    metadata = _find_session_metadata(
        repo_root,
        provider=provider,
        review_full_path=review_full_path,
    )
    if metadata is None:
        return None
    log_path = _resolve_log_path(metadata=metadata, provider=provider)
    if log_path is None or not log_path.exists() or log_path.stat().st_size <= 0:
        return None
    tail_text = _sanitize_terminal_tail(
        _read_tail_text(log_path, max_bytes=max_bytes),
        max_lines=max_lines,
    )
    if not tail_text.strip():
        return None
    updated_at = _mtime_iso_utc(log_path)
    session_name = str(metadata.get("session_name") or f"{provider}{DEFAULT_SESSION_NAME_SUFFIX}")
    capture_mode = _as_text(metadata.get("capture_mode"))
    prepared_at = _as_text(metadata.get("prepared_at"))
    metadata_path = _as_text(metadata.get("_metadata_path"))
    return SessionTraceSnapshot(
        provider=provider,
        session_name=session_name,
        capture_mode=capture_mode,
        prepared_at=prepared_at,
        updated_at=updated_at,
        metadata_path=metadata_path,
        log_path=str(log_path),
        tail_text=tail_text,
    )


def _find_session_metadata(
    repo_root: Path,
    *,
    provider: str,
    review_full_path: Path | None,
) -> dict[str, object] | None:
    provider = provider.strip().lower()
    for session_dir in _candidate_session_dirs(repo_root, review_full_path=review_full_path):
        explicit = session_dir / f"{provider}{DEFAULT_SESSION_NAME_SUFFIX}.json"
        if explicit.exists():
            payload = _load_json_object(explicit)
            if payload is not None:
                return payload
        for candidate in sorted(session_dir.glob("*.json")):
            payload = _load_json_object(candidate)
            if payload is None:
                continue
            payload_provider = _as_text(payload.get("provider"))
            if payload_provider == provider:
                return payload
    return None


def _candidate_session_dirs(
    repo_root: Path,
    *,
    review_full_path: Path | None,
) -> tuple[Path, ...]:
    candidates: list[Path] = []
    if review_full_path is not None:
        candidates.append(review_full_path.parent / "sessions")
    for relative_path in DEFAULT_SESSION_TRACE_DIR_CANDIDATES:
        candidates.append(repo_root / relative_path)
    ordered: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(candidate)
    return tuple(ordered)


def _load_json_object(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    payload["_metadata_path"] = str(path)
    return payload


def _resolve_log_path(
    *,
    metadata: dict[str, object],
    provider: str,
) -> Path | None:
    log_path = _as_text(metadata.get("log_path"))
    if log_path:
        return Path(log_path)
    metadata_path = _as_text(metadata.get("_metadata_path"))
    if metadata_path is None:
        return None
    return Path(metadata_path).with_name(f"{provider}{DEFAULT_SESSION_NAME_SUFFIX}.log")


def _read_tail_text(path: Path, *, max_bytes: int) -> str:
    with path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        handle.seek(max(0, size - max_bytes))
        return handle.read().decode("utf-8", errors="replace")


def _sanitize_terminal_tail(text: str, *, max_lines: int) -> str:
    screen_lines = _render_terminal_screen(text)
    if screen_lines:
        visible = screen_lines[-max_lines:]
        return "\n".join(visible)

    return _sanitize_line_stream(text, max_lines=max_lines)


def _sanitize_line_stream(text: str, *, max_lines: int) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _ANSI_OSC_RE.sub("", text)
    text = _ANSI_CSI_RE.sub("", text)
    text = _apply_backspaces(text)
    lines = []
    for raw_line in text.splitlines():
        line = _strip_controls(raw_line)
        if not line.strip():
            continue
        if line.startswith("Script started on ") or line.startswith("Script done on "):
            continue
        lines.append(line)
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    return "\n".join(lines)


def _render_terminal_screen(
    text: str,
    *,
    rows: int = 120,
    cols: int = 240,
) -> list[str]:
    if "\x1b" not in text and "\r" not in text:
        return []
    grid = [[" "] * cols for _ in range(rows)]
    row = 0
    col = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\x1b":
            next_index, row, col = _consume_escape(
                text,
                index=index,
                grid=grid,
                row=row,
                col=col,
                rows=rows,
                cols=cols,
            )
            if next_index == index:
                index += 1
            else:
                index = next_index
            continue
        if char == "\r":
            col = 0
            index += 1
            continue
        if char == "\n":
            row, grid = _newline(grid, row=row, rows=rows)
            index += 1
            continue
        if char == "\b":
            col = max(0, col - 1)
            index += 1
            continue
        if char == "\t":
            spaces = 4 - (col % 4)
            for _ in range(spaces):
                if col >= cols:
                    break
                grid[row][col] = " "
                col += 1
            index += 1
            continue
        if _is_printable(char):
            if col >= cols:
                row, grid = _newline(grid, row=row, rows=rows)
                col = 0
            grid[row][col] = char
            col += 1
        index += 1

    lines = []
    for raw_line in ("".join(line).rstrip() for line in grid):
        if not raw_line.strip():
            continue
        if raw_line.startswith("Script started on ") or raw_line.startswith("Script done on "):
            continue
        if _looks_like_noise(raw_line):
            continue
        lines.append(raw_line)
    return lines


def _consume_escape(
    text: str,
    *,
    index: int,
    grid: list[list[str]],
    row: int,
    col: int,
    rows: int,
    cols: int,
) -> tuple[int, int, int]:
    if index + 1 >= len(text):
        return index + 1, row, col
    leader = text[index + 1]
    if leader == "[":
        match = _ANSI_CSI_RE.match(text, index)
        if match is None:
            return index + 1, row, col
        params = match.group()[2:-1]
        final = match.group()[-1]
        return match.end(), *_apply_csi(
            params=params,
            final=final,
            grid=grid,
            row=row,
            col=col,
            rows=rows,
            cols=cols,
        )
    if leader == "]":
        match = _ANSI_OSC_RE.match(text, index)
        if match is None:
            return index + 1, row, col
        return match.end(), row, col
    return index + 2, row, col


def _apply_csi(
    *,
    params: str,
    final: str,
    grid: list[list[str]],
    row: int,
    col: int,
    rows: int,
    cols: int,
) -> tuple[int, int]:
    normalized = params.lstrip("?")
    values = [int(value) if value else 0 for value in normalized.split(";")] if normalized else []

    if final in {"m", "h", "l", "t"}:
        return row, col
    if final in {"H", "f"}:
        target_row = (values[0] if len(values) >= 1 and values[0] > 0 else 1) - 1
        target_col = (values[1] if len(values) >= 2 and values[1] > 0 else 1) - 1
        return _clamp(target_row, rows), _clamp(target_col, cols)
    if final == "A":
        amount = values[0] if values else 1
        return max(0, row - amount), col
    if final == "B":
        amount = values[0] if values else 1
        return min(rows - 1, row + amount), col
    if final == "C":
        amount = values[0] if values else 1
        return row, min(cols - 1, col + amount)
    if final == "D":
        amount = values[0] if values else 1
        return row, max(0, col - amount)
    if final == "G":
        amount = values[0] if values and values[0] > 0 else 1
        return row, min(cols - 1, amount - 1)
    if final == "K":
        mode = values[0] if values else 0
        _erase_in_line(grid[row], col=col, mode=mode)
        return row, col
    if final == "J":
        mode = values[0] if values else 0
        _erase_in_display(grid, row=row, col=col, mode=mode)
        return row, col
    if final == "P":
        amount = values[0] if values and values[0] > 0 else 1
        _delete_chars(grid[row], col=col, amount=amount)
        return row, col
    if final == "X":
        amount = values[0] if values and values[0] > 0 else 1
        _erase_chars(grid[row], col=col, amount=amount)
        return row, col
    return row, col


def _erase_in_line(line: list[str], *, col: int, mode: int) -> None:
    if mode == 1:
        start = 0
        end = col + 1
    elif mode == 2:
        start = 0
        end = len(line)
    else:
        start = col
        end = len(line)
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
        row_range = range(len(grid))
        for row_index in row_range:
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


def _apply_backspaces(text: str) -> str:
    buffer: list[str] = []
    for char in text:
        if char == "\b":
            if buffer:
                buffer.pop()
            continue
        buffer.append(char)
    return "".join(buffer)


def _strip_controls(text: str) -> str:
    return "".join(
        char
        for char in text
        if char == "\t" or 32 <= ord(char) or ord(char) >= 160
    )


def _is_printable(char: str) -> bool:
    codepoint = ord(char)
    return codepoint == 9 or codepoint >= 32


def _looks_like_noise(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if len(stripped) <= 3 and all(ch.isdigit() or ch in "·✢✳✶✻✽•" for ch in stripped):
        return True
    if len(stripped) <= 8 and _ANSI_SEQUENCE_RE.sub("", stripped) == stripped:
        symbols = sum(1 for ch in stripped if not ch.isalnum())
        if symbols == len(stripped):
            return True
    return False


def _mtime_iso_utc(path: Path) -> str:
    timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return timestamp.isoformat().replace("+00:00", "Z")


def _as_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
