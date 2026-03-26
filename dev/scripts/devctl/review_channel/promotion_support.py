"""Instruction-shape and metadata helpers for bridge promotion writes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from pathlib import Path

from .instruction_reset import reset_implementer_sections_on_instruction_change
from .peer_liveness import normalize_reviewer_mode
from .reviewer_state_support import (
    ReviewerMetadataUpdate,
    current_instruction_revision_from_bridge_text,
    write_reviewer_metadata,
)
from .write_preconditions import assert_expected_instruction_revision

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


@dataclass(frozen=True)
class InstructionRewriteContext:
    """Shared metadata for one instruction rewrite."""

    repo_root: Path
    bridge_path: Path
    reviewer_mode: str | None
    reason: str
    expected_instruction_revision: str | None = None


def instruction_needs_plan_promotion(instruction: str) -> bool:
    """Return True when instruction text is a generic progression placeholder."""
    lowered = instruction.strip().lower()
    if not lowered:
        return True
    if "next scoped plan item (" in lowered:
        return False
    return any(marker in lowered for marker in _GENERIC_PROGRESS_MARKERS)


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
    assert_expected_instruction_revision(
        bridge_text=bridge_text,
        expected_instruction_revision=context.expected_instruction_revision,
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
