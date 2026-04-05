"""Render and validate the transitional bridge compatibility projection."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ..runtime.conductor_capability import (
    build_conductor_capability_state,
    context_graph_bootstrap_command,
    reviewer_takeover_command,
    session_resume_command_for_role,
)
from ..runtime.role_profile import TandemRole, default_provider_for_role
from .bridge_projection_state import (
    BRIDGE_SECTION_ORDER,
    bridge_projection_metadata_lines,
    bridge_projection_state_from_review_state,
    bridge_projection_state_to_dict,
    build_bridge_projection_state,
)
from .bridge_sanitize import bridge_hygiene_errors as _bridge_hygiene_errors
from .collaboration_provider import collaboration_provider

bridge_hygiene_errors = _bridge_hygiene_errors

def _protocol_body(*, reviewer_name: str, implementer_name: str) -> str:
    return f"""1. {implementer_name} should poll this file periodically while coding.
2. {reviewer_name} rewrites reviewer-owned sections after each real review pass instead
   of appending historical transcript output.
3. `bridge.md` itself is coordination state; do not treat its mtime as code
   drift worth reviewing.
4. Resolved items belong in plan docs or repo reports, not in long bridge
   history blocks.
5. Freshness and current instruction truth should come from typed projections
   first; this bridge remains a compatibility projection while the migration
   finishes.
