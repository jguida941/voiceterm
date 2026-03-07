use super::*;
use crate::runtime_compat::RuntimeVariant;

#[derive(Clone, Copy)]
struct PtyChunkAnalysis {
    runtime_variant: RuntimeVariant,
    terminal_family: TerminalHost,
    now: Instant,
    startup_screen_clear: bool,
    may_scroll_rows: bool,
    codex_jetbrains: bool,
    claude_hud_debug: bool,
    claude_non_scroll_redraw_profile: bool,
    scroll_redraw_min_interval: Option<Duration>,
    flash_sensitive_scroll_profile: bool,
    claude_jetbrains_composer_keystroke: bool,
    claude_jetbrains_synchronized_cursor_rewrite: bool,
    claude_jetbrains_non_scroll_cursor_mutation: bool,
    claude_jetbrains_destructive_clear: bool,
    claude_jetbrains_recent_destructive_clear_repaint: bool,
    claude_jetbrains_chunk_touches_cursor_save_restore: bool,
    cursor_claude_startup_preclear: bool,
    cursor_claude_banner_preclear: bool,
    claude_jetbrains_banner_preclear: bool,
    claude_jetbrains_cup_preclear_safe: bool,
    claude_jetbrains_legacy_preclear_safe: bool,
    preclear_blocked_for_recent_input: bool,
    in_resize_repair_window: bool,
}

struct PtyPreclearStage {
    pre_clear: Vec<u8>,
    preclear_outcome: PreclearOutcome,
}

#[derive(Clone, Copy)]
struct PtyWriteStage {
    should_reassert_mouse_tracking: bool,
    chunk_contains_newline: bool,
}

enum PtyWriteError {
    StartupScreenClear(io::Error),
    ChunkWrite(io::Error),
}

impl WriterState {
    pub(super) fn handle_pty_output(&mut self, bytes: Vec<u8>) -> bool {
        let analysis = self.analyze_pty_chunk(&bytes);
        let preclear_stage = self.resolve_pty_preclear_stage(&analysis);
        self.log_pty_chunk_pre_write(&bytes, &analysis, preclear_stage.preclear_outcome);

        let write_stage = match self.write_pty_output_stage(&bytes, &analysis, &preclear_stage) {
            Ok(stage) => stage,
            Err(PtyWriteError::StartupScreenClear(err)) => {
                log_debug(&format!("startup screen clear write failed: {err}"));
                return false;
            }
            Err(PtyWriteError::ChunkWrite(err)) => {
                log_debug(&format!("stdout write_all failed: {err}"));
                return false;
            }
        };

        self.commit_pty_preclear_stage(&analysis, preclear_stage.preclear_outcome);
        let redraw_policy = self.resolve_pty_redraw_policy_stage(
            &bytes,
            &analysis,
            preclear_stage.preclear_outcome,
        );
        self.apply_pty_state_updates(&analysis, write_stage, redraw_policy);
        true
    }

