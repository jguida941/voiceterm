use super::*;

#[test]
fn format_status_banner_full_mode_recording_shows_rec_and_meter() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.voice_mode = VoiceMode::Auto;
    state.auto_voice_enabled = true;
    state.recording_state = RecordingState::Recording;
    state
        .meter_levels
        .extend_from_slice(&[-60.0, -45.0, -30.0, -15.0]);
    state.meter_db = Some(-30.0);
    state.message = "Recording...".to_string();

    let banner = format_status_banner(&state, Theme::Coral, 80);
    assert_eq!(banner.height, 4);
    assert!(banner.lines.iter().any(|line| line.contains("AUTO")));
    assert!(banner.lines.iter().any(|line| line.contains("Recording")));
    assert!(banner.lines.iter().any(|line| line.contains("dB")));
}

#[test]
fn format_status_banner_full_mode_recording_mode_lane_keeps_auto_without_rec_suffix() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.voice_mode = VoiceMode::Auto;
    state.recording_state = RecordingState::Recording;
    state.message.clear();

    let banner = format_status_banner(&state, Theme::Coral, 96);
    assert!(banner.lines[1].contains("AUTO"));
    assert!(!banner.lines[1].contains("AUTO REC"));
}

#[test]
fn format_status_banner_full_mode_manual_recording_mode_lane_keeps_ptt_without_rec_suffix() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.voice_mode = VoiceMode::Manual;
    state.recording_state = RecordingState::Recording;
    state.message.clear();

    let banner = format_status_banner(&state, Theme::Coral, 96);
    assert!(banner.lines[1].contains("PTT"));
    assert!(!banner.lines[1].contains("PTT REC"));
}

#[test]
fn format_status_banner_full_mode_idle_uses_theme_idle_indicator() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.voice_mode = VoiceMode::Auto;
    state.recording_state = RecordingState::Idle;

    let banner = format_status_banner(&state, Theme::Codex, 96);
    assert!(banner.lines[1].contains("◇"));
}

#[test]
fn format_status_banner_full_mode_recording_uses_theme_recording_indicator() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.voice_mode = VoiceMode::Auto;
    state.recording_state = RecordingState::Recording;
    state.message.clear();

    let banner = format_status_banner(&state, Theme::Codex, 96);
    assert!(banner.lines[1].contains("◆"));
    assert!(!banner.lines[1].contains("◇"));
}

#[test]
fn format_status_banner_full_mode_recording_uses_recording_color_for_mode_lane() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.voice_mode = VoiceMode::Auto;
    state.recording_state = RecordingState::Recording;
    state.message.clear();

    let theme = Theme::TokyoNight;
    let colors = theme.colors();
    assert_ne!(colors.recording, colors.border);
    let indicator = expected_recording_indicator(state.voice_mode, &colors);

    let banner = format_status_banner(&state, theme, 96);
    assert!(has_pulse_color_prefix(&banner.lines[1], indicator, &colors));
}

#[test]
fn format_mode_indicator_recording_keeps_theme_indicator_visible() {
    let mut state = StatusLineState::new();
    state.voice_mode = VoiceMode::Auto;
    state.recording_state = RecordingState::Recording;
    state.recording_duration = Some(0.60);

    let colors = Theme::Coral.colors();
    let mode = format_mode_indicator(&state, &colors);
    assert!(mode.contains(expected_recording_indicator(state.voice_mode, &colors)));
    assert!(mode.contains("AUTO"));
}

#[test]
fn format_status_line_compact_recording_uses_theme_recording_indicator() {
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Recording;
    state.voice_mode = VoiceMode::Auto;
    state.message.clear();

    let line = format_status_line(&state, Theme::Codex, 48);
    assert!(line.contains("◆"));
    assert!(!line.contains("◇"));
}

#[test]
fn format_status_banner_full_mode_border_style_override_uses_double_glyphs() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.hud_border_style = crate::config::HudBorderStyle::Double;

    let banner = format_status_banner(&state, Theme::Coral, 80);
    assert_eq!(banner.height, 4);
    assert!(banner.lines[0].contains('╔'));
    assert!(banner.lines[0].contains('╗'));
    assert!(banner.lines[3].contains('╚'));
    assert!(banner.lines[3].contains('╝'));
}

#[test]
fn format_status_banner_full_mode_none_border_hides_frame_rows() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.hud_border_style = crate::config::HudBorderStyle::None;
    state.hud_right_panel = HudRightPanel::Off;

    let banner = format_status_banner(&state, Theme::Coral, 80);
    assert_eq!(banner.height, 4);
    assert!(banner.lines[0].trim().is_empty());
    assert!(banner.lines[3].trim().is_empty());
}

#[test]
fn format_status_banner_full_mode_single_line_fallback_keeps_full_controls() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.hud_border_style = crate::config::HudBorderStyle::None;
    state.full_hud_single_line = true;
    state.hud_right_panel = HudRightPanel::Off;
    state.message = "Ready".to_string();

    let banner = format_status_banner(&state, Theme::Coral, 140);
    assert_eq!(banner.height, 1);
    assert_eq!(banner.lines.len(), 1);
    let line = strip_ansi(&banner.lines[0]);
    assert!(line.contains("Ready"), "line={line}");
    assert!(line.contains("[rec]"), "line={line}");
    assert!(line.contains("[studio]"), "line={line}");
    assert!(
        banner
            .buttons
            .iter()
            .any(|button| button.action == crate::buttons::ButtonAction::VoiceTrigger),
        "single-line full fallback should keep button hitboxes"
    );
}

