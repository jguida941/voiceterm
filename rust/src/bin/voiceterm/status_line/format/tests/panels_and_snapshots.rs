use super::*;
use crate::status_line::test_helpers;

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
    test_helpers::assert_meter_level_color_boundaries_are_exclusive();
}

#[test]
fn heartbeat_helpers_cover_truth_table() {
    test_helpers::assert_heartbeat_helpers_cover_truth_table();
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
    assert!(display_width(&tighter) < exact_width);
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
    let _env = crate::test_env::env_lock();
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
