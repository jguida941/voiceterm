use super::*;
use crate::config::HudBorderStyle;
use crate::HudStyle;
use rstest::rstest;
use std::env;
use std::sync::{Mutex, OnceLock};

fn with_backend_label_env<T>(backend_label: Option<&str>, f: impl FnOnce() -> T) -> T {
    static ENV_LOCK: OnceLock<Mutex<()>> = OnceLock::new();
    let lock = ENV_LOCK.get_or_init(|| Mutex::new(()));
    let _guard = lock.lock().expect("env lock poisoned");

    let prev = env::var("VOICETERM_BACKEND_LABEL").ok();
    match backend_label {
        Some(label) => env::set_var("VOICETERM_BACKEND_LABEL", label),
        None => env::remove_var("VOICETERM_BACKEND_LABEL"),
    }

    let out = f();

    match prev {
        Some(value) => env::set_var("VOICETERM_BACKEND_LABEL", value),
        None => env::remove_var("VOICETERM_BACKEND_LABEL"),
    }
    out
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum BackendMatrixCase {
    Codex,
    Claude,
    Other,
}

fn backend_flags_for_matrix(
    family: TerminalFamily,
    backend: BackendMatrixCase,
) -> (bool, bool, bool, bool, bool) {
    let codex_jetbrains =
        family == TerminalFamily::JetBrains && backend == BackendMatrixCase::Codex;
    let cursor_claude_startup_preclear = false;
    let cursor_claude_banner_preclear =
        family == TerminalFamily::Cursor && backend == BackendMatrixCase::Claude;
    let claude_jetbrains_banner_preclear =
        family == TerminalFamily::JetBrains && backend == BackendMatrixCase::Claude;
    let claude_jetbrains_cup_preclear_safe = claude_jetbrains_banner_preclear;
    (
        codex_jetbrains,
        cursor_claude_startup_preclear,
        cursor_claude_banner_preclear,
        claude_jetbrains_banner_preclear,
        claude_jetbrains_cup_preclear_safe,
    )
}

#[test]
fn resize_ignores_unchanged_dimensions() {
    let mut state = WriterState::new();
    state.rows = 40;
    state.cols = 120;

    assert!(state.handle_message(WriterMessage::Resize {
        rows: 40,
        cols: 120
    }));
    assert_eq!(state.rows, 40);
    assert_eq!(state.cols, 120);
    assert!(!state.needs_redraw);
}

#[test]
fn resize_updates_dimensions_when_changed() {
    let mut state = WriterState::new();
    state.rows = 24;
    state.cols = 80;
    state.pty_line_col_estimate = 12;

    assert!(state.handle_message(WriterMessage::Resize {
        rows: 30,
        cols: 100
    }));
    assert_eq!(state.rows, 30);
    assert_eq!(state.cols, 100);
    assert_eq!(state.pty_line_col_estimate, 0);
}

#[test]
fn resize_ignores_transient_jetbrains_claude_geometry_collapse() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 80;

        assert!(state.handle_message(WriterMessage::Resize { rows: 2, cols: 80 }));
        assert_eq!(state.rows, 24);
        assert_eq!(state.cols, 80);
    });
}

#[test]
fn resize_accepts_small_geometry_for_non_claude_backends() {
    with_backend_label_env(Some("codex"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 80;

        assert!(state.handle_message(WriterMessage::Resize { rows: 2, cols: 80 }));
        assert_eq!(state.rows, 2);
        assert_eq!(state.cols, 80);
    });
}

#[test]
fn status_clear_height_only_when_banner_shrinks() {
    assert_eq!(status_clear_height_for_redraw(4, 4), 0);
    assert_eq!(status_clear_height_for_redraw(3, 5), 0);
    assert_eq!(status_clear_height_for_redraw(5, 3), 5);
}

