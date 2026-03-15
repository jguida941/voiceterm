"""Source-row loading helpers for data-science snapshots."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..common import read_json_object
from ..jsonl_support import parse_json_line_dict
from ..numeric import to_float, to_int


@dataclass(frozen=True)
class AgentSummaryRow:
    """Typed row used before agent metrics are reduced into reports."""

    source: str
    selected_agents: int
    tasks_completed_total: int
    elapsed_seconds: float | None
    ok: bool
    path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def read_jsonl_dict_tail(path: Path, *, max_rows: int) -> list[dict[str, Any]]:
    """Read the most recent JSON object rows from a JSONL file."""
    rows: deque[dict[str, Any]] = deque(maxlen=max(1, max_rows))
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = parse_json_line_dict(line)
                if payload is not None:
                    rows.append(payload)
    except OSError:
        return []
    return list(rows)


def collect_swarm_summary_rows(root: Path, *, max_files: int) -> list[dict[str, Any]]:
    """Collect normalized agent rows from saved swarm summary artifacts."""
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    paths = sorted(root.glob("*/summary.json"), reverse=True)[: max(1, max_files)]
    for path in paths:
        payload = _read_summary_json(path)
        if payload is None:
            continue
        summary = payload.get("summary")
        if not isinstance(summary, dict):
            continue
        selected_agents = to_int(summary.get("selected_agents"), default=0)
        if selected_agents <= 0:
            continue
        task_total = _agent_task_total(payload.get("agents"))
        rows.append(
            AgentSummaryRow(
                source="swarm",
                selected_agents=selected_agents,
                tasks_completed_total=task_total,
                elapsed_seconds=None,
                ok=bool(payload.get("ok")),
                path=str(path),
            ).to_dict()
        )
    return rows


def collect_benchmark_summary_rows(
    root: Path,
    *,
    max_files: int,
) -> list[dict[str, Any]]:
    """Collect normalized agent rows from saved benchmark summary artifacts."""
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    paths = sorted(root.glob("*/summary.json"), reverse=True)[: max(1, max_files)]
    for path in paths:
        payload = _read_summary_json(path)
        if payload is None:
            continue
        scenarios = payload.get("scenarios")
        if not isinstance(scenarios, list):
            continue
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                continue
            swarms = scenario.get("swarms")
            if not isinstance(swarms, list):
                continue
            for swarm in swarms:
                if not isinstance(swarm, dict):
                    continue
                selected_agents = to_int(swarm.get("selected_agents"), default=0)
                if selected_agents <= 0:
                    continue
                rows.append(
                    AgentSummaryRow(
                        source="benchmark",
                        selected_agents=selected_agents,
                        tasks_completed_total=to_int(swarm.get("tasks_completed_total"), default=0),
                        elapsed_seconds=to_float(swarm.get("elapsed_seconds"), default=0.0),
                        ok=bool(swarm.get("ok")),
                        path=str(path),
                    ).to_dict()
                )
    return rows


def _read_summary_json(path: Path) -> dict[str, Any] | None:
    payload, _error = read_json_object(path)
    return payload


def _agent_task_total(agent_rows: object) -> int:
    if not isinstance(agent_rows, list):
        return 0
    task_total = 0
    for item in agent_rows:
        if isinstance(item, dict):
            task_total += to_int(item.get("tasks_completed"), default=0)
    return task_total
