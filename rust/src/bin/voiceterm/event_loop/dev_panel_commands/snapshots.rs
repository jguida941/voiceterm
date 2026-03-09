//! Memory, handoff, and context snapshot builders for dev-panel cockpit pages.

use super::super::*;

const MEMORY_EXPORT_ROOT: &str = ".voiceterm/memory/exports";
const MEMORY_TASK_QUERY_FALLBACK: &str = "memory";

fn current_memory_status_snapshot(
    state: &EventLoopState,
) -> Option<crate::dev_command::MemoryStatusSnapshot> {
    state
        .memory_ingestor
        .as_ref()
        .map(|ingestor| crate::dev_command::MemoryStatusSnapshot {
            mode_label: ingestor.mode().display_label().to_string(),
            capture_allowed: ingestor.mode().allows_capture(),
            retrieval_allowed: ingestor.mode().allows_retrieval(),
            events_ingested: ingestor.events_ingested(),
            events_rejected: ingestor.events_rejected(),
            index_size: ingestor.index().len(),
            session_id: ingestor.session_id().to_string(),
        })
}

/// Snapshot memory ingestor state onto DevPanelState for the Control page renderer.
pub(in super::super) fn refresh_memory_snapshot(state: &mut EventLoopState) {
    if let Some(snapshot) = current_memory_status_snapshot(state) {
        state.dev_panel_commands.set_memory_snapshot(snapshot);
    } else {
        state.dev_panel_commands.clear_memory_snapshot();
    }
}

/// Cycle the memory mode on the live ingestor and refresh the Control page snapshot.
pub(in super::super) fn cycle_memory_mode(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    if let Some(next_mode) = state.memory_ingestor.as_mut().map(|ingestor| {
        let next_mode = ingestor.mode().cycle();
        ingestor.set_mode(next_mode);
        next_mode
    }) {
        let snapshot = crate::persistent_config::snapshot_from_runtime_with_memory_mode(
            &state.config,
            &state.status_state,
            state.theme,
            Some(next_mode),
        );
        crate::persistent_config::save_user_config(&snapshot);
        refresh_memory_snapshot(state);
        let label = next_mode.display_label();
        super::set_dev_status(
            state,
            timers,
            deps,
            &format!("Memory mode: {label}"),
            Some(Duration::from_secs(2)),
        );
    } else {
        super::set_dev_status(
            state,
            timers,
            deps,
            "Memory subsystem not initialized",
            Some(Duration::from_secs(2)),
        );
    }
}

/// Build a HandoffSnapshot from the memory index and controller state.
/// Review-channel data is read from `ReviewArtifact` at render time, not
/// stored in the snapshot. All data comes from existing in-memory fields.
pub(in super::super) fn refresh_handoff_snapshot(state: &mut EventLoopState) {
    let mut snapshot = if let Some(ref ingestor) = state.memory_ingestor {
        let pack = crate::memory::context_pack::generate_boot_pack(
            ingestor.index(),
            ingestor.project_id(),
            4096,
        );
        crate::dev_command::HandoffSnapshot {
            pack_type: match pack.pack_type {
                crate::memory::types::ContextPackType::Boot => "Boot".to_string(),
                crate::memory::types::ContextPackType::Task => "Task".to_string(),
            },
            summary: pack.summary,
            active_tasks: pack.active_tasks,
            recent_decisions: pack.recent_decisions,
            evidence_count: pack.evidence.len(),
            token_used: pack.token_budget.used,
            token_target: pack.token_budget.target,
            token_trimmed: pack.token_budget.trimmed,
            ..Default::default()
        }
    } else {
        crate::dev_command::HandoffSnapshot::default()
    };

    // Controller metadata.
    snapshot.execution_profile = state
        .dev_panel_commands
        .execution_profile()
        .label()
        .to_string();
    if let Some(completion) = state.dev_panel_commands.last_completion() {
        snapshot.last_command_result = format!(
            "{} {} ({}ms)",
            completion.command.label(),
            completion.status.label(),
            completion.duration_ms,
        );
    }

    // Git context comes from the cached shell-session snapshot.
    let git_summary = state
        .dev_panel_commands
        .git_snapshot()
        .filter(|g| !g.has_error)
        .map(|g| {
            let mut s = format!("Branch: {}", g.branch);
            if g.ahead > 0 || g.behind > 0 {
                s.push_str(&format!(" [ahead {}, behind {}]", g.ahead, g.behind));
            }
            let changes = g.dirty_count + g.untracked_count;
            if changes > 0 {
                s.push_str(&format!(", {} changed files", changes));
            }
            s
        });

    // Generate the fresh-conversation prompt from collected context.
    // Review-channel data comes directly from the artifact (single source of truth).
    snapshot.fresh_prompt = generate_fresh_prompt(
        &snapshot,
        state.dev_panel_commands.review().artifact(),
        git_summary.as_deref(),
    );

    state.dev_panel_commands.set_handoff_snapshot(snapshot);
}

