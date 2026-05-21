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
from typing import TYPE_CHECKING, Any

from ..platform.coordination_snapshot_models import (
    CoordinationSnapshot,
    coordination_snapshot_from_mapping,
)
from .auto_mode import AutoModePhase
from .advisory_next_action_role_filter import project_next_command_for_role
from .control_plane_sources import load_sources
from .control_plane_loop_wake import ControlPlaneLoopWakeState
from .control_plane_read_model_support import (
    ControlPlaneContextInputs,
    ControlPlaneReadModelOptions,
    _extract_coordination,
    resolve_control_plane_context,
)
from .control_plane_read_model_defaults import default_read_model_kwargs
from .control_plane_resolve import (
    load_git_state,
    utc_now_iso,
)
from .control_plane_reviewer_observation_decode import observation_from_mapping
from .control_plane_worktree_projection import (
    control_plane_worktree_clean,
    managed_projection_dirty_paths,
)
from .reviewer_runtime_models import (
    RemoteControlAttachmentState,
    remote_control_attachment_from_mapping,
)
from .session_posture import SessionPosture, session_posture_from_mapping
from .surface_snapshot import build_surface_zref
from .surface_provenance import (
    SurfaceProvenance,
    attach_surface_provenance,
    surface_provenance_from_mapping,
)
from .value_coercion import coerce_bool, coerce_int, coerce_string, coerce_string_items

if TYPE_CHECKING:
    from .reviewer_observation import ReviewerObservation


CONTROL_PLANE_READ_MODEL_CONTRACT_ID = "ControlPlaneReadModel"
CONTROL_PLANE_READ_MODEL_SCHEMA_VERSION = 1

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
    managed_projection_drift: bool = False
    managed_projection_dirty_paths: tuple[str, ...] = ()
    loop_wake_mode: str = "unknown"
    loop_wake_interval_seconds: int = 0
    loop_driver_agent: str = ""
    loop_autonomy_ok: bool = False
    loop_gap_summary: str = ""

    # Typed reviewer observation (derived from bridge state)
    reviewer_observation: ReviewerObservation | None = None
    remote_control_attachment: RemoteControlAttachmentState | None = None
    session_posture: SessionPosture | None = None
    coordination: CoordinationSnapshot | None = None
    snapshot_id: str = ""
    zref: str = ""
    provenance: SurfaceProvenance | None = None
    # Phase 0.6.A v4.17/v4.18/v4.22 BlockerSnapshot typed action fields
    # (rev_pkt_4672/4674/4676/4683): preserve the blocker repair metadata so
    # downstream agent_loop_context_builder, develop parser/model, and
    # final-response gate consumers can refuse to auto-execute
    # repair_command_runnable=False commands and surface owner/target/reason.
    blocker_owner: str = ""
    blocker_target: str = ""
    blocker_reason: str = ""
    repair_command: str = ""
    stop_anchor: str = ""
    repair_command_runnable: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("provenance", None)
        if self.coordination is not None:
            payload["coordination"] = self.coordination.to_dict()
        result = attach_surface_provenance(payload, provenance=self.provenance)
        result.setdefault("snapshot_id", self.snapshot_id)
        result.setdefault("zref", self.zref)
        return result


