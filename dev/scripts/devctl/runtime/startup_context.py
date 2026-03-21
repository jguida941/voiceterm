"""Typed startup-context surface for AI agent sessions.

Combines ProjectGovernance, push/checkpoint state, and reviewer/ready-gate
inputs into one machine-readable packet that an agent inspects at session
start to decide: continue editing, checkpoint first, or push now.

This is advisory policy, not forced execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .project_governance import ProjectGovernance


@dataclass(frozen=True, slots=True)
class ReviewerGateState:
    """Current reviewer/ready-gate inputs for safe checkpoint/push decisions."""

    bridge_active: bool = False
    reviewer_mode: str = "single_agent"
    review_accepted: bool = False
    required_checks_green: bool = False
    checkpoint_permitted: bool = True
    push_permitted: bool = False


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
    advisory_action: str = "continue_editing"
    advisory_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "advisory_action": self.advisory_action,
            "advisory_reason": self.advisory_reason,
            "reviewer_gate": asdict(self.reviewer_gate),
        }
        if self.governance is not None:
            d["governance"] = self.governance.to_dict()
        return d


def _detect_reviewer_gate(repo_root: Path) -> ReviewerGateState:
    """Detect current reviewer/ready-gate state from live repo artifacts."""
    bridge_path = repo_root / "bridge.md"
    if not bridge_path.exists():
        return ReviewerGateState(
            checkpoint_permitted=True,
            push_permitted=True,
        )
    try:
        from ..review_channel.bridge_validation import bridge_review_accepted
        from ..review_channel.peer_liveness import reviewer_mode_is_active
        from ..review_channel.handoff import (
            extract_bridge_snapshot,
            summarize_bridge_liveness,
        )

        text = bridge_path.read_text(encoding="utf-8")
        snapshot = extract_bridge_snapshot(text)
        liveness = summarize_bridge_liveness(snapshot)
        mode = liveness.reviewer_mode or "single_agent"
        active = reviewer_mode_is_active(mode)
        if not active:
            return ReviewerGateState(
                bridge_active=False,
                reviewer_mode=mode,
                review_accepted=True,
                required_checks_green=False,
                checkpoint_permitted=True,
                push_permitted=True,
            )
        review_accepted = bridge_review_accepted(snapshot)
        return ReviewerGateState(
            bridge_active=True,
            reviewer_mode=mode,
            review_accepted=review_accepted,
            required_checks_green=False,
            checkpoint_permitted=True,
            push_permitted=review_accepted,
        )
    except (OSError, ImportError, ValueError):
        # Fail closed: unknown gate state → no push, checkpoint only
        return ReviewerGateState(
            checkpoint_permitted=True,
            push_permitted=False,
        )


def _derive_advisory_action(
    governance: ProjectGovernance,
    gate: ReviewerGateState,
) -> tuple[str, str]:
    """Derive the advisory action from push enforcement + reviewer gate.

    Outcomes:
    - continue_editing: safe to keep working
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
    if gate.bridge_active and not gate.review_accepted:
        return "continue_editing", "review_pending"
    if not pe.worktree_dirty and pe.ahead_of_upstream_commits in (0, None):
        return "no_push_needed", "clean_worktree"
    if pe.push_ready and gate.push_permitted:
        return "push_allowed", "clean_worktree_and_review_accepted"
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
    gate = _detect_reviewer_gate(repo_root)
    action, reason = _derive_advisory_action(governance, gate)

    return StartupContext(
        governance=governance,
        reviewer_gate=gate,
        advisory_action=action,
        advisory_reason=reason,
    )
