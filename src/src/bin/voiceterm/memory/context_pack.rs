//! Context pack generation for AI boot/handoff workflows (MP-232).
//!
//! Produces `context_pack.json` and `context_pack.md` outputs from
//! memory retrieval results with provenance-tagged evidence.

use super::retrieval::{estimate_tokens, execute_query, trim_to_budget, RetrievalQuery};
use super::store::sqlite::MemoryIndex;
use super::types::*;

/// Default token budget for context packs.
const DEFAULT_TOKEN_BUDGET: usize = 4096;

/// Generate a boot context pack from the memory index.
pub(crate) fn generate_boot_pack(
    index: &MemoryIndex,
    project_id: &str,
    max_tokens: usize,
) -> ContextPack {
    let results = execute_query(index, &RetrievalQuery::Recent(100));
    let (included, used, trimmed) = trim_to_budget(&results, max_tokens);

    let evidence: Vec<PackEvidence> = included
        .iter()
        .filter_map(|&i| results.get(i))
        .map(|r| PackEvidence {
            event_id: r.event.event_id.clone(),
            score: r.score,
            text_preview: truncate_text(&r.event.text, 120),
            source: r.event.source.as_str().to_string(),
        })
        .collect();

    // Extract task refs and decisions from evidence.
    let mut active_tasks: Vec<String> = Vec::new();
    let mut recent_decisions: Vec<String> = Vec::new();
    for r in &results {
        for task in &r.event.task_refs {
            if !active_tasks.contains(task) {
                active_tasks.push(task.clone());
            }
        }
        if r.event.event_type == EventType::Decision {
            recent_decisions.push(truncate_text(&r.event.text, 200));
        }
    }

    let summary = if evidence.is_empty() {
        "No memory events available for boot context.".to_string()
    } else {
        format!(
            "Boot context pack with {} evidence items from project {}.",
            evidence.len(),
            project_id
        )
    };

    ContextPack {
        query: "boot".to_string(),
        generated_at: iso_timestamp(),
        pack_type: ContextPackType::Boot,
        summary,
        active_tasks,
        recent_decisions,
        changed_files: Vec::new(),
        open_questions: Vec::new(),
        token_budget: TokenBudget {
            target: max_tokens,
            used,
            trimmed,
        },
        evidence,
    }
}

/// Generate a task-focused context pack from a query.
pub(crate) fn generate_task_pack(
    index: &MemoryIndex,
    query: &str,
    _project_id: &str,
    max_tokens: usize,
) -> ContextPack {
    // Try task reference first, then text search.
    let query_type = if query.starts_with("MP-") || query.starts_with("mp-") {
        RetrievalQuery::ByTask {
            task: query.to_string(),
            limit: 100,
        }
    } else {
        RetrievalQuery::TextSearch {
            query: query.to_string(),
            limit: 100,
        }
    };

    let results = execute_query(index, &query_type);
    let (included, used, trimmed) = trim_to_budget(&results, max_tokens);

    let evidence: Vec<PackEvidence> = included
        .iter()
        .filter_map(|&i| results.get(i))
        .map(|r| PackEvidence {
            event_id: r.event.event_id.clone(),
            score: r.score,
            text_preview: truncate_text(&r.event.text, 120),
            source: r.event.source.as_str().to_string(),
        })
        .collect();

    let summary = if evidence.is_empty() {
        format!("No memory events found for query: {query}")
    } else {
        format!(
            "Task context pack for '{}' with {} evidence items.",
            query,
            evidence.len()
        )
    };

    ContextPack {
        query: query.to_string(),
        generated_at: iso_timestamp(),
        pack_type: ContextPackType::Task,
        summary,
        active_tasks: Vec::new(),
        recent_decisions: Vec::new(),
        changed_files: Vec::new(),
        open_questions: Vec::new(),
        token_budget: TokenBudget {
            target: max_tokens,
            used,
            trimmed,
        },
        evidence,
    }
}

/// Render a context pack as JSON.
pub(crate) fn pack_to_json(pack: &ContextPack) -> String {
    serde_json::to_string_pretty(pack).unwrap_or_else(|_| "{}".to_string())
}

/// Render a context pack as markdown.
pub(crate) fn pack_to_markdown(pack: &ContextPack) -> String {
    let mut md = String::new();
    md.push_str("# Context Pack\n\n");
    md.push_str(&format!(
        "- **Type**: {}\n",
        match pack.pack_type {
            ContextPackType::Boot => "Boot",
            ContextPackType::Task => "Task",
        }
    ));
    md.push_str(&format!("- **Query**: {}\n", pack.query));
    md.push_str(&format!("- **Generated**: {}\n", pack.generated_at));
    md.push_str(&format!(
        "- **Token budget**: {}/{} (trimmed: {})\n\n",
        pack.token_budget.used, pack.token_budget.target, pack.token_budget.trimmed
    ));

    md.push_str("## Summary\n\n");
    md.push_str(&pack.summary);
    md.push_str("\n\n");

    if !pack.active_tasks.is_empty() {
        md.push_str("## Active Tasks\n\n");
        for task in &pack.active_tasks {
            md.push_str(&format!("- {task}\n"));
        }
        md.push('\n');
    }

    if !pack.recent_decisions.is_empty() {
        md.push_str("## Recent Decisions\n\n");
        for decision in &pack.recent_decisions {
            md.push_str(&format!("- {decision}\n"));
        }
        md.push('\n');
    }

    if !pack.evidence.is_empty() {
        md.push_str("## Evidence\n\n");
        for (i, e) in pack.evidence.iter().enumerate() {
            md.push_str(&format!(
                "{}. [{}] (score: {:.2}, source: {}): {}\n",
                i + 1,
                e.event_id,
                e.score,
                e.source,
                e.text_preview
            ));
        }
        md.push('\n');
    }

    md
}