#[rstest]
#[case(TerminalFamily::JetBrains, BackendMatrixCase::Codex, false)]
#[case(TerminalFamily::JetBrains, BackendMatrixCase::Claude, true)]
#[case(TerminalFamily::JetBrains, BackendMatrixCase::Other, false)]
#[case(TerminalFamily::Cursor, BackendMatrixCase::Codex, false)]
#[case(TerminalFamily::Cursor, BackendMatrixCase::Claude, true)]
#[case(TerminalFamily::Cursor, BackendMatrixCase::Other, false)]
#[case(TerminalFamily::Other, BackendMatrixCase::Codex, true)]
#[case(TerminalFamily::Other, BackendMatrixCase::Claude, true)]
#[case(TerminalFamily::Other, BackendMatrixCase::Other, true)]
fn should_preclear_bottom_rows_matrix_matches_host_provider_contract(
    #[case] family: TerminalFamily,
    #[case] backend: BackendMatrixCase,
    #[case] expected: bool,
) {
    let display = DisplayState {
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    let (
        codex_jetbrains,
        cursor_claude_startup_preclear,
        cursor_claude_banner_preclear,
        claude_jetbrains_banner_preclear,
        claude_jetbrains_cup_preclear_safe,
    ) = backend_flags_for_matrix(family, backend);
    let actual = should_preclear_bottom_rows(
        family,
        true,
        &display,
        false,
        codex_jetbrains,
        cursor_claude_startup_preclear,
        cursor_claude_banner_preclear,
        claude_jetbrains_banner_preclear,
        claude_jetbrains_cup_preclear_safe,
        now,
        now - Duration::from_secs(1),
    );
    assert_eq!(actual, expected, "family={family:?}, backend={backend:?}");
}

#[rstest]
#[case(
    TerminalFamily::JetBrains,
    BackendMatrixCase::Codex,
    Some(CODEX_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS)
)]
#[case(
    TerminalFamily::JetBrains,
    BackendMatrixCase::Claude,
    Some(CLAUDE_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS)
)]
#[case(TerminalFamily::JetBrains, BackendMatrixCase::Other, None)]
#[case(TerminalFamily::Cursor, BackendMatrixCase::Codex, None)]
#[case(
    TerminalFamily::Cursor,
    BackendMatrixCase::Claude,
    Some(CLAUDE_CURSOR_SCROLL_REDRAW_MIN_INTERVAL_MS)
)]
#[case(TerminalFamily::Cursor, BackendMatrixCase::Other, None)]
#[case(TerminalFamily::Other, BackendMatrixCase::Codex, None)]
#[case(TerminalFamily::Other, BackendMatrixCase::Claude, None)]
#[case(TerminalFamily::Other, BackendMatrixCase::Other, None)]
fn scroll_redraw_interval_matrix_matches_host_provider_contract(
    #[case] family: TerminalFamily,
    #[case] backend: BackendMatrixCase,
    #[case] expected_interval_ms: Option<u64>,
) {
    let actual = scroll_redraw_min_interval_for_profile(
        family,
        backend == BackendMatrixCase::Codex,
        backend == BackendMatrixCase::Claude,
    );
    let expected = expected_interval_ms.map(Duration::from_millis);
    assert_eq!(actual, expected, "family={family:?}, backend={backend:?}");
}

#[rstest]
#[case(TerminalFamily::JetBrains, BackendMatrixCase::Codex)]
#[case(TerminalFamily::JetBrains, BackendMatrixCase::Claude)]
#[case(TerminalFamily::JetBrains, BackendMatrixCase::Other)]
#[case(TerminalFamily::Cursor, BackendMatrixCase::Codex)]
#[case(TerminalFamily::Cursor, BackendMatrixCase::Claude)]
#[case(TerminalFamily::Cursor, BackendMatrixCase::Other)]
#[case(TerminalFamily::Other, BackendMatrixCase::Codex)]
#[case(TerminalFamily::Other, BackendMatrixCase::Claude)]
#[case(TerminalFamily::Other, BackendMatrixCase::Other)]
fn force_scroll_redraw_trigger_matrix_respects_host_provider_profile(
    #[case] family: TerminalFamily,
    #[case] backend: BackendMatrixCase,
) {
    let min_interval = scroll_redraw_min_interval_for_profile(
        family,
        backend == BackendMatrixCase::Codex,
        backend == BackendMatrixCase::Claude,
    );
    let now = Instant::now();
    let immediate = should_force_scroll_full_redraw(min_interval, now, now);
    assert_eq!(
        immediate,
        min_interval.is_none(),
        "family={family:?}, backend={backend:?}"
    );

    let elapsed_last_scroll = min_interval.map_or(now, |interval| now - interval);
    assert!(
        should_force_scroll_full_redraw(min_interval, now, elapsed_last_scroll),
        "family={family:?}, backend={backend:?}"
    );
}

