"""Typed execution-checklist phase parsing for governed plan docs."""

from __future__ import annotations

import re
from collections.abc import Sequence

from ..markdown_sections import parse_markdown_sections
from ..text_utils import normalize_inline_markdown
from .planning_ir_models import PlanDependency, PlanPhase, PlanTask

_PHASE_HEADING_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$")
_CHECKLIST_ITEM_RE = re.compile(r"^- \[(?P<mark>[ xX])\]\s+(?P<body>.+)$")
_TASK_HEADER_RE = re.compile(r"^`(?P<task_id>[^`]+)`\s+(?P<summary>.+)$")
_PHASE_METADATA_RE = re.compile(r"^Phase metadata:\s*(?P<body>.+)$", re.IGNORECASE)
_TASK_FIELD_RE = re.compile(
    r"^(?P<key>owner_doc|status|depends_on|dependencies)\s*:\s*(?P<value>.+)$",
    re.IGNORECASE,
)
_PHASE_FIELD_RE = re.compile(
    r"(?P<key>phase_id|owner_doc|status|depends_on|summary)\s*=\s*(?P<value>[^;]+)"
)


def parse_execution_plan_phases(markdown_text: str) -> tuple[PlanPhase, ...]:
    """Parse typed phase/task metadata from ``## Execution Checklist``."""
    checklist = parse_markdown_sections(markdown_text).get("Execution Checklist", "")
    if not checklist:
        return ()

    phases: list[PlanPhase] = []
    current_title = ""
    current_metadata: dict[str, str] = {}
    current_tasks: list[PlanTask] = []
    task_state: dict[str, object] | None = None

    def flush_task() -> None:
        nonlocal task_state
        if not task_state:
            return
        task_id = str(task_state.get("task_id") or "").strip()
        summary = str(task_state.get("summary") or "").strip()
        if task_id and summary:
            current_tasks.append(
                PlanTask(
                    task_id=task_id,
                    summary=summary,
                    owner_doc=str(task_state.get("owner_doc") or "").strip(),
                    status=str(task_state.get("status") or "pending").strip() or "pending",
                    phase_id=str(current_metadata.get("phase_id") or "").strip(),
                    phase_title=current_title,
                    dependencies=_parse_dependencies(task_state.get("depends_on")),
                    anchor_ref=f"checklist:{task_id}",
                )
            )
        task_state = None

    def flush_phase() -> None:
        flush_task()
        if not current_title and not current_tasks and not current_metadata:
            return
        if not current_tasks and not current_metadata:
            return
        phase_id = str(current_metadata.get("phase_id") or "").strip()
        if not phase_id and current_tasks:
            phase_id = _phase_id_from_title(current_title)
        phases.append(
            PlanPhase(
                phase_id=phase_id,
                title=current_title,
                owner_doc=str(current_metadata.get("owner_doc") or "").strip(),
                status=_phase_status(current_metadata, current_tasks),
                dependencies=_parse_dependencies(current_metadata.get("depends_on")),
                tasks=tuple(current_tasks),
                summary=str(current_metadata.get("summary") or "").strip(),
                anchor_ref=f"phase:{phase_id.casefold()}" if phase_id else "",
            )
        )
        current_tasks.clear()
        current_metadata.clear()

    for raw_line in checklist.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_task()
            continue

        phase_match = _PHASE_HEADING_RE.match(stripped)
        if phase_match is not None:
            flush_phase()
            current_title = phase_match.group("title").strip()
            continue

        phase_metadata_match = _PHASE_METADATA_RE.match(stripped)
        if phase_metadata_match is not None:
            current_metadata = _parse_phase_metadata(phase_metadata_match.group("body"))
            continue

        checklist_match = _CHECKLIST_ITEM_RE.match(stripped)
        if checklist_match is not None:
            flush_task()
            task_state = _typed_task_state(
                checklist_mark=checklist_match.group("mark"),
                body=checklist_match.group("body").strip(),
            )
            continue

        if task_state is not None:
            field_match = _TASK_FIELD_RE.match(stripped)
            if field_match is None:
                continue
            task_state[str(field_match.group("key")).casefold()] = _clean_value(
                field_match.group("value")
            )

    flush_phase()
    return tuple(phase for phase in phases if phase.phase_id or phase.tasks)


def first_actionable_task(phases: Sequence[PlanPhase]) -> PlanTask | None:
    """Return the current in-progress task, or the next open task."""
    for status in ("in_progress", "pending", "blocked"):
        for phase in phases:
            for task in phase.tasks:
                if task.status == status:
                    return task
    return None


def _typed_task_state(*, checklist_mark: str, body: str) -> dict[str, object] | None:
    task_match = _TASK_HEADER_RE.match(body)
    if task_match is None:
        return None
    status = "done" if checklist_mark.lower() == "x" else "pending"
    return {
        "task_id": _clean_value(task_match.group("task_id")),
        "summary": normalize_inline_markdown(task_match.group("summary").strip()),
        "status": status,
        "depends_on": "",
        "owner_doc": "",
    }


def _parse_phase_metadata(raw_value: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for match in _PHASE_FIELD_RE.finditer(raw_value):
        parsed[match.group("key").casefold()] = _clean_value(match.group("value"))
    return parsed


def _parse_dependencies(raw_value: object) -> tuple[PlanDependency, ...]:
    text = _clean_value(raw_value)
    if not text or text.casefold() == "none":
        return ()
    items = [
        _clean_dependency_value(item)
        for item in text.split(",")
        if _clean_dependency_value(item)
    ]
    return tuple(
        PlanDependency(
            dependency_id=item,
            dependency_kind=_dependency_kind(item),
        )
        for item in items
    )


def _dependency_kind(value: str) -> str:
    if "-T" in value:
        return "task"
    if "-P" in value or value.startswith("MP") or value.startswith("P"):
        return "phase"
    return "task"


def _phase_id_from_title(title: str) -> str:
    match = re.search(r"\b(P\d+)\b", title)
    return match.group(1) if match is not None else ""


def _phase_status(metadata: dict[str, str], tasks: Sequence[PlanTask]) -> str:
    explicit = str(metadata.get("status") or "").strip()
    if explicit:
        return explicit
    if tasks and all(task.status == "done" for task in tasks):
        return "done"
    if any(task.status == "in_progress" for task in tasks):
        return "in_progress"
    if tasks:
        return "pending"
    return "unknown"


def _clean_dependency_value(value: object) -> str:
    return _clean_value(value).strip("`").strip()


def _clean_value(value: object) -> str:
    text = normalize_inline_markdown(str(value or "").strip())
    if text.startswith("`") and text.endswith("`"):
        return text[1:-1].strip()
    return text


__all__ = ["first_actionable_task", "parse_execution_plan_phases"]
