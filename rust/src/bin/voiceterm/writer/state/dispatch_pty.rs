use super::*;

impl WriterState {
    pub(super) fn handle_pty_output(&mut self, bytes: Vec<u8>) -> bool {
        let profile = self.runtime_profile;
        let codex_jetbrains = profile.codex_jetbrains;
        let claude_jetbrains = profile.claude_jetbrains;
        let jetbrains_claude_startup_clear =
            profile.startup_guard_enabled && self.jetbrains_claude_startup_screen_clear_pending;
        if jetbrains_claude_startup_clear {
            self.jetbrains_claude_startup_screen_clear_pending = false;
        }
        let cursor_startup_clear = profile.terminal_family == TerminalHost::Cursor
            && self.cursor_startup_screen_clear_pending;
        if cursor_startup_clear {
            self.cursor_startup_screen_clear_pending = false;
        }
        let startup_screen_clear = jetbrains_claude_startup_clear || cursor_startup_clear;
        let cursor_claude = profile.cursor_claude;
        let claude_hud_debug = claude_hud_debug_enabled() && (cursor_claude || claude_jetbrains);
        let claude_non_scroll_redraw_profile = profile.claude_non_scroll_redraw_profile;
        let scroll_redraw_min_interval = profile.scroll_redraw_min_interval;
        let flash_sensitive_scroll_profile = profile.flash_sensitive_scroll_profile;
        let may_scroll_rows = pty_output_may_scroll_rows(
            self.cols as usize,
            &mut self.pty_line_col_estimate,
            &bytes,
            // Treat repeated CR bytes as scroll-like updates for IDE HUD timing.
            profile.treat_cr_as_scroll,
        );
        let now = Instant::now();
        let claude_jetbrains_recent_input = claude_jetbrains
            && claude_jetbrains_has_recent_input(now, self.last_user_input_at, self.host_timing());
        let claude_jetbrains_composer_keystroke =
            claude_jetbrains_recent_input && chunk_looks_like_claude_composer_keystroke(&bytes);
        let claude_jetbrains_full_hud_active = claude_jetbrains
            && self.display.overlay_panel.is_none()
            && (self
                .display
                .enhanced_status
                .as_ref()
                .is_some_and(is_unsuppressed_full_hud)
                || self
                    .pending
                    .enhanced_status
                    .as_ref()
                    .is_some_and(is_unsuppressed_full_hud));
        let claude_jetbrains_synchronized_cursor_rewrite = claude_jetbrains
            && claude_jetbrains_full_hud_active
            && chunk_looks_like_claude_synchronized_cursor_rewrite(&bytes);
        let claude_jetbrains_non_scroll_cursor_mutation = claude_jetbrains
            && claude_jetbrains_full_hud_active
            && pty_output_can_mutate_cursor_line(&bytes)
            && ((!may_scroll_rows && claude_jetbrains_recent_input)
                || claude_jetbrains_synchronized_cursor_rewrite);
        let claude_jetbrains_destructive_clear = claude_jetbrains
            && claude_jetbrains_full_hud_active
            && pty_output_contains_destructive_clear(&bytes);
        let claude_jetbrains_recent_destructive_clear_repaint = claude_jetbrains
            && self
                .jetbrains_claude_last_destructive_clear_repaint_at
                .is_some_and(|last| {
                    now.duration_since(last)
                        < self
                            .host_timing()
                            .claude_destructive_clear_repaint_cooldown()
                            .unwrap_or_default()
                });
        let mut claude_jetbrains_chunk_touches_cursor_save_restore = false;
        if claude_jetbrains {
            let (
                dec_active_after_chunk,
                ansi_active_after_chunk,
                saw_save,
                saw_restore,
                next_escape_carry,
            ) = track_cursor_save_restore(
                self.jetbrains_dec_cursor_saved_active,
                self.jetbrains_ansi_cursor_saved_active,
                &self.jetbrains_cursor_escape_carry,
                &bytes,
            );
            claude_jetbrains_chunk_touches_cursor_save_restore = saw_save || saw_restore;
            self.jetbrains_dec_cursor_saved_active = dec_active_after_chunk;
            self.jetbrains_ansi_cursor_saved_active = ansi_active_after_chunk;
            self.jetbrains_cursor_escape_carry = next_escape_carry;
            if saw_save {
                self.jetbrains_cursor_restore_settle_until = None;
            }
            if saw_restore || (!dec_active_after_chunk && !ansi_active_after_chunk) {
                self.jetbrains_cursor_restore_settle_until = Some(
                    now + self
                        .host_timing()
                        .claude_cursor_restore_settle()
                        .unwrap_or_default(),
                );
            }
        }
        let cursor_claude_startup_preclear =
            cursor_claude && self.cursor_startup_scroll_preclear_pending;
        let cursor_claude_banner_preclear = cursor_claude && self.display.overlay_panel.is_none();
        // Use CUP-only pre-clear when chunks begin with absolute cursor moves.
        // This avoids stacked ghost rows in JetBrains+Claude.
        let claude_jetbrains_banner_preclear =
            claude_jetbrains && self.display.overlay_panel.is_none();
        let claude_jetbrains_cup_preclear_safe = claude_jetbrains_banner_preclear
            && (pty_chunk_starts_with_absolute_cursor_position(&bytes)
                || claude_jetbrains_synchronized_cursor_rewrite);
        let preclear_blocked_for_recent_input = claude_jetbrains
            && should_defer_non_urgent_redraw_for_recent_input(
                self.terminal_family(),
                now,
                self.last_user_input_at,
            );
        let claude_jetbrains_legacy_preclear_safe = claude_jetbrains_banner_preclear
            && may_scroll_rows
            && !claude_jetbrains_cup_preclear_safe
            && !claude_jetbrains_chunk_touches_cursor_save_restore
            && !self.jetbrains_dec_cursor_saved_active
            && !self.jetbrains_ansi_cursor_saved_active
            && now.duration_since(self.last_preclear_at)
                >= self
                    .host_timing()
                    .claude_banner_preclear_cooldown()
                    .unwrap_or_default();
        let in_resize_repair_window = claude_jetbrains
            && self
                .jetbrains_claude_resize_repair_until
                .is_some_and(|until| now < until);
        let (pre_clear, preclear_outcome) =
            self.run_preclear_policy_pipeline(PreclearPolicyContext {
                family: self.terminal_family(),
                display: &self.display,
                status_clear_pending: self.pending.clear_status,
                may_scroll_rows,
                codex_jetbrains,
                cursor_claude_startup_preclear,
                cursor_claude_banner_preclear,
                claude_jetbrains_banner_preclear,
                claude_jetbrains_cup_preclear_safe,
                claude_jetbrains_legacy_preclear_safe,
                in_resize_repair_window,
                preclear_blocked_for_recent_input,
                claude_jetbrains_destructive_clear,
                now,
                last_preclear_at: self.last_preclear_at,
            });
        if claude_hud_debug {
            log_debug(&format!(
                "[claude-hud-debug] writer pty chunk (bytes={}, may_scroll={}, preclear={}, startup_clear={}, force_full_before={}, force_after_preclear_before={}, pending_clear_status={}, pending_clear_overlay={}): \"{}\"",
                bytes.len(),
                may_scroll_rows,
                preclear_outcome.pre_cleared,
                startup_screen_clear,
                self.display.force_full_banner_redraw,
                self.force_redraw_after_preclear,
                self.pending.clear_status,
                self.pending.clear_overlay,
                debug_bytes_preview(&bytes, 120)
            ));
        }

        if startup_screen_clear {
            if let Err(err) = self.stdout.write_all(STARTUP_SCREEN_CLEAR) {
                log_debug(&format!("startup screen clear write failed: {err}"));
                return false;
            }
        }
        const SGR_RESET: &[u8] = b"\x1b[0m";
        // Cursor resize packets can start with erase-display bytes (`CSI J`).
        // Reset styles first so cleared rows do not keep stale decorations.
        let reset_before_chunk_for_erase_display = self.terminal_family() == TerminalHost::Cursor
            && pty_output_contains_erase_display(&bytes);
        let should_reassert_mouse_tracking =
            self.mouse_enabled && pty_chunk_disables_mouse_tracking(&bytes);
        let write_result = if pre_clear.is_empty()
            && !should_reassert_mouse_tracking
            && !reset_before_chunk_for_erase_display
        {
            self.stdout.write_all(&bytes)
        } else {
            let mut combined = Vec::with_capacity(
                pre_clear.len()
                    + bytes.len()
                    + if reset_before_chunk_for_erase_display {
                        SGR_RESET.len()
                    } else {
                        0
                    }
                    + if should_reassert_mouse_tracking {
                        mouse_enable_sequence_len()
                    } else {
                        0
                    },
            );
            combined.extend_from_slice(&pre_clear);
            if reset_before_chunk_for_erase_display {
                combined.extend_from_slice(SGR_RESET);
            }
            combined.extend_from_slice(&bytes);
            if should_reassert_mouse_tracking {
                append_mouse_enable_sequence(&mut combined);
            }
            self.stdout.write_all(&combined)
        };
        if let Err(err) = write_result {
            log_debug(&format!("stdout write_all failed: {err}"));
            return false;
        }
        if should_reassert_mouse_tracking {
            log_debug("reasserted mouse tracking after backend disable sequence");
        }
        self.apply_preclear_outcome(preclear_outcome, now);
        self.last_output_at = now;
        if self.display.has_any() {
            let claude_jetbrains_immediate_keystroke_repaint = claude_jetbrains_composer_keystroke
                && !claude_jetbrains_chunk_touches_cursor_save_restore
                && !self.jetbrains_dec_cursor_saved_active
                && !self.jetbrains_ansi_cursor_saved_active;
            if claude_jetbrains_immediate_keystroke_repaint {
                // Some JetBrains+Claude keystroke packets wipe HUD rows.
                // Repaint in the same cycle to avoid per-keystroke flicker.
                self.display.force_full_banner_redraw = true;
                self.force_redraw_after_preclear = true;
                self.needs_redraw = true;
                self.jetbrains_cursor_restore_settle_until = None;
                self.jetbrains_claude_composer_repair_due = None;
                self.jetbrains_claude_repair_skip_quiet_window = false;
            }
            if claude_jetbrains_synchronized_cursor_rewrite
                && !claude_jetbrains_immediate_keystroke_repaint
            {
                // Cursor rewrite bursts can touch HUD rows across many chunks.
                // Do one redraw after the burst instead of one redraw per chunk.
                self.display.force_full_banner_redraw = true;
                self.needs_redraw = true;
                self.jetbrains_cursor_restore_settle_until = None;
            }
            if claude_jetbrains_composer_keystroke || claude_jetbrains_non_scroll_cursor_mutation {
                // Keep one repair marker per burst.
                // Re-arming on every chunk can re-trigger redraw races.
                let hud_active = self.display.overlay_panel.is_none()
                    && (self
                        .display
                        .enhanced_status
                        .as_ref()
                        .is_some_and(|state| !state.prompt_suppressed)
                        || self
                            .pending
                            .enhanced_status
                            .as_ref()
                            .is_some_and(|state| !state.prompt_suppressed));
                if hud_active && !claude_jetbrains_immediate_keystroke_repaint {
                    self.display.force_full_banner_redraw = true;
                    self.needs_redraw = true;
                    if self.jetbrains_claude_composer_repair_due.is_none() {
                        let repair_due = now
                            + self
                                .host_timing()
                                .claude_composer_repair_delay()
                                .unwrap_or_default();
                        self.jetbrains_claude_composer_repair_due = Some(repair_due);
                        // Keep quiet-window gating on by default.
                        // Skipping it during long cursor bursts can re-trigger
                        // redraw races and leave stale HUD rows.
                        self.jetbrains_claude_repair_skip_quiet_window = false;
                        if claude_hud_debug_enabled() {
                            log_debug(&format!(
                                "[claude-hud-debug] scheduled jetbrains+claude composer repair redraw (due_in_ms={})",
                                repair_due.saturating_duration_since(now).as_millis()
                            ));
                        }
                    }
                }
            }
            let redraw_policy = self.run_redraw_policy_pipeline(RedrawPolicyContext {
                family: self.terminal_family(),
                bytes: &bytes,
                now,
                last_scroll_redraw_at: self.last_scroll_redraw_at,
                scroll_redraw_min_interval,
                may_scroll_rows,
                display_force_full_banner_redraw: self.display.force_full_banner_redraw,
                display_has_enhanced_status: self.display.enhanced_status.is_some(),
                display_has_unsuppressed_enhanced_status: self
                    .display
                    .enhanced_status
                    .as_ref()
                    .is_some_and(|status| !status.prompt_suppressed),
                display_should_force_full_banner_redraw_on_output: self
                    .display
                    .should_force_full_banner_redraw_on_output(self.terminal_family()),
                pending_clear_status: self.pending.clear_status,
                pending_clear_overlay: self.pending.clear_overlay,
                pending_overlay_panel_present: self.pending.overlay_panel.is_some(),
                preclear_outcome,
                codex_jetbrains,
                claude_jetbrains,
                cursor_claude,
                flash_sensitive_scroll_profile,
                claude_non_scroll_redraw_profile,
                claude_jetbrains_non_scroll_cursor_mutation,
                claude_jetbrains_composer_keystroke,
                claude_jetbrains_destructive_clear,
                claude_jetbrains_chunk_touches_cursor_save_restore,
                jetbrains_dec_cursor_saved_active: self.jetbrains_dec_cursor_saved_active,
                jetbrains_ansi_cursor_saved_active: self.jetbrains_ansi_cursor_saved_active,
                claude_jetbrains_recent_destructive_clear_repaint,
            });
            self.apply_redraw_policy_outcome(redraw_policy, now, claude_hud_debug);
        }
        // If we force redraw-after-preclear, skip this flush.
        // That keeps PTY bytes and HUD redraw in one batch and prevents flicker.
        if !self.force_redraw_after_preclear
            && (now.duration_since(self.last_output_flush_at)
                >= Duration::from_millis(OUTPUT_FLUSH_INTERVAL_MS)
                || bytes.contains(&b'\n')
                || should_reassert_mouse_tracking)
        {
            if let Err(err) = self.stdout.flush() {
                log_debug(&format!("stdout flush failed: {err}"));
            } else {
                self.last_output_flush_at = now;
            }
        }
        // Keep overlays/HUD responsive during long PTY output bursts.
        // Without this, timeout-based redraws can starve.
        self.maybe_redraw_status();
        if claude_hud_debug {
            log_debug(&format!(
                "[claude-hud-debug] writer pty post (needs_redraw={}, force_full_after={}, force_after_preclear_after={}, banner_height={}, preclear_banner_height={})",
                self.needs_redraw,
                self.display.force_full_banner_redraw,
                self.force_redraw_after_preclear,
                self.display.banner_height,
                self.display.preclear_banner_height
            ));
        }
        true
    }
}