#[test]
fn should_preclear_bottom_rows_jetbrains_skips_banner_preclear_without_transition() {
    let display = DisplayState {
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    assert!(!should_preclear_bottom_rows(
        TerminalFamily::JetBrains,
        true,
        &display,
        false,
        false,
        false,
        false,
        false,
        false,
        now,
        now - Duration::from_millis(JETBRAINS_PRECLEAR_COOLDOWN_MS)
    ));
}

#[test]
fn should_preclear_bottom_rows_jetbrains_preclears_on_pending_status_transition() {
    let display = DisplayState {
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    assert!(should_preclear_bottom_rows(
        TerminalFamily::JetBrains,
        true,
        &display,
        true,
        false,
        false,
        false,
        false,
        false,
        now,
        now - Duration::from_millis(JETBRAINS_PRECLEAR_COOLDOWN_MS)
    ));
}

#[test]
fn should_preclear_bottom_rows_jetbrains_codex_skips_preclear_even_on_transition() {
    let display = DisplayState {
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    assert!(!should_preclear_bottom_rows(
        TerminalFamily::JetBrains,
        true,
        &display,
        true,
        true,
        false,
        false,
        false,
        false,
        Instant::now(),
        Instant::now() - Duration::from_millis(JETBRAINS_PRECLEAR_COOLDOWN_MS)
    ));
}

#[test]
fn should_preclear_bottom_rows_jetbrains_respects_cooldown() {
    let display = DisplayState {
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    assert!(!should_preclear_bottom_rows(
        TerminalFamily::JetBrains,
        true,
        &display,
        true,
        false,
        false,
        false,
        false,
        false,
        now,
        now
    ));
}

#[test]
fn should_preclear_bottom_rows_jetbrains_claude_requires_safe_cup_chunk() {
    let display = DisplayState {
        enhanced_status: Some(StatusLineState::new()),
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    assert!(!should_preclear_bottom_rows(
        TerminalFamily::JetBrains,
        true,
        &display,
        false,
        false,
        false,
        false,
        true,
        false,
        now,
        now
    ));
    assert!(should_preclear_bottom_rows(
        TerminalFamily::JetBrains,
        true,
        &display,
        false,
        false,
        false,
        false,
        true,
        true,
        now,
        now - Duration::from_millis(CLAUDE_JETBRAINS_BANNER_PRECLEAR_COOLDOWN_MS)
    ));
}

#[test]
fn pty_chunk_starts_with_absolute_cursor_position_requires_early_cup() {
    assert!(pty_chunk_starts_with_absolute_cursor_position(
        b"\x1b[?25l\x1b[12;1Hhello"
    ));
    assert!(!pty_chunk_starts_with_absolute_cursor_position(
        b"\x1b7\x1b[2;3H"
    ));
    assert!(!pty_chunk_starts_with_absolute_cursor_position(b"hello"));
    assert!(!pty_chunk_starts_with_absolute_cursor_position(
        b"\x1b[2Khello"
    ));
    assert!(!pty_chunk_starts_with_absolute_cursor_position(b"\rhello"));
}

#[test]
fn bytes_contains_short_cursor_up_csi_only_matches_small_upward_moves() {
    assert!(bytes_contains_short_cursor_up_csi(
        b"\x1b[?2026h\x1b[A\x1b[?2026l"
    ));
    assert!(bytes_contains_short_cursor_up_csi(
        b"\x1b[?2026h\x1b[2A\x1b[?2026l"
    ));
    assert!(bytes_contains_short_cursor_up_csi(
        b"\x1b[?2026h\x1b[3A\x1b[?2026l"
    ));
    assert!(!bytes_contains_short_cursor_up_csi(
        b"\x1b[?2026h\x1b[4A\x1b[?2026l"
    ));
    assert!(!bytes_contains_short_cursor_up_csi(
        b"\x1b[?2026h\x1b[6A\x1b[?2026l"
    ));
}

#[test]
fn claude_composer_packet_detection_matches_long_wrapped_variant() {
    let mut packet = b"\x1b[?2026h\r\x1b[193C\x1b[2A \r\x1b[1B  sdfdsfsfsfdsfds".to_vec();
    packet.extend(std::iter::repeat(b' ').take(700));
    packet.extend_from_slice(b"\x1b[7m \x1b[27m\r\r\n\r\n\x1b[?2026l");
    assert!(
        chunk_looks_like_claude_composer_keystroke(&packet),
        "long synchronized composer packet should still trigger HUD repair path"
    );
}

#[test]
fn claude_composer_packet_detection_ignores_large_thinking_update_packets() {
    let packet = b"\x1b[?2026h\r\x1b[21C\x1b[6A\x1b[37m50\x1b[10C\x1b[38;2;174;174;174mthinking\x1b[39m\r\r\n\r\n\r\n\r\n\r\n\r\n\x1b[?2026l";
    assert!(
        !chunk_looks_like_claude_composer_keystroke(packet),
        "non-composer synchronized packets should not force immediate repair"
    );
}

#[test]
fn claude_synchronized_cursor_rewrite_detection_matches_thinking_packets() {
    let packet = b"\x1b[?2026h\r\x1b[21C\x1b[6A\x1b[37m50\x1b[10C\x1b[38;2;174;174;174m(thinking)\x1b[39m\r\r\n\r\n\r\n\r\n\r\n\r\n\x1b[?2026l";
    assert!(
        chunk_looks_like_claude_synchronized_cursor_rewrite(packet),
        "synchronized 6A thinking packets should be classified as cursor rewrites"
    );
}

#[test]
fn claude_synchronized_cursor_rewrite_detection_matches_long_think_status_packets() {
    let packet = b"\x1b[?2026h\r\x1b[9A\x1b[37m* Churned for 38s\x1b[39m\r\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\x1b[?2026l";
    assert!(
        chunk_looks_like_claude_synchronized_cursor_rewrite(packet),
        "long-think status packets should be classified as synchronized cursor rewrites"
    );
}

#[test]
fn claude_synchronized_cursor_rewrite_detection_ignores_non_rewrite_packets() {
    let packet = b"\x1b[?2026hplain text only\x1b[?2026l";
    assert!(
        !chunk_looks_like_claude_synchronized_cursor_rewrite(packet),
        "synchronized packets without cursor-up rewrite markers should be ignored"
    );
}

#[test]
fn should_preclear_bottom_rows_cursor_respects_cooldown() {
    let display = DisplayState {
        overlay_panel: Some(OverlayPanel {
            content: "panel".to_string(),
            height: 4,
        }),
        ..DisplayState::default()
    };
    let now = Instant::now();
    assert!(!should_preclear_bottom_rows(
        TerminalFamily::Cursor,
        true,
        &display,
        false,
        false,
        false,
        false,
        false,
        false,
        now,
        now
    ));
    assert!(should_preclear_bottom_rows(
        TerminalFamily::Cursor,
        true,
        &display,
        false,
        false,
        false,
        false,
        false,
        false,
        now,
        now - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS)
    ));
}

#[test]
fn should_preclear_bottom_rows_cursor_skips_banner_only_preclear() {
    let display = DisplayState {
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    assert!(!should_preclear_bottom_rows(
        TerminalFamily::Cursor,
        true,
        &display,
        false,
        false,
        false,
        false,
        false,
        false,
        now,
        now - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS)
    ));
}

#[test]
fn should_preclear_bottom_rows_cursor_claude_skips_banner_only_preclear() {
    let display = DisplayState {
        enhanced_status: Some(StatusLineState::new()),
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    assert!(!should_preclear_bottom_rows(
        TerminalFamily::Cursor,
        true,
        &display,
        false,
        false,
        false,
        false,
        false,
        false,
        now,
        now - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS)
    ));
}

#[test]
fn should_preclear_bottom_rows_cursor_claude_preclears_once_for_startup_scroll() {
    let display = DisplayState {
        enhanced_status: Some(StatusLineState::new()),
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    assert!(should_preclear_bottom_rows(
        TerminalFamily::Cursor,
        true,
        &display,
        false,
        false,
        true,
        false,
        false,
        false,
        now,
        now - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS)
    ));
}

#[test]
fn should_preclear_bottom_rows_cursor_claude_preclears_banner_without_cadence_gate() {
    let mut status = StatusLineState::new();
    status.claude_prompt_suppressed = false;
    let display = DisplayState {
        enhanced_status: Some(status),
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    assert!(should_preclear_bottom_rows(
        TerminalFamily::Cursor,
        true,
        &display,
        false,
        false,
        false,
        true,
        false,
        false,
        now,
        now
    ));
}

#[test]
fn enhanced_status_does_not_cancel_pending_clear_status() {
    let mut state = WriterState::new();
    state.rows = 24;
    state.cols = 120;
    state.pending.clear_status = true;
    state.last_output_at = Instant::now();
    state.last_status_draw_at = Instant::now();

    // EnhancedStatus should preserve an already-pending clear transition.
    assert!(state.pending.clear_status);

    let mut suppressed = StatusLineState::new();
    suppressed.claude_prompt_suppressed = true;
    assert!(state.handle_message(WriterMessage::EnhancedStatus(suppressed)));
    assert!(
        state.pending.clear_status,
        "suppression transitions must preserve pending clear until it is applied"
    );
}

#[test]
fn should_preclear_bottom_rows_cursor_preclears_for_pending_status_clear() {
    let display = DisplayState {
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    assert!(should_preclear_bottom_rows(
        TerminalFamily::Cursor,
        true,
        &display,
        true,
        false,
        false,
        false,
        false,
        false,
        now,
        now - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS)
    ));
}

#[test]
fn should_preclear_bottom_rows_other_terminal_uses_legacy_behavior() {
    let display = DisplayState {
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    assert!(should_preclear_bottom_rows(
        TerminalFamily::Other,
        true,
        &display,
        false,
        false,
        false,
        false,
        false,
        false,
        Instant::now(),
        Instant::now()
    ));
}

#[test]
fn should_force_scroll_full_redraw_without_interval_always_true() {
    let now = Instant::now();
    assert!(should_force_scroll_full_redraw(None, now, now));
}

#[test]
fn should_force_scroll_full_redraw_respects_interval_when_configured() {
    let now = Instant::now();
    let interval = Duration::from_millis(CODEX_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS);
    assert!(!should_force_scroll_full_redraw(Some(interval), now, now));
    assert!(should_force_scroll_full_redraw(
        Some(interval),
        now,
        now - Duration::from_millis(CODEX_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS)
    ));
}

#[test]
fn pty_output_can_mutate_cursor_line_detects_echo_like_chunks() {
    assert!(pty_output_can_mutate_cursor_line(b"\rprompt"));
    assert!(pty_output_can_mutate_cursor_line(b"\x08"));
    assert!(pty_output_can_mutate_cursor_line(b"\x1b[2K"));
    assert!(!pty_output_can_mutate_cursor_line(b"\n"));
    assert!(!pty_output_can_mutate_cursor_line(b"\x1b[32mok\x1b[0m"));
}

#[test]
fn should_force_non_scroll_banner_redraw_requires_claude_flash_profile_and_interval() {
    let now = Instant::now();
    let interval = Duration::from_millis(CLAUDE_IDE_NON_SCROLL_REDRAW_MIN_INTERVAL_MS);
    assert!(!should_force_non_scroll_banner_redraw(
        false,
        false,
        true,
        b"a",
        now,
        now - interval
    ));
    assert!(!should_force_non_scroll_banner_redraw(
        true,
        false,
        true,
        b"\n",
        now,
        now - interval
    ));
    assert!(!should_force_non_scroll_banner_redraw(
        true, false, true, b"a", now, now
    ));
    assert!(should_force_non_scroll_banner_redraw(
        true,
        false,
        true,
        b"\r",
        now,
        now - interval
    ));
}

#[test]
fn defer_non_urgent_redraw_for_recent_input_applies_to_all_terminals() {
    let now = Instant::now();
    // Cursor uses the longer hold window
    assert!(should_defer_non_urgent_redraw_for_recent_input(
        TerminalFamily::Cursor,
        true,
        now,
        now - Duration::from_millis(CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS / 2)
    ));
    // Non-Claude Cursor still defers
    assert!(should_defer_non_urgent_redraw_for_recent_input(
        TerminalFamily::Cursor,
        false,
        now,
        now - Duration::from_millis(CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS / 2)
    ));
    // JetBrains defers with the shorter hold window
    assert!(should_defer_non_urgent_redraw_for_recent_input(
        TerminalFamily::JetBrains,
        true,
        now,
        now - Duration::from_millis(TYPING_REDRAW_HOLD_MS / 2)
    ));
    // Other terminals defer too
    assert!(should_defer_non_urgent_redraw_for_recent_input(
        TerminalFamily::Other,
        false,
        now,
        now - Duration::from_millis(TYPING_REDRAW_HOLD_MS / 2)
    ));
    // Cursor expires after its hold window
    assert!(!should_defer_non_urgent_redraw_for_recent_input(
        TerminalFamily::Cursor,
        true,
        now,
        now - Duration::from_millis(CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS + 10)
    ));
    // Other expires after the shorter hold window
    assert!(!should_defer_non_urgent_redraw_for_recent_input(
        TerminalFamily::Other,
        true,
        now,
        now - Duration::from_millis(TYPING_REDRAW_HOLD_MS + 10)
    ));
}

#[test]
fn maybe_redraw_status_defers_non_urgent_redraw_while_user_typing_in_cursor_claude() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Cursor;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.needs_redraw = true;
        state.last_output_at = Instant::now() - Duration::from_millis(320);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(80);
        assert!(state.handle_message(WriterMessage::UserInputActivity));

        state.maybe_redraw_status();
        assert!(
            state.needs_redraw,
            "recent typing should defer non-urgent redraw in cursor+claude"
        );
    });
}

#[test]
fn maybe_redraw_status_does_not_defer_minimal_hud_recovery_in_cursor_claude() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Cursor;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 1;
        state.needs_redraw = true;
        state.last_output_at = Instant::now() - Duration::from_millis(320);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(80);
        assert!(state.handle_message(WriterMessage::UserInputActivity));

        state.maybe_redraw_status();
        assert!(
            !state.needs_redraw,
            "minimal HUD in cursor+claude should be redrawn even during typing hold"
        );
    });
}

