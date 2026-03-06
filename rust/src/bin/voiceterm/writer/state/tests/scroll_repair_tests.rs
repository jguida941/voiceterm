use super::*;

const CLAUDE_COMPOSER_CHUNK: &[u8] = b"\x1b[?2026h\r\x1b[2A\x1b[7m \x1b[27m\r\n\x1b[?2026l";

fn jetbrains_state(rows: u16, cols: u16) -> WriterState {
    let mut state = WriterState::new();
    state.set_terminal_family_for_tests(TerminalHost::JetBrains);
    state.rows = rows;
    state.cols = cols;
    state
}

fn jetbrains_redraw_state() -> WriterState {
    let mut state = jetbrains_state(24, 120);
    state.display.enhanced_status = Some(StatusLineState::new());
    state.needs_redraw = true;
    state.last_output_at =
        Instant::now() - Duration::from_millis(CLAUDE_JETBRAINS_IDLE_REDRAW_HOLD_MS + 40);
    state.last_status_draw_at = Instant::now() - Duration::from_millis(2_000);
    state
}

fn jetbrains_destructive_clear_state(cursor_slot_busy: bool) -> WriterState {
    let mut state = jetbrains_state(26, 120);
    state.jetbrains_dec_cursor_saved_active = cursor_slot_busy;
    state.last_status_draw_at = Instant::now() - Duration::from_millis(2_000);
    state.last_output_at = Instant::now() - Duration::from_millis(2_000);

    let mut hud = StatusLineState::new();
    hud.hud_style = HudStyle::Full;
    hud.prompt_suppressed = false;
    state.display.enhanced_status = Some(hud);
    state.display.banner_height = 4;
    state.display.preclear_banner_height = 4;
    state
}

#[test]
fn pty_output_may_scroll_rows_skips_csi_escape_sequences() {
    let mut col = 0usize;
    // CSI sequence parameters should NOT count as printable characters.
    // "\x1b[31m" is SGR (3 param bytes + final 'm') — column should stay 0.
    assert!(!pty_output_may_scroll_rows(
        80,
        &mut col,
        b"\x1b[31m",
        false
    ));
    assert_eq!(col, 0, "CSI params must not inflate column estimate");
}

#[test]
fn pty_output_may_scroll_rows_handles_mixed_csi_and_printable() {
    let mut col = 0usize;
    // "\x1b[32mHi" — SGR skipped, then 'H' and 'i' count as 2 printable chars.
    assert!(!pty_output_may_scroll_rows(
        80,
        &mut col,
        b"\x1b[32mHi",
        false
    ));
    assert_eq!(col, 2, "only printable bytes after CSI should count");
}

#[test]
fn pty_output_may_scroll_rows_skips_two_byte_escape_sequences() {
    let mut col = 0usize;
    // ESC 7 (save cursor) + ESC 8 (restore cursor) — both should be skipped.
    assert!(!pty_output_may_scroll_rows(
        80,
        &mut col,
        b"\x1b7\x1b8ab",
        false
    ));
    assert_eq!(
        col, 2,
        "two-byte escapes should be skipped, only 'ab' counted"
    );
}

#[test]
fn pty_output_may_scroll_rows_sgr_does_not_cause_false_scroll() {
    let mut col = 0usize;
    // 8-column terminal: "Hi" (2 cols) + SGR "\x1b[0;38;5;196m" + "!" (1 col) = 3 cols total.
    // Before the fix, SGR parameter bytes inflated the estimate past 8, causing false scroll.
    let payload = b"Hi\x1b[0;38;5;196m!";
    assert!(!pty_output_may_scroll_rows(8, &mut col, payload, false));
    assert_eq!(col, 3, "SGR color codes must not cause false wrap-scroll");
}

#[test]
fn track_cursor_save_restore_tracks_dec_and_ansi_sequences() {
    let (dec_active, ansi_active, saw_save, saw_restore, carry) =
        track_cursor_save_restore(false, false, b"", b"\x1b7\x1b[s");
    assert!(dec_active);
    assert!(ansi_active);
    assert!(saw_save);
    assert!(!saw_restore);
    assert!(carry.is_empty());

    let (dec_active, ansi_active, saw_save, saw_restore, carry) =
        track_cursor_save_restore(dec_active, ansi_active, &carry, b"\x1b8\x1b[u");
    assert!(!dec_active);
    assert!(!ansi_active);
    assert!(!saw_save);
    assert!(saw_restore);
    assert!(carry.is_empty());
}

