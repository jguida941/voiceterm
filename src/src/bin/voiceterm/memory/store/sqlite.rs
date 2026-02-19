//! SQLite index for fast memory event lookup by topic/task/time/source.
//!
//! Uses the schema from `memory::schema::create_tables_sql()`.
//! All SQL uses parameterized queries (no raw string interpolation).
//!
//! NOTE: This module provides the schema and index contract but defers
//! actual SQLite runtime linkage to a future iteration. The current
//! implementation uses an in-memory index backed by vectors for the
//! initial buildable slice. The SQL schema is fully specified and tested
//! at the string level so the migration path is ready.

use std::collections::HashMap;

use super::super::types::{EventSource, EventType, MemoryEvent, RetrievalState};

/// In-memory event index that mirrors the SQLite schema contract.
/// This serves as the queryable store for the initial iteration.
#[derive(Debug)]
pub(crate) struct MemoryIndex {
    events: Vec<MemoryEvent>,
    topic_index: HashMap<String, Vec<usize>>,
    task_index: HashMap<String, Vec<usize>>,
}

impl MemoryIndex {
    pub(crate) fn new() -> Self {
        Self {
            events: Vec::new(),
            topic_index: HashMap::new(),
            task_index: HashMap::new(),
        }
    }

    /// Insert an event into the index.
    pub(crate) fn insert(&mut self, event: MemoryEvent) {
        let idx = self.events.len();
        for tag in &event.topic_tags {
            self.topic_index
                .entry(tag.to_ascii_lowercase())
                .or_default()
                .push(idx);
        }
        for task in &event.task_refs {
            self.task_index
                .entry(task.to_ascii_lowercase())
                .or_default()
                .push(idx);
        }
        self.events.push(event);
    }

    /// Total number of indexed events.
    pub(crate) fn len(&self) -> usize {
        self.events.len()
    }

    /// Whether the index is empty.
    #[allow(dead_code)]
    pub(crate) fn is_empty(&self) -> bool {
        self.events.is_empty()
    }

    /// Retrieve the N most recent eligible events, newest first.
    pub(crate) fn recent(&self, n: usize) -> Vec<&MemoryEvent> {
        self.events
            .iter()
            .rev()
            .filter(|e| e.retrieval_state == RetrievalState::Eligible)
            .take(n)
            .collect()
    }

    /// Retrieve events by topic tag (case-insensitive), newest first.
    pub(crate) fn by_topic(&self, topic: &str, n: usize) -> Vec<&MemoryEvent> {
        let key = topic.to_ascii_lowercase();
        let Some(indices) = self.topic_index.get(&key) else {
            return Vec::new();
        };
        indices
            .iter()
            .rev()
            .filter_map(|&idx| {
                let event = &self.events[idx];
                if event.retrieval_state == RetrievalState::Eligible {
                    Some(event)
                } else {
                    None
                }
            })
            .take(n)
            .collect()
    }

    /// Retrieve events by task reference (case-insensitive), newest first.
    pub(crate) fn by_task(&self, task: &str, n: usize) -> Vec<&MemoryEvent> {
        let key = task.to_ascii_lowercase();
        let Some(indices) = self.task_index.get(&key) else {
            return Vec::new();
        };
        indices
            .iter()
            .rev()
            .filter_map(|&idx| {
                let event = &self.events[idx];
                if event.retrieval_state == RetrievalState::Eligible {
                    Some(event)
                } else {
                    None
                }
            })
            .take(n)
            .collect()
    }

    /// Full-text search across event text (simple case-insensitive substring).
    /// Returns matching events newest-first, capped at `n`.
    pub(crate) fn search_text(&self, query: &str, n: usize) -> Vec<&MemoryEvent> {
        if query.is_empty() {
            return self.recent(n);
        }
        let lower_query = query.to_ascii_lowercase();
        self.events
            .iter()
            .rev()
            .filter(|e| {
                e.retrieval_state == RetrievalState::Eligible
                    && e.text.to_ascii_lowercase().contains(&lower_query)
            })
            .take(n)
            .collect()
    }

    /// Retrieve events within a time range (ISO string comparison).
    pub(crate) fn timeline(
        &self,
        start: &str,
        end: &str,
        n: usize,
    ) -> Vec<&MemoryEvent> {
        self.events
            .iter()
            .rev()
            .filter(|e| {
                e.retrieval_state == RetrievalState::Eligible
                    && e.ts.as_str() >= start
                    && e.ts.as_str() <= end
            })
            .take(n)
            .collect()
    }

    /// Update retrieval state for an event by ID.
    pub(crate) fn set_retrieval_state(&mut self, event_id: &str, state: RetrievalState) -> bool {
        for event in &mut self.events {
            if event.event_id == event_id {
                event.retrieval_state = state;
                return true;
            }
        }
        false
    }

    /// Get an event by ID.
    pub(crate) fn get_by_id(&self, event_id: &str) -> Option<&MemoryEvent> {
        self.events.iter().find(|e| e.event_id == event_id)
    }

