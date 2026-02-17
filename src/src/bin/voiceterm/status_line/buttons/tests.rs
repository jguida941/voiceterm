use super::*;
use crate::status_line::layout::breakpoints;

fn count_substring(haystack: &str, needle: &str) -> usize {
    haystack.match_indices(needle).count()
}

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

#[test]
fn get_button_positions_hidden_idle_has_open_button() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Hidden;
    let positions = get_button_positions(&state, Theme::None, 80);
    assert_eq!(positions.len(), 1);
    assert_eq!(positions[0].row, 1);
    assert_eq!(positions[0].action, ButtonAction::ToggleHudStyle);
}

#[test]
fn get_button_positions_full_has_buttons() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    let positions = get_button_positions(&state, Theme::None, 80);
    assert!(!positions.is_empty());
    assert_eq!(positions[0].row, 2);
}

#[test]
fn get_button_positions_minimal_has_back_button() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Minimal;
    let positions = get_button_positions(&state, Theme::None, 40);
    assert_eq!(positions.len(), 1);
    assert_eq!(positions[0].row, 1);
    assert_eq!(positions[0].action, ButtonAction::HudBack);
}

#[test]
fn hidden_launcher_text_contains_hint() {
    let colors = Theme::None.colors();
    let state = StatusLineState::new();
    let line = hidden_launcher_text(&state, &colors);
    assert!(line.contains("Voice"));
    assert!(line.contains("Ctrl+U"));
}

#[test]
fn hidden_launcher_uses_neutral_gray_color_instead_of_theme_dim() {
    let colors = Theme::Codex.colors();
    let state = StatusLineState::new();
    let line = hidden_launcher_text(&state, &colors);
    assert!(line.contains("\x1b[90mVoiceTerm hidden"));
    assert!(!line.contains(&format!("{}VoiceTerm hidden", colors.dim)));
}

#[test]
fn hidden_launcher_open_button_uses_neutral_gray_when_unfocused() {
    let colors = Theme::Codex.colors();
    let state = StatusLineState::new();
    let (line, _) = format_hidden_launcher_with_button(&state, &colors, 80);
    assert!(line.contains("\x1b[90m[open]"));
    assert!(!line.contains(&format!("{}open", colors.info)));
}

#[test]
fn button_defs_use_send_label_from_send_mode() {
    let mut state = StatusLineState::new();
    let defs = get_button_defs(&state);
    let send = defs
        .iter()
        .find(|def| def.action == ButtonAction::ToggleSendMode)
        .expect("send button");
    assert_eq!(send.label, "send");

    state.send_mode = VoiceSendMode::Insert;
    let defs = get_button_defs(&state);
    let send = defs
        .iter()
        .find(|def| def.action == ButtonAction::ToggleSendMode)
        .expect("send button");
    assert_eq!(send.label, "edit");
}

#[test]
fn minimal_right_panel_respects_recording_only() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.hud_right_panel = HudRightPanel::Dots;
    state.hud_right_panel_recording_only = true;
    state.recording_state = RecordingState::Idle;
    state.meter_db = Some(-12.0);
    let idle_panel = minimal_right_panel(&state, &colors).expect("idle panel");
    assert!(idle_panel.contains("·"));

    state.recording_state = RecordingState::Recording;
    assert!(minimal_right_panel(&state, &colors).is_some());
}

#[test]
fn minimal_right_panel_ribbon_shows_waveform() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.hud_right_panel = HudRightPanel::Ribbon;
    state.hud_right_panel_recording_only = false;
    state.recording_state = RecordingState::Recording;
    state
        .meter_levels
        .extend_from_slice(&[-55.0, -42.0, -30.0, -18.0]);
    let panel = minimal_right_panel(&state, &colors).expect("panel");
    assert!(panel.contains("▁") || panel.contains("▂") || panel.contains("▃"));
}

