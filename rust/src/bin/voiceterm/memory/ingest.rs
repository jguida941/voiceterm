//! Event ingestion pipeline for the memory subsystem.
//!
//! Normalizes raw inputs (transcripts, PTY I/O, devtool output) into
//! canonical [`MemoryEvent`] envelopes and routes them to storage.
//!
//! Key behaviors:
//! - ANSI escape sequences are stripped before persistence
//! - Noise events (whitespace-only, very short) are discarded
//! - Events are buffered and flushed periodically (not on every call)
//! - File rotation enforced at ~10 MB via [`JsonlWriter`]
//! - Retention GC runs on startup recovery

use super::schema::validate_event;
use super::store::jsonl::JsonlWriter;
use super::store::sqlite::MemoryIndex;
use super::types::*;

use std::io;
use std::path::Path;
use std::time::Instant;

/// Minimum meaningful text length after ANSI stripping (bytes).
/// Events shorter than this are considered noise and dropped.
const MIN_TEXT_LEN: usize = 2;

/// Number of events to buffer before flushing to disk.
const FLUSH_BUFFER_SIZE: usize = 50;

/// Maximum time between flushes (seconds).
const FLUSH_INTERVAL_SECS: u64 = 5;
const MAX_TOPIC_TAGS: usize = 8;
const MAX_TASK_REFS: usize = 8;
const MAX_ENTITIES: usize = 8;

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
    /// Buffered events waiting to be flushed to JSONL.
    write_buffer: Vec<MemoryEvent>,
    /// Last time the buffer was flushed to disk.
    last_flush: Instant,
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
            write_buffer: Vec::with_capacity(FLUSH_BUFFER_SIZE),
            last_flush: Instant::now(),
        })
    }

    /// Ingest a voice transcript.
    pub(crate) fn ingest_transcript(&mut self, text: &str) {
        // Transcripts are already clean text from STT — no ANSI stripping needed.
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
        let cleaned = strip_ansi(text);
        if is_noise(&cleaned) {
            return;
        }
        self.ingest_event_raw(
            EventSource::PtyInput,
            EventType::ChatTurn,
            EventRole::User,
            &cleaned,
            0.5,
            &[],
            &[],
            &[],
        );
    }

    /// Ingest a backend/assistant output line.
    pub(crate) fn ingest_assistant_output(&mut self, text: &str) {
        let cleaned = strip_ansi(text);
        if is_noise(&cleaned) {
            return;
        }
        self.ingest_event_raw(
            EventSource::PtyOutput,
            EventType::ChatTurn,
            EventRole::Assistant,
            &cleaned,
            0.4,
            &[],
            &[],
            &[],
        );
    }

    /// Ingest a raw event with full control over fields.
    #[allow(
        clippy::too_many_arguments,
        reason = "Ingestion needs the full normalized event envelope at one boundary before it becomes a MemoryEvent."
    )]
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
        let topic_tags = merge_topic_tags(topic_tags, &redacted_text);
        let entities = merge_entities(entities, &redacted_text);
        let task_refs = merge_task_refs(task_refs, &redacted_text);

        let event = MemoryEvent {
            event_id: generate_event_id(),
            session_id: self.session_id.clone(),
            project_id: self.project_id.clone(),
            ts: iso_timestamp(),
            source,
            event_type,
            role,
            text: redacted_text,
            topic_tags,
            entities,
            task_refs,
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

        // Buffer for batched JSONL writes.
        self.write_buffer.push(event.clone());

        // Flush if buffer is full or enough time has passed.
        if self.write_buffer.len() >= FLUSH_BUFFER_SIZE
            || self.last_flush.elapsed().as_secs() >= FLUSH_INTERVAL_SECS
        {
            self.flush_buffer();
        }

        // Index in memory.
        self.index.insert(event);
        self.events_ingested += 1;
    }

    /// Flush buffered events to the JSONL writer.
    fn flush_buffer(&mut self) {
        if self.write_buffer.is_empty() {
            return;
        }
        if let Some(ref mut writer) = self.jsonl_writer {
            for event in self.write_buffer.drain(..) {
                let _ = writer.append(&event);
            }
            let _ = writer.flush();
        } else {
            self.write_buffer.clear();
        }
        self.last_flush = Instant::now();
    }

    /// Force-flush any buffered events to disk. Call this on shutdown
    /// or when the event loop is idle.
    pub(crate) fn flush(&mut self) {
        self.flush_buffer();
    }

    /// Recover events from a JSONL file into the in-memory index.
    /// Runs retention GC after loading. Returns the number of events loaded.
    pub(crate) fn recover_from_jsonl(&mut self, path: &Path) -> usize {
        let events = match super::store::jsonl::read_all_events(path) {
            Ok(evts) => evts,
            Err(_) => return 0,
        };
        let cap = super::governance::MAX_INDEX_EVENTS;
        let skip = events.len().saturating_sub(cap);
        let mut count: usize = 0;
        for event in events.into_iter().skip(skip) {
            self.index.insert(event);
            count += 1;
        }
        // Run retention GC on recovered events.
        let now_ts = super::types::iso_timestamp();
        let deprecated = super::governance::run_gc(
            &mut self.index,
            super::governance::GovernanceConfig::default().retention,
            &now_ts,
        );
        count.saturating_sub(deprecated)
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
    #[allow(
        dead_code,
        reason = "Retention for upcoming memory-ingest metrics/status reporting surfaces."
    )]
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

