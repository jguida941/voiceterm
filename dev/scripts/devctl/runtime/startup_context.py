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

from .project_governance import ProjectGovernance
from .startup_signals import load_startup_quality_signals


@dataclass(frozen=True, slots=True)
class ReviewerGateState:
    """Current reviewer/ready-gate inputs for safe checkpoint/push decisions."""

    bridge_active: bool = False
    reviewer_mode: str = "single_agent"
    review_accepted: bool = False
    required_checks_status: str = "unknown"
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
    quality_signals: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        d["schema_version"] = self.schema_version
        d["contract_id"] = self.contract_id
        d["advisory_action"] = self.advisory_action
        d["advisory_reason"] = self.advisory_reason
        d["reviewer_gate"] = asdict(self.reviewer_gate)
        d["quality_signals"] = dict(self.quality_signals)
        if self.governance is not None:
            d["governance"] = self.governance.to_dict()
        return d


def _detect_reviewer_gate(repo_root: Path) -> ReviewerGateState:
    """Detect current reviewer/ready-gate state from typed review-state
    artifacts when available, falling back to live bridge.md prose.

    Preferred path (typed): read review_state.json from the managed projection
    root. This avoids coupling startup to live bridge.md modifications.

    Fallback path (bridge): parse bridge.md directly when projections are not
    available. This preserves backward compatibility during migration.
    """
    # Try typed review-state first (preferred path)
    typed_gate = _detect_reviewer_gate_from_typed_state(repo_root)
    if typed_gate is not None:
        return typed_gate

    # Fallback: parse bridge.md directly (compatibility path)
    return _detect_reviewer_gate_from_bridge(repo_root)


def _detect_reviewer_gate_from_typed_state(
    repo_root: Path,
) -> ReviewerGateState | None:
    """Read reviewer gate from typed review_state.json when available.

    Uses the same reviewer-owned acceptance semantics as
    ``bridge_validation.bridge_review_accepted()`` — verdict must show
    accepted/all-green/resolved AND findings must be clear/none.  The typed
    ``ReviewBridgeState`` carries ``open_findings`` directly and the bridge
    snapshot is reconstructed from the live file only for the verdict check so
    the acceptance contract stays identical to the bridge-backed path.
    """
    review_state_path = (
        repo_root / "dev" / "reports" / "review_channel" / "latest" / "review_state.json"
    )
    if not review_state_path.exists():
        return None
    try:
        import json

        payload = json.loads(review_state_path.read_text(encoding="utf-8"))
        bridge_block = payload.get("bridge") or {}
        mode = str(bridge_block.get("reviewer_mode") or "single_agent")

        from ..review_channel.peer_liveness import reviewer_mode_is_active

        active = reviewer_mode_is_active(mode)
        if not active:
            return ReviewerGateState(
                bridge_active=False,
                reviewer_mode=mode,
                review_accepted=True,
                required_checks_status="unknown",
                checkpoint_permitted=True,
                push_permitted=True,
            )

        # Read review_accepted directly from the typed bridge state.
        # This field is populated by the projection layer using the same
        # reviewer-owned acceptance semantics as bridge_review_accepted().
        review_accepted = bool(bridge_block.get("review_accepted", False))

        return ReviewerGateState(
            bridge_active=True,
            reviewer_mode=mode,
            review_accepted=review_accepted,
            required_checks_status="unknown",
            checkpoint_permitted=True,
            push_permitted=review_accepted,
        )
    except (OSError, ImportError, ValueError, KeyError):
        return None  # Fall through to bridge path


def _detect_reviewer_gate_from_bridge(repo_root: Path) -> ReviewerGateState:
    """Fallback: detect reviewer gate by parsing live bridge.md prose."""
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
                required_checks_status="unknown",
                checkpoint_permitted=True,
                push_permitted=True,
            )
        review_accepted = bridge_review_accepted(snapshot)
        return ReviewerGateState(
            bridge_active=True,
            reviewer_mode=mode,
            review_accepted=review_accepted,
            required_checks_status="unknown",
            checkpoint_permitted=True,
            push_permitted=review_accepted,
        )
    except (OSError, ImportError, ValueError):
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
    quality_signals = load_startup_quality_signals(repo_root)

    return StartupContext(
        governance=governance,
        reviewer_gate=gate,
        advisory_action=action,
        advisory_reason=reason,
        quality_signals=quality_signals,
    )


def blocks_new_implementation(ctx: StartupContext) -> bool:
    """Return whether the typed startup receipt blocks another edit slice."""
    governance = ctx.governance
    if governance is None:
        return False
    push = governance.push_enforcement
    return bool(
        push.checkpoint_required or not push.safe_to_continue_editing
    )