#[test]
fn minimal_strip_text_includes_panel_when_enabled() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.hud_right_panel = HudRightPanel::Dots;
    state.hud_right_panel_recording_only = false;
    state.recording_state = RecordingState::Recording;
    state.meter_db = Some(-8.0);
    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains("•"));
}

#[test]
fn minimal_strip_recording_always_shows_db_lane() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Recording;
    state.meter_db = None;

    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains("-60dB"));
}

#[test]
fn minimal_strip_recording_keeps_panel_anchor_when_meter_db_missing() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Recording;
    state.hud_right_panel = HudRightPanel::Ribbon;
    state.hud_right_panel_recording_only = false;
    state
        .meter_levels
        .extend_from_slice(&[-48.0, -40.0, -33.0, -22.0, -15.0, -12.0]);
    state.meter_db = Some(-41.0);
    let with_meter = minimal_strip_text(&state, &colors);

    state.meter_db = None;
    let without_meter = minimal_strip_text(&state, &colors);

    let with_panel_col = with_meter
        .find('[')
        .expect("recording strip should render right panel");
    let without_panel_col = without_meter
        .find('[')
        .expect("recording strip should render right panel");
    assert_eq!(with_panel_col, without_panel_col);
}

#[test]
fn minimal_strip_idle_success_collapses_to_ready() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Idle;
    state.voice_mode = VoiceMode::Auto;
    state.message = "Transcript ready".to_string();

    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains("Ready"));
    assert!(!line.contains("Transcript ready"));
}

#[test]
fn minimal_strip_idle_shows_queue_state() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Idle;
    state.queue_depth = 2;
    state.message = "Auto-voice enabled".to_string();

    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains("Queued 2"));
}

#[test]
fn minimal_strip_idle_shows_info_message_text() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Idle;
    state.message = "Edit mode: press Enter to send".to_string();

    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains("Edit mode: press Enter to send"));
}

#[test]
fn minimal_strip_idle_shows_full_warning_message_text() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Idle;
    state.message = "Auto-voice disabled (capture cancelled)".to_string();

    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains("Auto-voice disabled (capture cancelled)"));
}

#[test]
fn minimal_strip_recording_shows_info_message_text() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Recording;
    state.meter_db = Some(-28.0);
    state.message = "Edit mode: press Enter to send".to_string();

    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains("Edit mode: press Enter to send"));
}

#[test]
fn minimal_strip_responding_shows_state_lane() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Responding;
    state.message = "Voice command: explain last error".to_string();

    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains("responding"));
}

#[test]
fn minimal_strip_idle_uses_theme_specific_auto_indicator() {
    let colors = Theme::Codex.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Idle;
    state.voice_mode = VoiceMode::Auto;

    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains("◇"));
}

#[test]
fn minimal_strip_recording_uses_theme_specific_recording_indicator() {
    let colors = Theme::Codex.colors();
    let mut state = StatusLineState::new();
    state.voice_mode = VoiceMode::Auto;
    state.recording_state = RecordingState::Recording;

    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains("◆"));
    assert!(!line.contains("◇"));
}

#[test]
fn minimal_strip_recording_uses_theme_recording_indicator_with_stable_color() {
    let colors = Theme::TokyoNight.colors();
    assert_ne!(colors.recording, colors.border);

    let mut state = StatusLineState::new();
    state.voice_mode = VoiceMode::Auto;
    state.recording_state = RecordingState::Recording;
    let indicator = expected_recording_indicator(state.voice_mode, &colors);

    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains(indicator));
    assert!(has_pulse_color_prefix(&line, indicator, &colors));
    assert!(line.contains("REC"));
}

#[test]
fn minimal_strip_recording_keeps_indicator_visible() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.voice_mode = VoiceMode::Auto;
    state.recording_state = RecordingState::Recording;
    state.recording_duration = Some(0.60);

    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains(expected_recording_indicator(state.voice_mode, &colors)));
    assert!(line.contains("REC"));
}

