"""Reviewer-loop checks for the startup-authority contract."""

from __future__ import annotations

import os
from pathlib import Path

_COMMIT_GATE_BYPASS_ENV = "DEVCTL_COMMIT_GATE_BYPASS_STARTUP_AUTHORITY"
_IMPLEMENTATION_STRICT_INTENT = "implementation_strict"
_REVIEWER_BOOTSTRAP_INTENT = "reviewer_bootstrap"
_COMPLETED_HANDOFF_REVIEWER_LOOP_REASONS = frozenset(
    {"runtime_missing", "no_live_agents", "process_dead"}
)

try:
    from check_bootstrap import REPO_ROOT, import_repo_module
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, import_repo_module

_detect_reviewer_gate = import_repo_module(
    "dev.scripts.devctl.runtime.startup_context",
    repo_root=REPO_ROOT,
)._detect_reviewer_gate
_current_completed_handoff_outcome = import_repo_module(
    "dev.scripts.devctl.runtime.completed_handoff_authority",
    repo_root=REPO_ROOT,
).current_completed_handoff_outcome


def collect_reviewer_loop_block_errors(
    repo_root: Path,
    gov,
    *,
    intent: str = _IMPLEMENTATION_STRICT_INTENT,
    reviewer_gate=None,
) -> list[str]:
    """Return fail-closed errors when the active reviewer loop blocks implementation."""
    if os.environ.get(_COMMIT_GATE_BYPASS_ENV, "").strip() == "1":
        return []
    gate = reviewer_gate
    if gate is None:
        try:
            gate = _detect_reviewer_gate(repo_root, governance=gov)
        except AttributeError:
            gate = _detect_reviewer_gate(repo_root)
    if not gate.implementation_blocked:
        return []
    if gate.review_gate_allows_push:
        return []
    if _completed_handoff_satisfies_reviewer_loop_block(repo_root, gate):
        return []
    if intent == _REVIEWER_BOOTSTRAP_INTENT:
        return []
    reason = gate.implementation_block_reason or "reviewer_loop_blocked"
    return [
        "Reviewer loop blocks a new implementation slice: "
        f"reviewer_mode={gate.reviewer_mode}, "
        f"review_accepted={gate.review_accepted}, "
        f"reason={reason}."
    ]


def _completed_handoff_satisfies_reviewer_loop_block(
    repo_root: Path,
    gate,
) -> bool:
    """Return True when completed-handoff evidence covers the publish-only block."""
    if not _gate_reports_completed_handoff_publication_block(gate):
        return False
    try:
        return _current_completed_handoff_outcome(repo_root=repo_root) is not None
    except (OSError, ValueError):
        return False


def _gate_reports_completed_handoff_publication_block(gate) -> bool:
    mode = _gate_text(gate, "reviewer_mode")
    effective_mode = _gate_text(gate, "effective_reviewer_mode")
    if "active_dual_agent" not in {mode, effective_mode}:
        return False
    reason = _gate_text(gate, "implementation_block_reason")
    return reason in _COMPLETED_HANDOFF_REVIEWER_LOOP_REASONS


def _gate_text(gate, attr: str) -> str:
    return str(getattr(gate, attr, "") or "").strip()


__all__ = ["collect_reviewer_loop_block_errors"]
