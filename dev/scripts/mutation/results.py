"""Mutation outcome parsing and result rendering."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dev.scripts.checks.check_mutation_score import age_hours_from_timestamp, isoformat_utc
from dev.scripts.checks.mutation_outcome_parse import (
    CAUGHT_SUMMARIES,
    SURVIVOR_SUMMARIES,
    TIMEOUT_SUMMARIES,
    UNVIABLE_SUMMARIES,
)
from dev.scripts.devctl.common import find_latest_outcomes_file
from dev.scripts.devctl.time_utils import utc_timestamp


def scenario_fields(outcome: dict[str, Any]) -> dict[str, Any]:
    """Normalize outcome scenario fields across cargo-mutants schema versions."""
    scenario = outcome.get("scenario")
    if not isinstance(scenario, dict):
        return {"file": "unknown", "line": 0, "function": "unknown", "mutation": "unknown"}

    mutant = scenario.get("Mutant")
    if isinstance(mutant, dict):
        return _fields_from_mutant(mutant)

    return _fields_from_legacy_scenario(scenario)


def _fields_from_mutant(mutant: dict[str, Any]) -> dict[str, Any]:
    function = mutant.get("function")
    if isinstance(function, dict):
        function_name = function.get("function_name", "unknown")
    elif isinstance(function, str):
        function_name = function
    else:
        function_name = "unknown"

    line = 0
    span = mutant.get("span")
    if isinstance(span, dict):
        start = span.get("start")
        if isinstance(start, dict):
            line = int(start.get("line", 0) or 0)

    mutation_name = mutant.get("name") or mutant.get("replacement") or mutant.get("genre") or "unknown"
    return {
        "file": mutant.get("file", "unknown"),
        "line": line,
        "function": function_name,
        "mutation": mutation_name,
    }


def _fields_from_legacy_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    function_value = scenario.get("function", "unknown")
    function_name = function_value.get("function_name", "unknown") if isinstance(function_value, dict) else function_value
    return {
        "file": scenario.get("file", "unknown"),
        "line": int(scenario.get("line", 0) or 0),
        "function": function_name,
        "mutation": scenario.get("mutation", "unknown"),
    }


def parse_results() -> Optional[dict[str, Any]]:
    """Parse the most recent mutation testing outcomes."""
    outcomes_file = find_latest_outcomes_file()
    if outcomes_file is None:
        print("No mutation results found.")
        return None

    with open(outcomes_file, encoding="utf-8") as handle:
        data = json.load(handle)

    outcomes = data.get("outcomes", [])
    stats = {
        "killed": int(data.get("caught", 0)),
        "survived": int(data.get("missed", 0)),
        "timeout": int(data.get("timeout", 0)),
        "unviable": int(data.get("unviable", 0)),
        "total": int(data.get("total_mutants", len(outcomes))),
    }
    fallback = {"killed": 0, "survived": 0, "timeout": 0, "unviable": 0}

    survived_mutants: list[dict[str, Any]] = []
    survived_by_file: Counter[str] = Counter()
    survived_by_dir: Counter[str] = Counter()

    for outcome in outcomes:
        status = outcome.get("summary", "unknown")
        if status in CAUGHT_SUMMARIES:
            fallback["killed"] += 1
        elif status in SURVIVOR_SUMMARIES:
            fallback["survived"] += 1
            fields = scenario_fields(outcome)
            survived_mutants.append(fields)
            survived_by_file[fields["file"]] += 1
            survived_by_dir[str(Path(fields["file"]).parent)] += 1
        elif status in TIMEOUT_SUMMARIES:
            fallback["timeout"] += 1
        elif status in UNVIABLE_SUMMARIES:
            fallback["unviable"] += 1

    if stats["total"] == 0:
        stats["total"] = len(outcomes)
    if (stats["killed"] + stats["survived"] + stats["timeout"] + stats["unviable"]) == 0:
        stats.update(fallback)

    testable = stats["killed"] + stats["survived"] + stats["timeout"]
    score = (stats["killed"] / testable * 100) if testable > 0 else 0
    outcomes_stat = outcomes_file.stat()

    return {
        "stats": stats,
        "score": score,
        "survived": survived_mutants,
        "survived_by_file": survived_by_file,
        "survived_by_dir": survived_by_dir,
        "outcomes_path": str(outcomes_file),
        "results_dir": str(outcomes_file.parent),
        "outcomes_updated_at": isoformat_utc(outcomes_stat.st_mtime),
        "outcomes_age_hours": round(age_hours_from_timestamp(outcomes_stat.st_mtime), 2),
        "timestamp": utc_timestamp(),
    }


def output_results(results: Optional[dict[str, Any]], fmt: str = "markdown", top_n: int = 5) -> None:
    """Render parsed results to stdout and save a summary file."""
    if results is None:
        return
    if fmt == "json":
        _render_json(results)
        return

    _render_markdown(results, top_n)
    _save_summary(results, top_n)


def _render_json(results: dict[str, Any]) -> None:
    out = results.copy()
    out["survived_by_file"] = results["survived_by_file"].most_common()
    out["survived_by_dir"] = results["survived_by_dir"].most_common()
    print(json.dumps(out, indent=2))


def _render_markdown(results: dict[str, Any], top_n: int) -> None:
    stats = results["stats"]
    score = results["score"]
    survived = results["survived"]

    print("\n" + "=" * 60)
    print("MUTATION TESTING RESULTS")
    print("=" * 60)

    print(
        f"""
