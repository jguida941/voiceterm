"""Typed monitor snapshot builder and bundle writer for remote phone mode."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from ..time_utils import utc_timestamp
from .control_plane_read_model import build_control_plane_read_model
from .governance_scan import scan_repo_governance_safely
from .monitor_snapshot_contracts import (
    MonitorSelfAudit,
    MonitorSnapshot,
    MonitorSnapshotPaths,
    MonitorSourceLabel,
)
from .monitor_snapshot_render import (
    render_monitor_snapshot_markdown,
    render_monitor_snapshot_terminal,
)
from .monitor_snapshot_support import (
    build_monitor_source_labels,
    count_dirty_files,
    load_monitor_review_state,
    monitor_output_root,
)
from .startup_context import build_startup_context

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .review_state_models import ReviewState


MONITOR_SNAPSHOT_CONTRACT_ID = "MonitorSnapshot"
MONITOR_SNAPSHOT_SCHEMA_VERSION = 1


def build_monitor_snapshot(
    *,
    repo_root: Path,
    mode: str = "remote_phone",
    agent: str = "operator",
    review_status_dir: Path | None = None,
    governance: "ProjectGovernance | None" = None,
    review_state: "ReviewState | None" = None,
) -> MonitorSnapshot:
    """Build one typed monitor snapshot from shared runtime contracts."""
    resolved_root = repo_root.resolve()
    resolved_governance = governance or scan_repo_governance_safely(resolved_root)
    typed_review_state = load_monitor_review_state(
        repo_root=resolved_root,
        governance=resolved_governance,
        review_state=review_state,
        review_status_dir=review_status_dir,
    )
    startup = build_startup_context(
        repo_root=resolved_root,
        governance=resolved_governance,
        review_state=typed_review_state,
        review_status_dir=review_status_dir,
    )
    model = build_control_plane_read_model(
        resolved_root,
        governance=resolved_governance,
        review_state=typed_review_state,
        review_status_dir=review_status_dir,
    )
    review_state_payload = typed_review_state.to_dict() if typed_review_state else {}
    verdict_presence = _build_verdict_presence(review_state_payload)
    self_audit = _build_self_audit(
        startup=startup,
        model=model,
        verdict_presence=verdict_presence,
    )
    return MonitorSnapshot(
        schema_version=MONITOR_SNAPSHOT_SCHEMA_VERSION,
        contract_id=MONITOR_SNAPSHOT_CONTRACT_ID,
        command="monitor",
        timestamp=utc_timestamp(),
        snapshot_id=_field(startup, "snapshot_id"),
        mode=_normalize_text(mode, default="remote_phone"),
        agent=_normalize_text(agent, default="operator"),
        canonical_runtime_state=_build_runtime_state(startup=startup, model=model),
        observational_telemetry=_build_telemetry(model),
        verdict_presence=verdict_presence,
        worktree_state=_build_worktree_state(
            repo_root=resolved_root,
            branch=_field(model, "branch", default="unknown"),
            head_sha=_field(model, "head_sha", default="unknown"),
            worktree_clean=_field(model, "worktree_clean", cast=bool, default=True),
            ahead_of_upstream=_field(model, "ahead_of_upstream", cast=int),
        ),
        source_labels=tuple(build_monitor_source_labels(repo_root=resolved_root, review_status_dir=review_status_dir)),
        summary=_build_summary(startup=startup, model=model, self_audit=self_audit),
        self_audit=self_audit,
    )


def write_latest_monitor_snapshot(
    *,
    repo_root: Path,
    review_status_dir: Path | None = None,
    mode: str = "remote_phone",
    agent: str = "operator",
) -> MonitorSnapshotPaths:
    """Write the latest monitor snapshot bundle into the review-status root."""
    snapshot = build_monitor_snapshot(
        repo_root=repo_root,
        mode=mode,
        agent=agent,
        review_status_dir=review_status_dir,
    )
    output_root = monitor_output_root(
        repo_root=repo_root,
        review_status_dir=review_status_dir,
    )
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / "monitor_snapshot.json"
    markdown_path = output_root / "monitor_snapshot.md"
    json_path.write_text(json.dumps(snapshot.to_dict(), indent=2), encoding="utf-8")
    markdown_path.write_text(
        render_monitor_snapshot_markdown(snapshot),
        encoding="utf-8",
    )
    return MonitorSnapshotPaths(
        root_dir=str(output_root),
        json_path=str(json_path),
        markdown_path=str(markdown_path),
    )


def _build_runtime_state(*, startup, model) -> dict[str, object]:
    recovery = getattr(startup, "recovery_authority", None)
    return dict(
        [
            ("resolved_phase", _field(model, "resolved_phase")),
            ("operator_interaction_mode", _field(model, "operator_interaction_mode")),
            ("reviewer_mode", _field(model, "reviewer_mode")),
            ("top_blocker", _field(model, "top_blocker")),
            ("next_action", _field(model, "next_action")),
            ("next_command", _resolve_next_command(startup=startup, model=model)),
            ("review_accepted", _field(model, "review_accepted", cast=bool)),
            ("last_guard_ok", _field(model, "last_guard_ok", cast=bool, default=True)),
            ("implementation_permission", _field(startup, "implementation_permission")),
            ("observed_control_topology", _field(startup, "observed_control_topology")),
            ("recovery_action", _field(recovery, "recovery_action")),
            ("recovery_basis", _field(recovery, "recovery_basis")),
            ("recovery_scope", _field(recovery, "recovery_scope")),
            ("pending_action_requests", _field(model, "pending_action_requests", cast=int)),
        ]
    )


def _build_telemetry(model) -> dict[str, object]:
    return dict(
        [
            ("publisher_running", _field(model, "publisher_running", cast=bool)),
            ("reviewer_supervisor_running", _field(model, "supervisor_running", cast=bool)),
            ("codex_conductor_alive", _field(model, "codex_conductor_alive", cast=bool)),
            ("claude_conductor_alive", _field(model, "claude_conductor_alive", cast=bool)),
            ("reviewer_freshness", _field(model, "reviewer_freshness")),
            ("attention_status", _field(model, "attention_status")),
            ("attention_summary", _field(model, "attention_summary")),
        ]
    )


def _build_summary(*, startup, model, self_audit: MonitorSelfAudit) -> dict[str, object]:
    can_work_continue = not _field(
        getattr(startup, "reviewer_gate", None),
        "implementation_blocked",
        cast=bool,
    )
    can_push = _field(model, "push_eligible", cast=bool) and _field(
        model,
        "last_guard_ok",
        cast=bool,
        default=True,
    )
    permission = _field(startup, "implementation_permission")
    state = (
        "blocked"
        if permission == "blocked"
        else "push_ready"
        if can_push
        else _field(model, "resolved_phase", default="active")
    )
    return dict(
        [
            ("state", state),
            ("main_problem", _field(model, "top_blocker", default="none")),
            ("can_work_continue", can_work_continue),
            ("can_code_be_pushed", can_push),
            ("who_needs_to_act", _next_actor(startup=startup, model=model)),
            (
                "what_should_happen_next",
                _resolve_next_command(startup=startup, model=model) or "continue editing",
            ),
            ("confidence", _confidence_label(self_audit)),
        ]
    )


def _next_actor(*, startup, model) -> str:
    if _field(startup, "implementation_permission") == "blocked":
        return "operator"
    if not _field(model, "last_guard_ok", cast=bool, default=True):
        return "implementer"
    freshness = _field(model, "reviewer_freshness")
    if freshness not in {"", "--", "fresh", "recent"} and "ago" in freshness:
        return "reviewer"
    return "operator" if _field(model, "push_eligible", cast=bool) else "implementer"


def _confidence_label(self_audit: MonitorSelfAudit) -> str:
    if not self_audit.reasons:
        return "high"
    return "medium" if len(self_audit.reasons) == 1 else "low"


def _build_self_audit(*, startup, model, verdict_presence: dict[str, object]) -> MonitorSelfAudit:
    coordination = getattr(startup, "coordination", None)
    reasons = [reason for reason in _self_audit_reasons(startup, model, coordination, verdict_presence) if reason]
    return MonitorSelfAudit(
        should_emit_finding=bool(reasons),
        finding_type="observer_self_audit",
        reasons=tuple(reasons),
    )


def _self_audit_reasons(startup, model, coordination, verdict_presence: dict[str, object]) -> tuple[str, ...]:
    stale_verdict = bool(verdict_presence.get("present")) and verdict_presence.get(
        "reviewed_hash_current"
    ) is False
    remote_control = _field(model, "operator_interaction_mode") == "remote_control"
    dual_agent = _field(model, "reviewer_mode") == "active_dual_agent"
    live_conductors = _field(model, "codex_conductor_alive", cast=bool) or _field(
        model,
        "claude_conductor_alive",
        cast=bool,
    )
    return (
        "coordination_resync_required"
        if _field(coordination, "resync_required", cast=bool)
        else "",
        "remote_control_publisher_missing"
        if remote_control and not _field(model, "publisher_running", cast=bool)
        else "",
        "active_dual_agent_without_live_conductors"
        if dual_agent and not live_conductors
        else "",
        "stale_verdict_replayed" if stale_verdict else "",
    )


def _build_verdict_presence(review_state_payload: dict[str, object]) -> dict[str, object]:
    reviewer_runtime = review_state_payload.get("reviewer_runtime")
    bridge = review_state_payload.get("bridge")
    acceptance = reviewer_runtime.get("review_acceptance") if isinstance(reviewer_runtime, dict) else {}
    bridge_mapping = bridge if isinstance(bridge, dict) else {}
    verdict = _normalize_text(acceptance.get("current_verdict"))
    return dict(
        [
            ("present", bool(verdict)),
            ("current_verdict", verdict),
            ("review_needed", bridge_mapping.get("review_needed")),
            ("reviewed_hash_current", bridge_mapping.get("reviewed_hash_current")),
        ]
    )


def _build_worktree_state(
    *,
    repo_root: Path,
    branch: str,
    head_sha: str,
    worktree_clean: bool,
    ahead_of_upstream: int,
) -> dict[str, object]:
    return dict(
        [
            ("branch", branch or "unknown"),
            ("head_sha", head_sha or "unknown"),
            ("clean", worktree_clean),
            ("dirty_files", count_dirty_files(repo_root)),
            ("ahead_of_upstream", ahead_of_upstream),
        ]
    )


def _resolve_next_command(*, startup, model) -> str:
    push_decision = getattr(startup, "push_decision", None)
    return _normalize_text(
        getattr(push_decision, "next_step_command", None) or getattr(model, "next_command", None),
    )


def _normalize_text(value: object, *, default: str = "") -> str:
    return str(value or "").strip() or default


def _field(
    obj: object | None,
    name: str,
    *,
    cast: type[str] | type[bool] | type[int] = str,
    default: str | bool | int = "",
) -> str | bool | int:
    value = getattr(obj, name, default)
    if cast is bool:
        return default if value is None else bool(value)
    if cast is int:
        try:
            return int(default if value is None else value)
        except (TypeError, ValueError):
            return int(default)
    return _normalize_text(value, default=str(default))
