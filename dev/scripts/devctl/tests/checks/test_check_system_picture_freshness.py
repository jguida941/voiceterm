"""Tests for the SystemPicture freshness guard."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.checks.system_picture_freshness.command import build_report
from dev.scripts.devctl.platform.system_picture_models import (
    SystemPictureSection,
    SystemPictureSnapshot,
)


def _section(section_id: str, status: str, command: str = "") -> SystemPictureSection:
    return SystemPictureSection(
        section_id=section_id,
        title=section_id.replace("_", " ").title(),
        status=status,
        summary={},
        source_command=command,
    )


def _snapshot(*sections: SystemPictureSection) -> SystemPictureSnapshot:
    return SystemPictureSnapshot(
        snapshot_id="sys-test",
        head_commit_sha="abc123",
        current_section_count=sum(1 for section in sections if section.status == "current"),
        stale_section_count=sum(1 for section in sections if section.status == "stale"),
        missing_section_count=sum(1 for section in sections if section.status == "missing"),
        sections=sections,
    )


def _errors(report: dict[str, object]) -> list[object]:
    errors = report["errors"]
    assert isinstance(errors, list)
    return errors


def test_build_report_passes_when_required_sections_are_current(tmp_path: Path) -> None:
    report = build_report(
        repo_root=tmp_path,
        snapshot_override=_snapshot(
            _section("startup", "current"),
            _section("graph", "current"),
            _section("external_findings", "missing"),
        ),
    )

    assert report["ok"] is True
    assert report["errors"] == []


def test_build_report_fails_stale_sections(tmp_path: Path) -> None:
    report = build_report(
        repo_root=tmp_path,
        snapshot_override=_snapshot(
            _section("startup", "current"),
            _section(
                "graph",
                "stale",
                "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md",
            ),
        ),
    )

    assert report["ok"] is False
    errors = _errors(report)
    assert any("stale_section: graph" in str(error) for error in errors)
    assert "context-graph --mode bootstrap" in str(errors[0])


def test_build_report_fails_missing_required_sections(tmp_path: Path) -> None:
    report = build_report(
        repo_root=tmp_path,
        snapshot_override=_snapshot(
            _section(
                "startup",
                "missing",
                "python3 dev/scripts/devctl.py startup-context --format summary",
            ),
            _section("graph", "current"),
        ),
    )

    assert report["ok"] is False
    assert any(
        "required_section_not_current: startup" in error
        for error in map(str, _errors(report))
    )
