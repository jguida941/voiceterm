#!/usr/bin/env python3
"""Render a Shields endpoint JSON badge from cargo-mutants outcomes."""

import argparse
import glob
import json
from pathlib import Path
from typing import Dict, List, Tuple


def counts_from_outcomes(data: Dict) -> Tuple[int, int, int, int]:
    """Fallback counter for outcomes schema variants."""
    caught = 0
    missed = 0
    timeout = 0
    unviable = 0

    for outcome in data.get("outcomes", []):
        summary = outcome.get("summary")
        if summary in {"CaughtMutant", "Killed"}:
            caught += 1
        elif summary in {"MissedMutant", "Survived"}:
            missed += 1
        elif summary == "Timeout":
            timeout += 1
        elif summary == "Unviable":
            unviable += 1

    return caught, missed, timeout, unviable


def read_counts(path: Path) -> Dict[str, int]:
    """Read one outcomes file and return normalized counters."""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    caught = int(data.get("caught", 0))
    missed = int(data.get("missed", 0))
    timeout = int(data.get("timeout", 0))
    unviable = int(data.get("unviable", 0))

    if (caught + missed + timeout + unviable) == 0 and data.get("outcomes"):
        caught, missed, timeout, unviable = counts_from_outcomes(data)

    return {
        "caught": caught,
        "missed": missed,
        "timeout": timeout,
        "unviable": unviable,
    }


def resolve_paths(patterns: List[str]) -> List[Path]:
    """Resolve glob patterns into a unique ordered list of paths."""
    resolved: List[Path] = []
    for pattern in patterns:
        for matched in sorted(glob.glob(pattern, recursive=True)):
            resolved.append(Path(matched))

    seen = set()
    unique: List[Path] = []
    for path in resolved:
        normalized = str(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(path)
    return unique


def color_for_score(score: float) -> str:
    """Map mutation score to badge color."""
    if score >= 0.90:
        return "brightgreen"
    if score >= 0.80:
        return "orange"
    return "red"


def write_badge(path: Path, label: str, message: str, color: str) -> None:
    """Write shields endpoint JSON payload."""
    payload = {
        "schemaVersion": 1,
        "label": label,
        "message": message,
        "color": color,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render mutation score badge JSON.")
    parser.add_argument(
        "--glob",
        action="append",
        default=["mutation-shards/**/shard-*-outcomes.json"],
        help="Glob pattern for outcomes files (repeatable)",
    )
    parser.add_argument(
        "--output",
        default=".github/badges/mutation-score.json",
        help="Output path for shields endpoint JSON",
    )
    parser.add_argument(
        "--label",
        default="Mutation",
        help="Badge label",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    outcome_paths = resolve_paths(args.glob)
    if not outcome_paths:
        write_badge(output_path, args.label, "failed", "red")
        print("No mutation outcomes found; wrote failed badge.")
        return 0

    total = {"caught": 0, "missed": 0, "timeout": 0, "unviable": 0}
    try:
        for path in outcome_paths:
            counts = read_counts(path)
            for key in total:
                total[key] += counts[key]
    except Exception as exc:  # noqa: BLE001
        write_badge(output_path, args.label, "failed", "red")
        print(f"Failed to parse mutation outcomes ({exc}); wrote failed badge.")
        return 0

    denom = total["caught"] + total["missed"] + total["timeout"]
    score = 1.0 if denom == 0 else total["caught"] / denom
    message = f"{score * 100:.2f}%"
    color = color_for_score(score)
    write_badge(output_path, args.label, message, color)
    print(
        "Mutation badge: {message} ({color}) from {count} outcomes files.".format(
            message=message,
            color=color,
            count=len(outcome_paths),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
