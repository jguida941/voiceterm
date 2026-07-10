"""Reviewer-duty packet and semantic review context builders."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PacketReviewContext:
    pending_packet_count: int
    last_packet_event_id: str
    last_packet_observed_at_utc: str
    current_head_sha: str
    staged_tree_hash: str


@dataclass(frozen=True, slots=True)
class SemanticReviewContext:
    worktree_hash: str
    changed_path_count: int
    reviewed_diff_hash: str
    reviewed_diff_base: str
    reviewed_path_count: int
    last_diff_review_at_utc: str
    source: str
    claimed: bool
    has_concrete_evidence: bool


def build_packet_review_context(
    bridge_liveness: Mapping[str, object],
) -> PacketReviewContext:
    return PacketReviewContext(
        pending_packet_count=_pending_packet_count(bridge_liveness),
        last_packet_event_id=str(
            bridge_liveness.get("last_packet_event_id")
            or bridge_liveness.get("last_packet_id")
            or ""
        ),
        last_packet_observed_at_utc=str(
            bridge_liveness.get("last_packet_observed_at_utc")
            or bridge_liveness.get("last_codex_poll_utc")
            or ""
        ),
        current_head_sha=str(
            bridge_liveness.get("head_at_push_time")
            or bridge_liveness.get("current_head_commit")
            or ""
        ),
        staged_tree_hash=str(bridge_liveness.get("staged_tree_hash") or ""),
    )


def build_semantic_review_context(
    agent_mind: Mapping[str, object] | None,
) -> SemanticReviewContext:
    payload = agent_mind or {}
    reviewed_diff_hash = str(payload.get("reviewed_diff_hash") or "")
    reviewed_diff_base = str(payload.get("reviewed_diff_base") or "")
    reviewed_path_count = int(payload.get("reviewed_path_count") or 0)
    last_diff_review_at_utc = str(payload.get("last_diff_review_at_utc") or "")
    semantic_review_claimed = bool(payload.get("semantic_review_claimed"))
    has_concrete_evidence = bool(
        reviewed_diff_hash and last_diff_review_at_utc and reviewed_path_count > 0
    )
    return SemanticReviewContext(
        worktree_hash=str(payload.get("worktree_hash") or ""),
        changed_path_count=int(payload.get("changed_path_count") or 0),
        reviewed_diff_hash=reviewed_diff_hash,
        reviewed_diff_base=reviewed_diff_base,
        reviewed_path_count=reviewed_path_count,
        last_diff_review_at_utc=last_diff_review_at_utc,
        source=_semantic_review_source(payload),
        claimed=semantic_review_claimed,
        has_concrete_evidence=has_concrete_evidence,
    )


def _semantic_review_source(agent_mind: Mapping[str, object]) -> str:
    keys = (
        "reviewed_diff_hash",
        "reviewed_diff_base",
        "reviewed_path_count",
        "last_diff_review_at_utc",
        "semantic_review_claimed",
    )
    if any(agent_mind.get(key) for key in keys):
        return "agent_mind_auxiliary"
    return ""


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _pending_packet_count(bridge_liveness: Mapping[str, object]) -> int:
    raw_count = bridge_liveness.get("pending_packet_count")
    mapped_count = _mapping(raw_count).get("total")
    return int(mapped_count or raw_count or 0)


__all__ = [
    "PacketReviewContext",
    "SemanticReviewContext",
    "build_packet_review_context",
    "build_semantic_review_context",
]
