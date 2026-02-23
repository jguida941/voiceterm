//! Dev-panel command helpers extracted from the core event loop.

use super::*;

pub(super) fn move_dev_panel_selection(state: &mut EventLoopState, delta: i32) -> bool {
    let previous = state.dev_panel_commands.selected_command();
    state.dev_panel_commands.move_selection(delta);
    state.dev_panel_commands.selected_command() != previous
}

pub(super) fn select_dev_panel_command_by_index(state: &mut EventLoopState, index: usize) -> bool {
    let previous = state.dev_panel_commands.selected_command();
    state.dev_panel_commands.select_index(index);
    state.dev_panel_commands.selected_command() != previous
}

pub(super) fn request_selected_dev_panel_command(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    if !state.config.dev_mode {
        return;
    }

    if state.dev_panel_commands.running_request_id().is_some() {
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            "Dev command already running",
            Some(Duration::from_secs(2)),
        );
        return;
    }

    let command = state.dev_panel_commands.selected_command();
    if command.is_mutating() && state.dev_panel_commands.pending_confirmation() != Some(command) {
        state.dev_panel_commands.request_confirmation(command);
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            "Sync is mutating; press Enter again to confirm",
            Some(Duration::from_secs(3)),
        );
        return;
    }

    state.dev_panel_commands.clear_pending_confirmation();
    let Some(broker) = deps.dev_command_broker.as_mut() else {
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            "Dev command broker unavailable",
            Some(Duration::from_secs(2)),
        );
        return;
    };

    match broker.run_command(command) {
        Ok(request_id) => {
            state
                .dev_panel_commands
                .register_launch(request_id, command);
            let message = format!("Running devctl {}...", command.label());
            set_status(
                &deps.writer_tx,
                &mut timers.status_clear_deadline,
                &mut state.current_status,
                &mut state.status_state,
                &message,
                Some(Duration::from_secs(2)),
            );
        }
        Err(err) => {
            let message = format!("Failed to queue dev command: {err}");
            set_status(
                &deps.writer_tx,
                &mut timers.status_clear_deadline,
                &mut state.current_status,
                &mut state.status_state,
                &message,
                Some(Duration::from_secs(2)),
            );
        }
    }
}

pub(super) fn cancel_running_dev_panel_command(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    state.dev_panel_commands.clear_pending_confirmation();
    let Some(request_id) = state.dev_panel_commands.running_request_id() else {
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            "No running dev command",
            Some(Duration::from_secs(2)),
        );
        return;
    };

    let Some(broker) = deps.dev_command_broker.as_ref() else {
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            "Dev command broker unavailable",
            Some(Duration::from_secs(2)),
        );
        return;
    };

    if let Err(err) = broker.cancel_command(request_id) {
        let message = format!("Failed to cancel dev command: {err}");
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            &message,
            Some(Duration::from_secs(2)),
        );
        return;
    }

    set_status(
        &deps.writer_tx,
        &mut timers.status_clear_deadline,
        &mut state.current_status,
        &mut state.status_state,
        "Cancelling dev command...",
        Some(Duration::from_secs(2)),
    );
}

pub(super) fn poll_dev_command_updates(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    let mut updates = Vec::new();
    if let Some(broker) = deps.dev_command_broker.as_ref() {
        while let Some(update) = broker.try_recv_update() {
            updates.push(update);
        }
    }

    if updates.is_empty() {
        return;
    }

    for update in updates {
        if let crate::dev_command::DevCommandUpdate::Completed(completion) = &update {
            let message = format!(
                "Dev {} {}",
                completion.command.label(),
                completion.status.label()
            );
            set_status(
                &deps.writer_tx,
                &mut timers.status_clear_deadline,
                &mut state.current_status,
                &mut state.status_state,
                &message,
                Some(Duration::from_secs(3)),
            );
        }
        state.dev_panel_commands.apply_update(update);
    }

    if state.overlay_mode == OverlayMode::DevPanel {
        render_dev_panel_overlay_for_state(state, deps);
    }
}
