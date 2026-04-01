"""Safety-comment helpers for the Rust best-practices guard."""

from __future__ import annotations

import re

UNSAFE_BLOCK_RE = re.compile(r"\bunsafe\s*\{")
UNSAFE_FN_RE = re.compile(r"\bunsafe\s+fn\b")
PUB_UNSAFE_FN_RE = re.compile(r"\bpub(?:\s*\([^\)]*\))?\s+unsafe\s+fn\b")
UNSAFE_IMPL_RE = re.compile(r"\bunsafe\s+impl\b")


def has_nearby_safety_comment(
    lines: list[str],
    index: int,
    lookback: int = 5,
    *,
    allow_following: bool = False,
) -> bool:
    if "SAFETY:" in lines[index] or "# Safety" in lines[index]:
        return True
    min_index = max(0, index - lookback)
    for probe in range(index - 1, min_index - 1, -1):
        raw = lines[probe].strip()
        if not raw:
            continue
        if "SAFETY:" in raw or "# Safety" in raw:
            return True
        if raw.startswith(("//", "/*", "*", "///", "//!", "#[")):
            continue
        break
    if allow_following:
        max_index = min(len(lines), index + 4)
        for probe in range(index + 1, max_index):
            raw = lines[probe].strip()
            if not raw:
                continue
            if "SAFETY:" in raw or "# Safety" in raw:
                return True
            if raw.startswith(("//", "/*", "*")):
                continue
            break
    return False


def count_undocumented_unsafe_blocks(text: str | None) -> int:
    if text is None:
        return 0
    lines = text.splitlines()
    count = 0
    for index, line in enumerate(lines):
        if not UNSAFE_BLOCK_RE.search(line):
            continue
        if UNSAFE_FN_RE.search(line):
            continue
        if not has_nearby_safety_comment(lines, index, allow_following=True):
            count += 1
    return count


def public_unsafe_fn_missing_safety_docs(lines: list[str], index: int) -> bool:
    saw_doc = False
    saw_safety_heading = False
    probe = index - 1
    while probe >= 0:
        raw = lines[probe].strip()
        if not raw:
            if saw_doc:
                break
            probe -= 1
            continue
        if raw.startswith("#["):
            probe -= 1
            continue
        if raw.startswith("///"):
            saw_doc = True
            if "# Safety" in raw:
                saw_safety_heading = True
            probe -= 1
            continue
        break
    return not (saw_doc and saw_safety_heading)


def count_pub_unsafe_fn_missing_safety_docs(text: str | None) -> int:
    if text is None:
        return 0
    lines = text.splitlines()
    count = 0
    for index, line in enumerate(lines):
        if not PUB_UNSAFE_FN_RE.search(line):
            continue
        if public_unsafe_fn_missing_safety_docs(lines, index):
            count += 1
    return count


def count_unsafe_impl_missing_safety_comment(text: str | None) -> int:
    if text is None:
        return 0
    lines = text.splitlines()
    count = 0
    for index, line in enumerate(lines):
        if not UNSAFE_IMPL_RE.search(line):
            continue
        if not has_nearby_safety_comment(lines, index):
            count += 1
    return count
