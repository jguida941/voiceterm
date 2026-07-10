"""Discovery and learning snapshots for the typed `/develop` controller."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...governance.system_catalog import build_system_catalog
from .models import DevelopmentDiscoverySnapshot, DevelopmentLearningSnapshot


def discovery_snapshot(repo_root: Path) -> DevelopmentDiscoverySnapshot:
    """Summarize system catalog coverage inputs for `/develop`."""
    catalog = build_system_catalog(repo_root=repo_root)
    return DevelopmentDiscoverySnapshot(
        commands=catalog.total_commands,
        guards=catalog.total_guards,
        probes=catalog.total_probes,
        surfaces=catalog.total_surfaces,
        coverage_targets=(
            "commands",
            "guards",
            "probes",
            "surfaces",
            "runtime-spine rows",
            "platform contracts",
        ),
    )


def learning_snapshot(repo_root: Path) -> DevelopmentLearningSnapshot:
    """Summarize typed learning inputs that `/develop` should consume."""
    finding_rows = _jsonl_rows(repo_root / "dev/reports/governance/finding_reviews.jsonl")
    promotion_rows = _jsonl_rows(
        repo_root / "dev/reports/governance/guard_promotion_candidates.jsonl"
    )
    queued_promotions = sum(
        1
        for row in promotion_rows
        if str(row.get("status") or row.get("candidate_status") or "queued") == "queued"
    )
    return DevelopmentLearningSnapshot(
        open_findings=len(finding_rows),
        promotion_candidates=len(promotion_rows),
        queued_promotion_candidates=queued_promotions,
        smartness_inputs=(
            "governance-quality-feedback",
            "probe-report",
            "GuardSmartnessReport",
            "red_team_fixture_result",
        ),
        learning_state="typed_inputs_available",
    )


def _jsonl_rows(path: Path) -> tuple[dict[str, Any], ...]:
    if not path.exists():
        return ()
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return tuple(rows)


__all__ = ["discovery_snapshot", "learning_snapshot"]
