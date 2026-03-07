use super::*;

impl WriterState {
    pub(super) fn dispatch_message(&mut self, message: WriterMessage) -> bool {
        match message {
            WriterMessage::PtyOutput(bytes) => self.handle_pty_output(bytes),
            WriterMessage::Status { text } => {
                self.pending.status = Some(text);
                self.pending.enhanced_status = None;
                self.needs_redraw = true;
                self.maybe_redraw_status();
                true
            }
            WriterMessage::EnhancedStatus(state) => {
                if claude_hud_debug_enabled() && self.runtime_profile.cursor_claude {
                    log_debug(&format!(
                        "[claude-hud-debug] writer received EnhancedStatus (rows={}, cols={}, hud_style={:?}, prompt_suppressed={}, message=\"{}\")",
                        self.rows,
                        self.cols,
                        state.hud_style,
                        state.prompt_suppressed,
                        debug_text_preview(&state.message, 72)
                    ));
                }
                self.pending.enhanced_status = Some(state);
                self.pending.status = None;
                self.needs_redraw = true;
                self.maybe_redraw_status();
                true
            }
            WriterMessage::ShowOverlay { content, height } => {
                self.pending.overlay_panel = Some(OverlayPanel { content, height });
                self.pending.clear_overlay = false;
                self.needs_redraw = true;
                self.maybe_redraw_status();
                true
            }
            WriterMessage::ClearOverlay => {
                self.pending.overlay_panel = None;
                self.pending.clear_overlay = true;
                self.needs_redraw = true;
                self.maybe_redraw_status();
                true
            }
            WriterMessage::ClearStatus => {
                if claude_hud_debug_enabled() && self.runtime_profile.cursor_claude {
                    let hud_style = self
                        .display
                        .enhanced_status
                        .as_ref()
                        .map(|state| state.hud_style);
                    let prompt_suppressed = self
                        .display
                        .enhanced_status
                        .as_ref()
                        .map(|state| state.prompt_suppressed);
                    log_debug(&format!(
                        "[claude-hud-debug] writer received ClearStatus (rows={}, cols={}, banner_height={}, anchor_row={:?}, hud_style={:?}, prompt_suppressed={:?})",
                        self.rows,
                        self.cols,
                        self.display.banner_height,
                        self.display.banner_anchor_row,
                        hud_style,
                        prompt_suppressed
                    ));
                }
                self.pending.status = None;
                self.pending.enhanced_status = None;
                self.pending.clear_status = true;
                // Clear transitions should not wait behind output-throttle windows.
                self.force_redraw_after_preclear = true;
                self.needs_redraw = true;
                self.maybe_redraw_status();
                true
            }
            WriterMessage::Bell { count } => {
                let sequence = vec![0x07; count.max(1) as usize];
                if let Err(err) = self.stdout.write_all(&sequence) {
                    log_debug(&format!("bell write failed: {err}"));
                }
                if let Err(err) = self.stdout.flush() {
                    log_debug(&format!("bell flush failed: {err}"));
                }
                true
            }
            WriterMessage::Resize { rows, cols } => self.handle_resize_message(rows, cols),
            WriterMessage::SetTheme(new_theme) => {
                self.theme = new_theme;
                if self.display.has_any() {
                    self.needs_redraw = true;
                }
                true
            }
            WriterMessage::EnableMouse => {
                enable_mouse(&mut self.stdout, &mut self.mouse_enabled);
                true
            }
            WriterMessage::DisableMouse => {
                disable_mouse(&mut self.stdout, &mut self.mouse_enabled);
                true
            }
            WriterMessage::UserInputActivity => self.handle_user_input_activity(),
            WriterMessage::Shutdown => self.handle_shutdown_message(),
        }
    }

