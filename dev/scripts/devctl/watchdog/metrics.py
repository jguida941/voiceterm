"""Metric reduction and summary-artifact loading for watchdog analytics."""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .models import (
    GuardedCodingEpisode,
    WatchdogGuardFamilyMetrics,
    WatchdogMetrics,
    WatchdogProviderMetrics,
    WatchdogSummaryArtifact,
    empty_watchdog_metrics,
    watchdog_metrics_from_dict,
)


def build_watchdog_metrics(rows: list[GuardedCodingEpisode]) -> WatchdogMetrics:
    """Aggregate typed watchdog episodes into the shared metrics bundle."""
    if not rows:
        return empty_watchdog_metrics()

    provider_counts: Counter[str] = Counter()
    guard_counts: Counter[str] = Counter()
    guard_success: Counter[str] = Counter()
    guard_time_to_green_sum: defaultdict[str, float] = defaultdict(float)
    guard_time_to_green_count: Counter[str] = Counter()
    success = 0
    noisy_or_skipped = 0
    known_provider_count = 0
    time_to_green_values: list[float] = []
    guard_runtime_values: list[float] = []
    retry_values: list[float] = []
    escaped_values: list[float] = []

    for row in rows:
        provider_counts[row.provider] += 1
        guard_counts[row.guard_family] += 1
        guard_runtime_values.append(row.guard_runtime_seconds)
        retry_values.append(float(row.retry_count))
        escaped_values.append(float(row.escaped_findings_count))
        if row.provider != "unknown":
            known_provider_count += 1
        if row.reviewer_verdict in {"accepted", "accepted_with_followups"}:
            success += 1
            guard_success[row.guard_family] += 1
            if row.time_to_green_seconds is not None and row.time_to_green_seconds > 0:
                time_to_green_values.append(row.time_to_green_seconds)
                guard_time_to_green_sum[row.guard_family] += row.time_to_green_seconds
                guard_time_to_green_count[row.guard_family] += 1
        if row.guard_result in {"noisy", "skipped"}:
            noisy_or_skipped += 1

    return WatchdogMetrics(
        total_episodes=len(rows),
        success_rate_pct=round((success / len(rows)) * 100.0, 2),
        avg_time_to_green_seconds=round(_mean(time_to_green_values), 3),
        p50_time_to_green_seconds=round(_quantile(time_to_green_values, 0.50), 3),
        avg_guard_runtime_seconds=round(_mean(guard_runtime_values), 3),
        avg_retry_count=round(_mean(retry_values), 3),
        avg_escaped_findings=round(_mean(escaped_values), 3),
        false_positive_rate_pct=round((noisy_or_skipped / len(rows)) * 100.0, 2),
        known_provider_pct=round((known_provider_count / len(rows)) * 100.0, 2),
        providers=tuple(
            WatchdogProviderMetrics(provider=provider, episodes=count)
            for provider, count in provider_counts.most_common()
        ),
        guard_families=tuple(
            WatchdogGuardFamilyMetrics(
                guard_family=family,
                episodes=count,
                success_rate_pct=round((guard_success[family] / count) * 100.0, 2),
                avg_time_to_green_seconds=round(
                    guard_time_to_green_sum[family]
                    / max(guard_time_to_green_count[family], 1),
                    3,
                ),
            )
            for family, count in guard_counts.most_common()
        ),
    )


def load_watchdog_summary_artifact(summary_path: Path) -> WatchdogSummaryArtifact:
    """Load one typed summary artifact from data-science output."""
    if not summary_path.exists():
        return _unavailable("watchdog analytics summary has not been generated yet", summary_path)
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _unavailable("watchdog analytics summary is invalid JSON", summary_path)
    except OSError as exc:
        return _unavailable(f"watchdog analytics summary could not be read: {exc}", summary_path)
    if not isinstance(payload, dict):
        return _unavailable("watchdog analytics summary is not a JSON object", summary_path)
    watchdog_payload = payload.get("watchdog_stats")
    if not isinstance(watchdog_payload, dict):
        return _unavailable("watchdog analytics summary is missing watchdog_stats", summary_path)
    metrics = watchdog_metrics_from_dict(watchdog_payload)
    note = None
    if metrics.total_episodes <= 0:
        note = "No guarded coding episodes are recorded in the current snapshot."
    return WatchdogSummaryArtifact(
        available=True,
        generated_at_utc=_text(payload.get("generated_at")),
        trigger_command=_text(payload.get("trigger_command")),
        summary_path=str(summary_path),
        age_minutes=_age_minutes(summary_path),
        metrics=metrics,
        note=note,
    )


def _unavailable(note: str, summary_path: Path) -> WatchdogSummaryArtifact:
    return WatchdogSummaryArtifact(
        available=False,
        generated_at_utc=None,
        trigger_command=None,
        summary_path=str(summary_path),
        age_minutes=None,
        metrics=empty_watchdog_metrics(),
        note=note,
    )


def _mean(values: list[float]) -> float:
    return sum(values) / max(len(values), 1)


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    idx = min(max(q, 0.0), 1.0) * (len(ordered) - 1)
    lower = int(idx)
    upper = min(lower + 1, len(ordered) - 1)
    frac = idx - lower
    return ordered[lower] * (1.0 - frac) + ordered[upper] * frac


def _age_minutes(path: Path) -> float | None:
    try:
        age_seconds = max(0.0, time.time() - path.stat().st_mtime)
    except OSError:
        return None
    return age_seconds / 60.0


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
