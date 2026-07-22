//! Regression tests for runtime logging and performance metrics.

use super::{init_logging, log_debug, log_debug_content, set_logging_for_tests};
use crate::config::AppConfig;
use crate::voice;
use crate::{audio, crash_log_path, log_file_path};
use clap::Parser;
use std::env;
use std::sync::{Mutex, OnceLock};

static LOG_TEST_LOCK: OnceLock<Mutex<()>> = OnceLock::new();

fn with_logging_enabled(action: impl FnOnce()) {
    let _guard = LOG_TEST_LOCK
        .get_or_init(|| Mutex::new(()))
        .lock()
        .unwrap_or_else(std::sync::PoisonError::into_inner);
    let inherited_path = env::var_os("VOICETERM_LOG_PATH")
        .map(std::path::PathBuf::from)
        .filter(|path| !path.as_os_str().is_empty());
    clear_log_env();
    let isolated_path = inherited_path
        .clone()
        .unwrap_or_else(|| isolated_log_path("enabled"));
    env::set_var("VOICETERM_LOG_PATH", &isolated_path);
    let log_path = log_file_path();
    let _ = std::fs::remove_file(&log_path);
    set_logging_for_tests(true, false);
    action();
    set_logging_for_tests(false, false);
    if inherited_path.is_none() {
        let _ = std::fs::remove_file(&isolated_path);
    }
    clear_log_env();
    if let Some(path) = inherited_path {
        env::set_var("VOICETERM_LOG_PATH", path);
    }
}

fn with_log_lock(action: impl FnOnce()) {
    let _guard = LOG_TEST_LOCK
        .get_or_init(|| Mutex::new(()))
        .lock()
        .unwrap_or_else(std::sync::PoisonError::into_inner);
    action();
}

fn isolated_log_path(label: &str) -> std::path::PathBuf {
    env::temp_dir().join(format!(
        "voiceterm_test_{}_{}_tui.log",
        std::process::id(),
        label
    ))
}

fn clear_log_env() {
    env::remove_var("VOICETERM_LOGS");
    env::remove_var("VOICETERM_NO_LOGS");
    env::remove_var("VOICETERM_LOG_CONTENT");
    env::remove_var("VOICETERM_LOG_PATH");
    env::remove_var("VOICETERM_CRASH_LOG_PATH");
}

#[test]
fn perf_smoke_emits_voice_metrics() {
    with_logging_enabled(|| {
        let log_path = log_file_path();
        let metrics = audio::CaptureMetrics {
            capture_ms: 800,
            transcribe_ms: 0,
            speech_ms: 600,
            silence_tail_ms: 200,
            frames_processed: 5,
            frames_dropped: 0,
            early_stop_reason: audio::StopReason::VadSilence { tail_ms: 200 },
        };
        voice::log_voice_metrics(&metrics);
        let contents =
            std::fs::read_to_string(&log_path).expect("perf smoke log file should exist");
        assert!(contents.contains("voice_metrics|"));
    });
}

#[test]
fn logging_disabled_by_default() {
    with_log_lock(|| {
        clear_log_env();
        let isolated_path = isolated_log_path("disabled");
        env::set_var("VOICETERM_LOG_PATH", &isolated_path);
        let log_path = log_file_path();
        let _ = std::fs::remove_file(&log_path);
        let config = AppConfig::parse_from(["voiceterm-tests"]);
        init_logging(&config);
        log_debug("should-not-write");
        assert!(std::fs::metadata(&log_path).is_err());
        clear_log_env();
    });
}

#[test]
fn logging_enabled_writes_log() {
    with_log_lock(|| {
        clear_log_env();
        let isolated_path = isolated_log_path("enabled_write");
        env::set_var("VOICETERM_LOG_PATH", &isolated_path);
        let log_path = log_file_path();
        let _ = std::fs::remove_file(&log_path);
        let mut config = AppConfig::parse_from(["voiceterm-tests"]);
        config.logs = true;
        init_logging(&config);
        log_debug("log-enabled");
        let contents = std::fs::read_to_string(&log_path).expect("log file should be created");
        assert!(contents.contains("log-enabled"));
        set_logging_for_tests(false, false);
        let _ = std::fs::remove_file(&isolated_path);
        clear_log_env();
    });
}

#[test]
fn log_content_requires_flag() {
    with_log_lock(|| {
        clear_log_env();
        let isolated_path = isolated_log_path("content_disabled");
        env::set_var("VOICETERM_LOG_PATH", &isolated_path);
        let log_path = log_file_path();
        let _ = std::fs::remove_file(&log_path);
        let mut config = AppConfig::parse_from(["voiceterm-tests"]);
        config.logs = true;
        config.log_content = false;
        init_logging(&config);
        log_debug_content("secret");
        let contents = std::fs::read_to_string(&log_path).unwrap_or_default();
        assert!(!contents.contains("secret"));
        set_logging_for_tests(false, false);
        let _ = std::fs::remove_file(&isolated_path);
        clear_log_env();
    });
}

#[test]
fn log_file_path_honors_env_override() {
    with_log_lock(|| {
        clear_log_env();
        let override_path = env::temp_dir().join("voiceterm_tui_override.log");
        env::set_var("VOICETERM_LOG_PATH", &override_path);
        assert_eq!(log_file_path(), override_path);
        env::remove_var("VOICETERM_LOG_PATH");
    });
}

#[test]
fn crash_log_path_honors_env_override() {
    with_log_lock(|| {
        clear_log_env();
        let override_path = env::temp_dir().join("voiceterm_crash_override.log");
        env::set_var("VOICETERM_CRASH_LOG_PATH", &override_path);
        assert_eq!(crash_log_path(), override_path);
        env::remove_var("VOICETERM_CRASH_LOG_PATH");
    });
}
