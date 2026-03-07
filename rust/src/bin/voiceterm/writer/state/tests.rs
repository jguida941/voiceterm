use super::*;
use crate::config::HudBorderStyle;
use crate::runtime_compat::RuntimeVariant;
use crate::test_env::env_lock;
use crate::HudStyle;
use rstest::rstest;
use std::env;

const CURSOR_CLAUDE_BANNER_PRECLEAR_COOLDOWN_MS: u64 = 180;
const CURSOR_PRECLEAR_COOLDOWN_MS: u64 = 220;
const CLAUDE_JETBRAINS_BANNER_PRECLEAR_COOLDOWN_MS: u64 = 90;
const CLAUDE_JETBRAINS_IDLE_REDRAW_HOLD_MS: u64 = 500;
const JETBRAINS_PRECLEAR_COOLDOWN_MS: u64 = 260;
const CODEX_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 320;
const CLAUDE_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 150;
const CLAUDE_CURSOR_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 900;
const CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS: u64 = 450;
const CLAUDE_JETBRAINS_COMPOSER_REPAIR_QUIET_MS: u64 = 700;
const CLAUDE_JETBRAINS_COMPOSER_RECENT_INPUT_MS: u64 = 1500;
const CLAUDE_IDE_NON_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 700;
const TYPING_REDRAW_HOLD_MS: u64 = 250;

struct BackendLabelEnvGuard {
    previous: Option<String>,
}

impl BackendLabelEnvGuard {
    fn install(backend_label: Option<&str>) -> Self {
        let previous = env::var("VOICETERM_BACKEND_LABEL").ok();
        match backend_label {
            Some(label) => env::set_var("VOICETERM_BACKEND_LABEL", label),
            None => env::remove_var("VOICETERM_BACKEND_LABEL"),
        }
        Self { previous }
    }
}

impl Drop for BackendLabelEnvGuard {
    fn drop(&mut self) {
        match &self.previous {
            Some(value) => env::set_var("VOICETERM_BACKEND_LABEL", value),
            None => env::remove_var("VOICETERM_BACKEND_LABEL"),
        }
    }
}

