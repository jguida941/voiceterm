"""Typed task-router authority shared by docs, bootstrap surfaces, and checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

TASK_ROUTER_AUTHORITY_PATH = "dev/scripts/devctl/governance/task_router_contract.py"


@dataclass(frozen=True, slots=True)
class TaskRouterRow:
    """One human-facing task-router row backed by the typed lane router."""

    user_story: str
    task_class: str
    lane: str


TASK_ROUTER_ROWS: tuple[TaskRouterRow, ...] = (
    TaskRouterRow(
        user_story="Changed runtime behavior under `rust/src/**`",
        task_class="Runtime feature/fix",
        lane="runtime",
    ),
    TaskRouterRow(
        user_story="Changed HUD/layout/controls/flags/UI text",
        task_class="HUD/overlay/controls/flags",
        lane="runtime",
    ),
    TaskRouterRow(
        user_story="Touched perf/latency/wake/threading/unsafe/parser boundaries",
        task_class="Risk-sensitive runtime",
        lane="runtime",
    ),
    TaskRouterRow(
        user_story="Changed only user-facing docs",
        task_class="Docs-only",
        lane="docs",
    ),
    TaskRouterRow(
        user_story="Changed tooling/process/CI/governance surfaces",
        task_class="Tooling/process/CI",
        lane="tooling",
    ),
    TaskRouterRow(
        user_story="Preparing/publishing release",
        task_class="Release/tag/distribution",
        lane="release",
    ),
)

_TASK_ROUTER_TABLE_HEADER = (
    "| User story | Task class | Required bundle |",
    "|---|---|---|",
)


def _resolve_bundle_name(
    lane: str,
    bundle_by_lane: Mapping[str, str],
) -> str:
    return bundle_by_lane[lane]


def task_router_markdown_rows(
    *,
    bundle_by_lane: Mapping[str, str],
) -> tuple[str, ...]:
    """Render task-router body rows from the typed router definitions."""
    return tuple(
        "| {user_story} | {task_class} | `{bundle}` |".format(
            user_story=row.user_story,
            task_class=row.task_class,
            bundle=_resolve_bundle_name(row.lane, bundle_by_lane),
        )
        for row in TASK_ROUTER_ROWS
    )


def render_task_router_table_markdown(
    *,
    bundle_by_lane: Mapping[str, str],
) -> str:
    """Render the full task-router markdown table."""
    return "\n".join(
        (
            *_TASK_ROUTER_TABLE_HEADER,
            *task_router_markdown_rows(bundle_by_lane=bundle_by_lane),
        )
    )
