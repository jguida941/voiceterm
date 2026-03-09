"""Unit tests for Rust best-practices guard script metrics."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest import TestCase

from dev.scripts.devctl.config import REPO_ROOT

SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_rust_best_practices.py"


def _load_script_module():
    script_dir = str(SCRIPT_PATH.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(
        "check_rust_best_practices_script", SCRIPT_PATH
    )
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
    let _ = tx.send("ignored");
    _ = tx.try_send("ignored again");
    let _ = sender.emit("ignored third");
    thread::spawn(move || {
        do_work();
    });
    worker.join().unwrap();
    rx.recv().unwrap();
    rx.recv_timeout(timeout).expect("recv timeout");
    env::set_var("VOICETERM_X", "1");
    std::env::remove_var("VOICETERM_X");
    let _file = std::fs::OpenOptions::new().create(true).write(true).open(path);
    if centered == 0.0 {
        return;
    }
}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["allow_without_reason"], 1)
        self.assertEqual(metrics["undocumented_unsafe_blocks"], 1)
        self.assertEqual(metrics["pub_unsafe_fn_missing_safety_docs"], 1)
        self.assertEqual(metrics["unsafe_impl_missing_safety_comment"], 0)
        self.assertEqual(metrics["mem_forget_calls"], 2)
        self.assertEqual(metrics["unwrap_on_join_recv"], 2)
        self.assertEqual(metrics["expect_on_join_recv"], 1)
        self.assertEqual(metrics["dropped_send_results"], 2)
        self.assertEqual(metrics["dropped_emit_results"], 1)
        self.assertEqual(metrics["detached_thread_spawns"], 1)
        self.assertEqual(metrics["env_mutation_calls"], 2)
        self.assertEqual(metrics["suspicious_open_options"], 1)
        self.assertEqual(metrics["float_literal_comparisons"], 1)
        self.assertEqual(metrics["nonatomic_persistent_toml_writes"], 0)
        self.assertEqual(metrics["custom_persistent_toml_parsers"], 0)

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
        self.assertEqual(metrics["unsafe_impl_missing_safety_comment"], 0)
        self.assertEqual(metrics["mem_forget_calls"], 0)
        self.assertEqual(metrics["unwrap_on_join_recv"], 0)
        self.assertEqual(metrics["expect_on_join_recv"], 0)
        self.assertEqual(metrics["dropped_send_results"], 0)
        self.assertEqual(metrics["dropped_emit_results"], 0)
        self.assertEqual(metrics["detached_thread_spawns"], 0)
        self.assertEqual(metrics["env_mutation_calls"], 0)
        self.assertEqual(metrics["suspicious_open_options"], 0)
        self.assertEqual(metrics["float_literal_comparisons"], 0)
        self.assertEqual(metrics["nonatomic_persistent_toml_writes"], 0)
        self.assertEqual(metrics["custom_persistent_toml_parsers"], 0)

    def test_count_metrics_tracks_unsafe_impl_missing_safety_comment(self) -> None:
        text = """
unsafe impl Send for Demo {}
// SAFETY: Demo does not share mutable state across threads.
unsafe impl Sync for Demo {}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["unsafe_impl_missing_safety_comment"], 1)

    def test_count_metrics_ignores_cfg_test_blocks(self) -> None:
        text = """
#[cfg(test)]
mod tests {
    #[allow(clippy::missing_panics_doc)]
    pub unsafe fn test_only() {
        unsafe { std::ptr::read_volatile(0 as *const u8); }
        std::mem::forget(String::from("x"));
        let _ = tx.send("ignored");
        worker.join().unwrap();
        rx.recv().expect("test-only");
        env::set_var("VOICETERM_TEST", "1");
    }
}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["allow_without_reason"], 0)
        self.assertEqual(metrics["undocumented_unsafe_blocks"], 0)
        self.assertEqual(metrics["pub_unsafe_fn_missing_safety_docs"], 0)
        self.assertEqual(metrics["unsafe_impl_missing_safety_comment"], 0)
        self.assertEqual(metrics["mem_forget_calls"], 0)
        self.assertEqual(metrics["unwrap_on_join_recv"], 0)
        self.assertEqual(metrics["expect_on_join_recv"], 0)
        self.assertEqual(metrics["dropped_send_results"], 0)
        self.assertEqual(metrics["dropped_emit_results"], 0)
        self.assertEqual(metrics["detached_thread_spawns"], 0)
        self.assertEqual(metrics["env_mutation_calls"], 0)
        self.assertEqual(metrics["suspicious_open_options"], 0)
        self.assertEqual(metrics["float_literal_comparisons"], 0)
        self.assertEqual(metrics["dropped_emit_results"], 0)
        self.assertEqual(metrics["nonatomic_persistent_toml_writes"], 0)
        self.assertEqual(metrics["custom_persistent_toml_parsers"], 0)

    def test_count_metrics_ignores_explicit_open_options_write_modes(self) -> None:
        text = """