impl Drop for MemoryIngestor {
    fn drop(&mut self) {
        // Flush remaining buffered events on shutdown.
        self.flush_buffer();
    }
}

/// Strip ANSI escape sequences from text, returning only visible content.
fn strip_ansi(text: &str) -> String {
    crate::ansi::strip_ansi(text)
}

/// Returns true if text is noise that shouldn't be stored as memory.
/// Noise includes: whitespace-only, very short strings, pure control characters.
fn is_noise(text: &str) -> bool {
    let trimmed = text.trim();
    if trimmed.len() < MIN_TEXT_LEN {
        return true;
    }
    // Skip strings that are only non-printable / control chars after stripping.
    if trimmed.chars().all(|c| c.is_control() || c == '\x1b') {
        return true;
    }
    false
}

fn merge_topic_tags(explicit: &[&str], text: &str) -> Vec<String> {
    let mut merged = Vec::new();
    for tag in explicit {
        push_unique_normalized(&mut merged, normalize_topic_tag(tag), MAX_TOPIC_TAGS, false);
    }
    for tag in extract_topic_tags(text) {
        push_unique_normalized(&mut merged, Some(tag), MAX_TOPIC_TAGS, false);
    }
    merged
}

fn merge_task_refs(explicit: &[&str], text: &str) -> Vec<String> {
    let mut merged = Vec::new();
    for task in explicit {
        push_unique_normalized(&mut merged, normalize_task_ref(task), MAX_TASK_REFS, false);
    }
    for task in extract_task_refs(text) {
        push_unique_normalized(&mut merged, Some(task), MAX_TASK_REFS, false);
    }
    merged
}

fn merge_entities(explicit: &[&str], text: &str) -> Vec<String> {
    let mut merged = Vec::new();
    for entity in explicit {
        push_unique_normalized(&mut merged, normalize_entity(entity), MAX_ENTITIES, true);
    }
    for entity in extract_entities(text) {
        push_unique_normalized(&mut merged, Some(entity), MAX_ENTITIES, true);
    }
    merged
}

fn push_unique_normalized(
    values: &mut Vec<String>,
    candidate: Option<String>,
    limit: usize,
    case_sensitive: bool,
) {
    let Some(candidate) = candidate else {
        return;
    };
    if values.len() >= limit {
        return;
    }
    let already_present = values.iter().any(|existing| {
        if case_sensitive {
            existing == &candidate
        } else {
            existing.eq_ignore_ascii_case(&candidate)
        }
    });
    if !already_present {
        values.push(candidate);
    }
}

fn extract_topic_tags(text: &str) -> Vec<String> {
    let lower = text.to_ascii_lowercase();
    let mut tags = Vec::new();
    maybe_add_topic(
        &mut tags,
        "memory",
        &lower,
        &[
            "memory",
            "boot pack",
            "task pack",
            "session handoff",
            "survival index",
        ],
    );
    maybe_add_topic(
        &mut tags,
        "rust",
        &lower,
        &["rust", "cargo", ".rs", "cargo.toml"],
    );
    maybe_add_topic(
        &mut tags,
        "python",
        &lower,
        &["python", "pytest", "pyqt", ".py", "pip "],
    );
    maybe_add_topic(
        &mut tags,
        "testing",
        &lower,
        &["test", "tests", "pytest", "unittest", "cargo test"],
    );
    maybe_add_topic(
        &mut tags,
        "docs",
        &lower,
        &["readme", "docs", "markdown", ".md"],
    );
    maybe_add_topic(
        &mut tags,
        "git",
        &lower,
        &[
            "git", "branch", "commit", "diff", "merge", "worktree", "rebase",
        ],
    );
    maybe_add_topic(
        &mut tags,
        "review",
        &lower,
        &["review", "approval", "approve", "deny", "review-channel"],
    );
    maybe_add_topic(
        &mut tags,
        "ci",
        &lower,
        &["github actions", "workflow", "ci", "checks", "pipeline"],
    );
    tags
}

