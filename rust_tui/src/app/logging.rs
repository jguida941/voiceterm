use crate::config::AppConfig;
use std::{
    env, fs,
    io::Write,
    path::PathBuf,
    sync::{
        atomic::{AtomicBool, Ordering},
        Mutex, OnceLock,
    },
    time::{SystemTime, UNIX_EPOCH},
};

const LOG_MAX_BYTES: u64 = 5 * 1024 * 1024;
static LOG_ENABLED: AtomicBool = AtomicBool::new(false);
static LOG_CONTENT_ENABLED: AtomicBool = AtomicBool::new(false);
static LOG_STATE: OnceLock<Mutex<LogState>> = OnceLock::new();

/// Path to the temp log file we rotate between runs.
pub fn log_file_path() -> PathBuf {
    env::temp_dir().join("codex_voice_tui.log")
}

struct LogWriter {
    path: PathBuf,
    file: fs::File,
    max_bytes: u64,
    bytes_written: u64,
}

impl LogWriter {
    fn new(path: PathBuf, max_bytes: u64) -> Option<Self> {
        let mut bytes_written = fs::metadata(&path).map(|m| m.len()).unwrap_or(0);
        if bytes_written > max_bytes {
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
            max_bytes,
            bytes_written,
        })
    }

    fn rotate_if_needed(&mut self, next_len: usize) {
        if self.bytes_written.saturating_add(next_len as u64) <= self.max_bytes {
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

#[derive(Default)]
struct LogState {
    writer: Option<LogWriter>,
}

fn log_state() -> &'static Mutex<LogState> {
    LOG_STATE.get_or_init(|| Mutex::new(LogState::default()))
}

/// Configure logging based on CLI flags or environment.
pub fn init_logging(config: &AppConfig) {
    let enabled = (config.logs || config.log_timings) && !config.no_logs;
    let content_enabled = enabled && config.log_content;
    LOG_ENABLED.store(enabled, Ordering::Relaxed);
    LOG_CONTENT_ENABLED.store(content_enabled, Ordering::Relaxed);

    let mut state = log_state()
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    if enabled {
        state.writer = LogWriter::new(log_file_path(), LOG_MAX_BYTES);
    } else {
        state.writer = None;
    }
}

/// Write debug messages to a temp file so we can troubleshoot without corrupting the TUI.
pub fn log_debug(msg: &str) {
    if !LOG_ENABLED.load(Ordering::Relaxed) {
        return;
    }
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    let line = format!("[{timestamp}] {msg}\n");
    let mut state = log_state()
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    if let Some(writer) = state.writer.as_mut() {
        writer.write_line(&line);
    }
}

/// Write logs that may contain user content (prompt/transcript snippets).
pub fn log_debug_content(msg: &str) {
    if !LOG_CONTENT_ENABLED.load(Ordering::Relaxed) {
        return;
    }
    log_debug(msg);
}

#[cfg(test)]
pub(crate) fn set_logging_for_tests(enabled: bool, content_enabled: bool) {
    LOG_ENABLED.store(enabled, Ordering::Relaxed);
    LOG_CONTENT_ENABLED.store(content_enabled, Ordering::Relaxed);
    let mut state = log_state()
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    if enabled {
        state.writer = LogWriter::new(log_file_path(), LOG_MAX_BYTES);
    } else {
        state.writer = None;
    }
}
