"""Mutation outcome parsing and result rendering.

Reuses shared helpers rather than reimplementing score calculation or
timestamp formatting:
- ``devctl.common.find_latest_outcomes_file`` for outcome discovery
- ``checks.check_mutation_score`` for timestamp/age helpers
- ``checks.mutation_outcome_parse`` for summary-bucket constants
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

# Wire repo root onto sys.path so ``dev.scripts.*`` imports resolve when
# this module is loaded as a sibling script from ``dev/scripts/``.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dev.scripts.devctl.common import find_latest_outcomes_file  # noqa: E402
from dev.scripts.devctl.time_utils import utc_timestamp  # noqa: E402
from dev.scripts.checks.check_mutation_score import (  # noqa: E402
    isoformat_utc,
    age_hours_from_timestamp,
)
from dev.scripts.checks.mutation_outcome_parse import (  # noqa: E402
    CAUGHT_SUMMARIES,
    SURVIVOR_SUMMARIES,
    TIMEOUT_SUMMARIES,
    UNVIABLE_SUMMARIES,
)


def scenario_fields(outcome: dict[str, Any]) -> dict[str, Any]:
    """Normalize outcome scenario fields across cargo-mutants schema versions.

    Extracts file, line, function, and mutation description from either the
    newer nested ``scenario.Mutant`` layout or the legacy flat ``scenario`` keys.
    """
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

    mutation_name = (
        mutant.get("name")
        or mutant.get("replacement")
        or mutant.get("genre")
        or "unknown"
    )
    return {
        "file": mutant.get("file", "unknown"),
        "line": line,
        "function": function_name,
        "mutation": mutation_name,
    }


def _fields_from_legacy_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    function_value = scenario.get("function", "unknown")
    if isinstance(function_value, dict):
        function_name = function_value.get("function_name", "unknown")
    else:
        function_name = function_value

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

    with open(outcomes_file, encoding="utf-8") as f:
        data = json.load(f)

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


# ---------------------------------------------------------------------------
# Output rendering
# ---------------------------------------------------------------------------

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

    print(f"""
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
""")

    if survived:
        print("## Survived Mutants (need better tests)\n")
        print("| File | Line | Function | Mutation |")
        print("|------|------|----------|----------|")
        for m in survived[:20]:
            print(f"| {m['file']} | {m['line']} | {m['function']} | {m['mutation'][:50]} |")
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

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# Mutation Testing Results\n\n")
        f.write(f"Generated: {results['timestamp']}\n\n")
        f.write(f"## Score: {score:.1f}%\n\n")
        f.write(f"- Killed: {stats['killed']}\n")
        f.write(f"- Survived: {stats['survived']}\n")
        f.write(f"- Total: {stats['total']}\n")
        f.write(f"- Results dir: {results['results_dir']}\n")
        f.write(f"- Outcomes: {results['outcomes_path']}\n\n")
        f.write(f"- Outcomes updated: {results.get('outcomes_updated_at', 'unknown')}\n")
        age = results.get("outcomes_age_hours")
        if age is not None:
            f.write(f"- Outcomes age (hours): {age}\n\n")
        survived_by_file = results["survived_by_file"]
        survived_by_dir = results["survived_by_dir"]
        if survived_by_file:
            f.write("## Top Files by Survived Mutants\n\n")
            for file_path, count in survived_by_file.most_common(top_n):
                f.write(f"- {file_path}: {count}\n")
            f.write("\n## Top Directories by Survived Mutants\n\n")
            for dir_path, count in survived_by_dir.most_common(top_n):
                f.write(f"- {dir_path}: {count}\n")

    print(f"Results saved to: {output_file}")
