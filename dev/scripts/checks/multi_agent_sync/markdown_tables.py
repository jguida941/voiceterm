"""Markdown table parsing and shared text helpers for the sync guard."""

from __future__ import annotations

from .models import AGENT_NAME_PATTERN


def _strip_code_ticks(value: str) -> str:
    text = value.strip()
    if text.startswith("`") and text.endswith("`"):
        return text[1:-1]
    return text


def _normalize(value: str) -> str:
    return " ".join(_strip_code_ticks(value).split())


def _split_table_row(line: str) -> list[str]:
    return [_strip_code_ticks(col.strip()) for col in line.strip().split("|")[1:-1]]


def _extract_table_rows(markdown: str, heading: str) -> tuple[list[dict], str | None]:
    lines = markdown.splitlines()
    heading_index = -1
    for idx, line in enumerate(lines):
        if line.strip() == heading:
            heading_index = idx
            break
    if heading_index < 0:
        return [], f"Missing heading: {heading}"

    table_start = -1
    for idx in range(heading_index + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("|"):
            table_start = idx
            break
        if stripped.startswith("## "):
            break
    if table_start < 0:
        return [], f"Missing table under heading: {heading}"

    table_lines: list[str] = []
    for idx in range(table_start, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("|"):
            table_lines.append(stripped)
            continue
        if table_lines:
            break
    if len(table_lines) < 2:
        return [], f"Incomplete table under heading: {heading}"

    headers = _split_table_row(table_lines[0])
    if not headers:
        return [], f"Invalid table header under heading: {heading}"

    rows: list[dict] = []
    for row_line in table_lines[2:]:
        columns = _split_table_row(row_line)
        if len(columns) != len(headers):
            return [], f"Malformed row under heading: {heading}"
        rows.append({headers[i]: columns[i] for i in range(len(headers))})
    return rows, None


def _rows_by_key(rows: list[dict], field: str) -> dict[str, dict]:
    mapping: dict[str, dict] = {}
    for row in rows:
        key = _normalize(str(row.get(field, ""))).upper()
        if key:
            mapping[key] = row
    return mapping


def _sorted_agents(agents: set[str]) -> list[str]:
    return sorted(
        agents,
        key=lambda agent: (
            (0, int(match.group(1)))
            if (match := AGENT_NAME_PATTERN.fullmatch(agent))
            else (1, agent)
        ),
    )


def _sorted_signers(signers: set[str]) -> list[str]:
    agents = _sorted_agents({signer for signer in signers if signer != "ORCHESTRATOR"})
    return agents + (["ORCHESTRATOR"] if "ORCHESTRATOR" in signers else [])

