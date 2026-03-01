//! Overlay-mode input handling extracted from input dispatch.

use super::*;
use crate::transcript_history::transcript_history_visible_rows;

mod overlay_mouse;
mod theme_studio_cycles;
mod theme_studio_input;

use self::theme_studio_cycles::{
    cycle_runtime_banner_style_override, cycle_runtime_border_style_override,
    cycle_runtime_glyph_set_override, cycle_runtime_indicator_set_override,
    cycle_runtime_progress_bar_family_override, cycle_runtime_progress_style_override,
    cycle_runtime_startup_style_override, cycle_runtime_toast_position_override,
    cycle_runtime_toast_severity_mode_override, cycle_runtime_voice_scene_style_override,
};
use self::theme_studio_input::{handle_theme_studio_bytes, handle_theme_studio_enter_key};

fn dev_panel_index_from_ascii(byte: u8) -> Option<usize> {
    if !byte.is_ascii_digit() {
        return None;
    }
    let digit = usize::from(byte.saturating_sub(b'0'));
    if digit == 0 {
        return None;
    }
    let index = digit.saturating_sub(1);
    if index < crate::dev_command::DevCommandKind::ALL.len() {
        Some(index)
    } else {
        None
    }
}

pub(super) fn handle_overlay_input_event(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    evt: InputEvent,
    running: &mut bool,
) -> Option<InputEvent> {
    match (state.ui.overlay_mode, evt) {
        (_, InputEvent::Exit) => {
            *running = false;
            None
        }
        (_, InputEvent::MouseClick { x, y }) => {
            overlay_mouse::handle_overlay_mouse_click(state, timers, deps, running, x, y);
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
        (mode, InputEvent::QuickThemeCycle) => {
            run_settings_action(state, timers, deps, mode, |settings_ctx| {
                settings_ctx.cycle_theme(1);
            });
            match mode {
                OverlayMode::DevPanel => {
                    render_dev_panel_overlay_for_state(state, deps);
                }
                OverlayMode::Settings => {
                    render_settings_overlay_for_state(state, deps);
                }
                OverlayMode::ThemePicker => {
                    state.theme_studio.picker_selected = theme_index_from_theme(state.theme);
                    render_theme_picker_overlay_for_state(state, deps);
                }
                OverlayMode::ThemeStudio => {
                    render_theme_studio_overlay_for_state(state, deps);
                }
                OverlayMode::Help => {
                    render_help_overlay_for_state(state, deps);
                }
                OverlayMode::TranscriptHistory => {
                    render_transcript_history_overlay_for_state(state, deps);
                }
                OverlayMode::ToastHistory => {
                    render_toast_history_overlay_for_state(state, deps);
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
            open_theme_studio_overlay(state, deps);
            None
        }
        (OverlayMode::Settings, InputEvent::EnterKey) => {
            let mut should_redraw = false;
            let selected = state.settings.menu.selected_item();
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
                        state.ui.overlay_mode,
                    );
                }
            }
            if state.ui.overlay_mode == OverlayMode::Settings && should_redraw {
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
                            state.settings.menu.move_up();
                            should_redraw = true;
                        }
                        ArrowKey::Down => {
                            state.settings.menu.move_down();
                            should_redraw = true;
                        }
                        ArrowKey::Left => {
                            let selected = state.settings.menu.selected_item();
                            should_redraw |= run_settings_item_action(
                                state,
                                timers,
                                deps,
                                selected,
                                -1,
                                state.ui.overlay_mode,
                            );
                        }
                        ArrowKey::Right => {
                            let selected = state.settings.menu.selected_item();
                            should_redraw |= run_settings_item_action(
                                state,
                                timers,
                                deps,
                                selected,
                                1,
                                state.ui.overlay_mode,
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
            open_theme_studio_overlay(state, deps);
            None
        }
        (OverlayMode::ThemeStudio, InputEvent::HelpToggle) => {
            open_help_overlay(state, deps);
            None
        }
        (OverlayMode::ThemeStudio, InputEvent::SettingsToggle) => {
            open_settings_overlay(state, deps);
            None
        }
        (OverlayMode::ThemeStudio, InputEvent::ThemePicker) => {
            close_overlay(state, deps, false);
            None
        }
        (OverlayMode::DevPanel, InputEvent::DevPanelToggle) => {
            close_overlay(state, deps, false);
            None
        }
        (OverlayMode::DevPanel, InputEvent::HelpToggle) => {
            open_help_overlay(state, deps);
            None
        }
        (OverlayMode::DevPanel, InputEvent::SettingsToggle) => {
            open_settings_overlay(state, deps);
            None
        }
        (OverlayMode::DevPanel, InputEvent::ThemePicker) => {
            open_theme_studio_overlay(state, deps);
            None
        }
        (OverlayMode::DevPanel, InputEvent::EnterKey) => {
            request_selected_dev_panel_command(state, timers, deps);
            if state.ui.overlay_mode == OverlayMode::DevPanel {
                render_dev_panel_overlay_for_state(state, deps);
            }
            None
        }
        (OverlayMode::DevPanel, InputEvent::Bytes(bytes)) => {
            if bytes == [0x1b] {
                close_overlay(state, deps, false);
            } else {
                let mut should_redraw = false;
                if let Some(keys) = parse_arrow_keys_only(&bytes) {
                    for key in keys {
                        let moved = match key {
                            ArrowKey::Up | ArrowKey::Left => move_dev_panel_selection(state, -1),
                            ArrowKey::Down | ArrowKey::Right => move_dev_panel_selection(state, 1),
                        };
                        should_redraw |= moved;
                    }
                } else if bytes.len() == 1 {
                    match bytes[0] {
                        b'0'..=b'9' => {
                            if let Some(index) = dev_panel_index_from_ascii(bytes[0]) {
                                should_redraw |= select_dev_panel_command_by_index(state, index);
                            }
                        }
                        b'r' | b'R' => {
                            request_selected_dev_panel_command(state, timers, deps);
                            should_redraw = true;
                        }
                        b'x' | b'X' => {
                            cancel_running_dev_panel_command(state, timers, deps);
                            should_redraw = true;
                        }
                        _ => {}
                    }
                }

                if should_redraw && state.ui.overlay_mode == OverlayMode::DevPanel {
                    render_dev_panel_overlay_for_state(state, deps);
                }
            }
            None
        }
        (OverlayMode::ThemeStudio, InputEvent::EnterKey) => {
            handle_theme_studio_enter_key(state, timers, deps, running);
            None
        }
        (OverlayMode::ThemeStudio, InputEvent::Bytes(bytes)) => {
            handle_theme_studio_bytes(state, timers, deps, &bytes);
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
            open_theme_studio_overlay(state, deps);
            reset_theme_picker_digits(state, timers);
            None
        }
        (OverlayMode::ThemePicker, InputEvent::EnterKey) => {
            apply_theme_picker_selection(state, timers, deps, state.theme_studio.picker_selected);
            reset_theme_picker_digits(state, timers);
            None
        }
        (OverlayMode::ThemePicker, InputEvent::Bytes(bytes)) => {
            if bytes == [0x1b] {
                close_overlay(state, deps, false);
                reset_theme_picker_digits(state, timers);
            } else if let Some(locked_theme) = style_pack_theme_lock() {
                state.theme_studio.picker_selected = theme_index_from_theme(locked_theme);
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
                        let selected_i64 =
                            i64::try_from(state.theme_studio.picker_selected).unwrap_or(0);
                        let next_i64 = (selected_i64 + i64::from(direction)).rem_euclid(total_i64);
                        let next = usize::try_from(next_i64).unwrap_or(0);
                        if next != state.theme_studio.picker_selected {
                            state.theme_studio.picker_selected = next;
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
                    state.theme_studio.picker_digits.push_str(&digits);
                    if state.theme_studio.picker_digits.len() > 3 {
                        reset_theme_picker_digits(state, timers);
                    }
                    let now = Instant::now();
                    timers.theme_picker_digit_deadline =
                        Some(now + Duration::from_millis(THEME_PICKER_NUMERIC_TIMEOUT_MS));
                    if let Some(idx) = theme_picker_parse_index(
                        &state.theme_studio.picker_digits,
                        THEME_OPTIONS.len(),
                    ) {
                        if !theme_picker_has_longer_match(
                            &state.theme_studio.picker_digits,
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
        // --- Transcript History overlay ---
        (OverlayMode::TranscriptHistory, InputEvent::TranscriptHistoryToggle) => {
            close_overlay(state, deps, false);
            None
        }
        (OverlayMode::TranscriptHistory, InputEvent::HelpToggle) => {
            open_help_overlay(state, deps);
            None
        }
        (OverlayMode::TranscriptHistory, InputEvent::SettingsToggle) => {
            open_settings_overlay(state, deps);
            None
        }
        (OverlayMode::TranscriptHistory, InputEvent::ThemePicker) => {
            open_theme_studio_overlay(state, deps);
            None
        }
        (OverlayMode::TranscriptHistory, InputEvent::EnterKey) => {
            // Replay the selected transcript
            if let Some(entry_idx) = state.transcript_history_state.selected_entry_index() {
                if let Some(entry) = state.transcript_history.get(entry_idx) {
                    if !entry.replayable() {
                        set_status(
                            &deps.writer_tx,
                            &mut timers.status_clear_deadline,
                            &mut state.current_status,
                            &mut state.status_state,
                            "Selected entry is output-only (not replayable)",
                            Some(Duration::from_secs(2)),
                        );
                        return None;
                    }
                    let text = entry.text.clone();
                    close_overlay(state, deps, true);
                    if !write_or_queue_pty_input(state, deps, text.into_bytes()) {
                        *running = false;
                    }
                }
            }
            None
        }
        (OverlayMode::TranscriptHistory, InputEvent::Bytes(bytes)) => {
            if bytes == [0x1b] {
                close_overlay(state, deps, false);
            } else if bytes == [0x7f] {
                // Backspace/Delete: remove last search char
                state
                    .transcript_history_state
                    .pop_search_char(&state.transcript_history);
                render_transcript_history_overlay_for_state(state, deps);
            } else {
                let mut should_redraw = false;
                let arrow_keys = parse_arrow_keys(&bytes);
                if !arrow_keys.is_empty() {
                    let visible = transcript_history_visible_rows();
                    for key in arrow_keys {
                        match key {
                            ArrowKey::Up => {
                                state.transcript_history_state.move_up();
                                should_redraw = true;
                            }
                            ArrowKey::Down => {
                                state.transcript_history_state.move_down();
                                should_redraw = true;
                            }
                            ArrowKey::Left | ArrowKey::Right => {}
                        }
                    }
                    if should_redraw {
                        state.transcript_history_state.clamp_scroll(visible);
                        render_transcript_history_overlay_for_state(state, deps);
                    }
                } else {
                    // Type-to-search: append printable user text, ignoring escape/control noise.
                    if let Some(fragment) = transcript_history_search_fragment(&bytes) {
                        for ch in fragment.chars() {
                            state
                                .transcript_history_state
                                .push_search_char(ch, &state.transcript_history);
                            should_redraw = true;
                        }
                    }
                    if should_redraw {
                        render_transcript_history_overlay_for_state(state, deps);
                    }
                }
            }
            None
        }
        // --- Toast History overlay ---
        (OverlayMode::ToastHistory, InputEvent::Bytes(bytes)) => {
            if bytes == [0x1b] {
                close_overlay(state, deps, false);
            }
            // Arrow keys and other input are ignored in toast history (read-only).
            None
        }
        (OverlayMode::ToastHistory, InputEvent::ToastHistoryToggle) => {
            close_overlay(state, deps, false);
            None
        }
        (OverlayMode::ToastHistory, InputEvent::HelpToggle) => {
            open_help_overlay(state, deps);
            None
        }
        (OverlayMode::ToastHistory, InputEvent::SettingsToggle) => {
            open_settings_overlay(state, deps);
            None
        }
        (OverlayMode::ToastHistory, InputEvent::ThemePicker) => {
            open_theme_studio_overlay(state, deps);
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
    !matches!(
        evt,
        InputEvent::Exit | InputEvent::MouseClick { .. } | InputEvent::TranscriptHistoryToggle
    )
}

fn transcript_history_search_fragment(bytes: &[u8]) -> Option<String> {
    if bytes.is_empty() || bytes.contains(&0x1b) {
        return None;
    }

    let mut out = String::new();
    for ch in String::from_utf8_lossy(bytes).chars() {
        if ch.is_control() {
            continue;
        }
        out.push(ch);
    }
    if out.is_empty() {
        None
    } else {
        Some(out)
    }
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
        &mut state.ui.terminal_rows,
        &mut state.ui.terminal_cols,
        &mut state.ui.overlay_mode,
    ) {
        state.theme_studio.picker_selected = theme_index_from_theme(state.theme);
        refresh_button_registry_if_mouse(state, deps);
        save_persistent_config(state);
    } else if state.ui.overlay_mode == OverlayMode::ThemePicker {
        if let Some(locked_theme) = style_pack_theme_lock() {
            state.theme_studio.picker_selected = theme_index_from_theme(locked_theme);
        }
        render_theme_picker_overlay_for_state(state, deps);
    }
}

#[cfg(test)]
mod tests {
    use super::should_replay_after_overlay_close;
    use crate::input::InputEvent;

    #[test]
    fn should_replay_after_overlay_close_filters_exit_and_mouse_events() {
        assert!(!should_replay_after_overlay_close(&InputEvent::Exit));
        assert!(!should_replay_after_overlay_close(
            &InputEvent::MouseClick { x: 1, y: 1 }
        ));
        assert!(should_replay_after_overlay_close(&InputEvent::EnterKey));
    }
}
