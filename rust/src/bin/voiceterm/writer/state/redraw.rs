use super::redraw_support::{
    build_redraw_render_state, redraw_anchor_row, RedrawContext, RedrawSnapshot,
};
use super::*;

impl WriterState {
    pub(crate) fn maybe_redraw_status(&mut self) {
        let context = match self.begin_redraw_cycle() {
            Some(context) => context,
            None => return,
        };
        if !self.refresh_redraw_geometry(&context) {
            return;
        }
        let snapshot = self.capture_redraw_snapshot();
        self.apply_pending_redraw_state();
        let flush_error = self.render_redraw_state(&context, &snapshot);
        self.finish_redraw_cycle(&context, &snapshot, flush_error);
    }

    fn begin_redraw_cycle(&mut self) -> Option<RedrawContext> {
        let context = RedrawContext {
            now: Instant::now(),
            cursor_input_repair_profile: self.runtime_profile.cursor_claude,
            jetbrains_prompt_guard_profile: self.runtime_profile.claude_jetbrains,
            claude_cursor_debug: claude_hud_debug_enabled() && self.runtime_profile.cursor_claude,
            suppression_transition_pending: self.suppression_transition_pending(),
        };
        if !self.arm_due_cursor_claude_repair(&context) {
            return None;
        }
        if self.should_defer_redraw_for_recent_input(&context) {
            return None;
        }
        if self.should_defer_redraw_for_idle_timing(&context) {
            return None;
        }
        Some(context)
    }

    fn suppression_transition_pending(&self) -> bool {
        self.pending
            .enhanced_status
            .as_ref()
            .is_some_and(|pending_state| {
                self.display.enhanced_status.as_ref().map_or(
                    // Transition updates immediately following ClearStatus
                    // have no display snapshot but still need urgent redraw.
                    self.display.preclear_banner_height > 0,
                    |display_state| {
                        pending_state.prompt_suppressed != display_state.prompt_suppressed
                    },
                )
            })
    }

    fn arm_due_cursor_claude_repair(&mut self, context: &RedrawContext) -> bool {
        if self.needs_redraw {
            return true;
        }
        let Some(due) = self.adapter_state.cursor_claude_input_repair_due() else {
            return false;
        };
        let repair_ready = context.cursor_input_repair_profile
            && self.display.overlay_panel.is_none()
            && (self.display.enhanced_status.is_some() || self.pending.enhanced_status.is_some())
            && context.now >= due;
        if !repair_ready {
            return false;
        }
        self.display.force_full_banner_redraw = true;
        self.force_redraw_after_preclear = true;
        self.needs_redraw = true;
        self.adapter_state.set_cursor_claude_input_repair_due(None);
        if claude_hud_debug_enabled() {
            log_debug("[claude-hud-debug] scheduled cursor+claude HUD repair redraw fired");
        }
        true
    }

    fn should_defer_redraw_for_recent_input(&self, context: &RedrawContext) -> bool {
        // In Claude/Cursor, keep the HUD stable while the user is actively
        // typing in the composer to prevent cursor flicker and redraw jitter.
        if !should_defer_non_urgent_redraw_for_recent_input(
            self.terminal_family(),
            context.now,
            self.last_user_input_at,
        ) || self.force_redraw_after_preclear
        {
            return false;
        }
        let minimal_hud_recovery = context.cursor_input_repair_profile
            && self.display.overlay_panel.is_none()
            && self.display.enhanced_status.is_some()
            && self.display.banner_height == 1;
        let urgent = self.pending.overlay_panel.is_some()
            || self.pending.clear_overlay
            || self.pending.clear_status
            || context.suppression_transition_pending;
        if context.claude_cursor_debug {
            log_debug(&format!(
                "[claude-hud-debug] redraw deferred for recent input (needs_redraw={}, urgent={}, suppression_transition_pending={}, minimal_hud_recovery={}, pending_has_any={}, force_full={}, force_after_preclear={})",
                self.needs_redraw,
                urgent,
                context.suppression_transition_pending,
                minimal_hud_recovery,
                self.pending.has_any(),
                self.display.force_full_banner_redraw,
                self.force_redraw_after_preclear
            ));
        }
        !urgent && !minimal_hud_recovery
    }

