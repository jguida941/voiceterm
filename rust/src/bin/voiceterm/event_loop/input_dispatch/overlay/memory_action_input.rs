use super::*;

pub(super) fn handle_memory_browser_overlay_event(
    state: &mut EventLoopState,
    deps: &mut EventLoopDeps,
    running: &mut bool,
    evt: InputEvent,
) -> Option<InputEvent> {
    match evt {
        InputEvent::HelpToggle => {
            open_help_overlay(state, deps);
            None
        }
        InputEvent::SettingsToggle => {
            open_settings_overlay(state, deps);
            None
        }
        InputEvent::ThemePicker => {
            open_theme_studio_overlay(state, deps);
            None
        }
        InputEvent::EnterKey => {
            let events = super::super::overlay_dispatch::memory_browser_events(state);
            if state.memory_browser_state.selected < events.len() {
                let text = events[state.memory_browser_state.selected].text.clone();
                close_overlay(state, deps, true);
                if !write_or_queue_pty_input(state, deps, text.into_bytes()) {
                    *running = false;
                }
            }
            None
        }
        InputEvent::Bytes(bytes) => {
            handle_memory_browser_overlay_bytes(state, deps, &bytes);
            None
        }
        replay_evt => replay_overlay_event(state, deps, replay_evt),
    }
}

fn handle_memory_browser_overlay_bytes(
    state: &mut EventLoopState,
    deps: &mut EventLoopDeps,
    bytes: &[u8],
) {
    if bytes == [0x1b] {
        close_overlay(state, deps, false);
    } else if bytes == [0x7f] {
        state.memory_browser_state.pop_search_char();
        render_memory_browser_overlay_for_state(state, deps);
    } else if bytes == [0x09] {
        state.memory_browser_state.toggle_detail();
        render_memory_browser_overlay_for_state(state, deps);
    } else if matches!(bytes, [b'f'] | [b'F']) {
        state.memory_browser_state.cycle_filter();
        render_memory_browser_overlay_for_state(state, deps);
    } else if matches!(bytes, [b'a'] | [b'A']) {
        open_action_center_overlay(state, deps);
    } else if let Some(keys) = parse_arrow_keys_only(bytes) {
        for key in keys {
            match key {
                ArrowKey::Up | ArrowKey::Left => state.memory_browser_state.move_up(),
                ArrowKey::Down | ArrowKey::Right => state.memory_browser_state.move_down(),
            }
        }
        render_memory_browser_overlay_for_state(state, deps);
    } else if let Some(fragment) = super::transcript_history_search_fragment(bytes) {
        for ch in fragment.chars() {
            state.memory_browser_state.push_search_char(ch);
        }
        render_memory_browser_overlay_for_state(state, deps);
    }
}

pub(super) fn handle_action_center_overlay_event(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    evt: InputEvent,
) -> Option<InputEvent> {
    match evt {
        InputEvent::HelpToggle => {
            open_help_overlay(state, deps);
            None
        }
        InputEvent::SettingsToggle => {
            open_settings_overlay(state, deps);
            None
        }
        InputEvent::ThemePicker => {
            open_theme_studio_overlay(state, deps);
            None
        }
        InputEvent::EnterKey => {
            request_selected_dev_panel_command(state, timers, deps);
            render_action_center_overlay_for_state(state, deps);
            None
        }
        InputEvent::Bytes(bytes) => {
            handle_action_center_overlay_bytes(state, timers, deps, &bytes);
            None
        }
        replay_evt => replay_overlay_event(state, deps, replay_evt),
    }
}

fn handle_action_center_overlay_bytes(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    bytes: &[u8],
) {
    if bytes == [0x1b] {
        close_overlay(state, deps, false);
    } else if matches!(bytes, [b'b'] | [b'B']) {
        open_memory_browser_overlay(state, deps);
    } else if matches!(bytes, [b'p'] | [b'P']) {
        cycle_dev_panel_execution_profile(state, timers, deps);
        render_action_center_overlay_for_state(state, deps);
    } else if matches!(bytes, [b'x'] | [b'X']) {
        cancel_running_dev_panel_command(state, timers, deps);
        render_action_center_overlay_for_state(state, deps);
    } else if let Some(keys) = parse_arrow_keys_only(bytes) {
        let mut should_redraw = false;
        for key in keys {
            should_redraw |= match key {
                ArrowKey::Up | ArrowKey::Left => move_dev_panel_selection(state, -1),
                ArrowKey::Down | ArrowKey::Right => move_dev_panel_selection(state, 1),
            };
        }
        if should_redraw {
            render_action_center_overlay_for_state(state, deps);
        }
    }
}

fn replay_overlay_event(
    state: &mut EventLoopState,
    deps: &mut EventLoopDeps,
    replay_evt: InputEvent,
) -> Option<InputEvent> {
    close_overlay(state, deps, true);
    if super::should_replay_after_overlay_close(&replay_evt) {
        Some(replay_evt)
    } else {
        None
    }
}