6. Active-work `Claude Status` / `Claude Ack` updates must carry concrete work
   evidence or one concrete blocker/question; low-information polling notes are
   not valid bridge authority."""

def _swarm_mode_body() -> str:
    from ..repo_packs import active_path_config

    rc_rel = active_path_config().review_channel_rel
    return (
        f"- `{rc_rel}` contains the static planned lane table for this compatibility mode.\n"
        "- Those planned lanes are capacity/scope hints, not proof that repo-owned worker sessions already exist.\n"
        "- This file is the only live cross-team coordination surface during execution.\n"
        "- Keep `bridge.md` current-state only; do not turn it into a transcript dump.\n"
        "- Keep the active markdown bridge disciplined until the structured `review-channel` / overlay-native path replaces it."
    )


@dataclass(frozen=True)
class BridgeRenderResult:
    """Result of rebuilding the compatibility bridge projection."""

    lines_before: int
    lines_after: int
    bytes_before: int
    bytes_after: int
    dropped_headings: tuple[str, ...]
    sanitized_sections: tuple[str, ...]


def bridge_render_result_to_dict(
    result: BridgeRenderResult | None,
) -> dict[str, object] | None:
    if result is None:
        return None
    return asdict(result)


def render_bridge_projection(
    *,
    review_state,
    last_worktree_hash: str,
) -> tuple[str, BridgeRenderResult]:
    """Rebuild the compatibility bridge from typed review-channel state."""
    projection_state = bridge_projection_state_from_review_state(review_state)
    collaboration = review_state.get("collaboration")
    reviewer_provider = collaboration_provider(
        collaboration,
        role_id="review_agent",
        default=default_provider_for_role(TandemRole.REVIEWER),
    )
    implementer_provider = collaboration_provider(
        collaboration,
        role_id="coding_agent",
        default=default_provider_for_role(TandemRole.IMPLEMENTER),
    )
    reviewer_name = reviewer_provider.title()
    implementer_name = implementer_provider.title()
    metadata = bridge_projection_metadata_lines(
        projection_state,
        last_worktree_hash=last_worktree_hash,
    )
    rendered = "\n".join(
        [
            "# Review Bridge",
            "",
            (
                "Live shared review channel for "
                f"{reviewer_name} <-> {implementer_name} coordination during active work."
            ),
            "",
            "## Start-Of-Conversation Rules",
            "",
            _render_start_rules_body(
                reviewer_provider=reviewer_provider,
                implementer_provider=implementer_provider,
                reviewer_mode=projection_state.metadata.get(
                    "reviewer_mode",
                    "active_dual_agent",
                )
            ),
            "",
            *metadata,
            "",
            "## Protocol",
            "",
            _protocol_body(
                reviewer_name=reviewer_name,
                implementer_name=implementer_name,
            ),
            "",
            "## Swarm Mode",
            "",
            _swarm_mode_body(),
            "",
            *_render_section_pairs(projection_state.sections),
        ]
    ).rstrip() + "\n"
    result = BridgeRenderResult(
        lines_before=projection_state.lines_before,
        lines_after=len(rendered.splitlines()),
        bytes_before=projection_state.bytes_before,
        bytes_after=len(rendered.encode("utf-8")),
        dropped_headings=projection_state.dropped_headings,
        sanitized_sections=projection_state.sanitized_sections,
    )
    return rendered, result


def _render_start_rules_body(
    *,
    reviewer_provider: str,
    implementer_provider: str,
    reviewer_mode: str,
) -> str:
    reviewer_capability = build_conductor_capability_state(
        provider=reviewer_provider,
        role=TandemRole.REVIEWER.value,
        reviewer_mode=reviewer_mode,
    )
    implementer_capability = build_conductor_capability_state(
        provider=implementer_provider,
        role=TandemRole.IMPLEMENTER.value,
        reviewer_mode=reviewer_mode,
    )
    reviewer_name = reviewer_provider.title()
    implementer_name = implementer_provider.title()
    reviewer_resume_command = session_resume_command_for_role("reviewer")
    implementer_resume_command = session_resume_command_for_role("implementer")
    reviewer_owned_sections = (
        "the Codex-owned sections"
        if reviewer_provider == "codex"
        else "the reviewer-owned sections, including the `Last Codex poll` compatibility heartbeat"
    )
    implementer_owned_sections = (
        "the Claude-owned sections"
        if implementer_provider == "claude"
        else "the implementer-owned compatibility sections (`Claude Status`, `Claude Questions`, `Claude Ack`)"
    )
    lines = [
        (
            f"If this file is attached at the start of a new {reviewer_name} "
            f"or {implementer_name} conversation,"
        ),
        "treat these rules as active workflow instructions immediately.",
        "",
        (
            f"1. Use this file as the live {reviewer_name}<->{implementer_name} "
            "coordination authority for the"
        ),
        "   current loop. Do not create parallel control files for the same work.",
        f"2. {reviewer_name} is the reviewer. {implementer_name} is the coder.",
        "3. At conversation start, both agents must bootstrap repo authority before",
        f"   acting. {reviewer_name} uses "
        f"`{reviewer_capability.startup_context_command}` and {implementer_name} uses "
        f"`{implementer_capability.startup_context_command}` first. If either exits",
        "   non-zero, checkpoint or repair the repo state before coding or",
        "   relaunching conductor work. User summaries, stale chat continuity, or",
        "   remembered prior state are not substitutes for this Step 0 receipt.",
        f"   Then {reviewer_name} uses `{reviewer_resume_command}` and {implementer_name} uses",
        f"   `{implementer_resume_command}` as the canonical role bootstrap packet.",
        "   Then run",
        f"   `{context_graph_bootstrap_command()}`.",
        "   Keep chat bootstrap acknowledgements concise: blocker state plus next step,",
        "   not a replay of the packet, unless the operator asks for the detail.",
        "4. Treat `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and",
        "   `dev/active/review_channel.md` as the canonical authority chain.",
        "5. Start from the live sections in this file:",
        (
            f"   - {reviewer_name} should start from `Poll Status`, `Current Verdict`, "
            "`Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`."
        ),
        (
            f"   - {implementer_name} should start from `Poll Status`, `Current Verdict`, "
            "`Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`, "
            "then acknowledge the active instruction in `Claude Ack` before coding."
        ),
        (
            "   - `Last Codex poll` remains the reviewer-heartbeat compatibility field "
            "and `Claude Status` / `Claude Ack` remain the implementer-owned compatibility "
            "sections until native role-labeled bridge headings land."
        ),
        "   - `Claude Ack` must acknowledge the current instruction revision with a machine-readable line such as `- acknowledged current instruction revision: <rev>` or `- acknowledged; instruction-rev: <rev>`.",
        f"   - {implementer_name} must read `Last Codex poll` / `Poll Status` first on each repoll.",
        f"6. {reviewer_name} must poll non-`bridge.md` worktree changes every 2-3 minutes while",
        "   code is moving.",
        f"7. {reviewer_name} must exclude `bridge.md` itself when computing the reviewed",
        "   worktree hash. Advisory scratch/audit artifacts such as `convo.md` and",
        "   `dev/audits/**` must stay out of that reviewed-hash truth too.",
        f"8. Each meaningful {reviewer_name} review must include an operator-visible chat update.",
        "9. When `Reviewer mode` is `active_dual_agent`, this file is the live",
        f"   reviewer/coder authority. {reviewer_name} stays reviewer-only by default:",
        "   missing worker worktrees, absent fanout, or a promising fix are not",
        "   permission to start local implementation. Use the repo-owned",
        "   review/promote/wait paths unless the workflow explicitly switches to",
        f"   takeover (`reviewer_mode=single_agent` or `{reviewer_takeover_command()}`).",
        "10. When `Reviewer mode` is `single_agent`, `tools_only`, `paused`, or",
        f"    `offline`, {implementer_name} must not assume a live {reviewer_name} review loop.",
        f"11. Only the {reviewer_name} conductor may update {reviewer_owned_sections} in this file.",
        f"12. Only the {implementer_name} conductor may update {implementer_owned_sections} in this",
        "    file.",
        "13. Specialist workers should wake on owned-path changes instead of polling",
        "    the full tree blindly.",
        f"14. {reviewer_name} must emit an operator-visible heartbeat every 5 minutes while code",
        "    is moving, even when the blocker set is unchanged.",
        "15. Keep this file current-state only. Replace stale findings instead of",
        "    turning it into a transcript dump.",
        f"16. When the current slice is accepted and scoped plan work remains, {reviewer_name} must",
        "    promote the next bounded task instead of idling.",
        "17. If `Current Instruction For Claude` or `Poll Status` says `hold steady`,",
        f"    {implementer_name} must stay in polling mode until the reviewer-owned sections change.",
        "18. If `Current Instruction For Claude` still contains active work and there is",
        "    no explicit reviewer-owned wait state, Claude status/ack updates must be",
        "    substantive: name concrete files, subsystems, findings, or one concrete",
        "    blocker/question. `No change. Continuing.`, `instruction unchanged`, and",
        f"    `{reviewer_name} should review` are contract violations.",
        "19. Do not use raw shell sleep loops such as `sleep 60` or",
        "    `bash -lc 'sleep 60'` to represent waiting. Use the repo-owned",
        "    `review-channel --action implementer-wait` path only under an explicit",
        "    reviewer-owned wait state.",
    ]
    return "\n".join(lines)


def _render_section_pairs(sections: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for heading in BRIDGE_SECTION_ORDER:
        lines.extend(
            [
                f"## {heading}",
                "",
                sections.get(heading, ""),
                "",
            ]
        )
    return lines[:-1]
