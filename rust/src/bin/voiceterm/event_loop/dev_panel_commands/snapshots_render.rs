//! Rendering helpers shared by dev-panel snapshot builders.

use crate::dev_command::{parse_scope_list, push_trimmed_lines, ReviewArtifact};

/// Append review artifact findings/scope/context/questions sections.
pub(super) fn append_artifact_sections(parts: &mut Vec<String>, artifact: &ReviewArtifact) {
    if !artifact.findings.is_empty() {
        parts.push(String::new());
        parts.push("Open Findings (live blockers):".to_string());
        push_trimmed_lines(parts, &artifact.findings);
    }

    let scope_items = parse_scope_list(&artifact.last_reviewed_scope);
    if !scope_items.is_empty() {
        parts.push(String::new());
        parts.push("Last Reviewed Scope:".to_string());
        for item in &scope_items {
            parts.push(format!("  - {item}"));
        }
    }

    if !artifact.context_pack_refs.is_empty() {
        parts.push(String::new());
        parts.push("Attached Context Packs:".to_string());
        for context_pack_ref in &artifact.context_pack_refs {
            parts.push(format!("  - {}", context_pack_ref.summary_line()));
        }
    }

    if !artifact.claude_questions.is_empty() {
        parts.push(String::new());
        parts.push("Claude Questions:".to_string());
        push_trimmed_lines(parts, &artifact.claude_questions);
    }
}

/// Append compact retrieval-trace rows for survival index previews.
pub(super) fn append_survival_trace_lines(
    lines: &mut Vec<String>,
    survival: &crate::memory::survival_index::SurvivalIndex,
) {
    for trace in &survival.query_traces {
        let top_ids = if trace.top_event_ids.is_empty() {
            "(none)".to_string()
        } else {
            trace.top_event_ids.join(", ")
        };
        lines.push(format!(
            "Trace {} [{}]: matched={} included={} tokens={}/{} top={}",
            trace.label,
            trace.query,
            trace.matched,
            trace.included,
            trace.used_tokens,
            trace.used_tokens + trace.trimmed_tokens,
            top_ids
        ));
    }
}

/// Append top evidence rows for survival index previews.
pub(super) fn append_survival_evidence_lines(
    lines: &mut Vec<String>,
    survival: &crate::memory::survival_index::SurvivalIndex,
) {
    for evidence in survival.evidence.iter().take(3) {
        lines.push(format!(
            "Evidence: [{}] {:.2} [{}] {}",
            evidence.event_id,
            evidence.score,
            evidence.source_queries.join(", "),
            evidence.text_preview
        ));
    }
}
