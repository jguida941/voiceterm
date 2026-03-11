"""Typed watchdog models shared by emitters, reducers, and read-only consumers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..numeric import to_float, to_int, to_optional_float


@dataclass(frozen=True)
class GuardedCodingEpisode:
    """Canonical typed row for one guarded-coding watchdog episode."""

    episode_id: str
    task_id: str
    plan_id: str
    controller_run_id: str
    provider: str
    session_id: str
    peer_session_id: str
    reviewed_worktree_hash_before: str
    reviewed_worktree_hash_after: str
    guard_family: str
    guard_command_id: str
    trigger_reason: str
    files_changed: tuple[str, ...]
    file_count: int
    lines_added_before_guard: int
    lines_removed_before_guard: int
    lines_added_after_guard: int
    lines_removed_after_guard: int
    diff_churn_before_guard: int
    diff_churn_after_guard: int
    guard_started_at_utc: str | None
    guard_finished_at_utc: str | None
    episode_started_at_utc: str | None
    episode_finished_at_utc: str | None
    first_edit_at_utc: str | None
    terminal_active_seconds: float
    terminal_idle_seconds: float
    guard_runtime_seconds: float
    test_runtime_seconds: float
    review_to_fix_seconds: float
    time_to_green_seconds: float | None
    retry_count: int
    guard_fail_count_before_green: int
    test_fail_count_before_green: int
    review_findings_count: int
    escaped_findings_count: int
    handoff_count: int
    stale_peer_pause_count: int
    guard_result: str
    reviewer_verdict: str
    post_action: str
    cwd: str


@dataclass(frozen=True)
class WatchdogProviderMetrics:
    """Per-provider episode counts in the reduced watchdog summary."""

    provider: str
    episodes: int


@dataclass(frozen=True)
class WatchdogGuardFamilyMetrics:
    """Per-guard-family aggregate row in the reduced watchdog summary."""

    guard_family: str
    episodes: int
    success_rate_pct: float
    avg_time_to_green_seconds: float


@dataclass(frozen=True)
class WatchdogMetrics:
    """Reduced watchdog metrics consumed by reports and UI surfaces."""

    total_episodes: int
    success_rate_pct: float
    avg_time_to_green_seconds: float
    p50_time_to_green_seconds: float
    avg_guard_runtime_seconds: float
    avg_retry_count: float
    avg_escaped_findings: float
    false_positive_rate_pct: float
    known_provider_pct: float
    providers: tuple[WatchdogProviderMetrics, ...] = ()
    guard_families: tuple[WatchdogGuardFamilyMetrics, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        payload["total_episodes"] = self.total_episodes
        payload["success_rate_pct"] = self.success_rate_pct
        payload["avg_time_to_green_seconds"] = self.avg_time_to_green_seconds
        payload["p50_time_to_green_seconds"] = self.p50_time_to_green_seconds
        payload["avg_guard_runtime_seconds"] = self.avg_guard_runtime_seconds
        payload["avg_retry_count"] = self.avg_retry_count
        payload["avg_escaped_findings"] = self.avg_escaped_findings
        payload["false_positive_rate_pct"] = self.false_positive_rate_pct
        payload["known_provider_pct"] = self.known_provider_pct
        payload["providers"] = [
            {"provider": row.provider, "episodes": row.episodes}
            for row in self.providers
        ]
        payload["guard_families"] = [
            _guard_family_metrics_to_dict(row) for row in self.guard_families
        ]
        return payload


@dataclass(frozen=True)
class WatchdogSummaryArtifact:
    """Typed read-only summary artifact loaded from data-science output."""

    available: bool
    generated_at_utc: str | None
    trigger_command: str | None
    summary_path: str | None
    age_minutes: float | None
    metrics: WatchdogMetrics
    note: str | None = None


def guarded_coding_episode_from_dict(payload: dict[str, Any]) -> GuardedCodingEpisode:
    """Parse one episode row from JSON-compatible payload data."""
    return GuardedCodingEpisode(
        episode_id=_text(payload.get("episode_id")),
        task_id=_text(payload.get("task_id"), "guarded-command"),
        plan_id=_text(payload.get("plan_id"), "unscoped"),
        controller_run_id=_text(payload.get("controller_run_id"), "local"),
        provider=_text(payload.get("provider"), "unknown"),
        session_id=_text(payload.get("session_id"), "unknown"),
        peer_session_id=_text(payload.get("peer_session_id")),
        reviewed_worktree_hash_before=_text(payload.get("reviewed_worktree_hash_before")),
        reviewed_worktree_hash_after=_text(payload.get("reviewed_worktree_hash_after")),
        guard_family=_text(payload.get("guard_family"), "unknown"),
        guard_command_id=_text(payload.get("guard_command_id")),
        trigger_reason=_text(payload.get("trigger_reason"), "manual_guard_run"),
        files_changed=_text_tuple(payload.get("files_changed")),
        file_count=to_int(payload.get("file_count"), default=0),
        lines_added_before_guard=to_int(payload.get("lines_added_before_guard"), default=0),
        lines_removed_before_guard=to_int(payload.get("lines_removed_before_guard"), default=0),
        lines_added_after_guard=to_int(payload.get("lines_added_after_guard"), default=0),
        lines_removed_after_guard=to_int(payload.get("lines_removed_after_guard"), default=0),
        diff_churn_before_guard=to_int(payload.get("diff_churn_before_guard"), default=0),
        diff_churn_after_guard=to_int(payload.get("diff_churn_after_guard"), default=0),
        guard_started_at_utc=_optional_text(payload.get("guard_started_at_utc")),
        guard_finished_at_utc=_optional_text(payload.get("guard_finished_at_utc")),
        episode_started_at_utc=_optional_text(payload.get("episode_started_at_utc")),
        episode_finished_at_utc=_optional_text(payload.get("episode_finished_at_utc")),
        first_edit_at_utc=_optional_text(payload.get("first_edit_at_utc")),
        terminal_active_seconds=to_float(payload.get("terminal_active_seconds"), default=0.0),
        terminal_idle_seconds=to_float(payload.get("terminal_idle_seconds"), default=0.0),
        guard_runtime_seconds=to_float(payload.get("guard_runtime_seconds"), default=0.0),
        test_runtime_seconds=to_float(payload.get("test_runtime_seconds"), default=0.0),
        review_to_fix_seconds=to_float(payload.get("review_to_fix_seconds"), default=0.0),
        time_to_green_seconds=to_optional_float(payload.get("time_to_green_seconds")),
        retry_count=to_int(payload.get("retry_count"), default=0),
        guard_fail_count_before_green=to_int(payload.get("guard_fail_count_before_green"), default=0),
        test_fail_count_before_green=to_int(payload.get("test_fail_count_before_green"), default=0),
        review_findings_count=to_int(payload.get("review_findings_count"), default=0),
        escaped_findings_count=to_int(payload.get("escaped_findings_count"), default=0),
        handoff_count=to_int(payload.get("handoff_count"), default=0),
        stale_peer_pause_count=to_int(payload.get("stale_peer_pause_count"), default=0),
        guard_result=_text(payload.get("guard_result"), "unknown"),
        reviewer_verdict=_text(payload.get("reviewer_verdict"), "unknown"),
        post_action=_text(payload.get("post_action"), "none"),
        cwd=_text(payload.get("cwd")),
    )


def watchdog_metrics_to_dict(metrics: WatchdogMetrics) -> dict[str, Any]:
    """Serialize one typed metrics bundle into a JSON-compatible dict."""
    return metrics.to_dict()


def watchdog_metrics_from_dict(payload: dict[str, Any]) -> WatchdogMetrics:
    """Parse reduced watchdog metrics from JSON-compatible payload data."""
    providers = tuple(
        WatchdogProviderMetrics(
            provider=_text(item.get("provider"), "unknown"),
            episodes=to_int(item.get("episodes"), default=0),
        )
        for item in _dict_list(payload.get("providers"))
    )
    guard_families = tuple(
        WatchdogGuardFamilyMetrics(
            guard_family=_text(item.get("guard_family"), "unknown"),
            episodes=to_int(item.get("episodes"), default=0),
            success_rate_pct=to_float(item.get("success_rate_pct"), default=0.0),
            avg_time_to_green_seconds=to_float(
                item.get("avg_time_to_green_seconds"), default=0.0
            ),
        )
        for item in _dict_list(payload.get("guard_families"))
    )
    return WatchdogMetrics(
        total_episodes=to_int(payload.get("total_episodes"), default=0),
        success_rate_pct=to_float(payload.get("success_rate_pct"), default=0.0),
        avg_time_to_green_seconds=to_float(
            payload.get("avg_time_to_green_seconds"), default=0.0
        ),
        p50_time_to_green_seconds=to_float(
            payload.get("p50_time_to_green_seconds"), default=0.0
        ),
        avg_guard_runtime_seconds=to_float(
            payload.get("avg_guard_runtime_seconds"), default=0.0
        ),
        avg_retry_count=to_float(payload.get("avg_retry_count"), default=0.0),
        avg_escaped_findings=to_float(
            payload.get("avg_escaped_findings"), default=0.0
        ),
        false_positive_rate_pct=to_float(
            payload.get("false_positive_rate_pct"), default=0.0
        ),
        known_provider_pct=to_float(payload.get("known_provider_pct"), default=0.0),
        providers=providers,
        guard_families=guard_families,
    )


def empty_watchdog_metrics() -> WatchdogMetrics:
    """Return the canonical zero-value watchdog metrics bundle."""
    return WatchdogMetrics(
        total_episodes=0,
        success_rate_pct=0.0,
        avg_time_to_green_seconds=0.0,
        p50_time_to_green_seconds=0.0,
        avg_guard_runtime_seconds=0.0,
        avg_retry_count=0.0,
        avg_escaped_findings=0.0,
        false_positive_rate_pct=0.0,
        known_provider_pct=0.0,
        providers=(),
        guard_families=(),
    )


def _guard_family_metrics_to_dict(
    row: WatchdogGuardFamilyMetrics,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    payload["guard_family"] = row.guard_family
    payload["episodes"] = row.episodes
    payload["success_rate_pct"] = row.success_rate_pct
    payload["avg_time_to_green_seconds"] = row.avg_time_to_green_seconds
    return payload


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _text(value: object, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _optional_text(value: object) -> str | None:
    text = _text(value)
    return text or None


def _text_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(_text(item) for item in value if _text(item))
