"""Role-specific bootstrap section helpers for session-resume rendering.

Extracted from `session_resume_render.py` to keep that module under the
Python soft file-size limit (350 lines). The role-specific section
functions are independently testable surfaces and have no callers
outside the renderer dispatch table.
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

_IMPLEMENTER_ROLES = frozenset(
    {"implementer", "coding_agent", "coder", "implementer_agent"}
)


def implementer_provider_id(packet: "SessionCachePacket") -> str:
    """Derive the implementer provider from typed packet state.

    Session-resume is role-bound, not provider-bound, so the implementer
    bootstrap prompt must not hardcode a single provider (e.g.
    ``claude``). A Codex/Cursor/gemini implementer would otherwise poll
    the wrong inbox or fail actor-validation.

    Authority order (each step is a typed source on
    ``SessionCachePacket``; we walk them until one yields a provider):

    1. Live implementer actor in ``CoordinationSnapshot.actors``. Only
       LIVE actors are trusted — planned/configured rows represent
       intended topology, not live presence, and treating planned
       fanout (e.g., AGENT-9..14) as live authority would misroute when
       fanout is actually zero.
    2. ``AuthoritySnapshot.mutation_owner`` — the typed live owner of
       the mutation/implementer role at snapshot time. Codex finding
       rev_pkt_1786: ``SessionCachePacket`` explicitly supports
       ``authority_snapshot`` without requiring ``coordination``, so a
       cached/compatibility packet where coordination is absent or
       stale must still resolve a non-claude implementer if the typed
       owner field names one.
    3. Empty string. Callers render the inbox/operator command line
       *without* ``--target``/``--actor`` rather than silently
       targeting the historic claude lane on a flipped session.

    Critically, do NOT fall back to ``packet.remote_control_attachment``
    — in remote-control single-agent the attachment provider is the
    reviewer (e.g. ``codex``), and using it would render an inbox poll
    targeting the reviewer queue instead of the implementer's own
    queue.
    """
    coordination = getattr(packet, "coordination", None)
    actors = getattr(coordination, "actors", ()) or ()
    for actor in actors:
        actor_role = str(getattr(actor, "role", "") or "").strip().lower()
        if actor_role not in _IMPLEMENTER_ROLES:
            continue
        actor_presence = str(getattr(actor, "presence", "") or "").strip().lower()
        if actor_presence != "live":
            continue
        provider = str(
            getattr(actor, "provider", "")
            or getattr(actor, "actor_id", "")
            or ""
        ).strip().lower()
        if provider:
            return provider
    authority_snapshot = getattr(packet, "authority_snapshot", None)
    mutation_owner = str(
        getattr(authority_snapshot, "mutation_owner", "") or ""
    ).strip().lower()
    if mutation_owner:
        return mutation_owner
    return ""


def reviewer_bootstrap_section(packet: "SessionCachePacket") -> list[str]:
    lines = [
        "",
        "### Reviewer Rules",
        "- Use this packet as the first-hop reviewer bootstrap instead of operator memory or stale bridge prose.",
        "- Start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.",
        "- If `Pending Inbox` already names a reviewer-targeted packet or `required_command`, run that repo-owned inbox command immediately before bridge-only analysis or operator questions.",
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
                f"`{_STATUS_COMMAND}`, then "
                f"`{context_graph_bootstrap_command()}`. Use this packet plus typed "
                "review-state/`bridge.md` as live authority."
            ),
        ]
    )
    return lines


def implementer_bootstrap_section(packet: "SessionCachePacket") -> list[str]:
    provider_id = implementer_provider_id(packet)
    if provider_id:
        inbox_command = (
            f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel "
            f"--action inbox --target {provider_id} --actor {provider_id} "
            "--status pending --format md"
        )
        inbox_rule = (
            f"- If `Pending Inbox` or typed packet state names a "
            f"{provider_id}-targeted packet or required inbox command, run "
            f"`{inbox_command}` immediately before asking what to do next."
        )
    else:
        # No typed implementer provider in coordination.actors or
        # authority_snapshot.mutation_owner. Refuse to render a phantom
        # `--target claude --actor claude` command (operator role-symmetry
        # rule, codex finding rev_pkt_1786). The bootstrap surface tells
        # the implementer to repair the typed source instead of silently
        # picking the historic provider id.
        inbox_rule = (
            "- No live implementer provider is recorded in the typed packet "
            "(`coordination.actors` is empty and `authority_snapshot."
            "mutation_owner` is unset). Refresh the typed session state "
            "(`session-resume` after a reviewer-checkpoint or attach-remote-"
            "control) before polling the inbox; do not assume a default "
            "provider id."
        )
    lines = [
        "",
        "### Implementer Rules",
        "- Use `Current Instruction For Claude` / typed `current_instruction` as the live work source.",
        "- Acknowledge the live `instruction_revision` before coding.",
        "- If reviewer-owned state says `hold steady`, `waiting for reviewer promotion`, or governed push/review is still in progress, stay in polling mode instead of mining side work.",
        inbox_rule,
        "- Do not ask the operator whether to continue a permitted probe or pull a pending packet when the typed inbox already provides the next non-destructive step.",
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


def observer_bootstrap_section(
    packet: "SessionCachePacket",
    *,
    role: str,
) -> list[str]:
    role_name = "Dashboard" if role == "dashboard" else "Observer"
    lines = [
        "",
        f"### {role_name} Rules",
        "- Use this packet as the read-only bootstrap surface before bridge-first inspection or operator memory.",
        "- Run the typed status surface before interpreting stale bridge prose, lane tables, or local assumptions.",
        "- This lane may inspect state and post findings or action requests, but it must not take implementation ownership.",
        "- If `Pending Inbox` names a required command, run that repo-owned inbox/status command before asking what to do next.",
    ]
    lines.extend(
        [
            "",
            "### Conversation Starter",
            (
                f"{role_name} lane only. Run "
                f"`{startup_context_command_for_role(role)}`, then "
                f"`{session_resume_command_for_role(role)}`, then "
                f"`{_STATUS_COMMAND}`, then "
                f"`{context_graph_bootstrap_command()}`. Use typed review-state "
                "and `bridge.md` as read-only authority, not as permission to "
                "edit or commit."
            ),
        ]
    )
    return lines
