"""Repo-owned next-task promotion helpers for the markdown review bridge."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from ..common import display_path
from ..context_graph.escalation import (
    ContextEscalationPacket,
    append_context_packet_markdown,
    build_context_escalation_packet,
    collect_query_terms,
)
from ..repo_packs import active_path_config
from .bridge_file import rewrite_bridge_markdown
from .handoff import (
    IDLE_FINDING_MARKERS,
    IDLE_NEXT_ACTION_MARKERS,
    RESOLVED_VERDICT_MARKERS,
    BridgeSnapshot,
    extract_bridge_snapshot,
)
from .promotion_support import (
    InstructionRewriteContext,
    instruction_needs_plan_promotion,
    rewrite_instruction_and_metadata,
)

# Backward-compat alias sourced from the frozen path config
DEFAULT_PROMOTION_PLAN_REL = active_path_config().promotion_plan_rel
EXECUTION_CHECKLIST_HEADING = "## Execution Checklist"
CHECKLIST_ITEM_RE = re.compile(r"^- \[(?P<mark>[ xX])\]\s+(?P<body>.+)$")
SECTION_RE = re.compile(r"^##\s+")
SUBSECTION_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$")
PROMOTABLE_INSTRUCTION_MARKERS = (
    *IDLE_NEXT_ACTION_MARKERS,
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
CURRENT_INSTRUCTION_SECTION = "Current Instruction For Claude"


@dataclass(frozen=True)
class PromotionCandidate:
    """One unchecked plan item promoted into bridge instruction text."""

    instruction: str
    source_path: str
    phase_heading: str | None
    checklist_item: str
    context_packet: ContextEscalationPacket | None = None

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
            raise ValueError("Promotion plan is missing: " f"{display_path(promotion_plan_path, repo_root=repo_root)}")
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
    context_packet = _build_promotion_context_packet(
        source_path=source_path,
        phase_heading=phase_heading,
        checklist_item=checklist_item,
    )
    instruction = append_context_packet_markdown(
        f"- Next scoped plan item ({source_path}): {phase_prefix}{checklist_item}",
        context_packet,
    )
    return PromotionCandidate(
        instruction=instruction,
        source_path=source_path,
        phase_heading=phase_heading,
        checklist_item=checklist_item,
        context_packet=context_packet,
    )


def validate_promotion_ready(snapshot: BridgeSnapshot) -> list[str]:
    """Return fail-closed bridge-state errors before promoting the next item."""
    errors: list[str] = []
    current_verdict = snapshot.sections.get("Current Verdict", "").strip().lower()
    open_findings = snapshot.sections.get("Open Findings", "").strip().lower()
    current_instruction = snapshot.sections.get(CURRENT_INSTRUCTION_SECTION, "").strip().lower()

    if not current_verdict:
        errors.append("Missing `Current Verdict`; cannot promote from unknown review state.")
    elif not _contains_any(current_verdict, RESOLVED_VERDICT_MARKERS):
        errors.append("`Current Verdict` must show an accepted/resolved slice before " "the next task is promoted.")

    if open_findings and not _contains_any(open_findings, IDLE_FINDING_MARKERS):
        errors.append(
            "`Open Findings` still contains unresolved blockers; resolve or "
            "clear them before promoting the next task."
        )

    if current_instruction and not (
        _contains_any(current_instruction, PROMOTABLE_INSTRUCTION_MARKERS)
        or instruction_needs_plan_promotion(current_instruction)
    ):
        errors.append(
            "`Current Instruction For Claude` still looks live; refuse to " "overwrite an active instruction."
        )

    return errors


def promote_bridge_instruction(
    *,
    repo_root: Path,
    bridge_path: Path,
    promotion_plan_path: Path,
    expected_instruction_revision: str | None = None,
) -> PromotionCandidate:
    """Promote the next unchecked plan item into the live bridge instruction."""
    candidate = derive_promotion_candidate(
        repo_root=repo_root,
        promotion_plan_path=promotion_plan_path,
        require_exists=True,
    )
    assert candidate is not None

    def transform(bridge_text: str) -> str:
        snapshot = extract_bridge_snapshot(bridge_text)
        errors = validate_promotion_ready(snapshot)
        if errors:
            raise ValueError("; ".join(errors))
        return rewrite_instruction_and_metadata(
            bridge_text=bridge_text,
            instruction=candidate.instruction,
            context=InstructionRewriteContext(
                repo_root=repo_root,
                bridge_path=bridge_path,
                reviewer_mode=snapshot.metadata.get("reviewer_mode"),
                reason="next-plan-item",
                expected_instruction_revision=expected_instruction_revision,
            ),
        )

    rewrite_bridge_markdown(bridge_path, transform=transform)
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
            unchecked_items.append((current_phase, _normalize_item_text(current_item_lines)))
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


def _build_promotion_context_packet(
    *,
    source_path: str,
    phase_heading: str | None,
    checklist_item: str,
) -> ContextEscalationPacket | None:
    query_terms = collect_query_terms(
        [source_path, phase_heading, checklist_item],
        max_terms=4,
    )
    return build_context_escalation_packet(
        trigger="review-channel-promotion",
        query_terms=query_terms,
        options={"max_chars": 700},
    )


def resolve_scope_plan_path(
    *,
    repo_root: Path,
    scope_value: str,
) -> Path:
    """Resolve a ``--scope`` CLI value to an active-plan filesystem path.

    Accepts:
    - A bare filename: ``review_probes`` or ``review_probes.md``
    - A relative path: ``dev/active/review_probes.md``
    - An MP id: ``MP-368`` or ``368`` (scans INDEX.md for matching scope)
    """
    active_dir = repo_root / "dev" / "active"

    # Try as a relative path first.
    if "/" in scope_value:
        candidate = repo_root / scope_value
        if candidate.exists():
            return candidate
        raise ValueError(f"--scope path not found: {scope_value}")

    # Try as bare filename (with or without .md).
    name = scope_value if scope_value.endswith(".md") else f"{scope_value}.md"
    candidate = active_dir / name
    if candidate.exists():
        return candidate

    # Try as MP id (scan INDEX.md for matching scope).
    mp_query = scope_value.upper()
    if not mp_query.startswith("MP-"):
        mp_query = f"MP-{scope_value}"
    index_path = active_dir / "INDEX.md"
    if index_path.exists():
        for line in index_path.read_text(encoding="utf-8").splitlines():
            if mp_query in line and "| `dev/active/" in line:
                path_start = line.index("`dev/active/") + 1
                path_end = line.index("`", path_start + 1)
                found = repo_root / line[path_start:path_end]
                if found.exists():
                    return found

    raise ValueError(
        f"--scope could not resolve '{scope_value}' to an active-plan doc. "
        f"Try a filename (e.g. review_probes), path (dev/active/review_probes.md), "
        f"or MP id (MP-368)."
    )


def scope_bridge_instruction(
    *,
    repo_root: Path,
    bridge_path: Path,
    scope_plan_path: Path,
    expected_instruction_revision: str | None = None,
) -> PromotionCandidate:
    """Rewrite the bridge instruction from a scoped active-plan doc.

    Unlike ``promote_bridge_instruction``, this does NOT validate that the
    current instruction is idle/resolved — the operator explicitly asked to
    re-scope, so we overwrite unconditionally. When the bridge file does not
    exist the candidate is still derived but no bridge rewrite occurs.
    """
    candidate = derive_promotion_candidate(
        repo_root=repo_root,
        promotion_plan_path=scope_plan_path,
        require_exists=True,
    )
    assert candidate is not None
    if bridge_path.exists():
        source = display_path(scope_plan_path, repo_root=repo_root)
        instruction = f"Scoped from `{source}` via `--scope`.\n\n" f"{candidate.instruction}"

        def transform(bridge_text: str) -> str:
            snapshot = extract_bridge_snapshot(bridge_text)
            return rewrite_instruction_and_metadata(
                bridge_text=bridge_text,
                instruction=instruction,
                context=InstructionRewriteContext(
                    repo_root=repo_root,
                    bridge_path=bridge_path,
                    reviewer_mode=snapshot.metadata.get("reviewer_mode"),
                    reason=f"scope:{source}",
                    expected_instruction_revision=expected_instruction_revision,
                ),
            )

        rewrite_bridge_markdown(bridge_path, transform=transform)
    return candidate


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in markers)
