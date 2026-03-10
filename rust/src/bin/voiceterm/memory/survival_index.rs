//! Deterministic survival-index generation for compaction/recovery flows.
//!
//! The survival index is a compact, query-traced memory view that prioritizes:
//! - current task focus evidence
//! - broad recent context evidence
//! - reproducible token budgeting metadata

use std::collections::{BTreeSet, HashMap};

use serde::Serialize;

use super::retrieval::{
    execute_query_with_signal, trim_to_budget, ContextSignal, RetrievalQuery,
};
use super::store::sqlite::MemoryIndex;
use super::types::{EventType, TokenBudget};

const TASK_QUERY_LIMIT: usize = 80;
const RECENT_QUERY_LIMIT: usize = 120;
const EVIDENCE_PREVIEW_CHARS: usize = 140;
const DECISION_PREVIEW_CHARS: usize = 200;

/// Structured query trace used to audit survival-index retrieval behavior.
#[derive(Debug, Clone, Serialize)]
pub(crate) struct SurvivalQueryTrace {
    pub(crate) label: String,
    pub(crate) query: String,
    pub(crate) matched: usize,
    pub(crate) included: usize,
    pub(crate) used_tokens: usize,
    pub(crate) trimmed_tokens: usize,
    pub(crate) top_event_ids: Vec<String>,
}

/// Evidence row for the generated survival index.
#[derive(Debug, Clone, Serialize)]
pub(crate) struct SurvivalEvidence {
    pub(crate) event_id: String,
    pub(crate) score: f64,
    pub(crate) ts: String,
    pub(crate) is_decision: bool,
    pub(crate) text_preview: String,
    pub(crate) task_refs: Vec<String>,
    pub(crate) source_queries: Vec<String>,
}

/// Canonical survival-index payload exported for compaction/recovery handoff.
#[derive(Debug, Clone, Serialize)]
pub(crate) struct SurvivalIndex {
    pub(crate) generated_at: String,
    pub(crate) task_focus: String,
    pub(crate) summary: String,
    pub(crate) token_budget: TokenBudget,
    pub(crate) active_tasks: Vec<String>,
    pub(crate) recent_decisions: Vec<String>,
    pub(crate) evidence: Vec<SurvivalEvidence>,
    pub(crate) query_traces: Vec<SurvivalQueryTrace>,
}

#[derive(Debug, Clone)]
struct QueryPlan {
    label: &'static str,
    query: RetrievalQuery,
    signal: ContextSignal,
    query_label: String,
    budget: usize,
}

#[derive(Debug, Clone)]
struct EvidenceAccumulator {
    event_id: String,
    score: f64,
    ts: String,
    is_decision: bool,
    text_preview: String,
    task_refs: Vec<String>,
    source_queries: BTreeSet<String>,
}

/// Build a deterministic survival index from indexed memory events.
#[must_use = "survival index should be exported or rendered by callers"]
pub(crate) fn generate_survival_index(
    index: &MemoryIndex,
    task_focus: &str,
    max_tokens: usize,
) -> SurvivalIndex {
    let normalized_focus = normalize_task_focus(task_focus);
    let plans = build_query_plan(normalized_focus.as_str(), max_tokens);
    let mut evidence_map: HashMap<String, EvidenceAccumulator> = HashMap::new();
    let mut traces = Vec::new();
    let mut used_tokens = 0usize;
    let mut trimmed_tokens = 0usize;

    for plan in &plans {
        let (trace, used, trimmed) = execute_plan(plan, index, &mut evidence_map);
        traces.push(trace);
        used_tokens += used;
        trimmed_tokens += trimmed;
    }

    let evidence = into_sorted_evidence(evidence_map);
    let active_tasks = collect_active_tasks(&evidence);
    let recent_decisions = collect_recent_decisions(&evidence);
    let summary = format!(
        "Survival index with {} evidence items across {} retrieval traces.",
        evidence.len(),
        traces.len()
    );

    SurvivalIndex {
        generated_at: super::types::iso_timestamp(),
        task_focus: normalized_focus,
        summary,
        token_budget: TokenBudget {
            target: max_tokens,
            used: used_tokens.min(max_tokens),
            trimmed: trimmed_tokens,
        },
        active_tasks,
        recent_decisions,
        evidence,
        query_traces: traces,
    }
}

