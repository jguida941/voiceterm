"""Runtime checks for the startup-authority contract."""

from __future__ import annotations

from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        import_repo_module,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        import_repo_module,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )

from .runtime_import_atomicity import collect_import_index_atomicity_findings
from .runtime_push_checks import collect_push_decision_contract_errors

_detect_reviewer_gate = import_repo_module(
    "dev.scripts.devctl.runtime.startup_context",
    repo_root=REPO_ROOT,
)._detect_reviewer_gate


def collect_checkpoint_budget_errors(gov) -> list[str]:
    """Return fail-closed errors when the worktree is over the continuation budget."""
    push = gov.push_enforcement
    if push.checkpoint_required or not push.safe_to_continue_editing:
        return [
            "Startup authority is over budget: "
            f"checkpoint_required={push.checkpoint_required}, "
            f"safe_to_continue_editing={push.safe_to_continue_editing}, "
            f"reason={push.checkpoint_reason or 'worktree_budget_exceeded'}."
        ]
    return []


def collect_reviewer_loop_block_errors(repo_root: Path, gov) -> list[str]:
    """Return fail-closed errors when the active reviewer loop blocks implementation."""
    try:
        gate = _detect_reviewer_gate(repo_root, governance=gov)
    except AttributeError:
        gate = _detect_reviewer_gate(repo_root)
    if not gate.implementation_blocked:
        return []
    reason = gate.implementation_block_reason or "reviewer_loop_blocked"
    return [
        "Reviewer loop blocks a new implementation slice: "
        f"reviewer_mode={gate.reviewer_mode}, "
        f"review_accepted={gate.review_accepted}, "
        f"reason={reason}."
    ]
