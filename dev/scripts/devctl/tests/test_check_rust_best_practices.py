"""Unit tests for Rust best-practices guard script metrics."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest import TestCase

from dev.scripts.devctl.config import REPO_ROOT


SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_rust_best_practices.py"


def _load_script_module():
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("check_rust_best_practices_script", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_rust_best_practices.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckRustBestPracticesTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def test_count_metrics_detects_all_tracked_patterns(self) -> None:
        text = """
#[allow(clippy::missing_panics_doc)]
pub unsafe fn raw() {
    unsafe { std::ptr::read_volatile(0 as *const u8); }
    std::mem::forget(String::from("x"));
    mem::forget(String::from("y"));
}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["allow_without_reason"], 1)
        self.assertEqual(metrics["undocumented_unsafe_blocks"], 1)
        self.assertEqual(metrics["pub_unsafe_fn_missing_safety_docs"], 1)
        self.assertEqual(metrics["mem_forget_calls"], 2)

    def test_count_metrics_accepts_documented_unsafe_and_no_forget(self) -> None:
        text = """
/// # Safety
/// Caller must provide a valid pointer.
pub unsafe fn documented() {
    // SAFETY: caller contract guarantees `ptr` points to initialized memory.
    unsafe { std::ptr::read_volatile(0 as *const u8); }
}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["allow_without_reason"], 0)
        self.assertEqual(metrics["undocumented_unsafe_blocks"], 0)
        self.assertEqual(metrics["pub_unsafe_fn_missing_safety_docs"], 0)
        self.assertEqual(metrics["mem_forget_calls"], 0)