    fn analyze_pty_chunk(&mut self, bytes: &[u8]) -> PtyChunkAnalysis {
        let profile = self.runtime_profile;
        let runtime_variant = profile.runtime_variant;
        let codex_jetbrains = runtime_variant.is_jetbrains_codex();
        let claude_jetbrains = runtime_variant.is_jetbrains_claude();
        let cursor_claude = runtime_variant.is_cursor_claude();
        let terminal_family = profile.terminal_family;
        let startup_screen_clear = (profile.startup_guard_enabled
            && self
                .adapter_state
                .take_jetbrains_claude_startup_screen_clear_pending())
            || (terminal_family == TerminalHost::Cursor
                && self
                    .adapter_state
                    .take_cursor_startup_screen_clear_pending());
        let claude_hud_debug = claude_hud_debug_enabled() && (cursor_claude || claude_jetbrains);
        let may_scroll_rows = pty_output_may_scroll_rows(
            self.cols as usize,
            &mut self.pty_line_col_estimate,
            bytes,
            // Treat repeated CR bytes as scroll-like updates for IDE HUD timing.
            profile.treat_cr_as_scroll,
        );
        let now = Instant::now();

        let claude_jetbrains_recent_input = claude_jetbrains
            && claude_jetbrains_has_recent_input(now, self.last_user_input_at, self.host_timing());
        let claude_jetbrains_composer_keystroke =
            claude_jetbrains_recent_input && chunk_looks_like_claude_composer_keystroke(bytes);
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
            && chunk_looks_like_claude_synchronized_cursor_rewrite(bytes);
        let claude_jetbrains_non_scroll_cursor_mutation = claude_jetbrains
            && claude_jetbrains_full_hud_active
            && pty_output_can_mutate_cursor_line(bytes)
            && ((!may_scroll_rows && claude_jetbrains_recent_input)
                || claude_jetbrains_synchronized_cursor_rewrite);
        let claude_jetbrains_destructive_clear = claude_jetbrains
            && claude_jetbrains_full_hud_active
            && pty_output_contains_destructive_clear(bytes);
        let claude_jetbrains_recent_destructive_clear_repaint = claude_jetbrains
            && self
                .adapter_state
                .jetbrains_claude_last_destructive_clear_repaint_at()
                .is_some_and(|last| {
                    now.duration_since(last)
                        < self
                            .host_timing()
                            .claude_destructive_clear_repaint_cooldown()
                            .unwrap_or_default()
                });
        let claude_jetbrains_chunk_touches_cursor_save_restore =
            self.track_jetbrains_cursor_save_restore(bytes, now, claude_jetbrains);

        let cursor_claude_startup_preclear =
            cursor_claude && self.adapter_state.cursor_startup_scroll_preclear_pending();
        let cursor_claude_banner_preclear = cursor_claude && self.display.overlay_panel.is_none();
        // Use CUP-only pre-clear when chunks begin with absolute cursor moves.
        // This avoids stacked ghost rows in JetBrains+Claude.
        let claude_jetbrains_banner_preclear =
            claude_jetbrains && self.display.overlay_panel.is_none();
        let claude_jetbrains_cup_preclear_safe = claude_jetbrains_banner_preclear
            && (pty_chunk_starts_with_absolute_cursor_position(bytes)
                || claude_jetbrains_synchronized_cursor_rewrite);
        let preclear_blocked_for_recent_input = claude_jetbrains
            && should_defer_non_urgent_redraw_for_recent_input(
                terminal_family,
                now,
                self.last_user_input_at,
            );
        let claude_jetbrains_legacy_preclear_safe = claude_jetbrains_banner_preclear
            && may_scroll_rows
            && !claude_jetbrains_cup_preclear_safe
            && !claude_jetbrains_chunk_touches_cursor_save_restore
            && !self.adapter_state.jetbrains_dec_cursor_saved_active()
            && !self.adapter_state.jetbrains_ansi_cursor_saved_active()
            && now.duration_since(self.last_preclear_at)
                >= self
                    .host_timing()
                    .claude_banner_preclear_cooldown()
                    .unwrap_or_default();
        let in_resize_repair_window = claude_jetbrains
            && self
                .adapter_state
                .jetbrains_claude_resize_repair_until()
                .is_some_and(|until| now < until);

        PtyChunkAnalysis {
            runtime_variant,
            terminal_family,
            now,
            startup_screen_clear,
            may_scroll_rows,
            codex_jetbrains,
            claude_hud_debug,
            claude_non_scroll_redraw_profile: profile.claude_non_scroll_redraw_profile,
            scroll_redraw_min_interval: profile.scroll_redraw_min_interval,
            flash_sensitive_scroll_profile: profile.flash_sensitive_scroll_profile,
            claude_jetbrains_composer_keystroke,
            claude_jetbrains_synchronized_cursor_rewrite,
            claude_jetbrains_non_scroll_cursor_mutation,
            claude_jetbrains_destructive_clear,
            claude_jetbrains_recent_destructive_clear_repaint,
            claude_jetbrains_chunk_touches_cursor_save_restore,
            cursor_claude_startup_preclear,
            cursor_claude_banner_preclear,
            claude_jetbrains_banner_preclear,
            claude_jetbrains_cup_preclear_safe,
            claude_jetbrains_legacy_preclear_safe,
            preclear_blocked_for_recent_input,
            in_resize_repair_window,
        }
    }

