//! Memory governance controls: retention, redaction, per-project isolation (MP-235).
//!
//! Enforces bounded growth, privacy, and retrieval-state lifecycle policies.

use super::store::sqlite::MemoryIndex;
use super::types::*;

/// Maximum number of events retained in the active index before GC.
pub(crate) const MAX_INDEX_EVENTS: usize = 10_000;

/// Default project memory root directory name.
pub(crate) const MEMORY_DIR: &str = ".voiceterm/memory";

/// Events JSONL filename.
pub(crate) const EVENTS_JSONL: &str = "events.jsonl";

/// Resolve the project-scoped memory directory path.
pub(crate) fn memory_dir(project_root: &std::path::Path) -> std::path::PathBuf {
    project_root.join(MEMORY_DIR)
}

/// Resolve the events JSONL path.
pub(crate) fn events_jsonl_path(project_root: &std::path::Path) -> std::path::PathBuf {
    memory_dir(project_root).join(EVENTS_JSONL)
}

/// Redact potentially sensitive content from text before persistence.
/// This is a baseline redaction pass; project-specific rules can extend it.
pub(crate) fn redact_secrets(text: &str) -> String {
    let mut redacted = text.to_string();

    // Redact common secret patterns.
    let patterns = [
        // API keys / tokens (common prefixes)
        ("sk-", "[REDACTED_KEY]"),
        ("ghp_", "[REDACTED_TOKEN]"),
        ("ghs_", "[REDACTED_TOKEN]"),
        ("ghu_", "[REDACTED_TOKEN]"),
        ("glpat-", "[REDACTED_TOKEN]"),
        ("xoxb-", "[REDACTED_TOKEN]"),
        ("xoxp-", "[REDACTED_TOKEN]"),
        // AWS-style keys
        ("AKIA", "[REDACTED_AWS]"),
    ];

    for (prefix, replacement) in &patterns {
        if let Some(pos) = redacted.find(prefix) {
            // Find end of the secret (typically alphanumeric + dashes).
            let start = pos;
            let rest = &redacted[start..];
            let end = rest
                .find(|c: char| c.is_whitespace() || c == '"' || c == '\'' || c == ',' || c == ';')
                .unwrap_or(rest.len());
            redacted.replace_range(start..start + end, replacement);
        }
    }

    redacted
}

/// Count events eligible for garbage collection (older than retention limit).
pub(crate) fn count_gc_candidates(
    index: &MemoryIndex,
    retention: RetentionPolicy,
    current_ts: &str,
) -> usize {
    let Some(max_days) = retention.as_days() else {
        return 0; // Forever = no GC
    };

    // Simple GC candidate counting: events older than max_days from current_ts.
    // Uses ISO string comparison which works for chronological ordering.
    let cutoff = compute_cutoff_ts(current_ts, max_days);
    let all = index.all_eligible();
    all.iter()
        .filter(|e| e.ts.as_str() < cutoff.as_str())
        .count()
}

/// Compute a cutoff timestamp by subtracting days from a reference ISO timestamp.
fn compute_cutoff_ts(reference_ts: &str, days: u32) -> String {
    // Parse the date portion and subtract days.
    // Format: YYYY-MM-DDTHH:MM:SS.mmmZ
    if reference_ts.len() < 10 {
        return reference_ts.to_string();
    }
    let date_str = &reference_ts[..10];
    let parts: Vec<&str> = date_str.split('-').collect();
    if parts.len() != 3 {
        return reference_ts.to_string();
    }

    let year: i64 = parts[0].parse().unwrap_or(2026);
    let month: i64 = parts[1].parse().unwrap_or(1);
    let day: i64 = parts[2].parse().unwrap_or(1);

    // Convert to days since epoch, subtract, convert back (simplified).
    let total_days = ymd_to_days(year, month, day);
    let cutoff_days = total_days.saturating_sub(days as i64);
    let (cy, cm, cd) = days_to_ymd_signed(cutoff_days);

    let time_suffix = if reference_ts.len() > 10 {
        &reference_ts[10..]
    } else {
        "T00:00:00.000Z"
    };

    format!("{cy:04}-{cm:02}-{cd:02}{time_suffix}")
}

fn ymd_to_days(year: i64, month: i64, day: i64) -> i64 {
    // Simplified days since epoch (1970-01-01).
    let mut days: i64 = 0;
    for y in 1970..year {
        days += if is_leap_i64(y) { 366 } else { 365 };
    }
    let leap = is_leap_i64(year);
    let month_days: [i64; 12] = [
        31,
        if leap { 29 } else { 28 },
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ];
    for month_days_value in month_days.iter().take(((month - 1) as usize).min(11)) {
        days += *month_days_value;
    }
    days += day - 1;
    days
}

