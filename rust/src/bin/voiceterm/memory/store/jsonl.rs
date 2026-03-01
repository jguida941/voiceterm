//! Append-only JSONL writer for immutable event history.
//!
//! Events are written one-per-line to `.voiceterm/memory/events.jsonl`.
//! This log is the canonical audit trail. File rotation is enforced
//! when the log exceeds [`MAX_FILE_BYTES`].

use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

use super::super::types::MemoryEvent;

/// Maximum JSONL file size before rotation (~10 MB).
const MAX_FILE_BYTES: u64 = 10 * 1024 * 1024;

/// Maximum number of rotated backup files to keep.
const MAX_ROTATED_FILES: usize = 1;

/// Append-only JSONL event writer with size-based rotation.
#[derive(Debug)]
pub(crate) struct JsonlWriter {
    path: PathBuf,
    file: File,
    lines_written: u64,
    bytes_written: u64,
}

impl JsonlWriter {
    /// Open or create the JSONL file at the given path.
    pub(crate) fn open(path: &Path) -> io::Result<Self> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }

        let file = OpenOptions::new().create(true).append(true).open(path)?;

        // Get current file size and line count for bookkeeping.
        let bytes_written = file.metadata().map(|m| m.len()).unwrap_or(0);
        let lines_written = count_lines(path);

        Ok(Self {
            path: path.to_path_buf(),
            file,
            lines_written,
            bytes_written,
        })
    }

    /// Append one event to the log. Rotates the file if size exceeds the limit.
    pub(crate) fn append(&mut self, event: &MemoryEvent) -> io::Result<()> {
        // Check if rotation is needed before writing.
        if self.bytes_written >= MAX_FILE_BYTES {
            self.rotate()?;
        }

        let json = serde_json::to_string(event)
            .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, e))?;
        let line = format!("{json}\n");
        let line_bytes = line.len() as u64;

        self.file.write_all(line.as_bytes())?;
        self.bytes_written += line_bytes;
        self.lines_written += 1;

        Ok(())
    }

    /// Flush buffered writes to disk.
    pub(crate) fn flush(&mut self) -> io::Result<()> {
        self.file.flush()
    }

    /// Number of events written (including pre-existing lines).
    pub(crate) fn lines_written(&self) -> u64 {
        self.lines_written
    }

    /// Underlying file path.
    pub(crate) fn path(&self) -> &Path {
        &self.path
    }

    /// Rotate the current file: rename to .1.jsonl, delete older backups, reopen.
    fn rotate(&mut self) -> io::Result<()> {
        // Flush before rotating.
        self.file.flush()?;

        // Delete oldest backups beyond MAX_ROTATED_FILES.
        for i in (MAX_ROTATED_FILES..MAX_ROTATED_FILES + 3).rev() {
            let old = rotated_path(&self.path, i);
            let _ = fs::remove_file(&old);
        }

        // Shift existing rotated files up by one.
        for i in (1..MAX_ROTATED_FILES).rev() {
            let from = rotated_path(&self.path, i);
            let to = rotated_path(&self.path, i + 1);
            if from.exists() {
                let _ = fs::rename(&from, &to);
            }
        }

        // Rename current file to .1
        let rotated = rotated_path(&self.path, 1);
        fs::rename(&self.path, &rotated)?;

        // Reopen a fresh file.
        self.file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)?;
        self.lines_written = 0;
        self.bytes_written = 0;

        Ok(())
    }
}

/// Build the path for a rotated file (e.g., events.1.jsonl).
fn rotated_path(base: &Path, index: usize) -> PathBuf {
    let stem = base
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("events");
    let ext = base.extension().and_then(|s| s.to_str()).unwrap_or("jsonl");
    base.with_file_name(format!("{stem}.{index}.{ext}"))
}

/// Read all events from a JSONL file.
pub(crate) fn read_all_events(path: &Path) -> io::Result<Vec<MemoryEvent>> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut events = Vec::new();
    for line in reader.lines() {
        let line = line?;
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        match serde_json::from_str::<MemoryEvent>(trimmed) {
            Ok(event) => events.push(event),
            Err(_) => {
                // Skip malformed lines (forward compatibility).
                continue;
            }
        }
    }
    Ok(events)
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
    use crate::memory::types::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn temp_path(suffix: &str) -> PathBuf {
        let nanos = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos())
            .unwrap_or(0);
        std::env::temp_dir().join(format!("voiceterm-memory-jsonl-{}-{nanos}.jsonl", suffix))
    }

    fn sample_event(id: &str, text: &str) -> MemoryEvent {
        MemoryEvent {
            event_id: id.to_string(),
            session_id: "sess_test".to_string(),
            project_id: "proj_test".to_string(),
            ts: "2026-02-19T12:00:00.000Z".to_string(),
            source: EventSource::PtyInput,
            event_type: EventType::ChatTurn,
            role: EventRole::User,
            text: text.to_string(),
            topic_tags: vec![],
            entities: vec![],
            task_refs: vec![],
            artifacts: vec![],
            importance: 0.5,
            confidence: 1.0,
            retrieval_state: RetrievalState::Eligible,
            hash: None,
        }
    }

    #[test]
    fn append_and_read_back() {
        let path = temp_path("append");
        {
            let mut writer = JsonlWriter::open(&path).expect("open writer");
            writer
                .append(&sample_event("evt_1", "hello"))
                .expect("append");
            writer
                .append(&sample_event("evt_2", "world"))
                .expect("append");
            writer.flush().expect("flush");
            assert_eq!(writer.lines_written(), 2);
        }

        let events = read_all_events(&path).expect("read");
        assert_eq!(events.len(), 2);
        assert_eq!(events[0].event_id, "evt_1");
        assert_eq!(events[1].text, "world");

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn reopen_continues_count() {
        let path = temp_path("reopen");
        {
            let mut writer = JsonlWriter::open(&path).expect("open");
            writer
                .append(&sample_event("evt_1", "first"))
                .expect("append");
            writer.flush().expect("flush");
        }
        {
            let mut writer = JsonlWriter::open(&path).expect("reopen");
            assert_eq!(writer.lines_written(), 1);
            writer
                .append(&sample_event("evt_2", "second"))
                .expect("append");
            writer.flush().expect("flush");
            assert_eq!(writer.lines_written(), 2);
        }

        let events = read_all_events(&path).expect("read");
        assert_eq!(events.len(), 2);

        let _ = fs::remove_file(&path);
    }

    #[test]
    fn read_skips_malformed_lines() {
        let path = temp_path("malformed");
        fs::write(&path, "not json\n{\"invalid\":true}\n").expect("write");
        let events = read_all_events(&path).expect("read");
        assert!(events.is_empty());
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn read_nonexistent_file_returns_error() {
        let path = temp_path("nonexistent");
        let result = read_all_events(&path);
        assert!(result.is_err());
    }

    #[test]
    fn rotated_path_format() {
        let base = PathBuf::from("/tmp/events.jsonl");
        assert_eq!(rotated_path(&base, 1), PathBuf::from("/tmp/events.1.jsonl"));
        assert_eq!(rotated_path(&base, 2), PathBuf::from("/tmp/events.2.jsonl"));
    }
}
