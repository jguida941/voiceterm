use super::*;

fn expected_recording_indicator(mode: VoiceMode, colors: &ThemeColors) -> &'static str {
    let base = match mode {
        VoiceMode::Auto => colors.indicator_auto,
        VoiceMode::Manual => colors.indicator_manual,
        VoiceMode::Idle => colors.indicator_idle,
    };
    crate::theme::filled_indicator(base)
}

fn has_pulse_color_prefix(rendered: &str, indicator: &str, colors: &ThemeColors) -> bool {
    colors.recording.is_empty()
        || rendered.contains(&format!("{}{}", colors.recording, indicator))
        || rendered.contains(&format!("{}{}", colors.dim, indicator))
}

fn separator_columns(row: &str) -> Vec<usize> {
    let mut cols = Vec::new();
    let mut display_col = 0usize;
    let mut chars = row.chars();

    while let Some(ch) = chars.next() {
        if ch == '\u{1b}' {
            // Skip ANSI escape sequences.
            for next in chars.by_ref() {
                if ('@'..='~').contains(&next) {
                    break;
                }
            }
            continue;
        }

        display_col += 1;
        if ch == '│' {
            cols.push(display_col);
        }
    }

    cols
}

fn strip_ansi(input: &str) -> String {
    let mut out = String::with_capacity(input.len());
    let mut in_escape = false;
    for ch in input.chars() {
        if ch == '\x1b' {
            in_escape = true;
            continue;
        }
        if in_escape {
            if ch == 'm' {
                in_escape = false;
            }
            continue;
        }
        out.push(ch);
    }
    out
}

fn fnv1a64(input: &str) -> u64 {
    let mut hash: u64 = 0xcbf29ce484222325;
    for byte in input.as_bytes() {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

#[test]
fn recording_indicator_color_pulses_with_theme_palette() {
    for theme in [
        Theme::Ansi,
        Theme::Claude,
        Theme::Codex,
        Theme::TokyoNight,
        Theme::Coral,
        Theme::ChatGpt,
    ] {
        let colors = theme.colors();
        let pulse = recording_indicator_color(&colors);
        assert!(pulse == colors.recording || pulse == colors.dim);
    }
}

#[test]
fn processing_mode_indicator_uses_spinner_for_default_theme_symbol() {
    let colors = Theme::Codex.colors();
    let indicator = processing_mode_indicator(&colors);
    assert!(matches!(
        indicator,
        "⠋" | "⠙" | "⠹" | "⠸" | "⠼" | "⠴" | "⠦" | "⠧" | "⠇" | "⠏"
    ));
}

#[test]
fn processing_mode_indicator_uses_theme_override_symbol() {
    let mut colors = Theme::Codex.colors();
    colors.indicator_processing = "~";
    assert_eq!(processing_mode_indicator(&colors), "~");
}

fn internal_separator_columns(row: &str) -> Vec<usize> {
    let mut cols = separator_columns(row);
    if cols.len() >= 2 {
        cols.remove(0);
        cols.pop();
    }
    cols
}

fn button_start_col(banner: &StatusBanner, action: crate::buttons::ButtonAction) -> usize {
    usize::from(
        banner
            .buttons
            .iter()
            .find(|button| button.row == 2 && button.action == action)
            .expect("button position should exist on shortcuts row")
            .start_x,
    )
}

#[test]
fn format_status_line_basic() {
    let state = StatusLineState {
        auto_voice_enabled: true,
        voice_mode: VoiceMode::Auto,
        pipeline: Pipeline::Rust,
        sensitivity_db: -35.0,
        message: "Ready".to_string(),
        ..Default::default()
    };
    let line = format_status_line(&state, Theme::Coral, 80);
    assert!(line.contains("AUTO"));
    assert!(line.contains("-35dB"));
    assert!(line.contains("Ready"));
}

#[test]
fn format_status_line_with_duration() {
    let state = StatusLineState {
        recording_state: RecordingState::Recording,
        recording_duration: Some(2.5),
        message: "Recording...".to_string(),
        ..Default::default()
    };
    let line = format_status_line(&state, Theme::Coral, 80);
    assert!(line.contains("2.5s"));
    assert!(line.contains("REC"));
}

#[test]
fn format_status_line_narrow_terminal() {
    let state = StatusLineState {
        auto_voice_enabled: true,
        voice_mode: VoiceMode::Auto,
        message: "Ready".to_string(),
        ..Default::default()
    };
    // Narrow terminal should still produce output
    let line = format_status_line(&state, Theme::Coral, 40);
    assert!(!line.is_empty());
    // Should have some content
    assert!(line.len() > 5);
}

#[test]
fn format_status_line_very_narrow() {
    let state = StatusLineState {
        auto_voice_enabled: true,
        voice_mode: VoiceMode::Auto,
        message: "Ready".to_string(),
        ..Default::default()
    };
    // Very narrow terminal
    let line = format_status_line(&state, Theme::Coral, 20);
    assert!(!line.is_empty());
}

#[test]
fn format_status_line_minimal() {
    let state = StatusLineState {
        auto_voice_enabled: true,
        voice_mode: VoiceMode::Auto,
        message: "Ready".to_string(),
        ..Default::default()
    };
    // Minimal width
    let line = format_status_line(&state, Theme::None, 15);
    assert!(!line.is_empty());
    // Should contain indicator
    assert!(line.contains("◉") || line.contains("auto") || line.contains("Ready"));
}

#[test]
fn format_status_line_medium_shows_compact_shortcuts() {
    let state = StatusLineState {
        auto_voice_enabled: true,
        voice_mode: VoiceMode::Auto,
        message: "Ready".to_string(),
        ..Default::default()
    };
    // Medium terminal - should show compact shortcuts
    let line = format_status_line(&state, Theme::None, 65);
    // Should have some shortcut hint
    assert!(line.contains("R") || line.contains("V") || line.contains("rec"));
}

#[test]
fn format_status_banner_minimal_mode() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Minimal;
    state.voice_mode = VoiceMode::Auto;
    state.auto_voice_enabled = true;

    let banner = format_status_banner(&state, Theme::None, 80);
    // Minimal mode should produce a single-line banner
    assert_eq!(banner.height, 1);
    assert!(banner.lines[0].contains("AUTO"));
}

#[test]
fn format_status_banner_returns_no_rows_when_prompt_suppressed() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.claude_prompt_suppressed = true;

    let banner = format_status_banner(&state, Theme::Coral, 120);
    assert_eq!(banner.height, 0);
    assert!(banner.lines.is_empty());
    assert!(banner.buttons.is_empty());
}