    fn should_defer_redraw_for_idle_timing(&mut self, context: &RedrawContext) -> bool {
        let idle_timing = resolve_idle_redraw_timing(IdleRedrawTimingContext {
            now: context.now,
            runtime_variant: self.runtime_profile.runtime_variant,
            host_timing: self.host_timing(),
            since_output: context.now.duration_since(self.last_output_at),
            since_draw: context.now.duration_since(self.last_status_draw_at),
            suppression_transition_pending: context.suppression_transition_pending,
            force_redraw_after_preclear: self.force_redraw_after_preclear,
            in_resize_repair_window: self
                .adapter_state
                .jetbrains_claude_resize_repair_until()
                .is_some_and(|until| context.now < until),
            display_force_full_banner_redraw: self.display.force_full_banner_redraw,
            pending_has_any: self.pending.has_any(),
            pending_overlay_panel_present: self.pending.overlay_panel.is_some(),
            pending_clear_overlay: self.pending.clear_overlay,
            pending_clear_status: self.pending.clear_status,
            jetbrains_composer_repair_due: self
                .adapter_state
                .jetbrains_claude_composer_repair_due(),
            jetbrains_repair_skip_quiet_window: self
                .adapter_state
                .jetbrains_claude_repair_skip_quiet_window(),
            jetbrains_dec_cursor_saved_active: self
                .adapter_state
                .jetbrains_dec_cursor_saved_active(),
            jetbrains_ansi_cursor_saved_active: self
                .adapter_state
                .jetbrains_ansi_cursor_saved_active(),
            jetbrains_cursor_restore_settle_until: self
                .adapter_state
                .jetbrains_cursor_restore_settle_until(),
        });
        if idle_timing.clear_cursor_restore_settle_until {
            self.adapter_state
                .set_jetbrains_cursor_restore_settle_until(None);
        }
        idle_timing.defer_redraw
    }

    fn refresh_redraw_geometry(&mut self, context: &RedrawContext) -> bool {
        if self.pending.clear_status
            || self.pending.clear_overlay
            || self.force_redraw_after_preclear
        {
            self.refresh_terminal_size_sample(context.jetbrains_prompt_guard_profile);
        }
        if self.rows == 0 || self.cols == 0 {
            self.refresh_terminal_size_if_missing(context.jetbrains_prompt_guard_profile);
        }
        if self.rows != 0 && self.cols != 0 {
            return true;
        }
        // Keep pending redraw state intact and retry on the next writer tick.
        // This prevents startup HUD loss when IDE terminals briefly report no size.
        false
    }

    fn refresh_terminal_size_sample(&mut self, jetbrains_prompt_guard_profile: bool) {
        let Ok((cols, rows)) = read_terminal_size() else {
            return;
        };
        if is_transient_jetbrains_claude_geometry_collapse(
            jetbrains_prompt_guard_profile,
            self.rows,
            self.cols,
            rows,
            cols,
        ) {
            if claude_hud_debug_enabled() {
                log_debug(&format!(
                    "[claude-hud-debug] ignoring transient redraw geometry sample (current_rows={}, current_cols={}, measured_rows={}, measured_cols={})",
                    self.rows, self.cols, rows, cols
                ));
            }
            return;
        }
        if self.rows != rows || self.cols != cols {
            self.rows = rows;
            self.cols = cols;
            self.pty_line_col_estimate = 0;
        }
    }

    fn refresh_terminal_size_if_missing(&mut self, jetbrains_prompt_guard_profile: bool) {
        let Ok((cols, rows)) = read_terminal_size() else {
            return;
        };
        if is_transient_jetbrains_claude_geometry_collapse(
            jetbrains_prompt_guard_profile,
            self.rows,
            self.cols,
            rows,
            cols,
        ) {
            return;
        }
        self.rows = rows;
        self.cols = cols;
    }

    fn capture_redraw_snapshot(&self) -> RedrawSnapshot {
        RedrawSnapshot {
            previous_banner_height: self.display.banner_height,
            previous_hud_style: self
                .display
                .enhanced_status
                .as_ref()
                .map(|state| state.hud_style),
            previous_prompt_suppressed: self
                .display
                .enhanced_status
                .as_ref()
                .map(|state| state.prompt_suppressed),
        }
    }

