"""Unit tests for Rust audit-pattern guard script metrics."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest import TestCase
from unittest.mock import call, patch

from dev.scripts.devctl.config import REPO_ROOT

SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_rust_audit_patterns.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "check_rust_audit_patterns_script", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_rust_audit_patterns.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckRustAuditPatternsTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def _run_main_json(self, *argv: str) -> tuple[int, dict]:
        buffer = io.StringIO()
        with patch.object(sys, "argv", ["check_rust_audit_patterns.py", *argv]):
            with redirect_stdout(buffer):
                exit_code = self.script.main()
        return exit_code, json.loads(buffer.getvalue())

    def test_count_metrics_detects_target_patterns(self) -> None:
        text = """
fn sample(prompt: &str, line: &str, mut input: String) {
    let _ = &prompt[..prompt.len().min(30)];
    let _ = &line[..line.len().min(50)];
    input.truncate(INPUT_MAX_CHARS);
    let mut redacted = input.clone();
    if let Some(pos) = redacted.find("sk-") {
        redacted.replace_range(pos..pos + 2, "**");
    }
    let _suffix = (123u32).wrapping_mul(2654435761);
    let clamped = 1.0_f32;
    let _sample = (clamped * 32_768.0) as i16;
}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["utf8_prefix_slice"], 2)
        self.assertEqual(metrics["char_limit_truncate"], 1)
        self.assertEqual(metrics["single_pass_secret_find"], 1)
        self.assertEqual(metrics["deterministic_id_hash_suffix"], 1)
        self.assertEqual(metrics["lossy_vad_cast_i16"], 1)

    def test_has_positive_metrics(self) -> None:
        self.assertFalse(
            self.script._has_positive_metrics(
                {name: 0 for name in self.script.PATTERNS}
            )
        )
        self.assertTrue(
            self.script._has_positive_metrics(
                {
                    "utf8_prefix_slice": 0,
                    "char_limit_truncate": 0,
                    "single_pass_secret_find": 1,
                    "deterministic_id_hash_suffix": 0,
                    "lossy_vad_cast_i16": 0,
                }
            )
        )

    def test_source_root_points_to_rust_workspace(self) -> None:
        rel = self.script.SOURCE_ROOT.relative_to(REPO_ROOT).as_posix()
        self.assertEqual(rel, "rust/src")

    def test_iter_rust_paths_scoped_to_source_root(self) -> None:
        paths = self.script._iter_rust_paths()
        source_root = self.script.SOURCE_ROOT
        for path in paths:
            path.relative_to(source_root)
            self.assertTrue(path.suffix == ".rs")
            self.assertNotIn("target", path.parts)

    def test_runtime_source_scope_rejects_prefix_collisions(self) -> None:
        self.assertTrue(
            self.script._is_runtime_source_path(Path("rust/src/bin/main.rs"))
        )
        self.assertFalse(
            self.script._is_runtime_source_path(Path("rust/src2/bin/main.rs"))
        )
        self.assertFalse(
            self.script._is_runtime_source_path(Path("rust/src_backup/bin/main.rs"))
        )

    def test_main_commit_range_uses_refs_and_runtime_scope(self) -> None:
        changed = [
            Path("rust/src/bin/voiceterm/ok.rs"),
            Path("rust/src2/bin/voiceterm/not_ok.rs"),
            Path("rust/src_backup/bin/voiceterm/not_ok.rs"),
            Path("docs/not_rust.rs"),
        ]
        with patch.object(
            self.script.guard, "validate_ref"
        ) as validate_ref, patch.object(
            self.script,
            "_list_changed_paths",
            return_value=changed,
        ), patch.object(
            self.script.guard,
            "read_text_from_ref",
            return_value="fn scoped() {}\n",
        ) as read_ref, patch.object(
            self.script.guard,
            "read_text_from_worktree",
        ) as read_worktree:
            code, report = self._run_main_json(
                "--since-ref",
                "origin/master",
                "--head-ref",
                "HEAD",
                "--format",
                "json",
            )
        self.assertEqual(code, 0)
        self.assertEqual(report["mode"], "commit-range")
        self.assertEqual(report["since_ref"], "origin/master")
        self.assertEqual(report["head_ref"], "HEAD")
        self.assertEqual(report["files_considered"], 1)
        self.assertEqual(
            validate_ref.call_args_list, [call("origin/master"), call("HEAD")]
        )
        read_ref.assert_called_once_with(Path("rust/src/bin/voiceterm/ok.rs"), "HEAD")
        read_worktree.assert_not_called()

    def test_main_stale_pattern_warning_when_all_totals_zero(self) -> None:
        with patch.object(
            self.script,
            "_list_changed_paths",
            return_value=[Path("rust/src/bin/voiceterm/no_matches.rs")],
        ), patch.object(
            self.script.guard,
            "read_text_from_worktree",
            return_value="fn no_matches() {}\n",
        ):
            code, report = self._run_main_json("--format", "json")
        self.assertEqual(code, 0)
        self.assertEqual(report["mode"], "working-tree")
        self.assertEqual(report["files_considered"], 1)
        self.assertIsNotNone(report["stale_pattern_warning"])
        expected = f"all {len(self.script.PATTERNS)} audit patterns matched zero times across 1 file"
        self.assertIn(expected, report["stale_pattern_warning"])

    def test_main_error_on_invalid_since_ref(self) -> None:
        with patch.object(
            self.script.guard,
            "validate_ref",
            side_effect=RuntimeError("unknown revision"),
        ):
            code, report = self._run_main_json(
                "--since-ref",
                "nonexistent",
                "--format",
                "json",
            )
        self.assertEqual(code, 2)
        self.assertEqual(report["mode"], "error")
        self.assertIn("unknown revision", report["error"])
