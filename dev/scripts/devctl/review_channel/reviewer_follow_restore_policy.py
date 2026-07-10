"""Typed restore-policy helpers for reviewer-follow stale-runtime recovery."""

from __future__ import annotations

from .reviewer_follow_runtime import reviewer_runtime_text


def restore_action_from_report(
    *,
    report: dict[str, object],
    reviewer_runtime: dict[str, object],
) -> str:
    decision = recovery_decision(report)
    if decision:
        action = decision_action(decision)
        if action:
            return action
        action = command_action(str(decision.get("command") or ""))
        if action:
            return action
    action = command_action(reviewer_runtime_text(reviewer_runtime, "recovery_action_allowed"))
    if action:
        return action
    attention = report.get("attention")
    if not isinstance(attention, dict):
        return ""
    return command_action(str(attention.get("recommended_command") or ""))


def auto_relaunch_allowed(report: dict[str, object]) -> bool:
    decision = recovery_decision(report)
    if not decision:
        return False
    if "can_auto_fix" in decision:
        return bool(decision.get("can_auto_fix"))
    if "requires_approval" in decision:
        return not bool(decision.get("requires_approval"))
    return False


def recovery_decision(report: dict[str, object]) -> dict[str, object]:
    recovery_assessment = report.get("recovery_assessment")
    if not isinstance(recovery_assessment, dict):
        return {}
    decision = recovery_assessment.get("decision")
    return decision if isinstance(decision, dict) else {}


def decision_action(decision: dict[str, object]) -> str:
    action_id = str(decision.get("action_id") or "").strip()
    if action_id == "relaunch_review_loop":
        return "launch"
    if action_id == "recover_implementer":
        return "recover"
    return ""


def command_action(command: str) -> str:
    command_text = command.strip()
    for action in ("launch", "rollover", "recover"):
        if f"--action {action}" in command_text:
            return action
    return ""
