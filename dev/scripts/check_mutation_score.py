#!/usr/bin/env python3
"""Check a cargo-mutants outcomes.json against a minimum score."""
import argparse
import glob
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


def counts_from_outcomes(data: Dict) -> Tuple[int, int, int, int]:
    """Fallback counter for older/newer outcomes schema variants."""
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
    """Read one outcomes.json and return normalized counters."""
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


def resolve_paths(path_args: List[str], glob_args: List[str]) -> List[Path]:
    """Resolve explicit paths and glob patterns into a unique ordered list."""
    resolved: List[Path] = []

    for raw_path in path_args:
        resolved.append(Path(raw_path))

    for pattern in glob_args:
        for matched in sorted(glob.glob(pattern, recursive=True)):
            resolved.append(Path(matched))

    if not resolved and not (path_args or glob_args):
        resolved.append(Path("mutants.out/outcomes.json"))
    if not resolved:
        return []

    seen = set()
    unique: List[Path] = []
    for path in resolved:
        normalized = str(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(path)
    return unique


def isoformat_utc(timestamp: float) -> str:
    """Render a POSIX timestamp in stable UTC ISO-8601 format."""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def age_hours_from_timestamp(timestamp: float) -> float:
    """Return age in fractional hours from now for a POSIX timestamp."""
    now = datetime.now(timezone.utc).timestamp()
    return max(0.0, (now - timestamp) / 3600.0)


def format_age_hours(age_hours: float) -> str:
    """Format age-hours into a short human-readable duration."""
    total_minutes = int(round(age_hours * 60))
    days, rem_minutes = divmod(total_minutes, 60 * 24)
    hours, minutes = divmod(rem_minutes, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def main() -> int:
    """Parse outcomes.json, print score, and return non-zero if below threshold."""
    parser = argparse.ArgumentParser(description="Check mutation score threshold.")
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Path to cargo-mutants outcomes.json (repeatable)",
    )
    parser.add_argument(
        "--glob",
        action="append",
        default=[],
        help="Glob pattern for outcomes.json files (repeatable, supports **)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.80,
        help="Minimum acceptable mutation score (0.0-1.0)",
    )
    parser.add_argument(
        "--warn-age-hours",
        type=float,
        default=24.0,
        help="Warn when outcomes are older than this many hours (set <0 to disable)",
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        help="Fail when any outcomes are older than this many hours",
    )
    args = parser.parse_args()

    outcome_paths = resolve_paths(args.path, args.glob)
    if not outcome_paths:
        print("ERROR: no outcomes files matched the provided --path/--glob inputs")
        return 2
    missing = [path for path in outcome_paths if not path.exists()]
    if missing:
        for path in missing:
            print(f"ERROR: outcomes file not found: {path}")
        return 2

    total = {
        "caught": 0,
        "missed": 0,
        "timeout": 0,
        "unviable": 0,
    }
    freshness = []
    per_file = []
    for path in outcome_paths:
        counts = read_counts(path)
        per_file.append((path, counts))
        for key in total:
            total[key] += counts[key]
        stat = path.stat()
        age_hours = age_hours_from_timestamp(stat.st_mtime)
        freshness.append(
            {
                "path": path,
                "updated_at": isoformat_utc(stat.st_mtime),
                "age_hours": age_hours,
                "age_label": format_age_hours(age_hours),
            }
        )

    caught = total["caught"]
    missed = total["missed"]
    timeout = total["timeout"]
    unviable = total["unviable"]

    denom = caught + missed + timeout
    score = 1.0 if denom == 0 else caught / denom

    if len(per_file) > 1:
        print(f"Aggregating mutation outcomes from {len(per_file)} files:")
        for path, counts in per_file:
            file_denom = counts["caught"] + counts["missed"] + counts["timeout"]
            file_score = 1.0 if file_denom == 0 else counts["caught"] / file_denom
            print(
                "  - {path}: {score:.2%} (caught {caught}, missed {missed}, timeout {timeout}, unviable {unviable})".format(
                    path=path,
                    score=file_score,
                    caught=counts["caught"],
                    missed=counts["missed"],
                    timeout=counts["timeout"],
                    unviable=counts["unviable"],
                )
            )
        print("Outcome file freshness:")
        for item in freshness:
            print(
                f"  - {item['path']}: updated {item['updated_at']} ({item['age_label']} old)"
            )
    elif freshness:
        item = freshness[0]
        print(
            f"Outcome file: {item['path']} (updated {item['updated_at']}, {item['age_label']} old)"
        )

    print(
        "Mutation score: {score:.2%} (caught {caught}, missed {missed}, timeout {timeout}, unviable {unviable})".format(
            score=score,
            caught=caught,
            missed=missed,
            timeout=timeout,
            unviable=unviable,
        )
    )

    if score < args.threshold:
        print(
            "FAIL: mutation score {score:.2%} is below threshold {threshold:.2%}".format(
                score=score, threshold=args.threshold
            )
        )
        return 1

    if args.warn_age_hours is not None and args.warn_age_hours >= 0:
        stale_warn = [item for item in freshness if item["age_hours"] > args.warn_age_hours]
        if stale_warn:
            print(
                "WARN: mutation outcomes are older than warn threshold "
                f"({args.warn_age_hours:.1f}h):"
            )
            for item in stale_warn:
                print(f"  - {item['path']} ({item['age_label']} old)")

    if args.max_age_hours is not None:
        stale_fail = [item for item in freshness if item["age_hours"] > args.max_age_hours]
        if stale_fail:
            print(
                "FAIL: mutation outcomes exceed max age threshold "
                f"({args.max_age_hours:.1f}h). Re-run mutants to refresh data."
            )
            for item in stale_fail:
                print(f"  - {item['path']} ({item['age_label']} old)")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
