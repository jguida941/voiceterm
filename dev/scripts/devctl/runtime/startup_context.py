"""Typed startup-context surface for AI agent sessions.

Combines ProjectGovernance, push/checkpoint state, and reviewer/ready-gate
inputs into one machine-readable packet that an agent inspects at session
start to decide: continue editing, checkpoint first, or push now.

This packet is the typed startup receipt. Read-only helpers may render it
without enforcing the decision, but repo-owned startup launchers should treat
checkpoint-required states as fail-closed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .governance_scan import scan_repo_governance_safely
from .project_governance import ProjectGovernance
from .review_state_semantics import is_pending_implementer_state
from .review_state_locator import load_current_review_state
from .startup_governance_projection import startup_governance_dict
from .startup_push_decision import (
    PushDecisionState,
    derive_push_decision as _derive_push_decision,
)
from .startup_signals import load_startup_quality_signals
from .work_intake import WorkIntakePacket, build_work_intake_packet


@dataclass(frozen=True, slots=True)
class ReviewerGateState:
    """Current reviewer/ready-gate inputs for safe checkpoint/push decisions."""

    bridge_active: bool = False
    reviewer_mode: str = "single_agent"
    review_accepted: bool = False
    required_checks_status: str = "unknown"
    checkpoint_permitted: bool = True
    review_gate_allows_push: bool = False
    implementation_blocked: bool = False
    implementation_block_reason: str = ""


@dataclass(frozen=True, slots=True)
class StartupContext:
    """One typed packet for AI agent session startup.

    Carries everything an agent needs to understand the repo's governance
    posture, current worktree state, and what actions are safe — without
    re-reading prose docs.
    """

    schema_version: int = 1
    contract_id: str = "StartupContext"
    governance: ProjectGovernance | None = None
    reviewer_gate: ReviewerGateState = field(default_factory=ReviewerGateState)
    push_decision: PushDecisionState = field(default_factory=PushDecisionState)
    advisory_action: str = "continue_editing"
    advisory_reason: str = ""
    work_intake: WorkIntakePacket | None = None
    quality_signals: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        d["schema_version"] = self.schema_version
        d["contract_id"] = self.contract_id
        d["advisory_action"] = self.advisory_action
        d["advisory_reason"] = self.advisory_reason
        d["reviewer_gate"] = asdict(self.reviewer_gate)
        d["push_decision"] = asdict(self.push_decision)
        d["quality_signals"] = dict(self.quality_signals)
        if self.governance is not None:
            d["governance"] = _startup_governance_dict(self.governance)
        if self.work_intake is not None:
            d["work_intake"] = self.work_intake.to_dict()
        return d


def _detect_reviewer_gate(
    repo_root: Path,
    governance: ProjectGovernance | None = None,
) -> ReviewerGateState:
    """Detect reviewer gate state from typed review-state only."""
    resolved_governance = governance or scan_repo_governance_safely(repo_root)
    typed_gate = _detect_reviewer_gate_from_typed_state(
        repo_root,
        governance=resolved_governance,
    )
    if typed_gate is not None:
        return typed_gate
    return _detect_reviewer_gate_without_typed_state(resolved_governance)


def _detect_reviewer_gate_from_typed_state(
    repo_root: Path,
    *,
    governance: ProjectGovernance | None = None,
) -> ReviewerGateState | None:
    """Read reviewer gate from typed review_state.json when available."""
    state = load_current_review_state(repo_root, governance=governance)
    if state is None:
        return None
    try:
        from ..review_channel.peer_liveness import reviewer_mode_is_active

        mode = state.bridge.reviewer_mode
        active = reviewer_mode_is_active(mode)
        if not active:
            return ReviewerGateState(
                bridge_active=False,
                reviewer_mode=mode,
                review_accepted=True,
                required_checks_status="unknown",
                checkpoint_permitted=True,
                review_gate_allows_push=True,
            )

        implementation_blocked, implementation_block_reason = (
            _reviewer_loop_block_state(
                reviewer_mode=mode,
                claude_ack_current=state.bridge.claude_ack_current,
                attention_status=(
                    str(state.attention.status).strip()
                    if state.attention is not None
                    else ""
                ),
                implementer_status=state.current_session.implementer_status.strip(),
                implementer_ack=state.current_session.implementer_ack.strip(),
                implementer_ack_state=state.current_session.implementer_ack_state.strip(),
            )
        )

        return ReviewerGateState(
            bridge_active=True,
            reviewer_mode=mode,
            review_accepted=state.bridge.review_accepted,
            required_checks_status="unknown",
            checkpoint_permitted=True,
            review_gate_allows_push=state.bridge.review_accepted,
            implementation_blocked=implementation_blocked,
            implementation_block_reason=implementation_block_reason,
        )
    except ImportError:
        return None


def _detect_reviewer_gate_without_typed_state(
    governance: ProjectGovernance | None,
) -> ReviewerGateState:
    if governance is None:
        return ReviewerGateState(
            checkpoint_permitted=True,
            review_gate_allows_push=True,
        )
    bridge_active = bool(
        governance.bridge_config.bridge_active
        or str(governance.bridge_config.review_channel_path or "").strip()
        or str(governance.bridge_config.bridge_path or "").strip()
    )
    if not bridge_active:
        return ReviewerGateState(
            checkpoint_permitted=True,
            review_gate_allows_push=True,
        )
    return ReviewerGateState(
        bridge_active=True,
        reviewer_mode="unknown",
        review_accepted=False,
        checkpoint_permitted=True,
        review_gate_allows_push=False,
        implementation_blocked=True,
        implementation_block_reason="typed_review_state_required",
    )
def _reviewer_loop_block_state(
    *,
    reviewer_mode: str,
    claude_ack_current: bool,
    attention_status: str = "",
    implementer_status: str = "",
    implementer_ack: str = "",
    implementer_ack_state: str = "",
) -> tuple[bool, str]:
    from ..review_channel.peer_liveness import reviewer_mode_is_active

    if not reviewer_mode_is_active(reviewer_mode):
        return False, ""
    if claude_ack_current:
        return False, ""
    if is_pending_implementer_state(
        implementer_status=implementer_status,
        implementer_ack=implementer_ack,
        implementer_ack_state=implementer_ack_state,
    ):
        return False, ""
    reason = attention_status or "claude_ack_stale"
    return True, reason


def _derive_advisory_action(
    governance: ProjectGovernance,
    gate: ReviewerGateState,
) -> tuple[str, str]:
    """Derive the advisory action from push enforcement + reviewer gate.

    Outcomes:
    - continue_editing: safe to keep working
    - await_review: local slice is checkpointed; wait for current review state
    - checkpoint_before_continue: commit/checkpoint before more edits
    - checkpoint_allowed: checkpoint is permitted now (but not required)
    - push_allowed: push to remote is safe now
    - no_push_needed: worktree is clean, nothing to push
    """
    pe = governance.push_enforcement
    if pe.checkpoint_required:
        return "checkpoint_before_continue", pe.checkpoint_reason
    if not pe.safe_to_continue_editing:
        return "checkpoint_before_continue", "worktree_budget_exceeded"
    if gate.implementation_blocked:
        return "checkpoint_before_continue", (
            gate.implementation_block_reason or "reviewer_loop_blocked"
        )
    if gate.bridge_active and not gate.review_accepted:
        if pe.worktree_clean:
            return "await_review", "review_pending_before_push"
        return "continue_editing", "review_pending"
    if pe.worktree_clean and pe.ahead_of_upstream_commits in (0, None):
        return "no_push_needed", "clean_worktree"
    if pe.worktree_clean and gate.review_gate_allows_push:
        return "push_allowed", "worktree_clean_and_review_accepted"
    if gate.checkpoint_permitted and pe.worktree_dirty:
        return "checkpoint_allowed", "worktree_dirty_within_budget"
    return "continue_editing", "clean_worktree"


def build_startup_context(
    *,
    repo_root: Path | None = None,
) -> StartupContext:
    """Build the typed startup-context packet for the current repo state."""
    if repo_root is None:
        from ..config import get_repo_root
        repo_root = get_repo_root()

    from ..governance.draft import scan_repo_governance

    governance = scan_repo_governance(repo_root)
    gate = _detect_reviewer_gate(repo_root, governance=governance)
    push_decision = _derive_push_decision(governance, gate)
    action, reason = _derive_advisory_action(governance, gate)
    work_intake = build_work_intake_packet(
        repo_root=repo_root,
        governance=governance,
        advisory_action=action,
        advisory_reason=reason,
    )
    quality_signals = load_startup_quality_signals(repo_root)

    return StartupContext(
        governance=governance,
        reviewer_gate=gate,
        push_decision=push_decision,
        advisory_action=action,
        advisory_reason=reason,
        work_intake=work_intake,
        quality_signals=quality_signals,
    )


def blocks_new_implementation(ctx: StartupContext) -> bool:
    """Return whether the typed startup receipt blocks another edit slice."""
    if ctx.reviewer_gate.implementation_blocked:
        return True
    governance = ctx.governance
    if governance is None:
        return False
    push = governance.push_enforcement
    return bool(push.checkpoint_required or not push.safe_to_continue_editing)


def _startup_governance_dict(governance: ProjectGovernance) -> dict[str, Any]:
    """Return a bounded governance projection suitable for startup packets."""
    return startup_governance_dict(governance)
