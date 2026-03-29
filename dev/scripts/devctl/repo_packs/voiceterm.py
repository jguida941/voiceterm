"""VoiceTerm repo-pack defaults and read-only helper entrypoints."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_REVIEW_CHANNEL_REL = "dev/active/review_channel.md"
DEFAULT_BRIDGE_REL = "bridge.md"
DEFAULT_REVIEW_STATUS_DIR_REL = "dev/reports/review_channel/latest"
DEFAULT_MOBILE_STATUS_REL = "dev/reports/mobile/latest/full.json"
DEFAULT_PHONE_STATUS_REL = "dev/reports/autonomy/queue/phone/latest.json"
DEFAULT_PUSH_REPORT_REL = "dev/reports/push/latest.json"
# ---------------------------------------------------------------------------
# Centralized path configuration for VoiceTerm repo artifacts
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RepoPathConfig:
    """Frozen registry of repo-relative artifact paths for VoiceTerm.

    Thin clients and operator-console modules can read paths from a single
    ``RepoPathConfig`` instead of each module defining its own constants.
    Use the ``voiceterm_defaults()`` classmethod to get the standard config.
    """

    review_channel_rel: str = DEFAULT_REVIEW_CHANNEL_REL
    bridge_rel: str = DEFAULT_BRIDGE_REL
    review_status_dir_rel: str = DEFAULT_REVIEW_STATUS_DIR_REL
    mobile_status_rel: str = DEFAULT_MOBILE_STATUS_REL
    phone_status_rel: str = DEFAULT_PHONE_STATUS_REL
    push_report_rel: str = DEFAULT_PUSH_REPORT_REL

    # Structured review-state JSON candidates (tried in order)
    review_state_candidates: tuple[str, ...] = (
        "dev/reports/review_channel/projections/latest/review_state.json",
        "dev/reports/review_channel/latest/review_state.json",
        "dev/reports/review_channel/review_state.json",
    )

    # Full review-channel projection candidates (tried in order)
    review_full_candidates: tuple[str, ...] = (
        "dev/reports/review_channel/projections/latest/full.json",
        "dev/reports/review_channel/latest/full.json",
    )

    # Session trace directory candidates (tried in order)
    session_trace_dir_candidates: tuple[str, ...] = (
        "dev/reports/review_channel/projections/latest/sessions",
        "dev/reports/review_channel/latest/sessions",
    )

    # Operator decision latest file
    operator_decision_rel: str = (
        "dev/reports/review_channel/operator_decisions/latest.md"
    )

    # Operator decision root directory
    operator_decision_root_rel: str = (
        "dev/reports/review_channel/operator_decisions"
    )

    # Rollover handoff root directory
    rollover_root_rel: str = "dev/reports/review_channel/rollovers"

    # Watchdog summary artifact
    watchdog_summary_rel: str = "dev/reports/data_science/latest/summary.json"

    # Ralph guardrail report
    ralph_report_rel: str = "dev/reports/ralph/latest/ralph-report.json"

    # Operator Console dev-log root
    dev_log_root_rel: str = "dev/reports/review_channel/operator_console"

    # Operator Console layout state persistence
    layout_state_rel: str = (
        "dev/reports/review_channel/operator_console/layout_state.json"
    )

    # Canonical event-backed review-channel artifact root
    review_artifact_root_rel: str = "dev/reports/review_channel"

    # Event trace log (ndjson)
    review_event_log_rel: str = (
        "dev/reports/review_channel/events/trace.ndjson"
    )

    # Reduced review-channel state JSON
    review_state_json_rel: str = (
        "dev/reports/review_channel/state/latest.json"
    )

    # Event-backed projections directory
    review_projections_dir_rel: str = (
        "dev/reports/review_channel/projections/latest"
    )

    # Promotion plan doc (continuous swarm)
    promotion_plan_rel: str = "dev/active/continuous_swarm.md"

    # Governance review JSONL log
    governance_review_log_rel: str = (
        "dev/reports/governance/finding_reviews.jsonl"
    )

    # Governance review summary output directory
    governance_review_summary_root_rel: str = "dev/reports/governance/latest"

    # External (imported) finding JSONL log
    external_finding_log_rel: str = (
        "dev/reports/governance/external_pilot_findings.jsonl"
    )

    # External finding summary output directory
    external_finding_summary_root_rel: str = (
        "dev/reports/governance/external_findings_latest"
    )

    # Autonomy plan doc
    autonomy_plan_doc_rel: str = "dev/active/autonomous_control_plane.md"

    # Active-doc index
    active_index_doc_rel: str = "dev/active/INDEX.md"

    # Active master plan
    active_master_plan_doc_rel: str = "dev/active/MASTER_PLAN.md"

    # Autonomy swarm_run bundle root
    autonomy_run_root_rel: str = "dev/reports/autonomy/runs"

    # Autonomy swarm bundle root
    autonomy_swarm_root_rel: str = "dev/reports/autonomy/swarms"

    # Autonomy source root (post-audit digests)
    autonomy_source_root_rel: str = "dev/reports/autonomy"

    # Autonomy library root (post-audit library bundles)
    autonomy_library_root_rel: str = "dev/reports/autonomy/library"

    # Autonomy benchmark bundle root
    autonomy_benchmark_root_rel: str = "dev/reports/autonomy/benchmarks"

    # Audit event log (devctl event JSONL)
    audit_event_log_rel: str = "dev/reports/audits/devctl_events.jsonl"

    # Data-science snapshot output root
    data_science_output_root_rel: str = "dev/reports/data_science"

    # Watchdog episode persistence root
    watchdog_episode_root_rel: str = "dev/reports/autonomy/watchdog/episodes"

    # Top-level reports root (used by retention helpers)
    reports_root_rel: str = "dev/reports"

    # Aggregated probe-report output root
    probe_report_output_root_rel: str = "dev/reports/probes"

    # Audit scaffold generated output
    audit_scaffold_output_rel: str = (
        "dev/reports/audits/RUST_AUDIT_FINDINGS.md"
    )

    # Audit scaffold template
    audit_scaffold_template_rel: str = (
        "dev/config/templates/rust_audit_findings_template.md"
    )

    # Publication sync registry
    publication_sync_registry_rel: str = (
        "dev/config/publication_sync_registry.json"
    )

    # Integration federation audit log
    integration_audit_log_rel: str = "dev/reports/integration_import_audit.jsonl"

    # Repo quality policy JSON
    repo_policy_rel: str = "dev/config/devctl_repo_policy.json"

    @classmethod
    def voiceterm_defaults(cls) -> RepoPathConfig:
        """Return the standard VoiceTerm path configuration."""
        return cls()


VOICETERM_PATH_CONFIG: RepoPathConfig = RepoPathConfig.voiceterm_defaults()


@dataclass(frozen=True)
class WorkflowPresetDefinition:
    """Repo-pack owned workflow preset metadata for thin clients."""

    preset_id: str
    label: str
    plan_doc: str
    mp_scope: str
    summary: str


_WORKFLOW_PRESET_DEFINITIONS: tuple[WorkflowPresetDefinition, ...] = (
    WorkflowPresetDefinition(
        preset_id="operator_console",
        label="Operator Console",
        plan_doc="dev/active/operator_console.md",
        mp_scope="MP-359",
        summary=(
            "Desktop shell work: simplify the operator flow, keep backend commands "
            "honest, and surface loop/audit state without hidden steps."
        ),
    ),
    WorkflowPresetDefinition(
        preset_id="continuous_swarm",
        label="Continuous Swarm",
        plan_doc="dev/active/continuous_swarm.md",
        mp_scope="MP-358",
        summary=(
            "Reviewer/coder continuity work: keep Codex review and Claude coding "
            "moving through the scoped plan with minimal operator babysitting."
        ),
    ),
    WorkflowPresetDefinition(
        preset_id="review_channel",
        label="Review Channel",
        plan_doc="dev/active/review_channel.md",
        mp_scope="MP-355",
        summary=(
            "Shared review bridge work: packets, projections, and the live "
            "Codex/Claude/operator coordination lane."
        ),
    ),
    WorkflowPresetDefinition(
        preset_id="autonomous_control_plane",
        label="Autonomy Control",
        plan_doc="dev/active/autonomous_control_plane.md",
        mp_scope="MP-338",
        summary=(
            "Controller/autonomy work: guarded swarm runs, controller state, and "
            "loop evidence attached to the active plan."
        ),
    ),
    WorkflowPresetDefinition(
        preset_id="cursor_editor",
        label="Cursor Editor",
        plan_doc="dev/active/operator_console.md",
        mp_scope="MP-359",
        summary=(
            "IDE-integrated editing via Cursor: targeted file changes backed by "
            "the same review-channel guard pipeline as Codex and Claude."
        ),
    ),
)


def workflow_preset_definitions() -> tuple[WorkflowPresetDefinition, ...]:
    """Return the repo-pack owned workflow presets."""
    return _WORKFLOW_PRESET_DEFINITIONS


def voiceterm_repo_root() -> Path | None:
    """Return the VoiceTerm repo root from devctl config, or None if unavailable."""
    try:
        from ..config import REPO_ROOT

        return Path(REPO_ROOT) if REPO_ROOT else None
    except ImportError:
        return None


def collect_devctl_git_status() -> dict[str, object]:
    """Read-only helper: collect git status via the devctl collector."""
    try:
        from ..collect import collect_git_status

        result = collect_git_status()
        return result if isinstance(result, dict) else {}
    except ImportError:
        return {}


def collect_devctl_mutation_summary() -> dict[str, object]:
    """Read-only helper: collect mutation summary via the devctl collector."""
    try:
        from ..collect import collect_mutation_summary

        result = collect_mutation_summary()
        return result if isinstance(result, dict) else {}
    except ImportError:
        return {}


def collect_devctl_ci_runs(*, limit: int = 5) -> dict[str, object]:
    """Read-only helper: collect recent CI runs via the devctl collector."""
    try:
        from ..collect import collect_ci_runs

        result = collect_ci_runs(limit=limit)
        return result if isinstance(result, dict) else {}
    except ImportError:
        return {}


def collect_devctl_quality_backlog(
    *, top_n: int = 20, include_tests: bool = False
) -> dict[str, object] | None:
    """Read-only helper: collect quality backlog via the devctl collector."""
    try:
        from ..quality_backlog.report import collect_quality_backlog

        result = collect_quality_backlog(top_n=top_n, include_tests=include_tests)
        return result if isinstance(result, dict) else None
    except ImportError:
        return None


def load_review_payload_from_bridge(
    repo_root: Path, *, path_config: RepoPathConfig | None = None
) -> tuple[dict[str, object] | None, tuple[str, ...]]:
    """Refresh and load the repo-pack owned review payload for thin clients."""
    config = path_config or VOICETERM_PATH_CONFIG
    review_channel_path = repo_root / config.review_channel_rel
    bridge_path = repo_root / config.bridge_rel
    status_root = repo_root / config.review_status_dir_rel
    if not review_channel_path.exists() or not bridge_path.exists():
        return None, ()

    from ..review_channel.state import refresh_status_snapshot

    status_snapshot = refresh_status_snapshot(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=status_root,
    )
    payload = json.loads(
        Path(status_snapshot.projection_paths.full_path).read_text(encoding="utf-8")
    )
    return (
        payload if isinstance(payload, dict) else {},
        tuple(status_snapshot.warnings),
    )
