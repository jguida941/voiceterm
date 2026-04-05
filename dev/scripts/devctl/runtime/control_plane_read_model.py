"""Single resolved control-plane state for all governance surfaces.

Five surfaces (dashboard, operator console, phone, mobile, control-state)
previously computed state independently, allowing 3+ reducers to disagree.
This module provides ONE frozen dataclass and ONE builder so every surface
renders from an identical resolved snapshot.

Build once with ``build_control_plane_read_model(repo_root)``, then pass
the frozen result to any renderer.  Gate resolution lives in
``control_plane_resolve`` to keep both files under the 350-line soft limit.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .auto_mode import AutoModeInputs, AutoModePhase, resolve_auto_mode_phase
from .control_plane_resolve import (
    load_git_state,
    load_sources,
    resolve_blocker_and_action,
    resolve_daemon_state,
    resolve_pending_packets,
    resolve_quality,
    resolve_reviewer_state,
    utc_now_iso,
)
from .value_coercion import coerce_bool, coerce_int, coerce_string


CONTROL_PLANE_READ_MODEL_CONTRACT_ID = "ControlPlaneReadModel"
CONTROL_PLANE_READ_MODEL_SCHEMA_VERSION = 1


# -------------------------------------------------------
# Frozen read model -- all surfaces render only this
# -------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ControlPlaneReadModel:
    """Single resolved state for every governance surface to render."""

    timestamp: str
    branch: str
    head_sha: str
    worktree_clean: bool
    ahead_of_upstream: int

    # Resolved gates (computed ONCE from auto-mode resolution)
    resolved_phase: str
    push_eligible: bool
    implementation_blocked: bool
    top_blocker: str
    next_action: str
    next_command: str

    # Reviewer state
    reviewer_mode: str
    operator_interaction_mode: str
    reviewer_freshness: str
    review_accepted: bool
    last_reviewed_sha: str
    attention_status: str
    attention_summary: str

    # Session health
    publisher_running: bool
    supervisor_running: bool
    codex_conductor_alive: bool
    claude_conductor_alive: bool
    pending_action_requests: int

    # Quality
    last_guard_ok: bool
    check_details: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _nested_get(d: dict[str, Any] | None, *keys: str) -> Any:
    """Safely traverse nested dicts, returning None on any miss."""
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


# -------------------------------------------------------
# Public builder: one call, one frozen model
# -------------------------------------------------------

def build_control_plane_read_model(
    repo_root: Path,
    *,
    sources_override: dict[str, Any] | None = None,
    git_override: dict[str, Any] | None = None,
) -> ControlPlaneReadModel:
    """Load all artifacts ONCE, resolve ALL gates, return frozen model.

    ``sources_override`` and ``git_override`` allow tests to inject
    pre-built data without touching the filesystem or git.
    """
    sources = sources_override if sources_override is not None else load_sources(repo_root)
    git = git_override if git_override is not None else load_git_state(repo_root)

    receipt = sources.get("receipt")
    review_state = sources.get("review_state")
    push_report = sources.get("push_report")
    compact = sources.get("compact_json")
    full_json = sources.get("full_json")

    reviewer = resolve_reviewer_state(review_state, compact, full_json)
    daemons = resolve_daemon_state(sources)
    quality = resolve_quality(push_report)
    blocker = resolve_blocker_and_action(receipt, review_state, quality)
    pending = resolve_pending_packets(review_state)

    impl_blocked = coerce_bool((receipt or {}).get("implementation_blocked", False))
    # Governance-first: review_state > receipt > default
    op_mode = (
        coerce_string(_nested_get(review_state, "collaboration", "operator_interaction_mode"))
        or coerce_string(_nested_get(review_state, "reviewer_runtime", "operator_interaction_mode"))
        or coerce_string((receipt or {}).get("operator_interaction_mode"))
        or "local_terminal"
    )
    push_action = coerce_string((receipt or {}).get("push_action"))

    auto_state = resolve_auto_mode_phase(AutoModeInputs(
        push_decision_action=push_action,
        worktree_clean=git.get("clean", True),
        review_gate_allows_push=reviewer["review_accepted"],
        reviewer_mode=reviewer["reviewer_mode"],
        implementation_blocked=impl_blocked,
        last_guard_ok=quality["last_guard_ok"],
        current_head_commit=git.get("head", ""),
        last_reviewed_sha=reviewer.get("last_reviewed_sha", ""),
        pending_action_requests=pending,
        operator_interaction_mode=op_mode,
        timestamp_utc=utc_now_iso(),
    ))

    return ControlPlaneReadModel(
        timestamp=utc_now_iso(),
        branch=git.get("branch", "unknown"),
        head_sha=git.get("head", "unknown"),
        worktree_clean=git.get("clean", True),
        ahead_of_upstream=git.get("ahead", 0),
        resolved_phase=auto_state.phase,
        push_eligible=(push_action == "run_devctl_push"),
        implementation_blocked=impl_blocked,
        top_blocker=blocker["top_blocker"],
        next_action=blocker["next_action"],
        next_command=blocker["next_command"],
        reviewer_mode=reviewer["reviewer_mode"],
        operator_interaction_mode=op_mode,
        reviewer_freshness=reviewer["reviewer_freshness"],
        review_accepted=reviewer["review_accepted"],
        last_reviewed_sha=reviewer.get("last_reviewed_sha", ""),
        attention_status=reviewer["attention_status"],
        attention_summary=reviewer["attention_summary"],
        publisher_running=daemons["publisher_running"],
        supervisor_running=daemons["supervisor_running"],
        codex_conductor_alive=daemons["codex_conductor_alive"],
        claude_conductor_alive=daemons["claude_conductor_alive"],
        pending_action_requests=pending,
        last_guard_ok=quality["last_guard_ok"],
        check_details=quality["check_details"],
    )


# -------------------------------------------------------
# Deserialization from JSON-like mapping
# -------------------------------------------------------

def control_plane_read_model_from_mapping(
    value: object,
) -> ControlPlaneReadModel:
    """Deserialize a ControlPlaneReadModel from a JSON-like mapping."""
    if not isinstance(value, dict):
        return _default_read_model()
    details_raw = value.get("check_details", ())
    details: list[dict[str, str]] = []
    if isinstance(details_raw, (list, tuple)):
        for d in details_raw:
            if isinstance(d, dict):
                details.append({
                    "check": coerce_string(d.get("check")),
                    "status": coerce_string(d.get("status")),
                    "violation": coerce_string(d.get("violation")),
                })
    return ControlPlaneReadModel(
        timestamp=coerce_string(value.get("timestamp")),
        branch=coerce_string(value.get("branch")) or "unknown",
        head_sha=coerce_string(value.get("head_sha")) or "unknown",
        worktree_clean=coerce_bool(value.get("worktree_clean", True)),
        ahead_of_upstream=coerce_int(value.get("ahead_of_upstream")),
        resolved_phase=coerce_string(value.get("resolved_phase")) or AutoModePhase.IDLE.value,
        push_eligible=coerce_bool(value.get("push_eligible", False)),
        implementation_blocked=coerce_bool(value.get("implementation_blocked", False)),
        top_blocker=coerce_string(value.get("top_blocker")) or "none",
        next_action=coerce_string(value.get("next_action")) or "n/a",
        next_command=coerce_string(value.get("next_command")),
        reviewer_mode=coerce_string(value.get("reviewer_mode")) or "single_agent",
        operator_interaction_mode=coerce_string(value.get("operator_interaction_mode")) or "local_terminal",
        reviewer_freshness=coerce_string(value.get("reviewer_freshness")) or "--",
        review_accepted=coerce_bool(value.get("review_accepted", False)),
        last_reviewed_sha=coerce_string(value.get("last_reviewed_sha")),
        attention_status=coerce_string(value.get("attention_status")) or "n/a",
        attention_summary=coerce_string(value.get("attention_summary")) or "n/a",
        publisher_running=coerce_bool(value.get("publisher_running", False)),
        supervisor_running=coerce_bool(value.get("supervisor_running", False)),
        codex_conductor_alive=coerce_bool(value.get("codex_conductor_alive", False)),
        claude_conductor_alive=coerce_bool(value.get("claude_conductor_alive", False)),
        pending_action_requests=coerce_int(value.get("pending_action_requests")),
        last_guard_ok=coerce_bool(value.get("last_guard_ok", True)),
        check_details=tuple(details),
    )


def _default_read_model() -> ControlPlaneReadModel:
    """Return a default read model when deserialization input is invalid."""
    return ControlPlaneReadModel(
        timestamp="",
        branch="unknown",
        head_sha="unknown",
        worktree_clean=True,
        ahead_of_upstream=0,
        resolved_phase=AutoModePhase.IDLE.value,
        push_eligible=False,
        implementation_blocked=False,
        top_blocker="none",
        next_action="n/a",
        next_command="",
        reviewer_mode="single_agent",
        operator_interaction_mode="local_terminal",
        reviewer_freshness="--",
        review_accepted=False,
        last_reviewed_sha="",
        attention_status="n/a",
        attention_summary="n/a",
        publisher_running=False,
        supervisor_running=False,
        codex_conductor_alive=False,
        claude_conductor_alive=False,
        pending_action_requests=0,
        last_guard_ok=True,
        check_details=(),
    )
