"""Push-result projection helpers for the governed VCS executor."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ...runtime import ActionResult
from ...runtime.action_contracts import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionOutcome,
)
from .governed_executor_field_access import mapping, string_value


@dataclass(frozen=True, slots=True)
class PushReportProjection:
    """Derived pipeline-state fields from a push report."""

    push_result: ActionResult
    push_report_path: str
    artifact_paths: tuple[str, ...]
    next_state: str
    blocked_reason: str


def project_push_report(
    *,
    action_id: str,
    report: Mapping[str, object],
    pipeline_artifact_relpath: str,
) -> PushReportProjection:
    """Extract pipeline state transition fields from a push report dict."""
    push_result = pipeline_push_result(action_id=action_id, report=report)
    push_report_path = string_value(
        mapping(report.get("artifacts")) if isinstance(report, dict) else {}
    )
    artifacts: tuple[str, ...] = ()
    if isinstance(report, dict):
        artifacts_dict = report.get("artifacts")
        if isinstance(artifacts_dict, dict):
            latest_json = string_value(artifacts_dict.get("latest_json"))
            if latest_json:
                artifacts = (latest_json,)
                push_report_path = latest_json

    stages = report.get("push_stages", {}) if isinstance(report, dict) else {}
    push_completed = bool(
        isinstance(stages, dict)
        and stages.get("published_remote")
        and stages.get("post_push_green")
    )
    next_state = "push_completed" if push_completed else "push_blocked"
    blocked_reason = "" if push_completed else string_value(report.get("reason"))
    return PushReportProjection(
        push_result=push_result,
        push_report_path=push_report_path,
        artifact_paths=tuple(
            list(artifacts or ()) + [pipeline_artifact_relpath]
        ),
        next_state=next_state,
        blocked_reason=blocked_reason,
    )


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
