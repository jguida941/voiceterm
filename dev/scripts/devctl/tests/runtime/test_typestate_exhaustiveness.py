"""P102 typestate exhaustiveness fixture."""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Literal, assert_never

from dev.scripts.devctl.commands.vcs.governed_executor_push_result import (
    pipeline_push_result_case,
)
from dev.scripts.devctl.commands.vcs.push_result_typestate import (
    PushFailed,
    PushPartialProgress,
    PushSucceeded,
    action_result_for_push_result,
)
from dev.scripts.devctl.runtime.lifetime_bypass_mode import (
    BypassActivated,
    BypassAuthorityScope,
    BypassDenied,
    BypassEvaluationInput,
    BypassLifecycleState,
    BypassRequest,
    bypass_activation_lifecycle,
    evaluate_bypass_activation,
)
from dev.scripts.devctl.runtime.session_termination_policy import (
    CONTINUATION_ANCHOR_MISSING_ERROR,
    PACKET_ATTENTION_PENDING_ERROR,
    TaskCompleteDecision,
)
from dev.scripts.devctl.runtime.task_complete_result import (
    TaskCompleteContinuationActive,
    TaskCompleteContinuationMissing,
    TaskCompletePacketAttentionPending,
    TaskCompleteTerminated,
    task_complete_result,
    task_complete_result_reason,
)

LifecycleState = Literal["requested", "active", "expired"]


@dataclass(frozen=True)
class LifecycleReceiptFixture:
    receipt_id: str
    state: LifecycleState


def render_lifecycle_state(receipt: LifecycleReceiptFixture) -> str:
    match receipt.state:
        case "requested":
            return "waiting_for_activation"
        case "active":
            return "usable"
        case "expired":
            return "closed"
    assert_never(receipt.state)


class TypestateExhaustivenessTests(unittest.TestCase):
    def test_render_lifecycle_state_handles_every_literal_state(self) -> None:
        cases: tuple[tuple[LifecycleState, str], ...] = (
            ("requested", "waiting_for_activation"),
            ("active", "usable"),
            ("expired", "closed"),
        )

        for state, expected in cases:
            receipt = LifecycleReceiptFixture(
                receipt_id=f"receipt:{state}",
                state=state,
            )
            self.assertEqual(render_lifecycle_state(receipt), expected)

    def test_bypass_activation_result_is_discriminated(self) -> None:
        activated = evaluate_bypass_activation(
            _bypass_request("typestate-active"),
            _bypass_evidence(),
        )
        if not isinstance(activated, BypassActivated):
            self.fail(f"expected activated result, got {activated!r}")
        self.assertIs(activated.lifecycle.state, BypassLifecycleState.ACTIVE)
        self.assertEqual(
            bypass_activation_lifecycle(activated),
            activated.lifecycle,
        )

        denied = evaluate_bypass_activation(
            _bypass_request("typestate-denied"),
            _bypass_evidence(operator_signature=""),
        )
        if not isinstance(denied, BypassDenied):
            self.fail(f"expected denied result, got {denied!r}")
        self.assertEqual(denied.reason, "operator_signature_required")
        self.assertEqual(
            bypass_activation_lifecycle(denied),
            denied.lifecycle,
        )

    def test_push_result_cases_project_to_action_result(self) -> None:
        completed_report: dict[str, object] = {
            "push_stages": {
                "published_remote": True,
                "post_push_green": True,
            },
        }
        completed = pipeline_push_result_case(
            action_id="push:complete",
            report=completed_report,
        )
        self.assertIsInstance(completed, PushSucceeded)
        completed_action = action_result_for_push_result(completed)
        self.assertTrue(completed_action.ok)
        self.assertEqual(completed_action.reason, "push_completed")

        partial_report: dict[str, object] = {
            "reason": "post_push_incomplete",
            "push_stages": {
                "published_remote": True,
                "post_push_green": False,
            },
        }
        partial = pipeline_push_result_case(
            action_id="push:partial",
            report=partial_report,
        )
        self.assertIsInstance(partial, PushPartialProgress)
        partial_action = action_result_for_push_result(partial)
        self.assertFalse(partial_action.ok)
        self.assertTrue(partial_action.partial_progress)

        failed = pipeline_push_result_case(
            action_id="push:failed",
            report={"reason": "git_push_failed"},
        )
        self.assertIsInstance(failed, PushFailed)
        failed_action = action_result_for_push_result(failed)
        self.assertFalse(failed_action.ok)
        self.assertEqual(failed_action.reason, "git_push_failed")

    def test_task_complete_result_cases_are_discriminated(self) -> None:
        continuation = task_complete_result(
            TaskCompleteDecision(
                terminate=False,
                reason="continuation_anchor_active",
            )
        )
        self.assertIsInstance(continuation, TaskCompleteContinuationActive)
        self.assertEqual(
            task_complete_result_reason(continuation),
            "continuation_anchor_active",
        )

        missing = task_complete_result(
            TaskCompleteDecision(
                terminate=False,
                reason=CONTINUATION_ANCHOR_MISSING_ERROR,
                error_kind=CONTINUATION_ANCHOR_MISSING_ERROR,
            )
        )
        self.assertIsInstance(missing, TaskCompleteContinuationMissing)

        packet_attention = task_complete_result(
            TaskCompleteDecision(
                terminate=False,
                reason=PACKET_ATTENTION_PENDING_ERROR,
                error_kind=PACKET_ATTENTION_PENDING_ERROR,
            )
        )
        self.assertIsInstance(packet_attention, TaskCompletePacketAttentionPending)

        terminated = task_complete_result(TaskCompleteDecision())
        self.assertIsInstance(terminated, TaskCompleteTerminated)


def _bypass_request(request_id: str) -> BypassRequest:
    return BypassRequest(
        request_id=request_id,
        scope=BypassAuthorityScope.EDIT_ONLY,
        reason="Operator approved typestate test bypass.",
        actor="operator",
        requested_at_utc="2026-05-13T18:00:00Z",
        target_role="implementer",
        target_session_id="session-typestate",
        target_surface="typestate-test",
    )


def _bypass_evidence(operator_signature: str = "operator") -> BypassEvaluationInput:
    return BypassEvaluationInput(
        operator_signature=operator_signature,
        ai_approval_evidence="packet:rev_pkt_typestate",
        evaluated_at_utc="2026-05-13T18:01:00Z",
        evaluator_actor_id="codex",
    )
