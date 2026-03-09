//! Cockpit pages: tab bar + Control, Ops, Handoff, and Memory page content generators.

use std::time::Instant;

use super::{dev_panel_height, panel_width, review_content_line};
use crate::dev_command::{push_trimmed_lines, DevCommandKind, DevPanelState, DevPanelTab};
use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top,
};
use crate::theme::{
    overlay_close_symbol, overlay_separator, resolved_overlay_border_set, Theme, ThemeColors,
};

#[cfg(test)]
mod tests;

/// Maximum preview lines for the staged packet draft on the Control page.
const DRAFT_PREVIEW_MAX_LINES: usize = 3;

/// Section header glyph used across all cockpit page sections.
const SECTION_GLYPH: char = '\u{25B8}';

/// Build a section header line with the standard `▸` prefix.
fn section_header(name: &str) -> String {
    format!("{SECTION_GLYPH} {name}")
}

/// Number of visible content rows in cockpit pages (Control, Handoff).
/// Chrome: top + title + sep + tab_bar + sep + sep + footer + bottom = 8.
pub fn cockpit_visible_rows() -> usize {
    dev_panel_height().saturating_sub(8)
}

/// Total content lines for the active cockpit page, used by scroll handlers.
pub fn cockpit_content_line_count(commands: &DevPanelState, page: DevPanelTab) -> usize {
    cockpit_page_content(commands, page).len()
}

/// Render the cockpit tab bar showing all four pages with the active one highlighted.
fn cockpit_tab_bar(colors: &ThemeColors, active: DevPanelTab, inner_width: usize) -> String {
    let borders = &colors.borders;
    // Build the ANSI-colored bar and track visible width separately,
    // since display_width/truncate_display don't understand escape codes.
    let mut bar = String::new();
    let mut visible_width = 0usize;
    for (i, &tab) in DevPanelTab::ALL.iter().enumerate() {
        if i > 0 {
            bar.push_str(&format!("{}\u{2502}{}", colors.dim, colors.reset));
            visible_width += 1; // the │ separator
        }
        let segment = format!(" {} ", tab.label());
        let seg_width = display_width(&segment);
        if tab == active {
            bar.push_str(&format!("{}{}{}", colors.info, segment, colors.reset));
        } else {
            bar.push_str(&format!("{}{}{}", colors.dim, segment, colors.reset));
        }
        visible_width += seg_width;
    }
    let pad = " ".repeat(inner_width.saturating_sub(visible_width));
    format!(
        "{}{}{}{}{}{}{}",
        colors.border, borders.vertical, bar, pad, colors.border, borders.vertical, colors.reset,
    )
}

/// Render a cockpit page (Control or Handoff) with a tab bar and content.
pub fn format_cockpit_page(
    theme: Theme,
    commands: &DevPanelState,
    page: DevPanelTab,
    width: usize,
) -> String {
    let mut colors = theme.colors();
    colors.borders = resolved_overlay_border_set(theme);
    let borders = &colors.borders;
    let content_width = panel_width(width);
    let inner_width = content_width.saturating_sub(2);

    let title = format!("VoiceTerm - {}", page.label());
    let mut lines = vec![
        frame_top(&colors, borders, content_width),
        centered_title_line(&colors, borders, &title, content_width),
        frame_separator(&colors, borders, content_width),
        cockpit_tab_bar(&colors, page, inner_width),
        frame_separator(&colors, borders, content_width),
    ];

    let content_lines = cockpit_page_content(commands, page);
    let visible_rows = cockpit_visible_rows();
    let scroll_offset = commands.cockpit_scroll_offset();
    let total_rows = content_lines.len();
    let start = scroll_offset.min(total_rows);
    let end = (start + visible_rows).min(total_rows);
    for line in &content_lines[start..end] {
        lines.push(review_content_line(&colors, line, inner_width));
    }
    for _ in (end - start)..visible_rows {
        lines.push(review_content_line(&colors, "", inner_width));
    }

    let footer = cockpit_page_footer(&colors, commands, page, total_rows);
    lines.push(frame_separator(&colors, borders, content_width));
    lines.push(centered_title_line(
        &colors,
        borders,
        &footer,
        content_width,
    ));
    lines.push(frame_bottom(&colors, borders, content_width));

    lines.join("\n")
}

