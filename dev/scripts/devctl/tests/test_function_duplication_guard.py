"""Unit tests for check_function_duplication guard script."""

from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from conftest import load_repo_module

SCRIPT = load_repo_module(
    "check_function_duplication_script",
    "dev/scripts/checks/check_function_duplication.py",
)


def _rust_function(name: str, body_lines: list[str]) -> str:
    indented = [f"    {line}" for line in body_lines]
    return "\n".join([f"fn {name}() {{"] + indented + ["}"])


def _python_function(name: str, body_lines: list[str]) -> str:
    indented = [f"    {line}" for line in body_lines]
    return "\n".join([f"def {name}():"] + indented)


def _first_hash(source: str, ext: str) -> str:
    return SCRIPT._extract_function_hashes(source, ext)[0]["hash"]


def _run_main_json(
    *,
    changed_paths: list[str],
    worktree_texts: dict[str, str | None],
    ref_texts: dict[str, str | None] | None = None,
    global_index: dict[str, list[tuple[str, str]]] | None = None,
) -> tuple[int, dict, MagicMock]:
    normalized_worktree = {
        Path(path).as_posix(): text for path, text in worktree_texts.items()
    }
    normalized_ref = {
        Path(path).as_posix(): text for path, text in (ref_texts or {}).items()
    }
    mock_guard = MagicMock()
    mock_guard.read_text_from_worktree.side_effect = (
        lambda path: normalized_worktree.get(Path(path).as_posix())
    )
    mock_guard.read_text_from_ref.side_effect = (
        lambda path, _ref: normalized_ref.get(Path(path).as_posix())
    )

    stdout = io.StringIO()
    with (
        patch.object(SCRIPT, "guard", mock_guard),
        patch.object(
            SCRIPT,
            "list_changed_paths",
            return_value=[Path(path) for path in changed_paths],
        ),
        patch.object(
            SCRIPT,
            "_build_global_hash_index",
            return_value=global_index or {},
        ),
        patch.object(sys, "argv", ["check_function_duplication.py", "--format", "json"]),
        contextlib.redirect_stdout(stdout),
    ):
        rc = SCRIPT.main()
    return rc, json.loads(stdout.getvalue()), mock_guard


class FunctionDuplicationScriptCase(TestCase):
    script = SCRIPT


class NormalizeBodyTests(FunctionDuplicationScriptCase):
    def test_strips_rust_line_comments(self) -> None:
        result = self.script._normalize_body(
            "let x = 1; // assign x\nlet y = 2; // assign y",
            ".rs",
        )
        self.assertNotIn("//", result)
        self.assertNotIn("assign", result)
        self.assertIn("let x = 1;", result)

    def test_strips_python_line_comments(self) -> None:
        result = self.script._normalize_body("x = 1  # assign x\ny = 2  # assign y", ".py")
        self.assertNotIn("#", result)
        self.assertNotIn("assign", result)
        self.assertIn("x = 1", result)

    def test_collapses_whitespace_and_trims(self) -> None:
        result = self.script._normalize_body("   \n  let   x = 1;\n\n let y = 2;   ", ".rs")
        self.assertEqual(result, "let x = 1; let y = 2;")

    def test_unknown_extension_only_collapses_whitespace(self) -> None:
        result = self.script._normalize_body("let x = 1; // still here\n# also here", ".go")
        self.assertIn("//", result)
        self.assertIn("#", result)


class BodyHashTests(FunctionDuplicationScriptCase):
    def test_identical_normalized_bodies_produce_same_hash(self) -> None:
        hash_a = self.script._body_hash("let x = 1; // comment A\nlet y = 2;", ".rs")
        hash_b = self.script._body_hash("let x = 1; // comment B\nlet y = 2;", ".rs")
        self.assertEqual(hash_a, hash_b)

    def test_different_bodies_produce_different_hashes(self) -> None:
        hash_a = self.script._body_hash("let x = 1;\nlet y = 2;", ".rs")
        hash_b = self.script._body_hash("let x = 100;\nlet y = 200;", ".rs")
        self.assertNotEqual(hash_a, hash_b)

    def test_hash_is_stable_hex_string(self) -> None:
        value = self.script._body_hash("x = 1\ny = 2", ".py")
        self.assertEqual(len(value), 16)
        int(value, 16)


