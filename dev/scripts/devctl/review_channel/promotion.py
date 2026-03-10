"""Repo-owned next-task promotion helpers for the markdown review bridge."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from ..common import display_path
from .handoff import (
    IDLE_FINDING_MARKERS,
    IDLE_NEXT_ACTION_MARKERS,
    RESOLVED_VERDICT_MARKERS,
    BridgeSnapshot,
    extract_bridge_snapshot,
)

DEFAULT_PROMOTION_PLAN_REL = "dev/active/continuous_swarm.md"
EXECUTION_CHECKLIST_HEADING = "## Execution Checklist"
CHECKLIST_ITEM_RE = re.compile(r"^- \[(?P<mark>[ xX])\]\s+(?P<body>.+)$")
SECTION_RE = re.compile(r"^##\s+")
SUBSECTION_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$")
PROMOTABLE_INSTRUCTION_MARKERS = (
    *IDLE_NEXT_ACTION_MARKERS,
    *RESOLVED_VERDICT_MARKERS,
    "complete",
    "completed",
    "done",
    "fixed",
    "accepted",
)
CURRENT_INSTRUCTION_SECTION = "Current Instruction For Claude"
CURRENT_INSTRUCTION_SECTION_RE = re.compile(
    rf"(^## {re.escape(CURRENT_INSTRUCTION_SECTION)}\s*$\n)(.*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)


@dataclass(frozen=True)
class PromotionCandidate:
    """One unchecked plan item promoted into bridge instruction text."""

    instruction: str
    source_path: str
    phase_heading: str | None
    checklist_item: str


def promotion_candidate_to_dict(
    candidate: PromotionCandidate | None,
) -> dict[str, object] | None:
    """Convert a promotion candidate into JSON-friendly data."""
    if candidate is None:
        return None
    return asdict(candidate)


def derive_promotion_candidate(
    *,
    repo_root: Path,
    promotion_plan_path: Path,
    require_exists: bool = False,
) -> PromotionCandidate | None:
    """Return the first unchecked execution-checklist item, if any."""
    if not promotion_plan_path.exists():
        if require_exists:
            raise ValueError(
                "Promotion plan is missing: "
                f"{display_path(promotion_plan_path, repo_root=repo_root)}"
            )
        return None

    plan_text = promotion_plan_path.read_text(encoding="utf-8")
    unchecked_items = _iter_unchecked_checklist_items(plan_text)
    candidate_item = unchecked_items[0] if unchecked_items else None
    if candidate_item is None:
        if require_exists:
            raise ValueError(
                "Promotion plan has no unchecked execution-checklist items: "
                f"{display_path(promotion_plan_path, repo_root=repo_root)}"
            )
        return None

    phase_heading, checklist_item = candidate_item
    phase_prefix = f"{phase_heading}: " if phase_heading else ""
    source_path = display_path(promotion_plan_path, repo_root=repo_root)
    return PromotionCandidate(
        instruction=(
            f"- Next scoped plan item ({source_path}): "
            f"{phase_prefix}{checklist_item}"
        ),
        source_path=source_path,
        phase_heading=phase_heading,
        checklist_item=checklist_item,
    )


def validate_promotion_ready(snapshot: BridgeSnapshot) -> list[str]:
    """Return fail-closed bridge-state errors before promoting the next item."""
    errors: list[str] = []
    current_verdict = snapshot.sections.get("Current Verdict", "").strip().lower()
    open_findings = snapshot.sections.get("Open Findings", "").strip().lower()
    current_instruction = (
        snapshot.sections.get(CURRENT_INSTRUCTION_SECTION, "").strip().lower()
    )

    if not current_verdict:
        errors.append("Missing `Current Verdict`; cannot promote from unknown review state.")
    elif not _contains_any(current_verdict, RESOLVED_VERDICT_MARKERS):
        errors.append(
            "`Current Verdict` must show an accepted/resolved slice before "
            "the next task is promoted."
        )

    if open_findings and not _contains_any(open_findings, IDLE_FINDING_MARKERS):
        errors.append(
            "`Open Findings` still contains unresolved blockers; resolve or "
            "clear them before promoting the next task."
        )

    if current_instruction and not _contains_any(
        current_instruction,
        PROMOTABLE_INSTRUCTION_MARKERS,
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
    """Rewrite only the live Claude-instruction section in `code_audit.md`."""
    replacement = lambda match: f"{match.group(1)}\n{instruction.strip()}\n\n"
    rewritten, count = CURRENT_INSTRUCTION_SECTION_RE.subn(replacement, bridge_text, count=1)
    if count != 1:
        raise ValueError(
            f"Unable to locate `{CURRENT_INSTRUCTION_SECTION}` in the markdown bridge."
        )
    return rewritten


def promote_bridge_instruction(
    *,
    repo_root: Path,
    bridge_path: Path,
    promotion_plan_path: Path,
) -> PromotionCandidate:
    """Promote the next unchecked plan item into the live bridge instruction."""
    bridge_text = bridge_path.read_text(encoding="utf-8")
    snapshot = extract_bridge_snapshot(bridge_text)
    errors = validate_promotion_ready(snapshot)
    if errors:
        raise ValueError("; ".join(errors))

    candidate = derive_promotion_candidate(
        repo_root=repo_root,
        promotion_plan_path=promotion_plan_path,
        require_exists=True,
    )
    assert candidate is not None
    updated_text = rewrite_current_instruction(
        bridge_text=bridge_text,
        instruction=candidate.instruction,
    )
    bridge_path.write_text(updated_text, encoding="utf-8")
    return candidate


def _iter_unchecked_checklist_items(
    plan_text: str,
) -> list[tuple[str | None, str]]:
    in_execution_checklist = False
    current_phase: str | None = None
    current_item_mark: str | None = None
    current_item_lines: list[str] = []
    unchecked_items: list[tuple[str | None, str]] = []

    def flush_current_item() -> None:
        nonlocal current_item_mark, current_item_lines
        if current_item_mark == " " and current_item_lines:
            unchecked_items.append(
                (current_phase, _normalize_item_text(current_item_lines))
            )
        current_item_mark = None
        current_item_lines = []

    for raw_line in plan_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not in_execution_checklist:
            if stripped == EXECUTION_CHECKLIST_HEADING:
                in_execution_checklist = True
            continue

        if SECTION_RE.match(stripped) and not stripped.startswith("### "):
            flush_current_item()
            break

        subsection_match = SUBSECTION_RE.match(stripped)
        if subsection_match is not None:
            flush_current_item()
            current_phase = subsection_match.group("title").strip()
            continue

        checklist_match = CHECKLIST_ITEM_RE.match(stripped)
        if checklist_match is not None:
            flush_current_item()
            current_item_mark = checklist_match.group("mark")
            current_item_lines = [checklist_match.group("body").strip()]
            continue

        if current_item_mark is not None and line.startswith("      "):
            current_item_lines.append(stripped)
            continue

        if not stripped:
            flush_current_item()

    flush_current_item()
    return unchecked_items


def _normalize_item_text(lines: list[str]) -> str:
    return " ".join(part.strip() for part in lines if part.strip())


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in markers)
