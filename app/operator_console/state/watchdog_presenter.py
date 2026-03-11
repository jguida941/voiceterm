"""Shared watchdog formatting helpers for Operator Console read-only surfaces."""

from __future__ import annotations

from typing import TypeVar

from dev.scripts.devctl.watchdog import (
    WatchdogGuardFamilyMetrics,
    WatchdogMetrics,
    WatchdogProviderMetrics,
    WatchdogSummaryArtifact,
)

_RowT = TypeVar("_RowT", WatchdogProviderMetrics, WatchdogGuardFamilyMetrics)


def watchdog_available(watchdog_snapshot: WatchdogSummaryArtifact | None) -> bool:
    """Return True when a typed watchdog snapshot is present and usable."""
    return watchdog_snapshot is not None and watchdog_snapshot.available


def watchdog_note(
    watchdog_snapshot: WatchdogSummaryArtifact | None,
    *,
    default: str = "Watchdog summary has not been generated yet.",
) -> str:
    """Return the best visible note for missing or empty watchdog data."""
    if watchdog_snapshot is not None and watchdog_snapshot.note:
        return watchdog_snapshot.note
    return default


def watchdog_summary_line(watchdog_snapshot: WatchdogSummaryArtifact | None) -> str:
    """Render one compact one-line watchdog summary."""
    metrics = _metrics(watchdog_snapshot)
    if metrics is None:
        return watchdog_note(watchdog_snapshot, default="unavailable")
    return (
        f"{metrics.total_episodes} episodes | "
        f"{format_watchdog_pct(metrics.success_rate_pct)} accepted | "
        f"{format_watchdog_pct(metrics.false_positive_rate_pct)} noisy/skipped"
    )


def watchdog_topline_lines(watchdog_snapshot: WatchdogSummaryArtifact | None) -> list[str]:
    """Render the top-level watchdog bullet lines used across views."""
    metrics = _metrics(watchdog_snapshot)
    if metrics is None:
        return [f"- {watchdog_note(watchdog_snapshot)}"]
    return [
        f"- Total episodes: {metrics.total_episodes}",
        f"- Accepted episodes: {format_watchdog_pct(metrics.success_rate_pct)}",
        f"- Noisy/skipped rate: {format_watchdog_pct(metrics.false_positive_rate_pct)}",
        f"- Known provider coverage: {format_watchdog_pct(metrics.known_provider_pct)}",
        f"- Avg time to green: {format_watchdog_seconds(metrics.avg_time_to_green_seconds)}",
        f"- P50 time to green: {format_watchdog_seconds(metrics.p50_time_to_green_seconds)}",
        f"- Avg guard runtime: {format_watchdog_seconds(metrics.avg_guard_runtime_seconds)}",
        f"- Avg retry count: {format_watchdog_decimal(metrics.avg_retry_count)}",
        f"- Avg escaped findings: {format_watchdog_decimal(metrics.avg_escaped_findings)}",
    ]


def watchdog_provider_lines(
    watchdog_snapshot: WatchdogSummaryArtifact | None,
    *,
    limit: int = 4,
) -> list[str]:
    """Render one bullet per provider from the watchdog metrics."""
    metrics = _metrics(watchdog_snapshot)
    if metrics is None:
        return []
    providers = _limit_rows(metrics.providers, limit)
    return [f"- {row.provider}: {row.episodes} episode(s)" for row in providers]


def watchdog_guard_family_lines(
    watchdog_snapshot: WatchdogSummaryArtifact | None,
    *,
    limit: int = 4,
) -> list[str]:
    """Render one bullet per guard family from the watchdog metrics."""
    metrics = _metrics(watchdog_snapshot)
    if metrics is None:
        return []
    guard_families = _limit_rows(metrics.guard_families, limit)
    return [
        (
            "- "
            f"{row.guard_family}: {row.episodes} episode(s), "
            f"{format_watchdog_pct(row.success_rate_pct)} accepted, "
            f"avg green {format_watchdog_seconds(row.avg_time_to_green_seconds)}"
        )
        for row in guard_families
    ]


def watchdog_provenance_lines(
    watchdog_snapshot: WatchdogSummaryArtifact | None,
) -> list[str]:
    """Render artifact provenance lines for the watchdog snapshot."""
    if watchdog_snapshot is None:
        return []
    lines = [
        f"- Summary path: {watchdog_snapshot.summary_path or 'n/a'}",
        f"- Generated at: {watchdog_snapshot.generated_at_utc or 'n/a'}",
    ]
    age_minutes = watchdog_snapshot.age_minutes
    if age_minutes is not None:
        lines.append(f"- Snapshot age: {float(age_minutes):.1f} minutes")
    if watchdog_snapshot.trigger_command:
        lines.append(f"- Trigger command: {watchdog_snapshot.trigger_command}")
    if watchdog_snapshot.note:
        lines.append(f"- Note: {watchdog_snapshot.note}")
    return lines


def format_watchdog_pct(value: object) -> str:
    """Render a percentage-like metric for operator-facing text."""
    try:
        return f"{float(value):.0f}%"
    except (TypeError, ValueError):
        return "n/a"


def format_watchdog_seconds(value: object) -> str:
    """Render a seconds metric for operator-facing text."""
    try:
        return f"{float(value):.2f}s"
    except (TypeError, ValueError):
        return "n/a"


def format_watchdog_decimal(value: object) -> str:
    """Render a generic decimal metric for operator-facing text."""
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "n/a"


def _metrics(
    watchdog_snapshot: WatchdogSummaryArtifact | None,
) -> WatchdogMetrics | None:
    if not watchdog_available(watchdog_snapshot):
        return None
    return watchdog_snapshot.metrics


def _limit_rows(
    rows: tuple[_RowT, ...],
    limit: int,
) -> tuple[_RowT, ...]:
    return rows[: max(0, limit)]
