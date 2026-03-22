"""Runtime-state helpers for the implementer wait loop."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..review_channel_command import RuntimePaths
from ._bridge_poll import BridgePollResult, build_bridge_poll_result
from ._wait_support import (
    latest_pending_packet_id,
    load_pending_claude_packets,
    validate_wait_bridge_content,
)

if TYPE_CHECKING:
    from ._wait import ImplementerWaitDeps


@dataclass(frozen=True, slots=True)
class WaitAttentionSnapshot:
    """Typed attention fields extracted from a status report."""

    status: str
    summary: str
    recommended_action: str


@dataclass(frozen=True, slots=True)
class WaitRuntimeState:
    """Typed runtime state needed to build a wait snapshot."""

    poll_result: BridgePollResult
    pending_packet_id: str
    exit_code: int
    attention: WaitAttentionSnapshot


def read_wait_runtime_state(
    *,
    report: Mapping[str, object],
    exit_code: int,
    repo_root: Path,
    paths: RuntimePaths,
    deps: "ImplementerWaitDeps",
) -> WaitRuntimeState:
    bridge_text = deps.read_bridge_text_fn(paths.bridge_path)
    poll_result = _poll_bridge_state(bridge_text=bridge_text, deps=deps)
    pending_packet_id = _latest_pending_packet_id(
        repo_root=repo_root,
        paths=paths,
        deps=deps,
    )

    return WaitRuntimeState(
        poll_result=poll_result,
        pending_packet_id=pending_packet_id,
        exit_code=_validated_exit_code(
            bridge_text=bridge_text,
            exit_code=exit_code,
        ),
        attention=_extract_attention_snapshot(report),
    )


def _poll_bridge_state(
    *,
    bridge_text: str,
    deps: "ImplementerWaitDeps",
) -> BridgePollResult:
    # Route fully through typed bridge-poll for revision, ACK, and update
    # detection. Raw markdown parsing is no longer used in the normal path.
    poll_fn = deps.bridge_poll_fn or build_bridge_poll_result
    return poll_fn(bridge_text)


def _latest_pending_packet_id(
    *,
    repo_root: Path,
    paths: RuntimePaths,
    deps: "ImplementerWaitDeps",
) -> str:
    pending_packets_fn = deps.pending_packets_fn or load_pending_claude_packets
    pending_packets = pending_packets_fn(repo_root, paths)
    return latest_pending_packet_id(pending_packets)


def _validated_exit_code(*, bridge_text: str, exit_code: int) -> int:
    # Fail closed: if bridge content is malformed (not just ACK-stale),
    # force exit_code=1 so _reviewer_unhealthy treats this as broken.
    if validate_wait_bridge_content(bridge_text):
        return 1
    return exit_code


def _extract_attention_snapshot(report: Mapping[str, object]) -> WaitAttentionSnapshot:
    attention = report.get("attention")
    if not isinstance(attention, dict):
        return WaitAttentionSnapshot(status="", summary="", recommended_action="")

    return WaitAttentionSnapshot(
        status=str(attention.get("status") or ""),
        summary=str(attention.get("summary") or ""),
        recommended_action=str(attention.get("recommended_action") or ""),
    )
