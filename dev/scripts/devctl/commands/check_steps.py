"""Shared helpers for building and running `devctl check` step specs."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from ..common import run_cmd


def build_step_spec(
    name: str,
    cmd: List[str],
    default_env: dict,
    cwd=None,
    step_env=None,
) -> dict:
    """Return one executable check-step spec."""
    return {
        "name": name,
        "cmd": cmd,
        "cwd": cwd,
        "env": step_env or default_env,
    }


def run_step_specs_serial(step_specs: List[dict], dry_run: bool) -> List[dict]:
    """Run a list of step specs sequentially."""
    results: List[dict] = []
    for spec in step_specs:
        results.append(
            run_cmd(
                spec["name"],
                spec["cmd"],
                cwd=spec.get("cwd"),
                env=spec.get("env"),
                dry_run=dry_run,
            )
        )
    return results


def run_step_specs_parallel(step_specs: List[dict], dry_run: bool, max_workers: int) -> List[dict]:
    """Run independent step specs in parallel while preserving report order."""
    if not step_specs:
        return []
    if dry_run or max_workers <= 1 or len(step_specs) <= 1:
        return run_step_specs_serial(step_specs, dry_run=dry_run)

    worker_count = min(max_workers, len(step_specs))
    indexed_results: List[dict | None] = [None] * len(step_specs)
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = {
            pool.submit(
                run_cmd,
                spec["name"],
                spec["cmd"],
                cwd=spec.get("cwd"),
                env=spec.get("env"),
                dry_run=dry_run,
            ): index
            for index, spec in enumerate(step_specs)
        }
        for future in as_completed(futures):
            index = futures[future]
            indexed_results[index] = future.result()

    ordered_results: List[dict] = []
    for result in indexed_results:
        if result is None:
            raise RuntimeError("parallel step execution returned an incomplete result set")
        ordered_results.append(result)
    return ordered_results


def run_step_specs(
    step_specs: List[dict],
    *,
    dry_run: bool,
    parallel_enabled: bool,
    max_workers: int,
) -> List[dict]:
    """Run specs using serial or parallel mode based on command settings."""
    if parallel_enabled:
        return run_step_specs_parallel(step_specs, dry_run=dry_run, max_workers=max_workers)
    return run_step_specs_serial(step_specs, dry_run=dry_run)
