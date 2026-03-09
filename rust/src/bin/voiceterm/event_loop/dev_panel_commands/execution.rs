//! Dev-panel command execution, auto-send control, and polling.

use super::super::*;
use std::sync::OnceLock;

#[cfg(test)]
use std::sync::atomic::{AtomicU8, Ordering};

fn parse_dev_packet_auto_send_runtime_flag(raw: &str) -> bool {
    matches!(
        raw.trim().to_ascii_lowercase().as_str(),
        "1" | "true" | "yes" | "on"
    )
}

fn dev_packet_auto_send_runtime_env_enabled() -> bool {
    let raw = std::env::var("VOICETERM_DEV_PACKET_AUTOSEND").unwrap_or_default();
    parse_dev_packet_auto_send_runtime_flag(&raw)
}

static DEV_PACKET_AUTOSEND_RUNTIME_ENABLED: OnceLock<bool> = OnceLock::new();

#[cfg(test)]
static DEV_PACKET_AUTOSEND_RUNTIME_OVERRIDE: AtomicU8 = AtomicU8::new(0);

fn dev_packet_auto_send_runtime_enabled() -> bool {
    #[cfg(test)]
    {
        match DEV_PACKET_AUTOSEND_RUNTIME_OVERRIDE.load(Ordering::Relaxed) {
            1 => return false,
            2 => return true,
            _ => {}
        }
    }
    *DEV_PACKET_AUTOSEND_RUNTIME_ENABLED.get_or_init(dev_packet_auto_send_runtime_env_enabled)
}

#[cfg(test)]
pub(in super::super) fn set_dev_packet_auto_send_runtime_override(override_value: Option<bool>) {
    let encoded = match override_value {
        Some(false) => 1,
        Some(true) => 2,
        None => 0,
    };
    DEV_PACKET_AUTOSEND_RUNTIME_OVERRIDE.store(encoded, Ordering::Relaxed);
}

pub(in super::super) fn apply_terminal_packet_completion(
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

pub(in super::super) fn move_dev_panel_selection(state: &mut EventLoopState, delta: i32) -> bool {
    let previous = state.dev_panel_commands.selected_command();
    state.dev_panel_commands.move_selection(delta);
    state.dev_panel_commands.selected_command() != previous
}

pub(in super::super) fn select_dev_panel_command_by_index(
    state: &mut EventLoopState,
    index: usize,
) -> bool {
    let previous = state.dev_panel_commands.selected_command();
    state.dev_panel_commands.select_index(index);
    state.dev_panel_commands.selected_command() != previous
}

pub(in super::super) fn request_selected_dev_panel_command(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    if !state.config.dev_mode {
        return;
    }

    if state.dev_panel_commands.running_request_id().is_some() {
        super::set_dev_status(
            state,
            timers,
            deps,
            "Dev command already running",
            Some(Duration::from_secs(2)),
        );
        return;
    }

    let selected_index = state.dev_panel_commands.selected_index();
    let policy = state.dev_panel_commands.selected_policy();
    let label = state.dev_panel_commands.selected_entry().label();
    let policy_label = policy.label();

    if policy == crate::dev_command::PolicyOutcome::Blocked {
        let message = format!(
            "'{}' is blocked under current profile [{}]",
            label, policy_label
        );
        super::set_dev_status(state, timers, deps, &message, Some(Duration::from_secs(3)));
        return;
    }

    if policy == crate::dev_command::PolicyOutcome::OperatorApprovalRequired
        && state.dev_panel_commands.pending_confirmation_index() != Some(selected_index)
    {
        state
            .dev_panel_commands
            .request_confirmation_at(selected_index);
        let message = format!(
            "'{}' requires confirmation [{}]; press Enter again",
            label, policy_label
        );
        super::set_dev_status(state, timers, deps, &message, Some(Duration::from_secs(3)));
        return;
    }

    state.dev_panel_commands.clear_pending_confirmation();

    // StageDraft means the action should be staged for review, not executed.
    // Under Unsafe Direct, mutating actions produce a visible warning instead
    // of running the real broker command in this slice.
    if policy == crate::dev_command::PolicyOutcome::StageDraft {
        let message = format!(
            "'{}' staged [{}] — execution deferred until guarded handoff lands",
            label, policy_label
        );
        super::set_dev_status(state, timers, deps, &message, Some(Duration::from_secs(3)));
        return;
    }

    let Some(dev_command) = state.dev_panel_commands.selected_entry().dev_command() else {
        super::set_dev_status(
            state,
            timers,
            deps,
            "Action has no command implementation yet",
            Some(Duration::from_secs(2)),
        );
        return;
    };

    let Some(broker) = deps.dev_command_broker.as_mut() else {
        super::set_dev_status(
            state,
            timers,
            deps,
            "Dev command broker unavailable",
            Some(Duration::from_secs(2)),
        );
        return;
    };

    match broker.run_command(dev_command) {
        Ok(request_id) => {
            state
                .dev_panel_commands
                .register_launch(request_id, dev_command);
            let message = format!("Running devctl {}...", label);
            super::set_dev_status(state, timers, deps, &message, Some(Duration::from_secs(2)));
        }
        Err(err) => {
            let message = format!("Failed to queue dev command: {err}");
            super::set_dev_status(state, timers, deps, &message, Some(Duration::from_secs(2)));
        }
    }
}

pub(in super::super) fn cycle_dev_panel_execution_profile(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    state.dev_panel_commands.cycle_execution_profile();
    let profile = state.dev_panel_commands.execution_profile();
    let message = format!("Execution profile: {}", profile.label());
    super::set_dev_status(state, timers, deps, &message, Some(Duration::from_secs(2)));
}

pub(in super::super) fn cancel_running_dev_panel_command(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    state.dev_panel_commands.clear_pending_confirmation();
    let Some(request_id) = state.dev_panel_commands.running_request_id() else {
        super::set_dev_status(
            state,
            timers,
            deps,
            "No running dev command",
            Some(Duration::from_secs(2)),
        );
        return;
    };

    let Some(broker) = deps.dev_command_broker.as_ref() else {
        super::set_dev_status(
            state,
            timers,
            deps,
            "Dev command broker unavailable",
            Some(Duration::from_secs(2)),
        );
        return;
    };

    if let Err(err) = broker.cancel_command(request_id) {
        let message = format!("Failed to cancel dev command: {err}");
        super::set_dev_status(state, timers, deps, &message, Some(Duration::from_secs(2)));
        return;
    }

    super::set_dev_status(
        state,
        timers,
        deps,
        "Cancelling dev command...",
        Some(Duration::from_secs(2)),
    );
}

pub(in super::super) fn poll_dev_command_updates(
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
            super::set_dev_status(state, timers, deps, &message, Some(Duration::from_secs(3)));
        }
        state.dev_panel_commands.apply_update(update);
    }

    if state.ui.overlay_mode == OverlayMode::DevPanel {
        render_dev_panel_overlay_for_state(state, deps);
    }
}
