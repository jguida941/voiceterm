//! Storage backends for the memory subsystem.

pub(crate) mod jsonl;
pub(crate) mod sqlite;

#[cfg(test)]
pub(crate) fn sample_event(id: &str, text: &str) -> super::types::MemoryEvent {
    use super::types::{EventRole, EventSource, EventType, MemoryEvent, RetrievalState};

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
