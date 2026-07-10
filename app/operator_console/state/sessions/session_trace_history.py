"""History-line sanitization helpers for session traces."""

from __future__ import annotations

import re

from .session_trace_terminal import _ANSI_CSI_RE, _ANSI_OSC_RE, _looks_like_noise


def _sanitize_terminal_history(text: str, *, max_lines: int) -> str:
    return _sanitize_line_stream(text, max_lines=max_lines)


def _sanitize_line_stream(text: str, *, max_lines: int) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _ANSI_OSC_RE.sub("", text)
    text = _ANSI_CSI_RE.sub("", text)
    text = _apply_backspaces(text)
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = _normalize_history_line(raw_line)
        if _looks_like_history_noise(line):
            continue
        if lines and _history_dedupe_key(lines[-1]) == _history_dedupe_key(line):
            lines[-1] = line
            continue
        lines.append(line)
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    return "\n".join(lines)


def _apply_backspaces(text: str) -> str:
    buffer: list[str] = []
    for char in text:
        if char == "\b":
            if buffer:
                buffer.pop()
            continue
        buffer.append(char)
    return "".join(buffer)


def _normalize_history_line(text: str) -> str:
    normalized = _strip_controls(text).replace("\xa0", " ")
    normalized = re.sub(
        r"[•⏺✢✳✶✻✽·]?\s*thinking with high effort",
        "",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(r"[ \t]+", " ", normalized)
    return normalized.strip()


def _history_dedupe_key(text: str) -> str:
    lowered = text.lower().strip()
    lowered = re.sub(r"^[•⏺✢✳✶✻✽·›⎿]+", "", lowered).strip()
    lowered = re.sub(r"\s+", " ", lowered)
    if "thinking" in lowered and "tokens" in lowered:
        lowered = re.sub(r"\([^)]*tokens[^)]*\)", "(thinking)", lowered)
    return lowered


def _strip_controls(text: str) -> str:
    return "".join(
        char
        for char in text
        if char == "\t" or 32 <= ord(char) or ord(char) >= 160
    )


def _looks_like_history_noise(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if stripped.startswith("Script started on ") or stripped.startswith("Script done on "):
        return True
    if _looks_like_noise(stripped):
        return True
    lowered = stripped.lower()
    if lowered in {"ctrl+b to run in background", "press enter to confirm or esc to cancel"}:
        return True

    alpha_count = sum(char.isalpha() for char in stripped)
    digit_count = sum(char.isdigit() for char in stripped)
    whitespace_count = sum(char.isspace() for char in stripped)
    spinner_count = sum(1 for char in stripped if char in "•✢✳✶✻✽·")

    if "thinking with high effort" in lowered:
        signal_markers = (
            "bash(",
            "read ",
            "update(",
            "error",
            "agent(",
            "context",
            "tokens",
            "thought for",
        )
        if not any(marker in lowered for marker in signal_markers):
            return True

    if alpha_count < 4 and digit_count > alpha_count:
        return True
    if spinner_count >= 2 and whitespace_count < 2:
        return True
    if whitespace_count == 0 and alpha_count < 5 and "/" not in stripped and "." not in stripped:
        return True
    return False