def build_control_plane_read_model(
    repo_root: Path,
    *,
    sources_override: dict[str, Any] | None = None,
    git_override: dict[str, Any] | None = None,
    options: ControlPlaneReadModelOptions | None = None,
) -> ControlPlaneReadModel:
    """Load all artifacts ONCE, resolve ALL gates, return frozen model.

    ``sources_override`` and ``git_override`` allow tests to inject
    pre-built data without touching the filesystem or git. When options
    include ``governance``, ``load_sources`` uses it so every
    surface that resolves governance up front (for example
    session-resume) shares the same bridge-refreshed review-state.
    ``options.review_state`` is the optional frozen typed review state the
    caller already resolved for this proof tick; it is forwarded unchanged
    to ``_extract_coordination`` so the coordination reducer uses the exact
    same typed state as ``build_startup_context`` instead of triggering an
    independent bridge-refreshed reload.
    """
    resolved_options = options or ControlPlaneReadModelOptions()
    governance = resolved_options.governance
    review_state = resolved_options.review_state
    sources = (
        dict(sources_override)
        if sources_override is not None
        else load_sources(
            repo_root,
            governance=governance,
            review_status_dir=resolved_options.review_status_dir,
            review_state_override=review_state,
        )
    )
    if review_state is not None:
        # Belt-and-suspenders: when ``sources_override`` is in play (typically
        # from session-resume preloading the dict via ``_load_governed_sources``),
        # the override path inside ``load_sources`` is bypassed. Re-overlay the
        # typed snapshot so the read model still observes the caller's frozen
        # review state instead of whatever the override dict was constructed
        # with. When ``load_sources`` was called above, the override was already
        # applied there and this assignment is a no-op.
        sources["review_state"] = review_state.to_dict()
    git = git_override if git_override is not None else load_git_state(repo_root)

    context = resolve_control_plane_context(
        repo_root=repo_root,
        inputs=ControlPlaneContextInputs(
            sources=sources,
            git=git,
            governance=governance,
            review_state=review_state,
            review_state_payload=sources.get("review_state"),
            receipt=sources.get("receipt"),
            push_report=sources.get("push_report"),
            compact=sources.get("compact_json"),
            full_json=sources.get("full_json"),
        ),
        extract_coordination_fn=_extract_coordination,
    )
    review_state_payload = (
        review_state.to_dict()
        if review_state is not None
        else sources.get("review_state")
    )
    if not isinstance(review_state_payload, dict):
        review_state_payload = {}

    worktree_clean = control_plane_worktree_clean(
        git=git,
        governance=governance,
    )
    projection_paths = managed_projection_dirty_paths(governance)

    return ControlPlaneReadModel(
        timestamp=utc_now_iso(),
        branch=git.get("branch", "unknown"),
        head_sha=git.get("head", "unknown"),
        snapshot_id=context.snapshot_id,
        zref=build_surface_zref(
            snapshot_id=context.snapshot_id,
            head_sha=git.get("head", "unknown"),
        ),
        worktree_clean=worktree_clean,
        managed_projection_drift=bool(projection_paths),
        managed_projection_dirty_paths=projection_paths,
        ahead_of_upstream=git.get("ahead", 0),
        resolved_phase=context.auto_state.phase,
        push_eligible=(context.blocker["next_action"] == "run_devctl_push"),
        implementation_blocked=context.implementation_blocked,
        top_blocker=context.blocker["top_blocker"],
        next_action=context.blocker["next_action"],
        next_command=project_next_command_for_role(
            role=resolved_options.caller_role,
            command=context.blocker["next_command"],
        ),
        blocker_owner=str(context.blocker.get("blocker_owner") or ""),
        blocker_target=str(context.blocker.get("blocker_target") or ""),
        blocker_reason=str(context.blocker.get("blocker_reason") or ""),
        repair_command=str(context.blocker.get("repair_command") or ""),
        stop_anchor=str(context.blocker.get("stop_anchor") or ""),
        repair_command_runnable=bool(
            context.blocker.get("repair_command_runnable", True)
        ),
        reviewer_mode=context.reviewer["reviewer_mode"],
        operator_interaction_mode=context.operator_interaction_mode,
        reviewer_freshness=context.reviewer["reviewer_freshness"],
        review_accepted=context.reviewer["review_accepted"],
        last_reviewed_sha=context.reviewer.get("last_reviewed_sha", ""),
        attention_status=context.reviewer["attention_status"],
        attention_summary=context.reviewer["attention_summary"],
        reviewer_observation=context.reviewer_observation,
        publisher_running=context.daemons["publisher_running"],
        supervisor_running=context.daemons["supervisor_running"],
        codex_conductor_alive=context.daemons["codex_conductor_alive"],
        claude_conductor_alive=context.daemons["claude_conductor_alive"],
        pending_action_requests=context.pending,
        last_guard_ok=context.quality["last_guard_ok"],
        check_details=context.quality["check_details"],
        loop_wake_mode=context.loop_wake.loop_wake_mode,
        loop_wake_interval_seconds=context.loop_wake.loop_wake_interval_seconds,
        loop_driver_agent=context.loop_wake.loop_driver_agent,
        loop_autonomy_ok=context.loop_wake.loop_autonomy_ok,
        loop_gap_summary=context.loop_wake.loop_gap_summary,
        remote_control_attachment=context.remote_control_attachment,
        session_posture=context.session_posture,
        coordination=context.coordination,
        provenance=surface_provenance_from_mapping(review_state_payload),
    )

