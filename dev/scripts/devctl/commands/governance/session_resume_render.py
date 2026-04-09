"""Rendering helpers for SessionCachePacket output formats.

Extracted from session_resume_support.py to keep both modules under the
Python soft file-size limit (350 lines).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...runtime.conductor_capability import (
    context_graph_bootstrap_command,
    reviewer_takeover_command,
    session_resume_command_for_role,
    startup_context_command_for_role,
)

if TYPE_CHECKING:
    from .session_resume_support import SessionCachePacket


def render_bootstrap(packet: "SessionCachePacket") -> str:
    """Render the canonical role-bound bootstrap packet for a fresh session."""
    role = _normalized_role(packet)
    lines = [
        f"## {_role_label(role)} Bootstrap Packet",
        "",
        f"- **source_command**: `{session_resume_command_for_role(role)}`",
        _sha_line("head", packet.head_sha, default="(unknown)"),
        _sha_line("last_reviewed", packet.last_reviewed_sha, default="(none)"),
        _review_range_line(packet),
        f"- **mode**: {packet.operator_interaction_mode}",
        f"- **phase**: {packet.resolved_phase}",
        f"- **blockers**: {packet.blockers}",
    ]
    if packet.next_guard_bundle:
        lines.append(f"- **guard_bundle**: {packet.next_guard_bundle}")
    if packet.remote_control_attachment is not None:
        attachment = packet.remote_control_attachment
        target = attachment.session_url or attachment.remote_session_id or attachment.session_name
        if target:
            lines.append(
                f"- **remote_control**: {attachment.status} via `{target}`"
            )
    if packet.next_recommended_command:
        lines.append(f"- **next_command**: `{packet.next_recommended_command}`")
    elif packet.next_action:
        lines.append(f"- **next_command**: `{packet.next_action}`")

    if role == "reviewer":
        lines.extend(
            [
                "",
                "### Run In Order",
                f"1. `{startup_context_command_for_role(role)}`",
                f"2. `{session_resume_command_for_role(role)}`",
                "3. `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`",
                f"4. `{context_graph_bootstrap_command()}`",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "### Run In Order",
                f"1. `{startup_context_command_for_role(role)}`",
                f"2. `{session_resume_command_for_role(role)}`",
                f"3. `{context_graph_bootstrap_command()}`",
            ]
        )

    lines.extend(
        [
            "",
            "### Live Authority",
            "- `AGENTS.md`",
            "- `dev/active/INDEX.md`",
            "- `dev/active/MASTER_PLAN.md`",
        ]
    )
    if packet.operator_interaction_mode == "active_dual_agent":
        lines.extend(
            [
                "- `dev/active/review_channel.md`",
                "- `bridge.md`",
            ]
        )

    lines.extend(_role_bootstrap_section(packet, role=role))
    lines.extend(_coordination_lines(packet))

    if packet.current_instruction:
        lines.extend(
            [
                "",
                "### Current Instruction",
                packet.current_instruction,
            ]
        )
    candidate_lines = _review_candidate_lines(packet)
    if candidate_lines:
        lines.extend(candidate_lines)
    if packet.open_findings:
        lines.extend(
            [
                "",
                "### Open Findings",
                packet.open_findings,
            ]
        )
    return "\n".join(lines)


def render_markdown(packet: "SessionCachePacket") -> str:
    """Render a human-readable markdown summary of the session packet."""
    lines = [
        "## Session Resume",
        "",
        f"- **role**: {packet.role}",
        f"- **branch**: {packet.branch}",
        _sha_line("head", packet.head_sha, default="(unknown)"),
        _sha_line("last_reviewed", packet.last_reviewed_sha, default="(none)"),
        _sha_line("head_at_push", packet.head_at_push_time, default="(none)"),
        f"- **advisory**: {packet.advisory_action} / {packet.advisory_reason}",
        f"- **blockers**: {packet.blockers}",
        f"- **mode**: {packet.operator_interaction_mode}",
        f"- **phase**: {packet.resolved_phase}",
        f"- **ack**: {packet.ack_state}",
        f"- **guard_ok**: {packet.last_guard_ok}",
    ]
    if packet.remote_control_attachment is not None:
        attachment = packet.remote_control_attachment
        target = attachment.session_url or attachment.remote_session_id or attachment.session_name
        lines.append(
            f"- **remote_control**: {attachment.status}"
            + (f" / `{target}`" if target else "")
        )
    if packet.next_guard_bundle:
        lines.append(f"- **guard_bundle**: {packet.next_guard_bundle}")
    lines.append("")
    if packet.current_instruction:
        lines.append("### Current instruction")
        lines.append(packet.current_instruction)
        lines.append("")
    if packet.open_findings:
        lines.append("### Open findings")
        lines.append(packet.open_findings)
        lines.append("")
    candidate_lines = _review_candidate_lines(packet)
    if candidate_lines:
        lines.extend(candidate_lines)
        lines.append("")
    lines.extend(_coordination_lines(packet))
    if packet.next_recommended_command:
        lines.append(f"**Next**: `{packet.next_recommended_command}`")
        lines.append("")
    elif packet.next_action:
        lines.append(f"**Next**: `{packet.next_action}`")
        lines.append("")
    if packet.key_rules:
        lines.append("### Key rules")
        for rule in packet.key_rules:
            lines.append(f"- {rule}")
        lines.append("")
    return "\n".join(lines)


def render_summary(packet: "SessionCachePacket") -> str:
    """Render a compact key=value summary for terminal output."""
    lines = [
        f"role={packet.role}",
        f"branch={packet.branch}",
        f"head={_short_sha(packet.head_sha)}" if packet.head_sha else "head=unknown",
        f"last_reviewed={_short_sha(packet.last_reviewed_sha)}" if packet.last_reviewed_sha else "last_reviewed=none",
        f"head_at_push={_short_sha(packet.head_at_push_time)}" if packet.head_at_push_time else "head_at_push=none",
        f"action={packet.advisory_action}",
        f"reason={packet.advisory_reason}",
        f"blockers={packet.blockers}",
        f"mode={packet.operator_interaction_mode}",
        f"phase={packet.resolved_phase}",
        f"ack={packet.ack_state}",
        f"guard_ok={packet.last_guard_ok}",
        f"guard_bundle={packet.next_guard_bundle}" if packet.next_guard_bundle else "guard_bundle=none",
        (
            f"review_candidate={packet.review_candidate.candidate_id}"
            if packet.review_candidate is not None
            else "review_candidate=none"
        ),
        (
            "coordination="
            f"{packet.coordination.declared_topology}/"
            f"{packet.coordination.observed_topology}->"
            f"{packet.coordination.recommended_topology}"
            if packet.coordination is not None
            else "coordination=none"
        ),
        (
            f"safe_to_fanout={packet.coordination.safe_to_fanout}"
            if packet.coordination is not None
            else "safe_to_fanout=unknown"
        ),
        (
            "remote_control="
            f"{packet.remote_control_attachment.status}:"
            f"{packet.remote_control_attachment.remote_session_id or packet.remote_control_attachment.session_name or 'present'}"
            if packet.remote_control_attachment is not None
            else "remote_control=none"
        ),
        (
            f"resync_required={packet.coordination.resync_required}"
            if packet.coordination is not None
            else "resync_required=unknown"
        ),
        f"next={packet.next_recommended_command or packet.next_action}",
    ]
    return "\n".join(lines)


def _normalized_role(packet: "SessionCachePacket") -> str:
    role = str(packet.role or "").strip().lower()
    return "reviewer" if role == "reviewer" else "implementer"


def _role_label(role: str) -> str:
    return "Reviewer" if role == "reviewer" else "Implementer"


def _sha_line(label: str, value: str, *, default: str) -> str:
    if value:
        return f"- **{label}**: `{_short_sha(value)}`"
    return f"- **{label}**: {default}"


def _short_sha(value: str) -> str:
    return str(value or "")[:12]


def _review_range_line(packet: "SessionCachePacket") -> str:
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


def _role_bootstrap_section(packet: "SessionCachePacket", *, role: str) -> list[str]:
    if role == "reviewer":
        return _reviewer_bootstrap_section(packet)
    return _implementer_bootstrap_section(packet)


def _reviewer_bootstrap_section(packet: "SessionCachePacket") -> list[str]:
    lines = [
        "",
        "### Reviewer Rules",
        "- Use this packet as the first-hop reviewer bootstrap instead of operator memory or stale bridge prose.",
        "- Start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.",
    ]
    candidate = packet.review_candidate
    head = packet.head_sha.strip()
    last_reviewed = packet.last_reviewed_sha.strip()
    if candidate is not None and candidate.valid and candidate.ready_for_review:
        lines.append(
            f"- Prefer frozen review candidate `{candidate.candidate_id}` over raw HEAD drift."
        )
        if candidate.changed_paths:
            lines.append(
                "- Review the candidate path set first: "
                + ", ".join(f"`{path}`" for path in candidate.changed_paths[:6])
                + ("." if len(candidate.changed_paths) <= 6 else ", ...")
            )
        if candidate.artifact_kind == "dirty_tree" and candidate.worktree_hash:
            lines.append(
                f"- Inspect the dirty-tree candidate at worktree hash `{candidate.worktree_hash[:12]}` before any commit-range fallback."
            )
    elif head and last_reviewed and head != last_reviewed:
        lines.append(
            f"- Review the exact diff range `{last_reviewed}..{head}` before widening scope."
        )
    elif head and not last_reviewed:
        lines.append(
            "- No prior `last_reviewed_sha` is recorded; review all pending changes before widening scope."
        )
    lines.append(
        "- Stay reviewer-only unless the workflow explicitly enters `reviewer_mode=single_agent` "
        f"or `{reviewer_takeover_command()}`."
    )
    lines.extend(
        [
            "",
            "### Conversation Starter",
            (
                "Reviewer lane only. Run "
                f"`{startup_context_command_for_role('reviewer')}`, then "
                f"`{session_resume_command_for_role('reviewer')}`, then "
                "`python3 dev/scripts/devctl.py review-channel --action status "
                "--terminal none --format json`, then "
                f"`{context_graph_bootstrap_command()}`. Use this packet plus typed "
                "review-state/`bridge.md` as live authority."
            ),
        ]
    )
    return lines


def _implementer_bootstrap_section(packet: "SessionCachePacket") -> list[str]:
    lines = [
        "",
        "### Implementer Rules",
        "- Use `Current Instruction For Claude` / typed `current_instruction` as the live work source.",
        "- Acknowledge the live `instruction_revision` before coding.",
        "- If reviewer-owned state says `hold steady`, `waiting for reviewer promotion`, or governed push/review is still in progress, stay in polling mode instead of mining side work.",
    ]
    if packet.instruction_revision:
        lines.append(
            f"- Current instruction revision to acknowledge: `{packet.instruction_revision}`."
        )
    lines.extend(
        [
            "",
            "### Conversation Starter",
            (
                "Coder lane only. Run "
                f"`{startup_context_command_for_role('implementer')}`, then "
                f"`{session_resume_command_for_role('implementer')}`, then "
                f"`{context_graph_bootstrap_command()}`. Use this packet plus typed "
                "review-state/`bridge.md` as live authority and acknowledge the "
                "current instruction revision before coding."
            ),
        ]
    )
    return lines


def _review_candidate_lines(packet: "SessionCachePacket") -> list[str]:
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


def _coordination_lines(packet: "SessionCachePacket") -> list[str]:
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