#[test]
fn minimal_ribbon_waveform_uses_level_colors() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.hud_right_panel = HudRightPanel::Ribbon;
    state.hud_right_panel_recording_only = false;
    state.recording_state = RecordingState::Recording;
    state
        .meter_levels
        .extend_from_slice(&[-55.0, -45.0, -35.0, -20.0, -10.0, -5.0]);

    let panel = minimal_right_panel(&state, &colors).expect("panel");
    assert!(panel.contains(colors.success));
}

#[test]
fn full_row_ready_and_latency_render_without_separator_dot_between_them() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Idle;
    state.last_latency_ms = Some(199);

    let row = format_button_row(&state, &colors, 120);
    assert!(!row.contains("Ready"));
    assert!(row.contains("199ms"));
}

#[test]
fn full_row_latency_label_mode_shows_prefixed_text() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Idle;
    state.last_latency_ms = Some(300);
    state.latency_display = LatencyDisplayMode::Label;

    let row = format_button_row(&state, &colors, 120);
    assert!(row.contains("Latency: 300ms"));
}

#[test]
fn full_row_latency_off_mode_hides_badge() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Idle;
    state.last_latency_ms = Some(199);
    state.latency_display = LatencyDisplayMode::Off;

    let row = format_button_row(&state, &colors, 120);
    assert!(!row.contains("199ms"));
}

#[test]
fn wake_badge_is_hidden_when_wake_listener_is_off() {
    let colors = Theme::None.colors();
    let state = StatusLineState::new();
    let (row, _) = format_button_row_with_positions(&state, &colors, 160, 2, true, false);
    assert!(!row.contains("Wake:"));
}

#[test]
fn wake_badge_renders_theme_matched_on_and_paused_states() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.wake_word_state = WakeWordHudState::Listening;
    let (on_row, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    assert!(on_row.contains("Wake: ON"));
    assert!(
        on_row.contains(&format!("{}Wake: ON{}", colors.border, colors.reset))
            || on_row.contains(&format!(
                "{}\u{1b}[1mWake: ON{}",
                colors.success, colors.reset
            ))
    );

    state.wake_word_state = WakeWordHudState::Paused;
    let (paused_row, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    assert!(paused_row.contains("Wake: PAUSED"));
    assert!(paused_row.contains(&format!("{}Wake: PAUSED{}", colors.warning, colors.reset)));
}

#[test]
fn shortcuts_row_stays_within_banner_width() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.recording_state = RecordingState::Idle;
    state.last_latency_ms = Some(316);
    state.latency_display = LatencyDisplayMode::Short;

    let inner_width = 90;
    let (row, _) =
        format_shortcuts_row_with_positions(&state, &colors, &colors.borders, inner_width, None);

    // +2 accounts for left/right border columns in full HUD rows.
    assert!(
        display_width(&row) <= inner_width + 2,
        "shortcuts row should not exceed full HUD width"
    );
}

#[test]
fn shortcuts_row_trailing_panel_hugs_right_border() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    let panel = "[▁▂▃▅▆]";

    let (row, _) =
        format_shortcuts_row_with_positions(&state, &colors, &colors.borders, 120, Some(panel));

    assert!(row.contains(panel));
    let panel_end_idx = row
        .rfind(']')
        .expect("row should contain panel close bracket");
    let right_border_idx = row.rfind('│').expect("row should contain right border");
    let panel_end_col = display_width(&row[..=panel_end_idx]);
    let right_border_col = display_width(&row[..right_border_idx]);
    assert_eq!(panel_end_col, right_border_col);
}

#[test]
fn hidden_launcher_button_aligns_to_right_edge_when_space_available() {
    let colors = Theme::None.colors();
    let state = StatusLineState::new();
    let open_button = hidden_launcher_button(&colors, false);
    let button_width = display_width(&open_button);
    let width = button_width + 18;

    let (line, button) = format_hidden_launcher_with_button(&state, &colors, width);
    let button = button.expect("open button should be present");

    assert_eq!(display_width(&line), width);
    assert_eq!(button.start_x, (width - button_width + 1) as u16);
    assert_eq!(button.end_x, width as u16);
    assert_eq!(button.row, 1);
    assert_eq!(button.action, ButtonAction::ToggleHudStyle);
}