#[test]
fn format_status_banner_hidden_mode_idle() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Hidden;
    state.voice_mode = VoiceMode::Auto;
    state.recording_state = RecordingState::Idle;

    let banner = format_status_banner(&state, Theme::None, 80);
    // Hidden mode when idle should keep a discoverable launcher row.
    assert_eq!(banner.height, 1);
    assert_eq!(banner.lines.len(), 1);
    assert!(banner.lines[0].contains("Voice"));
    assert!(!banner.lines[0].contains("Ctrl+U"));
    assert!(banner
        .buttons
        .iter()
        .any(|button| button.action == crate::buttons::ButtonAction::ToggleHudStyle));
    assert!(banner
        .buttons
        .iter()
        .any(|button| button.action == crate::buttons::ButtonAction::CollapseHiddenLauncher));
}

#[test]
fn format_status_banner_hidden_mode_collapsed_launcher_shows_only_open() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Hidden;
    state.hidden_launcher_collapsed = true;
    state.recording_state = RecordingState::Idle;

    let banner = format_status_banner(&state, Theme::None, 80);
    assert_eq!(banner.height, 1);
    assert!(banner.lines[0].contains("[open]"));
    assert!(!banner.lines[0].contains("[hide]"));
    assert_eq!(banner.buttons.len(), 1);
    assert_eq!(
        banner.buttons[0].action,
        crate::buttons::ButtonAction::ToggleHudStyle
    );
}

#[test]
fn format_status_banner_hidden_mode_recording() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Hidden;
    state.recording_state = RecordingState::Recording;

    let banner = format_status_banner(&state, Theme::None, 80);
    // Hidden mode when recording should show dim/obscure indicator
    assert_eq!(banner.height, 1);
    assert!(banner.lines[0].contains("rec")); // lowercase, obscure style
}

