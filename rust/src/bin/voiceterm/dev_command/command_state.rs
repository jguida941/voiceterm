//! Dev panel state: selection, confirmation, in-flight tracking, tab + review artifact.

use std::time::Instant;

use super::{
    truncate_chars, ActionCatalog, ActionEntry, DevCommandCompletion, DevCommandKind,
    DevCommandUpdate, DevPanelTab, ExecutionProfile, PolicyOutcome, ReviewArtifactState,
    OUTPUT_EXCERPT_MAX_CHARS,
};

/// Lightweight snapshot for the Handoff page: memory boot pack, controller
/// metadata, and a generated fresh-conversation prompt. Review-channel data
/// (instruction, verdict, findings, scope, questions) is read directly from
/// the loaded `ReviewArtifact` at render time — not stored here.
#[derive(Debug, Clone, Default)]
pub(crate) struct HandoffSnapshot {
    // -- Boot pack fields (from MemoryIndex) --
    pub(crate) pack_type: String,
    pub(crate) summary: String,
    pub(crate) active_tasks: Vec<String>,
    pub(crate) recent_decisions: Vec<String>,
    pub(crate) evidence_count: usize,
    pub(crate) token_used: usize,
    pub(crate) token_target: usize,
    pub(crate) token_trimmed: usize,

    // -- Controller metadata (from DevPanelState) --
    pub(crate) execution_profile: String,
    pub(crate) last_command_result: String,

    // -- Generated fresh-conversation prompt --
    pub(crate) fresh_prompt: String,
}

/// Lightweight snapshot of repo git state for the Control page.
/// Populated by running `git status` and `git log` on tab entry so the
/// renderer never spawns subprocesses or touches disk directly.
#[derive(Debug, Clone, Default)]
pub(crate) struct GitStatusSnapshot {
    pub(crate) branch: String,
    pub(crate) dirty_count: usize,
    pub(crate) untracked_count: usize,
    pub(crate) ahead: usize,
    pub(crate) behind: usize,
    pub(crate) last_commit: String,
    /// Up to 8 changed file paths (status prefix + path) for the Control page.
    pub(crate) changed_files: Vec<String>,
    /// Up to 5 recent commit summaries (oneline format).
    pub(crate) recent_commits: Vec<String>,
    /// Summary line from `git diff --stat` (e.g., "12 files changed, 340 insertions(+), 89 deletions(-)").
    pub(crate) diff_stat: String,
    pub(crate) has_error: bool,
    pub(crate) error_message: String,
}

/// Lightweight snapshot of memory subsystem state for the Control page.
/// Populated from `MemoryIngestor` before rendering so the renderer
/// never touches runtime state directly.
#[derive(Debug, Clone, Default)]
pub(crate) struct MemoryStatusSnapshot {
    pub(crate) mode_label: String,
    pub(crate) capture_allowed: bool,
    pub(crate) retrieval_allowed: bool,
    pub(crate) events_ingested: u64,
    pub(crate) events_rejected: u64,
    pub(crate) index_size: usize,
    pub(crate) session_id: String,
}

/// Compact preview block for one memory-derived export/query surface.
#[derive(Debug, Clone, Default)]
pub(crate) struct MemoryPreviewSection {
    pub(crate) title: String,
    pub(crate) summary: String,
    pub(crate) lines: Vec<String>,
    pub(crate) json_ref: String,
    pub(crate) markdown_ref: String,
}

/// Read-only memory cockpit snapshot for the dedicated Memory tab.
#[derive(Debug, Clone, Default)]
pub(crate) struct MemoryCockpitSnapshot {
    pub(crate) status: Option<MemoryStatusSnapshot>,
    pub(crate) task_query: String,
    pub(crate) task_query_source: String,
    pub(crate) sections: Vec<MemoryPreviewSection>,
    pub(crate) context_pack_refs: Vec<String>,
}

/// Lightweight snapshot of terminal/runtime diagnostics for the Control page.
/// Populated on tab entry so the renderer stays decoupled from live event-loop
/// state.
#[derive(Debug, Clone, Default)]
pub(crate) struct RuntimeDiagnosticsSnapshot {
    pub(crate) terminal_host: String,
    pub(crate) terminal_rows: u16,
    pub(crate) terminal_cols: u16,
    pub(crate) backend_label: String,
    pub(crate) theme_name: String,
    pub(crate) auto_voice: String,
    pub(crate) overlay_mode: String,
    pub(crate) voice_mode: String,
    pub(crate) recording_state: String,
    pub(crate) dev_mode: bool,
    pub(crate) dev_log: bool,
    pub(crate) session_uptime_secs: f32,
    pub(crate) transcripts: u32,
    pub(crate) errors: u32,
}