#[test]
fn hidden_launcher_hides_button_when_width_too_small() {
    let colors = Theme::None.colors();
    let state = StatusLineState::new();
    let open_button = hidden_launcher_button(&colors, false);
    let width = display_width(&open_button) + 1;

    let (line, button) = format_hidden_launcher_with_button(&state, &colors, width);

    assert!(button.is_none());
    assert_eq!(display_width(&line), width);
}

#[test]
fn minimal_strip_button_geometry_is_stable() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Recording;
    state.meter_db = Some(-12.0);

    let back_button = format_button(&colors, "back", colors.border, false);
    let button_width = display_width(&back_button);
    let width = button_width + 24;

    let (line, button) = format_minimal_strip_with_button(&state, &colors, width);
    let button = button.expect("back button should be present");

    assert_eq!(display_width(&line), width);
    assert_eq!(button.start_x, (width - button_width + 1) as u16);
    assert_eq!(button.end_x, width as u16);
    assert_eq!(button.row, 1);
    assert_eq!(button.action, ButtonAction::HudBack);
}

#[test]
fn compact_button_row_omits_hud_button_and_recomputes_positions() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.queue_depth = 1;
    state.last_latency_ms = Some(312);

    let (full_row, full_positions) =
        format_button_row_with_positions(&state, &colors, 300, 2, true, false);
    let compact_width = display_width(&full_row).saturating_sub(1);
    let (compact_row, compact_positions) =
        format_button_row_with_positions(&state, &colors, compact_width, 2, true, false);

    assert_eq!(full_positions.len(), 7);
    assert_eq!(compact_positions.len(), 6);
    assert!(display_width(&compact_row) <= compact_width);
    assert!(compact_positions
        .iter()
        .all(|pos| pos.action != ButtonAction::ToggleHudStyle));
    assert!(compact_row.contains("Q:1"));
}

#[test]
fn button_row_ready_badge_requires_idle_and_empty_queue() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Idle;
    state.last_latency_ms = Some(250);

    let (idle_row, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, true);
    assert!(idle_row.contains("Ready"));
    assert!(idle_row.contains("250ms"));

    state.queue_depth = 1;
    let (queued_row, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, true);
    assert!(!queued_row.contains("Ready"));
    assert!(queued_row.contains("Q:1"));
}

#[test]
fn legacy_button_row_compact_mode_drops_hud_and_theme_entries() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.queue_depth = 2;
    state.last_latency_ms = Some(420);

    let full = format_button_row_legacy(&state, &colors, 240);
    let narrow_width = display_width(&full).saturating_sub(1);
    let compact = format_button_row_legacy(&state, &colors, narrow_width);

    assert!(display_width(&compact) <= narrow_width);
    assert!(!compact.contains("hud"));
    assert!(!compact.contains("theme"));
    assert!(compact.contains("help"));
}

#[test]
fn shortcuts_row_legacy_matches_positioned_renderer_when_untruncated() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.queue_depth = 1;
    state.last_latency_ms = Some(345);
    state.latency_display = LatencyDisplayMode::Label;

    let inner_width = 200;
    let (positioned, buttons) =
        format_shortcuts_row_with_positions(&state, &colors, &colors.borders, inner_width, None);
    let legacy = format_shortcuts_row_legacy(&state, &colors, &colors.borders, inner_width);

    assert_eq!(positioned, legacy);
    assert_eq!(display_width(&positioned), inner_width + 2);
    assert!(!buttons.is_empty());
    assert!(buttons.iter().all(|button| button.row == 2));
}