/// Render a survival index payload as markdown.
#[must_use = "markdown output should be consumed by callers"]
pub(crate) fn to_markdown(index: &SurvivalIndex) -> String {
    let mut markdown = String::new();
    markdown.push_str("# Survival Index\n\n");
    markdown.push_str(&format!("- **Generated**: {}\n", index.generated_at));
    markdown.push_str(&format!("- **Task focus**: {}\n", index.task_focus));
    markdown.push_str(&format!(
        "- **Token budget**: {}/{} (trimmed: {})\n\n",
        index.token_budget.used, index.token_budget.target, index.token_budget.trimmed
    ));
    markdown.push_str("## Summary\n\n");
    markdown.push_str(&index.summary);
    markdown.push_str("\n\n");

    if !index.active_tasks.is_empty() {
        markdown.push_str("## Active Tasks\n\n");
        for task in &index.active_tasks {
            markdown.push_str(&format!("- {task}\n"));
        }
        markdown.push('\n');
    }

    if !index.recent_decisions.is_empty() {
        markdown.push_str("## Recent Decisions\n\n");
        for decision in &index.recent_decisions {
            markdown.push_str(&format!("- {decision}\n"));
        }
        markdown.push('\n');
    }

    if !index.query_traces.is_empty() {
        markdown.push_str("## Query Traces\n\n");
        for trace in &index.query_traces {
            markdown.push_str(&format!(
                "- **{}** `{}` matched={} included={} tokens={}/{} top={}\n",
                trace.label,
                trace.query,
                trace.matched,
                trace.included,
                trace.used_tokens,
                trace.used_tokens + trace.trimmed_tokens,
                summarize_ids(&trace.top_event_ids)
            ));
        }
        markdown.push('\n');
    }

    if !index.evidence.is_empty() {
        markdown.push_str("## Evidence\n\n");
        for (idx, evidence) in index.evidence.iter().enumerate() {
            markdown.push_str(&format!(
                "{}. [{}] {:.2} [{}] ({}) {}\n",
                idx + 1,
                evidence.event_id,
                evidence.score,
                evidence.source_queries.join(", "),
                summarize_tasks(&evidence.task_refs),
                evidence.text_preview
            ));
        }
        markdown.push('\n');
    }

    markdown
}

fn build_query_plan(task_focus: &str, max_tokens: usize) -> Vec<QueryPlan> {
    let mut plans = Vec::new();
    let focus_query = build_focus_query(task_focus);
    let focus_budget = focus_query
        .as_ref()
        .map(|_| max_tokens.saturating_mul(3) / 5)
        .unwrap_or(0);
    if let Some((query, label)) = focus_query {
        plans.push(QueryPlan {
            label: "task_focus",
            query,
            signal: ContextSignal::UserQuery {
                text: task_focus.to_string(),
            },
            query_label: label,
            budget: focus_budget,
        });
    }
    plans.push(QueryPlan {
        label: "recent_context",
        query: RetrievalQuery::Recent(RECENT_QUERY_LIMIT),
        signal: ContextSignal::ContextBudgetWarning,
        query_label: format!("Recent({RECENT_QUERY_LIMIT})"),
        budget: max_tokens.saturating_sub(focus_budget),
    });
    plans
}

fn build_focus_query(task_focus: &str) -> Option<(RetrievalQuery, String)> {
    if task_focus.is_empty() || task_focus.eq_ignore_ascii_case("memory") {
        return None;
    }
    if looks_like_mp_ref(task_focus) {
        return Some((
            RetrievalQuery::ByTask {
                task: task_focus.to_string(),
                limit: TASK_QUERY_LIMIT,
            },
            format!("ByTask({task_focus})"),
        ));
    }
    Some((
        RetrievalQuery::TextSearch {
            query: task_focus.to_string(),
            limit: TASK_QUERY_LIMIT,
        },
        format!("TextSearch({task_focus})"),
    ))
}