## Summary

| Metric | Value |
|--------|-------|
| Score | **{score:.1f}%** |
| Killed | {stats['killed']} |
| Survived | {stats['survived']} |
| Timeout | {stats['timeout']} |
| Unviable | {stats['unviable']} |
| Total | {stats['total']} |

Threshold: 80%
Status: {"PASS" if score >= 80 else "FAIL"}

Results dir: {results['results_dir']}
Outcomes: {results['outcomes_path']}
Outcomes updated: {results.get('outcomes_updated_at', 'unknown')}
Outcomes age (hours): {results.get('outcomes_age_hours', 'unknown')}
"""
    )

    if survived:
        print("## Survived Mutants (need better tests)\n")
        print("| File | Line | Function | Mutation |")
        print("|------|------|----------|----------|")
        for mutant in survived[:20]:
            print(f"| {mutant['file']} | {mutant['line']} | {mutant['function']} | {mutant['mutation'][:50]} |")
        if len(survived) > 20:
            print(f"\n... and {len(survived) - 20} more")

        print("\n## Top Files by Survived Mutants\n")
        print("| File | Survived |")
        print("|------|----------|")
        for file_path, count in results["survived_by_file"].most_common(top_n):
            print(f"| {file_path} | {count} |")

        print("\n## Top Directories by Survived Mutants\n")
        print("| Directory | Survived |")
        print("|-----------|----------|")
        for dir_path, count in results["survived_by_dir"].most_common(top_n):
            print(f"| {dir_path} | {count} |")

    print()


def _save_summary(results: dict[str, Any], top_n: int) -> None:
    output_file = Path(results["results_dir"]) / "summary.md"
    stats = results["stats"]
    score = results["score"]

    with open(output_file, "w", encoding="utf-8") as handle:
        handle.write("# Mutation Testing Results\n\n")
        handle.write(f"Generated: {results['timestamp']}\n\n")
        handle.write(f"## Score: {score:.1f}%\n\n")
        handle.write(f"- Killed: {stats['killed']}\n")
        handle.write(f"- Survived: {stats['survived']}\n")
        handle.write(f"- Total: {stats['total']}\n")
        handle.write(f"- Results dir: {results['results_dir']}\n")
        handle.write(f"- Outcomes: {results['outcomes_path']}\n\n")
        handle.write(f"- Outcomes updated: {results.get('outcomes_updated_at', 'unknown')}\n")
        age = results.get("outcomes_age_hours")
        if age is not None:
            handle.write(f"- Outcomes age (hours): {age}\n\n")
        if results["survived"]:
            handle.write(f"## Top {top_n} Files\n\n")
            for file_path, count in results["survived_by_file"].most_common(top_n):
                handle.write(f"- {file_path}: {count}\n")

    print(f"Summary saved to: {output_file}")
