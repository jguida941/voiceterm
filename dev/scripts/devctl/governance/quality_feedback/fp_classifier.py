"""False-positive root cause classification engine.

Two-phase approach:
  Phase 1 — Rule-based heuristics (deterministic, from check_id + file path)
  Phase 2 — Notes keyword extraction (when Phase 1 is inconclusive)

Root cause categories:
  context_blind     — probe can't distinguish wrapper code from business logic
  threshold_noise   — tiny fixtures / test helpers flagged by strict thresholds
  style_opinion     — style preferences masquerading as quality signals
  pattern_mismatch  — regex/pattern matching picked up the wrong thing
  unknown           — insufficient evidence for classification
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from .models import FPClassification


class FPRootCause(str, Enum):
    """Canonical root cause categories for false-positive findings."""

    CONTEXT_BLIND = "context_blind"
    THRESHOLD_NOISE = "threshold_noise"
    STYLE_OPINION = "style_opinion"
    PATTERN_MISMATCH = "pattern_mismatch"
    UNKNOWN = "unknown"


# -- Phase 1: Rule-based heuristics -----------------------------------------

# Static table mapping check_id patterns to default root causes
_CHECK_ID_RULES: list[tuple[re.Pattern[str], FPRootCause]] = [
    (re.compile(r"probe_blank_line_frequency", re.I), FPRootCause.STYLE_OPINION),
    (re.compile(r"probe_side_effect_mixing", re.I), FPRootCause.CONTEXT_BLIND),
    (re.compile(r"probe_single_use_helpers", re.I), FPRootCause.CONTEXT_BLIND),
    (re.compile(r"probe_unnecessary_intermediates", re.I), FPRootCause.CONTEXT_BLIND),
    (re.compile(r"probe_defensive_overchecking", re.I), FPRootCause.CONTEXT_BLIND),
    (re.compile(r"probe_magic_numbers", re.I), FPRootCause.THRESHOLD_NOISE),
    (re.compile(r"check_function_duplication", re.I), FPRootCause.THRESHOLD_NOISE),
    (re.compile(r"check_code_shape", re.I), FPRootCause.THRESHOLD_NOISE),
    (re.compile(r"probe_stringly_typed", re.I), FPRootCause.STYLE_OPINION),
    (re.compile(r"probe_boolean_params", re.I), FPRootCause.STYLE_OPINION),
    (re.compile(r"probe_clone_density", re.I), FPRootCause.PATTERN_MISMATCH),
]

# File-path patterns that bias toward specific root causes
_TEST_PATH_RE = re.compile(r"(/tests?/|test_[^/]*\.py$|_test\.py$|_test\.rs$)", re.I)

# -- Phase 2: Notes keyword extraction --------------------------------------

_KEYWORD_RULES: list[tuple[list[str], FPRootCause]] = [
    (["wrapper", "context", "doesn't understand", "delegation", "adapter"],
     FPRootCause.CONTEXT_BLIND),
    (["threshold", "strict", "tiny", "fixture", "too small", "trivial", "boilerplate"],
     FPRootCause.THRESHOLD_NOISE),
    (["style", "preference", "opinion", "cosmetic", "formatting", "spacing"],
     FPRootCause.STYLE_OPINION),
    (["pattern", "regex", "false match", "misidentified", "wrong symbol"],
     FPRootCause.PATTERN_MISMATCH),
]


def _phase1_check_id(check_id: str) -> FPRootCause | None:
    """Match check_id against the static rule table."""
    for pattern, cause in _CHECK_ID_RULES:
        if pattern.search(check_id):
            return cause
    return None


def _phase1_file_path(file_path: str) -> FPRootCause | None:
    """Test-path bias: findings in test files tend to be threshold noise."""
    if _TEST_PATH_RE.search(file_path):
        return FPRootCause.THRESHOLD_NOISE
    return None


def _phase2_notes(notes: str) -> FPRootCause | None:
    """Keyword extraction from reviewer notes."""
    notes_lower = notes.lower()
    for keywords, cause in _KEYWORD_RULES:
        if any(kw in notes_lower for kw in keywords):
            return cause
    return None


def classify_false_positive(
    *,
    finding_id: str,
    check_id: str,
    file_path: str,
    notes: str | None = None,
    verdict: str | None = None,
) -> FPClassification | None:
    """Classify one adjudicated false-positive finding.

    Returns None if the verdict is not ``false_positive``.
    """
    if (verdict or "").lower() != "false_positive":
        return None

    # Phase 1: rule-based heuristics
    cause = _phase1_check_id(check_id)
    confidence = "high"
    evidence_parts: list[str] = []

    if cause is not None:
        evidence_parts.append(f"check_id '{check_id}' maps to {cause.value}")
    else:
        cause = _phase1_file_path(file_path)
        if cause is not None:
            confidence = "medium"
            evidence_parts.append(f"test-path bias: {file_path}")

    # Phase 2: notes keyword extraction (when Phase 1 is inconclusive)
    if cause is None and notes:
        cause = _phase2_notes(notes)
        if cause is not None:
            confidence = "medium"
            evidence_parts.append(f"keyword match in notes")

    if cause is None:
        cause = FPRootCause.UNKNOWN
        confidence = "low"
        evidence_parts.append("no heuristic matched")

    return FPClassification(
        finding_id=finding_id,
        check_id=check_id,
        file_path=file_path,
        root_cause=cause.value,
        confidence=confidence,
        evidence="; ".join(evidence_parts),
    )


def classify_findings(
    review_rows: list[dict[str, Any]],
) -> list[FPClassification]:
    """Classify all false-positive rows from a governance review ledger."""
    results: list[FPClassification] = []
    for row in review_rows:
        verdict = str(row.get("verdict") or "").strip().lower()
        if verdict != "false_positive":
            continue
        classification = classify_false_positive(
            finding_id=str(row.get("finding_id") or ""),
            check_id=str(row.get("check_id") or ""),
            file_path=str(row.get("file_path") or ""),
            notes=str(row.get("notes") or "") or None,
            verdict=verdict,
        )
        if classification is not None:
            results.append(classification)
    return results
