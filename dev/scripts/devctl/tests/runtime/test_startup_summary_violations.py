"""Tests for the startup-summary -> ViolationRecord adapter.

These tests lock the field-by-field mapping from a typed
``StartupContext`` projection (the dict shape produced by
``StartupContext.to_dict()``) into ``ViolationRecord`` tuples so
downstream consumers can render startup blockers through the same
shared ``CheckResult`` / ``ViolationRecord`` renderer used for checks,
probes, and governance-review. The shape mirrors the existing probe and
governance-review adapter test patterns.
"""

from __future__ import annotations

from typing import Any, cast

from dev.scripts.devctl.runtime.check_result_models import ViolationRecord
from dev.scripts.devctl.runtime.startup_summary_violations import (
    startup_summary_to_violations,
)


def _summary(**overrides: Any) -> dict[str, Any]:
    """Build a healthy minimal StartupContext.to_dict() projection.

    Defaults represent a healthy session: ``advisory_action`` is
    ``continue_editing``, no implementation block, no pending push
    decision. Tests override only the fields they need to drive a
    specific blocker.
    """
    base: dict[str, Any] = {
        "schema_version": 1,
        "contract_id": "StartupContext",
        "advisory_action": "continue_editing",
        "advisory_reason": "",
        "rule_summary": "",
        "reviewer_gate": {
            "bridge_active": False,
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "review_accepted": False,
            "implementation_blocked": False,
            "implementation_block_reason": "",
            "recovery_diagnosis_status": "",
            "recovery_action_id": "",
            "recovery_command": "",
            "operator_interaction_mode": "local_terminal",
        },
        "push_decision": {
            "action": "no_push_needed",
            "reason": "",
            "next_step_summary": "",
            "next_step_command": "",
        },
    }
    base.update(overrides)
    return base


def test_healthy_summary_returns_empty_tuple() -> None:
    """A healthy startup context with no blockers yields an empty tuple."""
    assert startup_summary_to_violations(_summary()) == ()


def test_non_mapping_input_returns_empty_tuple() -> None:
    """A non-dict input must not raise; it must yield an empty tuple.

    The function signature is ``Mapping[str, Any]`` so static checkers
    would reject the wrong-typed inputs we want to exercise. ``cast`` is
    the localized escape hatch for "deliberately wrong type at the
    runtime boundary"; it leaves ``# type: ignore`` clean for the
    suppression-debt guard.
    """
    assert startup_summary_to_violations(cast(Any, None)) == ()
    assert startup_summary_to_violations(cast(Any, [])) == ()
    assert startup_summary_to_violations(cast(Any, "repair")) == ()


def test_checkpoint_before_continue_emits_one_violation() -> None:
    """`advisory_action=checkpoint_before_continue` is the canonical blocking action.

    `startup_advisory_decision._checkpoint_required_decision` and
    `_budget_exceeded_decision` both emit this action. It must project
    into a single `startup_authority` record so the dashboard can
    surface "operator must checkpoint before further work".
    """
    summary = _summary(
        advisory_action="checkpoint_before_continue",
        advisory_reason="dirty_path_budget_exceeded",
        rule_summary="Startup blocks another implementation slice because the worktree has crossed the repo's continuation budget.",
    )

    violations = startup_summary_to_violations(summary)

    assert len(violations) == 1
    record = violations[0]
    assert isinstance(record, ViolationRecord)
    assert record.step_name == "startup_authority"
    assert record.exit_code == 0
    assert "dirty_path_budget_exceeded" in record.summary
    assert record.policy == "startup_authority"
    assert record.severity == "high"
    assert record.source == "startup-context"
    assert record.fix.startswith("Startup blocks another implementation slice")


def test_repair_reviewer_loop_emits_one_violation() -> None:
    """`advisory_action=repair_reviewer_loop` is the canonical reviewer-loop block.

    `startup_advisory_decision._blocked_loop_decision` emits this action
    when reviewer-owned state has marked the loop as blocked. It must
    project into a single `startup_authority` record so the dashboard
    can surface "operator must repair the reviewer loop".
    """
    summary = _summary(
        advisory_action="repair_reviewer_loop",
        advisory_reason="reviewer_heartbeat_stale",
        rule_summary="Startup routes the next step to reviewer-loop repair because reviewer-owned state is blocking the live collaboration lane.",
    )

    violations = startup_summary_to_violations(summary)

    assert len(violations) == 1
    record = violations[0]
    assert record.step_name == "startup_authority"
    assert "reviewer_heartbeat_stale" in record.summary
    assert record.severity == "high"


