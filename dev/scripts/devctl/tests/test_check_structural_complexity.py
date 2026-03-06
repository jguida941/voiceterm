"""Unit tests for structural-complexity guard."""

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


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_structural_complexity.py"


def _load_script_module():
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("check_structural_complexity_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_structural_complexity.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _high_complexity_fn(name: str) -> str:
    lines = [f"fn {name}() {{", "    let mut x = 0;"]
    for i in range(120):
        lines.append(f"    if x == {i} {{ x += 1; }}")
    lines.append("    if x > 0 { x += 1; }")
    lines.append("}")
    return "\n".join(lines) + "\n"


class CheckStructuralComplexityTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def _run(
        self,
        source_root: Path,
        *argv: str,
        changed_paths: list[Path] | None = None,
        exceptions: dict | None = None,
    ) -> tuple[int, dict]:
        changed_paths = changed_paths if changed_paths is not None else []
        exceptions = (
            exceptions
            if exceptions is not None
            else self.script.FUNCTION_COMPLEXITY_EXCEPTIONS
        )
        out = io.StringIO()
        with patch.object(self.script, "SOURCE_ROOT", source_root), patch.object(
            self.script, "FUNCTION_COMPLEXITY_EXCEPTIONS", exceptions
        ), patch.object(
            self.script, "list_changed_paths_with_base_map", return_value=(changed_paths, {})
        ), patch.object(self.script, "_validate_ref", return_value=None), patch.object(
            sys, "argv", ["check_structural_complexity.py", "--format", "json", *argv]
        ):
            with redirect_stdout(out):
                exit_code = self.script.main()
        return exit_code, json.loads(out.getvalue())

    def test_simple_function_passes(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            source_root = Path(temp_dir) / "rust/src"
            _write(source_root / "lib.rs", "fn ok() { let _x = 1; }\n")
            exit_code, report = self._run(source_root)

        self.assertEqual(exit_code, 0)
        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_high_complexity_function_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            source_root = Path(temp_dir) / "rust/src"
            _write(source_root / "lib.rs", _high_complexity_fn("too_complex"))
            exit_code, report = self._run(source_root)

        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(len(report["violations"]), 1)
        self.assertEqual(report["violations"][0]["function_name"], "too_complex")

    def test_exception_allows_known_hotspot(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            source_root = Path(temp_dir) / "rust/src"
            dispatch_path = source_root / "bin/voiceterm/writer/state/dispatch.rs"
            _write(dispatch_path, _high_complexity_fn("dispatch_message"))
            key = f"{self.script._path_for_report(dispatch_path)}::dispatch_message"
            exceptions = {
                key: self.script.ComplexityException(
                    max_score=140,
                    max_branch_points=130,
                    max_nesting_depth=10,
                    owner="test",
                    expires_on="2099-01-01",
                    follow_up_mp="MP-test",
                    reason="test exception",
                )
            }
            exit_code, report = self._run(source_root, exceptions=exceptions)

        self.assertEqual(exit_code, 0)
        self.assertTrue(report["ok"])
        self.assertGreaterEqual(report["exceptions_used"], 1)

    def test_expired_exception_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            source_root = Path(temp_dir) / "rust/src"
            dispatch_path = source_root / "bin/voiceterm/writer/state/dispatch.rs"
            _write(dispatch_path, _high_complexity_fn("dispatch_message"))
            key = f"{self.script._path_for_report(dispatch_path)}::dispatch_message"
            exceptions = {
                key: self.script.ComplexityException(
                    max_score=999,
                    max_branch_points=999,
                    max_nesting_depth=99,
                    owner="test",
                    expires_on="2000-01-01",
                    follow_up_mp="MP-test",
                    reason="expired",
                )
            }
            exit_code, report = self._run(source_root, exceptions=exceptions)

        self.assertEqual(exit_code, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["violations"][0]["reason"], "exception_expired")


if __name__ == "__main__":
    import unittest

    unittest.main()