#[test]
fn maybe_redraw_status_defers_non_urgent_redraw_while_user_typing_on_standard_terminal() {
    with_backend_label_env(None, || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Other;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.needs_redraw = true;
        state.last_output_at = Instant::now() - Duration::from_millis(320);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(80);
        assert!(state.handle_message(WriterMessage::UserInputActivity));

        state.maybe_redraw_status();
        assert!(
            state.needs_redraw,
            "recent typing should defer non-urgent redraw on standard terminals"
        );
    });
}

#[test]
fn user_input_activity_schedules_cursor_claude_repair_redraw() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Cursor;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        assert!(state.handle_message(WriterMessage::UserInputActivity));
        assert!(
            state.cursor_claude_input_repair_due.is_some(),
            "cursor+claude user input should schedule repair redraw deadline"
        );
    });
}

#[test]
fn user_input_activity_schedules_repair_when_status_is_pending() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Cursor;
        state.rows = 24;
        state.cols = 120;
        state.pending.enhanced_status = Some(StatusLineState::new());
        assert!(state.handle_message(WriterMessage::UserInputActivity));
        assert!(
            state.cursor_claude_input_repair_due.is_some(),
            "pending enhanced status should still schedule a repair redraw window"
        );
    });
}

#[test]
fn user_input_activity_schedules_repair_for_jetbrains_claude() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        assert!(state.handle_message(WriterMessage::UserInputActivity));
        assert!(
            state.cursor_claude_input_repair_due.is_none(),
            "JetBrains+Claude should avoid delayed repair redraws that can clobber the prompt row"
        );
    });
}