class ExtractFunctionHashesTests(FunctionDuplicationScriptCase):
    def test_extracts_rust_function_hashes(self) -> None:
        source = _rust_function(
            "alpha",
            [
                "let a = 1;",
                "let b = 2;",
                "let c = 3;",
                "let d = 4;",
                "let e = 5;",
                "let f = 6;",
            ],
        )
        results = self.script._extract_function_hashes(source, ".rs")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "alpha")
        self.assertEqual(results[0]["start_line"], 1)

    def test_extracts_python_function_hashes(self) -> None:
        source = _python_function(
            "beta",
            ["a = 1", "b = 2", "c = 3", "d = 4", "e = 5", "f = 6"],
        )
        results = self.script._extract_function_hashes(source, ".py")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "beta")

    def test_skips_short_or_unsupported_functions(self) -> None:
        self.assertEqual(
            self.script._extract_function_hashes(_rust_function("tiny", ["let a = 1;"]), ".rs"),
            [],
        )
        self.assertEqual(self.script._extract_function_hashes("fn main() {}", ".go"), [])
        self.assertEqual(self.script._extract_function_hashes(None, ".rs"), [])

    def test_multiple_functions_are_extracted(self) -> None:
        body = [
            "let a = 1;",
            "let b = 2;",
            "let c = 3;",
            "let d = 4;",
            "let e = 5;",
            "let f = 6;",
        ]
        source = _rust_function("first", body) + "\n\n" + _rust_function("second", body)
        results = self.script._extract_function_hashes(source, ".rs")
        self.assertEqual({row["name"] for row in results}, {"first", "second"})


class RenderMdTests(FunctionDuplicationScriptCase):
    def _make_report(
        self,
        *,
        ok: bool = True,
        violations: list | None = None,
        mode: str = "working-tree",
        since_ref: str | None = None,
        head_ref: str | None = None,
    ) -> dict:
        return {
            "command": "check_function_duplication",
            "timestamp": "2026-03-09T00:00:00Z",
            "mode": mode,
            "since_ref": since_ref,
            "head_ref": head_ref,
            "ok": ok,
            "files_changed": 3,
            "functions_scanned": 12,
            "violations": violations or [],
        }

    def test_clean_report_has_header_and_ok_true(self) -> None:
        md = self.script._render_md(self._make_report(ok=True))
        self.assertIn("# check_function_duplication", md)
        self.assertIn("- ok: True", md)
        self.assertIn("- duplicates_found: 0", md)
        self.assertNotIn("## Violations", md)

    def test_report_with_violations_lists_them(self) -> None:
        md = self.script._render_md(
            self._make_report(
                ok=False,
                violations=[
                    {
                        "path": "rust/src/mod_a.rs",
                        "function_name": "do_thing",
                        "line_count": 15,
                        "start_line": 10,
                        "end_line": 24,
                        "body_hash": "abc123",
                        "matches": [{"path": "rust/src/mod_b.rs", "name": "do_thing_copy"}],
                    }
                ],
            )
        )
        self.assertIn("## Violations", md)
        self.assertIn("`rust/src/mod_a.rs::do_thing`", md)
        self.assertIn("`rust/src/mod_b.rs::do_thing_copy`", md)

    def test_commit_range_mode_includes_refs(self) -> None:
        md = self.script._render_md(
            self._make_report(mode="commit-range", since_ref="abc123", head_ref="HEAD")
        )
        self.assertIn("- since_ref: abc123", md)
        self.assertIn("- head_ref: HEAD", md)


