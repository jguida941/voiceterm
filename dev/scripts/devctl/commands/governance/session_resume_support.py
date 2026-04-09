"""Support helpers for the session-resume command: data contract, cache, rendering."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...platform.coordination_snapshot_models import (
    CoordinationSnapshot,
    coordination_snapshot_from_mapping,
)
from ...runtime.control_plane_read_model import (
    ControlPlaneReadModel,
    build_control_plane_read_model,
)
from ...runtime.review_state_parser import review_state_from_payload
from ...runtime.review_state_models import (
    ReviewCandidateRecord,
    review_candidate_from_mapping,
)
from ...runtime.control_plane_resolve import (
    load_git_state,
    load_sources,
    read_json_artifact,
)
from ...runtime.value_coercion import coerce_string
from ...runtime.work_intake_models import SessionContinuityState
from ...time_utils import utc_timestamp
from .session_resume_paths import (
    get_review_state_mtime,
    governance_interaction_mode,
    resolve_source_paths,
)

if TYPE_CHECKING:
    from ...runtime.project_governance import ProjectGovernance
    from ...runtime.review_state_models import ReviewState

_BUNDLE_BY_LANE = {
    "docs": "bundle.docs",
    "runtime": "bundle.runtime",
    "tooling": "bundle.tooling",
    "release": "bundle.release",
}


SESSION_CACHE_RELATIVE_DIR = Path("dev/reports/session_cache/latest")
SESSION_CACHE_FILENAME = "cache.json"

# Typed continuity states that invalidate a cached session packet even when
# head/role/mtime all match. `alignment_status` values outside this set
# (for example `aligned`, `scope_aligned`, `instruction_aligned`) leave the
# cache intact. Keep this set in sync with
# ``runtime.work_intake_continuity.build_continuity`` outputs.
_STALE_CONTINUITY_STATUSES: frozenset[str] = frozenset(
    {"needs_review", "plan_only", "review_only", "missing"}
)

@dataclass(frozen=True, slots=True)  # noqa: too-many-instance-attributes
class SessionCachePacket:
    """Compact session state replacing full bootstrap output."""

    schema_version: int = 2
    contract_id: str = "SessionCachePacket"
    generated_at_utc: str = ""
    role: str = "implementer"
    branch: str = ""
    head_sha: str = ""
    advisory_action: str = ""
    advisory_reason: str = ""
    blockers: str = "none"
    interaction_mode: str = "unresolved"
    current_instruction: str = ""
    instruction_revision: str = ""
    ack_state: str = "missing"
    open_findings: str = ""
    last_guard_ok: bool = True
    review_state_mtime: float = 0.0
    last_reviewed_sha: str = ""
    done_summary: str = ""
    next_action: str = ""
    key_rules: tuple[str, ...] = ()
    # v2 fields: typed bootstrap for reviewer
    head_at_push_time: str = ""
    operator_interaction_mode: str = "unresolved"
    resolved_phase: str = "idle"
    next_guard_bundle: str = ""
    next_recommended_command: str = ""
    reviewer_observation_status: str = ""
    review_candidate: ReviewCandidateRecord | None = None
    coordination: CoordinationSnapshot | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["key_rules"] = list(self.key_rules)
        if self.coordination is not None:
            payload["coordination"] = self.coordination.to_dict()
        return payload


def try_cache_hit(
    repo_root: Path,
    *,
    head_sha: str,
    role: str,
    review_state_mtime: float = 0.0,
    continuity: SessionContinuityState | None = None,
) -> SessionCachePacket | None:
    """Return the cached packet when it matches current HEAD, role, and review state.

    Continuity gate: even if the head/mtime/role freshness signals match,
    refuse a cached packet when the typed continuity state shows the plan
    and review state have drifted. Stale continuity means the cached
    resume does not reflect the current target, and downstream callers
    would otherwise act on outdated state. Callers that cannot build a
    ``SessionContinuityState`` (for example legacy tests that only exercise
    the head/role/mtime gate) may omit the parameter and will see the
    existing behavior unchanged.
    """
    cache_path = repo_root / SESSION_CACHE_RELATIVE_DIR / SESSION_CACHE_FILENAME
    if not cache_path.is_file():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    if str(payload.get("head_sha") or "").strip() != head_sha:
        return None
    if str(payload.get("role") or "").strip() != role:
        return None
    cached_mtime = float(payload.get("review_state_mtime") or 0.0)
    if review_state_mtime != cached_mtime:
        return None
    if continuity is not None and continuity.alignment_status in _STALE_CONTINUITY_STATUSES:
        return None
    return packet_from_mapping(payload)


def write_cache(repo_root: Path, packet: SessionCachePacket) -> None:
    """Persist the session-cache packet for future cache hits."""
    cache_dir = repo_root / SESSION_CACHE_RELATIVE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / SESSION_CACHE_FILENAME
    cache_path.write_text(
        json.dumps(packet.to_dict(), indent=2),
        encoding="utf-8",
    )


def build_from_sources(
    repo_root: Path,
    *,
    role: str,
    head_sha: str,
    governance: "ProjectGovernance | None" = None,
    read_model_override: "ControlPlaneReadModel | None" = None,
    sources_override: dict[str, Any] | None = None,
    changed_paths: list[str] | None = None,
    review_state: "ReviewState | None" = None,
) -> SessionCachePacket:
    """Build a fresh packet as a pure projection of ControlPlaneReadModel.

    All gate resolution comes from the read model so every governance
    surface (dashboard, phone, session-resume) renders from one source.
    Session-specific fields (instruction, ack, findings) come from the
    same sources the read model consumed.

    ``read_model_override`` and ``sources_override`` let tests inject
    pre-built data without touching the filesystem. ``review_state`` is
    the optional frozen typed review state the caller already resolved
    for this proof tick; it is forwarded to
    ``build_control_plane_read_model`` so every governance surface
    computes coordination against the same typed review-state snapshot
    instead of triggering an independent bridge-refreshed reload.
    """
    sources = sources_override if sources_override is not None else _load_governed_sources(
        repo_root,
        governance=governance,
        review_state=review_state,
    )
    git = load_git_state(repo_root) if sources_override is None else {
        "branch": "unknown", "head": head_sha, "clean": True, "ahead": 0,
    }

    # Thread governance AND review_state so the read model resolves
    # coordination via the same governed loader path session-resume used
    # to pick ``sources``. Without the governance thread, the read model
    # would reconstruct coordination without it and only ever see the
    # persisted ``coordination`` mapping; without the review_state thread,
    # the read model would trigger an independent
    # ``load_current_review_state_payload`` refresh that can reproject
    # ``bridge.md`` between the three parity calls and desync
    # ``observed_topology`` / ``resync_reasons`` across surfaces. That
    # independent refresh is the residual F1 flake the parity proof tick
    # must close.
    model = read_model_override or build_control_plane_read_model(
        repo_root,
        sources_override=sources,
        git_override=git,
        governance=governance,
        review_state=review_state,
    )

    session = _extract_current_session(sources)
    receipt = sources.get("receipt")

    current_instruction = _str_field(session, "current_instruction")
    instruction_revision = _str_field(session, "current_instruction_revision")
    ack_state = _str_field(session, "implementer_ack_state") or "missing"
    open_findings = _str_field(session, "open_findings")

    rs_mtime = get_review_state_mtime(repo_root, governance=governance)

    # Gate booleans derived from read model, not receipt
    safe_to_continue = model.top_blocker == "none"
    checkpoint_required = model.resolved_phase == "committing"

    key_rules = distill_key_rules(
        safe_to_continue=safe_to_continue,
        checkpoint_required=checkpoint_required,
        ack_current=(ack_state == "current"),
        review_gate_allows_push=model.review_accepted,
        last_guard_ok=model.last_guard_ok,
    )

    blockers = _resolve_blockers(receipt, model.top_blocker)
    last_reviewed_sha = _extract_last_reviewed_sha(sources)
    head_at_push_time = _extract_head_at_push_time(sources)
    review_candidate = _extract_review_candidate(sources)
    guard_bundle = _resolve_guard_bundle(
        repo_root, changed_paths,
        head_sha=head_sha, last_reviewed_sha=last_reviewed_sha,
    )
    next_cmd = model.next_command or model.next_action

    obs_status = ""
    if model.reviewer_observation is not None:
        obs_status = model.reviewer_observation.status
    # One coordination snapshot per tick: reuse the read model's
    # already-resolved answer (built via the governed
    # ``coordination_loader``) so session-resume and dashboard cannot
    # diverge. ``_extract_coordination`` remains callable from tests and
    # legacy code paths that do not go through the read model.
    coordination = model.coordination
    if coordination is None:
        coordination = _extract_coordination(
            sources,
            repo_root=repo_root,
            governance=governance,
        )

    return SessionCachePacket(
        generated_at_utc=utc_timestamp(),
        role=role,
        branch=model.branch,
        head_sha=head_sha,
        advisory_action=model.next_action,
        advisory_reason=model.top_blocker,
        blockers=blockers,
        interaction_mode=model.operator_interaction_mode,
        current_instruction=current_instruction,
        instruction_revision=instruction_revision,
        ack_state=ack_state,
        open_findings=open_findings,
        last_guard_ok=model.last_guard_ok,
        last_reviewed_sha=last_reviewed_sha,
        review_state_mtime=rs_mtime,
        done_summary=next_cmd,
        next_action=next_cmd,
        key_rules=key_rules,
        head_at_push_time=head_at_push_time,
        operator_interaction_mode=model.operator_interaction_mode,
        resolved_phase=model.resolved_phase,
        next_guard_bundle=guard_bundle,
        next_recommended_command=next_cmd,
        reviewer_observation_status=obs_status,
        review_candidate=review_candidate,
        coordination=coordination,
    )


def _extract_current_session(sources: dict[str, Any]) -> dict[str, Any] | None:
    review_state = sources.get("review_state")
    session = _nested_dict(review_state, "current_session")
    if session:
        return session
    compact = sources.get("compact_json")
    return _nested_dict(compact, "current_session")


def _extract_head_at_push_time(sources: dict[str, Any]) -> str:
    """Return head_at_push_time from the typed review_state before compact."""
    for key in ("review_state", "compact_json"):
        bridge = _nested_dict(sources.get(key), "bridge")
        sha = _str_field(bridge, "head_at_push_time")
        if sha:
            return sha
    return ""


def _extract_review_candidate(
    sources: dict[str, Any],
) -> ReviewCandidateRecord | None:
    """Return the current typed review candidate from governed status sources."""
    for key in ("review_state", "compact_json", "full_json"):
        payload = sources.get(key)
        if not isinstance(payload, dict):
            continue
        candidate = review_candidate_from_mapping(payload.get("review_candidate"))
        if candidate is not None:
            return candidate
        review_state = payload.get("review_state")
        if isinstance(review_state, dict):
            candidate = review_candidate_from_mapping(review_state.get("review_candidate"))
            if candidate is not None:
                return candidate
    return None


def _extract_coordination(
    sources: dict[str, Any],
    *,
    repo_root: Path,
    governance: "ProjectGovernance | None",
) -> CoordinationSnapshot | None:
    """Return governed coordination truth via the shared loader.

    Kept as a thin adapter around ``coordination_loader.load_coordination_
    snapshot`` for direct test callers and any legacy code path that still
    calls this helper. The primary code path inside ``build_from_sources``
    reuses ``ControlPlaneReadModel.coordination`` so it and the dashboard
    render from exactly one resolved snapshot. When neither the loader
    nor the sources dict can produce a snapshot, a typed startup-context
    build is used as a last-resort fallback so legacy fixtures without
    governance still resolve something.
    """
    from ...runtime.coordination_loader import load_coordination_snapshot

    fresh = load_coordination_snapshot(
        repo_root=repo_root,
        sources=sources,
        governance=governance,
    )
    if fresh is not None:
        return fresh
    try:
        from ...runtime.startup_context import build_startup_context
    except ImportError:
        return None
    startup_context = build_startup_context(repo_root=repo_root)
    return startup_context.coordination


# Alias kept for backward compatibility with existing callers
_extract_last_reviewed_sha = _extract_head_at_push_time


def _resolve_guard_bundle(
    repo_root: Path,
    changed_paths: list[str] | None,
    *,
    head_sha: str = "",
    last_reviewed_sha: str = "",
) -> str:
    """Classify changed paths into the appropriate guard bundle name.

    Source precedence: (1) explicit ``changed_paths``, (2) live local
    worktree diffs, (3) commit-range fallback only when local diffs are
    empty and ``last_reviewed_sha != head_sha``.  This ensures dirty
    local changes always take priority over older commit-range diffs.

    Returns empty string when classification is unavailable (import fails
    or no paths provided).
    """
    if changed_paths is not None:
        paths = changed_paths
    else:
        paths = _git_changed_paths(repo_root)
        if not paths and last_reviewed_sha and head_sha and last_reviewed_sha != head_sha:
            paths = _git_commit_range_paths(repo_root, last_reviewed_sha, head_sha)
    if not paths:
        return ""
    try:
        from ..check.router_support import classify_lane
        result = classify_lane(paths, repo_root=repo_root)
        lane = str(result.get("lane", "")).strip()
        return _BUNDLE_BY_LANE.get(lane, "")
    except Exception:  # broad-except: allow reason=graceful degradation when router is unavailable fallback=return empty
        return ""


def _git_changed_paths(repo_root: Path) -> list[str]:
    """Return changed file paths from unstaged and staged diffs."""
    try:
        for cmd in (["git", "diff", "--name-only", "HEAD"],
                    ["git", "diff", "--name-only", "--cached"]):
            out = subprocess.run(
                cmd, cwd=str(repo_root), capture_output=True,
                text=True, timeout=5, check=False,
            ).stdout.strip()
            paths = [p for p in out.splitlines() if p.strip()]
            if paths:
                return paths
        return []
    except (OSError, subprocess.TimeoutExpired):
        return []


def _git_commit_range_paths(repo_root: Path, from_sha: str, to_sha: str) -> list[str]:
    """Return file paths changed between two commits.

    Used when a reviewer bootstraps on a clean worktree where HEAD has
    moved past the last reviewed SHA, so local diffs are empty but the
    commit range contains real changes that need a guard bundle.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{from_sha}..{to_sha}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return [p for p in result.stdout.strip().splitlines() if p.strip()]
    except Exception:  # broad-except: allow reason=git may fail on shallow clones or missing refs fallback=return empty
        return []