fn truncate_text(text: &str, max_chars: usize) -> String {
    if text.len() <= max_chars {
        text.to_string()
    } else {
        let mut truncated: String = text.chars().take(max_chars.saturating_sub(3)).collect();
        truncated.push_str("...");
        truncated
    }
}

/// Default token budget accessor.
pub(crate) fn default_token_budget() -> usize {
    DEFAULT_TOKEN_BUDGET
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::memory::types::*;

    fn sample_index() -> MemoryIndex {
        let mut idx = MemoryIndex::new();
        idx.insert(MemoryEvent {
            event_id: "evt_1".to_string(),
            session_id: "sess_test".to_string(),
            project_id: "proj_test".to_string(),
            ts: "2026-02-19T12:00:00.000Z".to_string(),
            source: EventSource::PtyInput,
            event_type: EventType::ChatTurn,
            role: EventRole::User,
            text: "first event about memory implementation".to_string(),
            topic_tags: vec!["memory".to_string()],
            entities: vec![],
            task_refs: vec!["MP-230".to_string()],
            artifacts: vec![],
            importance: 0.7,
            confidence: 1.0,
            retrieval_state: RetrievalState::Eligible,
            hash: None,
        });
        idx.insert(MemoryEvent {
            event_id: "evt_2".to_string(),
            session_id: "sess_test".to_string(),
            project_id: "proj_test".to_string(),
            ts: "2026-02-19T13:00:00.000Z".to_string(),
            source: EventSource::PtyOutput,
            event_type: EventType::Decision,
            role: EventRole::Assistant,
            text: "Use SQLite FTS5 for lexical search baseline".to_string(),
            topic_tags: vec!["memory".to_string(), "architecture".to_string()],
            entities: vec![],
            task_refs: vec!["MP-231".to_string()],
            artifacts: vec![],
            importance: 0.9,
            confidence: 1.0,
            retrieval_state: RetrievalState::Eligible,
            hash: None,
        });
        idx
    }

    #[test]
    fn generate_boot_pack_has_evidence() {
        let idx = sample_index();
        let pack = generate_boot_pack(&idx, "proj_test", 4096);
        assert_eq!(pack.pack_type, ContextPackType::Boot);
        assert!(!pack.evidence.is_empty());
        assert!(pack.summary.contains("evidence"));
    }

    #[test]
    fn generate_boot_pack_includes_tasks() {
        let idx = sample_index();
        let pack = generate_boot_pack(&idx, "proj_test", 4096);
        assert!(pack.active_tasks.contains(&"MP-230".to_string()));
        assert!(pack.active_tasks.contains(&"MP-231".to_string()));
    }

    #[test]
    fn generate_boot_pack_includes_decisions() {
        let idx = sample_index();
        let pack = generate_boot_pack(&idx, "proj_test", 4096);
        assert!(!pack.recent_decisions.is_empty());
    }

    #[test]
    fn generate_task_pack_by_mp_id() {
        let idx = sample_index();
        let pack = generate_task_pack(&idx, "MP-230", "proj_test", 4096);
        assert_eq!(pack.pack_type, ContextPackType::Task);
        assert!(!pack.evidence.is_empty());
    }

    #[test]
    fn generate_task_pack_by_text() {
        let idx = sample_index();
        let pack = generate_task_pack(&idx, "memory", "proj_test", 4096);
        assert!(!pack.evidence.is_empty());
    }

    #[test]
    fn generate_task_pack_no_results() {
        let idx = sample_index();
        let pack = generate_task_pack(&idx, "nonexistent_topic_xyz", "proj_test", 4096);
        assert!(pack.evidence.is_empty());
        assert!(pack.summary.contains("No memory events"));
    }

    #[test]
    fn empty_index_produces_empty_boot_pack() {
        let idx = MemoryIndex::new();
        let pack = generate_boot_pack(&idx, "proj_test", 4096);
        assert!(pack.evidence.is_empty());
        assert!(pack.summary.contains("No memory events"));
    }

    #[test]
    fn pack_to_json_roundtrip() {
        let idx = sample_index();
        let pack = generate_boot_pack(&idx, "proj_test", 4096);
        let json = pack_to_json(&pack);
        let parsed: ContextPack = serde_json::from_str(&json).expect("parse json");
        assert_eq!(parsed.pack_type, ContextPackType::Boot);
        assert_eq!(parsed.evidence.len(), pack.evidence.len());
    }

    #[test]
    fn pack_to_markdown_has_sections() {
        let idx = sample_index();
        let pack = generate_boot_pack(&idx, "proj_test", 4096);
        let md = pack_to_markdown(&pack);
        assert!(md.contains("# Context Pack"));
        assert!(md.contains("## Summary"));
        assert!(md.contains("## Evidence"));
    }

    #[test]
    fn truncate_text_long_string() {
        let long = "a".repeat(200);
        let truncated = truncate_text(&long, 50);
        assert!(truncated.len() <= 50);
        assert!(truncated.ends_with("..."));
    }

    #[test]
    fn truncate_text_short_string() {
        let short = "hello";
        let truncated = truncate_text(short, 50);
        assert_eq!(truncated, "hello");
    }

    #[test]
    fn token_budget_is_respected() {
        let idx = sample_index();
        let pack = generate_boot_pack(&idx, "proj_test", 10); // tiny budget
        assert!(pack.token_budget.used <= 10);
    }
}
