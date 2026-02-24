//! Event ingestion pipeline for the memory subsystem.
//!
//! Normalizes raw inputs (transcripts, PTY I/O, devtool output) into
//! canonical [`MemoryEvent`] envelopes and routes them to storage.

use super::schema::validate_event;
use super::store::jsonl::JsonlWriter;
use super::store::sqlite::MemoryIndex;
use super::types::*;

use std::io;
use std::path::Path;

/// Memory ingestion pipeline with dual-write to JSONL + in-memory index.
#[derive(Debug)]
pub(crate) struct MemoryIngestor {
    session_id: String,
    project_id: String,
    jsonl_writer: Option<JsonlWriter>,
    index: MemoryIndex,
    mode: MemoryMode,
    events_ingested: u64,
    events_rejected: u64,
}

impl MemoryIngestor {
    /// Create a new ingestor. If `jsonl_path` is provided and mode allows capture,
    /// events are persisted to the append log.
    pub(crate) fn new(
        session_id: String,
        project_id: String,
        jsonl_path: Option<&Path>,
        mode: MemoryMode,
    ) -> io::Result<Self> {
        let jsonl_writer = if mode.allows_capture() {
            jsonl_path.map(JsonlWriter::open).transpose()?
        } else {
            None
        };

        Ok(Self {
            session_id,
            project_id,
            jsonl_writer,
            index: MemoryIndex::new(),
            mode,
            events_ingested: 0,
            events_rejected: 0,
        })
    }

    /// Ingest a voice transcript.
    pub(crate) fn ingest_transcript(&mut self, text: &str) {
        self.ingest_event_raw(
            EventSource::VoiceCapture,
            EventType::VoiceTranscript,
            EventRole::User,
            text,
            0.7,
            &[],
            &[],
            &[],
        );
    }

    /// Ingest a user PTY input line.
    pub(crate) fn ingest_user_input(&mut self, text: &str) {
        self.ingest_event_raw(
            EventSource::PtyInput,
            EventType::ChatTurn,
            EventRole::User,
            text,
            0.5,
            &[],
            &[],
            &[],
        );
    }

    /// Ingest a backend/assistant output line.
    pub(crate) fn ingest_assistant_output(&mut self, text: &str) {
        self.ingest_event_raw(
            EventSource::PtyOutput,
            EventType::ChatTurn,
            EventRole::Assistant,
            text,
            0.4,
            &[],
            &[],
            &[],
        );
    }

    /// Ingest a raw event with full control over fields.
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn ingest_event_raw(
        &mut self,
        source: EventSource,
        event_type: EventType,
        role: EventRole,
        text: &str,
        importance: f64,
        topic_tags: &[&str],
        task_refs: &[&str],
        entities: &[&str],
    ) {
        if !self.mode.allows_capture() {
            return;
        }

        let trimmed = text.trim();
        if trimmed.is_empty() {
            return;
        }
        let redacted_text = super::governance::redact_secrets(trimmed);
        if redacted_text.trim().is_empty() {
            return;
        }

        let event = MemoryEvent {
            event_id: generate_event_id(),
            session_id: self.session_id.clone(),
            project_id: self.project_id.clone(),
            ts: iso_timestamp(),
            source,
            event_type,
            role,
            text: redacted_text,
            topic_tags: topic_tags.iter().map(ToString::to_string).collect(),
            entities: entities.iter().map(ToString::to_string).collect(),
            task_refs: task_refs.iter().map(ToString::to_string).collect(),
            artifacts: vec![],
            importance: importance.clamp(0.0, 1.0),
            confidence: 1.0,
            retrieval_state: RetrievalState::Eligible,
            hash: None,
        };

        let errors = validate_event(&event);
        if !errors.is_empty() {
            self.events_rejected += 1;
            return;
        }

        // Persist to JSONL (errors are non-fatal).
        if let Some(ref mut writer) = self.jsonl_writer {
            let _ = writer.append(&event);
        }

        // Index in memory.
        self.index.insert(event);
        self.events_ingested += 1;
    }

    /// Recover events from a JSONL file into the in-memory index.
    /// Returns the number of events loaded.
    pub(crate) fn recover_from_jsonl(&mut self, path: &Path) -> usize {
        let events = match super::store::jsonl::read_all_events(path) {
            Ok(evts) => evts,
            Err(_) => return 0,
        };
        let cap = super::governance::MAX_INDEX_EVENTS;
        let skip = events.len().saturating_sub(cap);
        let mut count = 0;
        for event in events.into_iter().skip(skip) {
            self.index.insert(event);
            count += 1;
        }
        count
    }

