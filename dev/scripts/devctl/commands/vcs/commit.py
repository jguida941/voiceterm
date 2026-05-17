"""Governed commit command backed by the typed remote/local pipeline."""

from __future__ import annotations

from pathlib import Path

from ...config import REPO_ROOT
from ...governance.push_policy import load_push_policy
from ...runtime.commit_permission import build_commit_permission_decision_for_executor
from ...runtime.governance_scan import scan_repo_governance_safely
from ...runtime.review_snapshot_refresh import receipt_commit_parent_sha
from .commit_action_request_authority import (
    action_request_authority_block_report,
    action_request_execution_receipt_report,
    mark_commit_action_request_execution_started,
    resolve_commit_action_request_grant,
)
from .commit_caller_role import caller_role_report
from .commit_guard_bundle import (
    _pipeline_has_validation_plan,
    guard_result,
    pipeline_has_checkpoint_snapshot as _pipeline_has_checkpoint_snapshot,
    run_guard_bundle,
)
from .commit_preflight import resolve_interaction_mode
from .commit_passthrough import (
    CommitPassthrough,
    build_git_commit_cmd as _build_git_commit_cmd,
    parse_passthrough as _parse_passthrough,
)
from .commit_runtime_flow import (
    run_commit_pipeline_flow,
)
from .governed_executor import GovernedVcsExecutor
from .progress import emit_vcs_progress
# Per rev_pkt_2487 issue 2: re-export build_commit_action from this module
# so the test patch seam `dev.scripts.devctl.commands.vcs.commit.build_commit_action`
# stays valid without forcing the test to track the actual production import.
# This is the canonical commit entry-point module; it should expose the
# action-builder name even though the implementation lives in
# governed_executor_actions.
from .governed_executor_actions import (
    _build_report,
    _emit_report,
    build_commit_action,
)

# Compatibility re-export while commit guard helpers live in their own module.
_run_guard_bundle = run_guard_bundle
_resolve_interaction_mode = resolve_interaction_mode


def _report_commit_shas(*, repo_root: Path, commit_sha: str) -> tuple[str, str]:
    """Compatibility wrapper for tests and older commit.py callers."""
    head_sha = str(commit_sha or "").strip()
    if not head_sha:
        return "", ""
    try:
        governance = scan_repo_governance_safely(repo_root)
    except (OSError, ValueError):
        governance = None
    content_sha = receipt_commit_parent_sha(
        repo_root=repo_root,
        current_head=head_sha,
        governance=governance,
    )
    if content_sha and content_sha != head_sha:
        return content_sha, head_sha
    return head_sha, ""


def _commit_permission_report(
    vcs_executor: GovernedVcsExecutor,
    *,
    action_request_grant=None,
) -> dict[str, object] | None:
    """Return a blocking report if startup authority denies governed commit."""
    decision, load_error = build_commit_permission_decision_for_executor(vcs_executor)
    if decision.commit_permission != "blocked":
        return None
    if not load_error and _action_request_grants_commit_permission(action_request_grant):
        return None
    next_command = str(decision.next_command or "").strip()
    guidance = "Run the reported next_command before staging or committing."
    if next_command:
        guidance = f"Run `{next_command}` before staging or committing."
    if load_error:
        guidance = (
            f"Startup authority could not be loaded for the commit gate: {load_error}. "
            "Rerun startup-context and repair blockers before requesting a commit."
        )
    return _build_report(
        status="blocked",
        reason="commit_permission_blocked",
        commit_permission=decision.to_dict(),
        blockers=list(decision.blockers),
        next_command=next_command,
        allowed_actions=list(decision.allowed_actions),
        blocked_actions=list(decision.blocked_actions),
        recovery_action=decision.recovery_action,
        escalation_action=decision.escalation_action,
        operator_guidance=guidance,
    )


def _action_request_grants_commit_permission(grant) -> bool:
    """Return True when a packet grant satisfies governed commit authority."""
    if grant is None or not bool(getattr(grant, "authorized", False)):
        return False
    capabilities = tuple(getattr(grant, "granted_capabilities", ()) or ())
    return "repo.stage" in capabilities and "repo.commit" in capabilities


def run_commit(
    args,
    *,
    repo_root: Path = REPO_ROOT,
    guard_runner=None,
    policy=None,
    executor: GovernedVcsExecutor | None = None,
    interaction_mode: str | None = None,
) -> int:
    """Run governed commit through the typed remote/local pipeline."""
    emit_vcs_progress("commit.entry", "validating governed commit invocation")
    passthrough = _parse_passthrough(args)
    if passthrough.unsupported:
        _emit_report(args, _unsupported_passthrough_report(passthrough))
        return 1

    emit_vcs_progress("commit.policy", "loading push policy and vcs executor")
    resolved_policy = policy or load_push_policy(repo_root=repo_root)
    vcs_executor = executor or GovernedVcsExecutor(
        repo_root=repo_root,
        push_policy=resolved_policy,
    )
    action_request_interaction_mode = (
        str(interaction_mode or "").strip()
        if getattr(args, "action_request", None)
        else ""
    )
    if getattr(args, "action_request", None) and not action_request_interaction_mode:
        action_request_interaction_mode = resolve_interaction_mode(repo_root)
    emit_vcs_progress("commit.action_request", "checking packet-scoped authority")
    action_request_grant = resolve_commit_action_request_grant(
        args=args,
        repo_root=repo_root,
        pipeline=vcs_executor.load_pipeline(),
        interaction_mode=action_request_interaction_mode,
    )
    if action_request_grant is not None and not action_request_grant.authorized:
        _emit_report(args, action_request_authority_block_report(action_request_grant))
        return 1
    role_report = caller_role_report(
        args,
        action_request_grant=action_request_grant,
    )
    if role_report is not None:
        _emit_report(args, role_report)
        return 1
    emit_vcs_progress("commit.permission_gate", "checking startup commit authority")
    permission_report = _commit_permission_report(
        vcs_executor,
        action_request_grant=action_request_grant,
    )
    if permission_report is not None:
        _emit_report(args, permission_report)
        return 1
    if action_request_grant is not None:
        try:
            action_request_grant = mark_commit_action_request_execution_started(
                repo_root=repo_root,
                grant=action_request_grant,
            )
        except (OSError, ValueError) as exc:
            _emit_report(
                args,
                action_request_execution_receipt_report(
                    grant=action_request_grant,
                    error=exc,
                ),
            )
            return 1
    emit_vcs_progress("commit.pipeline_flow", "entering staged pipeline flow")
    return run_commit_pipeline_flow(
        args=args,
        repo_root=repo_root,
        resolved_policy=resolved_policy,
        vcs_executor=vcs_executor,
        guard_runner=guard_runner,
        passthrough=passthrough,
        action_request_grant=action_request_grant,
        interaction_mode=interaction_mode,
        emit_report=_emit_report,
    )


def _unsupported_passthrough_report(passthrough: CommitPassthrough) -> dict[str, object]:
    return _build_report(
        status="blocked",
        reason="unsupported_passthrough",
        unsupported_passthrough=list(passthrough.unsupported),
        guidance=(
            "Use `devctl commit --paths <path>...` to stage exact paths "
            "through the governed pipeline, then rerun as needed. "
            "The governed commit path only supports `--allow-empty`, "
            "`--no-edit`, and `--amend`."
        ),
    )


def run(args) -> int:
    """Entry point for ``devctl commit``."""
    return run_commit(args)
