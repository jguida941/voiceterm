//! Deterministic retrieval APIs for the memory subsystem (MP-231).
//!
//! Provides topic/task/time/text queries with provenance-tagged results
//! and bounded token budgets.

use std::collections::HashSet;

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
#[derive(Debug, Clone, PartialEq, Eq)]
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

/// Signal describing the retrieval context for strategy routing.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum ContextSignal {
    SessionStart { gap_seconds: u64 },
    UserQuery { text: String },
    ContextBudgetWarning,
    Handoff { source: String },
    UserSelection,
}

impl ContextSignal {
    #[must_use = "signal label should be consumed by callers"]
    pub(crate) fn label(&self) -> &'static str {
        match self {
            ContextSignal::SessionStart { .. } => "session_start",
            ContextSignal::UserQuery { .. } => "user_query",
            ContextSignal::ContextBudgetWarning => "context_budget_warning",
            ContextSignal::Handoff { .. } => "handoff",
            ContextSignal::UserSelection => "user_selection",
        }
    }
}

/// Retrieval strategy selected from a context signal.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ContextStrategy {
    Rag,
    BootPack,
    SurvivalIndex,
    TaskPack,
    Hybrid,
}

impl ContextStrategy {
    #[must_use = "strategy label should be consumed by callers"]
    pub(crate) fn label(self) -> &'static str {
        match self {
            ContextStrategy::Rag => "rag",
            ContextStrategy::BootPack => "boot_pack",
            ContextStrategy::SurvivalIndex => "survival_index",
            ContextStrategy::TaskPack => "task_pack",
            ContextStrategy::Hybrid => "hybrid",
        }
    }
}

/// Execute a retrieval query against the memory index.
/// Returns scored results with provenance, ordered by relevance.
#[must_use = "retrieval results should be consumed by callers"]
pub(crate) fn execute_query<'a>(
    index: &'a MemoryIndex,
    query: &RetrievalQuery,
) -> Vec<RetrievalResult<'a>> {
    rank_events(fetch_events(index, query))
}

/// Select retrieval strategy from context signal.
#[must_use = "strategy output should be consumed by callers"]
pub(crate) fn select_strategy(signal: &ContextSignal) -> ContextStrategy {
    match signal {
        ContextSignal::SessionStart { gap_seconds } if *gap_seconds > 3600 => {
            ContextStrategy::Hybrid
        }
        ContextSignal::SessionStart { .. } => ContextStrategy::BootPack,
        ContextSignal::UserQuery { text } if looks_like_task_ref(text) => ContextStrategy::TaskPack,
        ContextSignal::UserQuery { .. } => ContextStrategy::Rag,
        ContextSignal::ContextBudgetWarning => ContextStrategy::SurvivalIndex,
        ContextSignal::Handoff { .. } => ContextStrategy::Hybrid,
        ContextSignal::UserSelection => ContextStrategy::TaskPack,
    }
}

/// Build the deterministic query plan for a given query and context signal.
#[must_use = "query plans should be consumed by callers"]
pub(crate) fn build_query_plan(
    query: &RetrievalQuery,
    signal: &ContextSignal,
) -> Vec<RetrievalQuery> {
    let strategy = select_strategy(signal);
    match strategy {
        ContextStrategy::Rag | ContextStrategy::TaskPack => vec![query.clone()],
        ContextStrategy::BootPack => vec![RetrievalQuery::Recent(query_limit(query))],
        ContextStrategy::SurvivalIndex => vec![RetrievalQuery::Recent(
            query_limit(query).max(DEFAULT_RETRIEVAL_LIMIT),
        )],
        ContextStrategy::Hybrid => build_hybrid_plan(query),
    }
}

/// Execute retrieval with strategy routing for context-sensitive memory recovery.
#[must_use = "retrieval results should be consumed by callers"]
pub(crate) fn execute_query_with_signal<'a>(
    index: &'a MemoryIndex,
    query: &RetrievalQuery,
    signal: &ContextSignal,
) -> Vec<RetrievalResult<'a>> {
    let mut merged_events = Vec::new();
    let mut seen_event_ids: HashSet<String> = HashSet::new();
    for planned_query in build_query_plan(query, signal) {
        for event in fetch_events(index, &planned_query) {
            if seen_event_ids.insert(event.event_id.clone()) {
                merged_events.push(event);
            }
        }
    }
    rank_events(merged_events)
}

#[must_use = "query labels should be consumed by callers"]
pub(crate) fn describe_query(query: &RetrievalQuery) -> String {
    match query {
        RetrievalQuery::Recent(limit) => format!("recent:{limit}"),
        RetrievalQuery::ByTopic { topic, limit } => format!("topic:{topic}:{limit}"),
        RetrievalQuery::ByTask { task, limit } => format!("task:{task}:{limit}"),
        RetrievalQuery::TextSearch { query, limit } => format!("text:{query}:{limit}"),
        RetrievalQuery::Timeline { start, end, limit } => {
            format!("timeline:{start}..{end}:{limit}")
        }
    }
}

fn build_hybrid_plan(query: &RetrievalQuery) -> Vec<RetrievalQuery> {
    let recent_limit = hybrid_recent_limit(query);
    if matches!(query, RetrievalQuery::Recent(_)) {
        return vec![RetrievalQuery::Recent(query_limit(query).max(recent_limit))];
    }
    vec![query.clone(), RetrievalQuery::Recent(recent_limit)]
}

fn hybrid_recent_limit(query: &RetrievalQuery) -> usize {
    query_limit(query).saturating_add(DEFAULT_RETRIEVAL_LIMIT / 2)
}

