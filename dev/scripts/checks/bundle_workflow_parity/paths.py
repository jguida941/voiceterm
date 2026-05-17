"""Path-filter helpers for bundle/workflow parity checks."""

from __future__ import annotations

import re

if __package__:
    from .parser import _locate_header
else:  # pragma: no cover - standalone script fallback
    from parser import _locate_header


def _strip_yaml_quotes(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        return stripped[1:-1]
    return stripped


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _collect_paths(
    lines: list[str],
    *,
    start_index: int,
    paths_indent: int,
) -> tuple[list[str], int]:
    paths: list[str] = []
    index = start_index
    while index < len(lines):
        path_line = lines[index]
        path_stripped = path_line.strip()
        if not path_stripped:
            index += 1
            continue
        if _line_indent(path_line) <= paths_indent:
            break
        if path_stripped.startswith("- "):
            path_value = _strip_yaml_quotes(path_stripped[2:])
            if path_value:
                paths.append(path_value)
        index += 1
    return paths, index


def _collect_event_paths(
    lines: list[str],
    *,
    start_index: int,
    event_indent: int,
    event_name: str,
) -> tuple[list[str], int]:
    index = start_index
    if event_name not in {"push", "pull_request"}:
        while index < len(lines):
            nested_line = lines[index]
            if nested_line.strip() and _line_indent(nested_line) <= event_indent:
                break
            index += 1
        return [], index

    while index < len(lines):
        nested_line = lines[index]
        nested_stripped = nested_line.strip()
        if not nested_stripped:
            index += 1
            continue
        nested_indent = _line_indent(nested_line)
        if nested_indent <= event_indent:
            break
        index += 1
        if nested_stripped != "paths:":
            continue
        return _collect_paths(lines, start_index=index, paths_indent=nested_indent)
    return [], index


def _extract_workflow_trigger_paths(workflow_text: str) -> dict[str, list[str]]:
    lines = workflow_text.splitlines()
    trigger_paths: dict[str, list[str]] = {}
    on_indent, index = _locate_header(lines, header="on:")
    if on_indent is None:
        return trigger_paths

    while index < len(lines):
        event_line = lines[index]
        event_stripped = event_line.strip()
        if not event_stripped:
            index += 1
            continue
        event_indent = _line_indent(event_line)
        if event_indent <= on_indent:
            break
        index += 1
        if not event_stripped.endswith(":"):
            continue
        event_name = event_stripped[:-1]
        paths, index = _collect_event_paths(
            lines,
            start_index=index,
            event_indent=event_indent,
            event_name=event_name,
        )
        if paths:
            trigger_paths[event_name] = paths

    return trigger_paths


def _has_workflow_path_filter(workflow_text: str, path_filter: str) -> bool:
    pattern = re.compile(
        rf"^\s*-\s*[\"']?{re.escape(path_filter)}[\"']?\s*$",
        re.MULTILINE,
    )
    return pattern.search(workflow_text) is not None


def _collect_missing_path_filters(
    *,
    target: dict,
    workflow_text: str,
    workflow_trigger_paths: dict[str, list[str]],
) -> tuple[list[str], dict[str, list[str]]]:
    required_path_filters = list(target.get("required_path_filters", ()))
    required_trigger_events = tuple(target.get("required_trigger_events", ()))
    missing_trigger_path_filters: dict[str, list[str]] = {}
    if required_trigger_events:
        for event_name in required_trigger_events:
            configured_paths = workflow_trigger_paths.get(event_name, [])
            missing_paths = [
                path_filter
                for path_filter in required_path_filters
                if path_filter not in configured_paths
            ]
            if missing_paths:
                missing_trigger_path_filters[event_name] = missing_paths
        return [], missing_trigger_path_filters
    missing_path_filters = [
        path_filter
        for path_filter in required_path_filters
        if not _has_workflow_path_filter(workflow_text, path_filter)
    ]
    return missing_path_filters, missing_trigger_path_filters
