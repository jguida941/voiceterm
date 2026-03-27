"""Render and validate the transitional bridge compatibility projection."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass

from .handoff import extract_bridge_snapshot

BRIDGE_ALLOWED_H2 = (
    "Start-Of-Conversation Rules",
    "Protocol",
    "Swarm Mode",
    "Poll Status",
    "Current Verdict",
    "Open Findings",
    "Claude Status",
    "Claude Questions",
    "Claude Ack",
    "Current Instruction For Claude",
    "Last Reviewed Scope",
)
BRIDGE_REQUIRED_H2 = (
    "Start-Of-Conversation Rules",
    "Protocol",
    "Poll Status",
    "Current Verdict",
    "Open Findings",
    "Claude Status",
    "Claude Questions",
    "Claude Ack",
    "Current Instruction For Claude",
    "Last Reviewed Scope",
)
BRIDGE_SECTION_LINE_LIMITS = {
    "Poll Status": 6,
    "Current Verdict": 8,
    "Open Findings": 16,
    "Claude Status": 40,
    "Claude Questions": 8,
    "Claude Ack": 16,
    "Current Instruction For Claude": 12,
    "Last Reviewed Scope": 16,
}
MAX_BRIDGE_LINES = 400
MAX_BRIDGE_BYTES = 24_000

_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_TRANSCRIPT_LINE_PATTERNS = (
    re.compile(r"(?i)^test .+\.\.\. ok$"),
    re.compile(r"(?i)^running \d+ tests$"),
    re.compile(r"(?i)^test result:"),
    re.compile(r"(?i)^compiling "),
    re.compile(r"(?i)^finished "),
    re.compile(r"(?i)^doc-tests "),
    re.compile(r"(?i)^\s*running tests/"),
    re.compile(r"(?i)^\[process-sweep-post\]"),
    re.compile(r"(?i)^last login:"),
    re.compile(r"(?i)^/bin/zsh "),
    re.compile(r"(?i)^❯ "),
    re.compile(r"(?i)^⏺ "),
)
_STATUS_HISTORY_MARKERS = (
    "prior slice",
    "prior rev",
    "session ",
    "superseded",
    "hold steady",
)
_QUESTION_DEFAULT = "- None recorded."

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


def bridge_hygiene_errors(text: str) -> list[str]:
    """Return fail-closed bridge hygiene errors."""
    errors: list[str] = []
    line_count = len(text.splitlines())
    byte_count = len(text.encode("utf-8"))
    if line_count > MAX_BRIDGE_LINES:
        errors.append(
            f"Bridge exceeds the {MAX_BRIDGE_LINES}-line hard limit ({line_count} lines)."
        )
    if byte_count > MAX_BRIDGE_BYTES:
        errors.append(
            f"Bridge exceeds the {MAX_BRIDGE_BYTES}-byte hard limit ({byte_count} bytes)."
        )

    headings = [match.group(1).strip() for match in _H2_RE.finditer(text)]
    duplicates = _duplicate_headings(headings)
    if duplicates:
        errors.append("Bridge contains duplicate H2 headings: " + ", ".join(duplicates))
    unknown = [heading for heading in headings if heading not in BRIDGE_ALLOWED_H2]
    if unknown:
        errors.append("Bridge contains unsupported H2 headings: " + ", ".join(sorted(set(unknown))))

    if _ANSI_ESCAPE_RE.search(text):
        errors.append("Bridge contains ANSI escape sequences or terminal control output.")
    if _CONTROL_CHAR_RE.search(text):
        errors.append("Bridge contains raw control characters.")

    transcript_hits = _find_transcript_lines(text)
    if transcript_hits:
        errors.append(
            "Bridge contains transcript/test-output lines: "
            + "; ".join(f"`{line}`" for line in transcript_hits[:3])
        )

    snapshot = extract_bridge_snapshot(text)
    for heading, limit in BRIDGE_SECTION_LINE_LIMITS.items():
        body = snapshot.sections.get(heading, "").strip()
        if not body:
            continue
        lines = len(body.splitlines())
        if lines > limit:
            errors.append(
                f"`{heading}` exceeds the {limit}-line live-state limit ({lines} lines)."
            )
    return errors


def render_bridge_projection(
    *,
    bridge_text: str,
    last_worktree_hash: str,
) -> tuple[str, BridgeRenderResult]:
    """Rebuild the compatibility bridge from the tracked live state."""
    snapshot = extract_bridge_snapshot(bridge_text)
    sections, sanitized_sections = _sanitize_sections(snapshot.sections)
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


def _sanitize_sections(sections: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    sanitized: dict[str, str] = {}
    mutated: list[str] = []
    sanitized["Poll Status"] = _sanitize_simple_section(
        sections.get("Poll Status", ""),
        default="- Reviewer state unavailable.",
        max_items=2,
        max_lines=BRIDGE_SECTION_LINE_LIMITS["Poll Status"],
    )
    sanitized["Current Verdict"] = _sanitize_simple_section(
        sections.get("Current Verdict", ""),
        default="- reviewer state unavailable",
        max_items=2,
        max_lines=BRIDGE_SECTION_LINE_LIMITS["Current Verdict"],
    )
    sanitized["Open Findings"] = _sanitize_simple_section(
        sections.get("Open Findings", ""),
        default="- none",
        max_items=6,
        max_lines=BRIDGE_SECTION_LINE_LIMITS["Open Findings"],
    )
    sanitized["Current Instruction For Claude"] = _sanitize_simple_section(
        sections.get("Current Instruction For Claude", ""),
        default="- Await reviewer instruction refresh.",
        max_items=4,
        max_lines=BRIDGE_SECTION_LINE_LIMITS["Current Instruction For Claude"],
    )
    sanitized["Claude Status"] = _sanitize_claude_status(sections.get("Claude Status", ""))
    sanitized["Claude Questions"] = _sanitize_simple_section(
        sections.get("Claude Questions", ""),
        default=_QUESTION_DEFAULT,
        max_items=3,
        max_lines=BRIDGE_SECTION_LINE_LIMITS["Claude Questions"],
    )
    sanitized["Claude Ack"] = _sanitize_claude_ack(sections.get("Claude Ack", ""))
    sanitized["Last Reviewed Scope"] = _sanitize_simple_section(
        sections.get("Last Reviewed Scope", ""),
        default="- (missing)",
        max_items=12,
        max_lines=BRIDGE_SECTION_LINE_LIMITS["Last Reviewed Scope"],
    )
    for heading, body in sanitized.items():
        previous = sections.get(heading, "").strip()
        if body != (previous or body):
            mutated.append(heading)
    return sanitized, mutated


def _sanitize_simple_section(
    raw: str,
    *,
    default: str,
    max_items: int,
    max_lines: int,
) -> str:
    blocks = _sanitize_blocks(_split_markdown_items(raw))
    if not blocks:
        return default
    kept = _take_blocks(blocks, max_items=max_items, max_lines=max_lines)
    return "\n".join(kept) if kept else default


def _sanitize_claude_status(raw: str) -> str:
    blocks = _sanitize_blocks(_split_markdown_items(raw))
    kept: list[str] = []
    for block in blocks:
        lowered = block.lower()
        if kept and any(marker in lowered for marker in _STATUS_HISTORY_MARKERS):
            break
        kept.append(block)
    kept = _take_blocks(
        kept,
        max_items=10,
        max_lines=BRIDGE_SECTION_LINE_LIMITS["Claude Status"],
    )
    return "\n".join(kept) if kept else "- Status unavailable."


def _sanitize_claude_ack(raw: str) -> str:
    blocks = _sanitize_blocks(_split_markdown_items(raw))
    if not blocks:
        return "- missing"
    kept = [blocks[0]]
    for block in blocks[1:]:
        lowered = block.lower()
        if "instruction-rev:" in lowered:
            break
        if any(marker in lowered for marker in _STATUS_HISTORY_MARKERS):
            break
        kept.append(block)
    kept = _take_blocks(
        kept,
        max_items=3,
        max_lines=BRIDGE_SECTION_LINE_LIMITS["Claude Ack"],
    )
    return "\n".join(kept) if kept else "- missing"


def _sanitize_blocks(blocks: list[str]) -> list[str]:
    cleaned: list[str] = []
    for block in blocks:
        normalized = _strip_transcript_lines(_strip_terminal_bytes(block)).strip()
        if not normalized:
            continue
        if any(
            pattern.search(line.strip())
            for line in normalized.splitlines()
            for pattern in _TRANSCRIPT_LINE_PATTERNS
        ):
            continue
        cleaned.append(normalized)
    return cleaned


def _strip_terminal_bytes(text: str) -> str:
    without_ansi = _ANSI_ESCAPE_RE.sub("", text)
    return _CONTROL_CHAR_RE.sub("", without_ansi)


def _strip_transcript_lines(text: str) -> str:
    kept = [
        line.rstrip()
        for line in text.splitlines()
        if not _is_transcript_line(line.strip())
    ]
    return "\n".join(_collapse_blank_lines(kept)).strip()


def _is_transcript_line(line: str) -> bool:
    if not line:
        return False
    return any(pattern.search(line) for pattern in _TRANSCRIPT_LINE_PATTERNS)


def _split_markdown_items(text: str) -> list[str]:
    lines = _collapse_blank_lines(_strip_terminal_bytes(text).splitlines())
    if not any(line.lstrip().startswith("- ") for line in lines):
        normalized = "\n".join(line.rstrip() for line in lines).strip()
        return [normalized] if normalized else []
    items: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.lstrip().startswith("- "):
            if current:
                items.append(current)
            current = [line.rstrip()]
            continue
        if current:
            current.append(line.rstrip())
    if current:
        items.append(current)
    return ["\n".join(block).strip() for block in items if "\n".join(block).strip()]


def _take_blocks(
    blocks: list[str],
    *,
    max_items: int,
    max_lines: int,
) -> list[str]:
    kept: list[str] = []
    used_lines = 0
    for block in blocks[:max_items]:
        block_lines = len(block.splitlines())
        if kept and used_lines + block_lines > max_lines:
            break
        if not kept and block_lines > max_lines:
            kept.append("\n".join(block.splitlines()[:max_lines]))
            break
        kept.append(block)
        used_lines += block_lines
    return kept


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


def _find_transcript_lines(text: str) -> list[str]:
    hits: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or not _is_transcript_line(line):
            continue
        if line not in hits:
            hits.append(line)
    return hits


def _duplicate_headings(headings: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for heading in headings:
        if heading in seen and heading not in duplicates:
            duplicates.append(heading)
        seen.add(heading)
    return duplicates


def _ordered_unique(values) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _collapse_blank_lines(lines: list[str]) -> list[str]:
    collapsed: list[str] = []
    previous_blank = False
    for raw in lines:
        blank = not raw.strip()
        if blank and previous_blank:
            continue
        collapsed.append(raw)
        previous_blank = blank
    return collapsed
