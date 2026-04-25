"""Shared markdown sections for session-resume renderers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...review_channel.ack_contract import packet_ack_is_transport_lifecycle_line

if TYPE_CHECKING:
    from .session_resume_support import SessionCachePacket


def packet_inbox_lines(packet: "SessionCachePacket") -> list[str]:
    packet_inbox = packet.packet_inbox
    if packet_inbox is None or not packet_inbox.agents:
        return []
    lines = [
        "",
        "### Pending Inbox",
        packet_ack_is_transport_lifecycle_line(),
    ]
    if packet_inbox.attention_revision:
        lines.append(f"- **attention_revision**: `{packet_inbox.attention_revision}`")
    for record in packet_inbox.agents:
        details = [f"attention={record.attention_status or 'none'}"]
        if record.wake_reason:
            details.append(f"wake_reason={record.wake_reason}")
        if record.delivery_state:
            details.append(f"delivery={record.delivery_state}")
        if record.current_instruction_packet_id:
            details.append(f"instruction={record.current_instruction_packet_id}")
        if record.latest_finding_packet_id:
            details.append(f"finding={record.latest_finding_packet_id}")
        if record.pending_actionable_packet_ids:
            details.append(
                f"pending_actionable={len(record.pending_actionable_packet_ids)}"
            )
        if record.expired_unresolved_packet_ids:
            details.append(
                f"expired_unresolved={len(record.expired_unresolved_packet_ids)}"
            )
        lines.append(f"- **{record.agent}**: " + ", ".join(details))
        if record.required_command:
            lines.append(f"  required_command: `{record.required_command}`")
    return lines


def sha_line(label: str, value: str, *, default: str) -> str:
    if value:
        return f"- **{label}**: `{short_sha(value)}`"
    return f"- **{label}**: {default}"


def short_sha(value: str) -> str:
    return str(value or "")[:12]


def review_range_line(packet: "SessionCachePacket") -> str:
    candidate = packet.review_candidate
    if candidate is not None and candidate.valid and candidate.ready_for_review:
        return (
            f"- **review_target**: candidate `{candidate.candidate_id}` "
            f"({candidate.artifact_kind or 'unknown'})"
        )
    head = packet.head_sha.strip()
    last_reviewed = packet.last_reviewed_sha.strip()
    if head and last_reviewed and head != last_reviewed:
        return f"- **review_range**: `{last_reviewed}..{head}`"
    if head and not last_reviewed:
        return "- **review_range**: full pending range (no prior review SHA recorded)"
    return "- **review_range**: already_current"


def review_candidate_lines(packet: "SessionCachePacket") -> list[str]:
    candidate = packet.review_candidate
    if candidate is None:
        return []
    lines = [
        "",
        "### Review Candidate",
        f"- **candidate_id**: `{candidate.candidate_id}`",
        f"- **artifact_kind**: {candidate.artifact_kind or 'n/a'}",
        f"- **valid**: {candidate.valid}",
        f"- **ready_for_review**: {candidate.ready_for_review}",
    ]
    if candidate.worktree_hash:
        lines.append(f"- **worktree_hash**: `{candidate.worktree_hash[:12]}`")
    if candidate.changed_paths:
        lines.append(
            "- **changed_paths**: "
            + ", ".join(f"`{path}`" for path in candidate.changed_paths[:6])
            + ("." if len(candidate.changed_paths) <= 6 else ", ...")
        )
    if candidate.missing_scope_paths:
        lines.append(
            "- **missing_scope_paths**: "
            + ", ".join(f"`{path}`" for path in candidate.missing_scope_paths[:6])
            + ("." if len(candidate.missing_scope_paths) <= 6 else ", ...")
        )
    if candidate.invalidation_reason:
        lines.append(f"- **invalidation_reason**: `{candidate.invalidation_reason}`")
    return lines


def coordination_lines(packet: "SessionCachePacket") -> list[str]:
    coordination = packet.coordination
    if coordination is None:
        return []
    lines = [
        "",
        "### Coordination",
        (
            "- **topology**: "
            f"`{coordination.declared_topology}` / "
            f"`{coordination.observed_topology}` -> "
            f"`{coordination.recommended_topology}`"
        ),
        (
            "- **fanout**: "
            f"`{coordination.fanout_posture}` | safe_to_fanout={coordination.safe_to_fanout}"
        ),
        f"- **worktree_strategy**: `{coordination.worktree_strategy}`",
        f"- **resync_required**: {coordination.resync_required}",
    ]
    if coordination.active_target is not None:
        lines.append(
            f"- **active_target**: `{coordination.active_target.plan_path}` "
            f"[{coordination.active_target.target_kind}]"
        )
    if coordination.current_slice:
        lines.append(f"- **current_slice**: {coordination.current_slice}")
    if coordination.scope_paths:
        lines.append(
            "- **scope_paths**: "
            + ", ".join(f"`{path}`" for path in coordination.scope_paths[:4])
            + ("." if len(coordination.scope_paths) <= 4 else ", ...")
        )
    if coordination.resync_reasons:
        lines.append(
            "- **resync_reasons**: "
            + ", ".join(f"`{reason}`" for reason in coordination.resync_reasons)
        )
    if coordination.actors:
        lines.append(
            "- **actors**: "
            + ", ".join(
                f"`{actor.actor_id}:{actor.presence}`"
                for actor in coordination.actors[:4]
            )
            + ("." if len(coordination.actors) <= 4 else ", ...")
        )
    return lines