class MainIntegrationTests(FunctionDuplicationScriptCase):
    def test_duplicate_rust_functions_in_changed_files_flagged(self) -> None:
        body_lines = [
            "let a = 1;",
            "let b = 2;",
            "let c = 3;",
            "let d = 4;",
            "let e = 5;",
            "let f = 6;",
        ]
        source_a = _rust_function("shared_helper", body_lines)
        source_b = _rust_function("shared_helper", body_lines)
        rc, payload, _guard = _run_main_json(
            changed_paths=["rust/src/file_a.rs", "rust/src/file_b.rs"],
            worktree_texts={
                "rust/src/file_a.rs": source_a,
                "rust/src/file_b.rs": source_b,
            },
        )

        self.assertEqual(rc, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["files_changed"], 2)
        self.assertEqual(
            {row["path"] for row in payload["violations"]},
            {"rust/src/file_a.rs", "rust/src/file_b.rs"},
        )

    def test_pre_existing_duplicate_is_not_flagged(self) -> None:
        source = _rust_function(
            "existing_helper",
            [
                "let a = 1;",
                "let b = 2;",
                "let c = 3;",
                "let d = 4;",
                "let e = 5;",
                "let f = 6;",
            ],
        )
        rc, payload, _guard = _run_main_json(
            changed_paths=["rust/src/existing.rs"],
            worktree_texts={"rust/src/existing.rs": source},
            ref_texts={"rust/src/existing.rs": source},
            global_index={
                _first_hash(source, ".rs"): [("rust/src/other.rs", "same_body_fn")]
            },
        )

        self.assertEqual(rc, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["violations"], [])

    def test_new_function_matching_global_index_is_flagged(self) -> None:
        source = _rust_function(
            "new_helper",
            [
                "let a = 1;",
                "let b = 2;",
                "let c = 3;",
                "let d = 4;",
                "let e = 5;",
                "let f = 6;",
            ],
        )
        rc, payload, _guard = _run_main_json(
            changed_paths=["rust/src/new_file.rs"],
            worktree_texts={"rust/src/new_file.rs": source},
            global_index={
                _first_hash(source, ".rs"): [("rust/src/old_file.rs", "original_fn")]
            },
        )

        self.assertEqual(rc, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(len(payload["violations"]), 1)
        self.assertEqual(payload["violations"][0]["path"], "rust/src/new_file.rs")
        self.assertEqual(
            payload["violations"][0]["matches"][0]["path"],
            "rust/src/old_file.rs",
        )


class MinBodyLinesTests(FunctionDuplicationScriptCase):
    def test_exact_threshold_is_included(self) -> None:
        results = self.script._extract_function_hashes(
            _rust_function("threshold", ["let a = 1;", "let b = 2;", "let c = 3;", "let d = 4;"]),
            ".rs",
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["line_count"], 6)

    def test_one_below_threshold_is_excluded(self) -> None:
        results = self.script._extract_function_hashes(
            _rust_function("almost", ["let a = 1;", "let b = 2;", "let c = 3;"]),
            ".rs",
        )
        self.assertEqual(results, [])


class BuildParserTests(FunctionDuplicationScriptCase):
    def test_parser_defaults_and_custom_args(self) -> None:
        parser = self.script._build_parser()
        default_args = parser.parse_args([])
        custom_args = parser.parse_args(
            ["--format", "json", "--min-body-lines", "10", "--since-ref", "abc123"]
        )

        self.assertEqual(default_args.format, "md")
        self.assertEqual(default_args.min_body_lines, self.script.MIN_BODY_LINES)
        self.assertEqual(custom_args.format, "json")
        self.assertEqual(custom_args.min_body_lines, 10)
        self.assertEqual(custom_args.since_ref, "abc123")
        self.assertEqual(custom_args.head_ref, "HEAD")


class PythonFunctionDuplicationTests(FunctionDuplicationScriptCase):
    def test_python_comment_stripping_preserves_hash_equality(self) -> None:
        hash_a = self.script._body_hash(
            "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\nf = 6  # comment A",
            ".py",
        )
        hash_b = self.script._body_hash(
            "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\nf = 6  # comment B",
            ".py",
        )
        self.assertEqual(hash_a, hash_b)

    def test_supported_extensions_cover_python_and_rust(self) -> None:
        self.assertIn(".rs", self.script.SUPPORTED_EXTENSIONS)
        self.assertIn(".py", self.script.SUPPORTED_EXTENSIONS)
        self.assertIn(".rs", self.script._SCANNER_BY_EXT)
        self.assertIn(".py", self.script._SCANNER_BY_EXT)
