"""Typed commit-boundary permission decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

STARTUP_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py startup-context --format summary"
)
REVIEW_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)


class _ReviewerGateLike(Protocol):
    review_gate_allows_push: bool
    implementation_blocked: bool
    implementation_block_reason: str


class _PushEnforcementLike(Protocol):
    checkpoint_required: bool
    safe_to_continue_editing: bool


class _GovernanceLike(Protocol):
    push_enforcement: _PushEnforcementLike | None


class _StartupCommitAuthorityLike(Protocol):
    implementation_permission: str
    observed_control_topology: str
    reviewer_gate: _ReviewerGateLike | None
    governance: _GovernanceLike | None


@dataclass(frozen=True, slots=True)
class CommitPermissionDecision:
    """Commit-boundary authority decision separate from implementation evidence."""

    schema_version: int = 1
    contract_id: str = "CommitPermissionDecision"
    commit_permission: str = "allowed"
    blockers: tuple[str, ...] = ()
    authorship_attribution: str = "unknown"
    review_authority: str = "valid"
    topology_state: str = "valid"
    checkpoint_state: str = "satisfied"
    next_command: str = STARTUP_STATUS_COMMAND
    allowed_actions: tuple[str, ...] = ("startup-context.summary",)
    blocked_actions: tuple[str, ...] = ()
    recovery_action: str = ""
    escalation_action: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        payload["allowed_actions"] = list(self.allowed_actions)
        payload["blocked_actions"] = list(self.blocked_actions)
        return payload


def build_commit_permission_decision(
    ctx: _StartupCommitAuthorityLike,
) -> CommitPermissionDecision:
    """Derive the hard commit gate from startup authority truth."""
    blockers: list[str] = []
    permission = _clean_text(ctx.implementation_permission)
    topology = _clean_text(ctx.observed_control_topology)
    if permission in {"blocked", "suspended"}:
        blockers.append(f"implementation_permission_{permission}")

    review_authority = _review_authority(ctx)
    if review_authority != "valid":
        blockers.append(f"review_authority_{review_authority}")

    checkpoint_state = _checkpoint_state(ctx)
    topology_state = _topology_state(topology)
    recovery_action = "refresh_startup_or_review_status" if blockers else ""
    return CommitPermissionDecision(
        commit_permission="blocked" if blockers else "allowed",
        blockers=tuple(blockers),
        review_authority=review_authority,
        topology_state=topology_state,
        checkpoint_state=checkpoint_state,
        next_command=REVIEW_STATUS_COMMAND if blockers else STARTUP_STATUS_COMMAND,
        allowed_actions=(
            ("startup-context.summary", "review-channel.status")
            if blockers
            else ("vcs.stage", "vcs.commit")
        ),
        blocked_actions=(("vcs.stage", "vcs.commit", "git.commit") if blockers else ()),
        recovery_action=recovery_action,
        escalation_action=("operator_resync_required" if blockers else ""),
    )


def build_commit_permission_decision_for_executor(
    executor: object,
) -> tuple[CommitPermissionDecision, str]:
    """Load startup authority through the executor and fail closed on errors."""
    try:
        startup_context = executor.startup_context_fn(repo_root=executor.repo_root)
    except (OSError, ValueError) as exc:
        return _startup_context_unavailable_decision(), str(exc)
    return build_commit_permission_decision(startup_context), ""


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _review_authority(ctx: _StartupCommitAuthorityLike) -> str:
    gate = ctx.reviewer_gate
    if gate is None:
        return "missing"
    if bool(gate.review_gate_allows_push):
        return "valid"
    if bool(gate.implementation_blocked):
        reason = _clean_text(gate.implementation_block_reason)
        if reason == "checkpoint_required":
            return "valid"
        return "stale" if reason else "missing"
    return "valid"


def _checkpoint_state(ctx: _StartupCommitAuthorityLike) -> str:
    governance = ctx.governance
    push = governance.push_enforcement if governance is not None else None
    if push is None:
        return "satisfied"
    if bool(push.checkpoint_required):
        return "required"
    if not bool(push.safe_to_continue_editing):
        return "required"
    return "satisfied"


def _topology_state(topology: str) -> str:
    if topology in {"single_implementer_single_reviewer", "single_agent"}:
        return "valid"
    if topology == "no_live_agents":
        return "absent"
    if topology:
        return "drifted"
    return "unknown"


def _startup_context_unavailable_decision() -> CommitPermissionDecision:
    return CommitPermissionDecision(
        commit_permission="blocked",
        blockers=("startup_context_unavailable",),
        review_authority="missing",
        topology_state="unknown",
        checkpoint_state="unknown",
        blocked_actions=("vcs.stage", "vcs.commit", "git.commit"),
        recovery_action="refresh_startup_or_review_status",
        escalation_action="operator_resync_required",
    )


__all__ = [
    "CommitPermissionDecision",
    "build_commit_permission_decision",
    "build_commit_permission_decision_for_executor",
]
