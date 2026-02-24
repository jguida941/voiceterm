//! Deterministic retrieval APIs for the memory subsystem (MP-231).
//!
//! Provides topic/task/time/text queries with provenance-tagged results
//! and bounded token budgets.

use super::store::sqlite::MemoryIndex;
use super::types::MemoryEvent;

/// Maximum results returned by a single retrieval call.
pub(crate) const DEFAULT_RETRIEVAL_LIMIT: usize = 50;

/// A scored retrieval result with provenance metadata.
#[derive(Debug, Clone)]
pub(crate) struct RetrievalResult<'a> {
    pub(crate) event: &'a MemoryEvent,
    pub(crate) score: f64,
    pub(crate) rank: usize,
}

/// Retrieval query types.
#[derive(Debug, Clone)]
pub(crate) enum RetrievalQuery {
    /// Most recent N events.
    Recent(usize),
    /// Events matching a topic tag.
    ByTopic { topic: String, limit: usize },
    /// Events matching a task reference.
    ByTask { task: String, limit: usize },
    /// Full-text search on event text.
    TextSearch { query: String, limit: usize },
    /// Events within a time range (ISO strings).
    Timeline {
        start: String,
        end: String,
        limit: usize,
    },
}

/// Execute a retrieval query against the memory index.
/// Returns scored results with provenance, ordered by relevance.
#[must_use = "retrieval results should be consumed by callers"]
pub(crate) fn execute_query<'a>(
    index: &'a MemoryIndex,
    query: &RetrievalQuery,
) -> Vec<RetrievalResult<'a>> {
    let events: Vec<&MemoryEvent> = match query {
        RetrievalQuery::Recent(n) => index.recent(*n),
        RetrievalQuery::ByTopic { topic, limit } => index.by_topic(topic, *limit),
        RetrievalQuery::ByTask { task, limit } => index.by_task(task, *limit),
        RetrievalQuery::TextSearch { query, limit } => index.search_text(query, *limit),
        RetrievalQuery::Timeline { start, end, limit } => index.timeline(start, end, *limit),
    };

    events
        .into_iter()
        .enumerate()
        .map(|(rank, event)| {
            // v1 scoring: recency-weighted importance.
            // Score = 0.40 * importance + 0.20 * recency_decay + 0.25 * text_relevance + 0.15 * confidence
            // Simplified for initial iteration: importance + confidence decay.
            let score = (event.importance * 0.55 + event.confidence * 0.45).clamp(0.0, 1.0);
            RetrievalResult { event, score, rank }
        })
        .collect()
}

/// Estimate token count for a text string (simple word-based approximation).
#[must_use = "token estimate should be used for retrieval budgeting"]
pub(crate) fn estimate_tokens(text: &str) -> usize {
    // Rough approximation: ~4 chars per token for English text.
    let len = text.len();
    len / 4 + usize::from(len % 4 != 0)
}

/// Trim retrieval results to fit within a token budget.
#[must_use = "budget output should be consumed by callers"]
pub(crate) fn trim_to_budget(
    results: &[RetrievalResult<'_>],
    max_tokens: usize,
) -> (Vec<usize>, usize, usize) {
    let mut included_indices = Vec::new();
    let mut used_tokens = 0;
    let mut trimmed_tokens = 0;

    for (i, result) in results.iter().enumerate() {
        let tokens = estimate_tokens(&result.event.text);
        if used_tokens + tokens <= max_tokens {
            included_indices.push(i);
            used_tokens += tokens;
        } else {
            trimmed_tokens += tokens;
        }
    }

    (included_indices, used_tokens, trimmed_tokens)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::memory::types::*;

    fn sample_event(id: &str, text: &str, importance: f64) -> MemoryEvent {
        MemoryEvent {
            event_id: id.to_string(),
            session_id: "sess_test".to_string(),
            project_id: "proj_test".to_string(),
            ts: "2026-02-19T12:00:00.000Z".to_string(),
            source: EventSource::PtyInput,
            event_type: EventType::ChatTurn,
            role: EventRole::User,
            text: text.to_string(),
            topic_tags: vec!["test".to_string()],
            entities: vec![],
            task_refs: vec!["MP-230".to_string()],
            artifacts: vec![],
            importance,
            confidence: 1.0,
            retrieval_state: RetrievalState::Eligible,
            hash: None,
        }
    }

    fn populated_index() -> MemoryIndex {
        let mut idx = MemoryIndex::new();
        idx.insert(sample_event("evt_1", "first event about rust", 0.3));
        idx.insert(sample_event("evt_2", "second event about python", 0.7));
        idx.insert(sample_event("evt_3", "third event about rust memory", 0.9));
        idx
    }

    #[test]
    fn execute_recent_query() {
        let idx = populated_index();
        let results = execute_query(&idx, &RetrievalQuery::Recent(2));
        assert_eq!(results.len(), 2);
        assert_eq!(results[0].event.event_id, "evt_3");
        assert_eq!(results[0].rank, 0);
    }

    #[test]
    fn execute_topic_query() {
        let idx = populated_index();
        let results = execute_query(
            &idx,
            &RetrievalQuery::ByTopic {
                topic: "test".to_string(),
                limit: 10,
            },
        );
        assert_eq!(results.len(), 3);
    }

    #[test]
    fn execute_task_query() {
        let idx = populated_index();
        let results = execute_query(
            &idx,
            &RetrievalQuery::ByTask {
                task: "MP-230".to_string(),
                limit: 10,
            },
        );
        assert_eq!(results.len(), 3);
    }

    #[test]
    fn execute_text_search() {
        let idx = populated_index();
        let results = execute_query(
            &idx,
            &RetrievalQuery::TextSearch {
                query: "rust".to_string(),
                limit: 10,
            },
        );
        assert_eq!(results.len(), 2);
    }

    #[test]
    fn scores_are_bounded() {
        let idx = populated_index();
        let results = execute_query(&idx, &RetrievalQuery::Recent(10));
        for r in &results {
            assert!(
                r.score >= 0.0 && r.score <= 1.0,
                "score out of range: {}",
                r.score
            );
        }
    }

    #[test]
    fn estimate_tokens_approximation() {
        assert_eq!(estimate_tokens(""), 0);
        assert_eq!(estimate_tokens("word"), 1);
        assert!(estimate_tokens("hello world, this is a test") > 0);
    }

    #[test]
    fn trim_to_budget_respects_limit() {
        let idx = populated_index();
        let results = execute_query(&idx, &RetrievalQuery::Recent(10));

        // Very small budget should include fewer items.
        let (indices, used, trimmed) = trim_to_budget(&results, 10);
        assert!(indices.len() <= results.len());
        assert!(used <= 10);
        assert!(trimmed > 0 || indices.len() == results.len());
    }

    #[test]
    fn trim_to_budget_large_budget_includes_all() {
        let idx = populated_index();
        let results = execute_query(&idx, &RetrievalQuery::Recent(10));
        let (indices, _used, trimmed) = trim_to_budget(&results, 100_000);
        assert_eq!(indices.len(), results.len());
        assert_eq!(trimmed, 0);
    }
}
