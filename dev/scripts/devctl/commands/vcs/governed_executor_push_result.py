"""Push-result projection helpers for the governed VCS executor."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from ...runtime import ActionResult
from ...runtime.action_contracts import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionOutcome,
)
from ...runtime.remote_commit_pipeline_state import (
    AUTO_DELIVERY_TRANSITION_RULE,
    PUSH_FAILURE_CLASSIFICATION_NON_DESTRUCTIVE,
    STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
    classify_push_failure,
)
from .governed_executor_field_access import mapping, string_value


@dataclass(frozen=True, slots=True)
class PushReportProjection:
    """Derived pipeline-state fields from a push report."""

    push_result: ActionResult
    push_report_path: str
    artifact_paths: tuple[str, ...]
    push_pipeline_phases: dict[str, object]
    push_failure_transition: dict[str, object]
    next_state: str
    blocked_reason: str


def project_push_report(
    *,
    action_id: str,
    report: Mapping[str, object],
    pipeline_artifact_relpath: str,
    pipeline_state: str = "",
    local_commit_landed: bool = False,
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
    push_pipeline_phases = dict(mapping(report.get("push_pipeline_phases")))

    push_completed = _push_report_completed(report)
    failure_classification = classify_push_failure(report)
    push_reason = string_value(report.get("reason"))
    auto_transition = (
        not push_completed
        and local_commit_landed
        and failure_classification == PUSH_FAILURE_CLASSIFICATION_NON_DESTRUCTIVE
    )
    next_state = _next_pipeline_state(
        push_completed=push_completed,
        auto_transition=auto_transition,
    )
    blocked_reason = "" if next_state != "push_blocked" else push_reason
    push_failure_transition = _push_failure_transition(
        report=report,
        classification=failure_classification,
        previous_state=pipeline_state,
        next_state=next_state,
        auto_transition=auto_transition,
    )
    return PushReportProjection(
        push_result=push_result,
        push_report_path=push_report_path,
        artifact_paths=tuple(
            list(artifacts or ()) + [pipeline_artifact_relpath]
        ),
        push_pipeline_phases=push_pipeline_phases,
        push_failure_transition=push_failure_transition,
        next_state=next_state,
        blocked_reason=blocked_reason,
    )


def apply_push_report_projection(pipeline, projection: PushReportProjection):
    """Return a pipeline updated from one push-report projection."""
    return replace(
        pipeline,
        state=projection.next_state,
        push_result=projection.push_result,
        push_pipeline_phases=projection.push_pipeline_phases,
        push_failure_transition=projection.push_failure_transition,
        push_report_path=projection.push_report_path,
        blocked_reason=projection.blocked_reason,
    )


def build_push_pipeline_phases(
    *,
    pre_validation_managed_projection_sync: dict[str, object] | None,
    post_validation_auto_commit_repair: dict[str, object] | None,
) -> dict[str, dict[str, object]]:
    """Return the report contract for push pipeline phase boundaries."""
    return {
        "pre_validation_managed_projection_sync": (
            pre_validation_managed_projection_sync
            or _default_phase("pre_validation_managed_projection_sync")
        ),
        "post_validation_auto_commit_repair": (
            post_validation_auto_commit_repair
            or _default_phase("post_validation_auto_commit_repair")
        ),
    }


def append_push_pipeline_phase_lines(lines: list[str], phase_state: object) -> None:
    """Append a compact markdown view of push pipeline phase state."""
    if not isinstance(phase_state, dict) or not phase_state:
        return
    lines.append("")
    lines.append("## Push Pipeline Phases")
    lines.append("")
    for name in (
        "pre_validation_managed_projection_sync",
        "post_validation_auto_commit_repair",
    ):
        phase = phase_state.get(name) or {}
        if not isinstance(phase, dict):
            continue
        lines.append(f"- {name}: {phase.get('status', 'unknown')}")
        if phase.get("reason"):
            lines.append(f"- {name}_reason: {phase.get('reason')}")


def pipeline_push_result(
    *,
    action_id: str,
    report: Mapping[str, object],
) -> ActionResult:
    """Project one governed push report into an ActionResult."""
    stages = mapping(report.get("push_stages"))
    reason = string_value(report.get("reason"))
    published_remote = bool(stages.get("published_remote"))
    post_push_green = bool(stages.get("post_push_green"))
    if _push_report_completed(report):
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
            reason=reason or "post_push_incomplete",
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


def _default_phase(name: str) -> dict[str, object]:
    return {"phase": name, "status": "not_run"}


def _push_report_completed(report: Mapping[str, object]) -> bool:
    """Return true only when the push report proves full post-push completion."""
    stages = mapping(report.get("push_stages"))
    if not bool(stages.get("published_remote")):
        return False
    return bool(stages.get("post_push_green"))


def _next_pipeline_state(*, push_completed: bool, auto_transition: bool) -> str:
    if push_completed:
        return "push_completed"
    if auto_transition:
        return STATE_DELIVERED_LOCALLY_PENDING_PUBLISH
    return "push_blocked"


def _push_failure_transition(
    *,
    report: Mapping[str, object],
    classification: str,
    previous_state: str,
    next_state: str,
    auto_transition: bool,
) -> dict[str, object]:
    reason = string_value(report.get("reason"))
    if next_state == "push_completed":
        return {}
    stages = mapping(report.get("push_stages"))
    transition: dict[str, object] = {}
    transition["rule"] = AUTO_DELIVERY_TRANSITION_RULE
    transition["classification"] = classification
    transition["previous_state"] = previous_state
    transition["new_state"] = next_state
    transition["reason"] = (
        "non_destructive_push_failure_local_commit_delivered"
        if auto_transition
        else "push_failure_requires_explicit_reconciliation"
    )
    transition["push_reason"] = reason or "push_failed"
    transition["validation_ready"] = bool(stages.get("validation_ready"))
    transition["published_remote"] = bool(stages.get("published_remote"))
    transition["post_push_green"] = bool(stages.get("post_push_green"))
    transition["auto_transitioned"] = auto_transition
    return transition
