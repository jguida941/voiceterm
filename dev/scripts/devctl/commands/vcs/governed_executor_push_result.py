"""Push-result projection helpers for the governed VCS executor."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from ...runtime import ActionResult
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.remote_commit_pipeline_state import (
    AUTO_DELIVERY_TRANSITION_RULE,
    PUSH_FAILURE_CLASSIFICATION_NON_DESTRUCTIVE,
    STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
    classify_push_failure,
)
from .governed_executor_field_access import mapping, string_value
from .push_result_typestate import (
    PushFailed,
    PushPartialProgress,
    PushResult,
    PushSucceeded,
    action_result_for_push_result,
)


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
    push_report_path = string_value(mapping(report.get("artifacts")))
    artifacts: tuple[str, ...] = ()
    artifacts_dict = mapping(report.get("artifacts"))
    if artifacts_dict:
        push_report_json = string_value(artifacts_dict.get("push_report_json"))
        latest_json = string_value(artifacts_dict.get("latest_json"))
        paths = tuple(
            dict.fromkeys(
                path for path in (push_report_json, latest_json) if path
            )
        )
        if paths:
            artifacts = paths
            push_report_path = paths[0]
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
        artifact_paths=tuple(list(artifacts or ()) + [pipeline_artifact_relpath]),
        push_pipeline_phases=push_pipeline_phases,
        push_failure_transition=push_failure_transition,
        next_state=next_state,
        blocked_reason=blocked_reason,
    )


def apply_push_report_projection(
    pipeline: RemoteCommitPipelineContract,
    projection: PushReportProjection,
) -> RemoteCommitPipelineContract:
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
    pre_validation_recovery_loop_repair: dict[str, object] | None,
    post_validation_auto_commit_repair: dict[str, object] | None,
) -> dict[str, dict[str, object]]:
    """Return the report contract for push pipeline phase boundaries."""
    return {
        "pre_validation_managed_projection_sync": (
            pre_validation_managed_projection_sync
            or _default_phase("pre_validation_managed_projection_sync")
        ),
        "pre_validation_recovery_loop_repair": (
            pre_validation_recovery_loop_repair
            or _default_phase("pre_validation_recovery_loop_repair")
        ),
        "post_validation_auto_commit_repair": (
            post_validation_auto_commit_repair
            or _default_phase("post_validation_auto_commit_repair")
        ),
    }


def append_push_pipeline_phase_lines(lines: list[str], phase_state: object) -> None:
    """Append a compact markdown view of push pipeline phase state."""
    phase_state_mapping = mapping(phase_state)
    if not phase_state_mapping:
        return
    lines.append("")
    lines.append("## Push Pipeline Phases")
    lines.append("")
    for name in (
        "pre_validation_managed_projection_sync",
        "pre_validation_recovery_loop_repair",
        "post_validation_auto_commit_repair",
    ):
        phase = mapping(phase_state_mapping.get(name))
        if not phase:
            continue
        status = string_value(phase.get("status")) or "unknown"
        reason = string_value(phase.get("reason"))
        lines.append(f"- {name}: {status}")
        if reason:
            lines.append(f"- {name}_reason: {reason}")


def pipeline_push_result(
    *,
    action_id: str,
    report: Mapping[str, object],
) -> ActionResult:
    """Project one governed push report into the canonical ActionResult envelope."""
    return action_result_for_push_result(
        pipeline_push_result_case(action_id=action_id, report=report)
    )


def pipeline_push_result_case(
    *,
    action_id: str,
    report: Mapping[str, object],
) -> PushResult:
    """Project one governed push report into exhaustive push-result cases."""
    silent_failure = _silent_push_failure_reason(report)
    if silent_failure:
        return PushFailed(
            action_id=action_id,
            reason=silent_failure,
            operator_guidance=(
                "The push report does not contain enough subprocess evidence to "
                "prove remote publication. Rerun governed push after repairing "
                "the push report path."
            ),
        )
    stages = mapping(report.get("push_stages"))
    reason = string_value(report.get("reason"))
    published_remote = bool(stages.get("published_remote"))
    if _push_report_completed(report):
        return PushSucceeded(
            action_id=action_id,
            operator_guidance="Remote publication and post-push validation completed.",
        )
    if published_remote:
        return PushPartialProgress(
            action_id=action_id,
            reason=reason or "post_push_incomplete",
            operator_guidance=(
                "Remote publication succeeded, but post-push validation is not green yet."
            ),
        )
    return PushFailed(
        action_id=action_id,
        reason=string_value(report.get("reason")) or "push_failed",
        operator_guidance=string_value(
            mapping(report.get("action_result")).get("operator_guidance")
        )
        or "Inspect the push failure and retry through the governed path.",
    )


def _default_phase(name: str) -> dict[str, object]:
    return {"phase": name, "status": "not_run"}


def _silent_push_failure_reason(report: Mapping[str, object]) -> str:
    stages = mapping(report.get("push_stages"))
    if not bool(stages.get("published_remote")):
        return ""
    if string_value(report.get("reason")) == "branch_already_pushed":
        return ""
    if not bool(report.get("execute")):
        return ""
    push_step = mapping(report.get("push_step"))
    if not push_step:
        return "published_remote_without_push_step"
    try:
        push_returncode = int(str(push_step.get("returncode", 1)).strip() or "1")
    except (TypeError, ValueError):
        push_returncode = 1
    if push_returncode != 0:
        return "published_remote_push_step_failed"
    if not mapping(report.get("fetch_step")):
        return "published_remote_without_fetch_step"
    if not mapping(report.get("preflight_step")):
        return "published_remote_without_preflight_step"
    post_push_steps = report.get("post_push_steps")
    if not isinstance(post_push_steps, list) or not post_push_steps:
        return "published_remote_without_post_push_steps"
    return ""


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
