"""Scoped startup gate for launcher and mutation commands."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

from ..config import REPO_ROOT
from .startup_authority import build_startup_authority_report
from .startup_receipt import load_startup_receipt, startup_receipt_problems

_REVIEW_CHANNEL_GATED_ACTIONS = {"launch", "rollover"}
_CONTROLLER_ACTION_GATED_ACTIONS = {"dispatch-report-only", "resume-loop"}
_GATED_COMMANDS = {
    "autonomy-swarm",
    "push",
    "guard-run",
    "sync",
    "autonomy-loop",
    "mutation-loop",
    "swarm_run",
}
_REVIEWER_LOOP_BLOCK_PREFIX = "Reviewer loop blocks a new implementation slice:"


def command_requires_startup_gate(args: SimpleNamespace) -> bool:
    """Return whether one CLI invocation must honor the startup gate."""
    command = str(getattr(args, "command", "") or "").strip()
    if command in _GATED_COMMANDS:
        return True
    if command == "review-channel":
        action = str(getattr(args, "action", "") or "").strip()
        return action in _REVIEW_CHANNEL_GATED_ACTIONS
    if command == "controller-action":
        action = str(getattr(args, "action", "") or "").strip()
        return action in _CONTROLLER_ACTION_GATED_ACTIONS
    return False


def enforce_startup_gate(
    args: SimpleNamespace,
    *,
    repo_root: Path = REPO_ROOT,
) -> str | None:
    """Return a blocking startup-gate message for launcher/mutation commands."""
    if not command_requires_startup_gate(args):
        return None

    authority_report = build_startup_authority_report(repo_root=repo_root)
    allow_recovery_action = _allow_recovery_action_despite_reviewer_block(
        args,
        authority_report=authority_report,
    )

    is_bootstrap = _is_reviewer_bootstrap_intent(args)
    if not _ci_environment():
        receipt = load_startup_receipt(repo_root=repo_root)
        receipt_failures = _filtered_receipt_failures(
            startup_receipt_problems(receipt, repo_root=repo_root),
            allow_recovery_action=allow_recovery_action,
            is_bootstrap=is_bootstrap,
        )
        if receipt_failures:
            return _format_gate_failure(
                args,
                heading="Startup gate blocked this command because the startup receipt is missing or stale.",
                failures=receipt_failures,
            )

    if bool(authority_report.get("ok", False)) or allow_recovery_action:
        return None
    return _format_gate_failure(
        args,
        heading="Startup gate blocked this command because the live startup-authority check is red.",
        failures=[
            str(row).strip()
            for row in authority_report.get("errors", ())
            if str(row).strip()
        ],
        footer=(
            "Refresh the startup packet with `startup-context`. "
            "If it exits non-zero, checkpoint or repair the state before continuing."
        ),
    )


def _is_reviewer_bootstrap_intent(args: SimpleNamespace) -> bool:
    """Return True when the command is review-channel launch or rollover."""
    command = str(getattr(args, "command", "") or "").strip()
    action = str(getattr(args, "action", "") or "").strip()
    return command == "review-channel" and action in _REVIEW_CHANNEL_GATED_ACTIONS


def _allow_recovery_action_despite_reviewer_block(
    args: SimpleNamespace,
    *,
    authority_report: dict[str, object],
) -> bool:
    """Permit launch/rollover for reviewer bootstrap even across reviewer-owned state drift.

    Launch/rollover is a reviewer-runtime repair action, not a new implementation
    slice. It must be allowed when the only problems are reviewer-loop blockage,
    stale implementer state, or reviewer-overdue conditions. It must NOT be
    allowed when there are non-reviewer authority failures or when a real
    checkpoint is required for dirty implementation work.
    """
    if not _is_reviewer_bootstrap_intent(args):
        return False
    if bool(authority_report.get("checkpoint_required", False)):
        return False
    errors = [
        str(row).strip()
        for row in authority_report.get("errors", ())
        if str(row).strip()
    ]
    if not errors:
        return True
    return all(error.startswith(_REVIEWER_LOOP_BLOCK_PREFIX) for error in errors)


def _filtered_receipt_failures(
    failures: list[str],
    *,
    allow_recovery_action: bool,
    is_bootstrap: bool = False,
) -> list[str]:
    """Keep stale-receipt blocking, but allow reviewer-bootstrap to cross admin drift.

    For reviewer bootstrap (launch/rollover), drop stale-HEAD failures and
    startup-authority mirror failures. The launch path repairs reviewer state,
    so HEAD drift from reviewer-owned artifacts is expected and safe.
    """
    if not allow_recovery_action and not is_bootstrap:
        return failures
    filtered = []
    for failure in failures:
        if "startup-authority failures" in failure:
            continue
        if is_bootstrap and "stale for the current HEAD commit" in failure:
            continue
        filtered.append(failure)
    return filtered


def _format_gate_failure(
    args: SimpleNamespace,
    *,
    heading: str,
    failures: list[str],
    footer: str | None = None,
) -> str:
    command_label = _command_label(args)
    lines = [heading, f"Command: `{command_label}`"]
    for failure in failures[:5]:
        lines.append(f"- {failure}")
    lines.append(
        "Run the repo's `startup-context` command before starting the next implementation or launcher slice."
    )
    if footer:
        lines.append(footer)
    return "\n".join(lines)


def _command_label(args: SimpleNamespace) -> str:
    command = str(getattr(args, "command", "") or "").strip()
    if command in {"review-channel", "controller-action"}:
        action = str(getattr(args, "action", "") or "").strip()
        if action:
            return f"{command} --action {action}"
    return command


def _ci_environment() -> bool:
    return str(os.getenv("GITHUB_ACTIONS") or "").strip().lower() == "true"