pub(crate) fn cockpit_page_footer(
    colors: &ThemeColors,
    commands: &DevPanelState,
    page: DevPanelTab,
    total_rows: usize,
) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    let page_keys = match page {
        DevPanelTab::Control => {
            format!(" {sep} Enter refresh review/git/memory {sep} m memory mode")
        }
        DevPanelTab::Ops => format!(" {sep} Enter refresh ops telemetry"),
        DevPanelTab::Handoff => format!(" {sep} Enter refresh handoff {sep} c copy prompt"),
        DevPanelTab::Memory => {
            format!(" {sep} Enter refresh packs {sep} m memory mode")
        }
        _ => String::new(),
    };
    let visible_rows = cockpit_visible_rows();
    let scroll_offset = commands.cockpit_scroll_offset();
    let scroll_info = if total_rows > visible_rows {
        let max_pos = total_rows.saturating_sub(visible_rows) + 1;
        let cur_pos = scroll_offset.min(max_pos.saturating_sub(1)) + 1;
        format!(" [{cur_pos}/{max_pos}]")
    } else {
        String::new()
    };
    format!("[{close}] close {sep} Tab next {sep} Shift+Tab prev{page_keys}{scroll_info}")
}

/// Generate content lines for a cockpit page from current DevPanelState.
fn cockpit_page_content(commands: &DevPanelState, page: DevPanelTab) -> Vec<String> {
    match page {
        DevPanelTab::Control => control_page_lines(commands),
        DevPanelTab::Ops => ops_page_lines(commands),
        DevPanelTab::Handoff => handoff_page_lines(commands),
        DevPanelTab::Memory => memory_page_lines(commands),
        _ => vec!["  (no content for this page)".to_string()],
    }
}

fn ops_page_lines(commands: &DevPanelState) -> Vec<String> {
    let now = Instant::now();
    let mut lines = Vec::new();

    lines.push(section_header("Host Process Hygiene"));
    if let Some(ops) = commands.ops_snapshot() {
        let audit = &ops.process_audit;
        if !audit.error_message.is_empty() {
            lines.push(format!("  Snapshot error: {}", audit.error_message));
        } else {
            let state = if audit.ok { "clean" } else { "attention" };
            let strict_label = if audit.strict { "strict" } else { "advisory" };
            let captured_at = if audit.captured_at.is_empty() {
                "unknown".to_string()
            } else {
                audit.captured_at.clone()
            };
            lines.push(format!(
                "  Audit: {state} ({strict_label}) at {captured_at}"
            ));
            lines.push(format!(
                "  Detected: {} total  Orphaned: {}  Stale: {}  Recent: {}",
                audit.total_detected,
                audit.orphaned_count,
                audit.stale_active_count,
                audit.active_recent_count
            ));
            lines.push(format!(
                "  Detached: {}  Blocking: {}  Advisory: {}",
                audit.recent_detached_count,
                audit.active_recent_blocking_count,
                audit.active_recent_advisory_count
            ));
            lines.push(format!(
                "  Warnings: {}  Errors: {}",
                audit.warning_count, audit.error_count
            ));
            if !audit.headline.is_empty() {
                lines.push(format!("  Note: {}", audit.headline));
            }
        }
    } else {
        lines.push("  (not loaded — press Enter to refresh ops telemetry)".to_string());
    }
    lines.push(String::new());

    lines.push(section_header("Triage"));
    if let Some(ops) = commands.ops_snapshot() {
        let triage = &ops.triage;
        if !triage.error_message.is_empty() {
            lines.push(format!("  Snapshot error: {}", triage.error_message));
        } else {
            let captured_at = if triage.captured_at.is_empty() {
                "unknown".to_string()
            } else {
                triage.captured_at.clone()
            };
            lines.push(format!("  Refreshed: {captured_at}"));
            lines.push(format!(
                "  Issues: {} total  High: {}  Medium: {}",
                triage.total_issues, triage.high_count, triage.medium_count
            ));
            lines.push(format!(
                "  Warnings: {}  External inputs: {}",
                triage.warning_count, triage.external_input_count
            ));
            if !triage.summary.is_empty() {
                lines.push(format!("  Summary: {}", triage.summary));
            }
        }
    } else {
        lines.push("  (triage snapshot not loaded yet)".to_string());
    }
    lines.push(String::new());

    lines.push(section_header("Typed Ops Actions"));
    for kind in [
        DevCommandKind::Triage,
        DevCommandKind::ProcessAudit,
        DevCommandKind::ProcessWatch,
        DevCommandKind::ProcessCleanup,
    ] {
        lines.push(format!(
            "  {}: {}",
            kind.label(),
            commands.status_for(kind, now)
        ));
        if let Some(completion) = commands.latest_completion_for(kind) {
            if !completion.summary.is_empty() {
                lines.push(format!("    {}", completion.summary));
            }
        }
    }

    lines
}

