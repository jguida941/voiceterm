"""Instruction-shape and metadata helpers for bridge promotion writes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from pathlib import Path

from .bridge_section_validation import find_embedded_markdown_headings
from .handoff import (
    IDLE_FINDING_MARKERS,
    IDLE_NEXT_ACTION_MARKERS,
    RESOLVED_VERDICT_MARKERS,
    BridgeSnapshot,
)
from .handoff_constants import MARKDOWN_ITEM_RE
from .instruction_reset import reset_implementer_sections_on_instruction_change
from .peer_liveness import REVIEWER_WAIT_STATE_MARKERS, normalize_reviewer_mode
from .promotion_marker_match import matches_any_marker
from .reviewer_state_support import (
    ReviewerMetadataUpdate,
    current_instruction_revision_from_bridge_text,
    write_reviewer_metadata,
)
from .write_preconditions import (
    assert_expected_implementer_state_hash,
    assert_expected_instruction_revision,
)

CURRENT_INSTRUCTION_SECTION = "Current Instruction For Claude"
CURRENT_INSTRUCTION_SECTION_RE = re.compile(
    rf"(^## {re.escape(CURRENT_INSTRUCTION_SECTION)}\s*$\n)(.*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
_GENERIC_PROGRESS_MARKERS = (
    "next unchecked",
    "continue checklist",
    "continue the next",
    "continue next",
    "start the next",
)
PROMOTABLE_INSTRUCTION_MARKERS = (
    *IDLE_NEXT_ACTION_MARKERS,
    *REVIEWER_WAIT_STATE_MARKERS,
    *RESOLVED_VERDICT_MARKERS,
    "next unchecked",
    "continue checklist",
    "continue the next",
    "continue next",
    "start the next",
    "complete",
    "completed",
    "done",
    "fixed",
    "accepted",
)


@dataclass(frozen=True)
class InstructionRewriteContext:
    """Shared metadata for one instruction rewrite."""

    repo_root: Path
    bridge_path: Path
    reviewer_mode: str | None
    reason: str
    expected_instruction_revision: str | None = None
    expected_implementer_state_hash: str | None = None


def instruction_needs_plan_promotion(instruction: str) -> bool:
    """Return True when instruction text is a generic progression placeholder."""
    primary_item = _primary_instruction_item(instruction)
    if not primary_item:
        return True
    if primary_item.startswith("next scoped plan item ("):
        return False
    return any(
        primary_item == marker
        or primary_item.startswith(f"{marker}:")
        or primary_item.startswith(f"{marker} ")
        for marker in _GENERIC_PROGRESS_MARKERS
    )


def validate_promotion_ready(snapshot: BridgeSnapshot) -> list[str]:
    """Return fail-closed bridge-state errors before promoting the next item."""
    errors: list[str] = []
    current_verdict = snapshot.sections.get("Current Verdict", "").strip().lower()
    open_findings = snapshot.sections.get("Open Findings", "").strip().lower()
    current_instruction = snapshot.sections.get(
        CURRENT_INSTRUCTION_SECTION, ""
    ).strip().lower()
    verdict_items = _state_items(current_verdict)
    finding_items = _state_items(open_findings)
    instruction_items = _state_items(current_instruction)

    if not current_verdict:
        errors.append("Missing `Current Verdict`; cannot promote from unknown review state.")
    elif not verdict_items or not matches_any_marker(
        verdict_items[0], RESOLVED_VERDICT_MARKERS
    ):
        errors.append(
            "`Current Verdict` must show an accepted/resolved slice before "
            "the next task is promoted."
        )

    if finding_items and not all(
        matches_any_marker(item, IDLE_FINDING_MARKERS) for item in finding_items
    ):
        errors.append(
            "`Open Findings` still contains unresolved blockers; resolve or "
            "clear them before promoting the next task."
        )

    if instruction_items and not (
        matches_any_marker(instruction_items[0], PROMOTABLE_INSTRUCTION_MARKERS)
        or instruction_needs_plan_promotion(current_instruction)
    ):
        errors.append(
            "`Current Instruction For Claude` still looks live; refuse to "
            "overwrite an active instruction."
        )

    return errors


def rewrite_current_instruction(
    *,
    bridge_text: str,
    instruction: str,
) -> str:
    """Rewrite only the live Claude-instruction section in `bridge.md`."""

    def replacement(match: re.Match[str]) -> str:
        return f"{match.group(1)}\n{instruction.strip()}\n\n"

    rewritten, count = CURRENT_INSTRUCTION_SECTION_RE.subn(
        replacement,
        bridge_text,
        count=1,
    )
    if count != 1:
        raise ValueError(
            f"Unable to locate `{CURRENT_INSTRUCTION_SECTION}` in the markdown bridge."
        )
    return rewritten


def rewrite_instruction_and_metadata(
    *,
    bridge_text: str,
    instruction: str,
    context: InstructionRewriteContext,
) -> str:
    """Rewrite instruction and refresh heartbeat metadata in one atomic text edit."""
    heading_hits = find_embedded_markdown_headings(instruction)
    if heading_hits:
        quoted = "; ".join(f"`{line}`" for line in heading_hits)
        raise ValueError(
            "Instruction rewrite rejected embedded markdown headings in "
            f"`{CURRENT_INSTRUCTION_SECTION}`: {quoted}"
        )
    assert_expected_instruction_revision(
        bridge_text=bridge_text,
        expected_instruction_revision=context.expected_instruction_revision,
        action="instruction-rewrite",
    )
    assert_expected_implementer_state_hash(
        bridge_text=bridge_text,
        expected_implementer_state_hash=context.expected_implementer_state_hash,
        action="instruction-rewrite",
    )
    previous_instruction_revision = current_instruction_revision_from_bridge_text(
        bridge_text
    )
    updated_text = rewrite_current_instruction(
        bridge_text=bridge_text,
        instruction=instruction,
    )
    normalized_mode = normalize_reviewer_mode(context.reviewer_mode)
    instruction_revision = _instruction_revision(instruction)
    rewritten, _write = write_reviewer_metadata(
        bridge_text=updated_text,
        repo_root=context.repo_root,
        bridge_path=context.bridge_path,
        update=ReviewerMetadataUpdate(
            reviewer_mode=normalized_mode,
            reason=context.reason,
            action="instruction-rewrite",
            worktree_hash=None,
            current_instruction_revision=instruction_revision,
            poll_note=(
                "Reviewer checkpoint updated through repo-owned tooling "
                f"(mode: {normalized_mode}; reason: {context.reason}; instruction-rev: {instruction_revision})."
            ),
        ),
    )
    return reset_implementer_sections_on_instruction_change(
        rewritten,
        previous_instruction_revision=previous_instruction_revision,
        next_instruction_revision=instruction_revision,
    )


def _instruction_revision(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def _primary_instruction_item(instruction: str) -> str:
    for raw_line in instruction.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        match = MARKDOWN_ITEM_RE.match(stripped)
        candidate = match.group("value").strip() if match is not None else stripped
        normalized = candidate.lower().strip()
        if normalized:
            return normalized
    return ""


def _state_items(value: str) -> tuple[str, ...]:
    """Return normalized markdown-item payloads from one bridge section."""
    items: list[str] = []
    for raw_line in value.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        match = MARKDOWN_ITEM_RE.match(stripped)
        candidate = match.group("value").strip() if match is not None else stripped
        normalized = candidate.lower().strip()
        if normalized:
            items.append(normalized)
    return tuple(items)