    fn apply_pending_redraw_state(&mut self) {
        if self.pending.clear_status {
            let current_banner_height = self.display.banner_height;
            if current_banner_height > 1 {
                let _ = clear_status_banner(&mut self.stdout, self.rows, current_banner_height);
            } else {
                let _ = clear_status_line(&mut self.stdout, self.rows, self.cols);
            }
            self.display.status = None;
            self.display.enhanced_status = None;
            self.display.banner_height = 0;
            self.display.banner_anchor_row = None;
            self.display.banner_lines.clear();
            self.display.force_full_banner_redraw = true;
            self.pending.clear_status = false;
        }
        if self.pending.clear_overlay {
            if let Some(panel) = self.display.overlay_panel.as_ref() {
                let _ = clear_overlay_panel(&mut self.stdout, self.rows, panel.height);
            }
            self.display.overlay_panel = None;
            // Overlay clears underlying rows; force next HUD paint to redraw all banner lines.
            self.display.banner_lines.clear();
            self.display.force_full_banner_redraw = true;
            self.pending.clear_overlay = false;
        }
        if let Some(panel) = self.pending.overlay_panel.as_ref() {
            if let Some(current) = self.display.overlay_panel.as_ref() {
                if current.height != panel.height {
                    let _ = clear_overlay_panel(&mut self.stdout, self.rows, current.height);
                }
            }
        }
        if let Some(panel) = self.pending.overlay_panel.take() {
            self.display.overlay_panel = Some(panel);
        }
        if let Some(state) = self.pending.enhanced_status.take() {
            self.display.enhanced_status = Some(state);
            self.display.status = None;
        }
        if let Some(text) = self.pending.status.take() {
            self.display.status = Some(text);
            self.display.enhanced_status = None;
        }
    }

    fn render_redraw_state(
        &mut self,
        context: &RedrawContext,
        snapshot: &RedrawSnapshot,
    ) -> Option<io::Error> {
        let rows = self.rows;
        let cols = self.cols;
        let theme = self.theme;
        if let Some(panel) = self.display.overlay_panel.as_ref() {
            let _ = write_overlay_panel(&mut self.stdout, panel, rows, cols);
        } else if let Some(state) = self.display.enhanced_status.as_ref().cloned() {
            self.render_enhanced_status(&state, context, snapshot);
        } else if let Some(text) = self.display.status.as_deref() {
            let _ = write_status_line(&mut self.stdout, text, rows, cols, theme);
            self.display.banner_anchor_row = None;
            self.display.banner_lines.clear();
            self.display.force_full_banner_redraw = true;
        }
        self.stdout.flush().err()
    }

    fn render_enhanced_status(
        &mut self,
        state: &crate::status_line::StatusLineState,
        context: &RedrawContext,
        snapshot: &RedrawSnapshot,
    ) {
        let render_state = build_redraw_render_state(state, context.jetbrains_prompt_guard_profile);
        let banner = format_status_banner(&render_state, self.theme, self.cols as usize);
        let new_anchor_row = redraw_anchor_row(self.rows, banner.height);
        if context.claude_cursor_debug {
            let banner_height_changed = self.display.banner_height != banner.height;
            let hud_changed = snapshot.previous_hud_style != Some(state.hud_style);
            let suppression_changed =
                snapshot.previous_prompt_suppressed != Some(state.prompt_suppressed);
            if banner_height_changed || hud_changed || suppression_changed {
                log_debug(&format!(
                    "[claude-hud-debug] enhanced status render decision (rows={}, cols={}, prev_banner_height={}, next_banner_height={}, prev_anchor_row={:?}, next_anchor_row={:?}, hud_style={:?}, prompt_suppressed={}, message=\"{}\")",
                    self.rows,
                    self.cols,
                    self.display.banner_height,
                    banner.height,
                    self.display.banner_anchor_row,
                    new_anchor_row,
                    state.hud_style,
                    state.prompt_suppressed,
                    debug_text_preview(&state.message, 72)
                ));
            }
        }
        if let (Some(previous_anchor), Some(next_anchor)) =
            (self.display.banner_anchor_row, new_anchor_row)
        {
            if previous_anchor != next_anchor && self.display.banner_height > 0 {
                let _ = clear_status_banner_at(
                    &mut self.stdout,
                    previous_anchor,
                    self.display.banner_height,
                );
            }
        }
        let clear_height =
            status_clear_height_for_redraw(self.display.banner_height, banner.height);
        if clear_height > 0 {
            let _ = clear_status_banner(&mut self.stdout, self.rows, clear_height);
        }
        self.display.banner_height = banner.height;
        // Track last non-zero height so pre-clear keeps working during
        // prompt suppression (when format_status_banner returns height 0).
        if banner.height > 0 {
            self.display.preclear_banner_height = banner.height;
        }
        self.display.banner_anchor_row = new_anchor_row;
        let use_previous_lines = should_use_previous_banner_lines_for_profile(
            self.runtime_profile.terminal_family,
            self.display.force_full_banner_redraw,
            self.force_redraw_after_preclear,
        );
        if context.claude_cursor_debug && self.force_redraw_after_preclear {
            log_debug(&format!(
                "[claude-hud-debug] transition redraw mode: {} (force_full_banner_redraw={}, preclear_transition={})",
                if use_previous_lines { "line-diff" } else { "full" },
                self.display.force_full_banner_redraw,
                self.force_redraw_after_preclear
            ));
        }
        let previous_lines = if use_previous_lines {
            Some(self.display.banner_lines.as_slice())
        } else {
            None
        };
        let _ = write_status_banner(
            &mut self.stdout,
            &banner,
            self.rows,
            self.cols,
            previous_lines,
        );
        self.display.banner_lines = banner.lines.clone();
        self.display.force_full_banner_redraw = false;
    }

