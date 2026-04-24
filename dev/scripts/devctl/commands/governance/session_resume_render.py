"""Rendering helpers for SessionCachePacket output formats.

Extracted from session_resume_support.py to keep both modules under the
Python soft file-size limit (350 lines). The role-specific bootstrap
section helpers moved further into
``session_resume_render_role_sections`` for the same reason.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...runtime.conductor_capability import (
    context_graph_bootstrap_command,
    reviewer_takeover_command,
    session_resume_command_for_role,
    startup_context_command_for_role,
)
from ...runtime.devctl_interpreter import devctl_interpreter
from .session_resume_render_role_sections import (
    implementer_bootstrap_section as _implementer_bootstrap_section,
    implementer_provider_id as _implementer_provider_id,
    observer_bootstrap_section as _observer_bootstrap_section,
    reviewer_bootstrap_section as _reviewer_bootstrap_section,
)
from .session_resume_render_sections import (
    coordination_lines as _coordination_lines,
    packet_inbox_lines as _packet_inbox_lines,
    review_candidate_lines as _review_candidate_lines,
    review_range_line as _review_range_line,
    sha_line as _sha_line,
    short_sha as _short_sha,
)

if TYPE_CHECKING:
    from .session_resume_support import SessionCachePacket


# Resolve via the shared helper so the rendered token always begins with
# ``python3`` (codex finding 2026-04-24): venv binaries named plain
# ``python`` and pyenv shims that resolve to broken 3.10 both flow
# through the same portable resolution.
_DEVCTL_INTERPRETER = devctl_interpreter()

_STATUS_COMMAND = (
    f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)


def render_bootstrap(packet: "SessionCachePacket") -> str:
    """Render the canonical role-bound bootstrap packet for a fresh session."""
    role = _normalized_role(packet)
    display_next = _display_next_command(packet, role=role)
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
        f"- **attention**: {packet.attention_status}",
    ]
    if packet.attention_revision:
        lines.append(f"- **attention_revision**: `{packet.attention_revision}`")
    lines.extend(_packet_inbox_lines(packet))
    if packet.next_guard_bundle:
        lines.append(f"- **guard_bundle**: {packet.next_guard_bundle}")
    if packet.remote_control_attachment is not None:
        attachment = packet.remote_control_attachment
        target = attachment.session_url or attachment.remote_session_id or attachment.session_name
        if target:
            lines.append(
                f"- **remote_control**: {attachment.status} via `{target}`"
            )
    if display_next:
        lines.append(f"- **next_command**: `{display_next}`")

    if role == "reviewer":
        lines.extend(
            [
                "",
                "### Run In Order",
                f"1. `{startup_context_command_for_role(role)}`",
                f"2. `{session_resume_command_for_role(role)}`",
                f"3. `{_STATUS_COMMAND}`",
                f"4. `{context_graph_bootstrap_command()}`",
            ]
        )
    elif role in {"dashboard", "observer"}:
        lines.extend(
            [
                "",
                "### Run In Order",
                f"1. `{startup_context_command_for_role(role)}`",
                f"2. `{session_resume_command_for_role(role)}`",
                f"3. `{_STATUS_COMMAND}`",
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
    role = _normalized_role(packet)
    display_next = _display_next_command(packet, role=role)
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
        f"- **attention**: {packet.attention_status}",
        f"- **ack**: {packet.ack_state}",
        f"- **guard_ok**: {packet.last_guard_ok}",
    ]
    if packet.attention_revision:
        lines.append(f"- **attention_revision**: `{packet.attention_revision}`")
    lines.extend(_packet_inbox_lines(packet))
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
    if display_next:
        lines.append(f"**Next**: `{display_next}`")
        lines.append("")
    if packet.key_rules:
        lines.append("### Key rules")
        for rule in packet.key_rules:
            lines.append(f"- {rule}")
        lines.append("")
    return "\n".join(lines)


def render_summary(packet: "SessionCachePacket") -> str:
    """Render a compact key=value summary for terminal output."""
    role = _normalized_role(packet)
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
        f"attention={packet.attention_status}",
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
            f"attention_revision={packet.attention_revision}"
            if packet.attention_revision
            else "attention_revision=none"
        ),
        (
            f"pending_inbox={len(packet.packet_inbox.agents)}"
            if packet.packet_inbox is not None
            else "pending_inbox=0"
        ),
        (
            f"resync_required={packet.coordination.resync_required}"
            if packet.coordination is not None
            else "resync_required=unknown"
        ),
        f"next={_display_next_command(packet, role=role)}",
    ]
    return "\n".join(lines)


def _normalized_role(packet: "SessionCachePacket") -> str:
    role = str(packet.role or "").strip().lower()
    if role in {"dashboard", "implementer", "observer", "reviewer"}:
        return role
    return "implementer"


def _role_label(role: str) -> str:
    if role == "reviewer":
        return "Reviewer"
    if role == "observer":
        return "Observer"
    if role == "dashboard":
        return "Dashboard"
    return "Implementer"


def _display_next_command(packet: "SessionCachePacket", *, role: str) -> str:
    if packet.authority_snapshot is not None and packet.authority_snapshot.next_command:
        return packet.authority_snapshot.next_command
    return packet.next_recommended_command or packet.next_action


def _role_bootstrap_section(packet: "SessionCachePacket", *, role: str) -> list[str]:
    if role == "reviewer":
        return _reviewer_bootstrap_section(packet)
    if role in {"dashboard", "observer"}:
        return _observer_bootstrap_section(packet, role=role)
    return _implementer_bootstrap_section(packet)