fn with_backend_label_env<T>(backend_label: Option<&str>, f: impl FnOnce() -> T) -> T {
    let _guard = env_lock();
    let _env_guard = BackendLabelEnvGuard::install(backend_label);
    f()
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum BackendMatrixCase {
    Codex,
    Claude,
    Other,
}

fn backend_flags_for_matrix(
    family: TerminalHost,
    backend: BackendMatrixCase,
) -> (bool, bool, bool, bool, bool) {
    let codex_jetbrains = family == TerminalHost::JetBrains && backend == BackendMatrixCase::Codex;
    let cursor_claude_startup_preclear = false;
    let cursor_claude_banner_preclear =
        family == TerminalHost::Cursor && backend == BackendMatrixCase::Claude;
    let claude_jetbrains_banner_preclear =
        family == TerminalHost::JetBrains && backend == BackendMatrixCase::Claude;
    let claude_jetbrains_cup_preclear_safe = claude_jetbrains_banner_preclear;
    (
        codex_jetbrains,
        cursor_claude_startup_preclear,
        cursor_claude_banner_preclear,
        claude_jetbrains_banner_preclear,
        claude_jetbrains_cup_preclear_safe,
    )
}

fn backend_family_for_matrix(backend: BackendMatrixCase) -> BackendFamily {
    match backend {
        BackendMatrixCase::Codex => BackendFamily::Codex,
        BackendMatrixCase::Claude => BackendFamily::Claude,
        BackendMatrixCase::Other => BackendFamily::Other,
    }
}

#[rstest]
#[case(
    TerminalHost::JetBrains,
    BackendMatrixCase::Codex,
    true,
    true,
    false,
    false
)]
#[case(
    TerminalHost::JetBrains,
    BackendMatrixCase::Claude,
    false,
    true,
    true,
    true
)]
#[case(
    TerminalHost::JetBrains,
    BackendMatrixCase::Other,
    false,
    false,
    false,
    false
)]
#[case(
    TerminalHost::Cursor,
    BackendMatrixCase::Codex,
    false,
    false,
    false,
    false
)]
#[case(
    TerminalHost::Cursor,
    BackendMatrixCase::Claude,
    false,
    true,
    false,
    true
)]
#[case(
    TerminalHost::Cursor,
    BackendMatrixCase::Other,
    false,
    false,
    false,
    false
)]
#[case(
    TerminalHost::Other,
    BackendMatrixCase::Codex,
    false,
    false,
    false,
    false
)]
#[case(
    TerminalHost::Other,
    BackendMatrixCase::Claude,
    false,
    false,
    false,
    false
)]
#[case(
    TerminalHost::Other,
    BackendMatrixCase::Other,
    false,
    false,
    false,
    false
)]
fn runtime_profile_matrix_matches_host_provider_contract(
    #[case] family: TerminalHost,
    #[case] backend: BackendMatrixCase,
    #[case] expect_treat_cr_as_scroll: bool,
    #[case] expect_flash_sensitive_scroll_profile: bool,
    #[case] expect_startup_guard: bool,
    #[case] expect_claude_non_scroll_profile: bool,
) {
    let profile = RuntimeProfile::resolve(family, backend_family_for_matrix(backend));
    assert_eq!(profile.treat_cr_as_scroll, expect_treat_cr_as_scroll);
    assert_eq!(
        profile.flash_sensitive_scroll_profile,
        expect_flash_sensitive_scroll_profile
    );
    assert_eq!(profile.startup_guard_enabled, expect_startup_guard);
    assert_eq!(
        profile.claude_non_scroll_redraw_profile,
        expect_claude_non_scroll_profile
    );
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
fn resize_clears_stale_banner_anchor_state_before_reflow() {
    let mut state = WriterState::new();
    state.rows = 24;
    state.cols = 80;
    state.display.banner_height = 4;
    state.display.banner_anchor_row = Some(2);

    assert!(state.handle_message(WriterMessage::Resize {
        rows: 30,
        cols: 100
    }));
    assert_eq!(state.rows, 30);
    assert_eq!(state.cols, 100);
    assert_eq!(state.display.banner_anchor_row, None);
    assert!(state.display.force_full_banner_redraw);
}

#[test]
fn resize_ignores_transient_jetbrains_claude_geometry_collapse() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::JetBrains);
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
        state.set_terminal_family_for_tests(TerminalHost::JetBrains);
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
#[case(TerminalHost::JetBrains, BackendMatrixCase::Codex, false)]
#[case(TerminalHost::JetBrains, BackendMatrixCase::Claude, true)]
#[case(TerminalHost::JetBrains, BackendMatrixCase::Other, false)]
#[case(TerminalHost::Cursor, BackendMatrixCase::Codex, false)]
#[case(TerminalHost::Cursor, BackendMatrixCase::Claude, true)]
#[case(TerminalHost::Cursor, BackendMatrixCase::Other, false)]
#[case(TerminalHost::Other, BackendMatrixCase::Codex, true)]
#[case(TerminalHost::Other, BackendMatrixCase::Claude, true)]
#[case(TerminalHost::Other, BackendMatrixCase::Other, true)]
fn should_preclear_bottom_rows_matrix_matches_host_provider_contract(
    #[case] family: TerminalHost,
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
    TerminalHost::JetBrains,
    BackendMatrixCase::Codex,
    Some(CODEX_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS)
)]
#[case(
    TerminalHost::JetBrains,
    BackendMatrixCase::Claude,
    Some(CLAUDE_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS)
)]
#[case(TerminalHost::JetBrains, BackendMatrixCase::Other, None)]
#[case(TerminalHost::Cursor, BackendMatrixCase::Codex, None)]
#[case(
    TerminalHost::Cursor,
    BackendMatrixCase::Claude,
    Some(CLAUDE_CURSOR_SCROLL_REDRAW_MIN_INTERVAL_MS)
)]
#[case(TerminalHost::Cursor, BackendMatrixCase::Other, None)]
#[case(TerminalHost::Other, BackendMatrixCase::Codex, None)]
#[case(TerminalHost::Other, BackendMatrixCase::Claude, None)]
#[case(TerminalHost::Other, BackendMatrixCase::Other, None)]
fn scroll_redraw_interval_matrix_matches_host_provider_contract(
    #[case] family: TerminalHost,
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
#[case(TerminalHost::JetBrains, BackendMatrixCase::Codex)]
#[case(TerminalHost::JetBrains, BackendMatrixCase::Claude)]
#[case(TerminalHost::JetBrains, BackendMatrixCase::Other)]
#[case(TerminalHost::Cursor, BackendMatrixCase::Codex)]
#[case(TerminalHost::Cursor, BackendMatrixCase::Claude)]
#[case(TerminalHost::Cursor, BackendMatrixCase::Other)]
#[case(TerminalHost::Other, BackendMatrixCase::Codex)]
#[case(TerminalHost::Other, BackendMatrixCase::Claude)]
#[case(TerminalHost::Other, BackendMatrixCase::Other)]
fn force_scroll_redraw_trigger_matrix_respects_host_provider_profile(
    #[case] family: TerminalHost,
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
        TerminalHost::JetBrains,
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
        TerminalHost::JetBrains,
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
        TerminalHost::JetBrains,
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
        TerminalHost::JetBrains,
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
        TerminalHost::JetBrains,
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
        TerminalHost::JetBrains,
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
    packet.extend(std::iter::repeat_n(b' ', 700));
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
        TerminalHost::Cursor,
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
        TerminalHost::Cursor,
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
        TerminalHost::Cursor,
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
        TerminalHost::Cursor,
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
        TerminalHost::Cursor,
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
    status.prompt_suppressed = false;
    let display = DisplayState {
        enhanced_status: Some(status),
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    assert!(should_preclear_bottom_rows(
        TerminalHost::Cursor,
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
    suppressed.prompt_suppressed = true;
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
        TerminalHost::Cursor,
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
        TerminalHost::Other,
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
fn preclear_policy_cursor_claude_banner_sets_immediate_redraw_flags() {
    let display = DisplayState {
        enhanced_status: Some(StatusLineState::new()),
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    let policy = PreclearPolicy::resolve(PreclearPolicyContext {
        family: TerminalHost::Cursor,
        display: &display,
        status_clear_pending: false,
        may_scroll_rows: true,
        codex_jetbrains: false,
        cursor_claude_startup_preclear: false,
        cursor_claude_banner_preclear: true,
        claude_jetbrains_banner_preclear: false,
        claude_jetbrains_cup_preclear_safe: false,
        claude_jetbrains_legacy_preclear_safe: false,
        in_resize_repair_window: false,
        preclear_blocked_for_recent_input: false,
        claude_jetbrains_destructive_clear: false,
        now,
        last_preclear_at: now,
    });
    let outcome = policy.outcome(true);
    assert!(policy.should_preclear);
    assert!(outcome.pre_cleared);
    assert!(outcome.force_redraw_after_preclear);
    assert!(outcome.force_full_banner_redraw);
    assert!(!outcome.needs_redraw);
}

#[test]
fn preclear_policy_jetbrains_claude_resize_window_forces_repair_flags() {
    let display = DisplayState {
        enhanced_status: Some(StatusLineState::new()),
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    let policy = PreclearPolicy::resolve(PreclearPolicyContext {
        family: TerminalHost::JetBrains,
        display: &display,
        status_clear_pending: false,
        may_scroll_rows: false,
        codex_jetbrains: false,
        cursor_claude_startup_preclear: false,
        cursor_claude_banner_preclear: false,
        claude_jetbrains_banner_preclear: true,
        claude_jetbrains_cup_preclear_safe: false,
        claude_jetbrains_legacy_preclear_safe: false,
        in_resize_repair_window: true,
        preclear_blocked_for_recent_input: false,
        claude_jetbrains_destructive_clear: false,
        now,
        last_preclear_at: now,
    });
    let outcome = policy.outcome(true);
    assert!(policy.should_preclear);
    assert!(outcome.pre_cleared);
    assert!(outcome.force_redraw_after_preclear);
    assert!(outcome.force_full_banner_redraw);
    assert!(outcome.needs_redraw);
}

#[test]
fn preclear_policy_outcome_without_preclear_disables_post_preclear_flags() {
    let display = DisplayState {
        enhanced_status: Some(StatusLineState::new()),
        banner_height: 4,
        preclear_banner_height: 4,
        ..DisplayState::default()
    };
    let now = Instant::now();
    let policy = PreclearPolicy::resolve(PreclearPolicyContext {
        family: TerminalHost::Cursor,
        display: &display,
        status_clear_pending: false,
        may_scroll_rows: true,
        codex_jetbrains: false,
        cursor_claude_startup_preclear: false,
        cursor_claude_banner_preclear: true,
        claude_jetbrains_banner_preclear: false,
        claude_jetbrains_cup_preclear_safe: false,
        claude_jetbrains_legacy_preclear_safe: false,
        in_resize_repair_window: false,
        preclear_blocked_for_recent_input: false,
        claude_jetbrains_destructive_clear: false,
        now,
        last_preclear_at: now,
    });
    let outcome = policy.outcome(false);
    assert!(!outcome.pre_cleared);
    assert!(!outcome.force_redraw_after_preclear);
    assert!(!outcome.force_full_banner_redraw);
    assert!(!outcome.needs_redraw);
}

fn redraw_policy_context<'a>(bytes: &'a [u8]) -> RedrawPolicyContext<'a> {
    let now = Instant::now();
    RedrawPolicyContext {
        family: TerminalHost::Other,
        runtime_variant: RuntimeVariant::Generic,
        bytes,
        now,
        last_scroll_redraw_at: now,
        scroll_redraw_min_interval: None,
        may_scroll_rows: false,
        display_force_full_banner_redraw: false,
        display_has_enhanced_status: false,
        display_has_unsuppressed_enhanced_status: false,
        display_should_force_full_banner_redraw_on_output: false,
        pending_clear_status: false,
        pending_clear_overlay: false,
        pending_overlay_panel_present: false,
        preclear_outcome: PreclearOutcome::default(),
        flash_sensitive_scroll_profile: false,
        claude_non_scroll_redraw_profile: false,
        claude_jetbrains_non_scroll_cursor_mutation: false,
        claude_jetbrains_composer_keystroke: false,
        claude_jetbrains_destructive_clear: false,
        claude_jetbrains_chunk_touches_cursor_save_restore: false,
        jetbrains_dec_cursor_saved_active: false,
        jetbrains_ansi_cursor_saved_active: false,
        claude_jetbrains_recent_destructive_clear_repaint: false,
    }
}

#[test]
fn redraw_policy_jetbrains_claude_scroll_defers_immediate_output_redraw() {
    let mut ctx = redraw_policy_context(b"\n");
    ctx.family = TerminalHost::JetBrains;
    ctx.runtime_variant = RuntimeVariant::JetBrainsClaude;
    ctx.may_scroll_rows = true;
    let policy = RedrawPolicy::resolve(ctx);
    assert!(policy.force_full_banner_redraw);
    assert!(policy.needs_redraw);
    assert!(!policy.output_redraw_needed);
    assert!(!policy.force_redraw_after_preclear);
}

#[test]
fn redraw_policy_cursor_claude_non_scroll_cursor_mutation_forces_immediate_redraw() {
    let mut ctx = redraw_policy_context(b"\x1b[2K");
    ctx.family = TerminalHost::Cursor;
    ctx.runtime_variant = RuntimeVariant::CursorClaude;
    ctx.display_has_enhanced_status = true;
    let policy = RedrawPolicy::resolve(ctx);
    assert!(policy.force_full_banner_redraw);
    assert!(policy.force_redraw_after_preclear);
    assert!(policy.output_redraw_needed);
    assert!(policy.needs_redraw);
}

#[test]
fn redraw_policy_jetbrains_claude_destructive_clear_busy_slot_arms_deferred_repair() {
    let mut ctx = redraw_policy_context(b"ignored");
    ctx.family = TerminalHost::JetBrains;
    ctx.runtime_variant = RuntimeVariant::JetBrainsClaude;
    ctx.claude_jetbrains_destructive_clear = true;
    ctx.claude_jetbrains_chunk_touches_cursor_save_restore = true;
    let policy = RedrawPolicy::resolve(ctx);
    assert!(policy.destructive_clear_repaint);
    assert!(policy.jetbrains_claude_destructive_clear_repaint);
    assert!(!policy.immediate_reanchor_allowed);
    assert!(!policy.force_redraw_after_preclear);
    assert!(policy.needs_redraw);
    assert!(policy.update_last_scroll_redraw_at);
    assert!(policy.schedule_jetbrains_destructive_clear_repair);
    assert!(policy.jetbrains_repair_skip_quiet_window);
}

#[test]
fn redraw_policy_codex_jetbrains_consumes_preclear_outcome_for_redraw_trigger() {
    let mut ctx = redraw_policy_context(b"ok");
    ctx.family = TerminalHost::JetBrains;
    ctx.runtime_variant = RuntimeVariant::JetBrainsCodex;
    ctx.preclear_outcome = PreclearOutcome {
        pre_cleared: true,
        ..PreclearOutcome::default()
    };
    let policy = RedrawPolicy::resolve(ctx);
    assert!(policy.output_redraw_needed);
    assert!(policy.needs_redraw);
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
        TerminalHost::Cursor,
        false,
        false,
        true,
        b"a",
        now,
        now - interval
    ));
    assert!(!should_force_non_scroll_banner_redraw(
        TerminalHost::Cursor,
        true,
        false,
        true,
        b"\n",
        now,
        now - interval
    ));
    assert!(!should_force_non_scroll_banner_redraw(
        TerminalHost::Cursor,
        true,
        false,
        true,
        b"a",
        now,
        now
    ));
    assert!(should_force_non_scroll_banner_redraw(
        TerminalHost::Cursor,
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
        TerminalHost::Cursor,
        now,
        now - Duration::from_millis(CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS / 2)
    ));
    // Non-Claude Cursor still defers
    assert!(should_defer_non_urgent_redraw_for_recent_input(
        TerminalHost::Cursor,
        now,
        now - Duration::from_millis(CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS / 2)
    ));
    // JetBrains defers with the shorter hold window
    assert!(should_defer_non_urgent_redraw_for_recent_input(
        TerminalHost::JetBrains,
        now,
        now - Duration::from_millis(TYPING_REDRAW_HOLD_MS / 2)
    ));
    // Other terminals defer too
    assert!(should_defer_non_urgent_redraw_for_recent_input(
        TerminalHost::Other,
        now,
        now - Duration::from_millis(TYPING_REDRAW_HOLD_MS / 2)
    ));
    // Cursor expires after its hold window
    assert!(!should_defer_non_urgent_redraw_for_recent_input(
        TerminalHost::Cursor,
        now,
        now - Duration::from_millis(CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS + 10)
    ));
    // Other expires after the shorter hold window
    assert!(!should_defer_non_urgent_redraw_for_recent_input(
        TerminalHost::Other,
        now,
        now - Duration::from_millis(TYPING_REDRAW_HOLD_MS + 10)
    ));
}

#[test]
fn maybe_redraw_status_defers_non_urgent_redraw_while_user_typing_in_cursor_claude() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
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
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
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
        state.set_terminal_family_for_tests(TerminalHost::Other);
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
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        assert!(state.handle_message(WriterMessage::UserInputActivity));
        assert!(
            state
                .adapter_state
                .cursor_claude_input_repair_due()
                .is_some(),
            "cursor+claude user input should schedule repair redraw deadline"
        );
    });
}