/// Read-only projection of the latest strict host-process audit.
#[derive(Debug, Clone, Default)]
pub(crate) struct ProcessAuditSnapshot {
    pub(crate) captured_at: String,
    pub(crate) strict: bool,
    pub(crate) total_detected: usize,
    pub(crate) orphaned_count: usize,
    pub(crate) stale_active_count: usize,
    pub(crate) active_recent_count: usize,
    pub(crate) recent_detached_count: usize,
    pub(crate) active_recent_blocking_count: usize,
    pub(crate) active_recent_advisory_count: usize,
    pub(crate) warning_count: usize,
    pub(crate) error_count: usize,
    pub(crate) ok: bool,
    pub(crate) headline: String,
    pub(crate) error_message: String,
}

/// Read-only projection of the latest triage report.
#[derive(Debug, Clone, Default)]
pub(crate) struct OpsTriageSnapshot {
    pub(crate) captured_at: String,
    pub(crate) total_issues: usize,
    pub(crate) high_count: usize,
    pub(crate) medium_count: usize,
    pub(crate) warning_count: usize,
    pub(crate) external_input_count: usize,
    pub(crate) next_action: String,
    pub(crate) summary: String,
    pub(crate) error_message: String,
}

/// Consolidated operational snapshot for the Dev panel Ops page.
#[derive(Debug, Clone, Default)]
pub(crate) struct OpsSnapshot {
    pub(crate) process_audit: ProcessAuditSnapshot,
    pub(crate) triage: OpsTriageSnapshot,
}

/// Maximum number of recent completions to retain for the command history tail.
const MAX_RECENT_COMPLETIONS: usize = 8;

#[derive(Debug, Clone, Copy)]
struct InFlight {
    request_id: u64,
    command: DevCommandKind,
    started_at: Instant,
}

#[derive(Debug, Clone)]
pub(crate) struct DevPanelState {
    catalog: ActionCatalog,
    execution_profile: ExecutionProfile,
    selected_index: usize,
    pending_confirmation: Option<usize>,
    in_flight: Option<InFlight>,
    active_tab: DevPanelTab,
    review: ReviewArtifactState,
    /// Recent command completions, newest last. Capped at `MAX_RECENT_COMPLETIONS`.
    recent_completions: Vec<DevCommandCompletion>,
    /// Scroll offset for Control and Handoff cockpit pages. Resets to 0 on
    /// tab switch so each page starts at the top.
    cockpit_scroll_offset: usize,
    git_snapshot: Option<GitStatusSnapshot>,
    memory_snapshot: Option<MemoryStatusSnapshot>,
    memory_cockpit_snapshot: Option<MemoryCockpitSnapshot>,
    ops_snapshot: Option<OpsSnapshot>,
    handoff_snapshot: Option<HandoffSnapshot>,
    runtime_diagnostics: Option<RuntimeDiagnosticsSnapshot>,
}

impl Default for DevPanelState {
    fn default() -> Self {
        Self {
            catalog: ActionCatalog::default_catalog(),
            execution_profile: ExecutionProfile::default(),
            selected_index: 0,
            pending_confirmation: None,
            in_flight: None,
            active_tab: DevPanelTab::default(),
            review: ReviewArtifactState::default(),
            recent_completions: Vec::new(),
            cockpit_scroll_offset: 0,
            git_snapshot: None,
            memory_snapshot: None,
            memory_cockpit_snapshot: None,
            ops_snapshot: None,
            handoff_snapshot: None,
            runtime_diagnostics: None,
        }
    }
}

impl DevPanelState {
    pub(crate) fn catalog(&self) -> &ActionCatalog {
        &self.catalog
    }

    pub(crate) fn execution_profile(&self) -> ExecutionProfile {
        self.execution_profile
    }

    #[cfg(test)]
    pub(crate) fn set_execution_profile(&mut self, profile: ExecutionProfile) {
        self.execution_profile = profile;
    }

    pub(crate) fn cycle_execution_profile(&mut self) {
        self.execution_profile = self.execution_profile.cycle();
    }

    pub(crate) fn selected_index(&self) -> usize {
        self.selected_index
    }

