"""Doctor/readiness helpers shared by review-channel status surfaces."""

from __future__ import annotations

import json
from pathlib import Path

from ...runtime.review_state_parser import review_state_from_payload
from .reviewer_runtime_snapshot import attach_reviewer_runtime_snapshot


def attach_status_runtime_snapshot(report: dict[str, object]) -> None:
    """Attach reviewer-runtime, doctor, and commit-pipeline snapshots when possible."""
    if (
        isinstance(report.get("reviewer_runtime"), dict)
        and isinstance(report.get("doctor"), dict)
        and isinstance(report.get("commit_pipeline"), dict)
        and "recovery_assessment" in report
    ):
        return

    review_state = _load_review_state_from_projection_paths(report)
    if review_state is None:
        return

    attention = report.get("attention") if isinstance(report.get("attention"), dict) else None
    attach_reviewer_runtime_snapshot(
        report,
        review_state=review_state,
        attention=attention,
    )


def resolve_status_recommended_command(
    status_report: dict[str, object],
) -> tuple[str, str]:
    """Return the single best next-step command from the typed status surface."""
    doctor = status_report.get("doctor")
    if isinstance(doctor, dict):
        command = str(doctor.get("recommended_command") or "").strip()
        if command:
            return command, "doctor"

    attention = status_report.get("attention")
    if isinstance(attention, dict):
        command = str(attention.get("recommended_command") or "").strip()
        if command:
            return command, "attention"

    push_decision = status_report.get("push_decision")
    if isinstance(push_decision, dict):
        command = str(push_decision.get("next_step_command") or "").strip()
        if command:
            return command, "push_decision"

    reviewer_runtime = status_report.get("reviewer_runtime")
    if isinstance(reviewer_runtime, dict):
        command = str(reviewer_runtime.get("recovery_action_allowed") or "").strip()
        if command:
            return command, "reviewer_runtime"

    return "", ""


def build_doctor_report(
    *,
    status_report: dict[str, object],
    exit_code: int,
) -> tuple[dict[str, object], int]:
    """Reduce the full status payload into the doctor/readiness surface."""
    doctor_report: dict[str, object] = {}
    doctor_report["command"] = "review-channel"
    doctor_report["timestamp"] = status_report.get("timestamp")
    doctor_report["action"] = "doctor"
    doctor_report["report_mode"] = status_report.get("report_mode")
    doctor_report["ok"] = status_report.get("ok", False)
    doctor_report["exit_ok"] = status_report.get("exit_ok", exit_code == 0)
    doctor_report["exit_code"] = exit_code
    doctor_report["execution_mode"] = status_report.get("execution_mode")
    doctor_report["terminal"] = status_report.get("terminal")
    doctor_report["warnings"] = list(status_report.get("warnings") or [])
    doctor_report["errors"] = list(status_report.get("errors") or [])
    doctor_report["attention"] = status_report.get("attention")
    doctor_report["recovery_assessment"] = status_report.get("recovery_assessment")
    doctor_report["doctor"] = status_report.get("doctor")
    doctor_report["reviewer_runtime"] = status_report.get("reviewer_runtime")
    doctor_report["commit_pipeline"] = status_report.get("commit_pipeline")
    doctor_report["coordination"] = status_report.get("coordination")
    doctor_report["projection_paths"] = status_report.get("projection_paths")
    doctor_report["service_identity"] = status_report.get("service_identity")
    doctor_report["attach_auth_policy"] = status_report.get("attach_auth_policy")
    doctor_report["push_decision"] = status_report.get("push_decision")
    recommended_command, command_source = resolve_status_recommended_command(
        status_report
    )
    doctor_report["recommended_command"] = recommended_command
    doctor_report["recommended_command_source"] = command_source

    for key in (
        "bridge_liveness",
        "publisher",
        "reviewer_supervisor",
        "reviewer_worker",
        "review_needed",
    ):
        if key in status_report:
            doctor_report[key] = status_report.get(key)

    return doctor_report, exit_code


def _load_review_state_from_projection_paths(report: dict[str, object]):
    projection_paths = report.get("projection_paths")
    if not isinstance(projection_paths, dict):
        return None

    review_state_path = projection_paths.get("review_state_path")
    if not review_state_path:
        return None

    try:
        payload = json.loads(Path(str(review_state_path)).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    return review_state_from_payload(payload)
