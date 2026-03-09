"""Structured review-state helpers for the Operator Console."""

from __future__ import annotations

import json
from pathlib import Path

from .models import ApprovalRequest

DEFAULT_REVIEW_STATE_CANDIDATES = (
    "dev/reports/review_channel/projections/latest/review_state.json",
    "dev/reports/review_channel/latest/review_state.json",
    "dev/reports/review_channel/review_state.json",
)
DEFAULT_REVIEW_FULL_CANDIDATES = (
    "dev/reports/review_channel/projections/latest/full.json",
    "dev/reports/review_channel/latest/full.json",
)


def find_review_state_path(repo_root: Path) -> Path | None:
    """Return the first known structured review-state path that exists."""
    for relative_path in DEFAULT_REVIEW_STATE_CANDIDATES:
        candidate = repo_root / relative_path
        if candidate.exists():
            return candidate
    return None


def find_review_full_path(repo_root: Path) -> Path | None:
    """Return the first known review-channel full projection path that exists."""
    for relative_path in DEFAULT_REVIEW_FULL_CANDIDATES:
        candidate = repo_root / relative_path
        if candidate.exists():
            return candidate
    return None


def load_json_object(path: Path) -> dict[str, object]:
    """Load a JSON object from disk and fail closed on non-object payloads."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def load_pending_approvals(review_state_path: Path) -> tuple[ApprovalRequest, ...]:
    """Load pending approval packets from a structured `review_state` JSON file."""
    payload = load_json_object(review_state_path)
    return parse_pending_approvals(payload)


def parse_pending_approvals(payload: dict[str, object]) -> tuple[ApprovalRequest, ...]:
    """Extract pending approval packets from a parsed review-state payload."""
    packets = payload.get("packets")
    if not isinstance(packets, list):
        raise ValueError("review_state JSON is missing a packets list")

    approvals: list[ApprovalRequest] = []
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if not packet.get("approval_required"):
            continue
        if packet.get("status") != "pending":
            continue
        approvals.append(
            ApprovalRequest(
                packet_id=str(packet.get("packet_id", "(missing-packet-id)")),
                from_agent=str(packet.get("from_agent", "(unknown)")),
                to_agent=str(packet.get("to_agent", "(unknown)")),
                summary=str(packet.get("summary", "(no summary)")),
                body=str(packet.get("body", "")),
                policy_hint=str(packet.get("policy_hint", "(unknown)")),
                requested_action=str(packet.get("requested_action", "(unknown)")),
                status=str(packet.get("status", "(unknown)")),
                evidence_refs=tuple(
                    str(item)
                    for item in packet.get("evidence_refs", [])
                    if isinstance(item, str)
                ),
            )
        )
    return tuple(approvals)