def test_await_review_advisory_action_emits_violation() -> None:
    """`advisory_action=await_review` is a blocking state and yields a record.

    `startup_advisory_decision._pending_review_decision` emits this
    action when the worktree is clean but reviewer acceptance is still
    pending; the operator must wait for review.
    """
    summary = _summary(
        advisory_action="await_review",
        advisory_reason="review_pending_before_push",
    )

    violations = startup_summary_to_violations(summary)

    assert len(violations) == 1
    assert violations[0].step_name == "startup_authority"
    assert "review_pending_before_push" in violations[0].summary


def test_continue_editing_advisory_action_yields_no_violation() -> None:
    """The healthy `continue_editing` advisory must NOT produce a violation."""
    summary = _summary(
        advisory_action="continue_editing",
        advisory_reason="ok",
    )
    assert startup_summary_to_violations(summary) == ()


def test_checkpoint_allowed_advisory_action_yields_no_violation() -> None:
    """`checkpoint_allowed` is non-blocking and must yield no violation.

    Even though the worktree may be dirty, this state means the operator
    is allowed to keep editing within the checkpoint budget; it is not a
    blocker the dashboard should flag.
    """
    summary = _summary(
        advisory_action="checkpoint_allowed",
        advisory_reason="worktree_dirty_within_budget",
    )
    assert startup_summary_to_violations(summary) == ()


def test_implementation_blocked_emits_reviewer_gate_violation() -> None:
    """A reviewer-gate block projects into one reviewer_gate record."""
    summary = _summary(
        reviewer_gate={
            "bridge_active": True,
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
            "review_accepted": False,
            "implementation_blocked": True,
            "implementation_block_reason": "review_loop_relaunch_required",
            "recovery_diagnosis_status": "stale",
            "recovery_action_id": "review-channel.relaunch",
            "recovery_command": (
                "python3 dev/scripts/devctl.py review-channel --action launch"
            ),
            "operator_interaction_mode": "local_terminal",
        },
    )

    violations = startup_summary_to_violations(summary)

    assert len(violations) == 1
    record = violations[0]
    assert record.step_name == "reviewer_gate"
    assert record.exit_code == 0
    assert "review_loop_relaunch_required" in record.summary
    assert record.policy == "reviewer_gate"
    assert record.severity == "high"
    assert record.fix == (
        "python3 dev/scripts/devctl.py review-channel --action launch"
    )


def test_implementation_blocked_prefers_effective_reviewer_mode_in_summary() -> None:
    """Current-state blocker summaries should use the effective reviewer mode."""
    summary = _summary(
        reviewer_gate={
            "bridge_active": True,
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "tools_only",
            "review_accepted": False,
            "implementation_blocked": True,
            "implementation_block_reason": "",
            "recovery_diagnosis_status": "runtime_missing",
            "recovery_action_id": "",
            "recovery_command": "",
            "operator_interaction_mode": "local_terminal",
        },
    )

    violations = startup_summary_to_violations(summary)

    assert len(violations) == 1
    assert violations[0].summary == "implementation_blocked: tools_only"


def test_implementation_blocked_false_yields_no_violation() -> None:
    """When `implementation_blocked` is false, no reviewer_gate record is emitted."""
    summary = _summary(
        reviewer_gate={
            "bridge_active": True,
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
            "review_accepted": True,
            "implementation_blocked": False,
            "implementation_block_reason": "",
            "operator_interaction_mode": "local_terminal",
        },
    )
    assert startup_summary_to_violations(summary) == ()


