//! Optional local telemetry logging used for debugging and performance triage.

use crate::config::AppConfig;
use std::env;
use std::fs::OpenOptions;
use std::path::PathBuf;
use std::sync::OnceLock;
use tracing_subscriber::fmt::time::UtcTime;

static TRACING_INIT: OnceLock<()> = OnceLock::new();

pub(crate) fn tracing_log_path() -> PathBuf {
    env::var("VOICETERM_TRACE_LOG")
        .map(PathBuf::from)
        .unwrap_or_else(|_| env::temp_dir().join("voiceterm_trace.jsonl"))
}

#[inline]
fn tracing_enabled(config: &AppConfig) -> bool {
    (config.logs || config.log_timings) && !config.no_logs
}

fn init_tracing_once(config: &AppConfig, once: &OnceLock<()>) {
    if !tracing_enabled(config) {
        return;
    }

    let _ = once.get_or_init(|| {
        let path = tracing_log_path();
        let file = match OpenOptions::new().create(true).append(true).open(&path) {
            Ok(file) => file,
            Err(_) => return,
        };
        let subscriber = tracing_subscriber::fmt()
            .json()
            .with_timer(UtcTime::rfc_3339())
            .with_writer(file)
            .with_current_span(false)
            .with_span_list(false)
            .finish();
        let _ = tracing::subscriber::set_global_default(subscriber);
    });
}

pub(crate) fn init_tracing(config: &AppConfig) {
    init_tracing_once(config, &TRACING_INIT);
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;
    use std::fs;
    use std::sync::Mutex;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn env_lock() -> &'static Mutex<()> {
        static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
        LOCK.get_or_init(|| Mutex::new(()))
    }

    fn test_config() -> AppConfig {
        AppConfig::parse_from(["telemetry-test"])
    }

    fn unique_trace_path(suffix: &str) -> PathBuf {
        let nanos = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system time should be after epoch")
            .as_nanos();
        env::temp_dir().join(format!("voiceterm-trace-{suffix}-{nanos}.jsonl"))
    }

    #[test]
    fn tracing_log_path_prefers_env_override() {
        let _guard = env_lock().lock().expect("env lock");
        let path = unique_trace_path("env");
        unsafe {
            env::set_var("VOICETERM_TRACE_LOG", &path);
        }
        assert_eq!(tracing_log_path(), path);
        unsafe {
            env::remove_var("VOICETERM_TRACE_LOG");
        }
    }

    #[test]
    fn tracing_log_path_defaults_to_temp_dir_when_env_missing() {
        let _guard = env_lock().lock().expect("env lock");
        unsafe {
            env::remove_var("VOICETERM_TRACE_LOG");
        }
        let expected = env::temp_dir().join("voiceterm_trace.jsonl");
        assert_eq!(tracing_log_path(), expected);
    }

    #[test]
    fn tracing_enabled_truth_table() {
        let mut cfg = test_config();
        cfg.logs = false;
        cfg.log_timings = false;
        cfg.no_logs = false;
        assert!(!tracing_enabled(&cfg));

        cfg.logs = true;
        assert!(tracing_enabled(&cfg));

        cfg.logs = false;
        cfg.log_timings = true;
        assert!(tracing_enabled(&cfg));

        cfg.logs = true;
        cfg.log_timings = true;
        cfg.no_logs = true;
        assert!(!tracing_enabled(&cfg));
    }

    #[test]
    fn init_tracing_once_respects_enabled_flag_and_creates_file() {
        let _guard = env_lock().lock().expect("env lock");

        let enabled_path = unique_trace_path("enabled");
        let _ = fs::remove_file(&enabled_path);
        unsafe {
            env::set_var("VOICETERM_TRACE_LOG", &enabled_path);
        }
        let enabled_once = OnceLock::new();
        let mut enabled_cfg = test_config();
        enabled_cfg.logs = true;
        enabled_cfg.log_timings = false;
        enabled_cfg.no_logs = false;
        init_tracing_once(&enabled_cfg, &enabled_once);
        assert!(
            enabled_path.exists(),
            "enabled config should create trace file"
        );

        let disabled_path = unique_trace_path("disabled");
        let _ = fs::remove_file(&disabled_path);
        unsafe {
            env::set_var("VOICETERM_TRACE_LOG", &disabled_path);
        }
        let disabled_once = OnceLock::new();
        let mut disabled_cfg = test_config();
        disabled_cfg.logs = false;
        disabled_cfg.log_timings = false;
        disabled_cfg.no_logs = true;
        init_tracing_once(&disabled_cfg, &disabled_once);
        assert!(
            !disabled_path.exists(),
            "disabled config should not create trace file"
        );

        unsafe {
            env::remove_var("VOICETERM_TRACE_LOG");
        }
        let _ = fs::remove_file(enabled_path);
        let _ = fs::remove_file(disabled_path);
    }
}
