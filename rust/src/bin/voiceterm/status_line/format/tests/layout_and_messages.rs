use super::*;

#[test]
fn format_status_banner_full_mode_separators_align_with_shortcut_boundaries() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.voice_mode = VoiceMode::Auto;
    state.auto_voice_enabled = true;
    state.send_mode = crate::config::VoiceSendMode::Insert;
    state.recording_state = RecordingState::Recording;
    state.recording_duration = Some(21.9);
    state.meter_db = Some(-60.0);
    state.message = "Recording".to_string();

    let banner = format_status_banner(&state, Theme::None, 200);
    let main_row = strip_ansi(&banner.lines[1]);
    let shortcuts_row = strip_ansi(&banner.lines[2]);
    let separators = internal_separator_columns(&main_row);
    assert_eq!(separators.len(), 3);
    let expected = vec![
        button_start_col(&banner, crate::buttons::ButtonAction::ToggleAutoVoice),
        button_start_col(&banner, crate::buttons::ButtonAction::ToggleSendMode),
        button_start_col(&banner, crate::buttons::ButtonAction::SettingsToggle),
    ];
    assert_eq!(
        separators, expected,
        "main_row={main_row}\nshortcuts_row={shortcuts_row}"
    );
    assert!(main_row.contains("21.9s"));
    assert!(main_row.contains("-60dB"));
    assert!(shortcuts_row.contains("[edit]"));
    assert!(shortcuts_row.contains("[set]"));
}

#[test]
fn format_status_banner_full_mode_manual_ptt_keeps_separator_alignment() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.voice_mode = VoiceMode::Manual;
    state.auto_voice_enabled = false;
    state.send_mode = crate::config::VoiceSendMode::Insert;
    state.recording_state = RecordingState::Idle;
    state.message.clear();

    let banner = format_status_banner(&state, Theme::None, 200);
    let main_row = strip_ansi(&banner.lines[1]);
    let shortcuts_row = strip_ansi(&banner.lines[2]);
    let separators = internal_separator_columns(&main_row);
    assert_eq!(separators.len(), 3);
    let expected = vec![
        button_start_col(&banner, crate::buttons::ButtonAction::ToggleAutoVoice),
        button_start_col(&banner, crate::buttons::ButtonAction::ToggleSendMode),
        button_start_col(&banner, crate::buttons::ButtonAction::SettingsToggle),
    ];
    assert_eq!(
        separators, expected,
        "main_row={main_row}\nshortcuts_row={shortcuts_row}"
    );
    assert!(main_row.contains("PTT"));
    assert!(main_row.contains(" --.-s "));
    assert!(main_row.contains("--dB"));
    assert!(shortcuts_row.contains("[ptt]"));
    assert!(shortcuts_row.contains("[edit]"));
}

#[test]
fn format_status_banner_full_mode_shows_ready_with_ribbon_panel() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.hud_right_panel = HudRightPanel::Ribbon;
    state.hud_right_panel_recording_only = false;
    state.recording_state = RecordingState::Idle;
    state.message.clear();

    let banner = format_status_banner(&state, Theme::Coral, 96);
    assert_eq!(banner.height, 4);
    assert!(banner.lines[1].contains("Ready"));
    assert!(!banner.lines[2].contains("Ready"));
    assert!(banner.lines[1].contains("▁"));
}

#[test]
fn format_status_banner_full_mode_keeps_static_right_panel_when_recording_only_and_idle() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.hud_right_panel = HudRightPanel::Ribbon;
    state.hud_right_panel_recording_only = true;
    state.recording_state = RecordingState::Idle;
    state.message.clear();

    let banner = format_status_banner(&state, Theme::Coral, 96);
    assert!(banner.lines[1].contains("Ready"));
    assert!(banner.lines[1].contains("▁"));
}

#[test]
fn format_status_banner_full_mode_collapses_idle_success_to_ready() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Idle;
    state.message = "Transcript ready".to_string();

    let banner = format_status_banner(&state, Theme::Coral, 96);
    assert!(banner.lines.iter().any(|line| line.contains("Ready")));
    assert!(!banner
        .lines
        .iter()
        .any(|line| line.contains("Transcript ready")));
}

#[test]
fn format_status_banner_full_mode_avoids_duplicate_queue_text() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Idle;
    state.queue_depth = 1;
    state.message = "Transcript queued (1)".to_string();

    let banner = format_status_banner(&state, Theme::Coral, 96);
    assert!(!banner
        .lines
        .iter()
        .any(|line| line.contains("Transcript queued")));
    assert!(banner.lines.iter().any(|line| line.contains("Q:1")));
}

#[test]
fn format_status_banner_full_mode_uses_ptt_label_for_manual() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Idle;
    state.voice_mode = VoiceMode::Manual;

    let banner = format_status_banner(&state, Theme::Coral, 96);
    assert!(banner.lines.iter().any(|line| line.contains("PTT")));
    assert!(!banner.lines.iter().any(|line| line.contains("MANUAL")));
}

#[test]
fn format_status_banner_full_mode_recording_suppresses_stale_ready_text() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Recording;
    state.message = "Transcript ready".to_string();

    let banner = format_status_banner(&state, Theme::Coral, 96);
    assert!(!banner.lines.iter().any(|line| line.contains("Ready")));
}

