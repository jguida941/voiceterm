use super::*;

#[test]
fn run_event_loop_help_overlay_mouse_body_click_keeps_overlay_open() {
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Help;
    let overlay_top_y = state
        .ui
        .terminal_rows
        .saturating_sub(help_overlay_height() as u16)
        .saturating_add(1);
    input_tx
        .send(InputEvent::MouseClick {
            x: 3,
            y: overlay_top_y.saturating_add(1),
        })
        .expect("queue overlay body click");
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Help);
}

#[test]
fn help_overlay_unhandled_bytes_close_overlay_and_replay_input() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Help;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"status".to_vec()),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 1));
}

#[test]
fn help_overlay_unhandled_ctrl_e_closes_overlay_and_replays_action() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Help;
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.recording_state = RecordingState::Idle;
    state.status_state.insert_pending_send = false;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::SendStagedText,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
    assert_eq!(state.current_status.as_deref(), Some("Nothing to finalize"));
}

#[test]
fn transcript_history_overlay_ignores_escape_noise_in_search() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::TranscriptHistory;
    state.transcript_history.push("alpha".to_string());
    state
        .transcript_history_state
        .refresh_filter(&state.transcript_history);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[0[I".to_vec()),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.transcript_history_state.search_query, "");
}

#[test]
fn transcript_history_overlay_enter_on_assistant_entry_does_not_replay() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::TranscriptHistory;
    state
        .transcript_history
        .ingest_backend_output_bytes(b"assistant output\n");
    state
        .transcript_history_state
        .refresh_filter(&state.transcript_history);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::TranscriptHistory);
    assert_eq!(
        state.current_status.as_deref(),
        Some("Selected entry is output-only (not replayable)")
    );
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn toggle_hud_style_in_help_overlay_does_not_render_settings_overlay() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}
    state.ui.overlay_mode = OverlayMode::Help;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::ToggleHudStyle,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::Help);
    let rendered_settings_overlay = writer_rx
        .try_iter()
        .any(|msg| matches!(msg, WriterMessage::ShowOverlay { height, .. } if height == settings_overlay_height()));
    assert!(
        !rendered_settings_overlay,
        "help overlay toggle should not render settings overlay"
    );
}

#[test]
fn run_event_loop_theme_picker_click_selects_theme_and_closes_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemePicker;
    let overlay_top_y = state
        .ui
        .terminal_rows
        .saturating_sub(theme_picker_height() as u16)
        .saturating_add(1);
    let click_x = centered_theme_picker_rel_x_to_screen_x(&state, 3);
    input_tx
        .send(InputEvent::MouseClick {
            x: click_x,
            y: overlay_top_y + THEME_PICKER_OPTION_START_ROW as u16 - 1,
        })
        .expect("queue theme option click");
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
    assert_ne!(state.theme, Theme::Codex);
}

#[test]
fn theme_picker_enter_with_invalid_selection_keeps_overlay_open_and_rerenders() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    state.ui.overlay_mode = OverlayMode::ThemePicker;
    state.theme_studio.picker_selected = THEME_OPTIONS.len() + 10;
    let original_theme = state.theme;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemePicker);
    assert_eq!(state.theme, original_theme);
    assert!(state.theme_studio.picker_digits.is_empty());
    let rendered = writer_rx
        .try_iter()
        .any(|message| matches!(message, WriterMessage::ShowOverlay { .. }));
    assert!(
        rendered,
        "invalid index should re-render theme picker overlay"
    );
}
