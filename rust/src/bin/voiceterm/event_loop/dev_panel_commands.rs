//! Dev-panel command helpers extracted from the core event loop.
//!
//! Submodules split by concern:
//! - `execution`: command dispatch, auto-send control, polling
//! - `git_snapshot`: git status capture and porcelain parsing
//! - `snapshots`: memory, handoff, and context snapshot builders
//! - `clipboard`: OSC 52 clipboard operations
//! - `review_loader`: review artifact loading and polling

mod clipboard;
mod execution;
mod git_snapshot;
mod ops_snapshot;
mod review_loader;
mod snapshots;
mod snapshots_render;

use super::*;

// Re-export all pub(super) items so callers in `event_loop` see them unchanged.
pub(super) use clipboard::copy_handoff_prompt_to_clipboard;
pub(super) use execution::{
    cancel_running_dev_panel_command, cycle_dev_panel_execution_profile, move_dev_panel_selection,
    poll_dev_command_updates, request_selected_dev_panel_command,
    select_dev_panel_command_by_index,
};
pub(super) use review_loader::{load_review, poll_review};
pub(super) use snapshots::cycle_memory_mode;

#[cfg(test)]
pub(super) use execution::{
    apply_terminal_packet_completion, set_dev_packet_auto_send_runtime_override,
};

fn set_dev_status(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &EventLoopDeps,
    text: &str,
    clear_after: Option<Duration>,
) {
    set_status(
        &deps.writer_tx,
        &mut timers.status_clear_deadline,
        &mut state.current_status,
        &mut state.status_state,
        text,
        clear_after,
    );
}

pub(super) fn toggle_dev_panel_tab(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    state.dev_panel_commands.toggle_tab();
    refresh_active_dev_panel_tab(state, deps, RefreshMode::Lazy);
    let tab_label = state.dev_panel_commands.active_tab().label();
    set_dev_status(state, timers, deps, tab_label, Some(Duration::from_secs(1)));
}

pub(super) fn prev_dev_panel_tab(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    state.dev_panel_commands.prev_tab();
    refresh_active_dev_panel_tab(state, deps, RefreshMode::Lazy);
    let tab_label = state.dev_panel_commands.active_tab().label();
    set_dev_status(state, timers, deps, tab_label, Some(Duration::from_secs(1)));
}

#[derive(Clone, Copy)]
pub(super) enum RefreshMode {
    Lazy,
    Force,
}

/// Reload the review artifact if forced, or if no artifact and no error
/// are cached yet. Shared gate used by both Control and Handoff refresh.
fn maybe_reload_review(
    state: &mut EventLoopState,
    session: &voiceterm::pty_session::PtyOverlaySession,
    force: bool,
) {
    if force
        || (state.dev_panel_commands.review().artifact().is_none()
            && state.dev_panel_commands.review().load_error().is_none())
    {
        review_loader::load_review(state, session);
    }
}

fn refresh_control_snapshot(
    state: &mut EventLoopState,
    deps: &EventLoopDeps,
    force_review_reload: bool,
) {
    maybe_reload_review(state, &deps.session, force_review_reload);
    git_snapshot::refresh_git_snapshot(state, &deps.session);
    snapshots::refresh_memory_snapshot(state);
    snapshots::build_runtime_diagnostics_snapshot(state, deps);
}

fn refresh_handoff_sources(
    state: &mut EventLoopState,
    deps: &EventLoopDeps,
    force_review_reload: bool,
    force_git_reload: bool,
) {
    maybe_reload_review(state, &deps.session, force_review_reload);
    if force_git_reload || state.dev_panel_commands.git_snapshot().is_none() {
        git_snapshot::refresh_git_snapshot(state, &deps.session);
    }
}

/// Refresh the active dev-panel tab from runtime state.
/// `Lazy` keeps already-loaded review/git data when the operator is just
/// cycling tabs. `Force` is used for explicit refresh/reopen paths so the
/// rendered footer never promises freshness while still showing cached data.
pub(super) fn refresh_active_dev_panel_tab(
    state: &mut EventLoopState,
    deps: &EventLoopDeps,
    mode: RefreshMode,
) {
    match state.dev_panel_commands.active_tab() {
        crate::dev_command::DevPanelTab::Review => {
            if matches!(mode, RefreshMode::Force) {
                review_loader::load_review(state, &deps.session);
            } else {
                maybe_reload_review(state, &deps.session, false);
            }
        }
        crate::dev_command::DevPanelTab::Control => {
            refresh_control_snapshot(state, deps, matches!(mode, RefreshMode::Force))
        }
        crate::dev_command::DevPanelTab::Ops => {
            if matches!(mode, RefreshMode::Force)
                || state.dev_panel_commands.ops_snapshot().is_none()
            {
                ops_snapshot::refresh_ops_snapshot(state);
            }
        }
        crate::dev_command::DevPanelTab::Handoff => {
            refresh_handoff_sources(
                state,
                deps,
                matches!(mode, RefreshMode::Force),
                matches!(mode, RefreshMode::Force),
            );
            snapshots::refresh_handoff_snapshot(state);
        }
        crate::dev_command::DevPanelTab::Memory => {
            if matches!(mode, RefreshMode::Force)
                || state.dev_panel_commands.git_snapshot().is_none()
            {
                git_snapshot::refresh_git_snapshot(state, &deps.session);
            }
            snapshots::refresh_memory_snapshot(state);
            snapshots::refresh_handoff_snapshot(state);
            snapshots::refresh_memory_cockpit_snapshot(state);
        }
        crate::dev_command::DevPanelTab::Actions => {}
    }
}
