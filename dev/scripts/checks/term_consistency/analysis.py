"""Compatibility surface for term-consistency analysis helpers."""

from __future__ import annotations

if __package__:
    from .hints import REVIEW_LENS, build_hint
    from .path_rules import TEXT_SUFFIXES, matches_any, matches_rule_path, normalize_path
    from .state import RuleDelta, RuleState, analyze_text, classify_delta
else:  # pragma: no cover - direct module loading in tests
    from hints import REVIEW_LENS, build_hint
    from path_rules import TEXT_SUFFIXES, matches_any, matches_rule_path, normalize_path
    from state import RuleDelta, RuleState, analyze_text, classify_delta

__all__ = (
    "REVIEW_LENS",
    "RuleDelta",
    "RuleState",
    "TEXT_SUFFIXES",
    "analyze_text",
    "build_hint",
    "classify_delta",
    "matches_any",
    "matches_rule_path",
    "normalize_path",
)