    fn track_jetbrains_cursor_save_restore(
        &mut self,
        bytes: &[u8],
        now: Instant,
        claude_jetbrains: bool,
    ) -> bool {
        if !claude_jetbrains {
            return false;
        }
        let (
            dec_active_after_chunk,
            ansi_active_after_chunk,
            saw_save,
            saw_restore,
            next_escape_carry,
        ) = track_cursor_save_restore(
            self.adapter_state.jetbrains_dec_cursor_saved_active(),
            self.adapter_state.jetbrains_ansi_cursor_saved_active(),
            self.adapter_state.jetbrains_cursor_escape_carry(),
            bytes,
        );
        self.adapter_state
            .set_jetbrains_dec_cursor_saved_active(dec_active_after_chunk);
        self.adapter_state
            .set_jetbrains_ansi_cursor_saved_active(ansi_active_after_chunk);
        self.adapter_state
            .set_jetbrains_cursor_escape_carry(next_escape_carry);
        if saw_save {
            self.adapter_state
                .set_jetbrains_cursor_restore_settle_until(None);
        }
        if saw_restore || (!dec_active_after_chunk && !ansi_active_after_chunk) {
            self.adapter_state
                .set_jetbrains_cursor_restore_settle_until(Some(
                    now + self
                        .host_timing()
                        .claude_cursor_restore_settle()
                        .unwrap_or_default(),
                ));
        }
        saw_save || saw_restore
    }

    fn resolve_pty_preclear_stage(&self, analysis: &PtyChunkAnalysis) -> PtyPreclearStage {
        let (pre_clear, preclear_outcome) =
            self.run_preclear_policy_pipeline(PreclearPolicyContext {
                family: analysis.terminal_family,
                display: &self.display,
                status_clear_pending: self.pending.clear_status,
                may_scroll_rows: analysis.may_scroll_rows,
                codex_jetbrains: analysis.codex_jetbrains,
                cursor_claude_startup_preclear: analysis.cursor_claude_startup_preclear,
                cursor_claude_banner_preclear: analysis.cursor_claude_banner_preclear,
                claude_jetbrains_banner_preclear: analysis.claude_jetbrains_banner_preclear,
                claude_jetbrains_cup_preclear_safe: analysis.claude_jetbrains_cup_preclear_safe,
                claude_jetbrains_legacy_preclear_safe: analysis
                    .claude_jetbrains_legacy_preclear_safe,
                in_resize_repair_window: analysis.in_resize_repair_window,
                preclear_blocked_for_recent_input: analysis.preclear_blocked_for_recent_input,
                claude_jetbrains_destructive_clear: analysis.claude_jetbrains_destructive_clear,
                now: analysis.now,
                last_preclear_at: self.last_preclear_at,
            });
        PtyPreclearStage {
            pre_clear,
            preclear_outcome,
        }
    }

    fn log_pty_chunk_pre_write(
        &self,
        bytes: &[u8],
        analysis: &PtyChunkAnalysis,
        preclear_outcome: PreclearOutcome,
    ) {
        if analysis.claude_hud_debug {
            log_debug(&format!(
                "[claude-hud-debug] writer pty chunk (bytes={}, may_scroll={}, preclear={}, startup_clear={}, force_full_before={}, force_after_preclear_before={}, pending_clear_status={}, pending_clear_overlay={}): \"{}\"",
                bytes.len(),
                analysis.may_scroll_rows,
                preclear_outcome.pre_cleared,
                analysis.startup_screen_clear,
                self.display.force_full_banner_redraw,
                self.force_redraw_after_preclear,
                self.pending.clear_status,
                self.pending.clear_overlay,
                debug_bytes_preview(bytes, 120)
            ));
        }
    }