    /// Access the in-memory index for queries.
    pub(crate) fn index(&self) -> &MemoryIndex {
        &self.index
    }

    /// Access the in-memory index mutably (for retrieval state changes).
    pub(crate) fn index_mut(&mut self) -> &mut MemoryIndex {
        &mut self.index
    }

    /// Current memory mode.
    pub(crate) fn mode(&self) -> MemoryMode {
        self.mode
    }

    /// Update the memory mode at runtime.
    pub(crate) fn set_mode(&mut self, mode: MemoryMode) {
        self.mode = mode;
    }

    /// Number of events successfully ingested.
    pub(crate) fn events_ingested(&self) -> u64 {
        self.events_ingested
    }

    /// Number of events rejected by validation.
    #[allow(dead_code)]
    pub(crate) fn events_rejected(&self) -> u64 {
        self.events_rejected
    }

    /// Session ID for this ingestor.
    pub(crate) fn session_id(&self) -> &str {
        &self.session_id
    }

    /// Project ID for this ingestor.
    pub(crate) fn project_id(&self) -> &str {
        &self.project_id
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_ingestor(mode: MemoryMode) -> MemoryIngestor {
        MemoryIngestor::new("sess_test".to_string(), "proj_test".to_string(), None, mode)
            .expect("create ingestor")
    }

    #[test]
    fn ingest_transcript_stores_event() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        ing.ingest_transcript("hello world");
        assert_eq!(ing.events_ingested(), 1);
        assert_eq!(ing.index().len(), 1);

        let recent = ing.index().recent(1);
        assert_eq!(recent[0].text, "hello world");
        assert_eq!(recent[0].event_type, EventType::VoiceTranscript);
    }

