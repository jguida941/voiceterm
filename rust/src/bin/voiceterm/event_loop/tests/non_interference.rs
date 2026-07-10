use super::*;

// Non-interference regression tests (MP-306)
//
// These tests prove that dev tooling surfaces (dev panel overlay, dev command
// broker, dev mode stats) are **never** loaded or activated when `--dev` is
// absent, ensuring the default Whisper/listen session is unchanged.
// ---------------------------------------------------------------------------

#[test]
fn non_interference_ctrl_d_sends_eof_byte_when_dev_mode_off() {
    // When dev_mode is false, Ctrl+D (InputEvent::DevPanelToggle) must forward
    // the 0x04 EOF byte to the PTY instead of opening a dev panel overlay.
    let _guard = install_try_send_hook(hook_would_block);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = false;
    state.ui.overlay_mode = OverlayMode::None;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::DevPanelToggle,
        &mut running,
    );

    assert!(
        running,
        "session must remain running after Ctrl+D in non-dev mode"
    );
    assert_eq!(
        state.ui.overlay_mode,
        OverlayMode::None,
        "overlay must stay None when dev_mode is off"
    );
    assert_eq!(
        state.pty_buffer.pending_input.front(),
        Some(&vec![0x04]),
        "Ctrl+D must queue the EOF byte (0x04) to the PTY"
    );
    assert_eq!(
        state.pty_buffer.pending_input_bytes, 1,
        "exactly one byte (EOF) should be queued"
    );
}

#[test]
fn non_interference_overlay_never_becomes_dev_panel_when_dev_mode_off() {
    // Exhaustively verify that no combination of normal input events can
    // transition the overlay to DevPanel when dev_mode is disabled.
    let _guard = install_try_send_hook(hook_non_empty_full_write);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = false;
    let mut running = true;

    let probe_events = vec![
        InputEvent::DevPanelToggle,
        InputEvent::HelpToggle,
        InputEvent::SettingsToggle,
        InputEvent::ThemePicker,
        InputEvent::EnterKey,
        InputEvent::Bytes(vec![0x04]),
        InputEvent::Bytes(vec![0x1b]),
    ];

    for evt in probe_events {
        handle_input_event(&mut state, &mut timers, &mut deps, evt, &mut running);
        assert_ne!(
            state.ui.overlay_mode,
            OverlayMode::DevPanel,
            "overlay must never transition to DevPanel when dev_mode is off"
        );
    }
}

#[test]
fn non_interference_dev_command_broker_absent_when_dev_mode_off() {
    // The build_harness helper mirrors the default (non-dev) mode where
    // dev_command_broker is None.  Confirm the invariant holds.
    let (state, _timers, deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);

    assert!(
        !state.config.dev_mode,
        "build_harness must default to dev_mode = false"
    );
    assert!(
        deps.dev_command_broker.is_none(),
        "dev_command_broker must be None when dev_mode is off"
    );
}

#[test]
fn non_interference_dev_mode_stats_absent_when_dev_mode_off() {
    // DevModeStats should only be allocated when --dev is present.
    let (state, _timers, _deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);

    assert!(
        !state.config.dev_mode,
        "build_harness must default to dev_mode = false"
    );
    assert!(
        state.dev_mode_stats.is_none(),
        "dev_mode_stats must be None when dev_mode is off"
    );
    assert!(
        state.dev_event_logger.is_none(),
        "dev_event_logger must be None when dev_mode is off"
    );
}

#[test]
fn non_interference_dev_panel_toggle_opens_panel_when_dev_mode_on() {
    // Positive control: verify that Ctrl+D *does* open the dev panel when
    // dev_mode is enabled, confirming the guard correctly distinguishes modes.
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::None;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::DevPanelToggle,
        &mut running,
    );

    assert!(running);
    assert_eq!(
        state.ui.overlay_mode,
        OverlayMode::DevPanel,
        "overlay must switch to DevPanel when dev_mode is on"
    );
    // The overlay renderer should have emitted a ShowOverlay message.
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("dev panel render message")
    {
        WriterMessage::ShowOverlay { content, height } => {
            assert_eq!(height, dev_panel_height());
            assert!(
                content.contains("Actions"),
                "overlay content should contain the Actions header"
            );
        }
        other => panic!("expected ShowOverlay, got: {other:?}"),
    }
    // Confirm PTY did NOT receive the EOF byte.
    assert!(
        state.pty_buffer.pending_input.is_empty(),
        "PTY input queue must be empty when dev panel opens"
    );
}

#[test]
fn non_interference_poll_dev_commands_is_noop_when_broker_absent() {
    // When dev_command_broker is None (non-dev mode), periodic polling
    // should be a harmless no-op that does not mutate state.
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = false;
    let status_before = state.current_status.clone();
    let overlay_before = state.ui.overlay_mode;

    assert!(deps.dev_command_broker.is_none());
    poll_dev_command_updates(&mut state, &mut timers, &mut deps);

    assert_eq!(
        state.current_status, status_before,
        "status must not change when broker is absent"
    );
    assert_eq!(
        state.ui.overlay_mode, overlay_before,
        "overlay must not change when broker is absent"
    );
}