    pub(crate) fn selected_entry(&self) -> &ActionEntry {
        let clamped = self
            .selected_index
            .min(self.catalog.len().saturating_sub(1));
        &self.catalog.entries()[clamped]
    }

    pub(crate) fn selected_command(&self) -> DevCommandKind {
        self.selected_entry()
            .dev_command()
            .unwrap_or(DevCommandKind::Status)
    }

    pub(crate) fn selected_policy(&self) -> PolicyOutcome {
        self.selected_entry().resolve_policy(self.execution_profile)
    }

    pub(crate) fn active_tab(&self) -> DevPanelTab {
        self.active_tab
    }

    #[cfg(test)]
    pub(crate) fn set_tab(&mut self, tab: DevPanelTab) {
        self.active_tab = tab;
    }

    pub(crate) fn toggle_tab(&mut self) {
        self.active_tab = self.active_tab.next();
        self.cockpit_scroll_offset = 0;
    }

    pub(crate) fn prev_tab(&mut self) {
        self.active_tab = self.active_tab.prev();
        self.cockpit_scroll_offset = 0;
    }

    pub(crate) fn cockpit_scroll_offset(&self) -> usize {
        self.cockpit_scroll_offset
    }

    pub(crate) fn cockpit_scroll_up(&mut self, amount: usize) {
        self.cockpit_scroll_offset = self.cockpit_scroll_offset.saturating_sub(amount);
    }

    pub(crate) fn cockpit_scroll_down(&mut self, amount: usize, max_offset: usize) {
        self.cockpit_scroll_offset = (self.cockpit_scroll_offset + amount).min(max_offset);
    }

    pub(crate) fn review(&self) -> &ReviewArtifactState {
        &self.review
    }

    pub(crate) fn review_mut(&mut self) -> &mut ReviewArtifactState {
        &mut self.review
    }

    pub(crate) fn git_snapshot(&self) -> Option<&GitStatusSnapshot> {
        self.git_snapshot.as_ref()
    }

    pub(crate) fn set_git_snapshot(&mut self, snapshot: GitStatusSnapshot) {
        self.git_snapshot = Some(snapshot);
    }

    pub(crate) fn memory_snapshot(&self) -> Option<&MemoryStatusSnapshot> {
        self.memory_snapshot.as_ref()
    }

    pub(crate) fn set_memory_snapshot(&mut self, snapshot: MemoryStatusSnapshot) {
        self.memory_snapshot = Some(snapshot);
    }

    pub(crate) fn clear_memory_snapshot(&mut self) {
        self.memory_snapshot = None;
    }

    pub(crate) fn memory_cockpit_snapshot(&self) -> Option<&MemoryCockpitSnapshot> {
        self.memory_cockpit_snapshot.as_ref()
    }

    pub(crate) fn set_memory_cockpit_snapshot(&mut self, snapshot: MemoryCockpitSnapshot) {
        self.memory_cockpit_snapshot = Some(snapshot);
    }

    pub(crate) fn ops_snapshot(&self) -> Option<&OpsSnapshot> {
        self.ops_snapshot.as_ref()
    }

    pub(crate) fn set_ops_snapshot(&mut self, snapshot: OpsSnapshot) {
        self.ops_snapshot = Some(snapshot);
    }

    pub(crate) fn handoff_snapshot(&self) -> Option<&HandoffSnapshot> {
        self.handoff_snapshot.as_ref()
    }

    pub(crate) fn set_handoff_snapshot(&mut self, snapshot: HandoffSnapshot) {
        self.handoff_snapshot = Some(snapshot);
    }

    pub(crate) fn runtime_diagnostics(&self) -> Option<&RuntimeDiagnosticsSnapshot> {
        self.runtime_diagnostics.as_ref()
    }

    pub(crate) fn set_runtime_diagnostics(&mut self, snapshot: RuntimeDiagnosticsSnapshot) {
        self.runtime_diagnostics = Some(snapshot);
    }

    pub(crate) fn move_selection(&mut self, delta: i32) {
        if self.catalog.is_empty() {
            self.selected_index = 0;
            return;
        }
        let total = i32::try_from(self.catalog.len()).unwrap_or(1);
        let current = i32::try_from(self.selected_index).unwrap_or(0);
        let next = (current + delta).rem_euclid(total);
        self.selected_index = usize::try_from(next).unwrap_or(0);
        self.pending_confirmation = None;
    }

