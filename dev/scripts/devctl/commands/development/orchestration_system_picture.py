"""System-picture signals consumed by `/develop` orchestration."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from ...context_graph.snapshot_payload import _SNAPSHOT_DIR
from ...governance.push_state import current_head_commit_sha
from ...repo_packs import active_path_config
from .models import DevelopmentOrchestrationSignal

_SYSTEM_PICTURE_SUMMARY_REL = "latest/summary.json"
_CONTEXT_GRAPH_COMMAND = (
    "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md"
)
_SYSTEM_PICTURE_FRESHNESS_CHECK = (
    "python3 dev/scripts/checks/check_system_picture_freshness.py --format md"
)


def system_picture_signals(
    repo_root: Path,
) -> tuple[DevelopmentOrchestrationSignal, ...]:
    payload = _load_latest_system_picture(repo_root)
    current_sections = _current_system_picture_sections_by_id(repo_root)
    if not payload:
        return (_missing_system_picture_signal(),)
    rows: list[DevelopmentOrchestrationSignal] = []
    for section in _sections(payload):
        section_id = _text(section.get("section_id"))
        section = current_sections.get(section_id, section)
        status = _text(section.get("status"))
        title = _text(section.get("title")) or section_id
        if status in {"stale", "missing"}:
            rows.append(_system_picture_signal(section_id, status, title, section))
    return tuple(rows)


def _missing_system_picture_signal() -> DevelopmentOrchestrationSignal:
    return DevelopmentOrchestrationSignal(
        source="system-picture",
        signal_id="system-picture",
        status="missing",
        summary="No latest SystemPicture artifact was available.",
        source_surface="system-picture",
        severity="high",
        recommended_action="generate_system_picture",
        closure_check_command=_SYSTEM_PICTURE_FRESHNESS_CHECK,
        suggested_command="python3 dev/scripts/devctl.py system-picture --format md",
    )


def _system_picture_signal(
    section_id: str,
    status: str,
    title: str,
    section: Mapping[str, object],
) -> DevelopmentOrchestrationSignal:
    command = _text(section.get("source_command"))
    return DevelopmentOrchestrationSignal(
        source="system-picture",
        signal_id=section_id,
        status=status,
        summary=_section_summary(title=title, section=section),
        source_surface=_source_surface(section, default="system-picture"),
        severity=_system_picture_severity(status),
        recommended_action=_system_picture_action(section_id, status),
        closure_check_command=_system_picture_closure_check(section_id),
        source_command=command,
        suggested_command=command,
        source_path=_text(section.get("source_path")),
    )


def _load_latest_system_picture(repo_root: Path) -> Mapping[str, object]:
    path = (
        repo_root
        / active_path_config().system_picture_output_root_rel
        / _SYSTEM_PICTURE_SUMMARY_REL
    )
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _current_system_picture_sections_by_id(
    repo_root: Path,
) -> Mapping[str, Mapping[str, object]]:
    current_graph = _current_graph_section(repo_root)
    if not current_graph:
        return {}
    return {"graph": current_graph}


def _current_graph_section(repo_root: Path) -> Mapping[str, object]:
    head = current_head_commit_sha(repo_root=repo_root)
    if not head:
        return {}
    snapshot_dir = repo_root / _SNAPSHOT_DIR
    matches = sorted(snapshot_dir.glob(f"{head}_*.json"))
    if not matches:
        return {}
    latest_path = matches[-1]
    return {
        "section_id": "graph",
        "title": "Context Graph",
        "status": "current",
        "source_path": _rel_path(repo_root, latest_path),
        "source_command": _CONTEXT_GRAPH_COMMAND,
    }


def _sections(payload: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    sections = payload.get("sections")
    if not isinstance(sections, Sequence) or isinstance(sections, (str, bytes)):
        return ()
    return tuple(section for section in sections if isinstance(section, Mapping))


def _section_summary(*, title: str, section: Mapping[str, object]) -> str:
    notes = section.get("notes")
    if isinstance(notes, Sequence) and not isinstance(notes, (str, bytes)):
        for note in notes:
            text = _text(note)
            if text:
                return f"{title}: {text}"
    return f"{title} is {_text(section.get('status')) or 'not current'}."


def _rel_path(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _source_surface(section: Mapping[str, object], *, default: str) -> str:
    return (
        _text(section.get("source_surface"))
        or _text(section.get("surface"))
        or default
    )


def _system_picture_severity(status: str) -> str:
    if status == "missing":
        return "high"
    if status == "stale":
        return "medium"
    return "info"


def _system_picture_action(section_id: str, status: str) -> str:
    if section_id == "graph" and status == "stale":
        return "refresh_context_graph"
    if status == "missing":
        return "generate_missing_projection"
    if status == "stale":
        return "refresh_stale_projection"
    return "inspect_system_picture"


def _system_picture_closure_check(section_id: str) -> str:
    if section_id == "graph":
        return _SYSTEM_PICTURE_FRESHNESS_CHECK
    return "python3 dev/scripts/devctl.py system-picture --format md"


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["system_picture_signals"]