#[test]
fn track_cursor_save_restore_handles_split_escape_sequences() {
    let (dec_active, ansi_active, saw_save, saw_restore, carry) =
        track_cursor_save_restore(false, false, b"", b"\x1b");
    assert!(!dec_active);
    assert!(!ansi_active);
    assert!(!saw_save);
    assert!(!saw_restore);
    assert_eq!(carry, b"\x1b");

    let (dec_active, ansi_active, saw_save, saw_restore, carry) =
        track_cursor_save_restore(dec_active, ansi_active, &carry, b"7prompt");
    assert!(dec_active);
    assert!(!ansi_active);
    assert!(saw_save);
    assert!(!saw_restore);
    assert!(carry.is_empty());

    let (dec_active, ansi_active, saw_save, saw_restore, carry) =
        track_cursor_save_restore(dec_active, ansi_active, &carry, b"\x1b[0");
    assert!(dec_active);
    assert!(!ansi_active);
    assert!(!saw_save);
    assert!(!saw_restore);
    assert_eq!(carry, b"\x1b[0");

    let (dec_active, ansi_active, saw_save, saw_restore, carry) =
        track_cursor_save_restore(dec_active, ansi_active, &carry, b"u");
    assert!(dec_active);
    assert!(!ansi_active);
    assert!(!saw_save);
    assert!(saw_restore);
    assert!(carry.is_empty());
}

#[test]
fn track_cursor_save_restore_ignores_csi_parameter_bytes() {
    let (dec_active, ansi_active, saw_save, saw_restore, carry) =
        track_cursor_save_restore(false, false, b"", b"\x1b[38;5;196mcolor\x1b[0m");
    assert!(!dec_active);
    assert!(!ansi_active);
    assert!(!saw_save);
    assert!(!saw_restore);
    assert!(carry.is_empty());
}

#[test]
fn maybe_redraw_status_defers_jetbrains_claude_when_cursor_save_is_active() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_redraw_state();
        state.jetbrains_dec_cursor_saved_active = true;
        state.jetbrains_ansi_cursor_saved_active = false;

        state.maybe_redraw_status();
        assert!(
            state.needs_redraw,
            "JetBrains+Claude redraw should wait while cursor-save state is active"
        );
    });
}

#[test]
fn maybe_redraw_status_defers_jetbrains_claude_during_restore_settle_window() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_redraw_state();
        state.jetbrains_dec_cursor_saved_active = false;
        state.jetbrains_ansi_cursor_saved_active = false;
        state.jetbrains_cursor_restore_settle_until =
            Some(Instant::now() + Duration::from_millis(80));

        state.maybe_redraw_status();
        assert!(
            state.needs_redraw,
            "JetBrains+Claude redraw should wait briefly after cursor restore"
        );
    });
}

#[test]
fn jetbrains_claude_composer_repair_waits_for_due_deadline() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_redraw_state();
        state.last_output_at = Instant::now();
        state.jetbrains_claude_composer_repair_due =
            Some(Instant::now() + Duration::from_millis(80));

        state.maybe_redraw_status();
        assert!(
            state.needs_redraw,
            "composer repair should wait until debounce deadline"
        );
    });
}

#[test]
fn jetbrains_claude_composer_keystroke_repaints_immediately_without_deferred_repair() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_state(24, 120);
        state.display.enhanced_status = Some(StatusLineState::new());
        assert!(state.handle_message(WriterMessage::UserInputActivity));

        let composer_chunk = CLAUDE_COMPOSER_CHUNK.to_vec();
        assert!(state.handle_message(WriterMessage::PtyOutput(composer_chunk)));
        assert!(
            state.jetbrains_claude_composer_repair_due.is_none(),
            "composer keystroke packets should repaint immediately without delayed repair arming"
        );
        assert!(
            !state.needs_redraw,
            "immediate composer repaint should complete in the same writer cycle"
        );
    });
}

#[test]
fn jetbrains_claude_composer_keystroke_falls_back_to_deferred_repair_when_cursor_slot_active() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_state(24, 120);
        state.display.enhanced_status = Some(StatusLineState::new());
        state.jetbrains_dec_cursor_saved_active = true;
        assert!(state.handle_message(WriterMessage::UserInputActivity));

        let composer_chunk = CLAUDE_COMPOSER_CHUNK.to_vec();
        assert!(state.handle_message(WriterMessage::PtyOutput(composer_chunk)));
        assert!(
            state.jetbrains_claude_composer_repair_due.is_some(),
            "when cursor save/restore is active, composer packets should use deferred repair path"
        );
    });
}

