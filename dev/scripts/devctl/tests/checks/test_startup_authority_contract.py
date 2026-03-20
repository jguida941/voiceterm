"""Tests for check_startup_authority_contract.py — startup authority guard."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from dev.scripts.checks.startup_authority_contract.command import _build_report


def _mock_subprocess_run(*_args, **_kwargs):
    """Return a fake CompletedProcess so git calls yield empty strings."""

    class _Fake:
        returncode = 1
        stdout = ""

    return _Fake()


def _setup_full_layout(root: Path) -> None:
    """Create the minimal repo layout that satisfies all startup-authority checks."""
    (root / "dev" / "active").mkdir(parents=True)
    (root / "dev" / "scripts").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (root / "dev" / "active" / "INDEX.md").write_text("# Index\n", encoding="utf-8")
    (root / "dev" / "active" / "MASTER_PLAN.md").write_text(
        "# Master Plan\n", encoding="utf-8"
    )


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_all_green(tmp_path: Path) -> None:
    """All required files and dirs present -> ok=True, zero errors."""
    _setup_full_layout(tmp_path)

    report = _build_report(repo_root=tmp_path)

    assert report["ok"] is True
    assert report["errors"] == []
    assert report["checks_passed"] == report["checks_run"]
    assert report["command"] == "check_startup_authority_contract"
    assert report["repo_name"] == tmp_path.name


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_missing_agents_md(tmp_path: Path) -> None:
    """Missing AGENTS.md -> ok=False with a startup-authority error."""
    _setup_full_layout(tmp_path)
    (tmp_path / "AGENTS.md").unlink()

    report = _build_report(repo_root=tmp_path)

    assert report["ok"] is False
    authority_errors = [e for e in report["errors"] if "AGENTS.md" in e]
    assert len(authority_errors) == 1


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_missing_tracker(tmp_path: Path) -> None:
    """Missing MASTER_PLAN.md -> ok=False with tracker errors."""
    _setup_full_layout(tmp_path)
    (tmp_path / "dev" / "active" / "MASTER_PLAN.md").unlink()

    report = _build_report(repo_root=tmp_path)

    assert report["ok"] is False
    tracker_errors = [e for e in report["errors"] if "tracker" in e.lower() or "MASTER_PLAN" in e]
    assert len(tracker_errors) >= 1


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_missing_path_roots(tmp_path: Path) -> None:
    """Empty tmp_path with no dirs -> errors about missing path roots."""
    report = _build_report(repo_root=tmp_path)

    assert report["ok"] is False
    path_root_errors = [
        e for e in report["errors"] if "path_roots" in e or "active_docs" in e or "scripts" in e
    ]
    assert len(path_root_errors) >= 2


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_empty_repo_name(tmp_path: Path) -> None:
    """Empty policy with no git -> repo_name falls back to directory name."""
    report = _build_report(repo_root=tmp_path)

    # Even without policy repo_name, scan_repo_governance falls back to dir name
    assert report["repo_name"] == tmp_path.name
    assert report["repo_name"] != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