#[test]
fn format_status_banner_full_mode_duration_lane_is_fixed_width() {
    let mut short = StatusLineState::new();
    short.hud_style = HudStyle::Full;
    short.recording_state = RecordingState::Recording;
    short.recording_duration = Some(6.7);
    short.meter_db = Some(-44.0);

    let mut long = short.clone();
    long.recording_duration = Some(10.4);

    let short_banner = format_status_banner(&short, Theme::None, 120);
    let long_banner = format_status_banner(&long, Theme::None, 120);
    let short_meter_col = short_banner.lines[1]
        .find("-44dB")
        .expect("short duration should contain meter");
    let long_meter_col = long_banner.lines[1]
        .find("-44dB")
        .expect("long duration should contain meter");
    assert_eq!(short_meter_col, long_meter_col);
}

#[test]
fn format_status_banner_full_mode_recording_without_meter_uses_floor_db() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Recording;
    state.recording_duration = Some(0.5);
    state.meter_db = None;
    state.meter_levels.clear();

    let banner = format_status_banner(&state, Theme::None, 120);
    let main_row = strip_ansi(&banner.lines[1]);
    assert!(main_row.contains("-60dB"), "main_row={main_row}");
    assert!(!main_row.contains(" --dB "), "main_row={main_row}");
}

#[test]
fn format_status_banner_full_mode_meter_separator_stays_stable_placeholder_to_recording() {
    let mut idle = StatusLineState::new();
    idle.hud_style = HudStyle::Full;
    idle.recording_state = RecordingState::Idle;
    idle.meter_db = None;
    idle.meter_levels.clear();

    let mut recording = idle.clone();
    recording.recording_state = RecordingState::Recording;
    recording.recording_duration = Some(0.5);

    let idle_banner = format_status_banner(&idle, Theme::None, 120);
    let recording_banner = format_status_banner(&recording, Theme::None, 120);

    let idle_cols = internal_separator_columns(&idle_banner.lines[1]);
    let recording_cols = internal_separator_columns(&recording_banner.lines[1]);
    assert_eq!(idle_cols, recording_cols);
}

#[test]
fn format_status_banner_full_mode_duration_separator_stays_right_of_edit_button_lane() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Recording;
    state.recording_duration = Some(5.0);
    state.meter_db = Some(-44.0);
    state.send_mode = crate::config::VoiceSendMode::Insert;

    let banner = format_status_banner(&state, Theme::None, 120);
    let main_row = &banner.lines[1];
    let shortcuts_row = &banner.lines[2];

    let meter_idx = main_row
        .find("-44dB")
        .expect("main row should include meter text");
    let before_meter = &main_row[..meter_idx];
    let separator_idx = before_meter
        .rfind('│')
        .expect("main row should include separator before meter");
    let separator_col = display_width(&main_row[..separator_idx]);
    let edit_col = display_width(
        shortcuts_row
            .split("[edit]")
            .next()
            .expect("shortcuts row should include edit button"),
    );
    assert!(separator_col >= edit_col);
}

#[test]
fn format_status_banner_full_mode_manual_matches_reference_spacing_from_this_md() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.voice_mode = VoiceMode::Manual;
    state.auto_voice_enabled = false;
    state.recording_state = RecordingState::Idle;
    state.message.clear();
    state.hud_right_panel = HudRightPanel::Off;

    let banner = format_status_banner(&state, Theme::TokyoNight, 200);
    let main_row = strip_ansi(&banner.lines[1]);
    let shortcuts_row = strip_ansi(&banner.lines[2]);

    assert!(main_row.contains("▹ PTT"), "main_row={main_row}");
    assert!(
        main_row.contains("PTT   │ --.-s │  --dB  │ Ready"),
        "main_row={main_row}"
    );
    assert!(
        shortcuts_row.contains("[rec] · [ptt] · [send] · [set] · [hud] · [help] · [studio]"),
        "shortcuts_row={shortcuts_row}"
    );
}

#[test]
fn format_status_banner_full_mode_main_row_separators_stay_stable_across_states() {
    let mut idle = StatusLineState::new();
    idle.hud_style = HudStyle::Full;
    idle.voice_mode = VoiceMode::Auto;
    idle.auto_voice_enabled = true;
    idle.recording_state = RecordingState::Idle;
    idle.meter_db = Some(-60.0);

    let mut recording = idle.clone();
    recording.recording_state = RecordingState::Recording;
    recording.recording_duration = Some(21.9);
    recording.message = "Recording".to_string();

    let mut processing = idle.clone();
    processing.recording_state = RecordingState::Processing;
    processing.recording_duration = Some(120.0);
    processing.meter_db = Some(-23.0);
    processing.transition_progress = 0.9;
    processing.message = "Processing...".to_string();

    let idle_banner = format_status_banner(&idle, Theme::None, 120);
    let recording_banner = format_status_banner(&recording, Theme::None, 120);
    let processing_banner = format_status_banner(&processing, Theme::None, 120);

    let idle_cols = internal_separator_columns(&idle_banner.lines[1]);
    let recording_cols = internal_separator_columns(&recording_banner.lines[1]);
    let processing_cols = internal_separator_columns(&processing_banner.lines[1]);

    assert_eq!(idle_cols.len(), 3);
    assert_eq!(idle_cols, recording_cols);
    assert_eq!(idle_cols, processing_cols);
}