#[test]
fn jetbrains_claude_composer_keystroke_ignored_without_recent_user_input() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_state(24, 120);
        state.display.enhanced_status = Some(StatusLineState::new());
        state.last_user_input_at =
            Instant::now() - Duration::from_millis(CLAUDE_JETBRAINS_COMPOSER_RECENT_INPUT_MS + 100);

        let composer_chunk = CLAUDE_COMPOSER_CHUNK.to_vec();
        assert!(state.handle_message(WriterMessage::PtyOutput(composer_chunk)));
        assert!(
            state.jetbrains_claude_composer_repair_due.is_none(),
            "without recent input, composer-like packets should not arm repair redraws"
        );
    });
}

#[test]
fn jetbrains_claude_full_hud_non_scroll_cursor_mutation_arms_repair() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_state(42, 196);
        assert!(state.handle_message(WriterMessage::UserInputActivity));

        let mut hud = StatusLineState::new();
        hud.hud_style = HudStyle::Full;
        hud.prompt_suppressed = false;
        state.display.enhanced_status = Some(hud);

        let mutation_chunk = b"\x1b[?2026h\r\x1b[6A\x1b[7m \x1b[27m\x1b[?2026l".to_vec();
        assert!(
            !chunk_looks_like_claude_composer_keystroke(&mutation_chunk),
            "6A packets should not require the short-composer classifier to schedule repair"
        );
        assert!(state.handle_message(WriterMessage::PtyOutput(mutation_chunk)));
        assert!(
            state.display.force_full_banner_redraw,
            "full HUD should mark a full repaint after non-scroll cursor mutation"
        );
        assert!(
            state.needs_redraw,
            "full HUD should queue deferred redraw after non-scroll cursor mutation"
        );
        assert!(
            !state.force_redraw_after_preclear,
            "full HUD repair should stay deferred for synchronized rewrite bursts on JetBrains+Claude"
        );
        assert!(
            state.jetbrains_claude_composer_repair_due.is_some(),
            "full HUD non-scroll cursor mutation should arm a repair deadline"
        );
    });
}

#[test]
fn jetbrains_claude_thinking_packet_without_recent_input_still_arms_repair() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_state(42, 196);
        state.last_user_input_at =
            Instant::now() - Duration::from_millis(CLAUDE_JETBRAINS_COMPOSER_RECENT_INPUT_MS + 250);

        let mut hud = StatusLineState::new();
        hud.hud_style = HudStyle::Full;
        hud.prompt_suppressed = false;
        state.display.enhanced_status = Some(hud);

        let thinking_chunk = b"\x1b[?2026h\r\x1b[21C\x1b[6A\x1b[37m50\x1b[10C\x1b[38;2;174;174;174m(thinking)\x1b[39m\r\r\n\r\n\r\n\r\n\r\n\r\n\x1b[?2026l".to_vec();
        assert!(state.handle_message(WriterMessage::PtyOutput(thinking_chunk)));
        assert!(
            state.jetbrains_claude_composer_repair_due.is_some(),
            "thinking rewrite packets should arm repair even without recent input"
        );
        assert!(
            !state.jetbrains_claude_repair_skip_quiet_window,
            "thinking rewrite packets should keep quiet-window gating to avoid repeated redraw races"
        );
    });
}

#[test]
fn jetbrains_claude_destructive_clear_reanchors_hud_immediately_when_cursor_slot_idle() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_destructive_clear_state(false);

        assert!(state.handle_message(WriterMessage::PtyOutput(b"\x1b[2J\x1b[3J\x1b[H".to_vec())));
        assert!(
            !state.needs_redraw,
            "destructive clears should repaint JetBrains+Claude HUD immediately when cursor slot is idle"
        );
        assert!(
            state.jetbrains_claude_composer_repair_due.is_some(),
            "destructive clear should still arm a near-term follow-up repair"
        );
        assert!(
            state.jetbrains_claude_repair_skip_quiet_window,
            "destructive-clear follow-up repair should bypass quiet window"
        );
    });
}

#[test]
fn jetbrains_claude_destructive_clear_defers_immediate_repaint_when_cursor_slot_busy() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_destructive_clear_state(true);

        assert!(state.handle_message(WriterMessage::PtyOutput(b"\x1b[2J\x1b[3J\x1b[H".to_vec())));
        assert!(
            state.needs_redraw,
            "when cursor slot is busy, destructive-clear repaint should stay deferred"
        );
        assert!(
            !state.force_redraw_after_preclear,
            "busy cursor slot should block immediate preclear redraw path"
        );
        assert!(
            state.jetbrains_claude_composer_repair_due.is_some(),
            "deferred path should still arm follow-up repair"
        );
        assert!(
            state.jetbrains_claude_repair_skip_quiet_window,
            "deferred destructive-clear repair should bypass quiet window"
        );
    });
}

