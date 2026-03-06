//! Prompt-observation logging so readiness heuristics can be tuned with evidence.

use std::env;
use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::config::OverlayConfig;

const PROMPT_LOG_MAX_BYTES: u64 = 5 * 1024 * 1024;

pub(crate) fn resolve_prompt_log(config: &OverlayConfig) -> Option<PathBuf> {
    if let Some(path) = &config.prompt_log {
        return Some(path.clone());
    }
    if let Ok(path) = env::var("VOICETERM_PROMPT_LOG") {
        return Some(PathBuf::from(path));
    }
    None
}

pub(crate) struct PromptLogger {
    writer: Option<Mutex<PromptLogWriter>>,
}

struct PromptLogWriter {
    path: PathBuf,
    file: fs::File,
    bytes_written: u64,
}

impl PromptLogWriter {
    fn new(path: PathBuf) -> Option<Self> {
        let mut bytes_written = fs::metadata(&path).map(|m| m.len()).unwrap_or(0);
        if bytes_written > PROMPT_LOG_MAX_BYTES {
            let _ = fs::remove_file(&path);
            bytes_written = 0;
        }
        let file = fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&path)
            .ok()?;
        Some(Self {
            path,
            file,
            bytes_written,
        })
    }

    fn rotate_if_needed(&mut self, next_len: usize) {
        if self.bytes_written.saturating_add(next_len as u64) <= PROMPT_LOG_MAX_BYTES {
            return;
        }
        if let Ok(file) = fs::OpenOptions::new()
            .create(true)
            .write(true)
            .truncate(true)
            .open(&self.path)
        {
            self.file = file;
            self.bytes_written = 0;
        }
    }

    fn write_line(&mut self, line: &str) {
        self.rotate_if_needed(line.len());
        if self.file.write_all(line.as_bytes()).is_ok() {
            self.bytes_written = self.bytes_written.saturating_add(line.len() as u64);
        }
    }
}

impl PromptLogger {
    pub(crate) fn new(path: Option<PathBuf>) -> Self {
        let writer = path.and_then(PromptLogWriter::new).map(Mutex::new);
        Self { writer }
    }

    pub(crate) fn log(&self, message: &str) {
        let Some(writer) = &self.writer else {
            return;
        };
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();
        let line = format!("[{timestamp}] {message}\n");
        if let Ok(mut guard) = writer.lock() {
            guard.write_line(&line);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_env::{default_overlay_config, env_lock as shared_env_lock};
    use std::time::{SystemTime, UNIX_EPOCH};

    fn temp_log_path(label: &str) -> PathBuf {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis();
        env::temp_dir().join(format!("{label}_{unique}.log"))
    }

    #[test]
    fn resolve_prompt_log_prefers_config() {
        let mut config = default_overlay_config();
        config.prompt_log = Some(PathBuf::from("/tmp/codex_prompt_override.log"));
        let resolved = resolve_prompt_log(&config);
        assert_eq!(
            resolved,
            Some(PathBuf::from("/tmp/codex_prompt_override.log"))
        );
    }

    #[test]
    fn resolve_prompt_log_uses_env() {
        let _guard = shared_env_lock();
        let env_path = PathBuf::from("/tmp/codex_prompt_env.log");
        env::set_var("VOICETERM_PROMPT_LOG", &env_path);
        let config = default_overlay_config();
        let resolved = resolve_prompt_log(&config);
        env::remove_var("VOICETERM_PROMPT_LOG");
        assert_eq!(resolved, Some(env_path));
    }

    #[test]
    fn resolve_prompt_log_defaults_to_none() {
        let _guard = shared_env_lock();
        env::remove_var("VOICETERM_PROMPT_LOG");
        let config = default_overlay_config();
        assert!(resolve_prompt_log(&config).is_none());
    }

    #[test]
    fn prompt_logger_writes_lines() {
        let path = temp_log_path("prompt_logger");
        let logger = PromptLogger::new(Some(path.clone()));
        logger.log("hello");
        let contents = std::fs::read_to_string(&path).expect("log file");
        let _ = std::fs::remove_file(&path);
        assert!(contents.contains("hello"));
    }

    #[test]
    fn prompt_log_max_bytes_constant_is_5mb() {
        assert_eq!(PROMPT_LOG_MAX_BYTES, 5_u64 * 1024 * 1024);
    }

    #[test]
    fn rotate_if_needed_keeps_file_when_next_line_fits_limit() {
        let path = temp_log_path("prompt_rotate_fit");
        let mut writer = PromptLogWriter::new(path.clone()).expect("writer");
        writer.bytes_written = PROMPT_LOG_MAX_BYTES - 2;

        writer.rotate_if_needed(2);

        assert_eq!(writer.bytes_written, PROMPT_LOG_MAX_BYTES - 2);
        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn rotate_if_needed_truncates_when_next_line_exceeds_limit() {
        let path = temp_log_path("prompt_rotate_truncate");
        let mut writer = PromptLogWriter::new(path.clone()).expect("writer");
        writer.bytes_written = PROMPT_LOG_MAX_BYTES - 1;

        writer.rotate_if_needed(2);

        assert_eq!(writer.bytes_written, 0);
        let len = std::fs::metadata(&path).expect("metadata").len();
        assert_eq!(len, 0);
        let _ = std::fs::remove_file(&path);
    }
}