/// Build a dedicated Memory-page snapshot from the current runtime, review,
/// git, and handoff data. This is a read-only preview surface; it does not
/// write any export files when the operator refreshes the page.
pub(in super::super) fn refresh_memory_cockpit_snapshot(state: &mut EventLoopState) {
    let status = current_memory_status_snapshot(state);
    let (task_query, task_query_source) = select_task_query(state);
    let mut snapshot = crate::dev_command::MemoryCockpitSnapshot {
        status,
        task_query,
        task_query_source,
        sections: Vec::new(),
        context_pack_refs: Vec::new(),
    };

    if let Some(ref ingestor) = state.memory_ingestor {
        let token_budget = crate::memory::context_pack::default_token_budget();
        let boot_pack = crate::memory::context_pack::generate_boot_pack(
            ingestor.index(),
            ingestor.project_id(),
            token_budget,
        );
        let task_pack = crate::memory::context_pack::generate_task_pack(
            ingestor.index(),
            &snapshot.task_query,
            ingestor.project_id(),
            token_budget,
        );
        snapshot.sections.push(section_from_context_pack(
            "Boot Pack",
            "boot_pack",
            &boot_pack,
        ));
        snapshot.sections.push(section_from_context_pack(
            "Task Pack",
            "task_pack",
            &task_pack,
        ));
        snapshot
            .sections
            .push(build_session_handoff_section(state, &boot_pack, &task_pack));
        snapshot
            .sections
            .push(build_survival_index_section(state, &boot_pack, &task_pack));
    } else {
        for (title, slug) in [
            ("Boot Pack", "boot_pack"),
            ("Task Pack", "task_pack"),
            ("Session Handoff", "session_handoff"),
            ("Survival Index", "survival_index"),
        ] {
            let (json_ref, markdown_ref) = planned_export_refs(slug);
            snapshot
                .sections
                .push(crate::dev_command::MemoryPreviewSection {
                    title: title.to_string(),
                    summary: "Memory subsystem not initialized.".to_string(),
                    lines: vec![
                        "Initialize memory capture to build preview packs.".to_string(),
                        "Use the Control or Memory page 'm' key to change runtime memory mode."
                            .to_string(),
                    ],
                    json_ref,
                    markdown_ref,
                });
        }
    }

    snapshot.context_pack_refs = snapshot
        .sections
        .iter()
        .flat_map(|section| [section.json_ref.clone(), section.markdown_ref.clone()])
        .collect();
    state
        .dev_panel_commands
        .set_memory_cockpit_snapshot(snapshot);
}