#[test]
fn full_hud_button_positions_match_expected_geometry() {
    let colors = Theme::None.colors();
    let state = StatusLineState::new();
    let (_, positions) = format_button_row_with_positions(&state, &colors, 300, 2, true, false);
    let expected = [
        (ButtonAction::VoiceTrigger, 3, 7),
        (ButtonAction::ToggleAutoVoice, 11, 15),
        (ButtonAction::ToggleSendMode, 19, 24),
        (ButtonAction::SettingsToggle, 28, 32),
        (ButtonAction::ToggleHudStyle, 36, 40),
        (ButtonAction::HelpToggle, 44, 49),
        (ButtonAction::ThemePicker, 53, 59),
    ];

    assert_eq!(positions.len(), expected.len());
    for (pos, (action, start, end)) in positions.iter().zip(expected) {
        assert_eq!(pos.action, action);
        assert_eq!(pos.start_x, start);
        assert_eq!(pos.end_x, end);
        assert_eq!(pos.row, 2);
    }
}

#[test]
fn full_hud_button_geometry_shifts_by_one_between_auto_and_ptt_labels() {
    let colors = Theme::None.colors();

    let mut auto_state = StatusLineState::new();
    auto_state.auto_voice_enabled = true;
    let (auto_row, auto_positions) =
        format_button_row_with_positions(&auto_state, &colors, 300, 2, true, false);
    assert!(auto_row.contains("[auto]"));

    let mut ptt_state = StatusLineState::new();
    ptt_state.auto_voice_enabled = false;
    let (ptt_row, ptt_positions) =
        format_button_row_with_positions(&ptt_state, &colors, 300, 2, true, false);
    assert!(ptt_row.contains("[ptt]"));

    let auto_send = auto_positions
        .iter()
        .find(|p| p.action == ButtonAction::ToggleSendMode)
        .expect("auto send position");
    let ptt_send = ptt_positions
        .iter()
        .find(|p| p.action == ButtonAction::ToggleSendMode)
        .expect("ptt send position");
    let auto_settings = auto_positions
        .iter()
        .find(|p| p.action == ButtonAction::SettingsToggle)
        .expect("auto settings position");
    let ptt_settings = ptt_positions
        .iter()
        .find(|p| p.action == ButtonAction::SettingsToggle)
        .expect("ptt settings position");

    assert_eq!(auto_send.start_x, ptt_send.start_x + 1);
    assert_eq!(auto_settings.start_x, ptt_settings.start_x + 1);
}

#[test]
fn full_hud_button_row_uses_uniform_separator_spacing_in_ptt_mode() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.auto_voice_enabled = false;

    let (row, _) = format_button_row_with_positions(&state, &colors, 300, 2, true, false);
    assert!(row.contains("[ptt] · [send]"));
    assert!(!row.contains("·  ["));
    assert!(!row.contains("]  ·"));
}

#[test]
fn compact_hud_button_positions_match_expected_geometry() {
    let colors = Theme::None.colors();
    let state = StatusLineState::new();
    let (_, positions) = format_button_row_with_positions(&state, &colors, 20, 2, true, false);
    let expected = [
        (ButtonAction::VoiceTrigger, 3, 7),
        (ButtonAction::ToggleAutoVoice, 9, 13),
        (ButtonAction::ToggleSendMode, 15, 20),
        (ButtonAction::SettingsToggle, 22, 26),
        (ButtonAction::HelpToggle, 28, 33),
        (ButtonAction::ThemePicker, 35, 41),
    ];

    assert_eq!(positions.len(), expected.len());
    for (pos, (action, start, end)) in positions.iter().zip(expected) {
        assert_eq!(pos.action, action);
        assert_eq!(pos.start_x, start);
        assert_eq!(pos.end_x, end);
        assert_eq!(pos.row, 2);
    }
}

#[test]
fn get_button_positions_full_hud_respects_breakpoint_boundary() {
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;

    let below = get_button_positions(&state, Theme::None, breakpoints::COMPACT - 1);
    let at = get_button_positions(&state, Theme::None, breakpoints::COMPACT);

    assert!(below.is_empty());
    assert!(!at.is_empty());
}