#[test]
fn scheduled_cursor_claude_repair_redraw_fires_without_pending_status_update() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Cursor;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.cursor_claude_input_repair_due = Some(Instant::now() - Duration::from_millis(1));
        state.needs_redraw = false;
        state.maybe_redraw_status();
        assert!(
            state.cursor_claude_input_repair_due.is_none(),
            "repair redraw deadline should be consumed after redraw"
        );
        assert!(!state.needs_redraw);
    });
}

#[test]
fn scheduled_jetbrains_claude_repair_redraw_waits_for_idle_settle() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.cursor_claude_input_repair_due = Some(Instant::now() - Duration::from_millis(1));
        state.last_output_at = Instant::now();
        state.last_status_draw_at = Instant::now() - Duration::from_millis(2_000);
        state.needs_redraw = false;

        state.maybe_redraw_status();
        assert!(
            state.cursor_claude_input_repair_due.is_some(),
            "JetBrains+Claude should ignore delayed cursor repair deadlines"
        );
        assert!(
            !state.needs_redraw,
            "JetBrains+Claude should not arm delayed repair redraws from this path"
        );
    });
}

#[test]
fn unrelated_redraw_keeps_future_cursor_claude_repair_deadline() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Cursor;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.status = Some("ready".to_string());
        state.needs_redraw = true;
        state.force_redraw_after_preclear = true;
        state.cursor_claude_input_repair_due = Some(Instant::now() + Duration::from_millis(250));
        state.maybe_redraw_status();
        assert!(
            state.cursor_claude_input_repair_due.is_some(),
            "future repair deadline should survive unrelated redraws"
        );
    });
}