/// Snapshot terminal/runtime diagnostics onto DevPanelState for the Control page.
pub(in super::super) fn build_runtime_diagnostics_snapshot(
    state: &mut EventLoopState,
    deps: &EventLoopDeps,
) {
    let host = crate::runtime_compat::detect_terminal_host();
    let host_label = match host {
        crate::runtime_compat::TerminalHost::JetBrains => "JetBrains",
        crate::runtime_compat::TerminalHost::Cursor => "Cursor",
        crate::runtime_compat::TerminalHost::Other => "Other",
    };
    let overlay_label = match state.ui.overlay_mode {
        crate::overlays::OverlayMode::None => "None",
        crate::overlays::OverlayMode::DevPanel => "DevPanel",
        crate::overlays::OverlayMode::Help => "Help",
        crate::overlays::OverlayMode::ThemeStudio => "ThemeStudio",
        crate::overlays::OverlayMode::ThemePicker => "ThemePicker",
        crate::overlays::OverlayMode::Settings => "Settings",
        crate::overlays::OverlayMode::TranscriptHistory => "TranscriptHistory",
        crate::overlays::OverlayMode::ToastHistory => "ToastHistory",
    };
    let auto_voice = if state.auto_voice_enabled {
        if state.auto_voice_paused_by_user {
            "Paused"
        } else {
            "Active"
        }
    } else {
        "Off"
    };
    let voice_mode = match state.status_state.voice_mode {
        crate::status_line::VoiceMode::Auto => "Auto",
        crate::status_line::VoiceMode::Manual => "Manual",
        crate::status_line::VoiceMode::Idle => "Idle",
    };
    let recording_state = match state.status_state.recording_state {
        crate::status_line::RecordingState::Idle => "Idle",
        crate::status_line::RecordingState::Recording => "Recording",
        crate::status_line::RecordingState::Processing => "Processing",
        crate::status_line::RecordingState::Responding => "Responding",
    };
    let snapshot = crate::dev_command::RuntimeDiagnosticsSnapshot {
        terminal_host: host_label.to_string(),
        terminal_rows: state.ui.terminal_rows,
        terminal_cols: state.ui.terminal_cols,
        backend_label: deps.backend_label.clone(),
        theme_name: format!("{:?}", state.theme),
        auto_voice: auto_voice.to_string(),
        overlay_mode: overlay_label.to_string(),
        voice_mode: voice_mode.to_string(),
        recording_state: recording_state.to_string(),
        dev_mode: state.config.dev_mode,
        dev_log: state.config.dev_log,
        session_uptime_secs: state.session_stats.session_duration().as_secs_f32(),
        transcripts: state.session_stats.transcripts,
        errors: state.session_stats.errors,
    };
    state.dev_panel_commands.set_runtime_diagnostics(snapshot);
}

/// Build a fresh-conversation bootstrap prompt from snapshot + artifact data.
/// Review-channel fields come directly from the artifact (single source of
/// truth), while memory/controller/git data comes from the snapshot.
fn generate_fresh_prompt(
    snap: &crate::dev_command::HandoffSnapshot,
    artifact: Option<&crate::dev_command::ReviewArtifact>,
    git_summary: Option<&str>,
) -> String {
    use crate::dev_command::{first_meaningful_line, parse_scope_list, push_trimmed_lines};

    let mut parts = Vec::new();

    parts.push("Bootstrap this session from the live review channel:".to_string());
    parts.push(String::new());

    if let Some(a) = artifact {
        let instruction = first_meaningful_line(&a.instruction);
        if !instruction.is_empty() {
            parts.push(format!("Current instruction: {instruction}"));
        }
        let verdict = first_meaningful_line(&a.verdict);
        if !verdict.is_empty() {
            parts.push(format!("Last verdict: {verdict}"));
        }
        if let Some(bridge) = a.bridge_status_summary() {
            parts.push(format!("Review bridge: {bridge}"));
        }
    }
    if !snap.execution_profile.is_empty() {
        parts.push(format!("Execution profile: {}", snap.execution_profile));
    }
    if let Some(git) = git_summary {
        parts.push(format!("Git: {git}"));
    }

    // Live blockers from Open Findings give the new session immediate context.
    if let Some(a) = artifact {
        if !a.findings.is_empty() {
            parts.push(String::new());
            parts.push("Open Findings (live blockers):".to_string());
            push_trimmed_lines(&mut parts, &a.findings);
        }

        let scope_items = parse_scope_list(&a.last_reviewed_scope);
        if !scope_items.is_empty() {
            parts.push(String::new());
            parts.push("Last Reviewed Scope:".to_string());
            for item in &scope_items {
                parts.push(format!("  - {item}"));
            }
        }

        if !a.claude_questions.is_empty() {
            parts.push(String::new());
            parts.push("Claude Questions:".to_string());
            push_trimmed_lines(&mut parts, &a.claude_questions);
        }
    }

    if !snap.summary.is_empty() {
        parts.push(String::new());
        parts.push(format!("Memory summary: {}", snap.summary));
    }

    if !snap.recent_decisions.is_empty() {
        parts.push(String::new());
        parts.push("Recent decisions:".to_string());
        for decision in &snap.recent_decisions {
            parts.push(format!("  - {decision}"));
        }
    }

    if !snap.active_tasks.is_empty() {
        parts.push(String::new());
        parts.push("Active tasks:".to_string());
        for task in &snap.active_tasks {
            parts.push(format!("  - {task}"));
        }
    }

    if !snap.last_command_result.is_empty() {
        parts.push(format!("Last command: {}", snap.last_command_result));
    }

    if snap.evidence_count > 0 {
        parts.push(format!(
            "Memory: {} evidence items, {}/{} tokens",
            snap.evidence_count, snap.token_used, snap.token_target,
        ));
    }

    parts.push(String::new());
    parts.push(
        "Read CLAUDE.md, AGENTS.md, dev/active/INDEX.md, dev/active/MASTER_PLAN.md, and dev/active/review_channel.md to bootstrap."
            .to_string(),
    );

    parts.join("\n")
}

