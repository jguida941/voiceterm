"""Shared watchdog helpers used by guard-run, data-science, and UI surfaces."""

from .episode import (
    DEFAULT_EPISODE_ROOT,
    build_guarded_coding_episode,
    emit_guarded_coding_episode,
    read_guarded_coding_episodes,
)
from .metrics import build_watchdog_metrics, load_watchdog_summary_artifact
from .probe_gate import (
    ProbeAggregation,
    ProbeScanResult,
    aggregate_probe_scans,
    run_probe_scan,
)
from .models import (
    GuardedCodingEpisode,
    WatchdogGuardFamilyMetrics,
    WatchdogMetrics,
    WatchdogProviderMetrics,
    WatchdogSummaryArtifact,
    empty_watchdog_metrics,
    guarded_coding_episode_from_dict,
    watchdog_metrics_from_dict,
    watchdog_metrics_to_dict,
)