#[test]
fn minimal_status_text_shows_processing_message_when_idle() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Idle;
    state.message = "Processing...".to_string();

    let line = minimal_strip_text(&state, &colors);
    assert!(line.contains("Processing..."));
}

#[test]
fn hidden_launcher_boundary_width_shows_button_at_exact_threshold() {
    let colors = Theme::None.colors();
    let state = StatusLineState::new();
    let open_button = hidden_launcher_button(&colors, false);
    let width = display_width(&open_button) + 2;

    let (_, button) = format_hidden_launcher_with_button(&state, &colors, width);
    assert!(button.is_some());
}

#[test]
fn focused_buttons_use_info_brackets() {
    let colors = Theme::Coral.colors();

    let mut hidden_state = StatusLineState::new();
    hidden_state.hud_button_focus = Some(ButtonAction::ToggleHudStyle);
    let (hidden_line, hidden_button) =
        format_hidden_launcher_with_button(&hidden_state, &colors, 80);
    assert!(hidden_button.is_some());
    assert!(hidden_line.contains(&format!("{}[", colors.info)));

    let mut minimal_state = StatusLineState::new();
    minimal_state.hud_button_focus = Some(ButtonAction::HudBack);
    let (minimal_line, minimal_button) =
        format_minimal_strip_with_button(&minimal_state, &colors, 80);
    assert!(minimal_button.is_some());
    assert!(minimal_line.contains(&format!("{}[", colors.info)));
}

#[test]
fn shortcut_pill_does_not_reset_immediately_after_open_bracket() {
    let colors = Theme::Coral.colors();
    let pill = format_button(&colors, "rec", colors.recording, false);
    assert!(
        !pill.contains("[\u{1b}[0m"),
        "pill should keep active color context through bracket and label"
    );
}

#[test]
fn minimal_waveform_handles_padding_and_boundaries() {
    let none = Theme::None.colors();
    assert_eq!(minimal_waveform(&[-30.0], 3, &none), "▁▁▄");
    assert_eq!(minimal_waveform(&[-30.0, -30.0, -30.0], 3, &none), "▄▄▄");

    let colors = Theme::Coral.colors();
    let waveform = minimal_waveform(&[-25.0, -10.0], 2, &colors);
    let expected = format!(
        "{}▅{}{}▆{}",
        colors.warning, colors.reset, colors.error, colors.reset
    );
    assert_eq!(waveform, expected);
}

#[test]
fn minimal_pulse_dots_respect_activity_and_color_thresholds() {
    let none = Theme::None.colors();
    assert_eq!(minimal_pulse_dots(-60.0, &none), "[·····]");
    assert_eq!(minimal_pulse_dots(-48.0, &none), "[•····]");
    assert_eq!(minimal_pulse_dots(-30.0, &none), "[•••··]");
    assert_eq!(minimal_pulse_dots(0.0, &none), "[•••••]");

    let colors = Theme::Coral.colors();
    let warning = minimal_pulse_dots(-25.0, &colors);
    assert!(warning.contains(&format!("{}•{}", colors.warning, colors.reset)));
    assert!(!warning.contains(&format!("{}•{}", colors.success, colors.reset)));

    let error = minimal_pulse_dots(-5.0, &colors);
    assert!(error.contains(&format!("{}•{}", colors.error, colors.reset)));
}

