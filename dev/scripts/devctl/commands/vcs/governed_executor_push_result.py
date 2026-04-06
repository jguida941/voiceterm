"""Push-result projection helpers for the governed VCS executor."""

from __future__ import annotations

from collections.abc import Mapping

from ...runtime import ActionResult
from ...runtime.action_contracts import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionOutcome,
)
from .governed_executor_field_access import mapping, string_value


def pipeline_push_result(
    *,
    action_id: str,
    report: Mapping[str, object],
) -> ActionResult:
    """Project one governed push report into an ActionResult."""
    stages = mapping(report.get("push_stages"))
    published_remote = bool(stages.get("published_remote"))
    post_push_green = bool(stages.get("post_push_green"))
    if published_remote and post_push_green:
        return ActionResult(
            schema_version=ACTION_RESULT_SCHEMA_VERSION,
            contract_id=ACTION_RESULT_CONTRACT_ID,
            action_id=action_id,
            ok=True,
            status=ActionOutcome.PASS,
            reason="push_completed",
            operator_guidance="Remote publication and post-push validation completed.",
        )
    if published_remote:
        return ActionResult(
            schema_version=ACTION_RESULT_SCHEMA_VERSION,
            contract_id=ACTION_RESULT_CONTRACT_ID,
            action_id=action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason=string_value(report.get("reason")) or "post_push_incomplete",
            retryable=True,
            partial_progress=True,
            operator_guidance=(
                "Remote publication succeeded, but post-push validation is not green yet."
            ),
        )
    return ActionResult(
        schema_version=ACTION_RESULT_SCHEMA_VERSION,
        contract_id=ACTION_RESULT_CONTRACT_ID,
        action_id=action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason=string_value(report.get("reason")) or "push_failed",
        retryable=True,
        operator_guidance=string_value(
            mapping(report.get("action_result")).get("operator_guidance")
        )
        or "Inspect the push failure and retry through the governed path.",
    )
