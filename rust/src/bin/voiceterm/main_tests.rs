use super::*;
use crate::test_env::with_terminal_host_env_overrides;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

fn with_jetbrains_env<T>(overrides: &[(&str, Option<&str>)], f: impl FnOnce() -> T) -> T {
    with_terminal_host_env_overrides(overrides, f)
}

#[test]
fn jetbrains_meter_floor_applies_only_in_jetbrains() {
    assert_eq!(
        apply_jetbrains_meter_floor(80, true),
        JETBRAINS_METER_UPDATE_MS
    );
    assert_eq!(
        apply_jetbrains_meter_floor(160, true),
        160,
        "higher explicit intervals should be preserved"
    );
    assert_eq!(apply_jetbrains_meter_floor(80, false), 80);
}

#[test]
fn startup_guard_enabled_only_for_claude_on_jetbrains() {
    with_jetbrains_env(&[("PYCHARM_HOSTED", Some("1"))], || {
        assert!(runtime_compat::should_enable_claude_startup_guard("claude"));
        assert!(runtime_compat::should_enable_claude_startup_guard(
            "Claude Code"
        ));
        assert!(!runtime_compat::should_enable_claude_startup_guard("codex"));
    });
    with_jetbrains_env(&[], || {
        assert!(!runtime_compat::should_enable_claude_startup_guard(
            "claude"
        ));
    });
}

#[test]
fn validate_dev_mode_flags_rejects_unguarded_dev_logging_flags() {
    let dev_log_only = OverlayConfig::parse_from(["test-app", "--dev-log"]);
    assert!(validate_dev_mode_flags(&dev_log_only).is_err());

    let dev_path_only = OverlayConfig::parse_from(["test-app", "--dev-path", "/tmp/dev"]);
    assert!(validate_dev_mode_flags(&dev_path_only).is_err());
}

#[test]
fn validate_dev_mode_flags_requires_dev_log_when_dev_path_is_set() {
    let missing_log = OverlayConfig::parse_from(["test-app", "--dev", "--dev-path", "/tmp/dev"]);
    assert!(validate_dev_mode_flags(&missing_log).is_err());
}

#[test]
fn validate_dev_mode_flags_accepts_dev_log_combo() {
    let guarded =
        OverlayConfig::parse_from(["test-app", "--dev", "--dev-log", "--dev-path", "/tmp/dev"]);
    assert!(validate_dev_mode_flags(&guarded).is_ok());
    assert_eq!(
        resolve_dev_root_path(&guarded, "/tmp/work"),
        PathBuf::from("/tmp/dev")
    );
}

#[test]
fn is_jetbrains_terminal_detects_and_rejects_expected_env_values() {
    with_jetbrains_env(&[], || {
        assert!(!runtime_compat::is_jetbrains_terminal());
    });

    with_jetbrains_env(&[("PYCHARM_HOSTED", Some("1"))], || {
        assert!(runtime_compat::is_jetbrains_terminal());
    });

    with_jetbrains_env(&[("TERM_PROGRAM", Some("JetBrains-JediTerm"))], || {
        assert!(runtime_compat::is_jetbrains_terminal());
    });

    with_jetbrains_env(&[("PYCHARM_HOSTED", Some(""))], || {
        assert!(
            !runtime_compat::is_jetbrains_terminal(),
            "empty hint values should not be treated as JetBrains terminals"
        );
    });
}

#[test]
fn resolved_meter_update_ms_respects_jetbrains_detection_and_registry_baseline() {
    let empty_registry = HudRegistry::new();

    with_jetbrains_env(&[], || {
        assert_eq!(resolved_meter_update_ms(&empty_registry), METER_UPDATE_MS);
    });

    with_jetbrains_env(&[("JETBRAINS_IDE", Some("1"))], || {
        assert_eq!(
            resolved_meter_update_ms(&empty_registry),
            JETBRAINS_METER_UPDATE_MS
        );
    });
}

#[test]
fn join_thread_with_timeout_waits_for_worker_to_finish_within_budget() {
    let done = Arc::new(AtomicBool::new(false));
    let done_ref = Arc::clone(&done);
    let handle = std::thread::spawn(move || {
        std::thread::sleep(Duration::from_millis(20));
        done_ref.store(true, Ordering::SeqCst);
    });

    join_thread_with_timeout("test-worker", handle, Duration::from_millis(250));
    assert!(done.load(Ordering::SeqCst));
}

#[test]
fn join_thread_with_timeout_returns_quickly_when_thread_already_finished() {
    let handle = std::thread::spawn(|| {});
    std::thread::sleep(Duration::from_millis(10));

    let start = Instant::now();
    join_thread_with_timeout(
        "already-finished-worker",
        handle,
        Duration::from_millis(300),
    );
    let elapsed = start.elapsed();

    assert!(
        elapsed < Duration::from_millis(100),
        "already-finished threads should not wait for full timeout"
    );
}