def test_push_decision_await_checkpoint_emits_violation() -> None:
    """`push_decision.action=await_checkpoint` projects into one push_decision record."""
    summary = _summary(
        push_decision={
            "action": "await_checkpoint",
            "reason": "worktree_dirty",
            "next_step_summary": (
                "Commit or checkpoint the current bounded slice, then rerun "
                "startup-context."
            ),
            "next_step_command": "",
        },
    )

    violations = startup_summary_to_violations(summary)

    assert len(violations) == 1
    record = violations[0]
    assert record.step_name == "push_decision"
    assert record.exit_code == 0
    assert "worktree_dirty" in record.summary
    assert record.policy == "push_state_machine"
    assert record.severity == "medium"


def test_push_decision_run_devctl_push_yields_no_violation() -> None:
    """The healthy `run_devctl_push` push decision must NOT yield a violation."""
    summary = _summary(
        push_decision={
            "action": "run_devctl_push",
            "reason": "ready",
            "next_step_summary": "",
            "next_step_command": "python3 dev/scripts/devctl.py push --execute",
        },
    )
    assert startup_summary_to_violations(summary) == ()


def test_push_allowed_advisory_action_yields_no_violation() -> None:
    """`push_allowed` is healthy (push gate satisfied); no violation."""
    summary = _summary(
        advisory_action="push_allowed",
        advisory_reason="worktree_clean_and_review_accepted",
    )
    assert startup_summary_to_violations(summary) == ()


def test_no_push_needed_advisory_action_yields_no_violation() -> None:
    """`no_push_needed` is healthy (already at upstream); no violation."""
    summary = _summary(
        advisory_action="no_push_needed",
        advisory_reason="clean_worktree",
    )
    assert startup_summary_to_violations(summary) == ()


def test_multiple_blockers_emit_multiple_violations_in_stable_order() -> None:
    """Several blockers at once yield records in advisory/gate/push order.

    The shared renderer relies on stable ordering so the same startup
    state always renders the same way; the adapter walks advisory then
    reviewer_gate then push_decision in fixed order. This test mirrors
    the actual live shape today: budget exceeded -> repair_reviewer_loop
    or checkpoint_before_continue advisory + implementation_blocked +
    push.action=await_checkpoint.
    """
    summary = _summary(
        advisory_action="checkpoint_before_continue",
        advisory_reason="dirty_path_budget_exceeded",
        rule_summary="Startup blocks another implementation slice because the worktree has crossed the repo's continuation budget.",
        reviewer_gate={
            "bridge_active": True,
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
            "review_accepted": False,
            "implementation_blocked": True,
            "implementation_block_reason": "reviewer_heartbeat_stale",
            "recovery_action_id": "review-channel.relaunch",
            "recovery_command": "devctl review-channel --action launch",
            "operator_interaction_mode": "local_terminal",
        },
        push_decision={
            "action": "await_checkpoint",
            "reason": "dirty_path_budget_exceeded",
            "next_step_summary": "Checkpoint the slice.",
            "next_step_command": "",
        },
    )

    violations = startup_summary_to_violations(summary)

    assert [v.step_name for v in violations] == [
        "startup_authority",
        "reviewer_gate",
        "push_decision",
    ]
    assert all(v.source == "startup-context" for v in violations)


def test_missing_reviewer_gate_subdict_is_safe() -> None:
    """A summary without a reviewer_gate key must not raise; only present blockers project."""
    summary = {
        "advisory_action": "repair_reviewer_loop",
        "advisory_reason": "reviewer_heartbeat_stale",
        "push_decision": {"action": "no_push_needed"},
    }

    violations = startup_summary_to_violations(summary)

    assert len(violations) == 1
    assert violations[0].step_name == "startup_authority"


def test_missing_push_decision_subdict_is_safe() -> None:
    """A summary without a push_decision key must not raise; only present blockers project."""
    summary = {
        "advisory_action": "continue_editing",
        "advisory_reason": "",
        "reviewer_gate": {
            "implementation_blocked": True,
            "implementation_block_reason": "stale_reviewer",
            "reviewer_mode": "active_dual_agent",
            "recovery_command": "devctl review-channel --action launch",
        },
    }

    violations = startup_summary_to_violations(summary)

    assert len(violations) == 1
    assert violations[0].step_name == "reviewer_gate"
