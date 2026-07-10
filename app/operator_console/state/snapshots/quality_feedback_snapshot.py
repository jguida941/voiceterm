"""Cached quality-feedback snapshot reader for the Operator Console."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
import time
from typing import Any

from dev.scripts.devctl.repo_packs import voiceterm_repo_root

_CACHE_TTL_SECONDS = 120.0
_CACHE_LOCK = Lock()
_CACHE: dict[str, tuple[float, "QualityFeedbackOCSnapshot | None"]] = {}

_ARTIFACT_REL_PATH = (
    "dev/reports/governance/quality_feedback_latest/quality_feedback_snapshot.json"
)


@dataclass(frozen=True)
class QualityFeedbackSubScore:
    """One sub-score from the maintainability composite."""

    name: str
    value: float
    weight: float
    weighted: float


@dataclass(frozen=True)
class QualityFeedbackOCSnapshot:
    """Thin OC-facing view of the quality-feedback artifact."""

    captured_at_utc: str
    repo_name: str
    overall_score: float
    grade: str
    sub_scores: tuple[QualityFeedbackSubScore, ...]
    files_scanned: int
    avg_maintainability_index: float
    estimated_total_bugs: float
    fp_count: int
    recommendation_count: int
    top_recommendations: tuple[dict[str, Any], ...]


def load_quality_feedback_snapshot(
    repo_root: Path,
) -> QualityFeedbackOCSnapshot | None:
    """Return a cached quality-feedback snapshot read from the artifact JSON."""
    devctl_root = voiceterm_repo_root()
    if devctl_root is None:
        return None
    if repo_root.resolve() != devctl_root.resolve():
        return None

    cache_key = str(repo_root.resolve())
    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None and now - cached[0] < _CACHE_TTL_SECONDS:
            return cached[1]

    snapshot = _load_uncached(repo_root)
    with _CACHE_LOCK:
        _CACHE[cache_key] = (now, snapshot)
    return snapshot


def _load_uncached(repo_root: Path) -> QualityFeedbackOCSnapshot | None:
    artifact_path = repo_root / _ARTIFACT_REL_PATH
    if not artifact_path.exists():
        return None
    try:
        raw = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    return _parse_snapshot(raw)


def _parse_snapshot(raw: dict[str, Any]) -> QualityFeedbackOCSnapshot | None:
    maintainability = raw.get("maintainability_score")
    if not isinstance(maintainability, dict):
        return None
    halstead = raw.get("halstead_summary") or {}
    fp_analysis = raw.get("false_positive_analysis") or {}
    recommendations = raw.get("recommendations") or []

    sub_scores_raw = maintainability.get("sub_scores") or {}
    sub_scores = tuple(
        QualityFeedbackSubScore(
            name=str(name),
            value=float(entry.get("value", 0)),
            weight=float(entry.get("weight", 0)),
            weighted=float(entry.get("weighted", 0)),
        )
        for name, entry in sub_scores_raw.items()
        if isinstance(entry, dict)
    )

    return QualityFeedbackOCSnapshot(
        captured_at_utc=str(raw.get("generated_at_utc") or ""),
        repo_name=str(raw.get("repo_name") or ""),
        overall_score=float(maintainability.get("overall", 0)),
        grade=str(maintainability.get("grade", "F")),
        sub_scores=sub_scores,
        files_scanned=int(halstead.get("files_scanned", 0)),
        avg_maintainability_index=float(
            halstead.get("avg_maintainability_index", 0)
        ),
        estimated_total_bugs=float(halstead.get("estimated_total_bugs", 0)),
        fp_count=int(fp_analysis.get("total_fp_count", 0)),
        recommendation_count=len(recommendations),
        top_recommendations=tuple(
            r for r in recommendations[:5] if isinstance(r, dict)
        ),
    )
