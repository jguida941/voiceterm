"""AI-readable recommendation engine for governance tuning."""

from __future__ import annotations

from .models import (
    CheckQualityScore,
    FPClassification,
    HalsteadSummary,
    MaintainabilityResult,
    Recommendation,
)


def build_recommendations(
    *,
    maintainability: MaintainabilityResult,
    halstead_summary: HalsteadSummary,
    check_scores: list[CheckQualityScore],
    fp_classifications: list[FPClassification],
) -> list[Recommendation]:
    """Generate prioritized, actionable recommendations from quality data."""
    recommendations: list[Recommendation] = []
    priority = 0

    # 1. High FP-rate checks (precision < 70%) — actionable tuning targets
    for score in check_scores:
        if score.total_findings < 2:
            continue
        if score.fp_rate_pct > 30.0:
            priority += 1
            fp_causes = [
                c.root_cause for c in fp_classifications
                if c.check_id == score.check_id
            ]
            dominant_cause = _most_common(fp_causes) or "unknown"
            recommendations.append(Recommendation(
                priority=priority,
                check_id=score.check_id,
                category="fp_reduction",
                action=_fp_action(dominant_cause),
                evidence=(
                    f"{score.fp_rate_pct:.0f}% FP rate "
                    f"({score.false_positive_count}/{score.total_findings}); "
                    f"dominant root cause: {dominant_cause}"
                ),
                estimated_impact="high",
            ))

    # 2. Low cleanup rate checks — stalled remediation
    for score in check_scores:
        if score.true_positive_count < 2:
            continue
        if score.cleanup_rate_pct < 30.0:
            priority += 1
            recommendations.append(Recommendation(
                priority=priority,
                check_id=score.check_id,
                category="cleanup_stall",
                action=(
                    f"Prioritize fixing confirmed findings for '{score.check_id}' — "
                    f"only {score.cleanup_rate_pct:.0f}% cleanup rate"
                ),
                evidence=(
                    f"{score.true_positive_count} true positives, "
                    f"{score.cleanup_rate_pct:.0f}% fixed"
                ),
                estimated_impact="medium",
            ))

    # 3. Low Halstead MI — code complexity hotspots
    if halstead_summary.files_scanned > 0 and halstead_summary.avg_maintainability_index < 40.0:
        priority += 1
        recommendations.append(Recommendation(
            priority=priority,
            check_id="halstead_mi",
            category="complexity",
            action=(
                "Average Maintainability Index is critically low "
                f"({halstead_summary.avg_maintainability_index:.1f}/100). "
                "Decompose complex functions and reduce nesting depth."
            ),
            evidence=(
                f"{halstead_summary.files_scanned} files scanned, "
                f"avg MI={halstead_summary.avg_maintainability_index:.1f}, "
                f"estimated bugs={halstead_summary.estimated_total_bugs:.1f}"
            ),
            estimated_impact="high",
        ))

    # 4. Sub-score drag — find the weakest AVAILABLE sub-scores pulling overall down
    for entry in maintainability.sub_scores:
        if not entry.available:
            continue
        if entry.value < 50.0:
            priority += 1
            recommendations.append(Recommendation(
                priority=priority,
                check_id=entry.name,
                category="threshold_tune",
                action=_sub_score_action(entry.name, entry.value),
                evidence=(
                    f"Sub-score '{entry.name}' = {entry.value:.0f}/100 "
                    f"(weight {entry.weight:.0%}, contributing {entry.weighted:.1f} points)"
                ),
                estimated_impact="medium" if entry.value >= 30.0 else "high",
            ))

    return recommendations


def _most_common(items: list[str]) -> str | None:
    if not items:
        return None
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return max(counts, key=lambda k: counts[k])


def _fp_action(root_cause: str) -> str:
    actions = {
        "context_blind": "Add wrapper-code and delegation path exclusions",
        "threshold_noise": "Raise thresholds for test fixtures and small modules",
        "style_opinion": "Convert to advisory-only or remove from blocking guards",
        "pattern_mismatch": "Refine pattern matching regex to reduce false hits",
        "unknown": "Investigate false-positive root causes with reviewer notes",
    }
    return actions.get(root_cause, actions["unknown"])


def _sub_score_action(name: str, value: float) -> str:
    actions = dict((
        ("halstead_mi", f"Reduce function complexity (current avg MI={value:.0f})"),
        ("code_shape", f"Break up oversize files (score={value:.0f})"),
        ("duplication", f"Extract shared helpers for duplicated code (score={value:.0f})"),
        ("guard_issue_burden", f"Resolve open guard findings to reduce issue burden (score={value:.0f})"),
        ("finding_density", f"Resolve open findings to reduce issue density (score={value:.0f})"),
        ("time_to_green", f"Speed up CI feedback loop (score={value:.0f})"),
        ("cleanup_rate", f"Close confirmed findings faster (score={value:.0f})"),
    ))
    return actions.get(name, f"Improve '{name}' sub-score (current={value:.0f})")
