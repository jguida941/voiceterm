use std::path::{Path, PathBuf};

use super::format::truncate_hash;

const EVENT_REVIEW_ARTIFACT_CANDIDATES: [&str; 4] = [
    "dev/reports/review_channel/projections/latest/full.json",
    "dev/reports/review_channel/state/latest.json",
    "dev/reports/review_channel/latest/full.json",
    "dev/reports/review_channel/latest/review_state.json",
];
const EVENT_REVIEW_SENTINELS: [&str; 2] = [
    "dev/reports/review_channel/events/trace.ndjson",
    "dev/reports/review_channel/state/latest.json",
];

/// Key sections extracted from code_audit.md for read-only display.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub(crate) struct ReviewContextPackRef {
    pub(crate) pack_kind: String,
    pub(crate) pack_ref: String,
    pub(crate) adapter_profile: String,
    pub(crate) generated_at_utc: String,
}

impl ReviewContextPackRef {
    pub(crate) fn summary_line(&self) -> String {
        let mut line = format!("{}: {}", self.pack_kind, self.pack_ref);
        if !self.adapter_profile.is_empty() {
            line.push_str(&format!(" ({})", self.adapter_profile));
        }
        if !self.generated_at_utc.is_empty() {
            line.push_str(&format!(" @ {}", self.generated_at_utc));
        }
        line
    }
}

/// Key sections extracted from code_audit.md for read-only display.
#[derive(Debug, Clone, Default)]
pub(crate) struct ReviewArtifact {
    pub(crate) verdict: String,
    pub(crate) findings: String,
    pub(crate) instruction: String,
    pub(crate) poll_status: String,
    pub(crate) claude_ack: String,
    pub(crate) claude_status: String,
    pub(crate) claude_questions: String,
    pub(crate) last_reviewed_scope: String,
    /// Bridge-critical header: last Codex poll timestamp (UTC).
    pub(crate) last_codex_poll: String,
    /// Bridge-critical header: last Codex poll timestamp (local/New York).
    pub(crate) last_codex_poll_local: String,
    /// Bridge-critical header: reviewed non-audit worktree hash.
    pub(crate) last_worktree_hash: String,
    /// Memory/context attachments carried by the current structured review packets.
    pub(crate) context_pack_refs: Vec<ReviewContextPackRef>,
}

impl ReviewArtifact {
    /// Compact bridge-status line derived from poll metadata.
    /// Returns `None` when no Codex poll has been recorded yet.
    pub(crate) fn bridge_status_summary(&self) -> Option<String> {
        if self.last_codex_poll.is_empty() {
            return None;
        }
        Some(format!(
            "poll {} | hash {}",
            self.last_codex_poll,
            truncate_hash(&self.last_worktree_hash)
        ))
    }
}

/// Parse code_audit.md content into structured sections.
pub(crate) fn parse_review_artifact(content: &str) -> ReviewArtifact {
    let mut artifact = ReviewArtifact::default();
    let mut current_section: Option<&str> = None;
    let mut current_buf = String::new();

    for line in content.lines() {
        if let Some(heading) = line.strip_prefix("## ") {
            if let Some(section) = current_section {
                assign_section(&mut artifact, section, current_buf.trim().to_string());
            }
            current_section = Some(heading.trim());
            current_buf.clear();
        } else if current_section.is_some() {
            current_buf.push_str(line);
            current_buf.push('\n');
        } else {
            // Preamble: extract bridge-critical header metadata bullets.
            extract_header_metadata(&mut artifact, line);
        }
    }

    if let Some(section) = current_section {
        assign_section(&mut artifact, section, current_buf.trim().to_string());
    }

    artifact
}

/// Locate code_audit.md by walking up from the given start directory,
/// then the session launch directory, then falling back to the process CWD
/// and compile-time repo root.
/// When `session_dir` is provided (the live PTY shell CWD), it is tried
/// first so the Review surface follows the same tree as Git snapshot.
pub(crate) fn find_review_artifact_path(
    session_dir: Option<&Path>,
    fallback_dir: Option<&Path>,
) -> Option<PathBuf> {
    // Preserve markdown-bridge authority within each candidate tree while
    // still honoring the live session/fallback directories before unrelated
    // process-CWD or compile-time repo fallbacks.
    if let Some(path) = find_review_artifact_in_location(session_dir) {
        return Some(path);
    }
    if let Some(path) = find_review_artifact_in_location(fallback_dir) {
        return Some(path);
    }
    if let Ok(cwd) = std::env::current_dir() {
        if let Some(path) = find_review_artifact_in_location(Some(&cwd)) {
            return Some(path);
        }
    }
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let repo_root = manifest_dir.parent().unwrap_or(manifest_dir);
    find_review_artifact_in_location(Some(repo_root))
}

fn find_review_artifact_in_location(start: Option<&Path>) -> Option<PathBuf> {
    let start = start?;
    find_bridge_artifact(start).or_else(|| find_event_review_artifact(start))
}

fn find_event_review_artifact(start: &Path) -> Option<PathBuf> {
    for ancestor in start.ancestors() {
        if !EVENT_REVIEW_SENTINELS
            .iter()
            .any(|relative| ancestor.join(relative).is_file())
        {
            continue;
        }
        for relative in EVENT_REVIEW_ARTIFACT_CANDIDATES {
            let candidate = ancestor.join(relative);
            if candidate.is_file() {
                return Some(candidate);
            }
        }
    }
    None
}

fn find_bridge_artifact(start: &Path) -> Option<PathBuf> {
    walk_ancestors_for_file(start, "code_audit.md")
}

fn extract_header_metadata(artifact: &mut ReviewArtifact, line: &str) {
    let trimmed = line.trim().trim_start_matches('-').trim();
    if let Some(value) = trimmed.strip_prefix("Last Codex poll (Local") {
        if let Some(rest) = value.split_once(':').map(|(_, value)| value.trim()) {
            artifact.last_codex_poll_local = strip_backticks(rest).to_string();
        }
    } else if let Some(rest) = trimmed.strip_prefix("Last Codex poll:") {
        artifact.last_codex_poll = strip_backticks(rest.trim()).to_string();
    } else if let Some(rest) = trimmed.strip_prefix("Last non-audit worktree hash:") {
        artifact.last_worktree_hash = strip_backticks(rest.trim()).to_string();
    }
}

fn strip_backticks(s: &str) -> &str {
    s.trim().trim_start_matches('`').trim_end_matches('`')
}

fn assign_section(artifact: &mut ReviewArtifact, section_name: &str, content: String) {
    match section_name {
        "Poll Status" => artifact.poll_status = content,
        "Current Verdict" => artifact.verdict = content,
        "Open Findings" => artifact.findings = content,
        "Current Instruction For Claude" => artifact.instruction = content,
        "Claude Ack" => artifact.claude_ack = content,
        "Claude Status" => artifact.claude_status = content,
        "Claude Questions" => artifact.claude_questions = content,
        "Last Reviewed Scope" => artifact.last_reviewed_scope = content,
        _ => {}
    }
}

fn walk_ancestors_for_file(start: &Path, filename: &str) -> Option<PathBuf> {
    for ancestor in start.ancestors() {
        let candidate = ancestor.join(filename);
        if candidate.is_file() {
            return Some(candidate);
        }
    }
    None
}
