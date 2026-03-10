//! Section builders for the Control cockpit page.

use std::time::Instant;

use super::{section_header, DRAFT_PREVIEW_MAX_LINES};
use crate::dev_command::{ActionCategory, DevPanelState};

pub(super) fn section_guard_state(lines: &mut Vec<String>, commands: &DevPanelState) {
    lines.push(section_header("Guard State"));
    lines.push(format!(
        "  Exec profile: {}",
        commands.execution_profile().label()
    ));
    lines.push(String::new());
}

pub(super) fn section_active_command(
    lines: &mut Vec<String>,
    commands: &DevPanelState,
    now: Instant,
) {
    lines.push(section_header("Active Command"));
    if let Some(label) = commands.running_command_label(now) {
        lines.push(format!("  Running: {label}"));
    } else {
        lines.push("  (idle)".to_string());
    }
    lines.push(String::new());
}

pub(super) fn section_last_command_result(lines: &mut Vec<String>, commands: &DevPanelState) {
    lines.push(section_header("Last Command Result"));
    if let Some(completion) = commands.last_completion() {
        lines.push(format!(
            "  Command: {}  Status: {}  Duration: {}ms",
            completion.command.label(),
            completion.status.label(),
            completion.duration_ms,
        ));
        if !completion.summary.is_empty() {
            lines.push(format!("  Summary: {}", completion.summary));
        }
        if let Some(ref stderr) = completion.stderr_excerpt {
            lines.push(format!("  Stderr: {stderr}"));
        }
        if let Some(ref packet) = completion.terminal_packet {
            lines.push(format!(
                "  Packet: {} (source: {}, auto_send: {})",
                packet.packet_id, packet.source_command, packet.auto_send
            ));
        }
    } else {
        lines.push("  (no commands run yet)".to_string());
    }
    lines.push(String::new());
}

pub(super) fn section_command_history(lines: &mut Vec<String>, commands: &DevPanelState) {
    // Recent completions newest-first, skipping the latest since it's shown
    // in "Last Command Result".
    let history = commands.recent_completions();
    if history.len() <= 1 {
        return;
    }
    lines.push(section_header("Command History"));
    for completion in history.iter().rev().skip(1) {
        lines.push(format!(
            "  {} {} ({}ms): {}",
            completion.command.label(),
            completion.status.label(),
            completion.duration_ms,
            if completion.summary.is_empty() {
                "(no summary)"
            } else {
                &completion.summary
            },
        ));
    }
    lines.push(String::new());
}

pub(super) fn section_staged_packet(lines: &mut Vec<String>, commands: &DevPanelState) {
    lines.push(section_header("Staged Packet Draft"));
    let Some(packet) = commands
        .last_completion()
        .and_then(|completion| completion.terminal_packet.as_ref())
    else {
        lines.push("  (no staged packet)".to_string());
        lines.push(String::new());
        return;
    };
    let send_label = if packet.auto_send {
        "auto-send requested"
    } else {
        "stage only"
    };
    lines.push(format!(
        "  [{send_label}] {} (source: {})",
        packet.packet_id, packet.source_command,
    ));
    let preview = truncate_draft_preview(&packet.draft_text, DRAFT_PREVIEW_MAX_LINES);
    for preview_line in &preview {
        lines.push(format!("  {preview_line}"));
    }
    lines.push("  (read-only preview — copy prompt from Handoff tab)".to_string());
    lines.push(String::new());
}

pub(super) fn section_review_bridge(lines: &mut Vec<String>, commands: &DevPanelState) {
    lines.push(section_header("Review Bridge"));
    if let Some(artifact) = commands.review().artifact() {
        if !artifact.last_codex_poll.is_empty() {
            lines.push(format!("  Last Codex poll: {}", artifact.last_codex_poll));
        }
        if !artifact.last_worktree_hash.is_empty() {
            lines.push(format!("  Worktree hash: {}", artifact.last_worktree_hash));
        }
        if !artifact.verdict.is_empty() {
            let verdict_first_line = artifact.verdict.lines().next().unwrap_or("").trim();
            lines.push(format!("  Verdict: {verdict_first_line}"));
        }
    } else if commands.review().load_error().is_some() {
        lines.push("  (review artifact load error)".to_string());
    } else {
        lines.push("  (not loaded — press Enter to refresh review data)".to_string());
    }
    lines.push(String::new());
}

