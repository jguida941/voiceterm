use std::path::{Path, PathBuf};

use super::format::truncate_hash;

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
    if let Some(dir) = session_dir {
        if let Some(path) = walk_ancestors_for_file(dir, "code_audit.md") {
            return Some(path);
        }
    }
    if let Some(dir) = fallback_dir {
        if let Some(path) = walk_ancestors_for_file(dir, "code_audit.md") {
            return Some(path);
        }
    }
    if let Ok(cwd) = std::env::current_dir() {
        if let Some(path) = walk_ancestors_for_file(&cwd, "code_audit.md") {
            return Some(path);
        }
    }
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let repo_root = manifest_dir.parent().unwrap_or(manifest_dir);
    let candidate = repo_root.join("code_audit.md");
    if candidate.is_file() {
        return Some(candidate);
    }
    None
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