    fn write_pty_output_stage(
        &mut self,
        bytes: &[u8],
        analysis: &PtyChunkAnalysis,
        preclear_stage: &PtyPreclearStage,
    ) -> Result<PtyWriteStage, PtyWriteError> {
        if analysis.startup_screen_clear {
            if let Err(err) = self.stdout.write_all(STARTUP_SCREEN_CLEAR) {
                return Err(PtyWriteError::StartupScreenClear(err));
            }
        }
        const SGR_RESET: &[u8] = b"\x1b[0m";
        // Cursor resize packets can start with erase-display bytes (`CSI J`).
        // Reset styles first so cleared rows do not keep stale decorations.
        let reset_before_chunk_for_erase_display = analysis.terminal_family == TerminalHost::Cursor
            && pty_output_contains_erase_display(bytes);
        let should_reassert_mouse_tracking =
            self.mouse_enabled && pty_chunk_disables_mouse_tracking(bytes);
        let write_result = if preclear_stage.pre_clear.is_empty()
            && !should_reassert_mouse_tracking
            && !reset_before_chunk_for_erase_display
        {
            self.stdout.write_all(bytes)
        } else {
            let mut combined = Vec::with_capacity(
                preclear_stage.pre_clear.len()
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
            combined.extend_from_slice(&preclear_stage.pre_clear);
            if reset_before_chunk_for_erase_display {
                combined.extend_from_slice(SGR_RESET);
            }
            combined.extend_from_slice(bytes);
            if should_reassert_mouse_tracking {
                append_mouse_enable_sequence(&mut combined);
            }
            self.stdout.write_all(&combined)
        };
        if let Err(err) = write_result {
            return Err(PtyWriteError::ChunkWrite(err));
        }
        if should_reassert_mouse_tracking {
            log_debug("reasserted mouse tracking after backend disable sequence");
        }
        Ok(PtyWriteStage {
            should_reassert_mouse_tracking,
            chunk_contains_newline: bytes.contains(&b'\n'),
        })
    }

    fn commit_pty_preclear_stage(
        &mut self,
        analysis: &PtyChunkAnalysis,
        preclear_outcome: PreclearOutcome,
    ) {
        self.apply_preclear_outcome(preclear_outcome, analysis.now);
        self.last_output_at = analysis.now;
    }

    fn resolve_pty_redraw_policy_stage(
        &mut self,
        bytes: &[u8],
        analysis: &PtyChunkAnalysis,
        preclear_outcome: PreclearOutcome,
    ) -> Option<RedrawPolicy> {
        if !self.display.has_any() {
            return None;
        }
        self.arm_jetbrains_chunk_repair_markers(analysis);
        Some(
            self.run_redraw_policy_pipeline(RedrawPolicyContext {
                family: analysis.terminal_family,
                runtime_variant: analysis.runtime_variant,
                bytes,
                now: analysis.now,
                last_scroll_redraw_at: self.last_scroll_redraw_at,
                scroll_redraw_min_interval: analysis.scroll_redraw_min_interval,
                may_scroll_rows: analysis.may_scroll_rows,
                display_force_full_banner_redraw: self.display.force_full_banner_redraw,
                display_has_enhanced_status: self.display.enhanced_status.is_some(),
                display_has_unsuppressed_enhanced_status: self
                    .display
                    .enhanced_status
                    .as_ref()
                    .is_some_and(|status| !status.prompt_suppressed),
                display_should_force_full_banner_redraw_on_output: self
                    .display
                    .should_force_full_banner_redraw_on_output(analysis.terminal_family),
                pending_clear_status: self.pending.clear_status,
                pending_clear_overlay: self.pending.clear_overlay,
                pending_overlay_panel_present: self.pending.overlay_panel.is_some(),
                preclear_outcome,
                flash_sensitive_scroll_profile: analysis.flash_sensitive_scroll_profile,
                claude_non_scroll_redraw_profile: analysis.claude_non_scroll_redraw_profile,
                claude_jetbrains_non_scroll_cursor_mutation: analysis
                    .claude_jetbrains_non_scroll_cursor_mutation,
                claude_jetbrains_composer_keystroke: analysis.claude_jetbrains_composer_keystroke,
                claude_jetbrains_destructive_clear: analysis.claude_jetbrains_destructive_clear,
                claude_jetbrains_chunk_touches_cursor_save_restore: analysis
                    .claude_jetbrains_chunk_touches_cursor_save_restore,
                jetbrains_dec_cursor_saved_active: self
                    .adapter_state
                    .jetbrains_dec_cursor_saved_active(),
                jetbrains_ansi_cursor_saved_active: self
                    .adapter_state
                    .jetbrains_ansi_cursor_saved_active(),
                claude_jetbrains_recent_destructive_clear_repaint: analysis
                    .claude_jetbrains_recent_destructive_clear_repaint,
            }),
        )
    }

    fn arm_jetbrains_chunk_repair_markers(&mut self, analysis: &PtyChunkAnalysis) {
        let immediate_keystroke_repaint = analysis.claude_jetbrains_composer_keystroke
            && !analysis.claude_jetbrains_chunk_touches_cursor_save_restore
            && !self.adapter_state.jetbrains_dec_cursor_saved_active()
            && !self.adapter_state.jetbrains_ansi_cursor_saved_active();
        if immediate_keystroke_repaint {
            // Some JetBrains+Claude keystroke packets wipe HUD rows.
            // Repaint in the same cycle to avoid per-keystroke flicker.
            self.display.force_full_banner_redraw = true;
            self.force_redraw_after_preclear = true;
            self.needs_redraw = true;
            self.adapter_state
                .set_jetbrains_cursor_restore_settle_until(None);
            self.adapter_state
                .set_jetbrains_claude_composer_repair_due(None);
            self.adapter_state
                .set_jetbrains_claude_repair_skip_quiet_window(false);
        }
        if analysis.claude_jetbrains_synchronized_cursor_rewrite && !immediate_keystroke_repaint {
            // Cursor rewrite bursts can touch HUD rows across many chunks.
            // Do one redraw after the burst instead of one redraw per chunk.
            self.display.force_full_banner_redraw = true;
            self.needs_redraw = true;
            self.adapter_state
                .set_jetbrains_cursor_restore_settle_until(None);
        }
        if analysis.claude_jetbrains_composer_keystroke
            || analysis.claude_jetbrains_non_scroll_cursor_mutation
        {
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
            if hud_active && !immediate_keystroke_repaint {
                self.display.force_full_banner_redraw = true;
                self.needs_redraw = true;
                if self
                    .adapter_state
                    .jetbrains_claude_composer_repair_due()
                    .is_none()
                {
                    let repair_due = analysis.now
                        + self
                            .host_timing()
                            .claude_composer_repair_delay()
                            .unwrap_or_default();
                    self.adapter_state
                        .set_jetbrains_claude_composer_repair_due(Some(repair_due));
                    // Keep quiet-window gating on by default.
                    // Skipping it during long cursor bursts can re-trigger
                    // redraw races and leave stale HUD rows.
                    self.adapter_state
                        .set_jetbrains_claude_repair_skip_quiet_window(false);
                    if analysis.claude_hud_debug {
                        log_debug(&format!(
                            "[claude-hud-debug] scheduled jetbrains+claude composer repair redraw (due_in_ms={})",
                            repair_due.saturating_duration_since(analysis.now).as_millis()
                        ));
                    }
                }
            }
        }
    }

    fn apply_pty_state_updates(
        &mut self,
        analysis: &PtyChunkAnalysis,
        write_stage: PtyWriteStage,
        redraw_policy: Option<RedrawPolicy>,
    ) {
        if let Some(policy) = redraw_policy {
            self.apply_redraw_policy_outcome(policy, analysis.now, analysis.claude_hud_debug);
        }
        // If we force redraw-after-preclear, skip this flush.
        // That keeps PTY bytes and HUD redraw in one batch and prevents flicker.
        if !self.force_redraw_after_preclear
            && (analysis.now.duration_since(self.last_output_flush_at)
                >= Duration::from_millis(OUTPUT_FLUSH_INTERVAL_MS)
                || write_stage.chunk_contains_newline
                || write_stage.should_reassert_mouse_tracking)
        {
            if let Err(err) = self.stdout.flush() {
                log_debug(&format!("stdout flush failed: {err}"));
            } else {
                self.last_output_flush_at = analysis.now;
            }
        }
        // Keep overlays/HUD responsive during long PTY output bursts.
        // Without this, timeout-based redraws can starve.
        self.maybe_redraw_status();
        if analysis.claude_hud_debug {
            log_debug(&format!(
                "[claude-hud-debug] writer pty post (needs_redraw={}, force_full_after={}, force_after_preclear_after={}, banner_height={}, preclear_banner_height={})",
                self.needs_redraw,
                self.display.force_full_banner_redraw,
                self.force_redraw_after_preclear,
                self.display.banner_height,
                self.display.preclear_banner_height
            ));
        }
    }
}
