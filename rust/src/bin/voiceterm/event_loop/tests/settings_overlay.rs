use super::*;

#[test]
fn settings_overlay_mouse_click_cycles_setting_value() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.config.latency_display = LatencyDisplayMode::Short;
    state.status_state.latency_display = LatencyDisplayMode::Short;
    let latency_row = settings_overlay_row_y(&state, SettingsItem::Latency);
    let click_x = centered_overlay_click_x(&state);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: click_x,
            y: latency_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
    assert_eq!(
        state.status_state.latency_display,
        LatencyDisplayMode::Label
    );
    let latency_index = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Latency)
        .expect("latency index");
    assert_eq!(state.settings.menu.selected, latency_index);
}

#[test]
fn settings_overlay_mouse_click_cycles_setting_value_with_centered_offset_x() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.config.latency_display = LatencyDisplayMode::Short;
    state.status_state.latency_display = LatencyDisplayMode::Short;
    let latency_row = settings_overlay_row_y(&state, SettingsItem::Latency);
    let click_x = centered_overlay_click_x(&state);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: click_x,
            y: latency_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
    assert_eq!(
        state.status_state.latency_display,
        LatencyDisplayMode::Label
    );
}

#[test]
fn settings_overlay_mouse_click_adjusts_sensitivity_with_centered_offset_x() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.status_state.sensitivity_db = -55.0;
    let sensitivity_row = settings_overlay_row_y(&state, SettingsItem::Sensitivity);
    let click_x = centered_overlay_click_x(&state);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: click_x,
            y: sensitivity_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
    assert_eq!(state.status_state.sensitivity_db, -50.0);
}

#[test]
fn settings_overlay_mouse_click_sensitivity_slider_left_moves_more_sensitive() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.status_state.sensitivity_db = -55.0;
    state.config.app.voice_vad_threshold_db = -55.0;
    let sensitivity_row = settings_overlay_row_y(&state, SettingsItem::Sensitivity);
    let click_x = settings_slider_click_x(&state, 1);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: click_x,
            y: sensitivity_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
    assert_eq!(state.status_state.sensitivity_db, -60.0);
    assert_eq!(
        state.current_status.as_deref(),
        Some("Mic sensitivity: -60 dB (more sensitive)")
    );
}

#[test]
fn settings_overlay_mouse_click_wake_sensitivity_slider_left_moves_less_sensitive() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.config.wake_word_sensitivity = 0.55;
    let sensitivity_row = settings_overlay_row_y(&state, SettingsItem::WakeSensitivity);
    let click_x = settings_slider_click_x(&state, 1);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: click_x,
            y: sensitivity_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
    assert!((state.config.wake_word_sensitivity - 0.50).abs() < f32::EPSILON);
}

#[test]
fn settings_overlay_mouse_click_selects_read_only_row_without_state_change() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    let initial_auto_voice = state.auto_voice_enabled;
    let backend_row = settings_overlay_row_y(&state, SettingsItem::Backend);
    let click_x = centered_overlay_click_x(&state);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: click_x,
            y: backend_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
    assert_eq!(state.auto_voice_enabled, initial_auto_voice);
    let backend_index = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Backend)
        .expect("backend index");
    assert_eq!(state.settings.menu.selected, backend_index);
}

#[test]
fn settings_overlay_mouse_click_close_row_closes_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    let close_row = settings_overlay_row_y(&state, SettingsItem::Close);
    let click_x = centered_overlay_click_x(&state);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: click_x,
            y: close_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
}

#[test]
fn settings_overlay_mouse_click_quit_row_stops_event_loop() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    let quit_row = settings_overlay_row_y(&state, SettingsItem::Quit);
    let click_x = centered_overlay_click_x(&state);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: click_x,
            y: quit_row,
        },
        &mut running,
    );

    assert!(!running);
}

