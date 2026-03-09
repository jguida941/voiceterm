use super::super::*;

fn dev_panel_action_index(action_id: &str) -> usize {
    crate::dev_command::ActionCatalog::default_catalog()
        .find_by_id(action_id)
        .expect("action should exist in default catalog")
        .0
}

#[test]
fn dev_panel_arrow_navigation_moves_command_selection() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state.dev_panel_commands.select_index(0);
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![0x1b, b'[', b'B']),
        &mut running,
    );

    assert!(running);
    assert_eq!(
        state.dev_panel_commands.selected_command(),
        DevCommandKind::Report
    );
}

#[test]
fn dev_panel_numeric_selection_supports_extended_command_set() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state.dev_panel_commands.select_index(0);
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![b'4']),
        &mut running,
    );

    assert!(running);
    assert_eq!(
        state.dev_panel_commands.selected_command(),
        DevCommandKind::LoopPacket
    );
}

#[test]
fn dev_panel_sync_requires_confirmation_before_run() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .select_index(dev_panel_action_index("devctl_sync"));
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(
        state.dev_panel_commands.pending_confirmation_index(),
        Some(state.dev_panel_commands.selected_index())
    );
    assert!(state.dev_panel_commands.running_request_id().is_none());
}

#[test]
fn dev_panel_sync_under_unsafe_direct_does_not_launch_broker() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .select_index(dev_panel_action_index("devctl_sync"));
    state
        .dev_panel_commands
        .set_execution_profile(crate::dev_command::ExecutionProfile::UnsafeDirect);
    let mut running = true;

    // Under Unsafe Direct, sync should resolve to StageDraft and NOT launch the broker.
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert!(state.dev_panel_commands.running_request_id().is_none());
    assert!(state
        .current_status
        .as_deref()
        .is_some_and(|status| status.contains("staged")));
}

#[test]
fn dev_panel_read_only_under_unsafe_direct_still_executes() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    // Index 0 = status (ReadOnly) — should still execute even under Unsafe Direct
    state.dev_panel_commands.select_index(0);
    state
        .dev_panel_commands
        .set_execution_profile(crate::dev_command::ExecutionProfile::UnsafeDirect);
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    // Read-only actions resolve to SafeAutoApply; broker may or may not be present
    // but the status should NOT say "staged" or "blocked"
    let status = state.current_status.as_deref().unwrap_or("");
    assert!(!status.contains("staged"));
    assert!(!status.contains("blocked"));
}

#[test]
fn apply_terminal_packet_completion_stages_draft_text() {
    let _guard = install_try_send_hook(hook_would_block);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let completion = DevCommandCompletion {
        request_id: 7,
        command: DevCommandKind::LoopPacket,
        status: DevCommandStatus::Success,
        duration_ms: 12,
        summary: "packet ready".to_string(),
        stdout_excerpt: None,
        stderr_excerpt: None,
        terminal_packet: Some(DevTerminalPacket {
            packet_id: "pkt-123".to_string(),
            source_command: "triage-loop".to_string(),
            draft_text: "propose bounded remediation".to_string(),
            auto_send: false,
        }),
    };

    let message = dev_panel_commands::apply_terminal_packet_completion(
        &mut state,
        &mut timers,
        &mut deps,
        &completion,
    )
    .expect("packet staging message");

    assert!(message.contains("staged"));
    assert!(state.status_state.insert_pending_send);
    assert_eq!(
        state.pty_buffer.pending_input_bytes,
        "propose bounded remediation".len()
    );
}

#[test]
fn apply_terminal_packet_completion_auto_send_requires_runtime_guard() {
    let _guard = install_try_send_hook(hook_would_block);
    struct AutoSendOverrideReset;
    impl Drop for AutoSendOverrideReset {
        fn drop(&mut self) {
            dev_panel_commands::set_dev_packet_auto_send_runtime_override(None);
        }
    }
    let _reset = AutoSendOverrideReset;
    dev_panel_commands::set_dev_packet_auto_send_runtime_override(Some(true));

    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let completion = DevCommandCompletion {
        request_id: 8,
        command: DevCommandKind::LoopPacket,
        status: DevCommandStatus::Success,
        duration_ms: 12,
        summary: "packet ready".to_string(),
        stdout_excerpt: None,
        stderr_excerpt: None,
        terminal_packet: Some(DevTerminalPacket {
            packet_id: "pkt-456".to_string(),
            source_command: "triage".to_string(),
            draft_text: "all clear, continue".to_string(),
            auto_send: true,
        }),
    };

    let message = dev_panel_commands::apply_terminal_packet_completion(
        &mut state,
        &mut timers,
        &mut deps,
        &completion,
    )
    .expect("packet auto-send message");

    assert!(message.contains("auto-sent"));
    assert!(!state.status_state.insert_pending_send);
    assert_eq!(
        state.pty_buffer.pending_input_bytes,
        "all clear, continue".len() + 1
    );
    assert!(timers.last_enter_at.is_some());
}

#[test]
fn dev_panel_second_sync_enter_without_broker_reports_unavailable() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
    state
        .dev_panel_commands
        .select_index(dev_panel_action_index("devctl_sync"));
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.dev_panel_commands.pending_confirmation_index(), None);
    assert_eq!(state.dev_panel_commands.running_request_id(), None);
    assert!(state
        .current_status
        .as_deref()
        .is_some_and(|status| status.contains("broker unavailable")));
}
