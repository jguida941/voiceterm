//! Input event handling extracted from the core event loop.

use super::*;

pub(super) fn handle_input_event(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    evt: InputEvent,
    running: &mut bool,
) {
    if state.overlay_mode != OverlayMode::None {
        handle_overlay_input_event(state, timers, deps, evt, running);
        return;
    }

    match evt {
        InputEvent::HelpToggle => {
            state.status_state.hud_button_focus = None;
            open_help_overlay(state, deps);
        }
        InputEvent::ThemePicker => {
            state.status_state.hud_button_focus = None;
            open_theme_picker_overlay(state, timers, deps);
        }
        InputEvent::QuickThemeCycle => {
            let overlay_mode = state.overlay_mode;
            run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                settings_ctx.cycle_theme(1);
            });
            state.status_state.hud_button_focus = None;
            refresh_button_registry_if_mouse(state, deps);
        }
        InputEvent::SettingsToggle => {
            state.status_state.hud_button_focus = None;
            open_settings_overlay(state, deps);
        }
        InputEvent::ToggleHudStyle => {
            let overlay_mode = state.overlay_mode;
            run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                settings_ctx.cycle_hud_style(1);
            });
            state.status_state.hud_button_focus = None;
            refresh_button_registry_if_mouse(state, deps);
        }
        InputEvent::Bytes(bytes) => {
            if state.suppress_startup_escape_input && is_arrow_escape_noise(&bytes) {
                return;
            }
            if let Some(keys) = parse_arrow_keys_only(&bytes) {
                let mut moved = false;
                for key in keys {
                    let direction = match key {
                        ArrowKey::Left => -1,
                        ArrowKey::Right => 1,
                        _ => 0,
                    };
                    if direction != 0
                        && advance_hud_button_focus(
                            &mut state.status_state,
                            state.overlay_mode,
                            state.terminal_cols,
                            state.theme,
                            direction,
                        )
                    {
                        moved = true;
                    }
                }
                if moved {
                    send_enhanced_status_with_buttons(
                        &deps.writer_tx,
                        &deps.button_registry,
                        &state.status_state,
                        state.overlay_mode,
                        state.terminal_cols,
                        state.theme,
                    );
                    return;
                }
            }

            state.status_state.hud_button_focus = None;
            let mark_insert_pending =
                state.config.voice_send_mode == VoiceSendMode::Insert && !bytes.is_empty();
            if !write_or_queue_pty_input(state, deps, bytes) {
                *running = false;
            } else if mark_insert_pending {
                state.status_state.insert_pending_send = true;
            }
        }
        InputEvent::VoiceTrigger => {
            if state.status_state.recording_state == RecordingState::Recording {
                let _ = stop_or_cancel_capture_for_enter(state, timers, deps);
            } else if let Err(err) = start_voice_capture(
                &mut deps.voice_manager,
                VoiceCaptureTrigger::Manual,
                &deps.writer_tx,
                &mut timers.status_clear_deadline,
                &mut state.current_status,
                &mut state.status_state,
            ) {
                set_status(
                    &deps.writer_tx,
                    &mut timers.status_clear_deadline,
                    &mut state.current_status,
                    &mut state.status_state,
                    "Voice capture failed (see log)",
                    Some(Duration::from_secs(2)),
                );
                log_debug(&format!("voice capture failed: {err:#}"));
            } else {
                timers.recording_started_at = Some(Instant::now());
                reset_capture_visuals(
                    &mut state.status_state,
                    &mut timers.preview_clear_deadline,
                    &mut timers.last_meter_update,
                );
            }
        }
        InputEvent::SendStagedText => {
            if should_send_staged_text_hotkey(state) {
                if !write_or_queue_pty_input(state, deps, vec![0x0d]) {
                    *running = false;
                } else {
                    timers.last_enter_at = Some(Instant::now());
                    state.status_state.insert_pending_send = false;
                }
                return;
            }
            if should_ignore_send_staged_text_hotkey(state) {
                return;
            }
            if !write_or_queue_pty_input(state, deps, vec![0x05]) {
                *running = false;
            }
        }
        InputEvent::ToggleAutoVoice => {
            let overlay_mode = state.overlay_mode;
            run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                settings_ctx.toggle_auto_voice();
            });
            refresh_button_registry_if_mouse(state, deps);
        }
        InputEvent::ToggleSendMode => {
            let overlay_mode = state.overlay_mode;
            run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                settings_ctx.toggle_send_mode();
            });
            refresh_button_registry_if_mouse(state, deps);
        }
        InputEvent::IncreaseSensitivity => {
            let overlay_mode = state.overlay_mode;
            run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                settings_ctx.adjust_sensitivity(5.0);
            });
        }
        InputEvent::DecreaseSensitivity => {
            let overlay_mode = state.overlay_mode;
            run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
                settings_ctx.adjust_sensitivity(-5.0);
            });
        }
        InputEvent::EnterKey => {
            if let Some(action) = state.status_state.hud_button_focus {
                state.status_state.hud_button_focus = None;
                if action == ButtonAction::ThemePicker {
                    reset_theme_picker_selection(state, timers);
                }
                {
                    let mut button_ctx = button_action_context(state, timers, deps);
                    button_ctx.handle_action(action);
                }
                send_enhanced_status_with_buttons(
                    &deps.writer_tx,
                    &deps.button_registry,
                    &state.status_state,
                    state.overlay_mode,
                    state.terminal_cols,
                    state.theme,
                );
                return;
            }
            if !write_or_queue_pty_input(state, deps, vec![0x0d]) {
                *running = false;
            } else {
                timers.last_enter_at = Some(Instant::now());
                state.status_state.insert_pending_send = false;
            }
        }
        InputEvent::Exit => {
            *running = false;
        }
        InputEvent::MouseClick { x, y } => {
            if !state.status_state.mouse_enabled {
                return;
            }

            if let Some(action) = deps.button_registry.find_at(x, y, state.terminal_rows) {
                if action == ButtonAction::ThemePicker {
                    reset_theme_picker_selection(state, timers);
                }
                {
                    let mut button_ctx = button_action_context(state, timers, deps);
                    button_ctx.handle_action(action);
                }
                state.status_state.hud_button_focus = None;
            }
        }
    }
}

