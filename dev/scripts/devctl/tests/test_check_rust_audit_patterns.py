"""Unit tests for Rust audit-pattern guard script metrics."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest import TestCase

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_rust_audit_patterns.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("check_rust_audit_patterns_script", SCRIPT_PATH)
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
        self.assertFalse(self.script._has_positive_metrics({name: 0 for name in self.script.PATTERNS}))
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
