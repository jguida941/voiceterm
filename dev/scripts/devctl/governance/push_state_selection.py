"""Push-report selection helpers for governed push-state detection."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace

from .push_state_report import (
    current_target_remote as _current_target_remote,
    latest_push_report_state as _latest_push_report_state,
)

_CURRENT_HEAD_LATEST_REPORT_REASONS = frozenset({
    "push_preflight_running",
    "push_pending",
    "post_push_bundle_pending",
})


@dataclass(frozen=True, slots=True)
class ProjectedPushReport:
    branch: str = ""
    remote: str = ""
    head_commit: str = ""
    status: str = ""
    reason: str = ""
    published_remote: bool = False
    post_push_green: bool = False
    publication_mode: str = ""
    governed_push_verified: bool = False
    operator_bypass_evidence_required: bool = False
    approved_target_identity: str = ""
    approved_worktree_identity: str = ""
    matches_current_branch: bool = False
    matches_current_head: bool = False
    matches_current_approved_target: bool = False
    matches_current_worktree: bool = False


@dataclass(frozen=True, slots=True)
class PushProjectionInputs:
    upstream_ref: str
    default_remote: str
    current_branch: str
    current_head_commit: str
    current_approved_target_identity: str
    current_worktree_identity: str


def project_push_report(
    report: dict[str, object],
    *,
    inputs: PushProjectionInputs,
) -> ProjectedPushReport:
    """Return the typed branch/head/approved-target projection for one report."""
    push_stages = report.get("push_stages")
    if not isinstance(push_stages, dict):
        push_stages = {}
    (
        branch,
        remote,
        head_commit,
        approved_target_identity,
        approved_worktree_identity,
        matches_branch,
        matches_head,
        matches_target,
        matches_worktree,
    ) = _latest_push_report_state(
        report=report,
        current_branch=inputs.current_branch,
        current_head_commit=inputs.current_head_commit,
        current_approved_target_identity=inputs.current_approved_target_identity,
        current_worktree_identity=inputs.current_worktree_identity,
    )
    return ProjectedPushReport(
        branch=branch,
        remote=remote,
        head_commit=head_commit,
        status=str(report.get("status") or "").strip(),
        reason=str(report.get("reason") or "").strip(),
        published_remote=bool(push_stages.get("published_remote")),
        post_push_green=bool(push_stages.get("post_push_green")),
        publication_mode=_publication_mode(report, push_stages=push_stages),
        governed_push_verified=_governed_push_verified(
            report,
            push_stages=push_stages,
        ),
        operator_bypass_evidence_required=bool(
            report.get("operator_bypass_evidence_required")
        ),
        approved_target_identity=approved_target_identity,
        approved_worktree_identity=approved_worktree_identity,
        matches_current_branch=matches_branch,
        matches_current_head=matches_head,
        matches_current_approved_target=matches_target,
        matches_current_worktree=matches_worktree,
    )


def load_push_report_projections(
    *,
    receipt: dict[str, object] | None,
    latest: dict[str, object],
    inputs: PushProjectionInputs,
) -> tuple[ProjectedPushReport, ProjectedPushReport, str, bool]:
    """Return raw latest, selected current-target report, source, and publish truth."""
    latest_projection = project_push_report(
        latest,
        inputs=inputs,
    )
    selected_report, selected_source = resolve_selected_push_report(
        receipt=receipt,
        latest=latest,
        inputs=inputs,
    )
    selected_projection = project_push_report(
        selected_report,
        inputs=inputs,
    )
    if selected_source == "receipt_history" and selected_projection.published_remote:
        selected_projection = replace(
            selected_projection,
            publication_mode=(
                selected_projection.publication_mode or "governed_push"
            ),
            governed_push_verified=True,
        )
    recorded_publication = records_current_target_publication(
        report=selected_projection,
        current_target_remote=_current_target_remote(
            upstream_ref=inputs.upstream_ref,
            default_remote=inputs.default_remote,
        ),
    )
    return latest_projection, selected_projection, selected_source, recorded_publication


def resolve_selected_push_report(
    *,
    receipt: dict[str, object] | None,
    latest: dict[str, object],
    inputs: PushProjectionInputs,
) -> tuple[dict[str, object], str]:
    """Prefer a current-head in-flight latest report over stale final receipts."""
    if latest_report_is_current_head_inflight(
        latest,
        inputs=inputs,
    ):
        return latest, "latest_artifact"
    if receipt:
        return receipt, "receipt_history"
    return latest, "latest_artifact"


def latest_report_is_current_head_inflight(
    report: dict[str, object],
    *,
    inputs: PushProjectionInputs,
) -> bool:
    """Return whether the raw latest artifact represents the active push run."""
    if not report:
        return False
    projection = project_push_report(
        report,
        inputs=inputs,
    )
    if projection.reason not in _CURRENT_HEAD_LATEST_REPORT_REASONS:
        return False
    return bool(
        projection.matches_current_branch
        and projection.matches_current_head
        and projection.matches_current_approved_target
        and projection.matches_current_worktree
    )


def records_current_target_publication(
    *,
    report: ProjectedPushReport,
    current_target_remote: str,
) -> bool:
    """Return whether one selected report proves current-target publication."""
    return bool(
        report.published_remote
        and report.governed_push_verified
        and report.publication_mode not in {"raw_no_verify", "ungoverned_remote_advance"}
        and report.matches_current_branch
        and report.matches_current_head
        and report.matches_current_approved_target
        and report.matches_current_worktree
        and (not report.remote or report.remote == current_target_remote)
    )


def _governed_push_verified(
    report: dict[str, object],
    *,
    push_stages: dict[str, object],
) -> bool:
    explicit = report.get("governed_push_verified")
    if explicit is not None:
        return bool(explicit)
    if _publication_mode(report, push_stages=push_stages) in {
        "raw_no_verify",
        "ungoverned_remote_advance",
    }:
        return False
    if str(report.get("command") or "") != "push":
        return False
    if not bool(push_stages.get("published_remote")):
        return False
    if str(report.get("reason") or "") == "branch_already_pushed":
        return True
    push_step = report.get("push_step")
    if not isinstance(push_step, dict):
        return False
    try:
        return int(push_step.get("returncode")) == 0
    except (TypeError, ValueError):
        return False


def _publication_mode(
    report: dict[str, object],
    *,
    push_stages: dict[str, object],
) -> str:
    explicit = str(report.get("publication_mode") or "").strip()
    if explicit:
        return explicit
    if bool(push_stages.get("published_remote")):
        return "legacy_push_report"
    if bool(push_stages.get("validation_ready")):
        return "validation_only"
    return "not_published"
