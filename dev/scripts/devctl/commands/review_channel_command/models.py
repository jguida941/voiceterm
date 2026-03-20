"""Dataclasses for the `devctl review-channel` command."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ...review_channel.core import REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE
from ...time_utils import utc_timestamp
from .constants import RUNTIME_PATH_FIELD_NAMES


def _as_path(value: object) -> Path | None:
    """Return a resolved Path or None."""
    return value if isinstance(value, Path) else None


@dataclass(frozen=True, slots=True)
class ReviewChannelErrorReport:
    """Structured review-channel failure payload."""

    command: str = "review-channel"
    timestamp: str = field(default_factory=utc_timestamp)
    action: str | None = None
    ok: bool = False
    exit_ok: bool = False
    exit_code: int = 1
    execution_mode: str = "auto"
    terminal: str = "terminal-app"
    terminal_profile_requested: str | None = None
    terminal_profile_applied: str | None = None
    approval_mode: str = "default"
    dangerous: bool = False
    rollover_threshold_pct: int | None = None
    rollover_trigger: str | None = None
    await_ack_seconds: int | None = None
    retirement_note: str = REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sessions: list[dict[str, object]] = field(default_factory=list)
    handoff_bundle: dict[str, object] | None = None
    handoff_ack_required: bool = False
    handoff_ack_observed: bool | None = None
    bridge_liveness: dict[str, object] | None = None
    projection_paths: dict[str, object] | None = None
    artifact_paths: dict[str, object] | None = None
    packet: dict[str, object] | None = None
    packets: list[dict[str, object]] = field(default_factory=list)
    history: list[dict[str, object]] = field(default_factory=list)
    promotion: dict[str, object] | None = None
    bridge_heartbeat_refresh: dict[str, object] | None = None
    reviewer_worker: dict[str, object] | None = None
    reviewer_supervisor: dict[str, object] | None = None
    service_identity: dict[str, object] | None = None
    attach_auth_policy: dict[str, object] | None = None

    def to_report(self) -> dict[str, object]:
        """Convert the payload into JSON/markdown renderer input."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    """Resolved review-channel paths."""

    review_channel_path: Path | None = None
    bridge_path: Path | None = None
    rollover_dir: Path | None = None
    status_dir: Path | None = None
    promotion_plan_path: Path | None = None
    script_dir: Path | None = None
    artifact_paths: object | None = None

    @classmethod
    def from_mapping(cls, paths: Mapping[str, object]) -> "RuntimePaths":
        """Build a typed view from legacy dict-style tests."""
        resolved_paths = {
            name: _as_path(paths.get(name))
            for name in RUNTIME_PATH_FIELD_NAMES
        }
        return cls(**resolved_paths, artifact_paths=paths.get("artifact_paths"))

    def get(self, key: str, default: object = None) -> object:
        """Support legacy dict-style access during the staged refactor."""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> object:
        """Support legacy dict-style indexing during the staged refactor."""
        if not hasattr(self, key):
            raise KeyError(key)
        return getattr(self, key)


@dataclass(frozen=True, slots=True)
class PublisherLifecycleAssessment:
    """Publisher state for ensure flows."""

    publisher_state: dict[str, object]
    publisher_running: bool
    publisher_required: bool
    publisher_status: str
    publisher_start_status: str = "not_attempted"
    publisher_pid: int | None = None
    publisher_log_path: str | None = None
    recommended_command: str | None = None
    attention_override: str | None = None
    details: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EnsureBridgeStatus:
    """Reduced bridge-health view for ensure."""

    reviewer_mode: str
    codex_poll_state: str
    reviewer_freshness: str
    heartbeat_age_seconds: object
    attention_status: str
    claude_ack_current: bool
    review_needed: bool
    reviewer_supervisor_running: bool
    reviewer_worker: dict[str, object] | None
    reviewer_supervisor: dict[str, object] | None
    service_identity: dict[str, object] | None
    attach_auth_policy: dict[str, object] | None

    @property
    def heartbeat_ok(self) -> bool:
        freshness = self.reviewer_freshness
        if freshness in {"", "unknown"}:
            freshness = self.codex_poll_state
        return freshness in {"fresh", "poll_due"}

    @property
    def loop_ok(self) -> bool:
        return self.heartbeat_ok and self.claude_ack_current

    @property
    def reviewer_supervisor_ok(self) -> bool:
        return (not self.review_needed) or self.reviewer_supervisor_running


@dataclass(frozen=True, slots=True)
class EnsureActionReport:
    """Ensure output that omits absent optional fields."""

    command: str
    action: str
    ok: bool
    reviewer_mode: str
    codex_poll_state: str
    reviewer_freshness: str
    heartbeat_age_seconds: object
    attention_status: str
    refreshed: bool
    publisher: dict[str, object]
    publisher_required: bool
    publisher_status: str
    publisher_start_status: str
    reviewer_worker: dict[str, object] | None
    reviewer_supervisor: dict[str, object] | None
    service_identity: dict[str, object] | None
    attach_auth_policy: dict[str, object] | None
    detail: str
    review_needed: bool | None = None
    publisher_pid: int | None = None
    publisher_log_path: str | None = None
    recommended_command: str | None = None

    def to_report(self) -> dict[str, object]:
        """Convert to the stable report surface while omitting absent keys."""
        report = asdict(self)
        optional_keys = (
            "review_needed",
            "publisher_pid",
            "publisher_log_path",
            "recommended_command",
        )
        for key in optional_keys:
            if report.get(key) is None:
                report.pop(key, None)
        return report


@dataclass(frozen=True, slots=True)
class ReviewerStateReportDefaults:
    """Stable kwargs for bridge-backed reviewer state reports."""

    terminal_profile_applied: str | None = None
    sessions: tuple[object, ...] = ()
    handoff_bundle: dict[str, object] | None = None
    launched: bool = False
    handoff_ack_required: bool = False
    handoff_ack_observed: bool | None = None
    promotion: dict[str, object] | None = None
    bridge_heartbeat_refresh: dict[str, object] | None = None
    execution_mode_override: str = "markdown-bridge"

    def to_kwargs(self) -> dict[str, object]:
        """Return bridge-render kwargs without a large dict literal."""
        return asdict(self)


REVIEWER_STATE_REPORT_DEFAULTS = ReviewerStateReportDefaults().to_kwargs()
