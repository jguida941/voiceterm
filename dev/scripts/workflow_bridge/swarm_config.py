"""Autonomy swarm-run workflow configuration helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

from .common import append_output, validate_decimal_hours


def resolve_swarm_config_from_env(env: Mapping[str, str]) -> dict[str, str]:
    """Resolve swarm-run dispatch inputs with safe defaults."""
    run_label = env.get("INPUT_RUN_LABEL", "")
    if not run_label:
        run_id = env.get("GITHUB_RUN_ID", "")
        run_attempt = env.get("GITHUB_RUN_ATTEMPT", "")
        run_label = f"gh-swarm-run-{run_id}-{run_attempt}"
    branch_base = env.get("INPUT_BRANCH_BASE", "") or "develop"
    agents = env.get("INPUT_AGENTS", "") or "10"
    parallel_workers = env.get("INPUT_PARALLEL_WORKERS", "") or "4"
    max_rounds = env.get("INPUT_MAX_ROUNDS", "") or "1"
    max_hours = env.get("INPUT_MAX_HOURS", "") or "1"
    max_tasks = env.get("INPUT_MAX_TASKS", "") or "1"
    stale_minutes = env.get("INPUT_STALE_MINUTES", "") or "120"

    for value in [agents, parallel_workers, max_rounds, max_tasks, stale_minutes]:
        if not re.fullmatch(r"[0-9]+", value or ""):
            raise ValueError(f"invalid numeric input: {value}")

    return {
        "run_label": run_label,
        "branch_base": branch_base,
        "agents": agents,
        "parallel_workers": parallel_workers,
        "max_rounds": max_rounds,
        "max_hours": validate_decimal_hours(
            max_hours,
            message=f"invalid max_hours: {max_hours}",
        ),
        "max_tasks": max_tasks,
        "stale_minutes": stale_minutes,
    }


def write_swarm_config_outputs(config: Mapping[str, str], output_path: Path) -> None:
    """Write swarm-run settings to GitHub output format."""
    append_output(
        output_path,
        [
            ("run_label", config["run_label"]),
            ("branch_base", config["branch_base"]),
            ("agents", config["agents"]),
            ("parallel_workers", config["parallel_workers"]),
            ("max_rounds", config["max_rounds"]),
            ("max_hours", config["max_hours"]),
            ("max_tasks", config["max_tasks"]),
            ("stale_minutes", config["stale_minutes"]),
        ],
    )