    pub(crate) fn select_index(&mut self, index: usize) {
        if index < self.catalog.len() {
            self.selected_index = index;
            self.pending_confirmation = None;
        }
    }

    pub(crate) fn request_confirmation_at(&mut self, index: usize) {
        self.pending_confirmation = Some(index);
    }

    pub(crate) fn clear_pending_confirmation(&mut self) {
        self.pending_confirmation = None;
    }

    pub(crate) fn pending_confirmation_index(&self) -> Option<usize> {
        self.pending_confirmation
    }

    pub(crate) fn running_request_id(&self) -> Option<u64> {
        self.in_flight.map(|f| f.request_id)
    }

    pub(crate) fn register_launch(&mut self, request_id: u64, command: DevCommandKind) {
        self.in_flight = Some(InFlight {
            request_id,
            command,
            started_at: Instant::now(),
        });
        self.pending_confirmation = None;
    }

    pub(crate) fn apply_update(&mut self, update: DevCommandUpdate) {
        match update {
            DevCommandUpdate::Started {
                request_id,
                command,
            } => {
                if self
                    .in_flight
                    .is_none_or(|existing| existing.request_id == request_id)
                {
                    self.in_flight = Some(InFlight {
                        request_id,
                        command,
                        started_at: Instant::now(),
                    });
                }
            }
            DevCommandUpdate::Completed(completion) => {
                if self
                    .in_flight
                    .is_some_and(|existing| existing.request_id == completion.request_id)
                {
                    self.in_flight = None;
                }
                self.pending_confirmation = None;
                self.recent_completions.push(completion);
                if self.recent_completions.len() > MAX_RECENT_COMPLETIONS {
                    self.recent_completions.remove(0);
                }
            }
        }
    }

    pub(crate) fn last_completion(&self) -> Option<&DevCommandCompletion> {
        self.recent_completions.last()
    }

    pub(crate) fn latest_completion_for(
        &self,
        command: DevCommandKind,
    ) -> Option<&DevCommandCompletion> {
        self.recent_completions
            .iter()
            .rev()
            .find(|completion| completion.command == command)
    }

    /// All recent completions, oldest first. Capped at 8 entries.
    pub(crate) fn recent_completions(&self) -> &[DevCommandCompletion] {
        &self.recent_completions
    }

    pub(crate) fn running_command_label(&self, now: Instant) -> Option<String> {
        self.in_flight.map(|f| {
            let elapsed = now.duration_since(f.started_at).as_secs_f32();
            format!("{} ({elapsed:.1}s)", f.command.label())
        })
    }

    pub(crate) fn status_for(&self, command: DevCommandKind, now: Instant) -> String {
        if let Some(in_flight) = self.in_flight {
            if in_flight.command == command {
                let elapsed = now.duration_since(in_flight.started_at).as_secs_f32();
                return format!("running ({elapsed:.1}s)");
            }
        }

        if let Some(completion) = self.recent_completions.last() {
            if completion.command == command {
                return format!(
                    "{} ({}ms)",
                    completion.status.label(),
                    completion.duration_ms
                );
            }
        }

        "idle".to_string()
    }

    pub(crate) fn active_summary(&self, now: Instant) -> String {
        if let Some(index) = self.pending_confirmation {
            let label = self
                .catalog
                .get(index)
                .map(super::action_catalog::ActionEntry::label)
                .unwrap_or("unknown");
            return format!("confirm '{}' (press Enter again; Esc/arrows clear)", label);
        }

        if let Some(in_flight) = self.in_flight {
            let elapsed = now.duration_since(in_flight.started_at).as_secs_f32();
            return format!("running '{}' for {elapsed:.1}s", in_flight.command.label());
        }

        "idle".to_string()
    }

    pub(crate) fn last_summary(&self) -> String {
        let Some(completion) = self.recent_completions.last() else {
            return "none".to_string();
        };

        let mut summary = format!(
            "{} {}: {}",
            completion.command.label(),
            completion.status.label(),
            completion.summary
        );

        if let Some(stderr_excerpt) = completion.stderr_excerpt.as_deref() {
            summary.push_str(" | stderr: ");
            summary.push_str(stderr_excerpt);
        } else if let Some(stdout_excerpt) = completion.stdout_excerpt.as_deref() {
            summary.push_str(" | out: ");
            summary.push_str(stdout_excerpt);
        }

        truncate_chars(&summary, OUTPUT_EXCERPT_MAX_CHARS)
    }
}