#[test]
fn user_input_activity_schedules_repair_when_status_is_pending() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
        state.rows = 24;
        state.cols = 120;
        state.pending.enhanced_status = Some(StatusLineState::new());
        assert!(state.handle_message(WriterMessage::UserInputActivity));
        assert!(
            state
                .adapter_state
                .cursor_claude_input_repair_due()
                .is_some(),
            "pending enhanced status should still schedule a repair redraw window"
        );
    });
}

#[test]
fn user_input_activity_schedules_repair_for_jetbrains_claude() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::JetBrains);
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        assert!(state.handle_message(WriterMessage::UserInputActivity));
        assert!(
            state
                .adapter_state
                .cursor_claude_input_repair_due()
                .is_none(),
            "JetBrains+Claude should avoid delayed repair redraws that can clobber the prompt row"
        );
    });
}

#[test]
fn jetbrains_claude_first_pty_output_consumes_startup_screen_clear_flag() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::JetBrains);
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        assert!(state
            .adapter_state
            .jetbrains_claude_startup_screen_clear_pending());

        assert!(state.handle_message(WriterMessage::PtyOutput(b"hello".to_vec())));
        assert!(
            !state
                .adapter_state
                .jetbrains_claude_startup_screen_clear_pending(),
            "JetBrains+Claude should clear the startup viewport only once on first PTY output"
        );
    });
}