    fn finish_redraw_cycle(
        &mut self,
        context: &RedrawContext,
        snapshot: &RedrawSnapshot,
        flush_error: Option<io::Error>,
    ) {
        self.needs_redraw = false;
        self.force_redraw_after_preclear = false;
        self.clear_committed_redraw_deadlines(context);
        self.last_status_draw_at = context.now;
        self.log_redraw_commit(context, snapshot);
        self.log_cursor_claude_redraw_anomalies(context);
        if let Some(err) = flush_error {
            log_debug(&format!("status redraw flush failed: {err}"));
        }
    }

    fn clear_committed_redraw_deadlines(&mut self, context: &RedrawContext) {
        if self
            .adapter_state
            .jetbrains_claude_composer_repair_due()
            .is_some_and(|due| context.now >= due)
        {
            self.adapter_state
                .set_jetbrains_claude_composer_repair_due(None);
            self.adapter_state
                .set_jetbrains_claude_repair_skip_quiet_window(false);
            if context.jetbrains_prompt_guard_profile && claude_hud_debug_enabled() {
                log_debug("[claude-hud-debug] jetbrains+claude composer repair redraw committed");
            }
        }
        if self
            .adapter_state
            .jetbrains_claude_resize_repair_until()
            .is_some_and(|until| context.now >= until)
        {
            self.adapter_state
                .set_jetbrains_claude_resize_repair_until(None);
        }
        if self
            .adapter_state
            .cursor_claude_input_repair_due()
            .is_some_and(|due| context.now >= due)
        {
            self.adapter_state.set_cursor_claude_input_repair_due(None);
        }
    }

    fn log_redraw_commit(&self, context: &RedrawContext, snapshot: &RedrawSnapshot) {
        if !context.claude_cursor_debug {
            return;
        }
        let current_hud_style = self
            .display
            .enhanced_status
            .as_ref()
            .map(|state| state.hud_style);
        let current_prompt_suppressed = self
            .display
            .enhanced_status
            .as_ref()
            .map(|state| state.prompt_suppressed);
        log_debug(&format!(
            "[claude-hud-debug] redraw committed (rows={}, cols={}, banner_height={}, anchor_row={:?}, has_enhanced={}, has_overlay={}, has_status={}, hud_style={:?}, prompt_suppressed={:?}, changed_banner_height={}, changed_hud_style={}, changed_prompt_suppressed={})",
            self.rows,
            self.cols,
            self.display.banner_height,
            self.display.banner_anchor_row,
            self.display.enhanced_status.is_some(),
            self.display.overlay_panel.is_some(),
            self.display.status.is_some(),
            current_hud_style,
            current_prompt_suppressed,
            snapshot.previous_banner_height != self.display.banner_height,
            snapshot.previous_hud_style != current_hud_style,
            snapshot.previous_prompt_suppressed != current_prompt_suppressed
        ));
    }

    fn log_cursor_claude_redraw_anomalies(&self, context: &RedrawContext) {
        if !context.cursor_input_repair_profile || self.display.overlay_panel.is_some() {
            return;
        }
        let Some(state) = self.display.enhanced_status.as_ref() else {
            return;
        };
        if !state.prompt_suppressed && self.display.banner_height == 0 {
            log_claude_hud_anomaly(&format!(
                "unsuppressed HUD committed with zero banner height (rows={}, cols={}, anchor_row={:?}, hud_style={:?}, needs_redraw={})",
                self.rows,
                self.cols,
                self.display.banner_anchor_row,
                state.hud_style,
                self.needs_redraw
            ));
        }
        if state.prompt_suppressed && self.display.banner_height > 0 {
            log_claude_hud_anomaly(&format!(
                "suppressed HUD committed with non-zero banner height (rows={}, cols={}, banner_height={}, anchor_row={:?}, hud_style={:?})",
                self.rows,
                self.cols,
                self.display.banner_height,
                self.display.banner_anchor_row,
                state.hud_style
            ));
        }
    }
}