fn query_limit(query: &RetrievalQuery) -> usize {
    match query {
        RetrievalQuery::Recent(limit) => *limit,
        RetrievalQuery::ByTopic { limit, .. } => *limit,
        RetrievalQuery::ByTask { limit, .. } => *limit,
        RetrievalQuery::TextSearch { limit, .. } => *limit,
        RetrievalQuery::Timeline { limit, .. } => *limit,
    }
}

fn fetch_events<'a>(index: &'a MemoryIndex, query: &RetrievalQuery) -> Vec<&'a MemoryEvent> {
    match query {
        RetrievalQuery::Recent(n) => index.recent(*n),
        RetrievalQuery::ByTopic { topic, limit } => index.by_topic(topic, *limit),
        RetrievalQuery::ByTask { task, limit } => index.by_task(task, *limit),
        RetrievalQuery::TextSearch { query, limit } => index.search_text(query, *limit),
        RetrievalQuery::Timeline { start, end, limit } => index.timeline(start, end, *limit),
    }
}

fn rank_events<'a>(events: Vec<&'a MemoryEvent>) -> Vec<RetrievalResult<'a>> {
    events
        .into_iter()
        .enumerate()
        .map(|(rank, event)| RetrievalResult {
            event,
            score: score_event(event),
            rank,
        })
        .collect()
}

fn score_event(event: &MemoryEvent) -> f64 {
    // v1 scoring: recency-weighted importance.
    // Score = 0.40 * importance + 0.20 * recency_decay + 0.25 * text_relevance + 0.15 * confidence
    // Simplified for initial iteration: importance + confidence decay.
    (event.importance * 0.55 + event.confidence * 0.45).clamp(0.0, 1.0)
}

fn looks_like_task_ref(value: &str) -> bool {
    let normalized = value.trim();
    normalized.len() > 3
        && normalized[..3].eq_ignore_ascii_case("mp-")
        && normalized[3..].chars().all(|ch| ch.is_ascii_digit())
}

/// Estimate token count for a text string (simple word-based approximation).
#[must_use = "token estimate should be used for retrieval budgeting"]
pub(crate) fn estimate_tokens(text: &str) -> usize {
    // Rough approximation: ~4 chars per token for English text.
    let len = text.len();
    len / 4 + usize::from(!len.is_multiple_of(4))
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
    fn strategy_selection_maps_context_signals() {
        assert_eq!(
            select_strategy(&ContextSignal::SessionStart { gap_seconds: 30 }),
            ContextStrategy::BootPack
        );
        assert_eq!(
            select_strategy(&ContextSignal::SessionStart { gap_seconds: 7200 }),
            ContextStrategy::Hybrid
        );
        assert_eq!(
            select_strategy(&ContextSignal::UserQuery {
                text: "MP-231".to_string(),
            }),
            ContextStrategy::TaskPack
        );
        assert_eq!(
            select_strategy(&ContextSignal::UserQuery {
                text: "memory retrieval".to_string(),
            }),
            ContextStrategy::Rag
        );
        assert_eq!(
            select_strategy(&ContextSignal::ContextBudgetWarning),
            ContextStrategy::SurvivalIndex
        );
        assert_eq!(
            select_strategy(&ContextSignal::Handoff {
                source: "review".to_string(),
            }),
            ContextStrategy::Hybrid
        );
        assert_eq!(
            select_strategy(&ContextSignal::UserSelection),
            ContextStrategy::TaskPack
        );
    }

    #[test]
    fn build_query_plan_for_hybrid_adds_recent_fallback() {
        let plan = build_query_plan(
            &RetrievalQuery::ByTask {
                task: "MP-231".to_string(),
                limit: 12,
            },
            &ContextSignal::Handoff {
                source: "review".to_string(),
            },
        );
        assert_eq!(plan.len(), 2);
        assert!(matches!(plan[0], RetrievalQuery::ByTask { .. }));
        assert!(matches!(plan[1], RetrievalQuery::Recent(_)));
    }

    #[test]
    fn execute_query_with_signal_hybrid_merges_and_deduplicates() {
        let mut idx = MemoryIndex::new();
        let mut evt1 = sample_event("evt_1", "first event about rust", 0.3);
        evt1.task_refs = vec!["MP-230".to_string()];
        let mut evt2 = sample_event("evt_2", "second event about python", 0.7);
        evt2.task_refs = vec!["MP-231".to_string()];
        let mut evt3 = sample_event("evt_3", "third event about rust memory", 0.9);
        evt3.task_refs = vec!["MP-232".to_string()];
        idx.insert(evt1);
        idx.insert(evt2);
        idx.insert(evt3);

        let results = execute_query_with_signal(
            &idx,
            &RetrievalQuery::ByTask {
                task: "MP-231".to_string(),
                limit: 1,
            },
            &ContextSignal::Handoff {
                source: "review".to_string(),
            },
        );

        assert!(results.len() >= 2);
        assert_eq!(results[0].event.event_id, "evt_2");
        let unique: HashSet<String> = results
            .iter()
            .map(|row| row.event.event_id.clone())
            .collect();
        assert_eq!(
            unique.len(),
            results.len(),
            "hybrid results should be deduplicated"
        );
    }

    #[test]
    fn execute_query_with_signal_survival_index_falls_back_to_recent() {
        let idx = populated_index();
        let results = execute_query_with_signal(
            &idx,
            &RetrievalQuery::ByTask {
                task: "MP-999".to_string(),
                limit: 2,
            },
            &ContextSignal::ContextBudgetWarning,
        );
        assert!(!results.is_empty());
        assert_eq!(results[0].event.event_id, "evt_3");
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