#[test]
fn maybe_redraw_status_jetbrains_claude_requires_idle_settle_for_passive_redraw() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.needs_redraw = true;
        state.last_output_at =
            Instant::now() - Duration::from_millis(CLAUDE_JETBRAINS_IDLE_REDRAW_HOLD_MS / 2);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(2_000);

        state.maybe_redraw_status();
        assert!(
            state.needs_redraw,
            "passive JetBrains+Claude redraw should wait until output has been idle long enough"
        );

        state.last_output_at =
            Instant::now() - Duration::from_millis(CLAUDE_JETBRAINS_IDLE_REDRAW_HOLD_MS + 20);
        state.maybe_redraw_status();
        assert!(
            !state.needs_redraw,
            "once output settles, passive JetBrains+Claude redraw should proceed"
        );
    });
}

#[test]
fn jetbrains_claude_keeps_full_hud_content_but_forces_borderless_frame() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.last_output_at = Instant::now() - Duration::from_millis(1_000);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(1_000);

        let mut next = StatusLineState::new();
        next.hud_style = HudStyle::Full;
        next.hud_border_style = HudBorderStyle::Single;
        next.claude_prompt_suppressed = false;
        next.message = "Ready".to_string();

        assert!(state.handle_message(WriterMessage::EnhancedStatus(next)));
        assert_eq!(
            state.display.banner_height, 4,
            "JetBrains+Claude should keep full HUD row count"
        );
        assert_eq!(state.display.banner_lines.len(), 4);
        assert!(
            state.display.banner_lines[0].trim().is_empty(),
            "top row should be borderless filler"
        );
        assert!(
            state.display.banner_lines[2].contains("rec")
                && state.display.banner_lines[2].contains("studio"),
            "shortcuts row should remain visible in full HUD mode"
        );
    });
}

#[test]
fn maybe_redraw_status_throttles_when_no_priority_or_preclear_force() {
    let mut state = WriterState::new();
    state.rows = 24;
    state.cols = 120;
    state.display.status = Some("Processing...".to_string());
    state.needs_redraw = true;
    state.last_output_at = Instant::now();
    state.last_status_draw_at = Instant::now();

    state.maybe_redraw_status();
    assert!(state.needs_redraw);
}

#[test]
fn maybe_redraw_status_skips_throttle_when_preclear_force_is_set() {
    let mut state = WriterState::new();
    state.rows = 24;
    state.cols = 120;
    state.display.status = Some("Processing...".to_string());
    state.needs_redraw = true;
    state.force_redraw_after_preclear = true;
    state.last_output_at = Instant::now();
    state.last_status_draw_at = Instant::now();

    state.maybe_redraw_status();
    assert!(!state.needs_redraw);
    assert!(!state.force_redraw_after_preclear);
}

fn hook_terminal_size_error() -> io::Result<(u16, u16)> {
    Err(io::Error::other("terminal unavailable"))
}

fn hook_terminal_size_zero() -> io::Result<(u16, u16)> {
    Ok((0, 0))
}

#[test]
fn maybe_redraw_status_falls_back_when_terminal_size_call_fails() {
    struct HookGuard;
    impl Drop for HookGuard {
        fn drop(&mut self) {
            set_terminal_size_hook(None);
        }
    }

    set_terminal_size_hook(Some(hook_terminal_size_error));
    let _guard = HookGuard;

    let mut state = WriterState::new();
    state.rows = 0;
    state.cols = 0;
    state.pending.enhanced_status = Some(StatusLineState::new());
    state.needs_redraw = true;
    state.force_redraw_after_preclear = true;

    state.maybe_redraw_status();

    assert!(state.rows > 0);
    assert!(state.cols > 0);
    assert!(!state.needs_redraw);
    assert!(state.pending.enhanced_status.is_none());
    assert!(state.display.enhanced_status.is_some());
}

#[test]
fn maybe_redraw_status_falls_back_when_terminal_reports_zero_size() {
    struct HookGuard;
    impl Drop for HookGuard {
        fn drop(&mut self) {
            set_terminal_size_hook(None);
        }
    }

    set_terminal_size_hook(Some(hook_terminal_size_zero));
    let _guard = HookGuard;

    let mut state = WriterState::new();
    state.rows = 0;
    state.cols = 0;
    state.pending.enhanced_status = Some(StatusLineState::new());
    state.needs_redraw = true;
    state.force_redraw_after_preclear = true;

    state.maybe_redraw_status();

    assert!(state.rows > 0);
    assert!(state.cols > 0);
    assert!(!state.needs_redraw);
    assert!(state.display.enhanced_status.is_some());
}

#[test]
fn pty_output_may_scroll_rows_tracks_wrapping_without_newline() {
    let mut col = 0usize;
    assert!(!pty_output_may_scroll_rows(10, &mut col, b"hello", false));
    assert_eq!(col, 5);

    // Crosses terminal width boundary without an explicit newline byte.
    assert!(pty_output_may_scroll_rows(10, &mut col, b" world", false));
    assert_eq!(col, 1);
}

#[test]
fn pty_output_may_scroll_rows_flags_newline_and_resets_column() {
    let mut col = 7usize;
    assert!(pty_output_may_scroll_rows(80, &mut col, b"\nnext", false));
    assert_eq!(col, 4);
}