#[test]
fn jetbrains_claude_repeated_destructive_clear_burst_uses_deferred_followup() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_destructive_clear_state(false);

        assert!(state.handle_message(WriterMessage::PtyOutput(b"\x1b[2J\x1b[3J\x1b[H".to_vec())));
        assert!(
            !state.needs_redraw,
            "first destructive clear should re-anchor immediately"
        );

        assert!(state.handle_message(WriterMessage::PtyOutput(b"\x1b[2J\x1b[3J\x1b[H".to_vec())));
        assert!(
            state.needs_redraw,
            "subsequent destructive clears in the same burst should defer to scheduled repair"
        );
        assert!(
            !state.force_redraw_after_preclear,
            "burst follow-up should not repeatedly force immediate preclear redraw"
        );
        assert!(
            state.jetbrains_claude_composer_repair_due.is_some(),
            "burst follow-up should keep a deferred repair marker armed"
        );
        assert!(
            state.jetbrains_claude_repair_skip_quiet_window,
            "deferred repair from destructive-clear burst should bypass quiet window"
        );
    });
}

#[test]
fn jetbrains_claude_composer_repair_requires_quiet_window_after_due() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_redraw_state();
        state.last_output_at = Instant::now() - Duration::from_millis(90);
        state.jetbrains_claude_composer_repair_due =
            Some(Instant::now() - Duration::from_millis(1));

        state.maybe_redraw_status();
        assert!(
            state.needs_redraw,
            "ready composer repair should still wait for a post-burst quiet window"
        );
        assert!(
            state.jetbrains_claude_composer_repair_due.is_some(),
            "repair marker should stay armed while output is still settling"
        );

        state.last_output_at =
            Instant::now() - Duration::from_millis(CLAUDE_JETBRAINS_COMPOSER_REPAIR_QUIET_MS + 20);
        state.maybe_redraw_status();
        assert!(
            !state.needs_redraw,
            "once output is quiet, composer repair should commit"
        );
        assert!(
            state.jetbrains_claude_composer_repair_due.is_none(),
            "composer repair deadline should clear after redraw commits"
        );
    });
}

#[test]
fn jetbrains_claude_sync_repair_can_bypass_quiet_window() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_redraw_state();
        state.last_output_at = Instant::now();
        state.jetbrains_claude_composer_repair_due =
            Some(Instant::now() - Duration::from_millis(1));
        state.jetbrains_claude_repair_skip_quiet_window = true;

        state.maybe_redraw_status();
        assert!(
            !state.needs_redraw,
            "quiet-window bypass should allow scheduled repair redraw while synchronized rewrite packets are active"
        );
        assert!(
            state.jetbrains_claude_composer_repair_due.is_none(),
            "repair deadline should clear after bypassed redraw commits"
        );
        assert!(
            !state.jetbrains_claude_repair_skip_quiet_window,
            "quiet-window bypass marker should reset after redraw commits"
        );
    });
}

#[test]
fn jetbrains_claude_composer_repair_still_waits_when_cursor_save_is_active() {
    with_backend_label_env(Some("claude"), || {
        let mut state = jetbrains_redraw_state();
        state.last_output_at = Instant::now() - Duration::from_millis(90);
        state.jetbrains_dec_cursor_saved_active = true;
        state.jetbrains_claude_composer_repair_due =
            Some(Instant::now() - Duration::from_millis(1));

        state.maybe_redraw_status();
        assert!(
            state.needs_redraw,
            "active cursor-save should still block composer repair redraw"
        );
        assert!(
            state.jetbrains_claude_composer_repair_due.is_some(),
            "composer repair marker should stay armed until redraw can run safely"
        );
    });
}

#[test]
fn pty_output_contains_destructive_clear_detects_screen_clear_sequences() {
    assert!(pty_output_contains_destructive_clear(b"\x1b[2J\x1b[H"));
    assert!(pty_output_contains_destructive_clear(b"\x1b[3J"));
    assert!(pty_output_contains_destructive_clear(b"\x1bc"));
}

#[test]
fn pty_output_contains_destructive_clear_ignores_non_destructive_sequences() {
    assert!(!pty_output_contains_destructive_clear(b"\x1b[0J"));
    assert!(!pty_output_contains_destructive_clear(b"\x1b[K"));
    assert!(!pty_output_contains_destructive_clear(b"plain output"));
}

