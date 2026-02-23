"""Unit tests for Rust security-footguns guard script metrics."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest import TestCase

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_rust_security_footguns.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("check_rust_security_footguns_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_rust_security_footguns.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckRustSecurityFootgunsTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def test_count_metrics_detects_footguns(self) -> None:
        text = """
use sha1::Digest;
use std::process::Command;

fn demo() {
    todo!("ship later");
    unimplemented!("not ready");
    dbg!("debug");
    let _ = Command::new("sh").arg("-c").arg("echo hi");
    let mode = 0o777;
}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["todo_macro_calls"], 1)
        self.assertEqual(metrics["unimplemented_macro_calls"], 1)
        self.assertEqual(metrics["dbg_macro_calls"], 1)
        self.assertEqual(metrics["shell_spawn_calls"], 1)
        self.assertEqual(metrics["shell_control_flag_calls"], 1)
        self.assertEqual(metrics["permissive_mode_literals"], 1)
        self.assertEqual(metrics["weak_crypto_refs"], 1)

    def test_has_positive_growth_only_for_positive_values(self) -> None:
        self.assertFalse(
            self.script._has_positive_growth(
                {
                    "todo_macro_calls": 0,
                    "unimplemented_macro_calls": 0,
                    "dbg_macro_calls": 0,
                    "shell_spawn_calls": 0,
                    "shell_control_flag_calls": 0,
                    "permissive_mode_literals": 0,
                    "weak_crypto_refs": 0,
                }
            )
        )
        self.assertTrue(
            self.script._has_positive_growth(
                {
                    "todo_macro_calls": 0,
                    "unimplemented_macro_calls": 0,
                    "dbg_macro_calls": 0,
                    "shell_spawn_calls": 1,
                    "shell_control_flag_calls": 0,
                    "permissive_mode_literals": 0,
                    "weak_crypto_refs": 0,
                }
            )
        )