#[test]
fn pty_output_may_scroll_rows_treats_carriage_return_as_same_row_rewind() {
    let mut col = 12usize;
    assert!(!pty_output_may_scroll_rows(
        80,
        &mut col,
        b"\rprompt",
        false
    ));
    assert_eq!(col, 6);
}

#[test]
fn pty_output_may_scroll_rows_can_treat_carriage_return_as_scroll_for_codex_jetbrains() {
    let mut col = 12usize;
    assert!(pty_output_may_scroll_rows(80, &mut col, b"\rprompt", true));
    assert_eq!(col, 6);
}

#[test]
fn pty_output_may_scroll_rows_flags_csi_scroll_sequences() {
    let mut col = 9usize;
    assert!(pty_output_may_scroll_rows(80, &mut col, b"\x1b[2S", false));
    assert_eq!(col, 0);

    col = 9;
    assert!(pty_output_may_scroll_rows(80, &mut col, b"\x1b[1T", false));
    assert_eq!(col, 0);
}

#[test]
fn non_scrolling_output_does_not_force_full_banner_redraw() {
    let mut state = WriterState::new();
    state.terminal_family = TerminalFamily::Other;
    state.rows = 24;
    state.cols = 120;
    state.display.enhanced_status = Some(StatusLineState::new());
    state.display.banner_height = 4;
    state.display.force_full_banner_redraw = false;

    assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'a'])));
    assert!(!state.display.force_full_banner_redraw);
    assert!(
        !state.needs_redraw,
        "non-scrolling single-line echo should not trigger HUD redraw flicker"
    );
}

#[test]
fn scrolling_output_forces_full_banner_redraw_for_multi_row_hud() {
    let mut state = WriterState::new();
    state.terminal_family = TerminalFamily::Other;
    state.rows = 24;
    state.cols = 120;
    state.display.enhanced_status = Some(StatusLineState::new());
    state.display.banner_height = 4;
    state.display.force_full_banner_redraw = false;

    assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'\n'])));
    assert!(state.display.force_full_banner_redraw);
}

#[test]
fn scrolling_output_forces_full_banner_redraw_for_single_row_hud() {
    let mut state = WriterState::new();
    state.terminal_family = TerminalFamily::Other;
    state.rows = 24;
    state.cols = 120;
    state.display.enhanced_status = Some(StatusLineState::new());
    state.display.banner_height = 1;
    state.display.force_full_banner_redraw = false;

    assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'\n'])));
    assert!(!state.display.force_full_banner_redraw);
}

#[test]
fn jetbrains_scroll_output_redraw_state_matches_backend_policy() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 4;
        state.display.force_full_banner_redraw = false;

        assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'\n'])));
        // Claude/JetBrains keeps redraw pending (instead of forcing every
        // pre-clear to repaint immediately) to reduce visible flashing.
        assert!(state.needs_redraw);
        assert!(!state.force_redraw_after_preclear);
    });
}

#[test]
fn jetbrains_claude_non_cup_scroll_chunk_preclears_when_cursor_slot_untouched() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 4;
        state.display.preclear_banner_height = 4;
        state.display.force_full_banner_redraw = false;
        state.last_user_input_at =
            Instant::now() - Duration::from_millis(TYPING_REDRAW_HOLD_MS + 20);
        let previous_preclear =
            Instant::now() - Duration::from_millis(CLAUDE_JETBRAINS_BANNER_PRECLEAR_COOLDOWN_MS);
        state.last_preclear_at = previous_preclear;

        assert!(state.handle_message(WriterMessage::PtyOutput(b"line one\nline two".to_vec())));
        assert!(
            state.last_preclear_at > previous_preclear,
            "JetBrains+Claude should preclear banner rows for non-CUP scroll chunks when cursor save/restore is not active"
        );
    });
}

#[test]
fn jetbrains_claude_non_cup_scroll_chunk_skips_preclear_when_cursor_slot_touched() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 4;
        state.display.preclear_banner_height = 4;
        state.display.force_full_banner_redraw = false;
        state.last_user_input_at =
            Instant::now() - Duration::from_millis(TYPING_REDRAW_HOLD_MS + 20);
        let previous_preclear =
            Instant::now() - Duration::from_millis(CLAUDE_JETBRAINS_BANNER_PRECLEAR_COOLDOWN_MS);
        state.last_preclear_at = previous_preclear;

        assert!(state.handle_message(WriterMessage::PtyOutput(
            b"\x1b7line one\nline two\x1b8".to_vec()
        )));
        assert_eq!(
            state.last_preclear_at, previous_preclear,
            "JetBrains+Claude should avoid legacy preclear when chunk touches DEC save/restore"
        );
    });
}

#[test]
fn cursor_scrolling_output_marks_full_banner_for_redraw() {
    with_backend_label_env(Some("codex"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Cursor;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 4;
        state.display.force_full_banner_redraw = false;
        state.last_preclear_at =
            Instant::now() - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS);

        assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'\n'])));
        assert!(state.needs_redraw);
        assert!(state.display.force_full_banner_redraw);
    });
}

