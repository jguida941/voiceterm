use super::*;

#[test]
fn theme_picker_escape_bytes_close_and_clear_digits() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemePicker;
    state.theme_studio.picker_digits = "12".to_string();

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
    assert!(state.theme_studio.picker_digits.is_empty());
}

#[test]
fn theme_picker_arrow_left_and_right_move_selection_in_opposite_directions() {
    let total = THEME_OPTIONS.len();
    assert!(total >= 3, "theme picker should expose multiple options");

    let (mut left_state, mut left_timers, mut left_deps, _left_writer_rx, _left_input_tx) =
        build_harness("cat", &[], 8);
    left_state.ui.overlay_mode = OverlayMode::ThemePicker;
    left_state.theme_studio.picker_selected = 1;
    let mut running = true;
    handle_input_event(
        &mut left_state,
        &mut left_timers,
        &mut left_deps,
        InputEvent::Bytes(b"\x1b[D".to_vec()),
        &mut running,
    );
    assert!(running);
    let left_selected = left_state.theme_studio.picker_selected;

    let (mut right_state, mut right_timers, mut right_deps, _right_writer_rx, _right_input_tx) =
        build_harness("cat", &[], 8);
    right_state.ui.overlay_mode = OverlayMode::ThemePicker;
    right_state.theme_studio.picker_selected = 1;
    let mut running = true;
    handle_input_event(
        &mut right_state,
        &mut right_timers,
        &mut right_deps,
        InputEvent::Bytes(b"\x1b[C".to_vec()),
        &mut running,
    );
    assert!(running);
    let right_selected = right_state.theme_studio.picker_selected;

    assert_ne!(left_selected, right_selected);
    assert_eq!(left_selected, 0);
    assert_eq!(right_selected, 2);
}

#[test]
fn theme_picker_numeric_input_keeps_three_digits_and_clears_after_fourth() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemePicker;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"123".to_vec()),
        &mut running,
    );
    assert!(running);
    assert_eq!(state.theme_studio.picker_digits, "123");

    let before = Instant::now();
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"4".to_vec()),
        &mut running,
    );
    assert!(running);
    assert!(state.theme_studio.picker_digits.is_empty());
    let deadline = timers
        .theme_picker_digit_deadline
        .expect("digit deadline should still be refreshed");
    assert!(
        deadline >= before,
        "digit timeout should not be scheduled in the past"
    );
}

#[test]
fn theme_picker_single_digit_waits_when_longer_match_exists() {
    if THEME_OPTIONS.len() < 10 {
        return;
    }
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemePicker;
    state.theme_studio.picker_selected = 5;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"1".to_vec()),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemePicker);
    assert_eq!(state.theme_studio.picker_selected, 5);
    assert_eq!(state.theme_studio.picker_digits, "1");
}

#[test]
fn overlay_mouse_click_outside_vertical_bounds_is_ignored() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.settings.menu.selected = 0;
    let overlay_top_y = state
        .ui
        .terminal_rows
        .saturating_sub(settings_overlay_height() as u16)
        .saturating_add(1);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: 3,
            y: overlay_top_y.saturating_sub(1),
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.settings.menu.selected, 0);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
}

#[test]
fn overlay_mouse_click_outside_horizontal_bounds_is_ignored() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.settings.menu.selected = 0;
    let row = settings_overlay_row_y(&state, SettingsItem::Latency);
    let click_x = state.ui.terminal_cols;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x: click_x, y: row },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.settings.menu.selected, 0);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
}

#[test]
fn theme_picker_mouse_click_on_border_columns_does_not_select_option() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemePicker;
    state.theme_studio.picker_selected = 2;
    let row = theme_picker_overlay_row_y(&state, 0);
    let left_border_x = centered_theme_picker_rel_x_to_screen_x(&state, 1);
    let cols = resolved_cols(state.ui.terminal_cols) as usize;
    let overlay_width = theme_picker_total_width_for_terminal(cols);
    let right_border_x = centered_theme_picker_rel_x_to_screen_x(&state, overlay_width);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: left_border_x,
            y: row,
        },
        &mut running,
    );
    assert!(running);
    assert_eq!(state.theme_studio.picker_selected, 2);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: right_border_x,
            y: row,
        },
        &mut running,
    );
    assert!(running);
    assert_eq!(state.theme_studio.picker_selected, 2);
}

#[test]
fn theme_studio_mouse_click_on_border_columns_does_not_select_option() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 4;
    let row = theme_studio_overlay_row_y(&state, 0);
    let left_border_x = centered_theme_studio_rel_x_to_screen_x(&state, 1);
    let cols = resolved_cols(state.ui.terminal_cols) as usize;
    let overlay_width = theme_studio_total_width_for_terminal(cols);
    let right_border_x = centered_theme_studio_rel_x_to_screen_x(&state, overlay_width);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: left_border_x,
            y: row,
        },
        &mut running,
    );
    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(state.theme_studio.selected, 4);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: right_border_x,
            y: row,
        },
        &mut running,
    );
    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(state.theme_studio.selected, 4);
}

#[test]
fn theme_studio_mouse_click_on_theme_picker_row_opens_theme_picker_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 6;
    let row = theme_studio_overlay_row_y(&state, 0);
    let interior_x = centered_theme_studio_rel_x_to_screen_x(&state, 3);

    let mut running = true;
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
fn theme_studio_mouse_click_above_option_rows_does_not_activate_selection() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 6;
    let overlay_top_y = state
        .ui
        .terminal_rows
        .saturating_sub(crate::theme_studio::theme_studio_overlay_height() as u16)
        .saturating_add(1);
    let row_above_options = overlay_top_y
        .saturating_add(THEME_STUDIO_OPTION_START_ROW as u16)
        .saturating_sub(2);
    let interior_x = centered_theme_studio_rel_x_to_screen_x(&state, 3);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: interior_x,
            y: row_above_options,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(state.theme_studio.selected, 6);
}

#[test]
fn settings_mouse_click_on_border_columns_does_not_select_option() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.settings.menu.selected = 0;
    let row = settings_overlay_row_y(&state, SettingsItem::Latency);
    let left_border_x = centered_settings_overlay_rel_x_to_screen_x(&state, 1);
    let cols = resolved_cols(state.ui.terminal_cols) as usize;
    let overlay_width = settings_overlay_width_for_terminal(cols);
    let right_border_x = centered_settings_overlay_rel_x_to_screen_x(&state, overlay_width);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: left_border_x,
            y: row,
        },
        &mut running,
    );
    assert!(running);
    assert_eq!(state.settings.menu.selected, 0);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: right_border_x,
            y: row,
        },
        &mut running,
    );
    assert!(running);
    assert_eq!(state.settings.menu.selected, 0);
}

#[test]
fn settings_mouse_click_zero_column_is_ignored() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    state.settings.menu.selected = 0;
    let row = settings_overlay_row_y(&state, SettingsItem::Latency);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x: 0, y: row },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
    assert_eq!(state.settings.menu.selected, 0);
}
