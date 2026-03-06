"""Unit tests for clippy high-signal baseline guard."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_clippy_high_signal.py"


def _load_script_module():
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("check_clippy_high_signal_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_clippy_high_signal.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckClippyHighSignalTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def test_load_baseline_requires_lints_map(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_path = Path(temp_dir) / "baseline.json"
            baseline_path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                self.script._load_baseline(baseline_path)

    def test_main_fails_when_observed_exceeds_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_path = Path(temp_dir) / "baseline.json"
            input_path = Path(temp_dir) / "lints.json"
            baseline_path.write_text(
                json.dumps({"schema_version": 1, "lints": {"clippy::panic": 0}}),
                encoding="utf-8",
            )
            input_path.write_text(
                json.dumps({"schema_version": 1, "lints": {"clippy::panic": 1}}),
                encoding="utf-8",
            )
            argv = [
                "check_clippy_high_signal.py",
                "--input-lints-json",
                str(input_path),
                "--baseline-file",
                str(baseline_path),
                "--format",
                "json",
            ]
            with patch.object(sys, "argv", argv):
                rc = self.script.main()
        self.assertEqual(rc, 1)

    def test_main_passes_when_observed_is_within_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_path = Path(temp_dir) / "baseline.json"
            input_path = Path(temp_dir) / "lints.json"
            baseline_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "lints": {
                            "clippy::panic": 0,
                            "clippy::unwrap_used": 1,
                        },
                    }
                ),
                encoding="utf-8",
            )
            input_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "lints": {
                            "clippy::unwrap_used": 1,
                        },
                    }
                ),
                encoding="utf-8",
            )
            argv = [
                "check_clippy_high_signal.py",
                "--input-lints-json",
                str(input_path),
                "--baseline-file",
                str(baseline_path),
                "--format",
                "md",
            ]
            with patch.object(sys, "argv", argv):
                rc = self.script.main()
        self.assertEqual(rc, 0)
