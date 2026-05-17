"""Startup-context helpers for RuntimeTruthSnapshot convergence."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from .runtime_truth_snapshot import RuntimeTruthSnapshot, build_runtime_truth_snapshot
from .startup_blocker_decision import derive_startup_blocker
from .startup_connectivity_registry import startup_connectivity_registry
from .startup_context_models import ReviewerGateState
from .startup_signals import compact_startup_quality_signals, load_startup_quality_signals
from .startup_push_decision import PushDecisionState
from .worktree_orphan_snapshot_projection import build_orphan_snapshot_projection

if TYPE_CHECKING:
    from .review_state_models import ReviewState


@dataclass(frozen=True, slots=True)
class StartupQualityBlockerDeps:
    build_orphan_snapshot_projection: Callable[..., object] = (
        build_orphan_snapshot_projection
    )
    load_startup_quality_signals: Callable[[Path], object] = load_startup_quality_signals
    compact_startup_quality_signals: Callable[[object], dict[str, object]] = (
        compact_startup_quality_signals
    )
    derive_startup_blocker: Callable[..., object] = derive_startup_blocker


def startup_runtime_truth_and_gate(
    *,
    repo_root: Path,
    review_state: "ReviewState | None",
    gate: ReviewerGateState,
) -> tuple[ReviewerGateState, RuntimeTruthSnapshot]:
    runtime_truth = build_runtime_truth_snapshot(
        repo_root=repo_root,
        review_state=review_state,
        connectivity_registry=startup_connectivity_registry(repo_root),
    )
    return reviewer_gate_with_runtime_truth(gate, runtime_truth), runtime_truth


def reviewer_gate_with_runtime_truth(
    gate: ReviewerGateState,
    runtime_truth: RuntimeTruthSnapshot,
) -> ReviewerGateState:
    interaction_mode = str(runtime_truth.interaction_mode or "").strip()
    if not interaction_mode or interaction_mode == "unresolved":
        return gate
    if gate.operator_interaction_mode == interaction_mode:
        return gate
    return replace(gate, operator_interaction_mode=interaction_mode)


def startup_quality_blocker_inputs(
    *,
    repo_root: Path,
    review_state: "ReviewState | None",
    push_decision: PushDecisionState,
    deps: StartupQualityBlockerDeps | None = None,
) -> tuple[object, dict[str, object], object]:
    if deps is None:
        deps = StartupQualityBlockerDeps()
    orphan_snapshot = deps.build_orphan_snapshot_projection(
        repo_root=repo_root,
        review_state=review_state,
        scan_scope="startup_context",
        scan_trigger="startup_context",
    )
    quality_signals = deps.compact_startup_quality_signals(
        deps.load_startup_quality_signals(repo_root)
    )
    blocker = deps.derive_startup_blocker(
        review_state=review_state,
        push_decision=push_decision,
    )
    return orphan_snapshot, quality_signals, blocker


__all__ = [
    "StartupQualityBlockerDeps",
    "reviewer_gate_with_runtime_truth",
    "startup_quality_blocker_inputs",
    "startup_runtime_truth_and_gate",
]
