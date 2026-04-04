"""Shared markdown projection for review-channel doctor surfaces."""

from __future__ import annotations


def append_doctor_markdown(lines: list[str], doctor: object) -> None:
    """Append the compact doctor/readiness section when a doctor payload exists."""
    if not isinstance(doctor, dict):
        return
    lines.append("")
    lines.append("## Doctor")
    lines.append(f"- status: {doctor.get('status') or 'unknown'}")
    diagnosis_status = doctor.get("diagnosis_status")
    if diagnosis_status:
        lines.append(f"- diagnosis_status: {diagnosis_status}")
    lines.append(f"- summary: {doctor.get('summary') or 'n/a'}")
    if doctor.get("decision_action_id"):
        lines.append(f"- decision_action_id: {doctor.get('decision_action_id')}")
    if doctor.get("decision_command"):
        lines.append(f"- decision_command: {doctor.get('decision_command')}")
    lines.append(f"- publish_clear: {doctor.get('publish_clear')}")
    lines.append(f"- publisher_running: {doctor.get('publisher_running')}")
    lines.append(
        "- publisher_last_heartbeat_utc: "
        f"{doctor.get('publisher_last_heartbeat_utc') or 'n/a'}"
    )
    lines.append(
        f"- publisher_stop_reason: {doctor.get('publisher_stop_reason') or 'n/a'}"
    )
    lines.append(
        f"- reviewer_supervisor_running: {doctor.get('reviewer_supervisor_running')}"
    )
    lines.append(
        "- reviewer_supervisor_last_heartbeat_utc: "
        f"{doctor.get('reviewer_supervisor_last_heartbeat_utc') or 'n/a'}"
    )
    lines.append(
        "- reviewer_supervisor_stop_reason: "
        f"{doctor.get('reviewer_supervisor_stop_reason') or 'n/a'}"
    )
    lines.append(f"- pipeline_state: {doctor.get('pipeline_state') or 'unknown'}")
    lines.append(f"- blocked_reason: {doctor.get('blocked_reason') or 'n/a'}")
    lines.append(f"- approval_state: {doctor.get('approval_state') or 'n/a'}")
    lines.append(f"- commit_ready: {doctor.get('commit_ready')}")
    lines.append(f"- push_ready: {doctor.get('push_ready')}")
