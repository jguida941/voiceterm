"""Unit tests for duplicate Rust type-name guard."""

from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import sys
import tempfile
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_duplicate_types.py"


def _load_script_module():
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("check_duplicate_types_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_duplicate_types.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class CheckDuplicateTypesTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def _run(
        self,
        source_root: Path,
        *argv: str,
        changed_paths: list[Path] | None = None,
        allowlist: dict[str, set[str]] | None = None,
    ) -> tuple[int, dict]:
        changed_paths = changed_paths if changed_paths is not None else []
        allowlist = allowlist if allowlist is not None else self.script.ALLOWLIST_DUPLICATES
        out = io.StringIO()
        with patch.object(self.script, "SOURCE_ROOT", source_root), patch.object(
            self.script, "ALLOWLIST_DUPLICATES", allowlist
        ), patch.object(
            self.script, "list_changed_paths_with_base_map", return_value=(changed_paths, {})
        ), patch.object(self.script, "_validate_ref", return_value=None), patch.object(
            sys, "argv", ["check_duplicate_types.py", "--format", "json", *argv]
        ):
            with redirect_stdout(out):
                exit_code = self.script.main()
        return exit_code, json.loads(out.getvalue())

    def test_allowlisted_duplicates_pass(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            source_root = Path(temp_dir) / "rust/src"
            p1 = source_root / "bin/latency_measurement.rs"
            p2 = source_root / "bin/stt_file_benchmark.rs"
            p3 = source_root / "bin/voice_benchmark.rs"
            _write(p1, "struct Args { value: usize }\n")
            _write(p2, "struct Args { value: usize }\n")
            _write(p3, "struct Args { value: usize }\n")
            _write(source_root / "lib.rs", "pub struct UniqueType;\n")
            allowlist = {
                "Args": {
                    self.script._path_for_report(p1),
                    self.script._path_for_report(p2),
                    self.script._path_for_report(p3),
                }
            }
            exit_code, report = self._run(source_root, allowlist=allowlist)

        self.assertEqual(exit_code, 0)
        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])
        self.assertGreaterEqual(report["allowlist_entries_used"], 1)

    def test_unallowlisted_duplicate_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            source_root = Path(temp_dir) / "rust/src"
            _write(source_root / "bin/a.rs", "pub struct ProviderState;\n")
            _write(source_root / "bin/b.rs", "pub enum ProviderState { Active }\n")
            exit_code, report = self._run(source_root)

        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(len(report["violations"]), 1)
        self.assertEqual(report["violations"][0]["type_name"], "ProviderState")

    def test_commit_range_filters_to_changed_duplicate_groups(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            source_root = Path(temp_dir) / "rust/src"
            _write(source_root / "bin/a.rs", "pub struct DuplicateName;\n")
            _write(source_root / "bin/b.rs", "pub enum DuplicateName { One }\n")
            _write(source_root / "bin/other.rs", "pub struct OtherName;\n")
            exit_code, report = self._run(
                source_root,
                "--since-ref",
                "origin/develop",
                "--head-ref",
                "HEAD",
                changed_paths=[Path("rust/src/bin/other.rs")],
            )

        self.assertEqual(exit_code, 0)
        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])


if __name__ == "__main__":
    import unittest

    unittest.main()
