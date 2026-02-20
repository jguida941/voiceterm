//! Append-only JSONL writer for immutable event history.
//!
//! Events are written one-per-line to `.voiceterm/memory/events.jsonl`.
//! This log is the canonical audit trail and must never be modified in place.

use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

use super::super::types::MemoryEvent;

/// Append-only JSONL event writer.
#[derive(Debug)]
pub(crate) struct JsonlWriter {
    path: PathBuf,
    file: File,
    lines_written: u64,
}

impl JsonlWriter {
    /// Open or create the JSONL file at the given path.
    pub(crate) fn open(path: &Path) -> io::Result<Self> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }

        let file = OpenOptions::new().create(true).append(true).open(path)?;

        // Count existing lines for bookkeeping.
        let lines_written = count_lines(path);

        Ok(Self {
            path: path.to_path_buf(),
            file,
            lines_written,
        })
    }

    /// Append one event to the log.
    pub(crate) fn append(&mut self, event: &MemoryEvent) -> io::Result<()> {
        let json = serde_json::to_string(event)
            .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, e))?;
        writeln!(self.file, "{json}")?;
        self.file.flush()?;
        self.lines_written += 1;
        Ok(())
    }

    /// Number of events written (including pre-existing lines).
    pub(crate) fn lines_written(&self) -> u64 {
        self.lines_written
    }

    /// Underlying file path.
    pub(crate) fn path(&self) -> &Path {
        &self.path
    }
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
        }
        {
            let mut writer = JsonlWriter::open(&path).expect("reopen");
            assert_eq!(writer.lines_written(), 1);
            writer
                .append(&sample_event("evt_2", "second"))
                .expect("append");
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
}
