//! Optional markdown session-memory logger.
//!
//! Captures newline-delimited user input and backend output in an append-only
//! markdown log so users can keep a local memory trail per project/session.

use std::fs::{self, File, OpenOptions};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::stream_line_buffer::StreamLineBuffer;

const MAX_LINE_BYTES: usize = 2048;

#[derive(Debug)]
pub(crate) struct SessionMemoryLogger {
    path: PathBuf,
    file: File,
    pending_user_line: StreamLineBuffer,
    pending_assistant_line: StreamLineBuffer,
}

impl SessionMemoryLogger {
    pub(crate) fn new(path: &Path, backend_label: &str, working_dir: &str) -> io::Result<Self> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }

        let mut file = OpenOptions::new().create(true).append(true).open(path)?;
        let metadata = file.metadata()?;
        if metadata.len() == 0 {
            writeln!(file, "# VoiceTerm Session Memory")?;
            writeln!(file)?;
        }

        writeln!(file, "## Session {}", unix_epoch_seconds())?;
        writeln!(file, "- backend: {backend_label}")?;
        writeln!(file, "- cwd: {working_dir}")?;
        writeln!(file)?;
        file.flush()?;

        Ok(Self {
            path: path.to_path_buf(),
            file,
            pending_user_line: StreamLineBuffer::new(MAX_LINE_BYTES),
            pending_assistant_line: StreamLineBuffer::new(MAX_LINE_BYTES),
        })
    }

    pub(crate) fn path(&self) -> &Path {
        &self.path
    }

    /// Capture PTY input bytes as newline-delimited user messages.
    pub(crate) fn record_user_input_bytes(&mut self, bytes: &[u8]) {
        if bytes.is_empty() || bytes.contains(&0x1b) {
            return;
        }

        for &b in bytes {
            match b {
                b'\r' | b'\n' => {
                    if let Some(line) = self.pending_user_line.take_line() {
                        let _ = self.write_entry("user", &line);
                    }
                }
                0x7f | 0x08 => {
                    self.pending_user_line.pop_char();
                }
                b'\t' => self.pending_user_line.push_char(' '),
                _ if b.is_ascii_control() => {}
                _ => self.pending_user_line.push_char(b as char),
            }
        }
    }

    /// Capture PTY output bytes as newline-delimited backend messages.
    pub(crate) fn record_backend_output_bytes(&mut self, bytes: &[u8]) {
        if bytes.is_empty() {
            return;
        }

        let cleaned = voiceterm::codex::sanitize_pty_output(bytes);
        if cleaned.is_empty() {
            return;
        }

        for ch in cleaned.chars() {
            match ch {
                '\n' => {
                    if let Some(line) = self.pending_assistant_line.take_line() {
                        let _ = self.write_entry("assistant", &line);
                    }
                }
                '\r' => {}
                _ if ch.is_control() => {}
                _ => self.pending_assistant_line.push_char(ch),
            }
        }
    }

    pub(crate) fn flush_pending(&mut self) {
        if let Some(line) = self.pending_user_line.take_line() {
            let _ = self.write_entry("user", &line);
        }
        if let Some(line) = self.pending_assistant_line.take_line() {
            let _ = self.write_entry("assistant", &line);
        }
        let _ = self.file.flush();
    }

    fn write_entry(&mut self, role: &str, line: &str) -> io::Result<()> {
        let sanitized = sanitize_entry_text(line);
        if sanitized.is_empty() {
            return Ok(());
        }
        writeln!(self.file, "- [{role}] {sanitized}")?;
        self.file.flush()
    }
}

impl Drop for SessionMemoryLogger {
    fn drop(&mut self) {
        self.flush_pending();
    }
}

fn unix_epoch_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

fn sanitize_entry_text(input: &str) -> String {
    let mut out = String::with_capacity(input.len());
    for ch in input.chars() {
        if ch.is_control() {
            continue;
        }
        out.push(ch);
    }
    out.trim().to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn unique_temp_path() -> PathBuf {
        let pid = std::process::id();
        let nanos = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos())
            .unwrap_or(0);
        std::env::temp_dir().join(format!("voiceterm-session-memory-{pid}-{nanos}.md"))
    }

    #[test]
    fn logger_records_user_and_assistant_lines() {
        let path = unique_temp_path();
        {
            let mut logger = SessionMemoryLogger::new(&path, "codex", "/tmp/project")
                .unwrap_or_else(|err| panic!("create logger: {err}"));
            logger.record_user_input_bytes(b"hello world\r");
            logger.record_backend_output_bytes(b"assistant says hi\n");
            logger.flush_pending();
        }

        let content = fs::read_to_string(&path)
            .unwrap_or_else(|err| panic!("read session memory log {}: {err}", path.display()));
        assert!(content.contains("# VoiceTerm Session Memory"));
        assert!(content.contains("- [user] hello world"));
        assert!(content.contains("- [assistant] assistant says hi"));

        let _ = fs::remove_file(path);
    }

    #[test]
    fn logger_ignores_escape_noise_in_user_input() {
        let path = unique_temp_path();
        {
            let mut logger = SessionMemoryLogger::new(&path, "codex", "/tmp/project")
                .unwrap_or_else(|err| panic!("create logger: {err}"));
            logger.record_user_input_bytes(b"\x1b[0[I");
            logger.flush_pending();
        }

        let content = fs::read_to_string(&path)
            .unwrap_or_else(|err| panic!("read session memory log {}: {err}", path.display()));
        assert!(!content.contains("[0[I"));

        let _ = fs::remove_file(path);
    }
}