fn select_task_query(state: &EventLoopState) -> (String, String) {
    if let Some(artifact) = state.dev_panel_commands.review().artifact() {
        for text in [
            artifact.instruction.as_str(),
            artifact.findings.as_str(),
            artifact.last_reviewed_scope.as_str(),
            artifact.claude_questions.as_str(),
            artifact.verdict.as_str(),
        ] {
            if let Some(task_ref) = first_task_ref(text) {
                return (task_ref, "review bridge".to_string());
            }
        }
    }

    if let Some(handoff) = state.dev_panel_commands.handoff_snapshot() {
        if let Some(task) = handoff.active_tasks.first().cloned() {
            return (task, "boot pack".to_string());
        }
    }

    (
        MEMORY_TASK_QUERY_FALLBACK.to_string(),
        "fallback".to_string(),
    )
}

fn first_task_ref(text: &str) -> Option<String> {
    for raw_token in text.split_whitespace() {
        let token = raw_token.trim_matches(|c: char| !c.is_ascii_alphanumeric() && c != '-');
        if token.len() > 3
            && token[..3].eq_ignore_ascii_case("mp-")
            && token[3..].chars().all(|ch| ch.is_ascii_digit())
        {
            return Some(format!("MP-{}", &token[3..]));
        }
    }
    None
}

fn section_from_context_pack(
    title: &str,
    slug: &str,
    pack: &crate::memory::types::ContextPack,
) -> crate::dev_command::MemoryPreviewSection {
    let (json_ref, markdown_ref) = planned_export_refs(slug);
    let mut lines = vec![
        format!("Query: {}", pack.query),
        format!("Generated: {}", pack.generated_at),
        format!(
            "Tokens: {}/{} (trimmed: {})",
            pack.token_budget.used, pack.token_budget.target, pack.token_budget.trimmed
        ),
    ];
    if !pack.active_tasks.is_empty() {
        lines.push(format!(
            "Active tasks: {}",
            summarize_list(&pack.active_tasks, 3)
        ));
    }
    if !pack.recent_decisions.is_empty() {
        lines.push(format!(
            "Recent decisions: {}",
            summarize_list(&pack.recent_decisions, 2)
        ));
    }
    if !pack.changed_files.is_empty() {
        lines.push(format!(
            "Changed files: {}",
            summarize_list(&pack.changed_files, 4)
        ));
    }
    if !pack.open_questions.is_empty() {
        lines.push(format!(
            "Open questions: {}",
            summarize_list(&pack.open_questions, 2)
        ));
    }
    if pack.evidence.is_empty() {
        lines.push("Evidence: none captured for this query.".to_string());
    } else {
        lines.push(format!("Evidence items: {}", pack.evidence.len()));
        for evidence in pack.evidence.iter().take(3) {
            lines.push(format!(
                "Evidence: [{}] {:.2} {}",
                evidence.event_id, evidence.score, evidence.text_preview
            ));
        }
    }
    crate::dev_command::MemoryPreviewSection {
        title: title.to_string(),
        summary: pack.summary.clone(),
        lines,
        json_ref,
        markdown_ref,
    }
}

