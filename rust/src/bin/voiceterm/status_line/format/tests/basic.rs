use super::*;
use crate::status_line::test_helpers;

#[test]
fn recording_indicator_color_pulses_with_theme_palette() {
    test_helpers::assert_recording_indicator_color_pulses_with_theme_palette();
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
    let line = format_status_line(&state, Theme::Coral, 40);
    assert!(!line.is_empty());
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
    let line = format_status_line(&state, Theme::None, 15);
    assert!(!line.is_empty());
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
    let line = format_status_line(&state, Theme::None, 65);
    assert!(line.contains("R") || line.contains("V") || line.contains("rec"));
}

#[test]
fn format_status_banner_minimal_mode() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Minimal;
    state.voice_mode = VoiceMode::Auto;
    state.auto_voice_enabled = true;

    let banner = format_status_banner(&state, Theme::None, 80);
    assert_eq!(banner.height, 1);
    assert!(banner.lines[0].contains("AUTO"));
}

#[test]
fn format_status_banner_returns_no_rows_when_prompt_suppressed() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.prompt_suppressed = true;

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
    assert_eq!(banner.height, 1);
    assert!(banner.lines[0].contains("rec"));
}

#[test]
fn format_status_banner_hidden_mode_recording_uses_theme_dim() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Hidden;
    state.recording_state = RecordingState::Recording;
    state.recording_duration = Some(3.0);

    let banner = format_status_banner(&state, Theme::Codex, 80);
    let line = &banner.lines[0];
    let colors = Theme::Codex.colors();

    assert!(line.contains(colors.dim));
}

#[test]
fn format_status_banner_minimal_mode_recording() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Minimal;
    state.recording_state = RecordingState::Recording;

    let banner = format_status_banner(&state, Theme::None, 80);
    assert_eq!(banner.height, 1);
    assert!(banner.lines[0].contains("REC"));
}

#[test]
fn format_status_banner_minimal_mode_processing() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Minimal;
    state.recording_state = RecordingState::Processing;

    let banner = format_status_banner(&state, Theme::None, 80);
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
