"""Risk-hint rendering for the term-consistency review probe."""

from __future__ import annotations

try:
    from probe_bootstrap import RiskHint
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.probe_bootstrap import RiskHint

if __package__:
    from .config import TermRule
    from .state import RuleDelta, RuleState, classify_delta
else:  # pragma: no cover - direct module loading in tests
    from config import TermRule
    from state import RuleDelta, RuleState, classify_delta

REVIEW_LENS = "naming_consistency"


def _format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"`{term}` x{count}" for term, count in counts.items() if count > 0) or "none"


def _inventory_signal(rule: TermRule, state: RuleState) -> str:
    if rule.match_mode == "prefer_canonical":
        if state.canonical_count > 0:
            return (
                f"inventory: mixed terminology for `{rule.canonical}`: "
                f"{_format_counts(state.found_terms)}"
            )
        return (
            f"inventory: legacy terminology for `{rule.canonical}`: "
            f"{_format_counts(state.found_terms)}"
        )
    return (
        f"inventory: mixed term family for `{rule.canonical}`: "
        f"{_format_counts(state.found_terms)}"
    )


def _delta_label(rule: TermRule) -> str:
    return "alias debt" if rule.match_mode == "prefer_canonical" else "mixed-term debt"


def _delta_signal(rule: TermRule, delta: RuleDelta) -> str:
    label = _delta_label(rule)
    return (
        f"delta: {delta.status} {label} for `{rule.canonical}` "
        f"({label} {delta.before.debt_score} -> {delta.after.debt_score})"
    )


def _hint_severity(rule: TermRule, delta: RuleDelta | None) -> str:
    if delta is None or delta.status in {"introduced", "worsened"}:
        return rule.severity
    return "low" if rule.severity != "low" else rule.severity


def build_hint(
    *,
    path: str,
    rule: TermRule,
    before_state: RuleState,
    after_state: RuleState,
    mode: str,
) -> RiskHint | None:
    if after_state.debt_score == 0:
        return None
    delta = None if mode == "adoption-scan" else classify_delta(before_state, after_state)
    signals = [_inventory_signal(rule, after_state)]
    if delta is not None:
        signals.append(_delta_signal(rule, delta))
    return RiskHint(
        file=path,
        symbol="(file-level)",
        risk_type="naming_contract",
        severity=_hint_severity(rule, delta),
        signals=signals,
        ai_instruction=rule.ai_instruction,
        review_lens=REVIEW_LENS,
    )