fn should_send_staged_text_hotkey(state: &EventLoopState) -> bool {
    state.config.voice_send_mode == VoiceSendMode::Insert
        && state.status_state.recording_state == RecordingState::Recording
        && state.status_state.insert_pending_send
}

fn should_ignore_send_staged_text_hotkey(state: &EventLoopState) -> bool {
    state.config.voice_send_mode == VoiceSendMode::Insert
        && state.status_state.recording_state == RecordingState::Recording
        && !state.status_state.insert_pending_send
}

fn stop_or_cancel_capture_for_enter(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) -> bool {
    if deps.voice_manager.active_source() == Some(VoiceCaptureSource::Python) {
        if !deps.voice_manager.cancel_capture() {
            return false;
        }
        state.status_state.recording_state = RecordingState::Idle;
        clear_capture_metrics(&mut state.status_state);
        timers.recording_started_at = None;
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            "Capture cancelled (python fallback cannot stop early)",
            Some(Duration::from_secs(3)),
        );
        true
    } else {
        if !deps.voice_manager.request_early_stop() {
            return false;
        }
        state.status_state.recording_state = RecordingState::Processing;
        clear_capture_metrics(&mut state.status_state);
        state.processing_spinner_index = 0;
        timers.last_processing_tick = Instant::now();
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            "Processing",
            None,
        );
        true
    }
}