#[test]
fn format_status_banner_hidden_mode_recording_uses_neutral_gray() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Hidden;
    state.recording_state = RecordingState::Recording;
    state.recording_duration = Some(3.0);

    let banner = format_status_banner(&state, Theme::Codex, 80);
    let line = &banner.lines[0];
    let colors = Theme::Codex.colors();

    assert!(line.contains("\x1b[90m"));
    assert!(!line.contains(colors.dim));
}

#[test]
fn format_status_banner_minimal_mode_recording() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Minimal;
    state.recording_state = RecordingState::Recording;

    let banner = format_status_banner(&state, Theme::None, 80);
    // Minimal mode when recording should show REC
    assert_eq!(banner.height, 1);
    assert!(banner.lines[0].contains("REC"));
}

#[test]
fn format_status_banner_minimal_mode_processing() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Minimal;
    state.recording_state = RecordingState::Processing;

    let banner = format_status_banner(&state, Theme::None, 80);
    // Minimal mode when processing should show processing indicator
    assert_eq!(banner.height, 1);
    assert!(banner.lines[0].contains("processing"));
}

#[test]
fn format_status_banner_minimal_mode_responding() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Minimal;
    state.recording_state = RecordingState::Responding;

    let banner = format_status_banner(&state, Theme::None, 80);
    assert_eq!(banner.height, 1);
    assert!(banner.lines[0].contains("responding"));
}

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

#[test]
fn active_state_fallback_message_matches_recording_state() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();

    state.recording_state = RecordingState::Recording;
    assert!(active_state_fallback_message(&state, &colors).contains("Recording"));

    state.recording_state = RecordingState::Processing;
    assert!(active_state_fallback_message(&state, &colors).contains("Processing"));

    state.recording_state = RecordingState::Responding;
    assert!(active_state_fallback_message(&state, &colors).contains("Responding"));

    state.recording_state = RecordingState::Idle;
    assert!(active_state_fallback_message(&state, &colors).is_empty());
}

#[test]
fn format_right_panel_respects_recording_only_animation_gate() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.hud_right_panel = HudRightPanel::Ribbon;
    state.hud_right_panel_recording_only = true;
    state.recording_state = RecordingState::Idle;
    state
        .meter_levels
        .extend_from_slice(&[-12.0, -10.0, -8.0, -6.0, -4.0, -2.0]);

    let idle_panel = format_right_panel(&state, &colors, Theme::None, 12);
    let mut static_state = state.clone();
    static_state.meter_levels.clear();
    let static_panel = format_right_panel(&static_state, &colors, Theme::None, 12);
    assert_eq!(idle_panel, static_panel);

    state.recording_state = RecordingState::Recording;
    let recording_panel = format_right_panel(&state, &colors, Theme::None, 12);
    assert_ne!(recording_panel, static_panel);
}

#[test]
fn format_right_panel_enforces_minimum_content_width() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.hud_right_panel = HudRightPanel::Dots;
    state.meter_db = Some(-12.0);

    assert_eq!(format_right_panel(&state, &colors, Theme::None, 3), "   ");
    assert_eq!(format_right_panel(&state, &colors, Theme::None, 4), "    ");
    assert_ne!(
        format_right_panel(&state, &colors, Theme::None, 5),
        " ".repeat(5)
    );
}

#[test]
fn format_pulse_dots_boundaries_are_stable() {
    let none = Theme::None.colors();
    assert_eq!(format_pulse_dots(-60.0, &none, 5), "[·····]");
    assert_eq!(format_pulse_dots(-48.0, &none, 5), "[•····]");
    assert_eq!(format_pulse_dots(-30.0, &none, 5), "[•••··]");
    assert_eq!(format_pulse_dots(0.0, &none, 5), "[•••••]");
    assert_eq!(format_pulse_dots(-30.0, &none, 3), "[••·]");

    let colors = Theme::Coral.colors();
    let warning = format_pulse_dots(-25.0, &colors, 5);
    assert!(warning.contains(&format!("{}•{}", colors.warning, colors.reset)));
    assert!(!warning.contains(&format!("{}•{}", colors.success, colors.reset)));

    let error = format_pulse_dots(-5.0, &colors, 5);
    assert!(error.contains(&format!("{}•{}", colors.error, colors.reset)));
}