pub(super) fn section_git(lines: &mut Vec<String>, commands: &DevPanelState) {
    lines.push(section_header("Git (current shell path)"));
    let Some(git) = commands.git_snapshot() else {
        lines.push("  (not loaded — press Enter to refresh shell git)".to_string());
        lines.push(String::new());
        return;
    };
    if git.has_error {
        lines.push(format!("  (error: {})", git.error_message));
        lines.push(String::new());
        return;
    }
    let mut branch_info = format!("  Branch: {}", git.branch);
    if git.ahead > 0 || git.behind > 0 {
        branch_info.push_str(&format!(" [ahead {}, behind {}]", git.ahead, git.behind));
    }
    lines.push(branch_info);
    lines.push(format!(
        "  Dirty: {}  Untracked: {}",
        git.dirty_count, git.untracked_count,
    ));
    if !git.last_commit.is_empty() {
        lines.push(format!("  HEAD: {}", git.last_commit));
    }
    if !git.changed_files.is_empty() {
        let total = git.dirty_count + git.untracked_count;
        let shown = git.changed_files.len();
        let suffix = if shown < total {
            format!(" (showing {shown}/{total})")
        } else {
            String::new()
        };
        lines.push(format!("  Changed files{suffix}:"));
        for entry in &git.changed_files {
            lines.push(format!("    {entry}"));
        }
    }
    if !git.diff_stat.is_empty() {
        lines.push(format!("  Diff: {}", git.diff_stat));
    }
    if git.recent_commits.len() > 1 {
        lines.push("  Recent commits:".to_string());
        for commit in git.recent_commits.iter().skip(1) {
            lines.push(format!("    {commit}"));
        }
    }
    lines.push(String::new());
}

pub(super) fn section_memory(lines: &mut Vec<String>, commands: &DevPanelState) {
    lines.push(section_header("Memory"));
    if let Some(mem) = commands.memory_snapshot() {
        lines.push(format!("  Mode: {}", mem.mode_label));
        lines.push(format!(
            "  Capture: {}  Retrieval: {}",
            if mem.capture_allowed { "on" } else { "off" },
            if mem.retrieval_allowed { "on" } else { "off" },
        ));
        lines.push(format!(
            "  Events: {} ingested, {} rejected, {} indexed",
            mem.events_ingested, mem.events_rejected, mem.index_size,
        ));
        if !mem.session_id.is_empty() {
            lines.push(format!("  Session: {}", mem.session_id));
        }
    } else {
        lines.push("  (memory subsystem not initialized)".to_string());
    }
    lines.push(String::new());
}

pub(super) fn section_action_catalog(lines: &mut Vec<String>, commands: &DevPanelState) {
    lines.push(section_header("Action Catalog"));
    let catalog = commands.catalog();
    let read_count = catalog
        .entries()
        .iter()
        .filter(|entry| entry.category() == ActionCategory::ReadOnly)
        .count();
    let mut_count = catalog
        .entries()
        .iter()
        .filter(|entry| entry.category() == ActionCategory::Mutating)
        .count();
    lines.push(format!(
        "  {} actions ({} read-only, {} mutating)",
        catalog.len(),
        read_count,
        mut_count,
    ));
    lines.push(String::new());
}

pub(super) fn section_runtime_snapshot(lines: &mut Vec<String>, commands: &DevPanelState) {
    lines.push(section_header("Runtime Snapshot"));
    let Some(diag) = commands.runtime_diagnostics() else {
        lines.push("  (diagnostics not loaded)".to_string());
        return;
    };
    lines.push(format!(
        "  Host: {}  Backend: {}",
        diag.terminal_host, diag.backend_label,
    ));
    lines.push(format!(
        "  Terminal: {}x{} (cols x rows)",
        diag.terminal_cols, diag.terminal_rows,
    ));
    lines.push(format!(
        "  Theme: {}  Auto-voice: {}  Overlay: {}",
        diag.theme_name, diag.auto_voice, diag.overlay_mode,
    ));
    lines.push(format!(
        "  Voice: {}  Recording: {}  Dev: {}{}",
        diag.voice_mode,
        diag.recording_state,
        if diag.dev_mode { "on" } else { "off" },
        if diag.dev_log { " (logging)" } else { "" },
    ));
    let uptime = format_uptime(diag.session_uptime_secs);
    lines.push(format!(
        "  Session: {}  Transcripts: {}  Errors: {}",
        uptime, diag.transcripts, diag.errors,
    ));
}

pub(super) fn format_uptime(secs: f32) -> String {
    if secs < 60.0 {
        format!("{secs:.0}s")
    } else if secs < 3600.0 {
        format!("{}m {}s", (secs / 60.0) as u32, (secs % 60.0) as u32)
    } else {
        format!(
            "{}h {}m",
            (secs / 3600.0) as u32,
            ((secs % 3600.0) / 60.0) as u32,
        )
    }
}

pub(super) fn truncate_draft_preview(draft: &str, max_lines: usize) -> Vec<String> {
    let all_lines: Vec<&str> = draft.lines().collect();
    if all_lines.is_empty() {
        return vec!["(empty draft)".to_string()];
    }
    let truncated = all_lines.len() > max_lines;
    let mut result: Vec<String> = all_lines
        .into_iter()
        .take(max_lines)
        .map(str::to_string)
        .collect();
    if truncated {
        result.push("...".to_string());
    }
    result
}