#[test]
fn format_status_banner_full_mode_recording_shows_info_message_on_main_row() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Recording;
    state.message = "Edit mode: press Enter to send".to_string();

    let banner = format_status_banner(&state, Theme::Coral, 120);
    assert!(banner.lines[1].contains("Edit mode: press Enter to send"));
}

#[test]
fn format_status_banner_full_mode_processing_does_not_duplicate_processing_text() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.voice_mode = VoiceMode::Manual;
    state.recording_state = RecordingState::Processing;
    state.message = "Processing...".to_string();

    let banner = format_status_banner(&state, Theme::Coral, 96);
    let main_row = &banner.lines[1];
    assert!(main_row.contains("PTT"));
    let count = main_row.to_lowercase().matches("processing").count();
    assert_eq!(count, 1);
}

#[test]
fn format_status_banner_full_mode_shows_latency_on_shortcuts_row() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Idle;
    state.last_latency_ms = Some(228);

    let banner = format_status_banner(&state, Theme::Coral, 96);
    assert!(!banner.lines[1].contains("228ms"));
    assert!(banner.lines[2].contains("228ms"));
}

#[test]
fn format_status_banner_full_mode_places_ribbon_panel_on_main_row() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Idle;
    state.last_latency_ms = Some(228);
    state.hud_right_panel = HudRightPanel::Ribbon;
    state.hud_right_panel_recording_only = false;

    let banner = format_status_banner(&state, Theme::Coral, 120);
    assert!(banner.lines[1].contains("["));
    assert!(banner.lines[1].contains("▁"));
    assert!(!banner.lines[2].contains("▁"));
    assert!(banner.lines[2].contains("228ms"));
}

#[test]
fn format_status_banner_full_mode_shows_idle_info_message_on_main_row() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Idle;
    state.message = "Auto-voice disabled (capture cancelled)".to_string();

    let banner = format_status_banner(&state, Theme::Coral, 120);
    assert!(banner.lines[1].contains("Auto-voice disabled"));
}

#[test]
fn format_status_banner_full_mode_latency_label_mode_uses_prefixed_badge() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Idle;
    state.last_latency_ms = Some(300);
    state.latency_display = crate::config::LatencyDisplayMode::Label;

    let banner = format_status_banner(&state, Theme::None, 120);
    assert!(banner.lines[2].contains("Latency: 300ms"));
}

#[test]
fn format_status_banner_full_mode_latency_off_hides_badge() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Idle;
    state.last_latency_ms = Some(300);
    state.latency_display = crate::config::LatencyDisplayMode::Off;

    let banner = format_status_banner(&state, Theme::None, 120);
    assert!(!banner.lines[2].contains("300ms"));
}

#[test]
fn format_status_line_shows_transition_marker_when_active() {
    let mut state = StatusLineState::new();
    state.voice_mode = VoiceMode::Auto;
    state.transition_progress = 0.9;
    let line = format_status_line(&state, Theme::Coral, 80);
    assert!(line.contains("✦") || line.contains("•") || line.contains("·"));
}

#[test]
fn borderless_row_preserves_requested_width() {
    assert_eq!(borderless_row(0), "");
    assert_eq!(borderless_row(5), "     ");
    assert_eq!(display_width(&borderless_row(5)), 5);
}

#[test]
fn format_hidden_strip_shows_duration_only_while_recording() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_duration = Some(9.4);

    state.recording_state = RecordingState::Processing;
    let processing = format_hidden_strip(&state, &colors, 80);
    assert!(!processing.contains("9s"));

    state.recording_state = RecordingState::Recording;
    let recording = format_hidden_strip(&state, &colors, 80);
    assert!(recording.contains("9s"));
}

#[test]
fn format_status_banner_full_hud_fallback_uses_compact_breakpoint() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;

    let below = format_status_banner(
        &state,
        Theme::None,
        crate::status_line::layout::breakpoints::COMPACT - 1,
    );
    let at = format_status_banner(
        &state,
        Theme::None,
        crate::status_line::layout::breakpoints::COMPACT,
    );

    assert_eq!(below.height, 1);
    assert_eq!(at.height, 4);
}

#[test]
fn format_duration_section_thresholds_and_state_styles_are_stable() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Recording;

    state.recording_duration = Some(99.9);
    assert!(strip_ansi(&format_duration_section(&state, &colors)).contains("99.9s"));

    state.recording_duration = Some(100.0);
    let rounded = strip_ansi(&format_duration_section(&state, &colors));
    assert!(rounded.contains("100s"));
    assert!(!rounded.contains("100.0s"));

    state.recording_duration = Some(10_000.0);
    assert!(strip_ansi(&format_duration_section(&state, &colors)).contains("9999s"));

    state.recording_duration = Some(12.3);
    state.recording_state = RecordingState::Idle;
    let idle = format_duration_section(&state, &colors);
    assert!(idle.contains(colors.dim));

    state.recording_state = RecordingState::Recording;
    let recording = format_duration_section(&state, &colors);
    assert!(!recording.contains(colors.dim));
}