fn maybe_add_topic(tags: &mut Vec<String>, topic: &str, text: &str, keywords: &[&str]) {
    if tags.len() >= MAX_TOPIC_TAGS || tags.iter().any(|existing| existing == topic) {
        return;
    }
    if keywords.iter().any(|keyword| text.contains(keyword)) {
        tags.push(topic.to_string());
    }
}

fn extract_task_refs(text: &str) -> Vec<String> {
    let bytes = text.as_bytes();
    let mut refs = Vec::new();
    let mut i = 0;
    while i + 3 < bytes.len() && refs.len() < MAX_TASK_REFS {
        let previous_is_boundary = i == 0 || !is_task_ref_char(bytes[i - 1]);
        if previous_is_boundary
            && bytes[i].eq_ignore_ascii_case(&b'm')
            && bytes[i + 1].eq_ignore_ascii_case(&b'p')
            && bytes[i + 2] == b'-'
        {
            let start = i + 3;
            let mut end = start;
            while end < bytes.len() && bytes[end].is_ascii_digit() {
                end += 1;
            }
            let next_is_boundary = end == bytes.len() || !is_task_ref_char(bytes[end]);
            if end > start && next_is_boundary {
                push_unique_normalized(
                    &mut refs,
                    Some(format!("MP-{}", &text[start..end])),
                    MAX_TASK_REFS,
                    false,
                );
                i = end;
                continue;
            }
        }
        i += 1;
    }
    refs
}

fn is_task_ref_char(byte: u8) -> bool {
    byte.is_ascii_alphanumeric() || byte == b'-'
}

fn extract_entities(text: &str) -> Vec<String> {
    let mut entities = Vec::new();
    for raw in text.split_whitespace() {
        if entities.len() >= MAX_ENTITIES {
            break;
        }
        push_unique_normalized(&mut entities, normalize_entity(raw), MAX_ENTITIES, true);
    }
    entities
}

fn normalize_topic_tag(tag: &str) -> Option<String> {
    let trimmed = trim_metadata_token(tag);
    if trimmed.is_empty() {
        return None;
    }
    Some(trimmed.to_ascii_lowercase())
}

fn normalize_task_ref(task: &str) -> Option<String> {
    let trimmed = trim_metadata_token(task);
    let digits = trimmed.to_ascii_lowercase();
    let suffix = digits.strip_prefix("mp-")?;
    if suffix.is_empty() || !suffix.chars().all(|ch| ch.is_ascii_digit()) {
        return None;
    }
    Some(format!("MP-{suffix}"))
}

fn normalize_entity(entity: &str) -> Option<String> {
    let trimmed = trim_entity_token(entity);
    if trimmed.is_empty() || trimmed.contains("://") {
        return None;
    }
    let candidate = trimmed
        .split('#')
        .next()
        .unwrap_or(trimmed)
        .trim_end_matches(':');
    if candidate.is_empty() || !looks_like_entity(candidate) {
        return None;
    }
    Some(candidate.to_string())
}

fn trim_metadata_token(value: &str) -> &str {
    value.trim_matches(|ch: char| {
        !ch.is_ascii_alphanumeric() && !matches!(ch, '-' | '_' | '/' | '.')
    })
}

fn trim_entity_token(value: &str) -> &str {
    value.trim_matches(|ch: char| {
        !ch.is_ascii_alphanumeric() && !matches!(ch, '/' | '.' | '_' | '-')
    })
}

