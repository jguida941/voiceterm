"""Contract-token helpers for the Python broad-except guard."""

from __future__ import annotations

import re

RATIONALE_RE = re.compile(r"broad-except:\s*allow\b.*\breason\s*=")
FALLBACK_RE = re.compile(r"broad-except:\s*allow\b.*\bfallback\s*=")


def has_contract_token(
    lines: list[str],
    line_number: int,
    *,
    token_pattern: re.Pattern[str],
) -> bool:
    index = line_number - 1
    if index < 0 or index >= len(lines):
        return False
    if token_pattern.search(lines[index]):
        return True
    probe = index - 1
    while probe >= 0:
        raw = lines[probe].strip()
        if not raw:
            break
        if raw.startswith("#"):
            if token_pattern.search(raw):
                return True
            probe -= 1
            continue
        break
    return False


def has_rationale(lines: list[str], line_number: int) -> bool:
    return has_contract_token(lines, line_number, token_pattern=RATIONALE_RE)


def has_fallback_contract(lines: list[str], line_number: int) -> bool:
    return has_contract_token(lines, line_number, token_pattern=FALLBACK_RE)
