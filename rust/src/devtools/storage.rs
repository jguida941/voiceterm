//! JSONL persistence helpers for guarded Dev Mode event logging.

use std::env;
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, BufWriter, Write};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::devtools::DevEvent;

pub const DEV_LOG_DIR_NAME: &str = ".voiceterm/dev";
pub const DEV_LOG_SESSIONS_DIR_NAME: &str = "sessions";

#[derive(Debug)]
pub struct DevEventJsonlWriter {
    path: PathBuf,
    file: BufWriter<File>,
    lines_written: u64,
}

impl DevEventJsonlWriter {
    pub fn open(path: &Path) -> io::Result<Self> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }

        let file = OpenOptions::new().create(true).append(true).open(path)?;
        let lines_written = count_lines(path);
        Ok(Self {
            path: path.to_path_buf(),
            file: BufWriter::new(file),
            lines_written,
        })
    }

    pub fn open_session(dev_root: &Path) -> io::Result<Self> {
        Self::open(&new_session_log_path(dev_root))
    }

    pub fn append(&mut self, event: &DevEvent) -> io::Result<()> {
        let json = serde_json::to_string(event)
            .map_err(|err| io::Error::new(io::ErrorKind::InvalidData, err))?;
        writeln!(self.file, "{json}")?;
        self.file.flush()?;
        self.lines_written = self.lines_written.saturating_add(1);
        Ok(())
    }

    pub fn flush(&mut self) -> io::Result<()> {
        self.file.flush()
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    pub fn lines_written(&self) -> u64 {
        self.lines_written
    }
}

pub fn default_dev_root_dir(working_dir: &Path) -> PathBuf {
    if let Some(home_dir) = env::var_os("HOME").filter(|value| !value.is_empty()) {
        PathBuf::from(home_dir).join(".voiceterm").join("dev")
    } else {
        working_dir.join(DEV_LOG_DIR_NAME)
    }
}

pub fn new_session_log_path(dev_root: &Path) -> PathBuf {
    dev_root
        .join(DEV_LOG_SESSIONS_DIR_NAME)
        .join(format!("session-{}.jsonl", session_suffix()))
}

fn session_suffix() -> String {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default();
    let secs = now.as_secs();
    let nanos = now.subsec_nanos();
    let pid = std::process::id();
    format!("{secs}-{nanos:09}-{pid}")
}

fn count_lines(path: &Path) -> u64 {
    let Ok(file) = File::open(path) else {
        return 0;
    };
    let reader = BufReader::new(file);
    reader.lines().count() as u64
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::devtools::{DevCaptureSource, DevEventKind, DEV_EVENT_SCHEMA_VERSION};
    use std::sync::{Mutex, OnceLock};

    fn with_env_lock<T>(run: impl FnOnce() -> T) -> T {
        static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
        let lock = LOCK.get_or_init(|| Mutex::new(()));
        let guard = lock.lock();
        assert!(guard.is_ok());
        run()
    }

    fn unique_temp_root() -> PathBuf {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos();
        env::temp_dir().join(format!("voiceterm-devtools-{now}"))
    }

    #[test]
    fn new_session_log_path_is_under_sessions_directory() {
        let root = PathBuf::from("/tmp/dev-root");
        let path = new_session_log_path(&root);
        assert!(path.starts_with(root.join(DEV_LOG_SESSIONS_DIR_NAME)));
        assert!(path.to_string_lossy().ends_with(".jsonl"));
    }

    #[test]
    fn writer_open_session_appends_jsonl_events() {
        let root = unique_temp_root();
        let mut writer = match DevEventJsonlWriter::open_session(&root) {
            Ok(writer) => writer,
            Err(err) => panic!("open_session failed: {err}"),
        };
        let path = writer.path().to_path_buf();
        let event = DevEvent {
            schema_version: DEV_EVENT_SCHEMA_VERSION,
            event_id: 1,
            timestamp_unix_ms: 123,
            kind: DevEventKind::Error,
            source: DevCaptureSource::Unknown,
            transcript_chars: 0,
            transcript_words: 0,
            latency_ms: None,
            speech_ms: None,
            dropped_frames: 0,
            error_message: Some("boom".to_string()),
        };
        let append_result = writer.append(&event);
        assert!(append_result.is_ok());
        assert_eq!(writer.lines_written(), 1);
        let flush_result = writer.flush();
        assert!(flush_result.is_ok());
        drop(writer);

        let content = match fs::read_to_string(&path) {
            Ok(content) => content,
            Err(err) => panic!("read_to_string failed for {}: {err}", path.display()),
        };
        assert!(content.contains("\"schema_version\":1"));
        assert!(content.contains("\"kind\":\"error\""));
        assert!(content.contains("\"error_message\":\"boom\""));

        let _ = fs::remove_dir_all(root);
    }

    #[test]
    fn default_dev_root_dir_prefers_home_env_when_available() {
        with_env_lock(|| {
            let previous = env::var_os("HOME");
            env::set_var("HOME", "/tmp/dev-home-test");
            let path = default_dev_root_dir(Path::new("/tmp/project"));
            assert_eq!(path, PathBuf::from("/tmp/dev-home-test/.voiceterm/dev"));
            match previous {
                Some(value) => env::set_var("HOME", value),
                None => env::remove_var("HOME"),
            }
        });
    }
}
