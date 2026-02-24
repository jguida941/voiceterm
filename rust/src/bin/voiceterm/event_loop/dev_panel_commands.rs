//! Dev-panel command helpers extracted from the core event loop.

use super::*;

fn dev_packet_auto_send_runtime_enabled() -> bool {
    let raw = std::env::var("VOICETERM_DEV_PACKET_AUTOSEND").unwrap_or_default();
    matches!(
        raw.trim().to_ascii_lowercase().as_str(),
        "1" | "true" | "yes" | "on"
    )
}

pub(super) fn apply_terminal_packet_completion(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    completion: &crate::dev_command::DevCommandCompletion,
) -> Option<String> {
    let packet = completion.terminal_packet.as_ref()?;
    if packet.draft_text.trim().is_empty() {
        return Some(format!(
            "Dev {} {} (empty packet draft)",
            completion.command.label(),
            completion.status.label()
        ));
    }
    if !write_or_queue_pty_input(state, deps, packet.draft_text.clone().into_bytes()) {
        return Some("Packet injection failed (PTY write error)".to_string());
    }

    let auto_send_requested = packet.auto_send;
    let auto_send_enabled = auto_send_requested && dev_packet_auto_send_runtime_enabled();
    if auto_send_enabled {
        if !write_or_queue_pty_input(state, deps, vec![0x0d]) {
            return Some("Packet auto-send failed (PTY write error)".to_string());
        }
        timers.last_enter_at = Some(Instant::now());
        state.status_state.insert_pending_send = false;
        state.status_state.recording_state = RecordingState::Responding;
        return Some(format!(
            "Packet {} auto-sent ({})",
            packet.packet_id, packet.source_command
        ));
    }

    state.status_state.insert_pending_send = true;
    if auto_send_requested {
        return Some(format!(
            "Packet {} staged from {} (auto-send requested but runtime guard is OFF)",
            packet.packet_id, packet.source_command
        ));
    }
    Some(format!(
        "Packet {} staged from {} (press Enter to send)",
        packet.packet_id, packet.source_command
    ))
}

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
            let message = apply_terminal_packet_completion(state, timers, deps, completion)
                .unwrap_or_else(|| {
                    format!(
                        "Dev {} {}",
                        completion.command.label(),
                        completion.status.label()
                    )
                });
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