fn days_to_ymd_signed(mut days: i64) -> (i64, i64, i64) {
    let mut year: i64 = 1970;
    if days < 0 {
        return (1970, 1, 1);
    }
    loop {
        let year_days: i64 = if is_leap_i64(year) { 366 } else { 365 };
        if days < year_days {
            break;
        }
        days -= year_days;
        year += 1;
    }
    let leap = is_leap_i64(year);
    let month_days: [i64; 12] = [
        31,
        if leap { 29 } else { 28 },
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ];
    let mut month: i64 = 1;
    for &md in &month_days {
        if days < md {
            break;
        }
        days -= md;
        month += 1;
    }
    (year, month, days + 1)
}

fn is_leap_i64(year: i64) -> bool {
    (year % 4 == 0 && year % 100 != 0) || year % 400 == 0
}

/// Memory governance configuration for a project.
#[derive(Debug, Clone)]
pub(crate) struct GovernanceConfig {
    pub(crate) retention: RetentionPolicy,
    pub(crate) redact_secrets: bool,
    pub(crate) max_index_events: usize,
}

impl Default for GovernanceConfig {
    fn default() -> Self {
        Self {
            retention: RetentionPolicy::default(),
            redact_secrets: true,
            max_index_events: MAX_INDEX_EVENTS,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn redact_secrets_removes_api_keys() {
        let input = "My key is sk-abc123xyz and token ghp_abcdef";
        let redacted = redact_secrets(input);
        assert!(redacted.contains("[REDACTED_KEY]"));
        assert!(redacted.contains("[REDACTED_TOKEN]"));
        assert!(!redacted.contains("sk-abc123xyz"));
        assert!(!redacted.contains("ghp_abcdef"));
    }

    #[test]
    fn redact_secrets_preserves_safe_text() {
        let input = "This is safe text with no secrets";
        let redacted = redact_secrets(input);
        assert_eq!(redacted, input);
    }

    #[test]
    fn redact_secrets_handles_aws_keys() {
        let input = "key=AKIAIOSFODNN7EXAMPLE";
        let redacted = redact_secrets(input);
        assert!(redacted.contains("[REDACTED_AWS]"));
    }

    #[test]
    fn memory_dir_is_project_scoped() {
        let root = std::path::Path::new("/tmp/myproject");
        let dir = memory_dir(root);
        assert_eq!(dir.to_str().unwrap(), "/tmp/myproject/.voiceterm/memory");
    }

    #[test]
    fn events_jsonl_path_correct() {
        let root = std::path::Path::new("/tmp/myproject");
        let path = events_jsonl_path(root);
        assert!(path.to_str().unwrap().ends_with("events.jsonl"));
    }

    #[test]
    fn governance_config_defaults() {
        let config = GovernanceConfig::default();
        assert_eq!(config.retention, RetentionPolicy::Days30);
        assert!(config.redact_secrets);
        assert_eq!(config.max_index_events, MAX_INDEX_EVENTS);
    }

    #[test]
    fn compute_cutoff_ts_subtracts_days() {
        let ts = "2026-02-19T12:00:00.000Z";
        let cutoff = compute_cutoff_ts(ts, 7);
        assert!(cutoff.starts_with("2026-02-12"));
        assert!(cutoff.ends_with("T12:00:00.000Z"));
    }

    #[test]
    fn compute_cutoff_ts_crosses_month() {
        let ts = "2026-02-05T00:00:00.000Z";
        let cutoff = compute_cutoff_ts(ts, 10);
        assert!(cutoff.starts_with("2026-01-26"));
    }

    #[test]
    fn count_gc_candidates_forever_returns_zero() {
        let idx = crate::memory::store::sqlite::MemoryIndex::new();
        assert_eq!(
            count_gc_candidates(&idx, RetentionPolicy::Forever, "2026-02-19T00:00:00.000Z"),
            0
        );
    }

    #[test]
    fn count_gc_candidates_with_old_events() {
        use crate::memory::types::*;
        let mut idx = crate::memory::store::sqlite::MemoryIndex::new();

        let mut old_event = MemoryEvent {
            event_id: "evt_old".to_string(),
            session_id: "sess_test".to_string(),
            project_id: "proj_test".to_string(),
            ts: "2026-01-01T12:00:00.000Z".to_string(),
            source: EventSource::PtyInput,
            event_type: EventType::ChatTurn,
            role: EventRole::User,
            text: "old event".to_string(),
            topic_tags: vec![],
            entities: vec![],
            task_refs: vec![],
            artifacts: vec![],
            importance: 0.5,
            confidence: 1.0,
            retrieval_state: RetrievalState::Eligible,
            hash: None,
        };
        idx.insert(old_event.clone());

        old_event.event_id = "evt_new".to_string();
        old_event.ts = "2026-02-18T12:00:00.000Z".to_string();
        idx.insert(old_event);

        let gc_count =
            count_gc_candidates(&idx, RetentionPolicy::Days30, "2026-02-19T00:00:00.000Z");
        assert_eq!(gc_count, 1); // Only the January event is older than 30 days
    }
}
