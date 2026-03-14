"""Structured review-state helpers for the Operator Console."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.runtime import (
    ReviewPacketState,
    ReviewState,
    review_state_from_payload,
)

from ...collaboration.context_pack_refs import parse_context_pack_refs
from ..core.models import ApprovalRequest

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


def load_review_contract(review_path: Path) -> ReviewState:
    """Load one review-channel JSON artifact into the shared runtime contract."""
    return parse_review_contract(load_json_object(review_path))


def load_review_packets(review_path: Path) -> tuple[ReviewPacketState, ...]:
    """Load typed review packets from a review-channel artifact path."""
    return load_review_contract(review_path).packets


def load_pending_approvals(review_state_path: Path) -> tuple[ApprovalRequest, ...]:
    """Load pending approval packets from a structured `review_state` JSON file."""
    return _approval_requests(load_review_packets(review_state_path))


def parse_pending_approvals(payload: dict[str, object]) -> tuple[ApprovalRequest, ...]:
    """Extract pending approval packets from a parsed review-state payload."""
    return _approval_requests(parse_review_packets(payload))


def parse_review_contract(payload: dict[str, object]) -> ReviewState:
    """Normalize review-channel JSON into the shared runtime contract."""
    contract = review_state_from_payload(payload)
    if contract is None:
        raise ValueError("review_state JSON is missing review-state fields")
    return contract


def parse_review_packets(payload: dict[str, object]) -> tuple[ReviewPacketState, ...]:
    """Extract typed review packets from a parsed review-channel payload."""
    return parse_review_contract(payload).packets


def _approval_requests(
    packets: tuple[ReviewPacketState, ...],
) -> tuple[ApprovalRequest, ...]:
    approvals: list[ApprovalRequest] = []
    for packet in packets:
        if not packet.requires_operator_approval():
            continue
        approvals.append(
            ApprovalRequest(
                packet_id=packet.packet_id or "(missing-packet-id)",
                from_agent=packet.from_agent or "(unknown)",
                to_agent=packet.to_agent or "(unknown)",
                summary=packet.summary or "(no summary)",
                body=packet.body,
                policy_hint=packet.policy_hint or "(unknown)",
                requested_action=packet.requested_action or "(unknown)",
                status=packet.status or "(unknown)",
                evidence_refs=packet.evidence_refs,
                context_pack_refs=parse_context_pack_refs(
                    [
                        {
                            "pack_kind": ref.pack_kind,
                            "pack_ref": ref.pack_ref,
                            "adapter_profile": ref.adapter_profile,
                            "generated_at_utc": ref.generated_at_utc,
                        }
                        for ref in packet.context_pack_refs
                    ]
                ),
            )
        )
    return tuple(approvals)
