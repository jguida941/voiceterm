"""Parsing helpers for the runtime-spine closure guard."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from pathlib import Path

from dev.scripts.devctl.runtime.runtime_spine_closure_state import (
    RuntimeSpineClosureRow,
    RuntimeSpineClosureState,
    RuntimeSpineItem,
)

SECTION_RE = re.compile(r"^## 0\.6\b.*$", re.MULTILINE)
NEXT_SECTION_RE = re.compile(r"^## \d", re.MULTILINE)
CLOSURE_RULE_TOKEN = "**Closure rule:**"
RUNTIME_SPINE_CHECK_ID = "runtime_spine_closure"
RISK_MARKER_LABELS = {
    "\u274c": "missing",
    "\u26a0": "partial",
}
MATRIX_HEADING = "### Runtime Spine Closure Matrix"
REQUIRED_MATRIX_COLUMNS = (
    "runtime object",
    "active owner",
    "typed contract",
    "producer",
    "consumer",
    "regression proof",
    "graph/context visibility",
    "carry-forward/compaction path",
    "priority",
)
PLACEHOLDER_RE = re.compile(r"^\s*(?:|[-\u2014]+|n/?a|none|tbd|todo|unknown)\s*$", re.IGNORECASE)
OWNER_RE = re.compile(r"\bMP\d*-P\d+(?:-[A-Z0-9]+)?\b|\bMP-\d+\b", re.IGNORECASE)
PROOF_RE = re.compile(r"\b(?:check|probe|test)_[A-Za-z0-9_]+\b")
PRIORITY_RE = re.compile(r"\bP[0-3]\b|\bMP\d*-P\d+", re.IGNORECASE)
PATH_OR_COMMAND_RE = re.compile(
    r"`[^`]+`|[A-Za-z0-9_./-]+\.(?:py|rs|md)\b|dev/scripts/|dev/active/|rust/src/|devctl\b"
)
GRAPH_CONTEXT_RE = re.compile(
    r"context-graph|startup-context|session-resume|ContextPack|DevSessionPack|system-map|AgentLoopDecision|agent-loop",
    re.IGNORECASE,
)
CARRY_FORWARD_RE = re.compile(
    r"ContextPack|DevSessionPack|PacketContinuityState|packet_carry_forward|carry-forward|startup-context|session-resume|plan_index|plan row",
    re.IGNORECASE,
)


def build_runtime_spine_report(
    *,
    system_map_text: str,
    owner_texts: Mapping[str, str],
    registered_check_ids: Sequence[str],
) -> dict[str, object]:
    """Return closure status for SYSTEM_MAP.md section 0.6."""
    return build_runtime_spine_closure_state(
        system_map_text=system_map_text,
        owner_texts=owner_texts,
        registered_check_ids=registered_check_ids,
    ).to_dict()


def build_runtime_spine_closure_state(
    *,
    system_map_text: str,
    owner_texts: Mapping[str, str],
    registered_check_ids: Sequence[str],
) -> RuntimeSpineClosureState:
    """Return typed closure state for SYSTEM_MAP.md section 0.6."""
    section = runtime_spine_section(system_map_text)
    closure_rule_present = CLOSURE_RULE_TOKEN in section if section else False
    items = tuple(runtime_spine_items(section)) if section else ()
    risky_items = tuple(item for item in items if item.status in {"missing", "partial"})
    matrix_rows = runtime_spine_closure_matrix(section) if section else ()
    matrix_by_object = {
        normalize_runtime_object(row.runtime_object): row
        for row in matrix_rows
    }
    owned_items = tuple(
        RuntimeSpineItem(
            name=item.name,
            marker=item.marker,
            status=item.status,
            detail=item.detail,
            owner_refs=find_owner_refs(item.name, owner_texts),
        )
        for item in risky_items
    )
    violations = runtime_spine_violations(
        section_present=bool(section),
        closure_rule_present=closure_rule_present,
        owned_items=owned_items,
        matrix_rows=matrix_rows,
        matrix_by_object=matrix_by_object,
        registered_check_ids=registered_check_ids,
    )
    return RuntimeSpineClosureState(
        risky_items=owned_items,
        closure_matrix=matrix_rows,
        violations=tuple(violations),
        closure_rule_present=closure_rule_present,
        registered_guard_present=RUNTIME_SPINE_CHECK_ID in set(registered_check_ids),
        section_present=bool(section),
    )


def runtime_spine_violations(
    *,
    section_present: bool,
    closure_rule_present: bool,
    owned_items: Sequence[RuntimeSpineItem],
    matrix_rows: Sequence[RuntimeSpineClosureRow],
    matrix_by_object: Mapping[str, RuntimeSpineClosureRow],
    registered_check_ids: Sequence[str],
) -> list[dict[str, str]]:
    """Return guard violations for closure-rule drift."""
    violations: list[dict[str, str]] = []
    if not section_present:
        violations.append(
            {
                "check": "runtime_spine_section_present",
                "detail": "SYSTEM_MAP.md is missing section 0.6 runtime-spine authority.",
            }
        )
    if section_present and not closure_rule_present:
        violations.append(
            {
                "check": "runtime_spine_closure_rule_present",
                "detail": "SYSTEM_MAP.md section 0.6 is missing the closure rule.",
            }
        )
    if RUNTIME_SPINE_CHECK_ID not in set(registered_check_ids):
        violations.append(
            {
                "check": "runtime_spine_guard_registered",
                "detail": "check_runtime_spine_closure is not registered in the script catalog.",
            }
        )
    if section_present and not matrix_rows:
        violations.append(
            {
                "check": "runtime_spine_closure_matrix_present",
                "detail": (
                    "SYSTEM_MAP.md section 0.6 must include a Runtime Spine "
                    "Closure Matrix with owner, proof, graph/context, and "
                    "carry-forward fields for every ❌/⚠️ item."
                ),
            }
        )
    for item in owned_items:
        if item.owner_refs:
            pass
        else:
            violations.append(
                {
                    "check": "runtime_spine_item_has_active_owner",
                    "component": item.name,
                    "status": item.status,
                    "detail": (
                        f"{item.name} is marked {item.status} in SYSTEM_MAP.md section 0.6 "
                        "but has no active plan or typed plan-store owner reference."
                    ),
                }
            )
        row = matrix_by_object.get(normalize_runtime_object(item.name))
        if row is None:
            violations.append(
                {
                    "check": "runtime_spine_item_has_closure_matrix_row",
                    "component": item.name,
                    "status": item.status,
                    "detail": f"{item.name} is missing from the Runtime Spine Closure Matrix.",
                }
            )
            continue
        violations.extend(_row_violations(item, row))
    return violations


def runtime_spine_section(system_map_text: str) -> str:
    """Return the SYSTEM_MAP section 0.6 body."""
    match = SECTION_RE.search(system_map_text)
    if match is None:
        return ""
    start = match.start()
    next_match = NEXT_SECTION_RE.search(system_map_text, match.end())
    end = next_match.start() if next_match is not None else len(system_map_text)
    return system_map_text[start:end]


def runtime_spine_items(section_text: str) -> tuple[RuntimeSpineItem, ...]:
    """Parse runtime-spine objects from the fenced section tree."""
    block = _first_fenced_block(section_text)
    items: list[RuntimeSpineItem] = []
    for line in block.splitlines():
        marker = _line_marker(line)
        if not marker:
            continue
        name = _line_name(line, marker)
        if not name:
            continue
        items.append(
            RuntimeSpineItem(
                name=name,
                marker=marker,
                status=RISK_MARKER_LABELS.get(marker, "implemented"),
                detail=line.strip(),
            )
        )
    return tuple(items)


def runtime_spine_closure_matrix(section_text: str) -> tuple[RuntimeSpineClosureRow, ...]:
    """Parse the runtime-spine closure matrix table from section 0.6."""
    lines = section_text.splitlines()
    heading_index = _line_index(lines, MATRIX_HEADING)
    if heading_index is None:
        return ()
    table_lines = _table_lines_after_heading(lines, heading_index)
    if len(table_lines) < 2:
        return ()
    headers = [_normalize_header(cell) for cell in _split_table_row(table_lines[0])]
    if tuple(headers) != REQUIRED_MATRIX_COLUMNS:
        return ()
    rows: list[RuntimeSpineClosureRow] = []
    for line in table_lines[2:]:
        cells = _split_table_row(line)
        if len(cells) != len(headers):
            continue
        values = dict(zip(headers, cells, strict=True))
        rows.append(
            RuntimeSpineClosureRow(
                runtime_object=values["runtime object"],
                active_owner=values["active owner"],
                typed_contract=values["typed contract"],
                producer=values["producer"],
                consumer=values["consumer"],
                regression_proof=values["regression proof"],
                graph_context_visibility=values["graph/context visibility"],
                carry_forward_compaction_path=values["carry-forward/compaction path"],
                priority=values["priority"],
            )
        )
    return tuple(rows)


def normalize_runtime_object(value: str) -> str:
    """Normalize runtime-spine object labels for table matching."""
    return re.sub(r"[^A-Za-z0-9]+", "", value).lower()


def find_owner_refs(component: str, owner_texts: Mapping[str, str]) -> tuple[str, ...]:
    """Return active owner references mentioning a runtime-spine component."""
    refs: list[str] = []
    for label, text in owner_texts.items():
        for line_number, line in enumerate(text.splitlines(), start=1):
            if component not in line:
                continue
            refs.append(f"{label}:{line_number}")
            break
    return tuple(refs)


def load_owner_texts(
    repo_root: Path,
    *,
    owner_paths: Sequence[Path] | None = None,
) -> dict[str, str]:
    """Load active plan surfaces used as durable closure owners."""
    paths = tuple(
        owner_paths
        or (
            Path("dev/active/ai_governance_platform.md"),
            Path("dev/active/MASTER_PLAN.md"),
            Path("dev/state/plan_index.jsonl"),
        )
    )
    texts: dict[str, str] = {}
    for path in paths:
        candidate = repo_root / path
        try:
            texts[path.as_posix()] = candidate.read_text(encoding="utf-8")
        except OSError:
            texts[path.as_posix()] = ""
    return texts


def _first_fenced_block(section_text: str) -> str:
    parts = section_text.split("```")
    if len(parts) < 3:
        return ""
    return parts[1]


def _line_marker(line: str) -> str:
    for marker in RISK_MARKER_LABELS:
        if marker in line:
            return marker
    if "\u2705" in line:
        return "\u2705"
    return ""


def _line_name(line: str, marker: str) -> str:
    prefix = line.split(marker, 1)[0]
    prefix = re.sub(r"^[\s\u2514\u251c\u2500]+", "", prefix).strip()
    if not prefix:
        return ""
    return prefix.split()[0]


def _row_violations(
    item: RuntimeSpineItem,
    row: RuntimeSpineClosureRow,
) -> list[dict[str, str]]:
    checks = (
        ("active owner", row.active_owner, OWNER_RE, "an MP active owner id"),
        ("typed contract", row.typed_contract, PATH_OR_COMMAND_RE, "a typed contract path or command"),
        ("producer", row.producer, PATH_OR_COMMAND_RE, "a producer path or command"),
        ("consumer", row.consumer, PATH_OR_COMMAND_RE, "a consumer path or command"),
        ("regression proof", row.regression_proof, PROOF_RE, "a check_, probe_, or test_ proof"),
        (
            "graph/context visibility",
            row.graph_context_visibility,
            GRAPH_CONTEXT_RE,
            "context-graph/startup-context/session-resume/system-map visibility",
        ),
        (
            "carry-forward/compaction path",
            row.carry_forward_compaction_path,
            CARRY_FORWARD_RE,
            "ContextPack/DevSessionPack/PacketContinuityState/carry-forward continuity",
        ),
        ("priority", row.priority, PRIORITY_RE, "a P0-P3 or MP priority"),
    )
    violations: list[dict[str, str]] = []
    for field_name, value, pattern, requirement in checks:
        if PLACEHOLDER_RE.fullmatch(value) or pattern.search(value) is None:
            violations.append(
                {
                    "check": "runtime_spine_closure_matrix_field_connected",
                    "component": item.name,
                    "status": item.status,
                    "field": field_name,
                    "detail": (
                        f"{item.name} closure matrix field '{field_name}' must name "
                        f"{requirement}; got {value!r}."
                    ),
                }
            )
    return violations


def _line_index(lines: Sequence[str], token: str) -> int | None:
    for index, line in enumerate(lines):
        if line.strip() == token:
            return index
    return None


def _table_lines_after_heading(lines: Sequence[str], heading_index: int) -> list[str]:
    table_lines: list[str] = []
    for line in lines[heading_index + 1 :]:
        if not line.strip():
            if table_lines:
                break
            continue
        if not line.lstrip().startswith("|"):
            if table_lines:
                break
            continue
        table_lines.append(line)
    return table_lines


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [_clean_cell(cell) for cell in stripped.split("|")]


def _normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _clean_cell(value: str) -> str:
    return value.replace("<br>", "; ").strip()