fn build_session_handoff_section(
    state: &EventLoopState,
    boot_pack: &crate::memory::types::ContextPack,
    task_pack: &crate::memory::types::ContextPack,
) -> crate::dev_command::MemoryPreviewSection {
    let (json_ref, markdown_ref) = planned_export_refs("session_handoff");
    let artifact = state.dev_panel_commands.review().artifact();
    let handoff = state.dev_panel_commands.handoff_snapshot();
    let mut lines = Vec::new();
    if let Some(artifact) = artifact {
        let instruction = crate::dev_command::first_meaningful_line(&artifact.instruction);
        if !instruction.is_empty() {
            lines.push(format!("Instruction: {instruction}"));
        }
        let verdict = crate::dev_command::first_meaningful_line(&artifact.verdict);
        if !verdict.is_empty() {
            lines.push(format!("Verdict: {verdict}"));
        }
        if let Some(bridge) = artifact.bridge_status_summary() {
            lines.push(format!("Bridge: {bridge}"));
        }
    } else if let Some(error) = state.dev_panel_commands.review().load_error() {
        lines.push(format!("Bridge: error: {error}"));
    }
    if let Some(git) = state.dev_panel_commands.git_snapshot() {
        if !git.has_error {
            lines.push(format!(
                "Git: {} ({} changed, {} untracked)",
                git.branch, git.dirty_count, git.untracked_count
            ));
        }
    }
    if let Some(handoff) = handoff {
        lines.push(format!("Execution profile: {}", handoff.execution_profile));
        if !handoff.last_command_result.is_empty() {
            lines.push(format!("Last command: {}", handoff.last_command_result));
        }
        if !handoff.fresh_prompt.is_empty() {
            lines.push(format!(
                "Prompt lines: {}",
                handoff.fresh_prompt.lines().count()
            ));
        }
    }
    lines.push(format!("Boot evidence: {}", boot_pack.evidence.len()));
    lines.push(format!("Task evidence: {}", task_pack.evidence.len()));
    crate::dev_command::MemoryPreviewSection {
        title: "Session Handoff".to_string(),
        summary: "Fresh-conversation handoff preview staged from review, git, and memory state."
            .to_string(),
        lines,
        json_ref,
        markdown_ref,
    }
}

fn build_survival_index_section(
    state: &EventLoopState,
    boot_pack: &crate::memory::types::ContextPack,
    task_pack: &crate::memory::types::ContextPack,
) -> crate::dev_command::MemoryPreviewSection {
    let (json_ref, markdown_ref) = planned_export_refs("survival_index");
    let artifact = state.dev_panel_commands.review().artifact();
    let git = state.dev_panel_commands.git_snapshot();
    let memory_mode = current_memory_status_snapshot(state)
        .map(|snapshot| snapshot.mode_label)
        .unwrap_or_else(|| "Not initialized".to_string());
    let mut lines = vec![
        format!("Task focus: {}", task_pack.query),
        format!("Memory mode: {memory_mode}"),
        format!(
            "Review findings: {}",
            artifact
                .map(|value| count_nonempty_lines(&value.findings))
                .unwrap_or(0)
        ),
        format!(
            "Claude questions: {}",
            artifact
                .map(|value| count_nonempty_lines(&value.claude_questions))
                .unwrap_or(0)
        ),
        format!("Active tasks: {}", boot_pack.active_tasks.len()),
        format!("Recent decisions: {}", boot_pack.recent_decisions.len()),
    ];
    if let Some(git) = git {
        if git.has_error {
            lines.push(format!("Git snapshot error: {}", git.error_message));
        } else {
            lines.push(format!(
                "Changed files: {} shown / {} total",
                git.changed_files.len(),
                git.dirty_count + git.untracked_count
            ));
        }
    }
    if let Some(artifact) = artifact {
        if let Some(bridge) = artifact.bridge_status_summary() {
            lines.push(format!("Bridge: {bridge}"));
        }
    }
    crate::dev_command::MemoryPreviewSection {
        title: "Survival Index".to_string(),
        summary: "Operator-focused survival snapshot for the current review loop.".to_string(),
        lines,
        json_ref,
        markdown_ref,
    }
}