def control_plane_read_model_from_mapping(
    value: object,
) -> ControlPlaneReadModel:
    """Deserialize a ControlPlaneReadModel from a JSON-like mapping."""
    if not isinstance(value, dict):
        return _default_read_model()
    loop_wake = ControlPlaneLoopWakeState.from_mapping(value) or ControlPlaneLoopWakeState()
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
        snapshot_id=coerce_string(value.get("snapshot_id")),
        zref=coerce_string(value.get("zref")),
        worktree_clean=coerce_bool(value.get("worktree_clean", True)),
        managed_projection_drift=coerce_bool(
            value.get("managed_projection_drift", False)
        ),
        managed_projection_dirty_paths=coerce_string_items(
            value.get("managed_projection_dirty_paths")
        ),
        ahead_of_upstream=coerce_int(value.get("ahead_of_upstream")),
        resolved_phase=coerce_string(value.get("resolved_phase")) or AutoModePhase.IDLE.value,
        push_eligible=coerce_bool(value.get("push_eligible", False)),
        implementation_blocked=coerce_bool(value.get("implementation_blocked", False)),
        top_blocker=coerce_string(value.get("top_blocker")) or "none",
        next_action=coerce_string(value.get("next_action")) or "n/a",
        next_command=coerce_string(value.get("next_command")),
        blocker_owner=coerce_string(value.get("blocker_owner")),
        blocker_target=coerce_string(value.get("blocker_target")),
        blocker_reason=coerce_string(value.get("blocker_reason")),
        repair_command=coerce_string(value.get("repair_command")),
        stop_anchor=coerce_string(value.get("stop_anchor")),
        repair_command_runnable=coerce_bool(
            value.get("repair_command_runnable", True)
        ),
        reviewer_mode=coerce_string(value.get("reviewer_mode")) or "single_agent",
        operator_interaction_mode=coerce_string(value.get("operator_interaction_mode")) or "unresolved",
        reviewer_freshness=coerce_string(value.get("reviewer_freshness")) or "--",
        review_accepted=coerce_bool(value.get("review_accepted", False)),
        last_reviewed_sha=coerce_string(value.get("last_reviewed_sha")),
        attention_status=coerce_string(value.get("attention_status")) or "n/a",
        attention_summary=coerce_string(value.get("attention_summary")) or "n/a",
        reviewer_observation=observation_from_mapping(
            value.get("reviewer_observation")
        ),
        remote_control_attachment=remote_control_attachment_from_mapping(
            value.get("remote_control_attachment")
        ),
        session_posture=session_posture_from_mapping(value.get("session_posture")),
        publisher_running=coerce_bool(value.get("publisher_running", False)),
        supervisor_running=coerce_bool(value.get("supervisor_running", False)),
        codex_conductor_alive=coerce_bool(value.get("codex_conductor_alive", False)),
        claude_conductor_alive=coerce_bool(value.get("claude_conductor_alive", False)),
        pending_action_requests=coerce_int(value.get("pending_action_requests")),
        last_guard_ok=coerce_bool(value.get("last_guard_ok", True)),
        check_details=tuple(details),
        loop_wake_mode=loop_wake.loop_wake_mode,
        loop_wake_interval_seconds=loop_wake.loop_wake_interval_seconds,
        loop_driver_agent=loop_wake.loop_driver_agent,
        loop_autonomy_ok=loop_wake.loop_autonomy_ok,
        loop_gap_summary=loop_wake.loop_gap_summary,
        coordination=coordination_snapshot_from_mapping(value.get("coordination")),
        provenance=surface_provenance_from_mapping(value),
    )

def _default_read_model() -> ControlPlaneReadModel:
    """Return a default read model when deserialization input is invalid."""
    return ControlPlaneReadModel(**default_read_model_kwargs())