fn looks_like_mp_ref(value: &str) -> bool {
    let normalized = value.trim();
    normalized.len() > 3
        && normalized[..3].eq_ignore_ascii_case("mp-")
        && normalized[3..].chars().all(|ch| ch.is_ascii_digit())
}

fn execute_plan(
    plan: &QueryPlan,
    index: &MemoryIndex,
    evidence_map: &mut HashMap<String, EvidenceAccumulator>,
) -> (SurvivalQueryTrace, usize, usize) {
    let results = execute_query_with_signal(index, &plan.query, &plan.signal);
    let (included, used_tokens, trimmed_tokens) = trim_to_budget(&results, plan.budget);
    for idx in &included {
        if let Some(row) = results.get(*idx) {
            merge_evidence(evidence_map, plan.label, row.event, row.score);
        }
    }
    let top_event_ids = included
        .iter()
        .filter_map(|idx| results.get(*idx))
        .take(3)
        .map(|row| row.event.event_id.clone())
        .collect();
    (
        SurvivalQueryTrace {
            label: plan.label.to_string(),
            query: plan.query_label.clone(),
            matched: results.len(),
            included: included.len(),
            used_tokens,
            trimmed_tokens,
            top_event_ids,
        },
        used_tokens,
        trimmed_tokens,
    )
}

fn merge_evidence(
    evidence_map: &mut HashMap<String, EvidenceAccumulator>,
    source_query: &str,
    event: &super::types::MemoryEvent,
    score: f64,
) {
    let entry = evidence_map
        .entry(event.event_id.clone())
        .or_insert_with(|| EvidenceAccumulator {
            event_id: event.event_id.clone(),
            score,
            ts: event.ts.clone(),
            is_decision: event.event_type == EventType::Decision,
            text_preview: truncate_text(&event.text, EVIDENCE_PREVIEW_CHARS),
            task_refs: event.task_refs.clone(),
            source_queries: BTreeSet::new(),
        });
    entry.score = entry.score.max(score);
    entry.source_queries.insert(source_query.to_string());
}

fn into_sorted_evidence(
    evidence_map: HashMap<String, EvidenceAccumulator>,
) -> Vec<SurvivalEvidence> {
    let mut evidence: Vec<SurvivalEvidence> = evidence_map
        .into_values()
        .map(|row| SurvivalEvidence {
            event_id: row.event_id,
            score: row.score,
            ts: row.ts,
            is_decision: row.is_decision,
            text_preview: row.text_preview,
            task_refs: row.task_refs,
            source_queries: row.source_queries.into_iter().collect(),
        })
        .collect();
    evidence.sort_by(|a, b| {
        b.score
            .total_cmp(&a.score)
            .then_with(|| b.ts.cmp(&a.ts))
            .then_with(|| a.event_id.cmp(&b.event_id))
    });
    evidence
}

fn collect_active_tasks(evidence: &[SurvivalEvidence]) -> Vec<String> {
    let mut tasks = BTreeSet::new();
    for row in evidence {
        for task in &row.task_refs {
            if !task.trim().is_empty() {
                tasks.insert(task.clone());
            }
        }
    }
    tasks.into_iter().collect()
}

fn collect_recent_decisions(evidence: &[SurvivalEvidence]) -> Vec<String> {
    let mut decisions = Vec::new();
    for row in evidence {
        if row.is_decision {
            decisions.push(truncate_text(&row.text_preview, DECISION_PREVIEW_CHARS));
        }
        if decisions.len() >= 6 {
            break;
        }
    }
    decisions
}

fn normalize_task_focus(task_focus: &str) -> String {
    let trimmed = task_focus.trim();
    if trimmed.is_empty() {
        "memory".to_string()
    } else {
        trimmed.to_string()
    }
}

fn truncate_text(text: &str, max_chars: usize) -> String {
    if text.len() <= max_chars {
        return text.to_string();
    }
    let mut truncated: String = text.chars().take(max_chars.saturating_sub(3)).collect();
    truncated.push_str("...");
    truncated
}

