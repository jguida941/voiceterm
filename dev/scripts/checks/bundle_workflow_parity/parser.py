"""Workflow parsing helpers for bundle/workflow parity checks."""

from __future__ import annotations

import re

RUN_STEP_RE = re.compile(r"^(?P<indent>\s*)(?:-\s*)?run:\s*(?P<value>.*)$")


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _normalize_command(command: str) -> str:
    tokens = command.strip().split()
    while tokens and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[0]):
        tokens.pop(0)
    return _normalize_space(" ".join(tokens))


def _normalize_workflow_text(raw_text: str) -> str:
    normalized = raw_text.replace("\\\n", " ").replace("\\\r\n", " ")
    return _normalize_space(normalized)


def _is_yaml_block_scalar(value: str) -> bool:
    stripped = value.strip()
    return stripped.startswith("|") or stripped.startswith(">")


def _dedent_yaml_block(lines: list[str]) -> str:
    min_indent: int | None = None
    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if min_indent is None or indent < min_indent:
            min_indent = indent
    if min_indent is None:
        return ""
    dedented_lines = [line[min_indent:] if line.strip() else "" for line in lines]
    return "\n".join(dedented_lines)


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _collect_indented_block(
    lines: list[str],
    *,
    start_index: int,
    parent_indent: int,
) -> tuple[list[str], int]:
    block_lines: list[str] = []
    index = start_index
    while index < len(lines):
        next_line = lines[index]
        if next_line.strip() and _line_indent(next_line) <= parent_indent:
            break
        block_lines.append(next_line)
        index += 1
    return block_lines, index


def _locate_header(
    lines: list[str],
    *,
    header: str,
) -> tuple[int | None, int]:
    for index, line in enumerate(lines):
        if line.strip() == header:
            return _line_indent(line), index + 1
    return None, len(lines)


def _iter_named_blocks(
    lines: list[str],
    *,
    start_index: int,
    parent_indent: int,
    child_indent: int,
):
    index = start_index
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        indent = _line_indent(line)
        if indent <= parent_indent:
            break
        if indent != parent_indent + child_indent or not stripped.endswith(":"):
            index += 1
            continue
        block_lines, index = _collect_indented_block(
            lines,
            start_index=index + 1,
            parent_indent=indent,
        )
        yield stripped[:-1], block_lines


def _extract_workflow_run_scopes(workflow_text: str) -> list[str]:
    lines = workflow_text.splitlines()
    scopes: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        match = RUN_STEP_RE.match(line)
        if match is None:
            index += 1
            continue
        run_indent = len(match.group("indent"))
        run_value = match.group("value").strip()
        if _is_yaml_block_scalar(run_value):
            block_lines, index = _collect_indented_block(
                lines,
                start_index=index + 1,
                parent_indent=run_indent,
            )
            normalized_scope = _normalize_workflow_text(_dedent_yaml_block(block_lines))
            if normalized_scope:
                scopes.append(normalized_scope)
            continue
        if run_value:
            normalized_scope = _normalize_workflow_text(run_value.strip("'\""))
            if normalized_scope:
                scopes.append(normalized_scope)
        index += 1
    return scopes


def _extract_workflow_job_scopes(workflow_text: str) -> dict[str, list[str]]:
    lines = workflow_text.splitlines()
    job_scopes: dict[str, list[str]] = {}
    jobs_indent, start_index = _locate_header(lines, header="jobs:")
    if jobs_indent is None:
        return job_scopes

    for job_name, job_lines in _iter_named_blocks(
        lines,
        start_index=start_index,
        parent_indent=jobs_indent,
        child_indent=2,
    ):
        scopes = _extract_workflow_run_scopes("\n".join(job_lines))
        if scopes:
            job_scopes[job_name] = scopes

    return job_scopes
