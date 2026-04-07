"""ReviewSnapshot builder — orchestrates typed sources into one projection.

Reads every governance/quality typed builder as a Python call (no shelling)
and aggregates them into one ``ReviewSnapshot``. Section builders live in
``review_snapshot_sections`` / ``review_snapshot_delta`` /
``review_snapshot_quality``; this file owns only orchestration, identity,
governance-state, stamp attachment, and the source loaders.

Missing optional sources fall back to empty defaults so the builder runs on
freshly-cloned adopter repos where no governance artifacts exist yet.
"""

from __future__ import annotations

import datetime as _dt
from collections.abc import Mapping
from pathlib import Path

from ..config import REPO_ROOT
from .review_snapshot_git import (
    commits_between,
    current_branch,
    head_author_and_time,
    head_sha,
    head_subject,
    tree_hash,
)
from .review_snapshot_models import (
    ReviewSnapshot,
    SnapshotDelta,
    SnapshotGovernanceState,
    SnapshotIdentity,
    SnapshotQualitySignals,
)
from .review_snapshot_sections import (
    build_architecture,
    build_delta,
    build_known_gaps,
    build_quality,
    build_reasoning,
    build_reviewer_hints,
)
from .surface_snapshot import build_surface_snapshot_id


def build_review_snapshot(
    *,
    repo_root: Path = REPO_ROOT,
    previous_head_sha: str = "",
    startup_payload: Mapping[str, object] | None = None,
    governance_payload: Mapping[str, object] | None = None,
    probe_payload: Mapping[str, object] | None = None,
    context_graph_payload: Mapping[str, object] | None = None,
    commit_limit: int = 25,
) -> ReviewSnapshot:
    """Return a typed ReviewSnapshot projecting current repo governance state."""
    startup = (
        startup_payload
        if startup_payload is not None
        else _safe_startup_context(repo_root)
    )
    governance_contract = _safe_project_governance(repo_root)
    governance_summary = (
        governance_payload
        if governance_payload is not None
        else _safe_governance_report(repo_root, governance_contract)
    )
    probe_summary = (
        probe_payload if probe_payload is not None else _safe_probe_report()
    )
    graph_bootstrap = (
        context_graph_payload
        if context_graph_payload is not None
        else _safe_context_graph_bootstrap()
    )

    identity = _build_identity(
        repo_root=repo_root,
        startup=startup,
        previous_head_sha=previous_head_sha,
    )
    governance_state = _build_governance_state(startup=startup)
    raw_commits = commits_between(
        repo_root,
        from_sha=previous_head_sha or identity.previous_snapshot_head_sha,
        to_sha=identity.head_sha or "HEAD",
        limit=commit_limit,
    )
    delta = build_delta(
        repo_root=repo_root,
        raw_commits=raw_commits,
        identity=identity,
        previous_head_sha=previous_head_sha or identity.previous_snapshot_head_sha,
    )
    quality = build_quality(
        governance_summary=governance_summary,
        probe_summary=probe_summary,
    )
    architecture = build_architecture(
        startup=startup,
        graph_bootstrap=graph_bootstrap,
        governance_contract=governance_contract,
    )
    reviewer_hints = build_reviewer_hints(delta=delta)
    reasoning = build_reasoning(repo_root=repo_root, raw_commits=raw_commits)
    known_gaps = build_known_gaps(
        startup=startup,
        governance_summary=governance_summary,
        quality=quality,
    )
    identity = _attach_generation_stamp(identity, governance_state, delta, quality)
    return ReviewSnapshot(
        identity=identity,
        governance_state=governance_state,
        delta=delta,
        quality=quality,
        architecture=architecture,
        reviewer_hints=reviewer_hints,
        reasoning=reasoning,
        known_gaps=known_gaps,
    )


# ---------------------------------------------------------------------------
# Identity + governance-state section builders (kept here — short + core)
# ---------------------------------------------------------------------------


def _build_identity(
    *,
    repo_root: Path,
    startup: Mapping[str, object],
    previous_head_sha: str,
) -> SnapshotIdentity:
    full_sha, short_sha = head_sha(repo_root)
    subject = head_subject(repo_root, "HEAD")
    author, timestamp = head_author_and_time(repo_root, "HEAD")
    tree = tree_hash(repo_root, "HEAD")
    branch = current_branch(repo_root)
    governance = _as_mapping(startup.get("governance"))
    repo_identity = _as_mapping(governance.get("repo_identity"))
    repo_pack = _as_mapping(governance.get("repo_pack"))
    generated_at = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return SnapshotIdentity(
        generation_stamp="",  # filled in _attach_generation_stamp
        generated_at_utc=generated_at,
        repo_name=str(repo_identity.get("repo_name") or ""),
        repo_description=str(repo_pack.get("description") or ""),
        product_thesis=str(startup.get("product_thesis") or ""),
        remote_url=str(repo_identity.get("remote_url") or ""),
        branch=branch,
        default_branch=str(repo_identity.get("default_branch") or ""),
        head_sha=full_sha,
        head_sha_short=short_sha,
        head_subject=subject,
        head_author=author,
        head_timestamp_utc=timestamp,
        tree_hash=tree,
        previous_snapshot_head_sha=previous_head_sha,
        commits_since_previous=0,  # filled in _build_delta via delta.commit_count
    )