fn looks_like_entity(candidate: &str) -> bool {
    const FILE_EXTENSIONS: &[&str] = &[
        ".rs", ".py", ".md", ".json", ".toml", ".yaml", ".yml", ".txt", ".sh",
    ];
    let lower = candidate.to_ascii_lowercase();
    candidate.contains('/') || FILE_EXTENSIONS.iter().any(|ext| lower.ends_with(ext))
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
    fn ingest_transcript_extracts_task_topic_and_entity_metadata() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        ing.ingest_transcript(
            "Review MP-230 in rust/src/bin/voiceterm/memory/ingest.rs before updating dev/active/memory_studio.md",
        );

        let recent = ing.index().recent(1);
        assert_eq!(recent[0].task_refs, vec!["MP-230".to_string()]);
        assert!(recent[0].topic_tags.contains(&"review".to_string()));
        assert!(recent[0].topic_tags.contains(&"rust".to_string()));
        assert!(recent[0].topic_tags.contains(&"memory".to_string()));
        assert!(recent[0].topic_tags.contains(&"docs".to_string()));
        assert!(recent[0]
            .entities
            .contains(&"rust/src/bin/voiceterm/memory/ingest.rs".to_string()));
        assert!(recent[0]
            .entities
            .contains(&"dev/active/memory_studio.md".to_string()));
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
    fn ingest_event_raw_merges_explicit_and_extracted_metadata() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        ing.ingest_event_raw(
            EventSource::PtyInput,
            EventType::CommandRun,
            EventRole::User,
            "Review MP-231 in rust/src/bin/voiceterm/memory/context_pack.rs",
            0.8,
            &["review", "docs"],
            &["mp-230"],
            &["dev/active/memory_studio.md"],
        );

        let event = ing.index().recent(1)[0].clone();
        assert_eq!(
            event.task_refs,
            vec!["MP-230".to_string(), "MP-231".to_string()]
        );
        assert!(event.topic_tags.contains(&"review".to_string()));
        assert!(event.topic_tags.contains(&"docs".to_string()));
        assert!(event.topic_tags.contains(&"rust".to_string()));
        assert!(event
            .entities
            .contains(&"dev/active/memory_studio.md".to_string()));
        assert!(event
            .entities
            .contains(&"rust/src/bin/voiceterm/memory/context_pack.rs".to_string()));
    }

    #[test]
    fn extracted_metadata_powers_task_and_topic_queries() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        ing.ingest_user_input(
            "cargo test rust/src/bin/voiceterm/memory/ingest.rs for MP-230 memory",
        );

        assert_eq!(ing.index().by_task("MP-230", 10).len(), 1);
        assert_eq!(ing.index().by_topic("rust", 10).len(), 1);
        assert_eq!(ing.index().by_topic("testing", 10).len(), 1);
        assert_eq!(ing.index().by_topic("memory", 10).len(), 1);
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
            writer_ing.flush();
        }

        let mut reader_ing = make_ingestor(MemoryMode::Assist);
        let recovered = reader_ing.recover_from_jsonl(&path);
        assert_eq!(recovered, 3);
        assert_eq!(reader_ing.index().len(), 3);

        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn test_recover_caps_at_max_index() {
        let unique = format!(
            "voiceterm-recover-cap-{}-{}.jsonl",
            std::process::id(),
            generate_event_id()
        );
        let path = std::env::temp_dir().join(unique);
        let cap = super::super::governance::MAX_INDEX_EVENTS;

        {
            let mut writer = super::super::store::jsonl::JsonlWriter::open(&path)
                .unwrap_or_else(|err| panic!("open writer failed: {err}"));
            for i in 0..(cap + 5) {
                let event = MemoryEvent {
                    event_id: generate_event_id(),
                    session_id: "sess_cap".to_string(),
                    project_id: "proj_cap".to_string(),
                    // Keep timestamps safely outside GC cutoff so this test
                    // only validates max-index capping behavior.
                    ts: "2999-01-01T00:00:00.000Z".to_string(),
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
            writer.flush().unwrap();
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
            ing.flush();
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

    #[test]
    fn ansi_escape_sequences_are_stripped() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        // Simulate PTY output with ANSI color codes.
        ing.ingest_assistant_output("\x1b[32mHello World\x1b[0m");
        assert_eq!(ing.events_ingested(), 1);
        let recent = ing.index().recent(1);
        assert_eq!(recent[0].text, "Hello World");
    }

    #[test]
    fn pure_escape_sequences_are_dropped() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        // Simulate cursor-move-only PTY output.
        ing.ingest_assistant_output("\x1b[?2004h\x1b[>7u\x1b[?1004h");
        assert_eq!(ing.events_ingested(), 0);
    }

    #[test]
    fn short_noise_is_dropped() {
        let mut ing = make_ingestor(MemoryMode::Assist);
        ing.ingest_user_input("x");
        assert_eq!(ing.events_ingested(), 0);
    }

    #[test]
    fn strip_ansi_removes_color_codes() {
        let input = "\x1b[1m\x1b[38;2;202;202;202mPlanning\x1b[0m";
        let result = strip_ansi(input);
        assert_eq!(result, "Planning");
    }

    #[test]
    fn is_noise_detects_empty_after_strip() {
        assert!(is_noise(""));
        assert!(is_noise("  "));
        assert!(is_noise("x"));
        assert!(!is_noise("hello"));
        assert!(!is_noise("git status"));
    }
}