fn handle_overlay_input_event(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    evt: InputEvent,
    running: &mut bool,
) {
    match (state.overlay_mode, evt) {
        (_, InputEvent::Exit) => *running = false,
        (_, InputEvent::MouseClick { x, y }) => {
            handle_overlay_mouse_click(state, timers, deps, x, y);
        }
        (mode, InputEvent::ToggleHudStyle) => {
            run_settings_action(state, timers, deps, mode, |settings_ctx| {
                settings_ctx.cycle_hud_style(1);
            });
            if mode == OverlayMode::Settings {
                render_settings_overlay_for_state(state, deps);
            }
        }
        (mode, InputEvent::QuickThemeCycle) => {
            run_settings_action(state, timers, deps, mode, |settings_ctx| {
                settings_ctx.cycle_theme(1);
            });
            match mode {
                OverlayMode::Settings => {
                    render_settings_overlay_for_state(state, deps);
                }
                OverlayMode::ThemePicker => {
                    state.theme_picker_selected = theme_index_from_theme(state.theme);
                    render_theme_picker_overlay_for_state(state, deps);
                }
                OverlayMode::Help => {
                    render_help_overlay_for_state(state, deps);
                }
                OverlayMode::None => {}
            }
        }
        (OverlayMode::Settings, InputEvent::SettingsToggle) => {
            close_overlay(state, deps, true);
        }
        (OverlayMode::Settings, InputEvent::HelpToggle) => {
            open_help_overlay(state, deps);
        }
        (OverlayMode::Settings, InputEvent::ThemePicker) => {
            open_theme_picker_overlay(state, timers, deps);
        }
        (OverlayMode::Settings, InputEvent::EnterKey) => {
            let mut should_redraw = false;
            let selected = state.settings_menu.selected_item();
            match selected {
                SettingsItem::Backend | SettingsItem::Pipeline => {}
                SettingsItem::Close => {
                    close_overlay(state, deps, false);
                }
                SettingsItem::Quit => *running = false,
                _ => {
                    should_redraw = run_settings_item_action(
                        state,
                        timers,
                        deps,
                        selected,
                        0,
                        state.overlay_mode,
                    );
                }
            }
            if state.overlay_mode == OverlayMode::Settings && should_redraw {
                render_settings_overlay_for_state(state, deps);
            }
        }
        (OverlayMode::Settings, InputEvent::Bytes(bytes)) => {
            if bytes == [0x1b] {
                close_overlay(state, deps, false);
            } else {
                let mut should_redraw = false;
                for key in parse_arrow_keys(&bytes) {
                    match key {
                        ArrowKey::Up => {
                            state.settings_menu.move_up();
                            should_redraw = true;
                        }
                        ArrowKey::Down => {
                            state.settings_menu.move_down();
                            should_redraw = true;
                        }
                        ArrowKey::Left => {
                            let selected = state.settings_menu.selected_item();
                            should_redraw |= run_settings_item_action(
                                state,
                                timers,
                                deps,
                                selected,
                                -1,
                                state.overlay_mode,
                            );
                        }
                        ArrowKey::Right => {
                            let selected = state.settings_menu.selected_item();
                            should_redraw |= run_settings_item_action(
                                state,
                                timers,
                                deps,
                                selected,
                                1,
                                state.overlay_mode,
                            );
                        }
                    }
                }
                if should_redraw {
                    render_settings_overlay_for_state(state, deps);
                }
            }
        }
        (OverlayMode::Help, InputEvent::HelpToggle) => {
            close_overlay(state, deps, false);
        }
        (OverlayMode::Help, InputEvent::SettingsToggle) => {
            open_settings_overlay(state, deps);
        }
        (OverlayMode::Help, InputEvent::ThemePicker) => {
            open_theme_picker_overlay(state, timers, deps);
        }
        (OverlayMode::ThemePicker, InputEvent::HelpToggle) => {
            open_help_overlay(state, deps);
        }
        (OverlayMode::ThemePicker, InputEvent::SettingsToggle) => {
            open_settings_overlay(state, deps);
        }
        (OverlayMode::ThemePicker, InputEvent::ThemePicker) => {
            close_overlay(state, deps, false);
            reset_theme_picker_digits(state, timers);
        }
        (OverlayMode::ThemePicker, InputEvent::EnterKey) => {
            apply_theme_picker_selection(state, timers, deps, state.theme_picker_selected);
            reset_theme_picker_digits(state, timers);
        }
        (OverlayMode::ThemePicker, InputEvent::Bytes(bytes)) => {
            if bytes == [0x1b] {
                close_overlay(state, deps, false);
                reset_theme_picker_digits(state, timers);
            } else if let Some(keys) = parse_arrow_keys_only(&bytes) {
                let mut moved = false;
                let total = THEME_OPTIONS.len();
                for key in keys {
                    let direction = match key {
                        ArrowKey::Up | ArrowKey::Left => -1,
                        ArrowKey::Down | ArrowKey::Right => 1,
                    };
                    if direction != 0 && total > 0 {
                        let next = (state.theme_picker_selected as i32 + direction)
                            .rem_euclid(total as i32) as usize;
                        if next != state.theme_picker_selected {
                            state.theme_picker_selected = next;
                            moved = true;
                        }
                    }
                }
                if moved {
                    render_theme_picker_overlay_for_state(state, deps);
                }
                reset_theme_picker_digits(state, timers);
            } else {
                let digits: String = bytes
                    .iter()
                    .filter(|b| b.is_ascii_digit())
                    .map(|b| *b as char)
                    .collect();
                if !digits.is_empty() {
                    state.theme_picker_digits.push_str(&digits);
                    if state.theme_picker_digits.len() > 3 {
                        reset_theme_picker_digits(state, timers);
                    }
                    let now = Instant::now();
                    timers.theme_picker_digit_deadline =
                        Some(now + Duration::from_millis(THEME_PICKER_NUMERIC_TIMEOUT_MS));
                    if let Some(idx) =
                        theme_picker_parse_index(&state.theme_picker_digits, THEME_OPTIONS.len())
                    {
                        if !theme_picker_has_longer_match(
                            &state.theme_picker_digits,
                            THEME_OPTIONS.len(),
                        ) {
                            apply_theme_picker_selection(state, timers, deps, idx);
                            reset_theme_picker_digits(state, timers);
                        }
                    }
                }
            }
        }
        (_, _) => {
            close_overlay(state, deps, true);
        }
    }
}

