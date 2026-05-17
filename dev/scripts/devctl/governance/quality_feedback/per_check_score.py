"""Per-guard/probe quality scoring from governance review data."""

from __future__ import annotations

from typing import Any

from .models import CheckQualityScore


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def build_check_quality_scores(
    review_rows: list[dict[str, Any]],
) -> list[CheckQualityScore]:
    """Compute quality metrics for each distinct check_id in the review ledger.

    Groups by (check_id, signal_type), then computes:
      - precision = true_positives / (true_positives + false_positives)
      - fp_rate = false_positives / total_adjudicated
      - cleanup_rate = fixed / positive_findings
    """
    buckets: dict[str, dict[str, Any]] = {}

    for row in review_rows:
        check_id = str(row.get("check_id") or "unknown").strip()
        signal_type = str(row.get("signal_type") or "unknown").strip()
        verdict = str(row.get("verdict") or "unknown").strip().lower()

        key = f"{check_id}|{signal_type}"
        if key not in buckets:
            buckets[key] = dict((
                ("check_id", check_id),
                ("signal_type", signal_type),
                ("total", 0),
                ("fp", 0),
                ("tp", 0),
                ("fixed", 0),
            ))
        bucket = buckets[key]
        bucket["total"] += 1
        if verdict == "false_positive":
            bucket["fp"] += 1
        elif verdict in ("confirmed_issue", "fixed", "waived", "deferred"):
            bucket["tp"] += 1
            if verdict == "fixed":
                bucket["fixed"] += 1

    scores: list[CheckQualityScore] = []
    for bucket in sorted(buckets.values(), key=lambda b: -b["total"]):
        total = bucket["total"]
        tp = bucket["tp"]
        fp = bucket["fp"]
        fixed = bucket["fixed"]
        scores.append(
            CheckQualityScore(
                check_id=bucket["check_id"],
                signal_type=bucket["signal_type"],
                total_findings=total,
                true_positive_count=tp,
                false_positive_count=fp,
                precision_pct=_rate(tp, tp + fp),
                fp_rate_pct=_rate(fp, total),
                cleanup_rate_pct=_rate(fixed, tp),
            )
        )
    return scores
