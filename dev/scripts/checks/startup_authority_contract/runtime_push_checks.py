"""Push-decision contract checks for the startup-authority guard."""

from __future__ import annotations

from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, import_repo_module
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, import_repo_module

_detect_reviewer_gate = import_repo_module(
    "dev.scripts.devctl.runtime.startup_context",
    repo_root=REPO_ROOT,
)._detect_reviewer_gate
_derive_push_decision = import_repo_module(
    "dev.scripts.devctl.runtime.startup_push_decision",
    repo_root=REPO_ROOT,
).derive_push_decision

_REVIEW_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)
_DEVCTL_PUSH_EXECUTE_COMMAND = "python3 dev/scripts/devctl.py push --execute"
_VALID_PUSH_ACTIONS = {
    "await_checkpoint",
    "await_review",
    "run_devctl_push",
    "no_push_needed",
}


def collect_push_decision_contract_errors(repo_root: Path, gov) -> list[str]:
    """Return startup-contract errors when push next-step guidance is inconsistent."""
    try:
        gate = _detect_reviewer_gate(repo_root, governance=gov)
    except AttributeError:
        gate = _detect_reviewer_gate(repo_root)
    decision = _derive_push_decision(
        gov.push_enforcement,
        review_gate_allows_push=gate.review_gate_allows_push,
        implementation_blocked=gate.implementation_blocked,
        implementation_block_reason=gate.implementation_block_reason,
    )
    errors: list[str] = []

    if decision.action not in _VALID_PUSH_ACTIONS:
        errors.append(
            "Push decision contract emitted an unknown action: "
            f"{decision.action or '(empty)'}."
        )
        return errors

    if decision.action == "await_checkpoint":
        if decision.push_eligible_now:
            errors.append(
                "Push decision contract marked `await_checkpoint` as push-eligible."
            )
        if "checkpoint" not in decision.next_step_summary.lower():
            errors.append(
                "Push decision contract is missing checkpoint guidance for `await_checkpoint`."
            )
        return errors

    if decision.action == "await_review":
        if decision.push_eligible_now:
            errors.append(
                "Push decision contract marked `await_review` as push-eligible."
            )
        if decision.next_step_command != _REVIEW_STATUS_COMMAND:
            errors.append(
                "Push decision contract must point `await_review` to the canonical "
                "review-channel status command."
            )
        if "review" not in decision.next_step_summary.lower():
            errors.append(
                "Push decision contract is missing review guidance for `await_review`."
            )
        return errors

    if decision.action == "run_devctl_push":
        if not decision.push_eligible_now:
            errors.append(
                "Push decision contract emitted `run_devctl_push` without "
                "`push_eligible_now=true`."
            )
        if decision.next_step_command != _DEVCTL_PUSH_EXECUTE_COMMAND:
            errors.append(
                "Push decision contract must point `run_devctl_push` to the canonical "
                "`devctl push --execute` command."
            )
        if "governed push" not in decision.next_step_summary.lower():
            errors.append(
                "Push decision contract is missing governed-push guidance for "
                "`run_devctl_push`."
            )
        return errors

    if decision.push_eligible_now:
        errors.append("Push decision contract marked `no_push_needed` as push-eligible.")
    if not decision.next_step_summary:
        errors.append(
            "Push decision contract is missing operator guidance for `no_push_needed`."
        )
    if decision.next_step_command:
        errors.append(
            "Push decision contract should not emit a follow-up command for `no_push_needed`."
        )
    return errors