def compute_blockers(
    *,
    checkpoint_required: bool,
    safe_to_continue: bool,
    authority_ok: bool,
) -> str:
    parts: list[str] = []
    if not authority_ok:
        parts.append("startup_authority")
    if checkpoint_required:
        parts.append("checkpoint_required")
    if not safe_to_continue:
        parts.append("continuation_blocked")
    return ",".join(parts) if parts else "none"


def derive_interaction_mode(
    compact: dict[str, Any] | None,
    *,
    governance: "ProjectGovernance | None" = None,
) -> str:
    """Derive interaction mode, preferring governance BridgeConfig over compact.

    Fails closed: returns 'unresolved' instead of 'local_terminal' when
    no source provides a definitive mode.
    """
    gov_mode = governance_interaction_mode(governance)
    if gov_mode:
        return gov_mode
    if compact is None:
        return "unresolved"
    collab = _nested_dict(compact, "collaboration")
    if not collab:
        return "unresolved"
    reviewer_mode = _str_field(collab, "reviewer_mode")
    if reviewer_mode == "active_dual_agent":
        return "dual_agent"
    if reviewer_mode == "single_agent":
        return "single_agent"
    return "unresolved"


def derive_next_action(receipt: dict[str, Any] | None, blockers: str) -> str:
    if receipt is None:
        return "run startup-context to generate receipt"
    if blockers != "none":
        cmd = _str_field(receipt, "push_next_step_command")
        if cmd:
            return cmd
        return "resolve blockers, then rerun startup-context"
    push_action = _str_field(receipt, "push_action")
    if push_action == "run_devctl_push":
        return "python3 dev/scripts/devctl.py push --execute"
    return "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md"


