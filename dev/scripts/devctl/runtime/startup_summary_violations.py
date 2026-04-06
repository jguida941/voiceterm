"""Adapter mapping startup-context blockers into ViolationRecord.

The startup-context surface emits a typed ``StartupContext`` packet whose
``reviewer_gate``, ``push_decision``, ``advisory_action`` / ``advisory_reason``,
and (optionally) ``quality_signals`` fields together describe whether the
session is allowed to keep editing, has to checkpoint, has to wait for
review, or has to repair. Each blocking condition is the start of the
operator's "what do I need to do next" loop.

This adapter projects each blocking condition into one ``ViolationRecord``
so dashboard, startup-summary, and other operator surfaces can render
startup blockers through the same shared
``CheckResult`` / ``ViolationRecord`` renderer
(``render_check_result_text`` / ``render_check_result_md``) as checks,
probes, and governance-review. The probe and governance-review adapters
already follow this pattern; this module is the third sibling for the
startup-summary surface required by MP-381.

The mapping is one-way and non-mutating: ``StartupContext`` keeps its own
typed contract; this adapter only adds a new consumer for the shared
renderer. The output is intentionally empty when nothing is blocking, so
healthy startup states render as zero violations rather than synthetic
"all clear" rows.
"""

from __future__ import annotations

from typing import Any, Mapping

from .check_result_models import ViolationRecord
from .violation_adapter_support import (
    build_bounded_summary,
    coerce_stripped_str,
)

# Advisory actions that represent a *blocking* startup state. The
# canonical action enum lives in ``startup_advisory_decision.py``; the
# healthy values (``continue_editing``, ``push_allowed``,
# ``checkpoint_allowed``, ``no_push_needed``) are intentionally excluded
# because they do not demand operator attention before the next
# governed step. The blocking values are:
#
# - ``await_review``: bridge active, worktree clean, reviewer acceptance
#   still pending; the operator (or implementer) must wait for review
#   instead of widening the slice.
# - ``checkpoint_before_continue``: ``push.checkpoint_required`` is set
#   or the worktree continuation budget is exceeded; the operator must
#   commit/clean before any further governed step.
# - ``repair_reviewer_loop``: reviewer-owned state has marked the live
#   collaboration loop as blocked; the operator must repair the reviewer
#   loop before further implementation work.
_BLOCKING_ADVISORY_ACTIONS: frozenset[str] = frozenset(
    {
        "await_review",
        "checkpoint_before_continue",
        "repair_reviewer_loop",
    }
)

# Push-decision actions that represent a wait/blocked state on the
# publication path. ``run_devctl_push`` and ``no_push_needed`` are
# non-blocking and intentionally excluded.
_BLOCKING_PUSH_DECISION_ACTIONS: frozenset[str] = frozenset(
    {
        "await_checkpoint",
        "await_review",
    }
)


def startup_summary_to_violations(
    summary: Mapping[str, Any],
) -> tuple[ViolationRecord, ...]:
    """Convert one startup-context dict projection into ViolationRecord tuples.

    Reads the dict produced by ``StartupContext.to_dict()`` and emits one
    ``ViolationRecord`` per blocking condition the operator should see:

    - ``advisory_action`` is one of ``repair`` / ``await_review`` /
      ``await_checkpoint`` (the typed startup-authority verdict)
    - ``reviewer_gate.implementation_blocked`` is true (the reviewer
      loop is gating new implementation work)
    - ``push_decision.action`` is one of ``await_checkpoint`` /
      ``await_review`` (the publication path is waiting on the operator)

    Healthy states (advisory_action ``continue_editing`` /
    ``checkpoint_allowed``, no implementation block, no pending push
    decision) yield an empty tuple. Non-dict input also yields an empty
    tuple so a malformed payload cannot break the renderer.
    """
    if not isinstance(summary, Mapping):
        return ()

    records: list[ViolationRecord] = []
    advisory_record = _advisory_violation(summary)
    if advisory_record is not None:
        records.append(advisory_record)
    gate_record = _reviewer_gate_violation(summary)
    if gate_record is not None:
        records.append(gate_record)
    push_record = _push_decision_violation(summary)
    if push_record is not None:
        records.append(push_record)
    return tuple(records)


def _advisory_violation(
    summary: Mapping[str, Any],
) -> ViolationRecord | None:
    """Build a violation for a blocking ``advisory_action`` if present."""
    action = coerce_stripped_str(summary.get("advisory_action"))
    if action not in _BLOCKING_ADVISORY_ACTIONS:
        return None
    reason = coerce_stripped_str(summary.get("advisory_reason"))
    rule_summary = coerce_stripped_str(summary.get("rule_summary"))
    return ViolationRecord(
        step_name="startup_authority",
        exit_code=0,
        summary=build_bounded_summary(
            primary_text=reason,
            fallback_labels=(rule_summary, action),
            prefix=f"{action}: " if action else "",
            default=action or "startup blocker",
        ),
        error="",
        failure_output=rule_summary,
        file_path="",
        line=0,
        policy="startup_authority",
        fix=rule_summary,
        source="startup-context",
        severity="high",
    )


def _reviewer_gate_violation(
    summary: Mapping[str, Any],
) -> ViolationRecord | None:
    """Build a violation for a reviewer-gate implementation block if present."""
    gate = summary.get("reviewer_gate")
    if not isinstance(gate, Mapping):
        return None
    if not bool(gate.get("implementation_blocked")):
        return None
    reason = coerce_stripped_str(gate.get("implementation_block_reason"))
    reviewer_mode = coerce_stripped_str(gate.get("reviewer_mode"))
    recovery_command = coerce_stripped_str(gate.get("recovery_command"))
    recovery_action = coerce_stripped_str(gate.get("recovery_action_id"))
    return ViolationRecord(
        step_name="reviewer_gate",
        exit_code=0,
        summary=build_bounded_summary(
            primary_text=reason,
            fallback_labels=(recovery_action, reviewer_mode),
            prefix="implementation_blocked: ",
            default="implementation_blocked",
        ),
        error="",
        failure_output="",
        file_path="",
        line=0,
        policy="reviewer_gate",
        fix=recovery_command,
        source="startup-context",
        severity="high",
    )


def _push_decision_violation(
    summary: Mapping[str, Any],
) -> ViolationRecord | None:
    """Build a violation for a blocking ``push_decision`` action if present."""
    push = summary.get("push_decision")
    if not isinstance(push, Mapping):
        return None
    action = coerce_stripped_str(push.get("action"))
    if action not in _BLOCKING_PUSH_DECISION_ACTIONS:
        return None
    reason = coerce_stripped_str(push.get("reason"))
    next_step_summary = coerce_stripped_str(push.get("next_step_summary"))
    next_step_command = coerce_stripped_str(push.get("next_step_command"))
    return ViolationRecord(
        step_name="push_decision",
        exit_code=0,
        summary=build_bounded_summary(
            primary_text=reason,
            fallback_labels=(next_step_summary, action),
            prefix=f"{action}: " if action else "",
            default=action or "push blocked",
        ),
        error="",
        failure_output=next_step_summary,
        file_path="",
        line=0,
        policy="push_state_machine",
        fix=next_step_command,
        source="startup-context",
        severity="medium",
    )


__all__ = [
    "startup_summary_to_violations",
]