def _build_governance_state(
    *, startup: Mapping[str, object]
) -> SnapshotGovernanceState:
    push = _as_mapping(startup.get("push_decision"))
    gate = _as_mapping(startup.get("reviewer_gate"))
    pipeline = _as_mapping(startup.get("remote_commit_pipeline"))
    work_intake = _as_mapping(startup.get("work_intake"))
    continuity = _as_mapping(work_intake.get("continuity"))
    backlog = _as_mapping(push.get("publication_backlog"))
    push_enforcement = _as_mapping(
        _as_mapping(startup.get("governance")).get("push_enforcement")
    )
    return SnapshotGovernanceState(
        push_action=str(push.get("action") or ""),
        push_reason=str(push.get("reason") or ""),
        push_eligible_now=bool(push.get("push_eligible_now")),
        next_step_command=str(push.get("next_step_command") or ""),
        publication_backlog_state=str(backlog.get("backlog_state") or ""),
        publication_guidance=str(push.get("publication_guidance") or ""),
        interaction_mode=str(gate.get("operator_interaction_mode") or "unresolved"),
        reviewer_mode=str(gate.get("effective_reviewer_mode") or ""),
        reviewer_freshness=str(gate.get("required_checks_status") or "unknown"),
        reviewer_publish_clear=bool(gate.get("review_gate_allows_push")),
        reviewer_implementation_blocked=bool(gate.get("implementation_blocked")),
        reviewer_block_reason=str(gate.get("implementation_block_reason") or ""),
        pipeline_state=str(pipeline.get("state") or ""),
        pipeline_blocked_reason=str(pipeline.get("blocked_reason") or ""),
        pipeline_approval_state=str(pipeline.get("approval_state") or ""),
        advisory_action=str(startup.get("advisory_action") or ""),
        advisory_reason=str(startup.get("advisory_reason") or ""),
        active_mp_scope=_coerce_str_tuple(continuity.get("source_scope")),
        active_plan_title=str(continuity.get("source_plan_title") or ""),
        active_plan_path=str(continuity.get("source_plan_path") or ""),
        worktree_clean=bool(push.get("worktree_clean")),
        checkpoint_required=bool(push_enforcement.get("checkpoint_required")),
    )


def _attach_generation_stamp(
    identity: SnapshotIdentity,
    governance_state: SnapshotGovernanceState,
    delta: SnapshotDelta,
    quality: SnapshotQualitySignals,
) -> SnapshotIdentity:
    stamp_inputs = {
        "head_sha": identity.head_sha,
        "tree_hash": identity.tree_hash,
        "push_action": governance_state.push_action,
        "reviewer_mode": governance_state.reviewer_mode,
        "pipeline_state": governance_state.pipeline_state,
        "commit_count": delta.commit_count,
        "governance_open": quality.governance_open_findings,
    }
    stamp = build_surface_snapshot_id(
        reviewer_runtime=stamp_inputs,
        commit_pipeline={"state": governance_state.pipeline_state},
        push_decision={"action": governance_state.push_action},
    )
    return SnapshotIdentity(
        generation_stamp=stamp,
        generated_at_utc=identity.generated_at_utc,
        repo_name=identity.repo_name,
        repo_description=identity.repo_description,
        product_thesis=identity.product_thesis,
        remote_url=identity.remote_url,
        branch=identity.branch,
        default_branch=identity.default_branch,
        head_sha=identity.head_sha,
        head_sha_short=identity.head_sha_short,
        head_subject=identity.head_subject,
        head_author=identity.head_author,
        head_timestamp_utc=identity.head_timestamp_utc,
        tree_hash=identity.tree_hash,
        previous_snapshot_head_sha=identity.previous_snapshot_head_sha,
        commits_since_previous=delta.commit_count,
    )


# ---------------------------------------------------------------------------
# Source loaders — call existing typed builders or return ``{}`` on failure
# ---------------------------------------------------------------------------


def _safe_startup_context(repo_root: Path) -> Mapping[str, object]:
    try:
        from .startup_context import build_startup_context

        ctx = build_startup_context()
        return ctx.to_dict()
    except Exception:
        return {}


def _safe_project_governance(repo_root: Path) -> object | None:
    """Load ProjectGovernance via repo-pack scan; None on fresh repos."""
    try:
        from .governance_scan import scan_repo_governance_safely

        return scan_repo_governance_safely(repo_root)
    except Exception:
        return None


def _safe_governance_report(
    repo_root: Path,
    governance: object | None,
) -> Mapping[str, object]:
    """Load the governance-review report using repo-pack-configured paths."""
    try:
        from ..governance_review_log import build_governance_review_report
    except Exception:
        return {}
    log_path = _resolve_governance_log_path(repo_root, governance)
    if not log_path.is_file():
        return {}
    try:
        return build_governance_review_report(
            log_path=log_path, max_rows=2000, recent_limit=15
        )
    except Exception:
        return {}


def _resolve_governance_log_path(
    repo_root: Path, governance: object | None
) -> Path:
    """Resolve the JSONL governance-review log via ProjectGovernance.

    Falls back to the canonical default only when the repo-pack config has
    no governance_log_root set, so adopter repos can point this at their
    own artifact layout.
    """
    relative = ""
    if governance is not None:
        artifact_roots = getattr(governance, "artifact_roots", None)
        if artifact_roots is not None:
            relative = str(
                getattr(artifact_roots, "governance_log_root", "") or ""
            ).strip()
    if not relative:
        relative = "dev/reports/governance"
    return repo_root / relative / "finding_reviews.jsonl"


def _safe_probe_report() -> Mapping[str, object]:
    try:
        from ..review_probe_report import build_probe_report

        return build_probe_report()
    except Exception:
        return {}


def _safe_context_graph_bootstrap() -> Mapping[str, object]:
    try:
        from ..context_graph.builder import build_context_graph
        from ..context_graph.query import build_bootstrap_context

        graph = build_context_graph()
        return build_bootstrap_context(graph)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Micro utilities
# ---------------------------------------------------------------------------


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _coerce_str_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if item)
    return ()


__all__ = ["build_review_snapshot"]