fn handle_overlay_mouse_click(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    x: u16,
    y: u16,
) {
    if !state.status_state.mouse_enabled {
        return;
    }

    let overlay_height = match state.overlay_mode {
        OverlayMode::Help => help_overlay_height(),
        OverlayMode::ThemePicker => theme_picker_height(),
        OverlayMode::Settings => settings_overlay_height(),
        OverlayMode::None => 0,
    };
    if overlay_height == 0 || state.terminal_rows == 0 {
        return;
    }
    let overlay_top_y = state
        .terminal_rows
        .saturating_sub(overlay_height as u16)
        .saturating_add(1);
    if y < overlay_top_y || y > state.terminal_rows {
        return;
    }
    let overlay_row = (y - overlay_top_y) as usize + 1;
    let cols = resolved_cols(state.terminal_cols) as usize;

    let (overlay_width, inner_width, footer_title) = match state.overlay_mode {
        OverlayMode::Help => (
            help_overlay_width_for_terminal(cols),
            help_overlay_inner_width_for_terminal(cols),
            HELP_OVERLAY_FOOTER,
        ),
        OverlayMode::ThemePicker => (
            theme_picker_total_width_for_terminal(cols),
            theme_picker_inner_width_for_terminal(cols),
            THEME_PICKER_FOOTER,
        ),
        OverlayMode::Settings => (
            settings_overlay_width_for_terminal(cols),
            settings_overlay_inner_width_for_terminal(cols),
            SETTINGS_OVERLAY_FOOTER,
        ),
        OverlayMode::None => (0, 0, ""),
    };

    if overlay_width == 0 || x as usize > overlay_width {
        return;
    }

    let footer_row = overlay_height.saturating_sub(1);
    if overlay_row == footer_row {
        let title_len = footer_title.chars().count();
        let left_pad = inner_width.saturating_sub(title_len) / 2;
        let close_prefix = footer_title
            .split('·')
            .next()
            .unwrap_or(footer_title)
            .trim_end();
        let close_len = close_prefix.chars().count();
        let close_start = 2usize.saturating_add(left_pad);
        let close_end = close_start.saturating_add(close_len.saturating_sub(1));
        if (x as usize) >= close_start && (x as usize) <= close_end {
            close_overlay(state, deps, true);
        }
        return;
    }

    if state.overlay_mode == OverlayMode::ThemePicker {
        let options_start = THEME_PICKER_OPTION_START_ROW;
        let options_end = options_start.saturating_add(THEME_OPTIONS.len().saturating_sub(1));
        if overlay_row >= options_start
            && overlay_row <= options_end
            && x > 1
            && (x as usize) < overlay_width
        {
            let idx = overlay_row.saturating_sub(options_start);
            apply_theme_picker_selection(state, timers, deps, idx);
        }
    }
}

fn run_settings_action(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    overlay_mode: OverlayMode,
    apply: impl FnOnce(&mut SettingsActionContext<'_>),
) {
    let mut settings_ctx = settings_action_context(state, timers, deps, overlay_mode);
    apply(&mut settings_ctx);
}

fn run_settings_item_action(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    selected: SettingsItem,
    direction: i32,
    overlay_mode: OverlayMode,
) -> bool {
    let mut did_apply = false;
    run_settings_action(state, timers, deps, overlay_mode, |settings_ctx| {
        did_apply = apply_settings_item_action(selected, direction, settings_ctx);
    });
    did_apply
}

fn apply_theme_picker_selection(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    idx: usize,
) {
    if apply_theme_picker_index(
        idx,
        &mut state.theme,
        &mut state.config,
        &deps.writer_tx,
        &mut timers.status_clear_deadline,
        &mut state.current_status,
        &mut state.status_state,
        &mut deps.session,
        &mut state.terminal_rows,
        &mut state.terminal_cols,
        &mut state.overlay_mode,
    ) {
        state.theme_picker_selected = theme_index_from_theme(state.theme);
        refresh_button_registry_if_mouse(state, deps);
    }
}
