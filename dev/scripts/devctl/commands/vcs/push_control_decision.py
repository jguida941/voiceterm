"""Control-decision bridge for governed push publication."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...runtime.control_decision_artifacts import load_control_decision_payload
from ...runtime.control_decision_obedience import (
    build_attempted_action_receipt,
    evaluate_control_decision_obedience,
)
from .push_attempted_command import push_attempted_argv, push_attempted_command
from .push_authorization_control import push_authorization_control_decision


def push_control_decision_obedience_report(
    args: Any,
    *,
    repo_root: Path,
    commit_pipeline: Any = None,
    publication_authorization_fn: Any = None,
) -> dict[str, object]:
    if bool(getattr(args, "allow_missing_control_decision_for_test", False)):
        return {
            "ok": True,
            "command": "devctl.push.control_decision_obedience",
            "contract_id": "ControlDecisionObeyedGuard",
            "diagnostic_bypass": "allow_missing_control_decision_for_test",
        }
    decision = load_control_decision_payload(args, repo_root=repo_root)
    if not decision:
        decision = push_authorization_control_decision(
            args,
            repo_root=repo_root,
            commit_pipeline=commit_pipeline,
            publication_authorization_fn=publication_authorization_fn,
        )
    if not decision:
        return {}
    attempted_action = build_attempted_action_receipt(
        action_kind="devctl.push.execute",
        command=push_attempted_command(args),
        argv=tuple(push_attempted_argv(args)),
        actor=str(getattr(args, "actor", "") or ""),
        role=str(getattr(args, "role", "") or ""),
        session_id=str(getattr(args, "session_id", "") or ""),
        mutates=True,
        writes_state=True,
        executes_command=True,
        source_decision_id=str(decision.get("receipt_id") or ""),
        source_snapshot_id=str(decision.get("source_snapshot_id") or ""),
        started_at_utc="",
    ).to_dict()
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(attempted_action,),
    ).to_dict()
    report["command"] = "devctl.push.control_decision_obedience"
    report["attempted_action"] = attempted_action
    return report


__all__ = ["push_control_decision_obedience_report"]