#[test]
fn format_meter_level_color_boundaries_are_exclusive() {
    let colors = Theme::Coral.colors();

    assert_eq!(meter_level_color(-31.0, &colors), colors.success);
    assert_eq!(meter_level_color(-30.0, &colors), colors.warning);
    assert_eq!(meter_level_color(-19.0, &colors), colors.warning);
    assert_eq!(meter_level_color(-18.0, &colors), colors.error);
}

#[test]
fn heartbeat_helpers_cover_truth_table() {
    assert!(scene_should_animate(VoiceSceneStyle::Theme, false, false));
    assert!(scene_should_animate(VoiceSceneStyle::Theme, false, true));
    assert!(!scene_should_animate(VoiceSceneStyle::Theme, true, false));
    assert!(scene_should_animate(VoiceSceneStyle::Theme, true, true));
    assert!(scene_should_animate(VoiceSceneStyle::Pulse, true, false));
    assert!(!scene_should_animate(VoiceSceneStyle::Static, false, true));
}

#[test]
fn heartbeat_color_requires_animation_and_peak() {
    let colors = Theme::Coral.colors();
    assert_eq!(heartbeat_color(false, false, &colors), colors.dim);
    assert_eq!(heartbeat_color(false, true, &colors), colors.dim);
    assert_eq!(heartbeat_color(true, false, &colors), colors.dim);
    assert_eq!(heartbeat_color(true, true, &colors), colors.info);
}

#[test]
fn format_heartbeat_panel_stays_dim_when_animation_is_disabled() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.hud_right_panel_recording_only = true;
    state.recording_state = RecordingState::Idle;

    let panel = format_heartbeat_panel(&state, &colors);
    assert!(panel.contains("·"));
    assert!(panel.contains(colors.dim));
}

#[test]
fn format_mode_indicator_is_stable_across_transition_progress() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.voice_mode = VoiceMode::Manual;
    state.recording_state = RecordingState::Idle;

    state.transition_progress = 0.0;
    let base = format_mode_indicator(&state, &colors);
    state.transition_progress = 0.9;
    let with_progress = format_mode_indicator(&state, &colors);

    assert_eq!(base, with_progress);
}

#[test]
fn format_transition_suffix_only_renders_for_idle_positive_progress() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.voice_mode = VoiceMode::Manual;
    state.recording_state = RecordingState::Recording;
    state.transition_progress = 0.9;
    assert!(format_transition_suffix(&state, &colors).is_empty());

    state.recording_state = RecordingState::Idle;
    state.transition_progress = 0.0;
    assert!(format_transition_suffix(&state, &colors).is_empty());

    state.transition_progress = 0.9;
    assert!(!format_transition_suffix(&state, &colors).is_empty());
}

#[test]
fn format_status_line_branch_boundaries_use_expected_renderers() {
    let mut state = StatusLineState::new();
    state.voice_mode = VoiceMode::Manual;
    state.message = "Boundary check".to_string();
    let theme = Theme::Coral;
    let colors = theme.colors();

    let minimal_width = crate::status_line::layout::breakpoints::MINIMAL - 1;
    let compact_width = crate::status_line::layout::breakpoints::COMPACT - 1;

    assert_eq!(
        format_status_line(&state, theme, minimal_width),
        format_minimal(&state, &colors, minimal_width)
    );
    assert_eq!(
        format_status_line(&state, theme, compact_width),
        format_compact(&state, &colors, theme, compact_width)
    );
}

#[test]
fn format_status_line_exact_fit_layout_is_stable() {
    let mut state = StatusLineState::new();
    state.voice_mode = VoiceMode::Manual;
    state.recording_state = RecordingState::Idle;
    state.message = "Ready".to_string();

    let theme = Theme::Coral;
    let colors = theme.colors();
    let probe_width = 200usize;
    let left = format_left_section(&state, &colors);
    let center = format_message(&state, &colors, theme, probe_width);
    let right = format_shortcuts(&colors);
    let exact_width = display_width(&left) + display_width(&center) + display_width(&right) + 2;
    let expected = format!("{left} {center}{right}");

    let exact = format_status_line(&state, theme, exact_width);
    assert_eq!(exact, expected);

    let tighter = format_status_line(&state, theme, exact_width - 1);
    assert_ne!(tighter, expected);
    assert!(display_width(&tighter) <= exact_width - 1);
}