/// Control page: synthesize a dashboard from in-memory DevPanelState.
/// Visible in tests via `super::cockpit_page::control_page_lines`.
pub(super) fn control_page_lines(commands: &DevPanelState) -> Vec<String> {
    let now = Instant::now();
    let mut lines = Vec::new();

    section_guard_state(&mut lines, commands);
    section_active_command(&mut lines, commands, now);
    section_last_command_result(&mut lines, commands);
    section_command_history(&mut lines, commands);
    section_staged_packet(&mut lines, commands);
    section_review_bridge(&mut lines, commands);
    section_git(&mut lines, commands);
    section_memory(&mut lines, commands);
    section_action_catalog(&mut lines, commands);
    section_runtime_snapshot(&mut lines, commands);

    lines
}

fn section_guard_state(lines: &mut Vec<String>, commands: &DevPanelState) {
    lines.push(section_header("Guard State"));
    lines.push(format!(
        "  Exec profile: {}",
        commands.execution_profile().label()
    ));
    lines.push(String::new());
}

fn section_active_command(lines: &mut Vec<String>, commands: &DevPanelState, now: Instant) {
    lines.push(section_header("Active Command"));
    if let Some(label) = commands.running_command_label(now) {
        lines.push(format!("  Running: {label}"));
    } else {
        lines.push("  (idle)".to_string());
    }
    lines.push(String::new());
}