#[test]
fn pty_output_contains_erase_display_detects_display_erase_sequences() {
    assert!(pty_output_contains_erase_display(b"\x1b[J"));
    assert!(pty_output_contains_erase_display(b"\x1b[0J"));
    assert!(pty_output_contains_erase_display(b"\x1b[2J\x1b[H"));
}

#[test]
fn pty_output_contains_erase_display_ignores_non_display_erase_sequences() {
    assert!(!pty_output_contains_erase_display(b"\x1b[K"));
    assert!(!pty_output_contains_erase_display(b"\x1b[2K"));
    assert!(!pty_output_contains_erase_display(b"plain output"));
}

#[test]
fn cursor_claude_suppression_transition_bypasses_typing_hold_deferral() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
        state.rows = 24;
        state.cols = 120;
        state.display.banner_height = 0;
        state.display.preclear_banner_height = 1;
        state.last_user_input_at = Instant::now();
        state.last_output_at = Instant::now() - Duration::from_millis(200);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(200);

        let mut suppressed = StatusLineState::new();
        suppressed.hud_style = HudStyle::Minimal;
        suppressed.prompt_suppressed = true;
        state.display.enhanced_status = Some(suppressed.clone());

        let mut unsuppressed = suppressed;
        unsuppressed.prompt_suppressed = false;

        assert!(state.handle_message(WriterMessage::EnhancedStatus(unsuppressed)));
        assert!(
                !state.needs_redraw,
                "suppression state transitions must bypass typing-hold deferral so HUD state syncs immediately"
            );
        assert_eq!(state.display.banner_height, 1);
        assert!(state
            .display
            .enhanced_status
            .as_ref()
            .is_some_and(|status| !status.prompt_suppressed));
    });
}

#[test]
fn cursor_claude_post_clear_enhanced_status_bypasses_typing_hold_deferral() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
        state.rows = 24;
        state.cols = 120;
        state.display.banner_height = 0;
        state.display.preclear_banner_height = 1;
        state.display.enhanced_status = None;
        state.last_user_input_at = Instant::now();
        state.last_output_at = Instant::now() - Duration::from_millis(200);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(200);

        let mut next = StatusLineState::new();
        next.hud_style = HudStyle::Minimal;
        next.prompt_suppressed = false;

        assert!(state.handle_message(WriterMessage::EnhancedStatus(next)));
        assert!(
                !state.needs_redraw,
                "EnhancedStatus posted after ClearStatus must redraw immediately in typing-hold windows"
            );
        assert_eq!(state.display.banner_height, 1);
    });
}

#[test]
fn cursor_claude_non_scroll_csi_mutation_triggers_redraw() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 4;
        state.display.preclear_banner_height = 4;
        state.display.force_full_banner_redraw = false;
        state.cursor_startup_scroll_preclear_pending = false;
        // Simulate recent user typing so the typing-hold deferral is active.
        state.last_user_input_at = Instant::now();
        state.last_scroll_redraw_at = Instant::now();

        // Non-scrolling CSI cursor mutation: "\x1b[2K" (erase line) with no newline.
        // Claude Code emits these on every keystroke echo, clearing the HUD rows.
        // The forced redraw should bypass the typing-hold deferral and actually
        // repaint the HUD in the same cycle (needs_redraw consumed = false).
        assert!(state.handle_message(WriterMessage::PtyOutput(b"\x1b[2K".to_vec())));
        assert!(
            !state.needs_redraw,
            "Cursor+Claude must repaint HUD immediately after non-scrolling CSI mutation \
                 (force_redraw_after_preclear should bypass typing-hold deferral)"
        );
    });
}

#[test]
fn cursor_claude_banner_preclear_handles_wrap_scroll_without_newline() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
        state.rows = 24;
        state.cols = 10;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 4;
        state.display.preclear_banner_height = 4;
        state.display.force_full_banner_redraw = false;
        state.cursor_startup_scroll_preclear_pending = false;
        state.last_preclear_at =
            Instant::now() - Duration::from_millis(CURSOR_CLAUDE_BANNER_PRECLEAR_COOLDOWN_MS);
        state.last_scroll_redraw_at = Instant::now();

        assert!(state.handle_message(WriterMessage::PtyOutput(b"hello world".to_vec())));
        assert!(
                !state.needs_redraw,
                "wrap-driven scroll should trigger same-cycle preclear+redraw even without explicit newline"
            );
    });
}
