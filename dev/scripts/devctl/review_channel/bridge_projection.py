"""Render and validate the transitional bridge compatibility projection."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass

from .bridge_sanitize import (
    BRIDGE_ALLOWED_H2,
    BRIDGE_SECTION_LINE_LIMITS,
    bridge_hygiene_errors as _bridge_hygiene_errors,
    sanitize_bridge_sections,
)
from .handoff import extract_bridge_snapshot

bridge_hygiene_errors = _bridge_hygiene_errors

_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

_START_RULES_BODY = """If this file is attached at the start of a new Codex or Claude conversation,
treat these rules as active workflow instructions immediately.

1. Use this file as the live Codex<->Claude coordination authority for the
   current loop. Do not create parallel control files for the same work.
2. Codex is the reviewer. Claude is the coder.
3. At conversation start, both agents must bootstrap repo authority before
   acting. The approved startup path is:
   `python3 dev/scripts/devctl.py startup-context --format summary` first. If it
   exits non-zero, checkpoint or repair the repo state before coding or
   relaunching conductor work. User summaries, stale chat continuity, or
   remembered prior state are not substitutes for this Step 0 receipt. Then run
   `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`.
   Keep chat bootstrap acknowledgements concise: blocker state plus next step,
   not a replay of the packet, unless the operator asks for the detail.
4. Treat `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and
   `dev/active/review_channel.md` as the canonical authority chain.
5. Start from the live sections in this file:
   - Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.
   - Claude should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`, then acknowledge the active instruction in `Claude Ack` before coding.
   - Claude must read `Last Codex poll` / `Poll Status` first on each repoll.
6. Codex must poll non-`bridge.md` worktree changes every 2-3 minutes while
   code is moving.
7. Codex must exclude `bridge.md` itself when computing the reviewed
   worktree hash. Advisory scratch/audit artifacts such as `convo.md` and
   `dev/audits/**` must stay out of that reviewed-hash truth too.
8. Each meaningful Codex review must include an operator-visible chat update.
9. When `Reviewer mode` is `active_dual_agent`, this file is the live
   reviewer/coder authority.
10. When `Reviewer mode` is `single_agent`, `tools_only`, `paused`, or
    `offline`, Claude must not assume a live Codex review loop.
11. Only the Codex conductor may update the Codex-owned sections in this file.
12. Only the Claude conductor may update the Claude-owned sections in this
    file.
13. Specialist workers should wake on owned-path changes instead of polling
    the full tree blindly.
14. Codex must emit an operator-visible heartbeat every 5 minutes while code
    is moving, even when the blocker set is unchanged.
15. Keep this file current-state only. Replace stale findings instead of
    turning it into a transcript dump.
16. When the current slice is accepted and scoped plan work remains, Codex must
    promote the next bounded task instead of idling.
17. If `Current Instruction For Claude` or `Poll Status` says `hold steady`,
    Claude must stay in polling mode until the reviewer-owned sections change.
18. If `Current Instruction For Claude` still contains active work and there is
    no explicit reviewer-owned wait state, Claude status/ack updates must be
    substantive: name concrete files, subsystems, findings, or one concrete
    blocker/question. `No change. Continuing.`, `instruction unchanged`, and
    `Codex should review` are contract violations.
19. Do not use raw shell sleep loops such as `sleep 60` or
    `bash -lc 'sleep 60'` to represent waiting. Use the repo-owned
    `review-channel --action implementer-wait` path only under an explicit
    reviewer-owned wait state."""

_PROTOCOL_BODY = """1. Claude should poll this file periodically while coding.
2. Codex rewrites reviewer-owned sections after each real review pass instead
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

_SWARM_MODE_BODY = """- Current scale-out mode is `8+8`.
- `dev/active/review_channel.md` contains the static swarm plan and lane map.
- This file is the only live cross-team coordination surface during execution.
- Keep `bridge.md` current-state only; do not turn it into a transcript dump.
- Keep the active markdown bridge disciplined until the structured `review-channel` / overlay-native path replaces it."""


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
    bridge_text: str,
    last_worktree_hash: str,
) -> tuple[str, BridgeRenderResult]:
    """Rebuild the compatibility bridge from the tracked live state."""
    snapshot = extract_bridge_snapshot(bridge_text)
    sections, sanitized_sections = sanitize_bridge_sections(
        snapshot.sections,
        section_line_limits=BRIDGE_SECTION_LINE_LIMITS,
    )
    metadata = _metadata_from_snapshot(snapshot, sections, last_worktree_hash=last_worktree_hash)
    rendered = "\n".join(
        [
            "# Review Bridge",
            "",
            "Live shared review channel for Codex <-> Claude coordination during active work.",
            "",
            "## Start-Of-Conversation Rules",
            "",
            _START_RULES_BODY,
            "",
            *metadata,
            "",
            "## Protocol",
            "",
            _PROTOCOL_BODY,
            "",
            "## Swarm Mode",
            "",
            _SWARM_MODE_BODY,
            "",
            *_render_section_pairs(sections),
        ]
    ).rstrip() + "\n"
    result = BridgeRenderResult(
        lines_before=len(bridge_text.splitlines()),
        lines_after=len(rendered.splitlines()),
        bytes_before=len(bridge_text.encode("utf-8")),
        bytes_after=len(rendered.encode("utf-8")),
        dropped_headings=tuple(
            heading
            for heading in _ordered_unique(
                match.group(1).strip() for match in _H2_RE.finditer(bridge_text)
            )
            if heading not in BRIDGE_ALLOWED_H2
        ),
        sanitized_sections=tuple(sanitized_sections),
    )
    return rendered, result


def _render_section_pairs(sections: dict[str, str]) -> list[str]:
    ordered = (
        "Poll Status",
        "Current Verdict",
        "Open Findings",
        "Claude Status",
        "Claude Questions",
        "Claude Ack",
        "Current Instruction For Claude",
        "Last Reviewed Scope",
    )
    lines: list[str] = []
    for heading in ordered:
        lines.extend(
            [
                f"## {heading}",
                "",
                sections[heading],
                "",
            ]
        )
    return lines[:-1]


def _metadata_from_snapshot(
    snapshot,
    sections: dict[str, str],
    *,
    last_worktree_hash: str,
) -> list[str]:
    metadata = snapshot.metadata
    current_instruction = sections["Current Instruction For Claude"]
    current_revision = metadata.get("current_instruction_revision", "").strip()
    if not current_revision and current_instruction.strip():
        current_revision = hashlib.sha256(
            current_instruction.strip().encode("utf-8")
        ).hexdigest()[:12]
    return [
        f"- Last Codex poll: `{metadata.get('last_codex_poll_utc', '')}`",
        "- Last Codex poll (Local America/New_York): "
        f"`{metadata.get('last_codex_poll_local', '')}`",
        f"- Reviewer mode: `{metadata.get('reviewer_mode', 'active_dual_agent')}`",
        f"- Last non-audit worktree hash: `{last_worktree_hash}`",
        f"- Current instruction revision: `{current_revision}`",
    ]


def _ordered_unique(values) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered
