//! Input event handling extracted from the core event loop.

use super::*;

pub(super) fn handle_input_event(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    evt: InputEvent,
    running: &mut bool,
) {
    let mut pending_event = Some(evt);
    while let Some(current_event) = pending_event.take() {
        if state.overlay_mode != OverlayMode::None {
            let overlay_before = state.overlay_mode;
            let replay = handle_overlay_input_event(state, timers, deps, current_event, running);
            pending_event = if replay.is_some() && state.overlay_mode == overlay_before {
                // Prevent replay loops if an overlay handler returns an event
                // without actually transitioning out of overlay mode.
                None
            } else {
                replay
            };
            continue;
        }

        match current_event {
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
            InputEvent::CollapseHiddenLauncher => {
                if state.status_state.hud_style == crate::config::HudStyle::Hidden {
                    state.status_state.hidden_launcher_collapsed = true;
                    state.status_state.hud_button_focus = None;
                    send_enhanced_status_with_buttons(
                        &deps.writer_tx,
                        &deps.button_registry,
                        &state.status_state,
                        state.overlay_mode,
                        state.terminal_cols,
                        state.theme,
                    );
                }
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
                handle_voice_trigger(state, timers, deps, VoiceTriggerOrigin::ManualHotkey);
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
                if should_finalize_insert_capture_hotkey(state) {
                    let _ = request_early_finalize_capture(state, timers, deps);
                    return;
                }
                if should_consume_insert_send_hotkey(state) {
                    if state.status_state.recording_state == RecordingState::Idle
                        && !state.status_state.insert_pending_send
                    {
                        set_status(
                            &deps.writer_tx,
                            &mut timers.status_clear_deadline,
                            &mut state.current_status,
                            &mut state.status_state,
                            "Nothing to send",
                            Some(Duration::from_secs(2)),
                        );
                    }
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
                    if action != ButtonAction::ToggleAutoVoice {
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
                    // Enter should submit terminal input even if a stale HUD focus highlight
                    // is sitting on the auto-voice button.
                    send_enhanced_status_with_buttons(
                        &deps.writer_tx,
                        &deps.button_registry,
                        &state.status_state,
                        state.overlay_mode,
                        state.terminal_cols,
                        state.theme,
                    );
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
                    send_enhanced_status_with_buttons(
                        &deps.writer_tx,
                        &deps.button_registry,
                        &state.status_state,
                        state.overlay_mode,
                        state.terminal_cols,
                        state.theme,
                    );
                }
            }
        }
    }
}

pub(super) fn handle_wake_word_detection(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    if !state.config.wake_word || state.overlay_mode != OverlayMode::None {
        return;
    }
    handle_voice_trigger(state, timers, deps, VoiceTriggerOrigin::WakeWord);
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum VoiceTriggerOrigin {
    ManualHotkey,
    WakeWord,
}

fn handle_voice_trigger(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    origin: VoiceTriggerOrigin,
) {
    if state.status_state.recording_state == RecordingState::Recording {
        if origin == VoiceTriggerOrigin::ManualHotkey {
            let _ = stop_active_capture(state, timers, deps);
        }
        return;
    }
    start_capture_for_trigger(state, timers, deps, origin);
}

fn start_capture_for_trigger(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    origin: VoiceTriggerOrigin,
) {
    let trigger = if state.auto_voice_enabled {
        VoiceCaptureTrigger::Auto
    } else {
        VoiceCaptureTrigger::Manual
    };
    if let Err(err) = start_voice_capture_with_hook(
        &mut deps.voice_manager,
        trigger,
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
            &crate::status_messages::with_log_path("Voice capture failed"),
            Some(Duration::from_secs(2)),
        );
        log_debug(&format!("voice capture failed: {err:#}"));
        return;
    }
    if origin == VoiceTriggerOrigin::WakeWord {
        log_wake_capture_started();
    }
    timers.recording_started_at = Some(Instant::now());
    state.force_send_on_next_transcript = false;
    reset_capture_visuals(
        &mut state.status_state,
        &mut timers.preview_clear_deadline,
        &mut timers.last_meter_update,
    );
}

fn should_send_staged_text_hotkey(state: &EventLoopState) -> bool {
    state.config.voice_send_mode == VoiceSendMode::Insert && state.status_state.insert_pending_send
}

fn should_finalize_insert_capture_hotkey(state: &EventLoopState) -> bool {
    state.config.voice_send_mode == VoiceSendMode::Insert
        && state.status_state.recording_state == RecordingState::Recording
        && !state.status_state.insert_pending_send
}

fn should_consume_insert_send_hotkey(state: &EventLoopState) -> bool {
    state.config.voice_send_mode == VoiceSendMode::Insert
}

fn request_early_finalize_capture(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) -> bool {
    if !request_early_stop_with_hook(&mut deps.voice_manager) {
        return false;
    }
    state.force_send_on_next_transcript = true;
    state.status_state.recording_state = RecordingState::Processing;
    set_status(
        &deps.writer_tx,
        &mut timers.status_clear_deadline,
        &mut state.current_status,
        &mut state.status_state,
        "Finalizing capture...",
        Some(Duration::from_secs(2)),
    );
    true
}

fn stop_active_capture(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) -> bool {
    if !cancel_capture_with_hook(&mut deps.voice_manager) {
        return false;
    }
    state.force_send_on_next_transcript = false;
    state.status_state.recording_state = RecordingState::Idle;
    clear_capture_metrics(&mut state.status_state);
    timers.recording_started_at = None;
    set_status(
        &deps.writer_tx,
        &mut timers.status_clear_deadline,
        &mut state.current_status,
        &mut state.status_state,
        "Capture stopped",
        Some(Duration::from_secs(2)),
    );
    true
}

fn handle_overlay_input_event(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    evt: InputEvent,
    running: &mut bool,
) -> Option<InputEvent> {
    match (state.overlay_mode, evt) {
        (_, InputEvent::Exit) => {
            *running = false;
            None
        }
        (_, InputEvent::MouseClick { x, y }) => {
            handle_overlay_mouse_click(state, timers, deps, running, x, y);
            None
        }
        (mode, InputEvent::ToggleHudStyle) => {
            run_settings_action(state, timers, deps, mode, |settings_ctx| {
                settings_ctx.cycle_hud_style(1);
            });
            if mode == OverlayMode::Settings {
                render_settings_overlay_for_state(state, deps);
            }
            None
        }
        (_, InputEvent::CollapseHiddenLauncher) => None,
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
            None
        }
        (OverlayMode::Settings, InputEvent::SettingsToggle) => {
            close_overlay(state, deps, true);
            None
        }
        (OverlayMode::Settings, InputEvent::HelpToggle) => {
            open_help_overlay(state, deps);
            None
        }
        (OverlayMode::Settings, InputEvent::ThemePicker) => {
            open_theme_picker_overlay(state, timers, deps);
            None
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
            None
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
            None
        }
        (OverlayMode::Help, InputEvent::HelpToggle) => {
            close_overlay(state, deps, false);
            None
        }
        (OverlayMode::Help, InputEvent::SettingsToggle) => {
            open_settings_overlay(state, deps);
            None
        }
        (OverlayMode::Help, InputEvent::ThemePicker) => {
            open_theme_picker_overlay(state, timers, deps);
            None
        }
        (OverlayMode::ThemePicker, InputEvent::HelpToggle) => {
            open_help_overlay(state, deps);
            None
        }
        (OverlayMode::ThemePicker, InputEvent::SettingsToggle) => {
            open_settings_overlay(state, deps);
            None
        }
        (OverlayMode::ThemePicker, InputEvent::ThemePicker) => {
            close_overlay(state, deps, false);
            reset_theme_picker_digits(state, timers);
            None
        }
        (OverlayMode::ThemePicker, InputEvent::EnterKey) => {
            apply_theme_picker_selection(state, timers, deps, state.theme_picker_selected);
            reset_theme_picker_digits(state, timers);
            None
        }
        (OverlayMode::ThemePicker, InputEvent::Bytes(bytes)) => {
            if bytes == [0x1b] {
                close_overlay(state, deps, false);
                reset_theme_picker_digits(state, timers);
            } else if let Some(locked_theme) = style_pack_theme_lock() {
                state.theme_picker_selected = theme_index_from_theme(locked_theme);
                reset_theme_picker_digits(state, timers);
                render_theme_picker_overlay_for_state(state, deps);
            } else if let Some(keys) = parse_arrow_keys_only(&bytes) {
                let mut moved = false;
                let total = THEME_OPTIONS.len();
                for key in keys {
                    let direction = match key {
                        ArrowKey::Up | ArrowKey::Left => -1,
                        ArrowKey::Down | ArrowKey::Right => 1,
                    };
                    if direction != 0 && total > 0 {
                        let total_i64 = i64::try_from(total).unwrap_or(1);
                        let selected_i64 = i64::try_from(state.theme_picker_selected).unwrap_or(0);
                        let next_i64 = (selected_i64 + i64::from(direction)).rem_euclid(total_i64);
                        let next = usize::try_from(next_i64).unwrap_or(0);
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
            None
        }
        (_, replay_evt) => {
            close_overlay(state, deps, true);
            if should_replay_after_overlay_close(&replay_evt) {
                Some(replay_evt)
            } else {
                None
            }
        }
    }
}

fn should_replay_after_overlay_close(evt: &InputEvent) -> bool {
    !matches!(evt, InputEvent::Exit | InputEvent::MouseClick { .. })
}

fn handle_overlay_mouse_click(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    running: &mut bool,
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
            help_overlay_footer(&state.theme.colors()),
        ),
        OverlayMode::ThemePicker => (
            theme_picker_total_width_for_terminal(cols),
            theme_picker_inner_width_for_terminal(cols),
            theme_picker_footer(&state.theme.colors(), style_pack_theme_lock()),
        ),
        OverlayMode::Settings => (
            settings_overlay_width_for_terminal(cols),
            settings_overlay_inner_width_for_terminal(cols),
            settings_overlay_footer(&state.theme.colors()),
        ),
        OverlayMode::None => (0, 0, String::new()),
    };

    if overlay_width == 0 {
        return;
    }
    let centered_overlay_left = cols.saturating_sub(overlay_width) / 2 + 1;
    let centered_overlay_right = centered_overlay_left.saturating_add(overlay_width);
    let centered_hit =
        (x as usize) >= centered_overlay_left && (x as usize) < centered_overlay_right;
    let left_aligned_hit = (x as usize) >= 1 && (x as usize) <= overlay_width;
    if !centered_hit && !left_aligned_hit {
        return;
    }
    let rel_x = if centered_hit {
        (x as usize)
            .saturating_sub(centered_overlay_left)
            .saturating_add(1)
    } else {
        x as usize
    };

    let footer_row = overlay_height.saturating_sub(1);
    if overlay_row == footer_row {
        let title_len = crate::overlay_frame::display_width(&footer_title);
        let left_pad = inner_width.saturating_sub(title_len) / 2;
        let close_prefix = footer_close_prefix(&footer_title);
        let close_len = crate::overlay_frame::display_width(close_prefix);
        let close_start = 2usize.saturating_add(left_pad);
        let close_end = close_start.saturating_add(close_len.saturating_sub(1));
        if rel_x >= close_start && rel_x <= close_end {
            close_overlay(state, deps, true);
        }
        return;
    }

    if state.overlay_mode == OverlayMode::ThemePicker {
        let options_start = THEME_PICKER_OPTION_START_ROW;
        let options_end = options_start.saturating_add(THEME_OPTIONS.len().saturating_sub(1));
        if overlay_row >= options_start
            && overlay_row <= options_end
            && rel_x > 1
            && rel_x < overlay_width
        {
            let idx = overlay_row.saturating_sub(options_start);
            apply_theme_picker_selection(state, timers, deps, idx);
        }
        return;
    }

    if state.overlay_mode == OverlayMode::Settings {
        let options_start = SETTINGS_OPTION_START_ROW;
        let options_end = options_start.saturating_add(SETTINGS_ITEMS.len().saturating_sub(1));
        if overlay_row < options_start
            || overlay_row > options_end
            || rel_x <= 1
            || rel_x >= overlay_width
        {
            return;
        }

        let selected_idx = overlay_row.saturating_sub(options_start);
        state.settings_menu.selected = selected_idx.min(SETTINGS_ITEMS.len().saturating_sub(1));

        let selected = state.settings_menu.selected_item();
        match selected {
            SettingsItem::Backend | SettingsItem::Pipeline => {}
            SettingsItem::Close => {
                close_overlay(state, deps, false);
                return;
            }
            SettingsItem::Quit => {
                *running = false;
                return;
            }
            _ => {
                let direction = settings_mouse_direction_for_item(state, selected, rel_x);
                let _ = run_settings_item_action(
                    state,
                    timers,
                    deps,
                    selected,
                    direction,
                    state.overlay_mode,
                );
            }
        }

        if state.overlay_mode == OverlayMode::Settings {
            render_settings_overlay_for_state(state, deps);
        }
    }
}

fn footer_close_prefix(footer_title: &str) -> &str {
    let dot_split = footer_title.split('·').next().unwrap_or(footer_title);
    dot_split.split('|').next().unwrap_or(dot_split).trim_end()
}

const SETTINGS_SLIDER_LABEL_WIDTH: usize = 15;
const SETTINGS_SLIDER_WIDTH: usize = 14;
const SETTINGS_SLIDER_START_REL_X: usize = 2 + 1 + 1 + SETTINGS_SLIDER_LABEL_WIDTH + 1;
const SETTINGS_VAD_MIN_DB: f32 = -80.0;
const SETTINGS_VAD_MAX_DB: f32 = -10.0;

fn settings_mouse_direction_for_item(
    state: &EventLoopState,
    selected: SettingsItem,
    rel_x: usize,
) -> i32 {
    match selected {
        SettingsItem::Sensitivity => {
            let knob = slider_knob_index_for_range(
                state.status_state.sensitivity_db,
                SETTINGS_VAD_MIN_DB,
                SETTINGS_VAD_MAX_DB,
                SETTINGS_SLIDER_WIDTH,
            );
            slider_direction_from_click(
                rel_x,
                SETTINGS_SLIDER_START_REL_X,
                SETTINGS_SLIDER_WIDTH,
                knob,
            )
            .unwrap_or(1)
        }
        SettingsItem::WakeSensitivity => {
            let knob = slider_knob_index_for_range(
                state.config.wake_word_sensitivity,
                0.0,
                1.0,
                SETTINGS_SLIDER_WIDTH,
            );
            slider_direction_from_click(
                rel_x,
                SETTINGS_SLIDER_START_REL_X,
                SETTINGS_SLIDER_WIDTH,
                knob,
            )
            .unwrap_or(1)
        }
        _ => 1,
    }
}

fn slider_direction_from_click(
    rel_x: usize,
    slider_start: usize,
    slider_width: usize,
    knob_index: usize,
) -> Option<i32> {
    if slider_width == 0 {
        return None;
    }
    let slider_end = slider_start.saturating_add(slider_width.saturating_sub(1));
    if rel_x < slider_start || rel_x > slider_end {
        return None;
    }
    let knob_x = slider_start.saturating_add(knob_index.min(slider_width.saturating_sub(1)));
    if rel_x < knob_x {
        Some(-1)
    } else if rel_x > knob_x {
        Some(1)
    } else {
        Some(0)
    }
}

fn slider_knob_index_for_range(value: f32, min: f32, max: f32, width: usize) -> usize {
    if width <= 1 {
        return 0;
    }
    let clamped = value.clamp(min, max);
    let ratio = if (max - min).abs() < f32::EPSILON {
        0.0
    } else {
        (clamped - min) / (max - min)
    };
    ((width.saturating_sub(1)) as f32 * ratio).round() as usize
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
    } else if state.overlay_mode == OverlayMode::ThemePicker {
        if let Some(locked_theme) = style_pack_theme_lock() {
            state.theme_picker_selected = theme_index_from_theme(locked_theme);
        }
        render_theme_picker_overlay_for_state(state, deps);
    }
}

#[cfg(test)]
mod tests {
    use super::{
        footer_close_prefix, should_replay_after_overlay_close, slider_direction_from_click,
        slider_knob_index_for_range, SETTINGS_SLIDER_START_REL_X, SETTINGS_VAD_MAX_DB,
    };
    use crate::input::InputEvent;

    #[test]
    fn footer_close_prefix_extracts_close_label_before_dot_and_pipe() {
        let footer = "[x] close | up/down move | Enter select · Click/Tap select";
        assert_eq!(footer_close_prefix(footer), "[x] close");
    }

    #[test]
    fn footer_close_prefix_falls_back_when_separators_are_missing() {
        assert_eq!(footer_close_prefix("close only"), "close only");
    }

    #[test]
    fn should_replay_after_overlay_close_filters_exit_and_mouse_events() {
        assert!(!should_replay_after_overlay_close(&InputEvent::Exit));
        assert!(!should_replay_after_overlay_close(
            &InputEvent::MouseClick { x: 1, y: 1 }
        ));
        assert!(should_replay_after_overlay_close(&InputEvent::EnterKey));
    }

    #[test]
    fn slider_constants_match_expected_overlay_geometry() {
        assert_eq!(SETTINGS_SLIDER_START_REL_X, 20);
        assert_eq!(SETTINGS_VAD_MAX_DB, -10.0);
    }

