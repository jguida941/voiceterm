"""Artifact-backed section builders for the system-picture snapshot.

These sections load JSON summary artifacts from known report paths and
produce SystemPictureSection rows. They share the _load_json + _build_section
helpers from the parent sections module.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..common_io import display_path
from ..repo_packs import active_path_config
from .system_picture_models import SystemPictureSection
from .system_picture_sections import _build_section


def build_governance_review_section(
    *,
    repo_root: Path,
) -> SystemPictureSection:
    """Build the governance-review section from the latest summary artifact."""
    path = repo_root / active_path_config().governance_review_summary_root_rel / "review_summary.json"
    payload = _load_json(path)
    if not payload:
        return _build_section(
            section_id="governance_review",
            title="Governance Review",
            status="missing",
            summary={},
            source_path=display_path(path, repo_root=repo_root),
            source_command="python3 dev/scripts/devctl.py governance-review --format md",
            generated_at_utc="",
            notes=("No latest governance-review summary artifact is present.",),
        )
    stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
    summary = {
        "total_findings": stats.get("total_findings"),
        "open_finding_count": stats.get("open_finding_count"),
        "fixed_count": stats.get("fixed_count"),
        "cleanup_rate_pct": stats.get("cleanup_rate_pct"),
        "false_positive_rate_pct": stats.get("false_positive_rate_pct"),
    }
    return _build_section(
        section_id="governance_review",
        title="Governance Review",
        status="current",
        summary=summary,
        source_path=display_path(path, repo_root=repo_root),
        source_command="python3 dev/scripts/devctl.py governance-review --format md",
        generated_at_utc=str(payload.get("generated_at_utc") or "").strip(),
        notes=(),
    )


def build_external_findings_section(
    *,
    repo_root: Path,
) -> SystemPictureSection:
    """Build the external-findings section from the latest summary artifact."""
    path = (
        repo_root
        / active_path_config().external_finding_summary_root_rel
        / "external_findings_summary.json"
    )
    payload = _load_json(path)
    if not payload:
        return _build_section(
            section_id="external_findings",
            title="External Findings",
            status="missing",
            summary={},
            source_path=display_path(path, repo_root=repo_root),
            source_command="python3 dev/scripts/devctl.py governance-import-findings --format md",
            generated_at_utc="",
            notes=("No latest external-findings summary artifact is present.",),
        )
    stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
    summary = {
        "total_findings": stats.get("total_findings"),
        "unique_repo_count": stats.get("unique_repo_count"),
        "reviewed_count": stats.get("reviewed_count"),
        "adjudication_coverage_pct": stats.get("adjudication_coverage_pct"),
        "fixed_count": stats.get("fixed_count"),
        "confirmed_issue_count": stats.get("confirmed_issue_count"),
    }
    return _build_section(
        section_id="external_findings",
        title="External Findings",
        status="current",
        summary=summary,
        source_path=display_path(path, repo_root=repo_root),
        source_command="python3 dev/scripts/devctl.py governance-import-findings --format md",
        generated_at_utc=str(payload.get("generated_at_utc") or "").strip(),
        notes=(),
    )


def build_data_science_section(
    *,
    repo_root: Path,
) -> SystemPictureSection:
    """Build the data-science section from the latest summary artifact."""
    path = repo_root / active_path_config().data_science_output_root_rel / "latest" / "summary.json"
    payload = _load_json(path)
    if not payload:
        return _build_section(
            section_id="data_science",
            title="Data Science",
            status="missing",
            summary={},
            source_path=display_path(path, repo_root=repo_root),
            source_command="python3 dev/scripts/devctl.py data-science --format md",
            generated_at_utc="",
            notes=("No latest data-science summary artifact is present.",),
        )
    event_stats = payload.get("event_stats") if isinstance(payload.get("event_stats"), dict) else {}
    watchdog = payload.get("watchdog_stats") if isinstance(payload.get("watchdog_stats"), dict) else {}
    external = payload.get("external_finding_stats") if isinstance(payload.get("external_finding_stats"), dict) else {}
    summary = {
        "total_events": event_stats.get("total_events"),
        "command_success_rate_pct": event_stats.get("success_rate_pct"),
        "command_p95_duration_seconds": event_stats.get("p95_duration_seconds"),
        "watchdog_total_episodes": watchdog.get("total_episodes"),
        "watchdog_success_rate_pct": watchdog.get("success_rate_pct"),
        "external_unique_repo_count": external.get("unique_repo_count"),
    }
    return _build_section(
        section_id="data_science",
        title="Data Science",
        status="current",
        summary=summary,
        source_path=display_path(path, repo_root=repo_root),
        source_command="python3 dev/scripts/devctl.py data-science --format md",
        generated_at_utc=str(payload.get("generated_at") or "").strip(),
        notes=(),
    )


def _load_json(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dict(payload) if isinstance(payload, dict) else None
