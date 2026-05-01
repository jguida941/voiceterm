"""Canonical plan-reference normalization."""

from __future__ import annotations

import re

_PLAN_REF_PREFIX_RE = re.compile(r"^plan:(?://)?", re.IGNORECASE)
_PLAN_TOKEN_RE = re.compile(r"\bMP\d+-P\d+(?:-T[A-Z0-9-]+)?\b|\bMP-\d+\b", re.IGNORECASE)


def canonical_plan_ref(value: object) -> str:
    """Return a canonical `plan:<id>` ref for raw/plan-prefixed plan ids."""
    text = str(value or "").strip().strip("`")
    if not text:
        return ""
    text = _PLAN_REF_PREFIX_RE.sub("", text).strip()
    if "#" in text:
        text = text.rsplit("#", 1)[-1].strip()
    match = _PLAN_TOKEN_RE.search(text)
    if match:
        return f"plan:{match.group(0).upper()}"
    if text.upper().startswith("MP"):
        return f"plan:{text.upper()}"
    return text


def is_plan_ref(value: object) -> bool:
    """Return True when value can be interpreted as a plan reference."""
    return bool(canonical_plan_ref(value).startswith("plan:"))


__all__ = ["canonical_plan_ref", "is_plan_ref"]