fn summarize_ids(ids: &[String]) -> String {
    if ids.is_empty() {
        "(none)".to_string()
    } else {
        ids.join(", ")
    }
}

fn summarize_tasks(tasks: &[String]) -> String {
    if tasks.is_empty() {
        "no-task".to_string()
    } else {
        tasks.join(", ")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::memory::types::{EventRole, EventSource, EventType, MemoryEvent, RetrievalState};

    fn event(
        id: &str,
        ts: &str,
        text: &str,
        task_refs: &[&str],
        event_type: EventType,
        importance: f64,
    ) -> MemoryEvent {
        MemoryEvent {
            event_id: id.to_string(),
            session_id: "sess_test".to_string(),
            project_id: "proj_test".to_string(),
            ts: ts.to_string(),
            source: EventSource::PtyInput,
            event_type,
            role: EventRole::Assistant,
            text: text.to_string(),
            topic_tags: vec!["memory".to_string()],
            entities: Vec::new(),
            task_refs: task_refs.iter().map(|value| (*value).to_string()).collect(),
            artifacts: Vec::new(),
            importance,
            confidence: 1.0,
            retrieval_state: RetrievalState::Eligible,
            hash: None,
        }
    }

    fn sample_index() -> MemoryIndex {
        let mut index = MemoryIndex::new();
        index.insert(event(
            "evt_old",
            "2026-03-08T11:00:00.000Z",
            "Older note for MP-340 prep.",
            &["MP-340"],
            EventType::Summary,
            0.4,
        ));
        index.insert(event(
            "evt_mid",
            "2026-03-08T12:00:00.000Z",
            "Decision: use structured retrieval traces for survival export.",
            &["MP-231"],
            EventType::Decision,
            0.8,
        ));
        index.insert(event(
            "evt_new",
            "2026-03-08T13:00:00.000Z",
            "Track MP-340 overlay memory cockpit progress.",
            &["MP-340"],
            EventType::ChatTurn,
            0.9,
        ));
        index
    }

    #[test]
    fn survival_index_includes_task_and_recent_traces() {
        let index = sample_index();
        let report = generate_survival_index(&index, "MP-340", 120);
        assert_eq!(report.query_traces.len(), 2);
        assert_eq!(report.query_traces[0].label, "task_focus");
        assert_eq!(report.query_traces[1].label, "recent_context");
        assert!(report
            .query_traces
            .iter()
            .any(|trace| trace.top_event_ids.iter().any(|id| id == "evt_new")));
    }

    #[test]
    fn survival_index_falls_back_to_recent_when_focus_misses() {
        let index = sample_index();
        let report = generate_survival_index(&index, "MP-999", 120);
        assert!(!report.evidence.is_empty());
        assert!(report
            .query_traces
            .iter()
            .any(|trace| trace.label == "task_focus" && trace.matched == 0));
        assert!(report
            .query_traces
            .iter()
            .any(|trace| trace.label == "recent_context" && trace.matched > 0));
    }

    #[test]
    fn survival_index_collects_active_tasks_and_decisions() {
        let index = sample_index();
        let report = generate_survival_index(&index, "memory", 160);
        assert!(report.active_tasks.contains(&"MP-231".to_string()));
        assert!(report.active_tasks.contains(&"MP-340".to_string()));
        assert!(!report.recent_decisions.is_empty());
    }

    #[test]
    fn survival_markdown_renders_traces_and_evidence() {
        let index = sample_index();
        let report = generate_survival_index(&index, "MP-340", 160);
        let markdown = to_markdown(&report);
        assert!(markdown.contains("# Survival Index"));
        assert!(markdown.contains("## Query Traces"));
        assert!(markdown.contains("evt_new"));
    }

    #[test]
    fn zero_budget_keeps_traces_but_no_included_evidence() {
        let index = sample_index();
        let report = generate_survival_index(&index, "MP-340", 0);
        assert_eq!(report.token_budget.target, 0);
        assert!(report.query_traces.iter().all(|trace| trace.included == 0));
    }
}
