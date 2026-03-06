#!/usr/bin/env python3
"""Workflow helper to detect GitHub dependency-graph availability."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Callable


RunResult = subprocess.CompletedProcess[str]
Runner = Callable[..., RunResult]


def probe_dependency_graph_status(
    repository: str,
    *,
    runner: Runner = subprocess.run,
) -> tuple[bool, list[str]]:
    result = runner(
        ["gh", "api", f"repos/{repository}"],
        check=False,
        capture_output=True,
        text=True,
    )
    stderr_lines = [line for line in (result.stderr or "").splitlines() if line.strip()]
    if result.returncode != 0:
        return False, stderr_lines

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return False, stderr_lines

    if not isinstance(payload, dict):
        return False, stderr_lines
    security_and_analysis = payload.get("security_and_analysis", {})
    if not isinstance(security_and_analysis, dict):
        return False, stderr_lines
    dependency_graph = security_and_analysis.get("dependency_graph", {})
    if not isinstance(dependency_graph, dict):
        return False, stderr_lines
    status = dependency_graph.get("status", "")
    return str(status).strip() == "enabled", stderr_lines


def append_enabled_output(output_path: Path, enabled: bool) -> None:
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(f"enabled={'true' if enabled else 'false'}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="Repository slug (owner/repo)")
    parser.add_argument("--github-output", required=True, help="GITHUB_OUTPUT path")
    args = parser.parse_args()

    enabled, stderr_lines = probe_dependency_graph_status(args.repo)
    append_enabled_output(Path(args.github_output), enabled)
    if not enabled:
        print("::warning::Dependency graph is not enabled; skipping dependency review gate.")
        for line in stderr_lines[:5]:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
