"""Unit tests for the Ralph AI fix wrapper (ralph_ai_fix.py)."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.ralph_ai_fix import (
    _FALLBACK_CATEGORY_TO_ARCH,
    build_prompt,
    commit_and_push,
    detect_architectures,
    has_changes,
    invoke_claude,
    load_backlog,
    main,
)


def _make_backlog(items: list[dict]) -> dict:
    """Build a backlog-medium.json payload."""
    return {"items": items}


def _sample_items() -> list[dict]:
    return [
        {"severity": "high", "category": "rust", "summary": "Unused import in auth.rs"},
        {"severity": "medium", "category": "python", "summary": "Broad except clause"},
    ]


# -- load_backlog -----------------------------------------------------------


class LoadBacklogTests(unittest.TestCase):
    def test_valid_json_returns_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            items = _sample_items()
            backlog_file = Path(tmp) / "backlog-medium.json"
            backlog_file.write_text(json.dumps(_make_backlog(items)))

            result = load_backlog(tmp)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["severity"], "high")
            self.assertEqual(result[1]["category"], "python")

    def test_empty_items_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            backlog_file = Path(tmp) / "backlog-medium.json"
            backlog_file.write_text(json.dumps(_make_backlog([])))

            result = load_backlog(tmp)
            self.assertEqual(result, [])

    def test_missing_file_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = load_backlog(tmp)
            self.assertEqual(result, [])

    def test_missing_items_key_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            backlog_file = Path(tmp) / "backlog-medium.json"
            backlog_file.write_text(json.dumps({"version": 1}))

            result = load_backlog(tmp)
            self.assertEqual(result, [])

    def test_malformed_json_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            backlog_file = Path(tmp) / "backlog-medium.json"
            backlog_file.write_text("{not valid json")

            with self.assertRaises(json.JSONDecodeError):
                load_backlog(tmp)


# -- build_prompt -----------------------------------------------------------


class BuildPromptTests(unittest.TestCase):
    def test_prompt_contains_findings(self) -> None:
        items = _sample_items()
        prompt = build_prompt(items, attempt=1)
        self.assertIn("Unused import in auth.rs", prompt)
        self.assertIn("Broad except clause", prompt)

    def test_prompt_contains_attempt_number(self) -> None:
        prompt = build_prompt(_sample_items(), attempt=3)
        self.assertIn("attempt 3", prompt)

    def test_prompt_contains_false_positive_filtering(self) -> None:
        prompt = build_prompt(_sample_items(), attempt=1)
        self.assertIn("false positive", prompt)
        self.assertIn("skip it", prompt)

    def test_prompt_includes_severity_and_category(self) -> None:
        items = [{"severity": "low", "category": "ios", "summary": "Lint warning"}]
        prompt = build_prompt(items, attempt=1)
        self.assertIn("[low]", prompt)
        self.assertIn("(ios)", prompt)

    def test_prompt_handles_missing_fields_gracefully(self) -> None:
        items = [{}]
        prompt = build_prompt(items, attempt=1)
        self.assertIn("[unknown]", prompt)
        self.assertIn("(unknown)", prompt)
        self.assertIn("no summary", prompt)

    def test_prompt_numbers_findings_sequentially(self) -> None:
        items = [
            {"severity": "high", "category": "rust", "summary": "Issue A"},
            {"severity": "low", "category": "python", "summary": "Issue B"},
            {"severity": "medium", "category": "ios", "summary": "Issue C"},
        ]
        prompt = build_prompt(items, attempt=1)
        self.assertIn("1.", prompt)
        self.assertIn("2.", prompt)
        self.assertIn("3.", prompt)

    def test_prompt_with_guardrails_config_includes_standards(self) -> None:
        items = [{"severity": "high", "category": "rust", "summary": "Issue A"}]
        config = {
            "standards": {
                "rust": {
                    "description": "Follow Rust best practices",
                    "agents_md_section": "Rust section",
                },
            },
        }
        prompt = build_prompt(items, attempt=1, guardrails_config=config)
        self.assertIn("Applicable Standards", prompt)
        self.assertIn("Follow Rust best practices", prompt)

    def test_prompt_without_guardrails_config_omits_standards(self) -> None:
        items = _sample_items()
        prompt = build_prompt(items, attempt=1)
        self.assertNotIn("Applicable Standards", prompt)


# -- detect_architectures ---------------------------------------------------


class DetectArchitecturesTests(unittest.TestCase):
    def test_rust_categories(self) -> None:
        for cat in ("rust", "performance", "security"):
            items = [{"category": cat}]
            self.assertIn("rust", detect_architectures(items), f"category={cat}")

    def test_python_devctl_categories(self) -> None:
        for cat in ("python", "tooling", "quality", "docs", "ci", "infra"):
            items = [{"category": cat}]
            self.assertIn("python-devctl", detect_architectures(items), f"category={cat}")

    def test_operator_console_categories(self) -> None:
        for cat in ("operator-console", "ui"):
            items = [{"category": cat}]
            self.assertIn(
                "python-operator-console",
                detect_architectures(items),
                f"category={cat}",
            )

    def test_ios_categories(self) -> None:
        for cat in ("ios", "mobile"):
            items = [{"category": cat}]
            self.assertIn("ios", detect_architectures(items), f"category={cat}")

    def test_unknown_category_defaults_to_python_devctl(self) -> None:
        items = [{"category": "banana"}]
        self.assertEqual(detect_architectures(items), {"python-devctl"})

    def test_missing_category_defaults_to_python_devctl(self) -> None:
        items = [{}]
        self.assertEqual(detect_architectures(items), {"python-devctl"})

    def test_mixed_categories_returns_multiple_architectures(self) -> None:
        items = [{"category": "rust"}, {"category": "python"}, {"category": "ios"}]
        archs = detect_architectures(items)
        self.assertEqual(archs, {"rust", "python-devctl", "ios"})

    def test_case_insensitive_lookup(self) -> None:
        items = [{"category": "Rust"}, {"category": "PYTHON"}]
        archs = detect_architectures(items)
        self.assertIn("rust", archs)
        self.assertIn("python-devctl", archs)

    def test_all_known_categories_are_mapped(self) -> None:
        """Every _FALLBACK_CATEGORY_TO_ARCH key maps to a valid architecture."""
        for cat, arch in _FALLBACK_CATEGORY_TO_ARCH.items():
            items = [{"category": cat}]
            self.assertIn(arch, detect_architectures(items))

    def test_guardrails_config_overrides_fallback(self) -> None:
        custom_map = {"rust": "custom-arch"}
        config = {"category_to_architecture": custom_map}
        items = [{"category": "rust"}]
        archs = detect_architectures(items, guardrails_config=config)
        self.assertEqual(archs, {"custom-arch"})


# -- has_changes -------------------------------------------------------------


class HasChangesTests(unittest.TestCase):
    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_returns_true_when_diff_exits_nonzero(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            ["git", "diff", "--quiet"], returncode=1
        )
        self.assertTrue(has_changes())

    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_returns_false_when_diff_exits_zero(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess(
            ["git", "diff", "--quiet"], returncode=0
        )
        self.assertFalse(has_changes())


# -- commit_and_push ---------------------------------------------------------


class CommitAndPushTests(unittest.TestCase):
    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_success_path(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess([], returncode=0)
        result = commit_and_push("develop", attempt=2, item_count=5)
        self.assertTrue(result)
        # Should call: git add -u, git commit, git push
        self.assertEqual(run_mock.call_count, 3)

    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_commit_failure_returns_false(self, run_mock) -> None:
        def side_effect(cmd, **kwargs):
            if cmd[0] == "git" and cmd[1] == "commit":
                return subprocess.CompletedProcess(cmd, returncode=1)
            return subprocess.CompletedProcess(cmd, returncode=0)

        run_mock.side_effect = side_effect
        result = commit_and_push("develop", attempt=1, item_count=3)
        self.assertFalse(result)

    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_push_failure_returns_false(self, run_mock) -> None:
        def side_effect(cmd, **kwargs):
            if cmd[0] == "git" and cmd[1] == "push":
                return subprocess.CompletedProcess(cmd, returncode=1)
            return subprocess.CompletedProcess(cmd, returncode=0)

        run_mock.side_effect = side_effect
        result = commit_and_push("develop", attempt=1, item_count=2)
        self.assertFalse(result)

    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_commit_message_includes_attempt_and_count(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess([], returncode=0)
        commit_and_push("develop", attempt=4, item_count=7)
        # Find the commit call (second call: add, commit, push)
        commit_call = run_mock.call_args_list[1]
        cmd = commit_call[0][0]
        msg = cmd[3]  # ["git", "commit", "-m", <msg>]
        self.assertIn("attempt 4", msg)
        self.assertIn("7", msg)

    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_push_targets_correct_branch(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess([], returncode=0)
        commit_and_push("feature/ralph-fix", attempt=1, item_count=1)
        push_call = run_mock.call_args_list[2]
        cmd = push_call[0][0]
        self.assertEqual(cmd, ["git", "push", "origin", "feature/ralph-fix"])


# -- invoke_claude -----------------------------------------------------------


class InvokeClaudeTests(unittest.TestCase):
    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_trusted_mode_uses_skip_permissions(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess([], returncode=0)
        with patch.dict(os.environ, {"RALPH_APPROVAL_MODE": "trusted"}):
            invoke_claude("fix stuff")
        cmd = run_mock.call_args[0][0]
        self.assertIn("--dangerously-skip-permissions", cmd)
        self.assertNotIn("--permission-mode", cmd)

    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_balanced_mode_uses_auto_permissions(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess([], returncode=0)
        with patch.dict(os.environ, {"RALPH_APPROVAL_MODE": "balanced"}):
            invoke_claude("fix stuff")
        cmd = run_mock.call_args[0][0]
        self.assertIn("--permission-mode", cmd)
        self.assertIn("auto", cmd)
        self.assertNotIn("--dangerously-skip-permissions", cmd)

    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_strict_mode_uses_auto_permissions(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess([], returncode=0)
        with patch.dict(os.environ, {"RALPH_APPROVAL_MODE": "strict"}):
            invoke_claude("fix stuff")
        cmd = run_mock.call_args[0][0]
        self.assertIn("--permission-mode", cmd)
        self.assertNotIn("--dangerously-skip-permissions", cmd)

    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_default_mode_without_env_var(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess([], returncode=0)
        env = os.environ.copy()
        env.pop("RALPH_APPROVAL_MODE", None)
        with patch.dict(os.environ, env, clear=True):
            invoke_claude("fix stuff")
        cmd = run_mock.call_args[0][0]
        # Default is "balanced", which uses --permission-mode auto
        self.assertIn("--permission-mode", cmd)

    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_returns_subprocess_exit_code(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess([], returncode=42)
        with patch.dict(os.environ, {"RALPH_APPROVAL_MODE": "balanced"}):
            rc = invoke_claude("fix stuff")
        self.assertEqual(rc, 42)

    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    def test_prompt_is_appended_to_command(self, run_mock) -> None:
        run_mock.return_value = subprocess.CompletedProcess([], returncode=0)
        with patch.dict(os.environ, {"RALPH_APPROVAL_MODE": "balanced"}):
            invoke_claude("please fix these findings")
        cmd = run_mock.call_args[0][0]
        self.assertEqual(cmd[-1], "please fix these findings")


# -- main --------------------------------------------------------------------


class MainTests(unittest.TestCase):
    def _env(self, **overrides) -> dict:
        """Build a valid Ralph environment dict."""
        base = {
            "RALPH_ATTEMPT": "1",
            "RALPH_REPO": "owner/repo",
            "RALPH_BRANCH": "develop",
            "RALPH_BACKLOG_DIR": "/tmp/ralph-backlog",
            "RALPH_BACKLOG_COUNT": "2",
            "RALPH_APPROVAL_MODE": "balanced",
        }
        base.update(overrides)
        return base

    def test_missing_backlog_dir_returns_2(self) -> None:
        env = self._env()
        env.pop("RALPH_BACKLOG_DIR")
        with patch.dict(os.environ, env, clear=True):
            rc = main()
        self.assertEqual(rc, 2)

    @patch("dev.scripts.ralph_ai_fix.load_backlog", return_value=[])
    def test_empty_backlog_returns_0(self, _load_mock) -> None:
        with patch.dict(os.environ, self._env(), clear=True):
            rc = main()
        self.assertEqual(rc, 0)

    @patch("dev.scripts.ralph_ai_fix.commit_and_push", return_value=True)
    @patch("dev.scripts.ralph_ai_fix.run_arch_checks", return_value=True)
    @patch("dev.scripts.ralph_ai_fix.has_changes", return_value=True)
    @patch("dev.scripts.ralph_ai_fix.invoke_claude", return_value=0)
    @patch("dev.scripts.ralph_ai_fix.load_backlog", return_value=_sample_items())
    def test_happy_path_returns_0(
        self, _load, _invoke, _changes, _checks, _commit
    ) -> None:
        with patch.dict(os.environ, self._env(), clear=True):
            rc = main()
        self.assertEqual(rc, 0)
        _commit.assert_called_once_with("develop", 1, 2)

    @patch("dev.scripts.ralph_ai_fix.invoke_claude", return_value=1)
    @patch("dev.scripts.ralph_ai_fix.load_backlog", return_value=_sample_items())
    def test_claude_failure_returns_1(self, _load, _invoke) -> None:
        with patch.dict(os.environ, self._env(), clear=True):
            rc = main()
        self.assertEqual(rc, 1)

    @patch("dev.scripts.ralph_ai_fix.has_changes", return_value=False)
    @patch("dev.scripts.ralph_ai_fix.invoke_claude", return_value=0)
    @patch("dev.scripts.ralph_ai_fix.load_backlog", return_value=_sample_items())
    def test_no_changes_returns_0(self, _load, _invoke, _changes) -> None:
        with patch.dict(os.environ, self._env(), clear=True):
            rc = main()
        self.assertEqual(rc, 0)

    @patch("dev.scripts.ralph_ai_fix.subprocess.run")
    @patch("dev.scripts.ralph_ai_fix.run_arch_checks", return_value=False)
    @patch("dev.scripts.ralph_ai_fix.has_changes", return_value=True)
    @patch("dev.scripts.ralph_ai_fix.invoke_claude", return_value=0)
    @patch("dev.scripts.ralph_ai_fix.load_backlog", return_value=_sample_items())
    def test_failed_arch_checks_reverts_and_returns_1(
        self, _load, _invoke, _changes, _checks, _subprocess_run
    ) -> None:
        _subprocess_run.return_value = subprocess.CompletedProcess([], returncode=0)
        with patch.dict(os.environ, self._env(), clear=True):
            rc = main()
        self.assertEqual(rc, 1)
        # Should have called git checkout . to revert
        revert_call = _subprocess_run.call_args[0][0]
        self.assertEqual(revert_call, ["git", "checkout", "."])

    @patch("dev.scripts.ralph_ai_fix.commit_and_push", return_value=True)
    @patch("dev.scripts.ralph_ai_fix.run_arch_checks", return_value=True)
    @patch("dev.scripts.ralph_ai_fix.has_changes", return_value=True)
    @patch("dev.scripts.ralph_ai_fix.invoke_claude", return_value=0)
    @patch("dev.scripts.ralph_ai_fix.load_backlog", return_value=_sample_items())
    def test_missing_branch_returns_2(
        self, _load, _invoke, _changes, _checks, _commit
    ) -> None:
        env = self._env(RALPH_BRANCH="")
        with patch.dict(os.environ, env, clear=True):
            rc = main()
        self.assertEqual(rc, 2)

    @patch("dev.scripts.ralph_ai_fix.commit_and_push", return_value=False)
    @patch("dev.scripts.ralph_ai_fix.run_arch_checks", return_value=True)
    @patch("dev.scripts.ralph_ai_fix.has_changes", return_value=True)
    @patch("dev.scripts.ralph_ai_fix.invoke_claude", return_value=0)
    @patch("dev.scripts.ralph_ai_fix.load_backlog", return_value=_sample_items())
    def test_commit_push_failure_returns_1(
        self, _load, _invoke, _changes, _checks, _commit
    ) -> None:
        with patch.dict(os.environ, self._env(), clear=True):
            rc = main()
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