#[test]
fn cursor_claude_banner_preclear_requests_redraw_on_scrolling_newline_output() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Cursor;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 4;
        state.display.preclear_banner_height = 4;
        state.display.force_full_banner_redraw = false;
        state.cursor_startup_scroll_preclear_pending = false;
        state.last_preclear_at =
            Instant::now() - Duration::from_millis(CURSOR_CLAUDE_BANNER_PRECLEAR_COOLDOWN_MS);
        state.last_scroll_redraw_at = Instant::now();

        assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'\n'])));
        assert!(
            !state.needs_redraw,
            "cursor+claude preclear should redraw in the same cycle (no pending blink frame)"
        );
    });
}

#[test]
fn transition_redraw_after_preclear_disables_previous_line_diff() {
    assert!(!should_use_previous_banner_lines(false, true));
    assert!(!should_use_previous_banner_lines(true, true));
    assert!(!should_use_previous_banner_lines(true, false));
    assert!(should_use_previous_banner_lines(false, false));
}

#[test]
fn jetbrains_forces_full_banner_repaint_even_without_transition() {
    // JetBrains always forces full repaint (returns false) regardless of backend
    assert!(!should_use_previous_banner_lines_for_profile(
        TerminalFamily::JetBrains,
        false,
        false
    ));
    // Even with force_full_banner_redraw=true, still false for JetBrains
    assert!(!should_use_previous_banner_lines_for_profile(
        TerminalFamily::JetBrains,
        true,
        false
    ));
    // Non-JetBrains terminals use normal line-diff logic
    assert!(should_use_previous_banner_lines_for_profile(
        TerminalFamily::Cursor,
        false,
        false
    ));
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
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.needs_redraw = true;
        state.last_output_at =
            Instant::now() - Duration::from_millis(CLAUDE_JETBRAINS_IDLE_REDRAW_HOLD_MS + 40);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(2_000);
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
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.needs_redraw = true;
        state.last_output_at =
            Instant::now() - Duration::from_millis(CLAUDE_JETBRAINS_IDLE_REDRAW_HOLD_MS + 40);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(2_000);
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
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.needs_redraw = true;
        state.last_output_at = Instant::now();
        state.last_status_draw_at = Instant::now() - Duration::from_millis(2_000);
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
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        assert!(state.handle_message(WriterMessage::UserInputActivity));

        let composer_chunk = b"\x1b[?2026h\r\x1b[2A\x1b[7m \x1b[27m\r\n\x1b[?2026l".to_vec();
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
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.jetbrains_dec_cursor_saved_active = true;
        assert!(state.handle_message(WriterMessage::UserInputActivity));

        let composer_chunk = b"\x1b[?2026h\r\x1b[2A\x1b[7m \x1b[27m\r\n\x1b[?2026l".to_vec();
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
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.last_user_input_at =
            Instant::now() - Duration::from_millis(CLAUDE_JETBRAINS_COMPOSER_RECENT_INPUT_MS + 100);

        let composer_chunk = b"\x1b[?2026h\r\x1b[2A\x1b[7m \x1b[27m\r\n\x1b[?2026l".to_vec();
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
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 42;
        state.cols = 196;
        assert!(state.handle_message(WriterMessage::UserInputActivity));

        let mut hud = StatusLineState::new();
        hud.hud_style = HudStyle::Full;
        hud.claude_prompt_suppressed = false;
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
            state.jetbrains_claude_composer_repair_due.is_some(),
            "full HUD non-scroll cursor mutation should arm a repair deadline"
        );
    });
}

#[test]
fn jetbrains_claude_thinking_packet_without_recent_input_still_arms_repair() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 42;
        state.cols = 196;
        state.last_user_input_at =
            Instant::now() - Duration::from_millis(CLAUDE_JETBRAINS_COMPOSER_RECENT_INPUT_MS + 250);

        let mut hud = StatusLineState::new();
        hud.hud_style = HudStyle::Full;
        hud.claude_prompt_suppressed = false;
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
fn jetbrains_claude_composer_repair_requires_quiet_window_after_due() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.needs_redraw = true;
        state.last_output_at = Instant::now() - Duration::from_millis(90);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(2_000);
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
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.needs_redraw = true;
        state.last_output_at = Instant::now();
        state.last_status_draw_at = Instant::now() - Duration::from_millis(2_000);
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
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.needs_redraw = true;
        state.last_output_at = Instant::now() - Duration::from_millis(90);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(2_000);
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
fn cursor_claude_suppression_transition_bypasses_typing_hold_deferral() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Cursor;
        state.rows = 24;
        state.cols = 120;
        state.display.banner_height = 0;
        state.display.preclear_banner_height = 1;
        state.last_user_input_at = Instant::now();
        state.last_output_at = Instant::now() - Duration::from_millis(200);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(200);

        let mut suppressed = StatusLineState::new();
        suppressed.hud_style = HudStyle::Minimal;
        suppressed.claude_prompt_suppressed = true;
        state.display.enhanced_status = Some(suppressed.clone());

        let mut unsuppressed = suppressed;
        unsuppressed.claude_prompt_suppressed = false;

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
            .is_some_and(|status| !status.claude_prompt_suppressed));
    });
}

#[test]
fn cursor_claude_post_clear_enhanced_status_bypasses_typing_hold_deferral() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Cursor;
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
        next.claude_prompt_suppressed = false;

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
        state.terminal_family = TerminalFamily::Cursor;
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
        state.terminal_family = TerminalFamily::Cursor;
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
