"""Unit tests for Rust security-footguns guard script metrics."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest import TestCase

from dev.scripts.devctl.config import REPO_ROOT

SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_rust_security_footguns.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "check_rust_security_footguns_script", SCRIPT_PATH
    )
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
    let current_pid = unsafe { libc::getpid() } as i32;
    let written = unsafe { libc::write(0, std::ptr::null(), 0) };
    let _len = written as usize;
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
        self.assertEqual(metrics["pid_signed_wrap_casts"], 1)
        self.assertEqual(metrics["sign_unsafe_syscall_casts"], 1)

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
                    "pid_signed_wrap_casts": 0,
                    "sign_unsafe_syscall_casts": 0,
                }
            )
        )

    def test_count_metrics_ignores_cfg_test_blocks(self) -> None:
        text = """
#[cfg(test)]
mod tests {
    fn helper() {
        todo!("test only");
        dbg!("debug");
    }
}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["todo_macro_calls"], 0)
        self.assertEqual(metrics["dbg_macro_calls"], 0)
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
                    "pid_signed_wrap_casts": 0,
                    "sign_unsafe_syscall_casts": 0,
                }
            )
        )

    def test_pid_signed_wrap_casts_detect_child_and_getpid_variants(self) -> None:
        text = """
use libc;

fn pids(child: &std::process::Child) {
    let child_pid = child.id() as i32;
    let current = unsafe { libc::getpid() } as i32;
    let inline = unsafe { libc::getpid() as i32 };
}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["pid_signed_wrap_casts"], 3)

    def test_pid_signed_wrap_casts_ignore_checked_conversion(self) -> None:
        text = """
fn checked(child: &std::process::Child) -> i32 {
    i32::try_from(child.id()).unwrap_or(i32::MAX)
}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["pid_signed_wrap_casts"], 0)

    def test_sign_unsafe_syscall_casts_ignores_guarded_write_results(self) -> None:
        text = """
use libc;

fn guarded(fd: libc::c_int, data: &[u8]) -> usize {
    let written = unsafe { libc::write(fd, data.as_ptr() as *const libc::c_void, data.len()) };
    if written < 0 {
        return 0;
    }
    if written == 0 {
        return 0;
    }
    written as usize
}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["sign_unsafe_syscall_casts"], 0)

    def test_sign_unsafe_syscall_casts_detects_unguarded_read_result(self) -> None:
        text = """
use libc;

fn unguarded(fd: libc::c_int, buffer: &mut [u8]) -> usize {
    let read_len = unsafe { libc::read(fd, buffer.as_mut_ptr() as *mut libc::c_void, buffer.len()) };
    read_len as usize
}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["sign_unsafe_syscall_casts"], 1)
