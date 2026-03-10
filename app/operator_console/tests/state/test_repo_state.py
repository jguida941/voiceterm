"""Tests for app.operator_console.state.repo.repo_state."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from app.operator_console.state.repo.repo_state import (
    RepoStateSnapshot,
    build_repo_state,
    classify_path_category,
    classify_path_risk,
    invalidate_cache,
    summarize_risk,
    _parse_porcelain,
    _read_active_mp_scope,
)


# ── classify_path_risk ──────────────────────────────────────────


class TestClassifyPathRisk:
    def test_ci_workflow_is_high(self):
        assert classify_path_risk(".github/workflows/ci.yml") == "high"

    def test_cargo_toml_is_high(self):
        assert classify_path_risk("Cargo.toml") == "high"
        assert classify_path_risk("rust/Cargo.toml") == "high"

    def test_cargo_lock_is_high(self):
        assert classify_path_risk("Cargo.lock") == "high"

    def test_scripts_root_is_high(self):
        assert classify_path_risk("scripts/operator_console.sh") == "high"

    def test_release_prefix_is_high(self):
        assert classify_path_risk("release_notes.md") == "high"

    def test_rust_source_is_medium(self):
        assert classify_path_risk("rust/src/bin/voiceterm/main.rs") == "medium"

    def test_app_source_is_medium(self):
        assert classify_path_risk("app/operator_console/views/main_window.py") == "medium"

    def test_devctl_scripts_is_medium(self):
        assert classify_path_risk("dev/scripts/devctl/cli.py") == "medium"

    def test_markdown_is_low(self):
        assert classify_path_risk("README.md") == "low"
        assert classify_path_risk("guides/INSTALL.md") == "low"

    def test_active_plan_is_low(self):
        assert classify_path_risk("dev/active/MASTER_PLAN.md") == "low"

    def test_adr_is_low(self):
        assert classify_path_risk("dev/adr/0027-foo.md") == "low"

    def test_unknown_extension_defaults_medium(self):
        assert classify_path_risk("something/unknown.xyz") == "medium"


# ── classify_path_category ──────────────────────────────────────


class TestClassifyPathCategory:
    def test_github_is_ci(self):
        assert classify_path_category(".github/workflows/ci.yml") == "ci"

    def test_rust_is_rust(self):
        assert classify_path_category("rust/src/main.rs") == "rust"

    def test_app_is_python_app(self):
        assert classify_path_category("app/operator_console/run.py") == "python-app"

    def test_devctl_is_python_tooling(self):
        assert classify_path_category("dev/scripts/devctl/cli.py") == "python-tooling"

    def test_markdown_is_docs(self):
        assert classify_path_category("README.md") == "docs"

    def test_toml_is_config(self):
        assert classify_path_category("Cargo.toml") == "config"

    def test_json_is_config(self):
        assert classify_path_category("package.json") == "config"

    def test_yaml_is_config(self):
        assert classify_path_category("config.yaml") == "config"
        assert classify_path_category("config.yml") == "config"

    def test_unknown_is_other(self):
        assert classify_path_category("something.xyz") == "other"


# ── summarize_risk ──────────────────────────────────────────────


class TestSummarizeRisk:
    def test_empty_is_low(self):
        assert summarize_risk([]) == "low"

    def test_all_low_is_low(self):
        assert summarize_risk(["low", "low", "low"]) == "low"

    def test_any_high_is_high(self):
        assert summarize_risk(["low", "medium", "high"]) == "high"

    def test_medium_without_high_is_medium(self):
        assert summarize_risk(["low", "medium"]) == "medium"


# ── _parse_porcelain ────────────────────────────────────────────


class TestParsePorcelain:
    def test_empty_input(self):
        staged, unstaged, untracked, paths = _parse_porcelain("")
        assert (staged, unstaged, untracked) == (0, 0, 0)
        assert paths == []

    def test_staged_file(self):
        staged, unstaged, untracked, paths = _parse_porcelain("M  src/main.rs\n")
        assert staged == 1
        assert unstaged == 0
        assert untracked == 0
        assert paths == ["src/main.rs"]

    def test_unstaged_modification(self):
        staged, unstaged, untracked, paths = _parse_porcelain(" M src/main.rs\n")
        assert staged == 0
        assert unstaged == 1
        assert paths == ["src/main.rs"]

    def test_both_staged_and_unstaged(self):
        staged, unstaged, untracked, paths = _parse_porcelain("MM src/main.rs\n")
        assert staged == 1
        assert unstaged == 1
        assert paths == ["src/main.rs"]

    def test_untracked_file(self):
        staged, unstaged, untracked, paths = _parse_porcelain("?? new_file.py\n")
        assert staged == 0
        assert unstaged == 0
        assert untracked == 1
        assert paths == ["new_file.py"]

    def test_renamed_file_extracts_new_path(self):
        staged, unstaged, untracked, paths = _parse_porcelain(
            "R  old_name.py -> new_name.py\n"
        )
        assert staged == 1
        assert paths == ["new_name.py"]

    def test_mixed_porcelain(self):
        porcelain = textwrap.dedent("""\
            M  rust/src/main.rs
             M app/run.py
            ?? new_file.txt
            A  added.py
            D  deleted.rs
        """)
        staged, unstaged, untracked, paths = _parse_porcelain(porcelain)
        assert staged == 3  # M, A, D in index column
        assert unstaged == 1  # M in worktree column
        assert untracked == 1
        assert len(paths) == 5

    def test_short_lines_are_skipped(self):
        staged, unstaged, untracked, paths = _parse_porcelain("ab\n")
        assert (staged, unstaged, untracked) == (0, 0, 0)
        assert paths == []


# ── _read_active_mp_scope ──────────────────────────────────────


class TestReadActiveMpScope:
    def test_extracts_strategic_focus(self, tmp_path: Path):
        mp_dir = tmp_path / "dev" / "active"
        mp_dir.mkdir(parents=True)
        mp_file = mp_dir / "MASTER_PLAN.md"
        mp_file.write_text(
            "# Master Plan\n"
            "## Status Snapshot\n"
            "- Last tagged release: v1.0\n"
            "- Strategic focus: sequential execution with one primary lane\n"
            "- Other note\n",
            encoding="utf-8",
        )
        result = _read_active_mp_scope(tmp_path)
        assert result == "sequential execution with one primary lane"

    def test_missing_file_returns_none(self, tmp_path: Path):
        assert _read_active_mp_scope(tmp_path) is None

    def test_no_strategic_focus_returns_none(self, tmp_path: Path):
        mp_dir = tmp_path / "dev" / "active"
        mp_dir.mkdir(parents=True)
        mp_file = mp_dir / "MASTER_PLAN.md"
        mp_file.write_text("# Master Plan\n- Some other line\n", encoding="utf-8")
        assert _read_active_mp_scope(tmp_path) is None

    def test_empty_focus_returns_none(self, tmp_path: Path):
        mp_dir = tmp_path / "dev" / "active"
        mp_dir.mkdir(parents=True)
        mp_file = mp_dir / "MASTER_PLAN.md"
        mp_file.write_text("- Strategic focus:\n", encoding="utf-8")
        assert _read_active_mp_scope(tmp_path) is None


# ── build_repo_state ────────────────────────────────────────────


class TestBuildRepoState:
    def setup_method(self):
        invalidate_cache()

    def test_unavailable_when_root_missing(self, tmp_path: Path):
        missing = tmp_path / "nonexistent"
        result = build_repo_state(missing)
        assert result.collection_note is not None
        assert "does not exist" in result.collection_note
        assert result.risk_summary == "unknown"

    def test_collects_from_git(self, tmp_path: Path):
        """Verify the happy path assembles fields from git output."""
        porcelain_output = "M  rust/src/main.rs\n?? new.txt\n"

        def mock_git(repo_root, *args):
            cmd = " ".join(args)
            if "rev-parse --abbrev-ref HEAD" in cmd:
                return "develop"
            if "rev-parse HEAD" in cmd:
                return "abc123def456"
            if "status --porcelain" in cmd:
                return porcelain_output
            return ""

        mp_dir = tmp_path / "dev" / "active"
        mp_dir.mkdir(parents=True)
        (mp_dir / "MASTER_PLAN.md").write_text(
            "- Strategic focus: Theme completion first\n",
            encoding="utf-8",
        )

        with patch(
            "app.operator_console.state.repo.repo_state._git",
            side_effect=mock_git,
        ):
            result = build_repo_state(tmp_path)

        assert result.branch == "develop"
        assert result.head_sha == "abc123def456"
        assert result.head_short == "abc123de"
        assert result.is_dirty is True
        assert result.dirty_file_count == 2
        assert result.staged_count == 1
        assert result.untracked_count == 1
        assert result.active_mp_scope == "Theme completion first"
        assert "rust" in result.changed_path_categories
        assert result.risk_summary == "medium"
        assert result.collection_note is None

    def test_git_failure_returns_unavailable(self, tmp_path: Path):
        import subprocess as sp

        with patch(
            "app.operator_console.state.repo.repo_state._git",
            side_effect=sp.SubprocessError("not a git repo"),
        ):
            result = build_repo_state(tmp_path)

        assert result.collection_note is not None
        assert "git identity failed" in result.collection_note

    def test_cache_returns_same_object(self, tmp_path: Path):
        """Verify that consecutive calls within TTL return cached result."""

        def mock_git(repo_root, *args):
            cmd = " ".join(args)
            if "rev-parse --abbrev-ref HEAD" in cmd:
                return "main"
            if "rev-parse HEAD" in cmd:
                return "aaa111"
            if "status --porcelain" in cmd:
                return ""
            return ""

        with patch(
            "app.operator_console.state.repo.repo_state._git",
            side_effect=mock_git,
        ):
            first = build_repo_state(tmp_path)
            second = build_repo_state(tmp_path)

        assert first is second

    def test_clean_repo_is_not_dirty(self, tmp_path: Path):
        def mock_git(repo_root, *args):
            cmd = " ".join(args)
            if "rev-parse --abbrev-ref HEAD" in cmd:
                return "main"
            if "rev-parse HEAD" in cmd:
                return "deadbeef"
            if "status --porcelain" in cmd:
                return ""
            return ""

        with patch(
            "app.operator_console.state.repo.repo_state._git",
            side_effect=mock_git,
        ):
            result = build_repo_state(tmp_path)

        assert result.is_dirty is False
        assert result.dirty_file_count == 0
        assert result.risk_summary == "low"

    def test_high_risk_paths(self, tmp_path: Path):
        porcelain = "M  .github/workflows/ci.yml\nM  Cargo.toml\n"

        def mock_git(repo_root, *args):
            cmd = " ".join(args)
            if "rev-parse --abbrev-ref HEAD" in cmd:
                return "feature"
            if "rev-parse HEAD" in cmd:
                return "fff000"
            if "status --porcelain" in cmd:
                return porcelain
            return ""

        with patch(
            "app.operator_console.state.repo.repo_state._git",
            side_effect=mock_git,
        ):
            result = build_repo_state(tmp_path)

        assert result.risk_summary == "high"
        assert "ci" in result.changed_path_categories
        assert "config" in result.changed_path_categories
