"""Phased execution-plan helpers for check-router."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RouterBatch:
    rows: list[dict[str, str]]
    parallel_enabled: bool


def router_batches(planned_rows: list[dict[str, str]]) -> list[RouterBatch]:
    batches: list[RouterBatch] = []
    pending: list[dict[str, str]] = []
    pending_parallel: bool | None = None
    for row in planned_rows:
        row_parallel = row.get("parallel_safety") != "serial_required"
        if pending and row_parallel != pending_parallel:
            batches.append(
                RouterBatch(
                    rows=pending,
                    parallel_enabled=bool(pending_parallel),
                )
            )
            pending = []
        pending.append(row)
        pending_parallel = row_parallel
    if pending:
        batches.append(
            RouterBatch(rows=pending, parallel_enabled=bool(pending_parallel))
        )
    return batches


def router_execution_summary(planned_rows: list[dict[str, str]]) -> dict[str, object]:
    serial_count = sum(
        1 for row in planned_rows if row.get("parallel_safety") == "serial_required"
    )
    parallel_count = max(0, len(planned_rows) - serial_count)
    return {
        "serial_required_command_count": serial_count,
        "parallel_safe_command_count": parallel_count,
        "phase_count": len(router_batches(planned_rows)),
    }


__all__ = ["RouterBatch", "router_batches", "router_execution_summary"]
