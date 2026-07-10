"""Markdown rendering for quality feedback snapshots."""

from __future__ import annotations

from .models import QualityFeedbackSnapshot

_MAX_CHECK_TABLE_ROWS = 20


def render_quality_feedback_markdown(snapshot: QualityFeedbackSnapshot) -> str:
    """Render a quality feedback snapshot as a CLI-oriented markdown report."""
    lines: list[str] = []

    lines.append("# Governance Quality Feedback Report")
    lines.append("")
    lines.append(f"- **repo**: {snapshot.repo_name}")
    lines.append(f"- **generated_at_utc**: {snapshot.generated_at_utc}")
    lines.append(f"- **contract_id**: {snapshot.contract_id}")
    lines.append(f"- **schema_version**: {snapshot.schema_version}")

    # Maintainability score
    m = snapshot.maintainability
    lines.append("")
    lines.append("## Maintainability Score")
    lines.append("")
    lines.append(f"**Overall: {m.overall:.1f} / 100  (Grade {m.grade})**")

    # Per-lens breakdown
    if m.lenses:
        lines.append("")
        lines.append("### Quality Lenses")
        lines.append("")
        lines.append("| Lens | Score | Grade | Status |")
        lines.append("|---|---:|---|---|")
        for lens in m.lenses:
            if lens.available:
                lines.append(
                    f"| {lens.lens} | {lens.score:.1f} | {lens.grade}"
                    f" | measured ({len([s for s in lens.sub_scores if s.available])}"
                    f"/{len(lens.sub_scores)} dims) |"
                )
            else:
                lines.append(
                    f"| {lens.lens} | n/a | n/a | no evidence loaded |"
                )

    # Sub-score detail
    lines.append("")
    lines.append("### Sub-Score Detail")
    lines.append("")
    lines.append("| Sub-Score | Value | Weight | Weighted | Status |")
    lines.append("|---|---:|---:|---:|---|")
    for entry in m.sub_scores:
        if entry.available:
            lines.append(
                f"| {entry.name} | {entry.value:.1f} | {entry.weight:.2f}"
                f" | {entry.weighted:.2f} | measured |"
            )
        else:
            lines.append(
                f"| {entry.name} | n/a | {entry.weight:.2f}"
                f" | — | no evidence loaded |"
            )

    # Halstead summary
    h = snapshot.halstead_summary
    lines.append("")
    lines.append("## Halstead Summary")
    lines.append("")
    lines.append(f"- files_scanned: {h.files_scanned}")
    lines.append(f"- total_loc: {h.total_loc}")
    lines.append(f"- avg_volume: {h.avg_volume:.1f}")
    lines.append(f"- avg_difficulty: {h.avg_difficulty:.1f}")
    lines.append(f"- avg_effort: {h.avg_effort:.1f}")
    lines.append(f"- avg_maintainability_index: {h.avg_maintainability_index:.1f}")
    lines.append(f"- estimated_total_bugs: {h.estimated_total_bugs:.1f}")

    # False-positive analysis
    fp = snapshot.false_positive_analysis
    lines.append("")
    lines.append("## False-Positive Analysis")
    lines.append("")
    lines.append(f"Total classified: **{fp.total_fp_count}**")
    lines.append("")
    if fp.by_root_cause:
        lines.append("| Root Cause | Count | % |")
        lines.append("|---|---:|---:|")
        for bucket in fp.by_root_cause:
            lines.append(
                f"| {bucket.get('category', '-')}"
                f" | {bucket.get('count', 0)}"
                f" | {bucket.get('pct', 0.0)} |"
            )
    else:
        lines.append("No false-positive classifications recorded.")

    # Per-check quality scores (top N by total findings)
    checks = sorted(
        snapshot.check_quality_scores,
        key=lambda c: c.total_findings,
        reverse=True,
    )[:_MAX_CHECK_TABLE_ROWS]
    lines.append("")
    lines.append(f"## Per-Check Quality Scores (top {_MAX_CHECK_TABLE_ROWS})")
    lines.append("")
    if checks:
        lines.append(
            "| Check | Type | Findings | TP | FP"
            " | Precision% | FP Rate% | Cleanup% |"
        )
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
        for c in checks:
            lines.append(
                f"| {c.check_id} | {c.signal_type}"
                f" | {c.total_findings} | {c.true_positive_count}"
                f" | {c.false_positive_count}"
                f" | {c.precision_pct:.1f} | {c.fp_rate_pct:.1f}"
                f" | {c.cleanup_rate_pct:.1f} |"
            )
    else:
        lines.append("No per-check quality data available.")

    # Improvement delta
    delta = snapshot.improvement_delta
    if delta is not None:
        lines.append("")
        lines.append("## Improvement Delta")
        lines.append("")
        sign = "+" if delta.overall_score_delta >= 0 else ""
        lines.append(
            f"- score_delta: **{sign}{delta.overall_score_delta:.1f}**"
            f" ({_fmt_score(delta.previous_score)} -> {delta.current_score:.1f})"
        )
        if delta.improved_checks:
            lines.append(f"- improved_checks: {len(delta.improved_checks)}")
        if delta.degraded_checks:
            lines.append(f"- degraded_checks: {len(delta.degraded_checks)}")

    # Recommendations
    recs = snapshot.recommendations
    lines.append("")
    lines.append("## Recommendations")
    lines.append("")
    if recs:
        for r in recs:
            lines.append(
                f"{r.priority}. **[{r.category}]** `{r.check_id}` — {r.action}"
                f" *(impact: {r.estimated_impact})*"
            )
    else:
        lines.append("No recommendations at this time.")

    return "\n".join(lines)


def _fmt_score(score: float | None) -> str:
    """Format a nullable score for display."""
    return f"{score:.1f}" if score is not None else "n/a"