#[test]
fn cursor_first_pty_output_consumes_startup_screen_clear_flag() {
    with_backend_label_env(Some("codex"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        assert!(state.adapter_state.cursor_startup_screen_clear_pending());

        assert!(state.handle_message(WriterMessage::PtyOutput(b"hello".to_vec())));
        assert!(
            !state.adapter_state.cursor_startup_screen_clear_pending(),
            "Cursor should clear the startup viewport only once on first PTY output"
        );
    });
}

#[test]
fn scheduled_cursor_claude_repair_redraw_fires_without_pending_status_update() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state
            .adapter_state
            .set_cursor_claude_input_repair_due(Some(Instant::now() - Duration::from_millis(1)));
        state.needs_redraw = false;
        state.maybe_redraw_status();
        assert!(
            state
                .adapter_state
                .cursor_claude_input_repair_due()
                .is_none(),
            "repair redraw deadline should be consumed after redraw"
        );
        assert!(!state.needs_redraw);
    });
}

#[test]
fn scheduled_jetbrains_claude_repair_redraw_waits_for_idle_settle() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::JetBrains);
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state
            .adapter_state
            .set_cursor_claude_input_repair_due(Some(Instant::now() - Duration::from_millis(1)));
        assert!(
            state
                .adapter_state
                .cursor_claude_input_repair_due()
                .is_none(),
            "JetBrains+Claude adapter ownership should reject cursor-only repair deadlines"
        );
        state.last_output_at = Instant::now();
        state.last_status_draw_at = Instant::now() - Duration::from_millis(2_000);
        state.needs_redraw = false;

        state.maybe_redraw_status();
        assert!(
            state
                .adapter_state
                .cursor_claude_input_repair_due()
                .is_none(),
            "JetBrains+Claude should keep cursor-only delayed repair deadlines impossible"
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
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.status = Some("ready".to_string());
        state.needs_redraw = true;
        state.force_redraw_after_preclear = true;
        state
            .adapter_state
            .set_cursor_claude_input_repair_due(Some(Instant::now() + Duration::from_millis(250)));
        state.maybe_redraw_status();
        assert!(
            state
                .adapter_state
                .cursor_claude_input_repair_due()
                .is_some(),
            "future repair deadline should survive unrelated redraws"
        );
    });
}

