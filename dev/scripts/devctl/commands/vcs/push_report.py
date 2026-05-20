"""Push report builders and render helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from ...governance.push_policy import PushPolicy
from .governed_executor_push_result import (
    append_push_pipeline_phase_lines,
    build_push_pipeline_phases,
)
from .push_diagnostics import build_push_diagnostic
from .push_findings import PushFindingPayload
from .push_report_artifacts import (
    append_push_report_artifact_lines,
    build_push_report_artifacts,
)
from .push_report_violations import _extract_preflight_violations


@dataclass(frozen=True, slots=True)
class PushStageTruth:
    """Typed push-stage truth for publish vs post-push reporting."""

    validation_ready: bool = False
    published_remote: bool = False
    post_push_green: bool = False

    def highest_stage(self) -> str:
        if self.post_push_green:
            return "post_push_green"
        if self.published_remote:
            return "published_remote"
        if self.validation_ready:
            return "validation_ready"
        return "blocked"


@dataclass(frozen=True, slots=True)
class PushReportInputs:
    """Structured inputs for one push report payload."""

    policy: PushPolicy
    branch: str
    remote: str
    head_commit: str
    execute: bool
    skip_preflight: bool
    skip_post_push: bool
    dirty_paths: list[str]
    fetch_step: dict[str, Any] | None
    preflight_step: dict[str, Any] | None
    push_step: dict[str, Any] | None
    post_push_steps: list[dict[str, Any]]
    push_stages: PushStageTruth
    typed_action: dict[str, Any]
    action_result: dict[str, Any]
    warnings: list[str]
    errors: list[str]
    findings: list[PushFindingPayload] | None = None
    artifact_path: str = ""
    git_mutation_proof_receipt_path: str = ""
    git_mutation_proof_verified: bool = False
    current_worktree_identity: str = ""
    approved_target_identity: str = ""
    approved_worktree_identity: str = ""
    push_authorization_id: str = ""
    push_authorization_mode: str = ""
    pre_validation_managed_projection_sync: dict[str, Any] | None = None
    pre_validation_recovery_loop_repair: dict[str, Any] | None = None
    post_validation_auto_commit_repair: dict[str, Any] | None = None


def build_push_report(inputs: PushReportInputs) -> dict[str, Any]:
    """Build the machine-readable push report payload."""
    report: dict[str, Any] = {}
    report["command"] = "push"
    report["timestamp"] = _timestamp()
    report["ok"] = bool(inputs.action_result.get("ok"))
    report["status"] = inputs.action_result.get("status")
    report["reason"] = inputs.action_result.get("reason")
    report["policy_path"] = inputs.policy.policy_path
    report["branch"] = inputs.branch
    report["remote"] = inputs.remote
    report["head_commit"] = inputs.head_commit
    report["execute"] = inputs.execute
    report["skip_preflight"] = inputs.skip_preflight
    report["skip_post_push"] = inputs.skip_post_push
    report["dirty_paths"] = inputs.dirty_paths
    report["fetch_step"] = inputs.fetch_step
    report["preflight_step"] = inputs.preflight_step
    report["push_step"] = inputs.push_step
    report["post_push_steps"] = inputs.post_push_steps
    report["push_stages"] = asdict(inputs.push_stages)
    report["published_remote"] = inputs.push_stages.published_remote
    report["post_push_green"] = inputs.push_stages.post_push_green
    governed_push_verified = _governed_push_verified(inputs)
    report["governed_push_verified"] = governed_push_verified
    report["publication_mode"] = _publication_mode(
        inputs,
        governed_push_verified=governed_push_verified,
    )
    report["operator_bypass_evidence_required"] = bool(
        inputs.push_stages.published_remote and not governed_push_verified
    )
    report["push_pipeline_phases"] = build_push_pipeline_phases(
        pre_validation_managed_projection_sync=(
            inputs.pre_validation_managed_projection_sync
        ),
        pre_validation_recovery_loop_repair=inputs.pre_validation_recovery_loop_repair,
        post_validation_auto_commit_repair=inputs.post_validation_auto_commit_repair,
    )
    report["push_diagnostic"] = build_push_diagnostic(
        execute=inputs.execute,
        push_stages=inputs.push_stages,
        reason=str(inputs.action_result.get("reason") or ""),
        errors=inputs.errors,
        push_step=inputs.push_step,
        post_push_steps=inputs.post_push_steps,
    )
    report["policy"] = _build_policy_summary(inputs.policy)
    report["typed_action"] = inputs.typed_action
    report["action_result"] = inputs.action_result
    report["violations"] = _extract_preflight_violations(
        inputs.preflight_step,
        report["timestamp"],
    )
    report["findings"] = list(inputs.findings or [])
    report["warnings"] = inputs.warnings
    report["errors"] = inputs.errors
    if inputs.current_worktree_identity:
        report["current_worktree_identity"] = inputs.current_worktree_identity
    if inputs.approved_target_identity:
        report["approved_target_identity"] = inputs.approved_target_identity
    if inputs.approved_worktree_identity:
        report["approved_worktree_identity"] = inputs.approved_worktree_identity
    if inputs.push_authorization_id:
        report["push_authorization_id"] = inputs.push_authorization_id
    if inputs.push_authorization_mode:
        report["push_authorization_mode"] = inputs.push_authorization_mode
    artifacts = build_push_report_artifacts(
        push_report_path=inputs.artifact_path,
        git_mutation_proof_receipt_path=inputs.git_mutation_proof_receipt_path,
    )
    if artifacts:
        report["artifacts"] = artifacts
    report["git_mutation_proof_verified"] = bool(
        inputs.git_mutation_proof_verified
    )
    return report


def render_push_report(report: dict[str, Any]) -> str:
    """Render the human-readable markdown report."""
    lines = ["# devctl push", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- status: {report.get('status')}")
    lines.append(f"- reason: {report.get('reason')}")
    lines.append(f"- branch: {report.get('branch')}")
    lines.append(f"- remote: {report.get('remote')}")
    lines.append(f"- head_commit: {report.get('head_commit')}")
    if report.get("current_worktree_identity"):
        lines.append(
            f"- current_worktree_identity: {report.get('current_worktree_identity')}"
        )
    if report.get("approved_target_identity"):
        lines.append(
            f"- approved_target_identity: {report.get('approved_target_identity')}"
        )
    if report.get("approved_worktree_identity"):
        lines.append(
            f"- approved_worktree_identity: {report.get('approved_worktree_identity')}"
        )
    if report.get("push_authorization_id"):
        lines.append(f"- push_authorization_id: {report.get('push_authorization_id')}")
    if report.get("push_authorization_mode"):
        lines.append(
            f"- push_authorization_mode: {report.get('push_authorization_mode')}"
        )
    lines.append(f"- execute: {report.get('execute')}")
    lines.append(f"- policy_path: {report.get('policy_path')}")
    warnings = report.get("warnings") or []
    errors = report.get("errors") or []
    lines.append(f"- warnings: {len(warnings)}")
    lines.append(f"- errors: {len(errors)}")
    artifacts = report.get("artifacts") or {}
    if artifacts:
        append_push_report_artifact_lines(lines, artifacts)
    lines.append("")
    lines.append("## Policy")
    lines.append("")
    policy = report.get("policy") or {}
    lines.append(
        f"- development_branch: {policy.get('development_branch', '(unknown)')}"
    )
    lines.append(f"- release_branch: {policy.get('release_branch', '(unknown)')}")
    lines.append(
        "- protected_branches: " + ", ".join(policy.get("protected_branches", []))
    )
    lines.append(
        "- allowed_branch_prefixes: "
        + ", ".join(policy.get("allowed_branch_prefixes", []))
    )
    bypass = policy.get("bypass") or {}
    lines.append(f"- allow_skip_preflight: {bypass.get('allow_skip_preflight', False)}")
    lines.append(f"- allow_skip_post_push: {bypass.get('allow_skip_post_push', False)}")
    push_stages = report.get("push_stages") or {}
    if push_stages:
        lines.append("")
        lines.append("## Push Stages")
        lines.append("")
        lines.append(f"- validation_ready: {push_stages.get('validation_ready')}")
        lines.append(f"- published_remote: {push_stages.get('published_remote')}")
        lines.append(f"- post_push_green: {push_stages.get('post_push_green')}")
        lines.append(f"- publication_mode: {report.get('publication_mode')}")
        lines.append(
            f"- governed_push_verified: {report.get('governed_push_verified')}"
        )
    append_push_pipeline_phase_lines(lines, report.get("push_pipeline_phases"))
    diagnostic = report.get("push_diagnostic") or {}
    if diagnostic:
        lines.append("")
        lines.append("## Push Diagnostic")
        lines.append("")
        for key in (
            "summary",
            "validation_state",
            "publication_state",
            "git_push_state",
            "post_push_state",
        ):
            lines.append(f"- {key}: {diagnostic.get(key)}")
    typed_action = report.get("typed_action") or {}
    if typed_action:
        lines.append("")
        lines.append("## Typed Action")
        lines.append("")
        for key in sorted(typed_action.keys()):
            lines.append(f"- {key}: {typed_action.get(key)}")
    action_result = report.get("action_result") or {}
    if action_result:
        lines.append("")
        lines.append("## Action Result")
        lines.append("")
        for key in sorted(action_result.keys()):
            lines.append(f"- {key}: {action_result.get(key)}")
    _append_step_section(lines, "Preflight", report.get("preflight_step"))
    _append_step_section(lines, "Push Step", report.get("push_step"))
    post_push_steps = report.get("post_push_steps") or []
    if post_push_steps:
        lines.append("")
        lines.append("## Post Push")
        lines.append("")
        for step in post_push_steps:
            lines.extend(_render_step_lines(step))
    if warnings:
        lines.append("")
        lines.append("## Warnings")
        lines.append("")
        lines.extend(f"- {warning}" for warning in warnings)
    if errors:
        lines.append("")
        lines.append("## Errors")
        lines.append("")
        lines.extend(f"- {error}" for error in errors)
    findings = report.get("findings") or []
    if findings:
        lines.append("")
        lines.append("## Findings")
        lines.append("")
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            finding_type = finding.get("type", "Finding")
            message = finding.get("message", "")
            lines.append(f"- {finding_type}: {message}")
    return "\n".join(lines)


def _append_step_section(
    lines: list[str],
    title: str,
    step: dict[str, Any] | None,
) -> None:
    if not step:
        return
    lines.append("")
    lines.append(f"## {title}")
    lines.append("")
    lines.extend(_render_step_lines(step))


def _build_policy_summary(policy: PushPolicy) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    summary["development_branch"] = policy.development_branch
    summary["release_branch"] = policy.release_branch
    summary["protected_branches"] = list(policy.protected_branches)
    summary["allowed_branch_prefixes"] = list(policy.allowed_branch_prefixes)
    summary["bypass"] = {
        "allow_skip_preflight": policy.bypass.allow_skip_preflight,
        "allow_skip_post_push": policy.bypass.allow_skip_post_push,
    }
    return summary


def _render_step_lines(step: dict[str, Any]) -> list[str]:
    command = " ".join(str(part) for part in step.get("cmd", []))
    lines = [f"- {step.get('name')}: rc={step.get('returncode')} cmd=`{command}`"]
    failure_output = step.get("failure_output")
    if failure_output:
        lines.append(f"  failure_output: {failure_output}")
    return lines


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _governed_push_verified(inputs: PushReportInputs) -> bool:
    if not inputs.push_stages.published_remote:
        return False
    reason = str(inputs.action_result.get("reason") or "")
    if reason == "branch_already_pushed" and inputs.execute:
        return True
    push_step = inputs.push_step
    if not isinstance(push_step, dict):
        return False
    try:
        return (
            int(push_step.get("returncode")) == 0
            and inputs.git_mutation_proof_verified
        )
    except (TypeError, ValueError):
        return False


def _publication_mode(
    inputs: PushReportInputs,
    *,
    governed_push_verified: bool,
) -> str:
    if governed_push_verified:
        return "governed_push"
    if inputs.push_stages.published_remote:
        return "raw_no_verify"
    if inputs.push_stages.validation_ready:
        return "validation_only"
    return "not_published"