#[test]
fn format_status_line_shortcut_lane_switches_at_breakpoints() {
    let colors = Theme::None.colors();

    assert_eq!(
        format_right_shortcuts(&colors, crate::status_line::layout::breakpoints::FULL),
        format_shortcuts(&colors)
    );
    assert_eq!(
        format_right_shortcuts(&colors, crate::status_line::layout::breakpoints::FULL - 1),
        format_shortcuts_compact(&colors)
    );
    assert_eq!(
        format_right_shortcuts(&colors, crate::status_line::layout::breakpoints::MEDIUM),
        format_shortcuts_compact(&colors)
    );
    assert_eq!(
        format_right_shortcuts(&colors, crate::status_line::layout::breakpoints::MEDIUM - 1),
        ""
    );
}

#[test]
fn full_hud_rows_never_exceed_terminal_width_across_common_sizes() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.voice_mode = VoiceMode::Manual;
    state.auto_voice_enabled = false;
    state.send_mode = crate::config::VoiceSendMode::Insert;
    state.message = "Ready".to_string();
    state.recording_duration = Some(12.3);
    state.meter_db = Some(-23.0);
    state.meter_levels = vec![-55.0, -46.0, -38.0, -29.0, -21.0, -15.0, -10.0];
    state.queue_depth = 2;
    state.last_latency_ms = Some(316);
    state.hud_right_panel = crate::config::HudRightPanel::Ribbon;
    state.hud_right_panel_recording_only = false;

    for width in 40..=220 {
        let banner = format_status_banner(&state, Theme::Coral, width);
        for line in banner.lines {
            let line_width = display_width(&line);
            assert!(
                line_width <= width,
                "line overflow at width {width}: line_width={line_width}, line={line:?}"
            );
        }
    }
}

#[test]
fn compact_registry_adapts_to_queue_state() {
    let mut state = StatusLineState::new();
    state.queue_depth = 2;
    let registry = compact_hud_registry(&state, 16);
    let ids: Vec<&str> = registry.iter().map(|module| module.id()).collect();
    assert_eq!(ids.first().copied(), Some("queue"));
}

#[test]
fn status_banner_snapshot_matrix_is_stable() {
    let mut full_idle = StatusLineState::new();
    full_idle.hud_style = HudStyle::Full;
    full_idle.voice_mode = VoiceMode::Auto;
    full_idle.auto_voice_enabled = true;
    full_idle.send_mode = crate::config::VoiceSendMode::Auto;
    full_idle.recording_state = RecordingState::Idle;
    full_idle.message = "Ready".to_string();
    full_idle.queue_depth = 1;
    full_idle.last_latency_ms = Some(128);

    let mut full_narrow = full_idle.clone();
    full_narrow.voice_mode = VoiceMode::Manual;
    full_narrow.auto_voice_enabled = false;

    let mut minimal_idle = StatusLineState::new();
    minimal_idle.hud_style = HudStyle::Minimal;
    minimal_idle.voice_mode = VoiceMode::Auto;
    minimal_idle.recording_state = RecordingState::Idle;
    minimal_idle.message = "Ready".to_string();

    let mut hidden_idle = StatusLineState::new();
    hidden_idle.hud_style = HudStyle::Hidden;
    hidden_idle.recording_state = RecordingState::Idle;
    hidden_idle.hidden_launcher_collapsed = true;

    let cases = [
        ("full_idle_w120", full_idle, 120usize, 0x83b1_b030_16d7_1504),
        (
            "full_manual_w52",
            full_narrow,
            52usize,
            0x786e_b245_8920_88e6,
        ),
        (
            "minimal_idle_w80",
            minimal_idle,
            80usize,
            0xd1e2_9893_0018_0914,
        ),
        (
            "hidden_collapsed_w60",
            hidden_idle,
            60usize,
            0x092d_a778_322c_7825,
        ),
    ];

    let mut snapshot_lines = Vec::new();
    let mut mismatches = Vec::new();

    for (name, state, width, expected) in cases {
        let banner = format_status_banner(&state, Theme::None, width);
        let rendered = banner.lines.join("\n");
        let actual = fnv1a64(&rendered);
        snapshot_lines.push(format!("{name}={actual:#018x}"));
        if actual != expected {
            mismatches.push(name);
        }
    }

    if !mismatches.is_empty() {
        panic!(
            "status-banner snapshot mismatch: {}\n{}",
            mismatches.join(", "),
            snapshot_lines.join("\n")
        );
    }
}