#[test]
fn maybe_redraw_status_jetbrains_claude_requires_idle_settle_for_passive_redraw() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::JetBrains);
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
fn jetbrains_claude_forces_single_line_full_hud_fallback_for_full_hud_requests() {
    with_backend_label_env(Some("claude"), || {
        let mut state = WriterState::new();
        state.set_terminal_family_for_tests(TerminalHost::JetBrains);
        state.rows = 24;
        state.cols = 120;
        state.last_output_at = Instant::now() - Duration::from_millis(1_000);
        state.last_status_draw_at = Instant::now() - Duration::from_millis(1_000);

        let mut next = StatusLineState::new();
        next.hud_style = HudStyle::Full;
        next.hud_border_style = HudBorderStyle::Single;
        next.prompt_suppressed = false;
        next.message = "Ready".to_string();

        assert!(state.handle_message(WriterMessage::EnhancedStatus(next)));
        assert_eq!(
            state.display.banner_height, 1,
            "JetBrains+Claude should collapse full HUD requests to a one-line full-HUD fallback"
        );
        assert_eq!(state.display.banner_lines.len(), 1);
        assert!(
            state.display.banner_lines[0].contains("Ready"),
            "single-line fallback should preserve primary status text"
        );
        assert!(
            state.display.banner_lines[0].contains("rec"),
            "single-line full fallback should preserve full HUD button controls"
        );
        assert!(
            state.display.banner_lines[0].contains("studio"),
            "single-line full fallback should retain trailing studio control"
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
    state.set_terminal_family_for_tests(TerminalHost::Other);
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
    state.set_terminal_family_for_tests(TerminalHost::Other);
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
    state.set_terminal_family_for_tests(TerminalHost::Other);
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
        state.set_terminal_family_for_tests(TerminalHost::JetBrains);
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
        state.set_terminal_family_for_tests(TerminalHost::JetBrains);
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
        state.set_terminal_family_for_tests(TerminalHost::JetBrains);
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
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
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
        state.set_terminal_family_for_tests(TerminalHost::Cursor);
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 4;
        state.display.preclear_banner_height = 4;
        state.display.force_full_banner_redraw = false;
        state
            .adapter_state
            .set_cursor_startup_scroll_preclear_pending(false);
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
        TerminalHost::JetBrains,
        false,
        false
    ));
    // Even with force_full_banner_redraw=true, still false for JetBrains
    assert!(!should_use_previous_banner_lines_for_profile(
        TerminalHost::JetBrains,
        true,
        false
    ));
    // Non-JetBrains terminals use normal line-diff logic
    assert!(should_use_previous_banner_lines_for_profile(
        TerminalHost::Cursor,
        false,
        false
    ));
}

mod scroll_repair_tests;
