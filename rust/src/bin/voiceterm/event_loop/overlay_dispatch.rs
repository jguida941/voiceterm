//! Overlay transition helpers extracted from the core event loop.

use super::*;

pub(super) fn close_overlay(
    state: &mut EventLoopState,
    deps: &mut EventLoopDeps,
    refresh_buttons: bool,
) {
    state.overlay_mode = OverlayMode::None;
    let _ = deps.writer_tx.send(WriterMessage::ClearOverlay);
    sync_overlay_winsize(state, deps);
    if refresh_buttons {
        refresh_button_registry_if_mouse(state, deps);
    }
}

pub(super) fn open_help_overlay(state: &mut EventLoopState, deps: &mut EventLoopDeps) {
    state.overlay_mode = OverlayMode::Help;
    sync_overlay_winsize(state, deps);
    render_help_overlay_for_state(state, deps);
}

pub(super) fn open_dev_panel_overlay(state: &mut EventLoopState, deps: &mut EventLoopDeps) {
    state.overlay_mode = OverlayMode::DevPanel;
    sync_overlay_winsize(state, deps);
    render_dev_panel_overlay_for_state(state, deps);
}

pub(super) fn open_settings_overlay(state: &mut EventLoopState, deps: &mut EventLoopDeps) {
    state.overlay_mode = OverlayMode::Settings;
    sync_overlay_winsize(state, deps);
    render_settings_overlay_for_state(state, deps);
}

pub(super) fn open_theme_picker_overlay(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    state.overlay_mode = OverlayMode::ThemePicker;
    sync_overlay_winsize(state, deps);
    reset_theme_picker_selection(state, timers);
    render_theme_picker_overlay_for_state(state, deps);
}

pub(super) fn open_theme_studio_overlay(state: &mut EventLoopState, deps: &mut EventLoopDeps) {
    state.overlay_mode = OverlayMode::ThemeStudio;
    reset_theme_studio_selection(state);
    sync_overlay_winsize(state, deps);
    render_theme_studio_overlay_for_state(state, deps);
}

pub(super) fn open_transcript_history_overlay(
    state: &mut EventLoopState,
    deps: &mut EventLoopDeps,
) {
    state.overlay_mode = OverlayMode::TranscriptHistory;
    state.transcript_history.flush_pending_stream_lines();
    state
        .transcript_history_state
        .refresh_filter(&state.transcript_history);
    sync_overlay_winsize(state, deps);
    render_transcript_history_overlay_for_state(state, deps);
}

pub(super) fn open_toast_history_overlay(state: &mut EventLoopState, deps: &mut EventLoopDeps) {
    state.overlay_mode = OverlayMode::ToastHistory;
    sync_overlay_winsize(state, deps);
    render_toast_history_overlay_for_state(state, deps);
}
