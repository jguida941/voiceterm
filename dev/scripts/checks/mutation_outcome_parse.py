"""Mutation outcomes aggregation helpers for remediation loops."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SURVIVOR_SUMMARIES = {"MissedMutant", "Survived"}
CAUGHT_SUMMARIES = {"CaughtMutant", "Killed"}
TIMEOUT_SUMMARIES = {"Timeout"}
UNVIABLE_SUMMARIES = {"Unviable"}


def _summary_bucket(summary: str) -> str:
    if summary in CAUGHT_SUMMARIES:
        return "caught"
    if summary in SURVIVOR_SUMMARIES:
        return "missed"
    if summary in TIMEOUT_SUMMARIES:
        return "timeout"
    if summary in UNVIABLE_SUMMARIES:
        return "unviable"
    return "other"


def _extract_hotspot_key(outcome: dict[str, Any]) -> str:
    candidates: list[Any] = [
        outcome.get("source_path"),
        outcome.get("package_path"),
        outcome.get("package"),
        outcome.get("path"),
    ]
    mutant = outcome.get("mutant")
    if isinstance(mutant, dict):
        candidates.extend(
            [
                mutant.get("source_path"),
                mutant.get("package_path"),
                mutant.get("package"),
                mutant.get("path"),
            ]
        )
    scenario = outcome.get("scenario")
    if isinstance(scenario, dict):
        candidates.extend(
            [
                scenario.get("source_path"),
                scenario.get("package_path"),
                scenario.get("package"),
                scenario.get("path"),
            ]
        )

    for value in candidates:
        text = str(value or "").strip()
        if text:
            return text
    return "(unknown)"


def _read_outcomes_file(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return {}, str(exc)
    except json.JSONDecodeError as exc:
        return {}, f"{path}: invalid json ({exc})"
    if not isinstance(payload, dict):
        return {}, f"{path}: payload is not an object"
    return payload, None


def _collect_outcome_paths(root: Path) -> list[Path]:
    preferred = sorted(root.rglob("shard-*-outcomes.json"))
    if preferred:
        return preferred
    return sorted(root.rglob("outcomes.json"))


def aggregate_outcomes(root: Path) -> tuple[dict[str, Any], str | None]:
    files = _collect_outcome_paths(root)
    if not files:
        return {}, "no mutation outcomes json files found in downloaded artifacts"

    totals = {"caught": 0, "missed": 0, "timeout": 0, "unviable": 0, "other": 0}
    hotspots: dict[str, int] = {}
    freshness: list[dict[str, Any]] = []
    for path in files:
        payload, error = _read_outcomes_file(path)
        if error:
            return {}, error

        counts_from_payload = {
            "caught": int(payload.get("caught", 0)),
            "missed": int(payload.get("missed", 0)),
            "timeout": int(payload.get("timeout", 0)),
            "unviable": int(payload.get("unviable", 0)),
        }
        counts_known = sum(counts_from_payload.values()) > 0
        if counts_known:
            for key, value in counts_from_payload.items():
                totals[key] += value
        outcomes = payload.get("outcomes", [])
        if isinstance(outcomes, list):
            for row in outcomes:
                if not isinstance(row, dict):
                    continue
                summary = str(row.get("summary") or "")
                bucket = _summary_bucket(summary)
                totals[bucket] = totals.get(bucket, 0) + (0 if counts_known else 1)
                if bucket == "missed":
                    hotspot_key = _extract_hotspot_key(row)
                    hotspots[hotspot_key] = hotspots.get(hotspot_key, 0) + 1

        stat = path.stat()
        updated = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        age_hours = max(
            0.0,
            (datetime.now(timezone.utc) - updated).total_seconds() / 3600.0,
        )
        freshness.append(
            {
                "path": str(path),
                "updated_at": updated.isoformat().replace("+00:00", "Z"),
                "age_hours": round(age_hours, 3),
            }
        )

    denom = totals["caught"] + totals["missed"] + totals["timeout"]
    score = 1.0 if denom == 0 else totals["caught"] / denom
    hotspot_rows = [
        {"path": path, "survivors": count}
        for path, count in sorted(hotspots.items(), key=lambda item: (-item[1], item[0]))
    ]
    return {
        "files": [str(path) for path in files],
        "counts": totals,
        "score": score,
        "freshness": freshness,
        "hotspots": hotspot_rows,
    }, None
