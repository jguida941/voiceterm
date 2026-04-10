"""Scoped startup gate for launcher and mutation commands."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

from ..config import REPO_ROOT
from .startup_authority import build_startup_authority_report
from .startup_receipt import (
    IMPLEMENTATION_STRICT_STARTUP_INTENT,
    REVIEWER_BOOTSTRAP_STARTUP_INTENT,
    load_startup_receipt,
    startup_receipt_problems_for_intent,
)

_REVIEW_CHANNEL_GATED_ACTIONS = {"launch", "rollover"}
_CONTROLLER_ACTION_GATED_ACTIONS = {"dispatch-report-only", "resume-loop"}
_GATED_COMMANDS = {
    "autonomy-swarm",
    "guard-run",
    "sync",
    "autonomy-loop",
    "mutation-loop",
    "swarm_run",
}


def command_requires_startup_gate(args: SimpleNamespace) -> bool:
    """Return whether one CLI invocation must honor the startup gate."""
    command = str(getattr(args, "command", "") or "").strip()
    if command in _GATED_COMMANDS:
        return True
    if command == "review-channel":
        action = str(getattr(args, "action", "") or "").strip()
        if action in _REVIEW_CHANNEL_GATED_ACTIONS:
            return not _is_repair_launch(args, action)
        return False
    if command == "controller-action":
        action = str(getattr(args, "action", "") or "").strip()
        return action in _CONTROLLER_ACTION_GATED_ACTIONS
    return False


def _is_repair_launch(args: SimpleNamespace, action: str) -> bool:
    """Allow launch/rollover when startup-context says repair_reviewer_loop.

    The gate must not block the command that IS the repair. When
    startup-context returns action=repair_reviewer_loop, launching the
    reviewer loop is the correct next step — blocking it creates a
    deadlock where the system says "repair needed" but refuses to run the
    repair.
    """
    if action not in {"launch", "rollover"}:
        return False
    try:
        receipt = load_startup_receipt(repo_root=REPO_ROOT)
    except (FileNotFoundError, ValueError):
        return False
    if receipt is None:
        return False
    return str(receipt.advisory_action or "").strip() == "repair_reviewer_loop"


def enforce_startup_gate(
    args: SimpleNamespace,
    *,
    repo_root: Path = REPO_ROOT,
) -> str | None:
    """Return a blocking startup-gate message for launcher/mutation commands."""
    if not command_requires_startup_gate(args):
        return None

    intent = _startup_gate_intent(args)
    authority_report = build_startup_authority_report(
        repo_root=repo_root,
        intent=intent,
    )

    if not _ci_environment():
        receipt = load_startup_receipt(repo_root=repo_root)
        receipt_failures = startup_receipt_problems_for_intent(
            receipt,
            repo_root=repo_root,
            intent=intent,
            authority_report=authority_report,
        )
        if receipt_failures:
            return _format_gate_failure(
                args,
                heading="Startup gate blocked this command because the startup receipt is missing or stale.",
                failures=receipt_failures,
            )

    if bool(authority_report.get("ok", False)):
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


def _startup_gate_intent(args: SimpleNamespace) -> str:
    """Return the startup intent for one gated command."""
    command = str(getattr(args, "command", "") or "").strip()
    action = str(getattr(args, "action", "") or "").strip()
    if command == "review-channel" and action in _REVIEW_CHANNEL_GATED_ACTIONS:
        return REVIEWER_BOOTSTRAP_STARTUP_INTENT
    return IMPLEMENTATION_STRICT_STARTUP_INTENT


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