#[test]
fn latency_threshold_colors_are_correct_in_full_and_legacy_rows() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Idle;

    state.last_latency_ms = Some(300);
    let (row_300, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    assert!(row_300.contains(&format!("{}300ms{}", colors.warning, colors.reset)));

    state.last_latency_ms = Some(500);
    let (row_500, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    assert!(row_500.contains(&format!("{}500ms{}", colors.error, colors.reset)));

    state.last_latency_ms = Some(300);
    let legacy_300 = format_button_row_legacy(&state, &colors, 200);
    assert!(legacy_300.contains(&format!("{}300ms{}", colors.warning, colors.reset)));

    state.last_latency_ms = Some(500);
    let legacy_500 = format_button_row_legacy(&state, &colors, 200);
    assert!(legacy_500.contains(&format!("{}500ms{}", colors.error, colors.reset)));
}

#[test]
fn latency_threshold_color_uses_worse_of_absolute_and_rtf() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Idle;
    state.last_latency_ms = Some(1100);
    state.last_latency_speech_ms = Some(6000);
    state.last_latency_rtf_x1000 = Some(183);

    let (row, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    assert!(row.contains(&format!("{}1100ms{}", colors.error, colors.reset)));

    state.last_latency_ms = Some(320);
    state.last_latency_rtf_x1000 = Some(500);
    let (row_warning, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    assert!(row_warning.contains(&format!("{}320ms{}", colors.warning, colors.reset)));

    state.last_latency_ms = Some(180);
    state.last_latency_rtf_x1000 = Some(900);
    let (row_error, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    assert!(row_error.contains(&format!("{}180ms{}", colors.error, colors.reset)));
}

#[test]
fn latency_badge_hides_during_recording_and_processing() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.last_latency_ms = Some(412);
    state.last_latency_rtf_x1000 = Some(300);

    state.recording_state = RecordingState::Recording;
    let (recording_row, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    assert!(!recording_row.contains("412ms"));

    state.recording_state = RecordingState::Processing;
    let (processing_row, _) =
        format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    assert!(!processing_row.contains("412ms"));

    state.recording_state = RecordingState::Idle;
    let (idle_row, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    assert!(idle_row.contains("412ms"));
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
fn recording_button_highlight_uses_theme_recording_color() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Recording;

    let highlight = button_highlight(&state, &colors, ButtonAction::VoiceTrigger);
    assert_eq!(highlight, colors.recording);
}

#[test]
fn full_row_rec_button_includes_recording_color_when_recording() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Recording;

    let row = format_button_row(&state, &colors, 200);
    assert!(row.contains(&format!("{}rec", colors.recording)));
}

#[test]
fn recording_button_highlight_is_empty_when_theme_has_no_color() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Recording;

    let highlight = button_highlight(&state, &colors, ButtonAction::VoiceTrigger);
    assert_eq!(highlight, "");
}

#[test]
fn recording_button_highlight_stays_recording_color_across_frames() {
    let colors = Theme::Coral.colors();
    assert_eq!(recording_button_highlight(&colors), colors.recording);
}

#[test]
fn wrappers_and_legacy_helpers_emit_structured_shortcut_text() {
    let colors = Theme::None.colors();
    let state = StatusLineState::new();

    let shortcuts = format_shortcuts_row(&state, &colors, &colors.borders, 120);
    assert!(!shortcuts.is_empty());
    assert!(shortcuts.contains("rec"));

    let shortcut = format_shortcut_colored(&colors, "u", "help", colors.info);
    assert!(shortcut.contains("u"));
    assert!(shortcut.contains("help"));
    assert!(shortcut.contains("["));
}

#[test]
fn minimal_status_text_non_idle_empty_message_is_none() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Processing;

    assert!(minimal_status_text(&state, &colors).is_none());
}

#[test]
fn minimal_right_panel_dots_without_meter_defaults_to_silent_level() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.hud_right_panel = HudRightPanel::Dots;
    state.hud_right_panel_recording_only = false;
    state.recording_state = RecordingState::Idle;
    state.meter_db = None;

    let panel = minimal_right_panel(&state, &colors).expect("dots panel");
    assert_eq!(panel, "[·····]");
}

#[test]
fn heartbeat_animation_truth_table() {
    assert!(should_animate_heartbeat(false, false));
    assert!(should_animate_heartbeat(false, true));
    assert!(!should_animate_heartbeat(true, false));
    assert!(should_animate_heartbeat(true, true));
}