#[test]
fn settings_overlay_mouse_click_footer_close_prefix_closes_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    let (x, y) = settings_overlay_footer_close_click(&state);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x, y },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
}

#[test]
fn settings_overlay_mouse_click_footer_outside_close_prefix_keeps_overlay_open() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;

    let overlay_height = settings_overlay_height() as u16;
    let overlay_top_y = state
        .ui
        .terminal_rows
        .saturating_sub(overlay_height)
        .saturating_add(1);
    let footer_y = overlay_top_y
        .saturating_add(overlay_height.saturating_sub(1))
        .saturating_sub(1);
    let cols = resolved_cols(state.ui.terminal_cols) as usize;
    let overlay_width = settings_overlay_width_for_terminal(cols);
    let x = centered_settings_overlay_rel_x_to_screen_x(&state, overlay_width.saturating_sub(2));

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x, y: footer_y },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
}

#[test]
fn centered_overlay_gutter_click_does_not_close_dev_panel_but_footer_close_still_works() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.terminal_cols = 120;
    state.ui.terminal_rows = 40;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    let cols = resolved_cols(state.ui.terminal_cols) as usize;
    let gutter_x = centered_overlay_left_gutter_x(state.ui.terminal_cols, panel_width(cols));
    let (_close_x, footer_y) = dev_panel_footer_close_click(&state);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: gutter_x,
            y: footer_y,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::DevPanel);

    let (close_x, close_y) = dev_panel_footer_close_click(&state);
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: close_x,
            y: close_y,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
}

#[test]
fn centered_overlay_gutter_click_does_not_trigger_settings_action_but_centered_click_still_works() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.settings.menu.selected = 0;
    state.config.latency_display = LatencyDisplayMode::Short;
    state.status_state.latency_display = LatencyDisplayMode::Short;

    let row = settings_overlay_row_y(&state, SettingsItem::Latency);
    let cols = resolved_cols(state.ui.terminal_cols) as usize;
    let gutter_x = centered_overlay_left_gutter_x(
        state.ui.terminal_cols,
        settings_overlay_width_for_terminal(cols),
    );
    let latency_index = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Latency)
        .expect("latency index");

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: gutter_x,
            y: row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
    assert_eq!(state.settings.menu.selected, 0);
    assert_eq!(
        state.status_state.latency_display,
        LatencyDisplayMode::Short
    );

    let click_x = centered_overlay_click_x(&state);
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x: click_x, y: row },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
    assert_eq!(state.settings.menu.selected, latency_index);
    assert_ne!(
        state.status_state.latency_display,
        LatencyDisplayMode::Short
    );
}

#[test]
fn centered_overlay_gutter_click_does_not_trigger_theme_picker_action_but_centered_click_still_works(
) {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemePicker;
    state.theme_studio.picker_selected = 2;
    let initial_theme = state.theme;

    let option_index = 0;
    let row = theme_picker_overlay_row_y(&state, option_index);
    let cols = resolved_cols(state.ui.terminal_cols) as usize;
    let gutter_x = centered_overlay_left_gutter_x(
        state.ui.terminal_cols,
        theme_picker_total_width_for_terminal(cols),
    );

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: gutter_x,
            y: row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemePicker);
    assert_eq!(state.theme_studio.picker_selected, 2);

    let interior_x = centered_theme_picker_rel_x_to_screen_x(&state, 3);
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: interior_x,
            y: row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
    assert_ne!(state.theme, initial_theme);
    assert_ne!(state.theme_studio.picker_selected, 2);
}

#[test]
fn centered_overlay_gutter_click_does_not_trigger_theme_studio_action_but_centered_click_still_works(
) {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.terminal_cols = 120;
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 6;

    let row = theme_studio_overlay_row_y(&state, 0);
    let cols = resolved_cols(state.ui.terminal_cols) as usize;
    let gutter_x = centered_overlay_left_gutter_x(
        state.ui.terminal_cols,
        theme_studio_total_width_for_terminal(cols),
    );

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: gutter_x,
            y: row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(state.theme_studio.selected, 6);

    let interior_x = centered_theme_studio_rel_x_to_screen_x(&state, 3);
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: interior_x,
            y: row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemePicker);
    assert_eq!(state.theme_studio.selected, 0);
}

