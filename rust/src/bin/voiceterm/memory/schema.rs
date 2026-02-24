//! Schema validation for memory events and migration helpers.
//!
//! Ensures all events conform to the canonical schema before storage.

use super::types::{MemoryEvent, SCHEMA_VERSION};

/// Validate that a memory event has the required fields populated.
/// Returns a list of validation errors (empty = valid).
pub(crate) fn validate_event(event: &MemoryEvent) -> Vec<String> {
    let mut errors = Vec::new();

    if event.event_id.is_empty() {
        errors.push("event_id is empty".to_string());
    }
    if event.session_id.is_empty() {
        errors.push("session_id is empty".to_string());
    }
    if event.project_id.is_empty() {
        errors.push("project_id is empty".to_string());
    }
    if event.ts.is_empty() {
        errors.push("ts (timestamp) is empty".to_string());
    }
    if event.text.trim().is_empty() {
        errors.push("text is empty or whitespace-only".to_string());
    }
    if !(0.0..=1.0).contains(&event.importance) {
        errors.push(format!(
            "importance {} out of [0.0, 1.0] range",
            event.importance
        ));
    }
    if !(0.0..=1.0).contains(&event.confidence) {
        errors.push(format!(
            "confidence {} out of [0.0, 1.0] range",
            event.confidence
        ));
    }

    errors
}

/// Check whether a stored schema version is compatible with the current runtime.
pub(crate) fn is_schema_compatible(stored_version: u32) -> bool {
    stored_version <= SCHEMA_VERSION
}

/// SQL statements for creating the initial memory index tables.
pub(crate) fn create_tables_sql() -> &'static str {
    r#"
CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_meta (key, value)
    VALUES ('schema_version', '1');

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at   TEXT
);

CREATE TABLE IF NOT EXISTS events (
    event_id        TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    project_id      TEXT NOT NULL,
    ts              TEXT NOT NULL,
    source          TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    role            TEXT NOT NULL,
    text            TEXT NOT NULL,
    importance      REAL NOT NULL DEFAULT 0.5,
    confidence      REAL NOT NULL DEFAULT 1.0,
    retrieval_state TEXT NOT NULL DEFAULT 'eligible',
    hash            TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_retrieval ON events(retrieval_state);

CREATE TABLE IF NOT EXISTS topics (
    topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS event_topics (
    event_id TEXT NOT NULL,
    topic_id INTEGER NOT NULL,
    PRIMARY KEY (event_id, topic_id)
);

CREATE TABLE IF NOT EXISTS entities (
    entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS event_entities (
    event_id  TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    PRIMARY KEY (event_id, entity_id)
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS event_tasks (
    event_id TEXT NOT NULL,
    task_id  INTEGER NOT NULL,
    PRIMARY KEY (event_id, task_id)
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    TEXT NOT NULL,
    kind        TEXT NOT NULL,
    reference   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_artifacts_event ON artifacts(event_id);

CREATE TABLE IF NOT EXISTS action_runs (
    run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id   TEXT NOT NULL,
    event_id    TEXT,
    command     TEXT NOT NULL,
    exit_code   INTEGER,
    approved_by TEXT NOT NULL,
    ts          TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS event_fts USING fts5(
    event_id,
    text,
    content='events',
    content_rowid='rowid'
);
    "#
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::memory::types::*;

    fn valid_event() -> MemoryEvent {
        MemoryEvent {
            event_id: "evt_test_001".to_string(),
            session_id: "sess_test_001".to_string(),
            project_id: "test_project".to_string(),
            ts: "2026-02-19T12:00:00.000Z".to_string(),
            source: EventSource::PtyInput,
            event_type: EventType::ChatTurn,
            role: EventRole::User,
            text: "test message".to_string(),
            topic_tags: vec![],
            entities: vec![],
            task_refs: vec![],
            artifacts: vec![],
            importance: 0.5,
            confidence: 0.9,
            retrieval_state: RetrievalState::Eligible,
            hash: None,
        }
    }

    #[test]
    fn valid_event_passes_validation() {
        let errors = validate_event(&valid_event());
        assert!(errors.is_empty(), "unexpected errors: {errors:?}");
    }

    #[test]
    fn empty_event_id_fails() {
        let mut event = valid_event();
        event.event_id = String::new();
        let errors = validate_event(&event);
        assert!(errors.iter().any(|e| e.contains("event_id")));
    }

    #[test]
    fn empty_text_fails() {
        let mut event = valid_event();
        event.text = "   ".to_string();
        let errors = validate_event(&event);
        assert!(errors.iter().any(|e| e.contains("text")));
    }

    #[test]
    fn importance_out_of_range_fails() {
        let mut event = valid_event();
        event.importance = 1.5;
        let errors = validate_event(&event);
        assert!(errors.iter().any(|e| e.contains("importance")));
    }

    #[test]
    fn confidence_out_of_range_fails() {
        let mut event = valid_event();
        event.confidence = -0.1;
        let errors = validate_event(&event);
        assert!(errors.iter().any(|e| e.contains("confidence")));
    }

    #[test]
    fn schema_version_compatibility() {
        assert!(is_schema_compatible(1));
        assert!(!is_schema_compatible(2));
        assert!(is_schema_compatible(0));
    }

    #[test]
    fn create_tables_sql_is_not_empty() {
        let sql = create_tables_sql();
        assert!(sql.contains("CREATE TABLE"));
        assert!(sql.contains("event_fts"));
        assert!(sql.contains("sessions"));
        assert!(sql.contains("events"));
    }
}
