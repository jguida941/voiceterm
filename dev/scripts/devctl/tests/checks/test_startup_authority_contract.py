"""Tests for check_startup_authority_contract.py — startup authority guard."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from dev.scripts.checks.startup_authority_contract.command import _build_report
from dev.scripts.checks.startup_authority_contract.runtime_checks import (
    collect_import_index_atomicity_findings,
)


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


def _write_policy(root: Path, payload: dict[str, object]) -> None:
    policy_path = root / "dev" / "config" / "devctl_repo_policy.json"
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(json.dumps(payload), encoding="utf-8")


def _fake_governance(
    repo_root: Path,
    *,
    checkpoint_required: bool = False,
    safe_to_continue_editing: bool = True,
    checkpoint_reason: str = "clean_worktree",
):
    return SimpleNamespace(
        docs_authority="AGENTS.md",
        plan_registry=SimpleNamespace(
            registry_path="dev/active/INDEX.md",
            tracker_path="dev/active/MASTER_PLAN.md",
        ),
        path_roots=SimpleNamespace(
            active_docs="dev/active",
            scripts="dev/scripts",
        ),
        repo_identity=SimpleNamespace(repo_name=repo_root.name),
        startup_order=("AGENTS.md", "dev/active/INDEX.md", "dev/active/MASTER_PLAN.md"),
        push_enforcement=SimpleNamespace(
            checkpoint_required=checkpoint_required,
            safe_to_continue_editing=safe_to_continue_editing,
            checkpoint_reason=checkpoint_reason,
        ),
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


@patch("dev.scripts.devctl.governance.draft.subprocess.run", _mock_subprocess_run)
def test_startup_authority_uses_policy_bootstrap_paths(tmp_path: Path) -> None:
    (tmp_path / "docs" / "plans").mkdir(parents=True)
    (tmp_path / "tools").mkdir(parents=True)
    (tmp_path / "CONTRIBUTING.md").write_text("# Process\n", encoding="utf-8")
    (tmp_path / "docs" / "plans" / "INDEX.md").write_text(
        "# Index\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "plans" / "MASTER_PLAN.md").write_text(
        "# Master Plan\n", encoding="utf-8"
    )
    _write_policy(
        tmp_path,
        {
            "schema_version": 1,
            "repo_name": "PortableRepo",
            "repo_governance": {
                "surface_generation": {
                    "context": {
                        "process_doc": "CONTRIBUTING.md",
                        "execution_tracker_doc": "docs/plans/MASTER_PLAN.md",
                        "active_registry_doc": "docs/plans/INDEX.md",
                        "python_tooling": "tools/",
                    },
                },
            },
        },
    )

    report = _build_report(repo_root=tmp_path)

    assert report["ok"] is True
    assert report["errors"] == []


def test_startup_authority_fails_when_checkpoint_budget_is_exceeded(
    tmp_path: Path,
) -> None:
    _setup_full_layout(tmp_path)
    fake_module = SimpleNamespace(
        scan_repo_governance=lambda _root: _fake_governance(
            tmp_path,
            checkpoint_required=True,
            safe_to_continue_editing=False,
            checkpoint_reason="dirty_path_budget_exceeded",
        )
    )

    with (
        patch(
            "dev.scripts.checks.startup_authority_contract.command.import_repo_module",
            return_value=fake_module,
        ),
        patch(
            "dev.scripts.checks.startup_authority_contract.command.collect_import_index_atomicity_findings",
            return_value=([], []),
        ),
    ):
        report = _build_report(repo_root=tmp_path)

    assert report["ok"] is False
    assert report["checkpoint_required"] is True
    assert report["safe_to_continue_editing"] is False
    assert any("over budget" in error for error in report["errors"])


def test_import_index_atomicity_flags_repo_local_worktree_only_module(
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    importer = tmp_path / "dev" / "testpkg" / "importer.py"
    importer.parent.mkdir(parents=True)
    importer.write_text("from . import startup_signals\n", encoding="utf-8")
    (tmp_path / "dev" / "testpkg" / "startup_signals.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "dev/testpkg/importer.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    with patch(
        "dev.scripts.checks.startup_authority_contract.runtime_checks.resolve_quality_scope_roots",
        return_value=(Path("dev"),),
    ):
        errors, warnings = collect_import_index_atomicity_findings(tmp_path)

    assert warnings == []
    assert any("startup_signals.py" in error for error in errors)


def test_import_index_atomicity_accepts_indexed_module_split(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    importer = tmp_path / "dev" / "testpkg" / "importer.py"
    importer.parent.mkdir(parents=True)
    importer.write_text("from . import startup_signals\n", encoding="utf-8")
    (tmp_path / "dev" / "testpkg" / "startup_signals.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "dev/testpkg/importer.py", "dev/testpkg/startup_signals.py"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    with patch(
        "dev.scripts.checks.startup_authority_contract.runtime_checks.resolve_quality_scope_roots",
        return_value=(Path("dev"),),
    ):
        errors, warnings = collect_import_index_atomicity_findings(tmp_path)

    assert errors == []
    assert warnings == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
