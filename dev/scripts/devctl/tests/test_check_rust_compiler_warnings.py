from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.tests.conftest import load_repo_module, override_module_attrs


class CheckRustCompilerWarningsTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_repo_module(
            "check_rust_compiler_warnings_script",
            "dev/scripts/checks/check_rust_compiler_warnings.py",
        )

    def test_normalize_warning_path_handles_relative_and_absolute_inputs(self) -> None:
        relative = self.script._normalize_warning_path("src/lib.rs", Path("rust"))
        absolute = self.script._normalize_warning_path(
            str(self.script.REPO_ROOT / "rust" / "src" / "lib.rs"),
            Path("rust"),
        )
        self.assertEqual(relative, "rust/src/lib.rs")
        self.assertEqual(absolute, "rust/src/lib.rs")

    def test_collect_warning_records_filters_to_target_paths(self) -> None:
        lines = [
            json.dumps(
                {
                    "reason": "compiler-message",
                    "message": {
                        "level": "warning",
                        "message": "unused import: `x`",
                        "code": {"code": "unused_imports"},
                        "spans": [
                            {
                                "file_name": "src/lib.rs",
                                "line_start": 7,
                                "is_primary": True,
                            }
                        ],
                    },
                }
            ),
            json.dumps(
                {
                    "reason": "compiler-message",
                    "message": {
                        "level": "warning",
                        "message": "unused import: `y`",
                        "code": {"code": "unused_imports"},
                        "spans": [
                            {
                                "file_name": "src/other.rs",
                                "line_start": 3,
                                "is_primary": True,
                            }
                        ],
                    },
                }
            ),
        ]
        warnings = self.script.collect_warning_records(
            lines,
            working_directory=Path("rust"),
            target_paths={"rust/src/lib.rs"},
        )
        self.assertEqual(
            warnings,
            [
                {
                    "path": "rust/src/lib.rs",
                    "line": 7,
                    "code": "unused_imports",
                    "message": "unused import: `x`",
                }
            ],
        )

    def test_main_fails_when_changed_file_has_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "warnings.jsonl"
            input_path.write_text(
                json.dumps(
                    {
                        "reason": "compiler-message",
                        "message": {
                            "level": "warning",
                            "message": "unused import: `x`",
                            "code": {"code": "unused_imports"},
                            "spans": [
                                {
                                    "file_name": "src/lib.rs",
                                    "line_start": 12,
                                    "is_primary": True,
                                }
                            ],
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            override_module_attrs(
                self,
                self.script,
                list_changed_paths_with_base_map=lambda *_args: (
                    [Path("rust/src/lib.rs")],
                    {Path("rust/src/lib.rs"): Path("rust/src/lib.rs")},
                ),
            )
            argv = [
                "check_rust_compiler_warnings.py",
                "--input-jsonl",
                str(input_path),
                "--format",
                "json",
            ]
            with patch.object(sys, "argv", argv):
                rc = self.script.main()
        self.assertEqual(rc, 1)

    def test_main_passes_when_warning_only_touches_unchanged_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "warnings.jsonl"
            input_path.write_text(
                json.dumps(
                    {
                        "reason": "compiler-message",
                        "message": {
                            "level": "warning",
                            "message": "unused import: `x`",
                            "code": {"code": "unused_imports"},
                            "spans": [
                                {
                                    "file_name": "src/other.rs",
                                    "line_start": 12,
                                    "is_primary": True,
                                }
                            ],
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            override_module_attrs(
                self,
                self.script,
                list_changed_paths_with_base_map=lambda *_args: (
                    [Path("rust/src/lib.rs")],
                    {Path("rust/src/lib.rs"): Path("rust/src/lib.rs")},
                ),
            )
            argv = [
                "check_rust_compiler_warnings.py",
                "--input-jsonl",
                str(input_path),
                "--format",
                "md",
            ]
            with patch.object(sys, "argv", argv):
                rc = self.script.main()
        self.assertEqual(rc, 0)

    def test_main_skips_cargo_when_no_rust_targets_are_changed(self) -> None:
        override_module_attrs(
            self,
            self.script,
            list_changed_paths_with_base_map=lambda *_args: ([Path("README.md")], {}),
            run_cargo_warning_scan=lambda *_args: self.fail("cargo scan should not run"),
        )
        argv = ["check_rust_compiler_warnings.py", "--format", "json"]
        with patch.object(sys, "argv", argv):
            rc = self.script.main()
        self.assertEqual(rc, 0)