    fn handle_resize_message(&mut self, rows: u16, cols: u16) -> bool {
        if is_transient_jetbrains_claude_geometry_collapse(
            self.runtime_profile.claude_jetbrains,
            self.rows,
            self.cols,
            rows,
            cols,
        ) {
            if claude_hud_debug_enabled() {
                log_debug(&format!(
                    "[claude-hud-debug] ignoring transient resize collapse sample (current_rows={}, current_cols={}, new_rows={}, new_cols={})",
                    self.rows, self.cols, rows, cols
                ));
            }
            return true;
        }
        if self.rows == rows && self.cols == cols {
            return true;
        }
        if claude_hud_debug_enabled() && self.runtime_profile.cursor_claude {
            log_debug(&format!(
                "[claude-hud-debug] writer received Resize (old_rows={}, old_cols={}, new_rows={}, new_cols={})",
                self.rows, self.cols, rows, cols
            ));
        }
        if self.rows > 0 {
            // Clear HUD/overlay at the old terminal geometry before moving to the new one.
            // This prevents stale frames when startup rows are briefly reported incorrectly.
            if let Some(anchor_row) = self.display.banner_anchor_row {
                if self.display.banner_height > 0 {
                    let _ = clear_status_banner_at(
                        &mut self.stdout,
                        anchor_row,
                        self.display.banner_height,
                    );
                }
            }
            if let Some(panel) = self.display.overlay_panel.as_ref() {
                let _ = clear_overlay_panel(&mut self.stdout, self.rows, panel.height);
            }
            if self.display.banner_height > 1 {
                let _ =
                    clear_status_banner(&mut self.stdout, self.rows, self.display.banner_height);
            } else if self.display.status.is_some() || self.display.enhanced_status.is_some() {
                let _ = clear_status_line(&mut self.stdout, self.rows, self.cols.max(1));
            }
            self.display.banner_lines.clear();
            self.display.banner_anchor_row = None;
            self.display.force_full_banner_redraw = true;
            let _ = self.stdout.flush();
        }
        self.rows = rows;
        self.cols = cols;
        self.pty_line_col_estimate = 0;
        self.force_redraw_after_preclear = false;
        let cursor_timing = HostTimingConfig::for_host(TerminalHost::Cursor);
        let scroll_redraw_min_interval = self
            .runtime_profile
            .scroll_redraw_min_interval
            .unwrap_or_default();
        self.last_preclear_at = Instant::now() - cursor_timing.preclear_cooldown();
        self.last_scroll_redraw_at = Instant::now() - scroll_redraw_min_interval;
        self.adapter_state
            .set_cursor_startup_scroll_preclear_pending(true);
        self.adapter_state
            .set_jetbrains_dec_cursor_saved_active(false);
        self.adapter_state
            .set_jetbrains_ansi_cursor_saved_active(false);
        self.adapter_state
            .set_jetbrains_cursor_restore_settle_until(None);
        self.adapter_state.clear_jetbrains_cursor_escape_carry();
        self.adapter_state
            .set_jetbrains_claude_composer_repair_due(None);
        self.adapter_state
            .set_jetbrains_claude_repair_skip_quiet_window(false);
        if self.display.has_any() || self.pending.has_any() {
            self.needs_redraw = true;
            self.force_redraw_after_preclear = true;
        }
        if self.runtime_profile.claude_jetbrains {
            self.adapter_state
                .set_jetbrains_claude_resize_repair_until(Some(
                    Instant::now()
                        + self
                            .host_timing()
                            .claude_resize_repair_window()
                            .unwrap_or_default(),
                ));
        }
        self.maybe_redraw_status();
        true
    }

    fn handle_user_input_activity(&mut self) -> bool {
        let now = Instant::now();
        self.last_user_input_at = now;
        let cursor_input_repair_profile = self.runtime_profile.cursor_claude;
        if cursor_input_repair_profile
            && self.display.overlay_panel.is_none()
            && (self.display.enhanced_status.is_some() || self.pending.enhanced_status.is_some())
        {
            // Cursor+Claude typing bursts can clear HUD rows without an obvious
            // scroll signal. Schedule a low-rate repair redraw after typing settles.
            let repair_due = now
                + self
                    .host_timing()
                    .claude_input_repair_delay()
                    .unwrap_or_default();
            self.adapter_state
                .set_cursor_claude_input_repair_due(Some(repair_due));
            if claude_hud_debug_enabled() {
                let hud_style = self
                    .display
                    .enhanced_status
                    .as_ref()
                    .map(|state| state.hud_style);
                let prompt_suppressed = self
                    .display
                    .enhanced_status
                    .as_ref()
                    .map(|state| state.prompt_suppressed);
                log_debug(&format!(
                    "[claude-hud-debug] user input activity (rows={}, cols={}, banner_height={}, anchor_row={:?}, hud_style={:?}, prompt_suppressed={:?}, repair_due_in_ms={})",
                    self.rows,
                    self.cols,
                    self.display.banner_height,
                    self.display.banner_anchor_row,
                    hud_style,
                    prompt_suppressed,
                    repair_due.saturating_duration_since(now).as_millis()
                ));
            }
            if let Some(state) = self.display.enhanced_status.as_ref() {
                if !state.prompt_suppressed && self.display.banner_height == 0 {
                    log_claude_hud_anomaly(&format!(
                        "user input observed unsuppressed HUD with zero banner height before repair scheduling (rows={}, cols={}, anchor_row={:?}, hud_style={:?})",
                        self.rows,
                        self.cols,
                        self.display.banner_anchor_row,
                        state.hud_style
                    ));
                }
            }
        }
        true
    }

    fn handle_shutdown_message(&mut self) -> bool {
        // Disable mouse before exiting to restore terminal state.
        disable_mouse(&mut self.stdout, &mut self.mouse_enabled);
        false
    }
}