#[test]
fn minimal_strip_shows_button_at_exact_width_threshold() {
    let colors = Theme::None.colors();
    let state = StatusLineState::new();
    let back_button = format_button(&colors, "back", colors.border, false);
    let button_width = display_width(&back_button);
    let width = button_width + 2;

    let (_, button) = format_minimal_strip_with_button(&state, &colors, width);
    assert!(button.is_some());
}

#[test]
fn minimal_strip_hides_button_just_below_width_threshold() {
    let colors = Theme::None.colors();
    let state = StatusLineState::new();
    let back_button = format_button(&colors, "back", colors.border, false);
    let button_width = display_width(&back_button);
    let width = button_width + 1;

    let (_, button) = format_minimal_strip_with_button(&state, &colors, width);
    assert!(button.is_none());
}

#[test]
fn full_row_focus_marks_exactly_one_button_bracket() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.hud_button_focus = Some(ButtonAction::ToggleSendMode);
    let (row, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    let focused_bracket = format!("{}[", colors.info);
    assert_eq!(count_substring(&row, &focused_bracket), 1);
}

#[test]
fn compact_row_focus_marks_exactly_one_button_bracket() {
    let colors = Theme::Coral.colors();
    let mut state = StatusLineState::new();
    state.hud_button_focus = Some(ButtonAction::HelpToggle);
    let (full_row, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    // Force compact path while still leaving room for the full compact row.
    let compact_width = display_width(&full_row).saturating_sub(1);
    let (row, positions) =
        format_button_row_with_positions(&state, &colors, compact_width, 2, true, false);
    assert_eq!(positions.len(), 6);
    let focused_bracket = format!("{}[", colors.info);
    assert_eq!(count_substring(&row, &focused_bracket), 1);
}

#[test]
fn queue_badge_zero_is_not_rendered_in_any_row_mode() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.queue_depth = 0;

    let (full, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    assert!(!full.contains("Q:0"));

    let (compact, _) = format_button_row_with_positions(&state, &colors, 20, 2, true, false);
    assert!(!compact.contains("Q:0"));

    let legacy_full = format_button_row_legacy(&state, &colors, 200);
    assert!(!legacy_full.contains("Q:0"));

    let legacy_compact = format_button_row_legacy(&state, &colors, breakpoints::COMPACT);
    assert!(!legacy_compact.contains("Q:0"));
}

#[test]
fn compact_row_queue_zero_not_rendered_when_untruncated() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.queue_depth = 0;

    let (full_row, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    let compact_width = display_width(&full_row).saturating_sub(1);
    let (compact_row, compact_positions) =
        format_button_row_with_positions(&state, &colors, compact_width, 2, true, false);
    assert_eq!(compact_positions.len(), 6);
    assert!(!compact_row.contains("Q:0"));
}

#[test]
fn queue_badge_positive_renders_in_full_and_legacy_rows() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.queue_depth = 1;

    let (full, _) = format_button_row_with_positions(&state, &colors, 200, 2, true, false);
    assert!(full.contains("Q:1"));

    let legacy = format_button_row_legacy(&state, &colors, 200);
    assert!(legacy.contains("Q:1"));
}

#[test]
fn legacy_compact_row_queue_positive_renders_when_untruncated() {
    let colors = Theme::None.colors();
    let mut state = StatusLineState::new();
    state.queue_depth = 1;

    let full_row = format_button_row_legacy(&state, &colors, 200);
    let compact_width = display_width(&full_row).saturating_sub(1);
    let compact_row = format_button_row_legacy(&state, &colors, compact_width);
    assert!(compact_row.contains("Q:1"));
}

#[test]
fn format_button_includes_non_empty_highlight_color() {
    let colors = Theme::Coral.colors();

    let highlighted = format_button(&colors, "send", colors.success, false);
    let plain = format_button(&colors, "send", "", false);

    assert!(highlighted.contains(colors.success));
    assert!(!plain.contains(colors.success));
}
