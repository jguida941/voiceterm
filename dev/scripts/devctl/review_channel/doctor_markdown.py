"""Shared markdown projection for review-channel doctor surfaces."""

from __future__ import annotations


def append_doctor_markdown(lines: list[str], doctor: object) -> None:
    """Append the compact doctor/readiness section when a doctor payload exists."""
    if not isinstance(doctor, dict):
        return
    lines.append("")
    lines.append("## Doctor")
    lines.append(f"- status: {doctor.get('status') or 'unknown'}")
    lines.append(f"- summary: {doctor.get('summary') or 'n/a'}")
    lines.append(f"- publish_clear: {doctor.get('publish_clear')}")
    lines.append(f"- pipeline_state: {doctor.get('pipeline_state') or 'unknown'}")
    lines.append(f"- blocked_reason: {doctor.get('blocked_reason') or 'n/a'}")
    lines.append(f"- approval_state: {doctor.get('approval_state') or 'n/a'}")
    lines.append(f"- commit_ready: {doctor.get('commit_ready')}")
    lines.append(f"- push_ready: {doctor.get('push_ready')}")