    #[test]
    fn ingest_user_input_stores_event() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        ing.ingest_user_input("git status");
        assert_eq!(ing.events_ingested(), 1);
        let recent = ing.index().recent(1);
        assert_eq!(recent[0].role, EventRole::User);
        assert_eq!(recent[0].source, EventSource::PtyInput);
    }

    #[test]
    fn ingest_assistant_output_stores_event() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        ing.ingest_assistant_output("On branch develop");
        assert_eq!(ing.events_ingested(), 1);
        let recent = ing.index().recent(1);
        assert_eq!(recent[0].role, EventRole::Assistant);
    }

    #[test]
    fn off_mode_blocks_all_capture() {
        let mut ing = make_ingestor(MemoryMode::Off);
        ing.ingest_transcript("should not store");
        assert_eq!(ing.events_ingested(), 0);
        assert!(ing.index().is_empty());
    }

    #[test]
    fn paused_mode_blocks_capture() {
        let mut ing = make_ingestor(MemoryMode::Paused);
        ing.ingest_user_input("should not store");
        assert_eq!(ing.events_ingested(), 0);
    }

    #[test]
    fn incognito_mode_blocks_capture() {
        let mut ing = make_ingestor(MemoryMode::Incognito);
        ing.ingest_user_input("ephemeral");
        assert_eq!(ing.events_ingested(), 0);
    }

    #[test]
    fn capture_only_mode_allows_capture() {
        let mut ing = make_ingestor(MemoryMode::CaptureOnly);
        ing.ingest_user_input("captured");
        assert_eq!(ing.events_ingested(), 1);
    }

    #[test]
    fn empty_text_is_rejected() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        ing.ingest_transcript("   ");
        ing.ingest_transcript("");
        assert_eq!(ing.events_ingested(), 0);
    }

    #[test]
    fn mode_switch_at_runtime() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        ing.ingest_transcript("before pause");
        assert_eq!(ing.events_ingested(), 1);

        ing.set_mode(MemoryMode::Paused);
        ing.ingest_transcript("during pause");
        assert_eq!(ing.events_ingested(), 1);

        ing.set_mode(MemoryMode::Assist);
        ing.ingest_transcript("after resume");
        assert_eq!(ing.events_ingested(), 2);
    }

    #[test]
    fn ingest_with_tags() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        ing.ingest_event_raw(
            EventSource::PtyInput,
            EventType::CommandRun,
            EventRole::User,
            "cargo test",
            0.8,
            &["testing", "rust"],
            &["MP-230"],
            &["rust/Cargo.toml"],
        );
        assert_eq!(ing.events_ingested(), 1);

        let by_topic = ing.index().by_topic("rust", 10);
        assert_eq!(by_topic.len(), 1);

        let by_task = ing.index().by_task("MP-230", 10);
        assert_eq!(by_task.len(), 1);
    }

    #[test]
    fn test_recover_from_jsonl_empty() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        let path = std::env::temp_dir().join("voiceterm-recover-nonexistent.jsonl");
        let _ = std::fs::remove_file(&path); // ensure it doesn't exist
        let recovered = ing.recover_from_jsonl(&path);
        assert_eq!(recovered, 0);
        assert!(ing.index().is_empty());
    }

    #[test]
    fn test_recover_from_jsonl_roundtrip() {
        use std::time::{SystemTime, UNIX_EPOCH};
        let nanos = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos())
            .unwrap_or(0);
        let path = std::env::temp_dir().join(format!("voiceterm-recover-rt-{nanos}.jsonl"));

        {
            let mut writer_ing = MemoryIngestor::new(
                "sess_w".to_string(),
                "proj_w".to_string(),
                Some(&path),
                MemoryMode::Assist,
            )
            .unwrap_or_else(|err| panic!("create writer ingestor failed: {err}"));
            writer_ing.ingest_transcript("event one");
            writer_ing.ingest_transcript("event two");
            writer_ing.ingest_transcript("event three");
            assert_eq!(writer_ing.events_ingested(), 3);
        }

        let mut reader_ing = make_ingestor(MemoryMode::Assist);
        let recovered = reader_ing.recover_from_jsonl(&path);
        assert_eq!(recovered, 3);
        assert_eq!(reader_ing.index().len(), 3);

        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn test_recover_caps_at_max_index() {
        use std::time::{SystemTime, UNIX_EPOCH};
        let nanos = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos())
            .unwrap_or(0);
        let path = std::env::temp_dir().join(format!("voiceterm-recover-cap-{nanos}.jsonl"));
        let cap = super::super::governance::MAX_INDEX_EVENTS;

        {
            let mut writer = super::super::store::jsonl::JsonlWriter::open(&path)
                .unwrap_or_else(|err| panic!("open writer failed: {err}"));
            for i in 0..(cap + 5) {
                let event = MemoryEvent {
                    event_id: generate_event_id(),
                    session_id: "sess_cap".to_string(),
                    project_id: "proj_cap".to_string(),
                    ts: iso_timestamp(),
                    source: EventSource::PtyInput,
                    event_type: EventType::ChatTurn,
                    role: EventRole::User,
                    text: format!("event {i}"),
                    topic_tags: vec![],
                    entities: vec![],
                    task_refs: vec![],
                    artifacts: vec![],
                    importance: 0.5,
                    confidence: 1.0,
                    retrieval_state: RetrievalState::Eligible,
                    hash: None,
                };
                writer
                    .append(&event)
                    .unwrap_or_else(|err| panic!("append failed: {err}"));
            }
        }

        let mut reader_ing = make_ingestor(MemoryMode::Assist);
        let recovered = reader_ing.recover_from_jsonl(&path);
        assert_eq!(recovered, cap);

        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn ingest_with_jsonl_persistence() {
        use std::time::{SystemTime, UNIX_EPOCH};
        let nanos = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos())
            .unwrap_or(0);
        let path = std::env::temp_dir().join(format!("voiceterm-ingest-{nanos}.jsonl"));

        {
            let mut ing = MemoryIngestor::new(
                "sess_test".to_string(),
                "proj_test".to_string(),
                Some(&path),
                MemoryMode::Assist,
            )
            .expect("create ingestor");
            ing.ingest_transcript("persisted event");
            assert_eq!(ing.events_ingested(), 1);
        }

        // Verify JSONL file has content.
        let events = super::super::store::jsonl::read_all_events(&path).expect("read jsonl");
        assert_eq!(events.len(), 1);
        assert_eq!(events[0].text, "persisted event");

        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn ingest_redacts_secret_prefixes_before_persisting() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        ing.ingest_transcript("token sk-supersecret and ghp_privatevalue");

        let recent = ing.index().recent(1);
        assert_eq!(recent.len(), 1);
        assert!(recent[0].text.contains("[REDACTED_KEY]"));
        assert!(recent[0].text.contains("[REDACTED_TOKEN]"));
        assert!(!recent[0].text.contains("sk-supersecret"));
        assert!(!recent[0].text.contains("ghp_privatevalue"));
    }
}