fn section_last_command_result(lines: &mut Vec<String>, commands: &DevPanelState) {
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

fn section_command_history(lines: &mut Vec<String>, commands: &DevPanelState) {
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

fn section_staged_packet(lines: &mut Vec<String>, commands: &DevPanelState) {
    lines.push(section_header("Staged Packet Draft"));
    let Some(packet) = commands
        .last_completion()
        .and_then(|c| c.terminal_packet.as_ref())
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

fn section_review_bridge(lines: &mut Vec<String>, commands: &DevPanelState) {
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

fn section_git(lines: &mut Vec<String>, commands: &DevPanelState) {
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

fn section_memory(lines: &mut Vec<String>, commands: &DevPanelState) {
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

fn section_action_catalog(lines: &mut Vec<String>, commands: &DevPanelState) {
    lines.push(section_header("Action Catalog"));
    let catalog = commands.catalog();
    let read_count = catalog
        .entries()
        .iter()
        .filter(|e| e.category() == crate::dev_command::ActionCategory::ReadOnly)
        .count();
    let mut_count = catalog
        .entries()
        .iter()
        .filter(|e| e.category() == crate::dev_command::ActionCategory::Mutating)
        .count();
    lines.push(format!(
        "  {} actions ({} read-only, {} mutating)",
        catalog.len(),
        read_count,
        mut_count,
    ));
    lines.push(String::new());
}

fn section_runtime_snapshot(lines: &mut Vec<String>, commands: &DevPanelState) {
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

/// Handoff page: resume bundle, controller metadata, boot pack, and
/// a generated fresh-conversation prompt ready for copy/paste.
///
/// Review-channel data (instruction, verdict, findings, scope, questions)
/// is read directly from the loaded `ReviewArtifact` — the same single
/// source of truth that the Control page uses. `HandoffSnapshot` only
/// carries memory-pack, controller, and generated-prompt data.
pub(super) fn handoff_page_lines(commands: &DevPanelState) -> Vec<String> {
    use crate::dev_command::{first_meaningful_line, parse_scope_list};

    let Some(snap) = commands.handoff_snapshot() else {
        return vec![
            section_header("Handoff"),
            "  (no handoff data — switch to this tab to generate)".to_string(),
        ];
    };

    let artifact = commands.review().artifact();
    let mut lines = Vec::new();

    // Resume bundle: current instruction + verdict from review channel.
    lines.push(section_header("Resume Bundle"));
    let instruction = artifact
        .map(|a| first_meaningful_line(&a.instruction))
        .unwrap_or_default();
    if !instruction.is_empty() {
        lines.push(format!("  Instruction: {instruction}"));
    } else {
        lines.push("  Instruction: (none — load Review tab first)".to_string());
    }
    if let Some(a) = artifact {
        let verdict = first_meaningful_line(&a.verdict);
        if !verdict.is_empty() {
            lines.push(format!("  Verdict: {verdict}"));
        }
        if let Some(bridge) = a.bridge_status_summary() {
            lines.push(format!("  Bridge: {bridge}"));
        }
    } else if let Some(error) = commands.review().load_error() {
        lines.push(format!("  Bridge: error: {error}"));
    }
    lines.push(String::new());

    // Open Findings — live blockers the next session needs to know about.
    if let Some(a) = artifact {
        if !a.findings.is_empty() {
            lines.push(section_header("Open Findings"));
            push_trimmed_lines(&mut lines, &a.findings);
            lines.push(String::new());
        }
    }

    // Last Reviewed Scope — files/areas the reviewer has already covered.
    if let Some(a) = artifact {
        let scope_items = parse_scope_list(&a.last_reviewed_scope);
        if !scope_items.is_empty() {
            lines.push(section_header("Last Reviewed Scope"));
            for item in &scope_items {
                lines.push(format!("  - {item}"));
            }
            lines.push(String::new());
        }
    }

    // Claude Questions — open questions from the coder side.
    if let Some(a) = artifact {
        if !a.claude_questions.is_empty() {
            lines.push(section_header("Claude Questions"));
            push_trimmed_lines(&mut lines, &a.claude_questions);
            lines.push(String::new());
        }
    }

    // Controller state: execution profile + last command result.
    lines.push(section_header("Controller State"));
    lines.push(format!("  Profile: {}", snap.execution_profile));
    if !snap.last_command_result.is_empty() {
        lines.push(format!("  Last cmd: {}", snap.last_command_result));
    } else {
        lines.push("  Last cmd: (none)".to_string());
    }
    lines.push(String::new());

    // Git context follows the current shell path when VoiceTerm can resolve
    // the PTY cwd, and falls back to the session launch path otherwise.
    if let Some(git) = commands.git_snapshot() {
        if !git.has_error {
            lines.push(section_header("Git Context (current shell path)"));
            let mut branch_info = format!("  {}", git.branch);
            if git.ahead > 0 || git.behind > 0 {
                branch_info.push_str(&format!(" [ahead {}, behind {}]", git.ahead, git.behind));
            }
            let changes = git.dirty_count + git.untracked_count;
            if changes > 0 {
                branch_info.push_str(&format!(", {} changed", changes));
            } else {
                branch_info.push_str(", clean");
            }
            lines.push(branch_info);
            if !git.last_commit.is_empty() {
                lines.push(format!("  HEAD: {}", git.last_commit));
            }
            lines.push(String::new());
        }
    }

    // Boot pack from memory index.
    lines.push(format!("{} {} Pack", SECTION_GLYPH, snap.pack_type));
    lines.push(format!("  {}", snap.summary));
    lines.push(format!(
        "  Tokens: {}/{} (trimmed: {})",
        snap.token_used, snap.token_target, snap.token_trimmed,
    ));
    lines.push(format!("  Evidence items: {}", snap.evidence_count));
    lines.push(String::new());

    if !snap.active_tasks.is_empty() {
        lines.push(section_header("Active Tasks"));
        for task in &snap.active_tasks {
            lines.push(format!("  - {task}"));
        }
        lines.push(String::new());
    }

    if !snap.recent_decisions.is_empty() {
        lines.push(section_header("Recent Decisions"));
        for decision in &snap.recent_decisions {
            lines.push(format!("  - {decision}"));
        }
        lines.push(String::new());
    }

    // Fresh-conversation prompt (generated, read-only, copy/paste ready).
    if !snap.fresh_prompt.is_empty() {
        lines.push(section_header("Fresh Conversation Prompt"));
        for prompt_line in snap.fresh_prompt.lines() {
            lines.push(format!("  {prompt_line}"));
        }
        lines.push(String::new());
    }

    let has_instruction = artifact.map(|a| !a.instruction.is_empty()).unwrap_or(false);
    if lines.len() <= 5 && snap.evidence_count == 0 && !has_instruction {
        lines.push("  No handoff data available yet. Load the Review".to_string());
        lines.push("  tab and ingest some memory events to populate.".to_string());
    }

    lines
}

pub(super) fn memory_page_lines(commands: &DevPanelState) -> Vec<String> {
    let Some(snapshot) = commands.memory_cockpit_snapshot() else {
        return vec![
            section_header("Memory Studio"),
            "  (no memory preview loaded — switch to this tab or press Enter to refresh)"
                .to_string(),
        ];
    };

    let mut lines = Vec::new();
    lines.push(section_header("Memory Status"));
    if let Some(status) = &snapshot.status {
        lines.push(format!("  Mode: {}", status.mode_label));
        lines.push(format!(
            "  Capture: {}  Retrieval: {}",
            if status.capture_allowed { "on" } else { "off" },
            if status.retrieval_allowed {
                "on"
            } else {
                "off"
            },
        ));
        lines.push(format!(
            "  Events: {} ingested, {} rejected, {} indexed",
            status.events_ingested, status.events_rejected, status.index_size,
        ));
        if !status.session_id.is_empty() {
            lines.push(format!("  Session: {}", status.session_id));
        }
    } else {
        lines.push("  (memory subsystem not initialized)".to_string());
    }
    lines.push(String::new());

    lines.push(section_header("Task Focus"));
    lines.push(format!("  Query: {}", snapshot.task_query));
    lines.push(format!("  Source: {}", snapshot.task_query_source));
    lines.push(String::new());

    for section in &snapshot.sections {
        lines.push(section_header(&section.title));
        if !section.summary.is_empty() {
            lines.push(format!("  {}", section.summary));
        }
        for item in &section.lines {
            lines.push(format!("  {item}"));
        }
        if !section.json_ref.is_empty() {
            lines.push(format!("  Planned JSON: {}", section.json_ref));
        }
        if !section.markdown_ref.is_empty() {
            lines.push(format!("  Planned Markdown: {}", section.markdown_ref));
        }
        lines.push(String::new());
    }

    if !snapshot.context_pack_refs.is_empty() {
        lines.push(section_header("Export Index"));
        for export_ref in &snapshot.context_pack_refs {
            lines.push(format!("  {export_ref}"));
        }
    }

    lines
}

/// Format uptime in a compact human-readable form.
fn format_uptime(secs: f32) -> String {
    if secs < 60.0 {
        format!("{:.0}s", secs)
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

/// Truncate draft text to a bounded number of preview lines.
/// Splits on newlines and caps to `max_lines`, appending a "..." indicator
/// if the original text had more lines.
fn truncate_draft_preview(draft: &str, max_lines: usize) -> Vec<String> {
    let all_lines: Vec<&str> = draft.lines().collect();
    if all_lines.is_empty() {
        return vec!["(empty draft)".to_string()];
    }
    let truncated = all_lines.len() > max_lines;
    let mut result: Vec<String> = all_lines
        .into_iter()
        .take(max_lines)
        .map(|l| l.to_string())
        .collect();
    if truncated {
        result.push("...".to_string());
    }
    result
}