fn planned_export_refs(slug: &str) -> (String, String) {
    (
        format!("{MEMORY_EXPORT_ROOT}/{slug}.json"),
        format!("{MEMORY_EXPORT_ROOT}/{slug}.md"),
    )
}

fn summarize_list(items: &[String], limit: usize) -> String {
    let mut preview = items
        .iter()
        .map(|item| crate::dev_command::first_meaningful_line(item))
        .filter(|item| !item.is_empty())
        .take(limit)
        .collect::<Vec<_>>();
    let shown = preview.len();
    let total = items.iter().filter(|item| !item.trim().is_empty()).count();
    if total > shown {
        preview.push(format!("+{} more", total - shown));
    }
    if preview.is_empty() {
        "(none)".to_string()
    } else {
        preview.join(" | ")
    }
}

fn count_nonempty_lines(text: &str) -> usize {
    text.lines().filter(|line| !line.trim().is_empty()).count()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dev_command::ReviewArtifact;

    #[test]
    fn bridge_critical_fresh_prompt_mentions_master_plan_and_git_context() {
        let artifact = ReviewArtifact {
            instruction: "fix the blocker".to_string(),
            ..Default::default()
        };
        let snap = crate::dev_command::HandoffSnapshot {
            execution_profile: "Guarded".to_string(),
            ..Default::default()
        };

        let prompt = generate_fresh_prompt(&snap, Some(&artifact), Some("Branch: develop"));

        assert!(prompt.contains("Git: Branch: develop"));
        assert!(prompt.contains("CLAUDE.md"));
        assert!(prompt.contains("dev/active/MASTER_PLAN.md"));
        assert!(prompt.contains("dev/active/review_channel.md"));
    }

    #[test]
    fn bridge_critical_fresh_prompt_includes_findings_scope_and_questions() {
        let artifact = ReviewArtifact {
            instruction: "fix the blocker".to_string(),
            findings: "- Fix gutter click\n- Verify bridge".to_string(),
            last_reviewed_scope: "- `overlay_mouse.rs`\n- `tests.rs`\n".to_string(),
            claude_questions: "- Is the reducer needed now?".to_string(),
            ..Default::default()
        };
        let snap = crate::dev_command::HandoffSnapshot::default();

        let prompt = generate_fresh_prompt(&snap, Some(&artifact), None);

        assert!(prompt.contains("Open Findings (live blockers):"));
        assert!(prompt.contains("Fix gutter click"));
        assert!(prompt.contains("Last Reviewed Scope:"));
        assert!(prompt.contains("`overlay_mouse.rs`"));
        assert!(prompt.contains("`tests.rs`"));
        assert!(prompt.contains("Claude Questions:"));
        assert!(prompt.contains("Is the reducer needed now?"));
    }

    #[test]
    fn bridge_critical_fresh_prompt_carries_memory_summary_and_decisions() {
        let artifact = ReviewArtifact {
            instruction: "fix the blocker".to_string(),
            ..Default::default()
        };
        let snap = crate::dev_command::HandoffSnapshot {
            summary: "Keep the read-only bridge state intact during resume flows.".to_string(),
            recent_decisions: vec![
                "Stay read-first only.".to_string(),
                "Do not add markdown writers.".to_string(),
            ],
            ..Default::default()
        };

        let prompt = generate_fresh_prompt(&snap, Some(&artifact), None);

        assert!(prompt.contains("Memory summary: Keep the read-only bridge state intact"));
        assert!(prompt.contains("Recent decisions:"));
        assert!(prompt.contains("Stay read-first only."));
        assert!(prompt.contains("Do not add markdown writers."));
    }
}