fn open_explicit(path: &std::path::Path) {
    let _append = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path);
    let _rewrite = std::fs::OpenOptions::new()
        .create(true)
        .write(true)
        .truncate(true)
        .open(path);
    let _preserve = std::fs::OpenOptions::new()
        .create(true)
        .write(true)
        .truncate(false)
        .open(path);
    let _new = std::fs::OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path);
}
        """
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["suspicious_open_options"], 0)
        self.assertEqual(metrics["float_literal_comparisons"], 0)
        self.assertEqual(metrics["nonatomic_persistent_toml_writes"], 0)
        self.assertEqual(metrics["custom_persistent_toml_parsers"], 0)

    def test_count_metrics_ignores_float_literal_comparisons_in_comments(self) -> None:
        text = """
fn describe(centered: f32) {
    // centered == 0.0 is the degenerate branch
    let _label = "value != 0.0";
    if centered != 0.5_f32 {
        log::debug!("runtime branch");
    }
}
        """
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["float_literal_comparisons"], 1)
        self.assertEqual(metrics["detached_thread_spawns"], 0)
        self.assertEqual(metrics["nonatomic_persistent_toml_writes"], 0)
        self.assertEqual(metrics["custom_persistent_toml_parsers"], 0)

    def test_count_metrics_tracks_nonatomic_persistent_toml_writes(self) -> None:
        text = """
const CONFIG_FILE: &str = "config.toml";

fn save_user_config(path: &std::path::Path, body: &str) {
    std::fs::write(&path, body).expect("write config");
    let _file = std::fs::File::create(&path).expect("create config");
    let _handle = std::fs::OpenOptions::new()
        .write(true)
        .truncate(true)
        .open(&path)
        .expect("open config");
}
"""
        metrics = self.script._count_metrics(
            text,
            path=Path("rust/src/bin/voiceterm/persistent_config.rs"),
        )
        self.assertEqual(metrics["nonatomic_persistent_toml_writes"], 3)
        self.assertEqual(metrics["custom_persistent_toml_parsers"], 0)

    def test_count_metrics_ignores_tempfile_swap_for_persistent_toml_writes(self) -> None:
        text = """
const CONFIG_FILE: &str = "config.toml";

fn save_user_config(path: &std::path::Path, body: &str) {
    let temp_path = path.with_extension("tmp");
    std::fs::write(&temp_path, body).expect("write temp config");
    let _file = std::fs::File::create(&temp_path).expect("create temp config");
    let _handle = std::fs::OpenOptions::new()
        .write(true)
        .truncate(true)
        .open(&temp_path)
        .expect("open temp config");
    std::fs::rename(&temp_path, &path).expect("swap config");
}
"""
        metrics = self.script._count_metrics(
            text,
            path=Path("rust/src/bin/voiceterm/persistent_config.rs"),
        )
        self.assertEqual(metrics["nonatomic_persistent_toml_writes"], 0)

    def test_count_metrics_tracks_custom_persistent_toml_parsers(self) -> None:
        text = """
const CONFIG_FILE: &str = "config.toml";

fn parse_toml_value(line: &str) -> Option<(&str, &str)> {
    let line = line.trim();
    let (key, rest) = line.split_once('=')?;
    Some((key.trim(), rest.trim().trim_matches('"')))
}

fn parse_user_config(contents: &str) {
    for line in contents.lines() {
        let _ = parse_toml_value(line);
    }
}
"""
        metrics = self.script._count_metrics(
            text,
            path=Path("rust/src/bin/voiceterm/persistent_config.rs"),
        )
        self.assertEqual(metrics["custom_persistent_toml_parsers"], 2)

    def test_count_metrics_ignores_toml_crate_backed_parsers(self) -> None:
        text = """
fn parse_user_config(contents: &str) -> Result<Config, toml::de::Error> {
    toml::from_str(contents)
}
"""
        metrics = self.script._count_metrics(
            text,
            path=Path("rust/src/bin/voiceterm/persistent_config.rs"),
        )
        self.assertEqual(metrics["custom_persistent_toml_parsers"], 0)

    def test_count_metrics_ignores_allowed_or_returned_thread_spawns(self) -> None:
        text = """
fn keep_handle() -> std::thread::JoinHandle<()> {
    thread::spawn(move || {
        do_work();
    })
}

fn detached_but_documented() {
    // detached-thread: allow reason=background reader owns the stream until EOF.
    thread::spawn(move || {
        do_more_work();
    });
}
"""
        metrics = self.script._count_metrics(text)
        self.assertEqual(metrics["detached_thread_spawns"], 0)

    def test_build_parser_accepts_absolute_mode(self) -> None:
        parser = self.script._build_parser()
        args = parser.parse_args(["--absolute"])
        self.assertTrue(args.absolute)
        self.assertEqual(args.format, "md")