    #[test]
    fn slider_direction_handles_empty_and_out_of_range_clicks() {
        assert_eq!(slider_direction_from_click(3, 3, 0, 0), None);
        assert_eq!(slider_direction_from_click(2, 3, 5, 0), None);
        assert_eq!(slider_direction_from_click(8, 3, 5, 0), None);
    }

    #[test]
    fn slider_direction_maps_left_right_and_knob_hit() {
        let slider_start = 3;
        let slider_width = 5;
        let knob_index = 2;

        assert_eq!(
            slider_direction_from_click(4, slider_start, slider_width, knob_index),
            Some(-1)
        );
        assert_eq!(
            slider_direction_from_click(5, slider_start, slider_width, knob_index),
            Some(0)
        );
        assert_eq!(
            slider_direction_from_click(6, slider_start, slider_width, knob_index),
            Some(1)
        );
    }

    #[test]
    fn slider_knob_index_uses_zero_when_width_is_one_or_less() {
        assert_eq!(slider_knob_index_for_range(10.0, 0.0, 100.0, 0), 0);
        assert_eq!(slider_knob_index_for_range(10.0, 0.0, 100.0, 1), 0);
    }

    #[test]
    fn slider_knob_index_uses_epsilon_guard_for_near_zero_span() {
        let min = 0.0;
        let almost_equal = f32::EPSILON * 0.5;
        let exactly_epsilon = f32::EPSILON;
        let width = 11;

        assert_eq!(
            slider_knob_index_for_range(almost_equal, min, almost_equal, width),
            0
        );
        assert_eq!(
            slider_knob_index_for_range(exactly_epsilon, min, exactly_epsilon, width),
            width - 1
        );
    }

    #[test]
    fn slider_knob_index_scales_linearly_across_range() {
        let width = 11;
        assert_eq!(slider_knob_index_for_range(-1.0, -1.0, 1.0, width), 0);
        assert_eq!(slider_knob_index_for_range(0.0, -1.0, 1.0, width), 5);
        assert_eq!(
            slider_knob_index_for_range(1.0, -1.0, 1.0, width),
            width - 1
        );
    }

    #[test]
    fn slider_knob_index_clamps_outside_range() {
        let width = 11;
        assert_eq!(slider_knob_index_for_range(-10.0, 0.0, 100.0, width), 0);
        assert_eq!(
            slider_knob_index_for_range(1000.0, 0.0, 100.0, width),
            width - 1
        );
    }
}