    /// Return all events (for export/pack generation), newest first.
    pub(crate) fn all_eligible(&self) -> Vec<&MemoryEvent> {
        self.events
            .iter()
            .rev()
            .filter(|e| e.retrieval_state == RetrievalState::Eligible)
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::memory::types::*;

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

    fn event_with_tags(id: &str, text: &str, topics: &[&str], tasks: &[&str]) -> MemoryEvent {
        let mut e = sample_event(id, text);
        e.topic_tags = topics.iter().map(|s| s.to_string()).collect();
        e.task_refs = tasks.iter().map(|s| s.to_string()).collect();
        e
    }

    #[test]
    fn empty_index() {
        let idx = MemoryIndex::new();
        assert!(idx.is_empty());
        assert_eq!(idx.len(), 0);
        assert!(idx.recent(10).is_empty());
    }

    #[test]
    fn insert_and_recent() {
        let mut idx = MemoryIndex::new();
        idx.insert(sample_event("evt_1", "first"));
        idx.insert(sample_event("evt_2", "second"));
        idx.insert(sample_event("evt_3", "third"));

        let recent = idx.recent(2);
        assert_eq!(recent.len(), 2);
        assert_eq!(recent[0].event_id, "evt_3"); // newest first
        assert_eq!(recent[1].event_id, "evt_2");
    }

    #[test]
    fn by_topic_filters() {
        let mut idx = MemoryIndex::new();
        idx.insert(event_with_tags("evt_1", "alpha", &["rust"], &[]));
        idx.insert(event_with_tags("evt_2", "beta", &["python"], &[]));
        idx.insert(event_with_tags("evt_3", "gamma", &["rust"], &[]));

        let rust_events = idx.by_topic("rust", 10);
        assert_eq!(rust_events.len(), 2);
        assert_eq!(rust_events[0].event_id, "evt_3");
        assert_eq!(rust_events[1].event_id, "evt_1");

        let python_events = idx.by_topic("python", 10);
        assert_eq!(python_events.len(), 1);
    }

    #[test]
    fn by_topic_case_insensitive() {
        let mut idx = MemoryIndex::new();
        idx.insert(event_with_tags("evt_1", "test", &["Rust"], &[]));
        let results = idx.by_topic("rust", 10);
        assert_eq!(results.len(), 1);
    }

    #[test]
    fn by_task_filters() {
        let mut idx = MemoryIndex::new();
        idx.insert(event_with_tags("evt_1", "alpha", &[], &["MP-230"]));
        idx.insert(event_with_tags("evt_2", "beta", &[], &["MP-231"]));
        idx.insert(event_with_tags("evt_3", "gamma", &[], &["MP-230"]));

        let results = idx.by_task("MP-230", 10);
        assert_eq!(results.len(), 2);
        assert_eq!(results[0].event_id, "evt_3");
    }

    #[test]
    fn search_text_substring() {
        let mut idx = MemoryIndex::new();
        idx.insert(sample_event("evt_1", "hello world"));
        idx.insert(sample_event("evt_2", "goodbye world"));
        idx.insert(sample_event("evt_3", "hello again"));

        let results = idx.search_text("hello", 10);
        assert_eq!(results.len(), 2);
        assert_eq!(results[0].event_id, "evt_3"); // newest first
    }

    #[test]
    fn search_text_empty_returns_recent() {
        let mut idx = MemoryIndex::new();
        idx.insert(sample_event("evt_1", "one"));
        idx.insert(sample_event("evt_2", "two"));

        let results = idx.search_text("", 10);
        assert_eq!(results.len(), 2);
    }

    #[test]
    fn set_retrieval_state_quarantines_event() {
        let mut idx = MemoryIndex::new();
        idx.insert(sample_event("evt_1", "visible"));
        idx.insert(sample_event("evt_2", "also visible"));

        assert!(idx.set_retrieval_state("evt_1", RetrievalState::Quarantined));
        let recent = idx.recent(10);
        assert_eq!(recent.len(), 1);
        assert_eq!(recent[0].event_id, "evt_2");
    }

    #[test]
    fn set_retrieval_state_returns_false_for_unknown_id() {
        let mut idx = MemoryIndex::new();
        assert!(!idx.set_retrieval_state("nonexistent", RetrievalState::Deprecated));
    }

    #[test]
    fn get_by_id_finds_event() {
        let mut idx = MemoryIndex::new();
        idx.insert(sample_event("evt_1", "findme"));
        let found = idx.get_by_id("evt_1");
        assert!(found.is_some());
        assert_eq!(found.unwrap().text, "findme");
    }

    #[test]
    fn get_by_id_returns_none_for_unknown() {
        let idx = MemoryIndex::new();
        assert!(idx.get_by_id("ghost").is_none());
    }

    #[test]
    fn timeline_filters_by_range() {
        let mut idx = MemoryIndex::new();
        let mut e1 = sample_event("evt_1", "early");
        e1.ts = "2026-02-19T10:00:00.000Z".to_string();
        let mut e2 = sample_event("evt_2", "mid");
        e2.ts = "2026-02-19T12:00:00.000Z".to_string();
        let mut e3 = sample_event("evt_3", "late");
        e3.ts = "2026-02-19T14:00:00.000Z".to_string();

        idx.insert(e1);
        idx.insert(e2);
        idx.insert(e3);

        let results = idx.timeline(
            "2026-02-19T11:00:00.000Z",
            "2026-02-19T13:00:00.000Z",
            10,
        );
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].event_id, "evt_2");
    }

    #[test]
    fn all_eligible_excludes_quarantined() {
        let mut idx = MemoryIndex::new();
        idx.insert(sample_event("evt_1", "one"));
        idx.insert(sample_event("evt_2", "two"));
        idx.set_retrieval_state("evt_1", RetrievalState::Quarantined);

        let all = idx.all_eligible();
        assert_eq!(all.len(), 1);
        assert_eq!(all[0].event_id, "evt_2");
    }
}
