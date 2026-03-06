use super::*;

impl WriterState {
    pub(crate) fn maybe_redraw_status(&mut self) {
        let now = Instant::now();
        let backend = self.runtime_profile.backend_family;
        let cursor_input_repair_profile = self.runtime_profile.cursor_claude;
        let jetbrains_prompt_guard_profile = self.runtime_profile.claude_jetbrains;
        let claude_cursor_debug = claude_hud_debug_enabled() && cursor_input_repair_profile;
        if !self.needs_redraw {
            if let Some(due) = self.cursor_claude_input_repair_due {
                if cursor_input_repair_profile
                    && self.display.overlay_panel.is_none()
                    && (self.display.enhanced_status.is_some()
                        || self.pending.enhanced_status.is_some())
                    && now >= due
                {
                    self.display.force_full_banner_redraw = true;
                    if cursor_input_repair_profile {
                        self.force_redraw_after_preclear = true;
                    }
                    self.needs_redraw = true;
                    self.cursor_claude_input_repair_due = None;
                    if claude_hud_debug_enabled() {
                        log_debug(
                            "[claude-hud-debug] scheduled cursor+claude HUD repair redraw fired",
                        );
                    }
                } else {
                    return;
                }
            } else {
                return;
            }
        }
        let since_output = now.duration_since(self.last_output_at);
        let since_draw = now.duration_since(self.last_status_draw_at);
        let suppression_transition_pending =
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
                });

        // In Claude/Cursor, keep the HUD stable while the user is actively
        // typing in the composer to prevent cursor flicker and redraw jitter.
        if should_defer_non_urgent_redraw_for_recent_input(
            self.terminal_family(),
            now,
            self.last_user_input_at,
        ) && !self.force_redraw_after_preclear
        {
            let minimal_hud_recovery = cursor_input_repair_profile
                && self.display.overlay_panel.is_none()
                && self.display.enhanced_status.is_some()
                && self.display.banner_height == 1;
            let urgent = self.pending.overlay_panel.is_some()
                || self.pending.clear_overlay
                || self.pending.clear_status
                || suppression_transition_pending;
            if claude_cursor_debug {
                log_debug(&format!(
                    "[claude-hud-debug] redraw deferred for recent input (needs_redraw={}, urgent={}, suppression_transition_pending={}, minimal_hud_recovery={}, pending_has_any={}, force_full={}, force_after_preclear={})",
                    self.needs_redraw,
                    urgent,
                    suppression_transition_pending,
                    minimal_hud_recovery,
                    self.pending.has_any(),
                    self.display.force_full_banner_redraw,
                    self.force_redraw_after_preclear
                ));
            }
            if !urgent && !minimal_hud_recovery {
                return;
            }
        }

        // Prioritize explicit status/overlay updates over passive PTY-driven repaints.
        // This keeps settings navigation and meter changes reactive under heavy backend output.
        let in_resize_repair_window = self
            .jetbrains_claude_resize_repair_until
            .is_some_and(|until| now < until);
        let idle_timing = resolve_idle_redraw_timing(IdleRedrawTimingContext {
            now,
            terminal_family: self.terminal_family(),
            backend_family: backend,
            host_timing: self.host_timing(),
            since_output,
            since_draw,
            suppression_transition_pending,
            force_redraw_after_preclear: self.force_redraw_after_preclear,
            in_resize_repair_window,
            display_force_full_banner_redraw: self.display.force_full_banner_redraw,
            pending_has_any: self.pending.has_any(),
            pending_overlay_panel_present: self.pending.overlay_panel.is_some(),
            pending_clear_overlay: self.pending.clear_overlay,
            pending_clear_status: self.pending.clear_status,
            jetbrains_composer_repair_due: self.jetbrains_claude_composer_repair_due,
            jetbrains_repair_skip_quiet_window: self.jetbrains_claude_repair_skip_quiet_window,
            jetbrains_dec_cursor_saved_active: self.jetbrains_dec_cursor_saved_active,
            jetbrains_ansi_cursor_saved_active: self.jetbrains_ansi_cursor_saved_active,
            jetbrains_cursor_restore_settle_until: self.jetbrains_cursor_restore_settle_until,
        });
        if idle_timing.clear_cursor_restore_settle_until {
            self.jetbrains_cursor_restore_settle_until = None;
        }
        if idle_timing.defer_redraw {
            return;
        }
        // Clear/transition redraws are anchor-sensitive. Refresh terminal size
        // once before clearing so stale row/col caches do not place the HUD at
        // a wrong origin after prompt/tool phases.
        if self.pending.clear_status
            || self.pending.clear_overlay
            || self.force_redraw_after_preclear
        {
            if let Ok((c, r)) = read_terminal_size() {
                if is_transient_jetbrains_claude_geometry_collapse(
                    jetbrains_prompt_guard_profile,
                    self.rows,
                    self.cols,
                    r,
                    c,
                ) {
                    if claude_hud_debug_enabled() {
                        log_debug(&format!(
                            "[claude-hud-debug] ignoring transient redraw geometry sample (current_rows={}, current_cols={}, measured_rows={}, measured_cols={})",
                            self.rows, self.cols, r, c
                        ));
                    }
                } else if self.rows != r || self.cols != c {
                    self.rows = r;
                    self.cols = c;
                    self.pty_line_col_estimate = 0;
                }
            }
        }
        if self.rows == 0 || self.cols == 0 {
            if let Ok((c, r)) = read_terminal_size() {
                if !is_transient_jetbrains_claude_geometry_collapse(
                    jetbrains_prompt_guard_profile,
                    self.rows,
                    self.cols,
                    r,
                    c,
                ) {
                    self.rows = r;
                    self.cols = c;
                }
            }
        }
        if self.rows == 0 || self.cols == 0 {
            // Keep pending redraw state intact and retry on the next writer tick.
            // This prevents startup HUD loss when IDE terminals briefly report no size.
            return;
        }
        let previous_banner_height = self.display.banner_height;
        let previous_hud_style = self
            .display
            .enhanced_status
            .as_ref()
            .map(|state| state.hud_style);
        let previous_prompt_suppressed = self
            .display
            .enhanced_status
            .as_ref()
            .map(|state| state.prompt_suppressed);
        let terminal_family = self.runtime_profile.terminal_family;
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

        let flush_error = {
            let force_redraw_after_preclear = self.force_redraw_after_preclear;
            let rows = self.rows;
            let cols = self.cols;
            let theme = self.theme;
            let (
                stdout,
                overlay_panel,
                enhanced_status,
                status,
                current_banner_height,
                preclear_banner_height,
                banner_anchor_row,
                current_banner_lines,
                force_full_banner_redraw,
            ) = (
                &mut self.stdout,
                &self.display.overlay_panel,
                &self.display.enhanced_status,
                &self.display.status,
                &mut self.display.banner_height,
                &mut self.display.preclear_banner_height,
                &mut self.display.banner_anchor_row,
                &mut self.display.banner_lines,
                &mut self.display.force_full_banner_redraw,
            );
            if let Some(panel) = overlay_panel.as_ref() {
                let _ = write_overlay_panel(stdout, panel, rows, cols);
            } else if let Some(state) = enhanced_status.as_ref() {
                let mut render_state = state.clone();
                if jetbrains_prompt_guard_profile
                    && !render_state.prompt_suppressed
                    && render_state.hud_style == HudStyle::Full
                {
                    // JetBrains+Claude fallback: keep full-HUD semantics but collapse
                    // the full frame into a single-line strip to avoid row drift under
                    // synchronized clear/redraw bursts in JetBrains.
                    if claude_hud_debug_enabled() {
                        log_debug(
                            "[claude-hud-debug] applying jetbrains+claude full-hud one-line fallback",
                        );
                    }
                    render_state.hud_border_style = HudBorderStyle::None;
                    render_state.full_hud_single_line = true;
                }
                let banner = format_status_banner(&render_state, theme, cols as usize);
                let new_anchor_row = if banner.height == 0 || rows == 0 {
                    None
                } else {
                    Some(
                        rows.saturating_sub(banner.height.min(rows as usize) as u16)
                            .saturating_add(1),
                    )
                };
                if claude_cursor_debug {
                    let next_hud_style = state.hud_style;
                    let next_prompt_suppressed = state.prompt_suppressed;
                    let banner_height_changed = *current_banner_height != banner.height;
                    let hud_changed = previous_hud_style != Some(next_hud_style);
                    let suppression_changed =
                        previous_prompt_suppressed != Some(next_prompt_suppressed);
                    if banner_height_changed || hud_changed || suppression_changed {
                        log_debug(&format!(
                            "[claude-hud-debug] enhanced status render decision (rows={}, cols={}, prev_banner_height={}, next_banner_height={}, prev_anchor_row={:?}, next_anchor_row={:?}, hud_style={:?}, prompt_suppressed={}, message=\"{}\")",
                            rows,
                            cols,
                            *current_banner_height,
                            banner.height,
                            *banner_anchor_row,
                            new_anchor_row,
                            next_hud_style,
                            next_prompt_suppressed,
                            debug_text_preview(&state.message, 72)
                        ));
                    }
                }
                if let (Some(previous_anchor), Some(next_anchor)) =
                    (*banner_anchor_row, new_anchor_row)
                {
                    if previous_anchor != next_anchor && *current_banner_height > 0 {
                        let _ =
                            clear_status_banner_at(stdout, previous_anchor, *current_banner_height);
                    }
                }
                // Avoid full-frame clear on every redraw; only clear when banner shrinks.
                // write_status_banner already clears each line it writes.
                let clear_height =
                    status_clear_height_for_redraw(*current_banner_height, banner.height);
                if clear_height > 0 {
                    let _ = clear_status_banner(stdout, rows, clear_height);
                }
                *current_banner_height = banner.height;
                // Track last non-zero height so pre-clear keeps working during
                // prompt suppression (when format_status_banner returns height 0).
                if banner.height > 0 {
                    *preclear_banner_height = banner.height;
                }
                *banner_anchor_row = new_anchor_row;
                let use_previous_lines = should_use_previous_banner_lines_for_profile(
                    terminal_family,
                    *force_full_banner_redraw,
                    force_redraw_after_preclear,
                );
                if claude_cursor_debug && force_redraw_after_preclear {
                    log_debug(&format!(
                        "[claude-hud-debug] transition redraw mode: {} (force_full_banner_redraw={}, preclear_transition={})",
                        if use_previous_lines { "line-diff" } else { "full" },
                        *force_full_banner_redraw,
                        force_redraw_after_preclear
                    ));
                }
                let previous_lines = if use_previous_lines {
                    Some(current_banner_lines.as_slice())
                } else {
                    None
                };
                let _ = write_status_banner(stdout, &banner, rows, cols, previous_lines);
                *current_banner_lines = banner.lines.clone();
                *force_full_banner_redraw = false;
            } else if let Some(text) = status.as_deref() {
                let _ = write_status_line(stdout, text, rows, cols, theme);
                *banner_anchor_row = None;
                current_banner_lines.clear();
                *force_full_banner_redraw = true;
            }
            stdout.flush().err()
        };
        self.needs_redraw = false;
        self.force_redraw_after_preclear = false;
        if self
            .jetbrains_claude_composer_repair_due
            .is_some_and(|due| now >= due)
        {
            self.jetbrains_claude_composer_repair_due = None;
            self.jetbrains_claude_repair_skip_quiet_window = false;
            if jetbrains_prompt_guard_profile && claude_hud_debug_enabled() {
                log_debug("[claude-hud-debug] jetbrains+claude composer repair redraw committed");
            }
        }
        if self
            .jetbrains_claude_resize_repair_until
            .is_some_and(|until| now >= until)
        {
            self.jetbrains_claude_resize_repair_until = None;
        }
        if self
            .cursor_claude_input_repair_due
            .is_some_and(|due| now >= due)
        {
            self.cursor_claude_input_repair_due = None;
        }
        self.last_status_draw_at = now;
        if claude_cursor_debug {
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
                previous_banner_height != self.display.banner_height,
                previous_hud_style != current_hud_style,
                previous_prompt_suppressed != current_prompt_suppressed
            ));
        }
        if cursor_input_repair_profile && self.display.overlay_panel.is_none() {
            if let Some(state) = self.display.enhanced_status.as_ref() {
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
        if let Some(err) = flush_error {
            log_debug(&format!("status redraw flush failed: {err}"));
        }
    }
}