#[test]
fn settings_overlay_enter_backend_row_keeps_overlay_open() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.settings.menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Backend)
        .expect("backend index");

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
}

#[test]
fn settings_overlay_enter_backend_row_does_not_redraw() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}
    state.ui.overlay_mode = OverlayMode::Settings;
    state.settings.menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Backend)
        .expect("backend index");

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    let rendered = writer_rx
        .try_iter()
        .any(|msg| matches!(msg, WriterMessage::ShowOverlay { .. }));
    assert!(
        !rendered,
        "read-only backend selection should not redraw settings overlay"
    );
}

#[test]
fn settings_overlay_enter_actionable_row_redraws_overlay() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}
    state.ui.overlay_mode = OverlayMode::Settings;
    state.settings.menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Latency)
        .expect("latency index");
    state.config.latency_display = LatencyDisplayMode::Short;
    state.status_state.latency_display = LatencyDisplayMode::Short;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    let rendered = writer_rx
        .try_iter()
        .any(|msg| matches!(msg, WriterMessage::ShowOverlay { .. }));
    assert!(rendered, "actionable row should redraw settings overlay");
}

#[test]
fn settings_overlay_enter_close_row_closes_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.settings.menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Close)
        .expect("close index");

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
}

#[test]
fn settings_overlay_enter_quit_row_stops_event_loop() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.settings.menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Quit)
        .expect("quit index");

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(!running);
}

#[test]
fn settings_overlay_escape_bytes_close_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![0x1b]),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
}

#[test]
fn settings_overlay_arrow_left_and_right_take_different_paths_and_redraw() {
    let (mut left_state, mut left_timers, mut left_deps, left_writer_rx, _left_input_tx) =
        build_harness("cat", &[], 8);
    left_state.ui.overlay_mode = OverlayMode::Settings;
    left_state.config.latency_display = LatencyDisplayMode::Short;
    left_state.status_state.latency_display = LatencyDisplayMode::Short;
    left_state.settings.menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Latency)
        .expect("latency index");
    while left_writer_rx.try_recv().is_ok() {}

    let mut running = true;
    handle_input_event(
        &mut left_state,
        &mut left_timers,
        &mut left_deps,
        InputEvent::Bytes(b"\x1b[D".to_vec()),
        &mut running,
    );
    assert!(running);
    let left_latency = left_state.status_state.latency_display;
    let left_redraw = left_writer_rx
        .try_iter()
        .any(|msg| matches!(msg, WriterMessage::ShowOverlay { .. }));
    assert!(left_redraw, "left-arrow setting changes should redraw");

    let (mut right_state, mut right_timers, mut right_deps, right_writer_rx, _right_input_tx) =
        build_harness("cat", &[], 8);
    right_state.ui.overlay_mode = OverlayMode::Settings;
    right_state.config.latency_display = LatencyDisplayMode::Short;
    right_state.status_state.latency_display = LatencyDisplayMode::Short;
    right_state.settings.menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Latency)
        .expect("latency index");
    while right_writer_rx.try_recv().is_ok() {}

    let mut running = true;
    handle_input_event(
        &mut right_state,
        &mut right_timers,
        &mut right_deps,
        InputEvent::Bytes(b"\x1b[C".to_vec()),
        &mut running,
    );
    assert!(running);
    let right_latency = right_state.status_state.latency_display;
    let right_redraw = right_writer_rx
        .try_iter()
        .any(|msg| matches!(msg, WriterMessage::ShowOverlay { .. }));
    assert!(right_redraw, "right-arrow setting changes should redraw");
    assert_ne!(left_latency, right_latency);
}
