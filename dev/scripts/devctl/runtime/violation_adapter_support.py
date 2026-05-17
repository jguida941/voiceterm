"""Shared helpers for ViolationRecord adapters.

The check-output contract in ``check_result_models`` consumes
``ViolationRecord`` instances from several adapter modules that project
domain-specific finding payloads (probe-report hints, governance-review
rows, etc.) onto the same shared renderer. Those adapters need a
consistent way to build bounded one-line summaries, coerce free-form
JSON inputs into strings and non-negative ints, and fall back through
an ordered list of labels when the preferred summary text is missing.

Centralizing those helpers here keeps the per-domain adapters focused
on the field map they own, removes structural duplication flagged by
``check_structural_similarity``, and gives the shared contract family
one well-known place to evolve summary-generation policy.
"""

from __future__ import annotations

from typing import Iterable

SUMMARY_MAX_LEN = 120


def coerce_stripped_str(value: object) -> str:
    """Return *value* coerced to a stripped string, or empty string.

    ``None`` becomes ``""`` so adapter field-map call sites can default
    cleanly without branching. Any other value is funneled through
    ``str(...)`` and stripped so accidental whitespace from JSON
    round-trips does not leak into ViolationRecord fields.
    """
    if value is None:
        return ""
    return str(value).strip()


def coerce_positive_int(value: object) -> int:
    """Return *value* coerced to a non-negative int, or 0 on failure.

    Narrowed by explicit isinstance branches instead of a blanket
    ``int(value)`` cast so the helper does not need a type-check
    suppression for the ``object`` parameter. Negative ints, booleans,
    and unparseable strings all collapse to ``0`` so adapters can
    safely default missing or malformed line numbers.
    """
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value if value > 0 else 0
    if isinstance(value, str):
        try:
            coerced = int(value)
        except ValueError:
            return 0
        return coerced if coerced > 0 else 0
    return 0


def build_bounded_summary(
    *,
    primary_text: str,
    fallback_labels: Iterable[str],
    prefix: str,
    default: str,
    max_len: int = SUMMARY_MAX_LEN,
) -> str:
    """Return a bounded one-line summary for a ViolationRecord adapter.

    Preference order:

    1. The first non-empty, stripped line of *primary_text*, truncated
       to *max_len* characters.
    2. The first non-empty label from *fallback_labels*, prefixed with
       *prefix* (which may be empty), truncated to *max_len*.
    3. *default*, truncated to *max_len*, when neither a preferred line
       nor any fallback label is available.

    Adapters supply the domain-specific source text, label candidates,
    and default value; this helper owns only the "preferred text, then
    labels, then default" selection policy so structural similarity
    between per-domain adapters no longer flags duplicated bodies.
    """
    for line in primary_text.splitlines():
        candidate = line.strip()
        if candidate:
            return candidate[:max_len]
    for label in fallback_labels:
        if label:
            composed = f"{prefix}{label}" if prefix else label
            return composed[:max_len]
    return default[:max_len] if default else ""
