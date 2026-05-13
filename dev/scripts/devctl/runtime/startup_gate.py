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
from .typed_gate_failure import TypedGateFailure

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
        if action not in _REVIEW_CHANNEL_GATED_ACTIONS:
            return False
        # A read-only reviewer launch (`--policy-hint review_only` plus
        # `--remote-role reviewer`) cannot mutate the worktree, so the
        # startup-authority gate that exists to catch dirty-worktree intent
        # drift does not apply. Without this short-circuit, every remote-
        # control resume in a session that has any auto-projection drift
        # is forced through a commit before a non-mutating reviewer can
        # spawn — which is the recurring cascade Finding F + Z named.
        if _is_review_only_reviewer_launch(args):
            return False
        return True
    if command == "controller-action":
        action = str(getattr(args, "action", "") or "").strip()
        return action in _CONTROLLER_ACTION_GATED_ACTIONS
    return False


def _is_review_only_reviewer_launch(args: SimpleNamespace) -> bool:
    policy_hint = str(getattr(args, "policy_hint", "") or "").strip().lower()
    remote_role = str(getattr(args, "remote_role", "") or "").strip().lower()
    return policy_hint == "review_only" and remote_role == "reviewer"


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
    for failure_text in failures[:5]:
        lines.append(f"- {failure_text}")
    lines.append(
        "Run the repo's `startup-context` command before starting the next implementation or launcher slice."
    )
    typed_failure = _typed_startup_gate_failure(
        gate_id="startup_gate",
        violation_reason=failures[0] if failures else heading,
    )
    lines.extend(_typed_gate_failure_lines(typed_failure))
    if footer:
        lines.append(footer)
    return "\n".join(lines)


def _typed_startup_gate_failure(
    *,
    gate_id: str,
    violation_reason: str,
) -> TypedGateFailure:
    return TypedGateFailure(
        gate_id=gate_id,
        violation_reason=violation_reason,
        bypass_invocation=(
            "python3 dev/scripts/devctl.py agent-loop --format json "
            "--actor <actor> --role implementer --plan <plan-id-or-slice-id> "
            "--operator-override --override-scope edit-only "
            "--override-reason '<typed reason>' --override-by operator"
        ),
        contract_definition_path="dev/scripts/devctl/runtime/startup_gate.py:61",
    )


def _typed_gate_failure_lines(failure: TypedGateFailure) -> list[str]:
    return [
        "TypedGateFailure:",
        f"- gate_id: {failure.gate_id}",
        f"- violation_reason: {failure.violation_reason}",
        f"- bypass_invocation: `{failure.bypass_invocation}`",
        f"- bypass_receipt_kind: {failure.bypass_receipt_kind}",
        f"- contract_definition_path: {failure.contract_definition_path}",
        f"- exception_lifecycle_class: {failure.exception_lifecycle_class}",
        (
            "This edit-only path requires explicit operator approval and does not "
            "authorize staging, commit, push, or raw bypass."
        ),
    ]


def _command_label(args: SimpleNamespace) -> str:
    command = str(getattr(args, "command", "") or "").strip()
    if command in {"review-channel", "controller-action"}:
        action = str(getattr(args, "action", "") or "").strip()
        if action:
            return f"{command} --action {action}"
    return command


def _ci_environment() -> bool:
    return str(os.getenv("GITHUB_ACTIONS") or "").strip().lower() == "true"