def distill_key_rules(
    *,
    safe_to_continue: bool,
    checkpoint_required: bool,
    ack_current: bool,
    review_gate_allows_push: bool,
    last_guard_ok: bool,
) -> tuple[str, ...]:
    rules: list[str] = [
        f"safe_to_continue={safe_to_continue}",
        f"checkpoint_required={checkpoint_required}",
        f"ack_current={ack_current}",
        f"review_gate_allows_push={review_gate_allows_push}",
        f"last_guard_ok={last_guard_ok}",
    ]
    return tuple(rules)


# Rendering moved to session_resume_render.py (file-size modularization)
from .session_resume_render import render_bootstrap, render_markdown, render_summary  # noqa: F401


def current_head(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def packet_from_mapping(payload: dict[str, Any]) -> SessionCachePacket:
    return SessionCachePacket(
        schema_version=int(payload.get("schema_version") or 2),
        contract_id=str(payload.get("contract_id") or "SessionCachePacket").strip(),
        generated_at_utc=str(payload.get("generated_at_utc") or "").strip(),
        role=str(payload.get("role") or "implementer").strip(),
        branch=str(payload.get("branch") or "").strip(),
        head_sha=str(payload.get("head_sha") or "").strip(),
        advisory_action=str(payload.get("advisory_action") or "").strip(),
        advisory_reason=str(payload.get("advisory_reason") or "").strip(),
        blockers=str(payload.get("blockers") or "none").strip(),
        interaction_mode=str(payload.get("interaction_mode") or "unresolved").strip(),
        current_instruction=str(payload.get("current_instruction") or "").strip(),
        instruction_revision=str(payload.get("instruction_revision") or "").strip(),
        ack_state=str(payload.get("ack_state") or "missing").strip(),
        open_findings=str(payload.get("open_findings") or "").strip(),
        last_guard_ok=bool(payload.get("last_guard_ok", True)),
        last_reviewed_sha=str(payload.get("last_reviewed_sha") or "").strip(),
        review_state_mtime=float(payload.get("review_state_mtime") or 0.0),
        done_summary=str(payload.get("done_summary") or "").strip(),
        next_action=str(payload.get("next_action") or "").strip(),
        key_rules=tuple(
            str(r).strip() for r in payload.get("key_rules", ()) if str(r).strip()
        ),
        head_at_push_time=str(payload.get("head_at_push_time") or "").strip(),
        operator_interaction_mode=str(
            payload.get("operator_interaction_mode") or "unresolved"
        ).strip(),
        resolved_phase=str(payload.get("resolved_phase") or "idle").strip(),
        next_guard_bundle=str(payload.get("next_guard_bundle") or "").strip(),
        next_recommended_command=str(payload.get("next_recommended_command") or "").strip(),
        reviewer_observation_status=str(payload.get("reviewer_observation_status") or "").strip(),
        review_candidate=review_candidate_from_mapping(payload.get("review_candidate")),
        coordination=coordination_snapshot_from_mapping(payload.get("coordination")),
    )


def _resolve_blockers(
    receipt: dict[str, Any] | None,
    top_blocker: str,
) -> str:
    """Return the effective blocker string, failing closed when no receipt exists.

    Without a receipt, there is no startup authority proof, so the session
    must require a bootstrap pass rather than silently reporting success.
    """
    if receipt is None:
        return "bootstrap_required"
    return top_blocker


def _load_governed_sources(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None" = None,
    review_state: "ReviewState | None" = None,
) -> dict[str, Any]:
    """Load sources using governance-aware path resolution.

    ``load_sources`` routes review_state through
    ``load_current_review_state_payload`` when governance is supplied, so
    dashboard, session-resume, and startup-context all see the same
    bridge-refreshed projection. The compact projection still honors the
    governance ``review_root`` explicitly because ``load_sources`` reads
    it from the repo-pack ``review_status_dir_rel``, which may point at a
    different directory than the governance review root.
    """
    base = load_sources(repo_root, governance=governance)
    if review_state is not None:
        # Keep session-resume's raw source packet aligned with the same frozen
        # typed ReviewState object the caller wants the read model to consume.
        base["review_state"] = review_state.to_dict()
    gov_paths = resolve_source_paths(repo_root, governance=governance)
    compact_path = repo_root / gov_paths["compact"]
    base["compact_json"] = read_json_artifact(compact_path)
    return base


def _nested_dict(data: dict[str, Any] | None, key: str) -> dict[str, Any] | None:
    if data is None:
        return None
    value = data.get(key)
    return dict(value) if isinstance(value, dict) else None


def _str_field(data: dict[str, Any] | None, key: str) -> str:
    if data is None:
        return ""
    return str(data.get(key) or "").strip()
