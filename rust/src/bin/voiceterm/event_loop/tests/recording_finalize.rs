use super::*;

#[test]
fn run_event_loop_enter_with_pending_insert_text_sends_without_capture_stop() {
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.recording_state = RecordingState::Recording;
    state.status_state.insert_pending_send = true;

    input_tx.send(InputEvent::EnterKey).expect("queue enter");
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);

    assert!(timers.last_enter_at.is_some());
    assert!(!state.status_state.insert_pending_send);
    assert_eq!(
        state.status_state.recording_state,
        RecordingState::Recording
    );
}

#[test]
fn run_event_loop_enter_without_pending_insert_text_does_not_stop_recording() {
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.recording_state = RecordingState::Recording;
    state.status_state.insert_pending_send = false;

    input_tx.send(InputEvent::EnterKey).expect("queue enter");
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);

    assert!(timers.last_enter_at.is_some());
    assert!(!state.status_state.insert_pending_send);
    assert_eq!(
        state.status_state.recording_state,
        RecordingState::Recording
    );
}

#[test]
fn hidden_open_enter_expands_collapsed_launcher_before_style_cycle() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.hud_style = HudStyle::Hidden;
    state.status_state.hidden_launcher_collapsed = true;
    state.status_state.hud_button_focus = Some(ButtonAction::ToggleHudStyle);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.status_state.hud_style, HudStyle::Hidden);
    assert!(!state.status_state.hidden_launcher_collapsed);
}

#[test]
fn hidden_open_enter_cycles_style_after_launcher_is_expanded() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.hud_style = HudStyle::Hidden;
    state.status_state.hidden_launcher_collapsed = false;
    state.status_state.hud_button_focus = Some(ButtonAction::ToggleHudStyle);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.status_state.hud_style, HudStyle::Full);
}

#[test]
fn hidden_hide_mouse_click_collapses_launcher_and_emits_status_redraw() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.hud_style = HudStyle::Hidden;
    state.status_state.hidden_launcher_collapsed = false;
    update_button_registry(
        &deps.button_registry,
        &state.status_state,
        state.ui.overlay_mode,
        state.ui.terminal_cols,
        state.theme,
    );
    let (x, y) = hud_button_click_coords(&state, &deps, ButtonAction::CollapseHiddenLauncher);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x, y },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.status_state.hud_style, HudStyle::Hidden);
    assert!(state.status_state.hidden_launcher_collapsed);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("hidden hide click should trigger redraw")
    {
        WriterMessage::EnhancedStatus(status) => {
            assert_eq!(status.hud_style, HudStyle::Hidden);
            assert!(status.hidden_launcher_collapsed);
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn hidden_open_mouse_click_expands_collapsed_launcher_and_emits_status_redraw() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.hud_style = HudStyle::Hidden;
    state.status_state.hidden_launcher_collapsed = true;
    update_button_registry(
        &deps.button_registry,
        &state.status_state,
        state.ui.overlay_mode,
        state.ui.terminal_cols,
        state.theme,
    );
    let (x, y) = hud_button_click_coords(&state, &deps, ButtonAction::ToggleHudStyle);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x, y },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.status_state.hud_style, HudStyle::Hidden);
    assert!(!state.status_state.hidden_launcher_collapsed);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("hidden open click should trigger redraw")
    {
        WriterMessage::EnhancedStatus(status) => {
            assert_eq!(status.hud_style, HudStyle::Hidden);
            assert!(!status.hidden_launcher_collapsed);
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn run_event_loop_ctrl_e_with_pending_insert_text_finalizes_without_sending_while_recording() {
    let _hook = install_try_send_hook(hook_count_writes);
    let _early_stop = install_request_early_stop_hook(hook_request_early_stop_true);
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.recording_state = RecordingState::Recording;
    state.status_state.insert_pending_send = true;

    input_tx
        .send(InputEvent::SendStagedText)
        .expect("queue ctrl+e send");
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);

    EARLY_STOP_CALLS.with(|calls| assert_eq!(calls.get(), 1));
    assert!(timers.last_enter_at.is_none());
    assert!(state.status_state.insert_pending_send);
    assert_eq!(
        state.status_state.recording_state,
        RecordingState::Processing
    );
    assert!(!state.force_send_on_next_transcript);
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn run_event_loop_ctrl_e_without_pending_insert_text_requests_early_finalize() {
    let _early_stop = install_request_early_stop_hook(hook_request_early_stop_true);
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.recording_state = RecordingState::Recording;
    state.status_state.insert_pending_send = false;

    input_tx
        .send(InputEvent::SendStagedText)
        .expect("queue ctrl+e send");
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);

    EARLY_STOP_CALLS.with(|calls| assert_eq!(calls.get(), 1));
    assert!(timers.last_enter_at.is_none());
    assert!(!state.status_state.insert_pending_send);
    assert_eq!(
        state.status_state.recording_state,
        RecordingState::Processing
    );
    assert!(!state.force_send_on_next_transcript);
}

#[test]
fn run_event_loop_ctrl_e_with_pending_insert_text_outside_recording_keeps_text_staged() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.recording_state = RecordingState::Idle;
    state.status_state.insert_pending_send = true;

    input_tx
        .send(InputEvent::SendStagedText)
        .expect("queue ctrl+e send");
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);

    assert!(timers.last_enter_at.is_none());
    assert!(state.status_state.insert_pending_send);
    assert_eq!(state.status_state.recording_state, RecordingState::Idle);
    assert!(!state.force_send_on_next_transcript);
    assert_eq!(
        state.current_status.as_deref(),
        Some("Text staged; press Enter to send")
    );
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn run_event_loop_ctrl_e_without_pending_insert_text_reports_nothing_to_finalize() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.recording_state = RecordingState::Idle;
    state.status_state.insert_pending_send = false;

    input_tx
        .send(InputEvent::SendStagedText)
        .expect("queue ctrl+e send");
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);

    assert!(timers.last_enter_at.is_none());
    assert!(!state.status_state.insert_pending_send);
    assert_eq!(state.status_state.recording_state, RecordingState::Idle);
    assert!(!state.force_send_on_next_transcript);
    assert_eq!(state.current_status.as_deref(), Some("Nothing to finalize"));
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn set_claude_prompt_suppression_expands_pty_row_budget() {
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;
    assert_eq!(status_banner_height(80, HudStyle::Full), 4);
    let reserved = crate::terminal::reserved_rows_for_mode(
        OverlayMode::None,
        state.ui.terminal_cols,
        state.status_state.hud_style,
        false,
    ) as u16;
    let unsuppressed_rows = state.ui.terminal_rows.saturating_sub(reserved).max(1);

    super::prompt_occlusion::apply_prompt_suppression(&mut state, &mut deps, true);
    assert!(state.status_state.prompt_suppressed);
    let (suppressed_rows, _) = deps.session.current_winsize();
    let expected_suppressed_rows = state
        .ui
        .terminal_rows
        .saturating_sub(crate::terminal::reserved_rows_for_mode(
            OverlayMode::None,
            state.ui.terminal_cols,
            state.status_state.hud_style,
            true,
        ) as u16)
        .max(1);
    assert_eq!(suppressed_rows, expected_suppressed_rows);

    super::prompt_occlusion::apply_prompt_suppression(&mut state, &mut deps, false);
    assert!(!state.status_state.prompt_suppressed);
    let (restored_rows, _) = deps.session.current_winsize();
    assert_eq!(restored_rows, unsuppressed_rows);
}

#[test]
fn set_claude_prompt_suppression_clears_hud_before_status_update() {
    let (mut state, _timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    super::prompt_occlusion::apply_prompt_suppression(&mut state, &mut deps, true);

    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("suppression should first clear status")
    {
        WriterMessage::ClearStatus => {}
        other => panic!("expected ClearStatus, got {other:?}"),
    }

    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("suppression should then send enhanced status")
    {
        WriterMessage::EnhancedStatus(status) => {
            assert!(status.prompt_suppressed);
        }
        other => panic!("expected EnhancedStatus, got {other:?}"),
    }

    super::prompt_occlusion::apply_prompt_suppression(&mut state, &mut deps, false);

    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("unsuppression should first clear status")
    {
        WriterMessage::ClearStatus => {}
        other => panic!("expected ClearStatus, got {other:?}"),
    }

    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("unsuppression should then send enhanced status")
    {
        WriterMessage::EnhancedStatus(status) => {
            assert!(!status.prompt_suppressed);
        }
        other => panic!("expected EnhancedStatus, got {other:?}"),
    }
}

#[test]
fn periodic_tasks_clear_stale_prompt_suppression_without_new_output() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;

    // Activate suppression and row-budget expansion.
    let detected = state
        .prompt
        .occlusion_detector
        .feed_output(b"Do you want to proceed? (y/n)\n");
    assert!(detected);
    super::prompt_occlusion::apply_prompt_suppression(&mut state, &mut deps, true);
    timers.prompt_suppression_release_not_before = Some(Instant::now() + Duration::from_secs(3));
    let (suppressed_rows, _) = deps.session.current_winsize();
    let reserved = crate::terminal::reserved_rows_for_mode(
        OverlayMode::None,
        state.ui.terminal_cols,
        state.status_state.hud_style,
        false,
    ) as u16;
    let unsuppressed_rows = state.ui.terminal_rows.saturating_sub(reserved).max(1);
    let expected_suppressed_rows = state
        .ui
        .terminal_rows
        .saturating_sub(crate::terminal::reserved_rows_for_mode(
            OverlayMode::None,
            state.ui.terminal_cols,
            state.status_state.hud_style,
            true,
        ) as u16)
        .max(1);
    assert_eq!(suppressed_rows, expected_suppressed_rows);

    // Detector resolved via user input path, but no fresh output chunk arrives.
    state.prompt.occlusion_detector.on_user_input();
    let now = Instant::now();
    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert!(state.status_state.prompt_suppressed);
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_secs(4),
    );

    assert!(!state.status_state.prompt_suppressed);
    let (restored_rows, _) = deps.session.current_winsize();
    assert_eq!(restored_rows, unsuppressed_rows);
}

#[test]
fn toast_history_toggle_opens_and_closes_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::ToastHistoryToggle,
        &mut running,
    );
    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ToastHistory);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::ToastHistoryToggle,
        &mut running,
    );
    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
}

#[test]
fn periodic_tasks_push_status_toasts_with_severity_mapping() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();

    state.current_status = Some("Transcript ready".to_string());
    state.status_state.message = "Transcript ready".to_string();
    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(state.toast_center.active_count(), 1);
    assert_eq!(
        state.toast_center.active_toasts()[0].severity,
        crate::toast::ToastSeverity::Success
    );

    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_millis(10),
    );
    assert_eq!(state.toast_center.active_count(), 1);

    state.current_status = Some("Voice capture failed".to_string());
    state.status_state.message = "Voice capture failed".to_string();
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_millis(20),
    );
    assert_eq!(state.toast_center.active_count(), 2);
    assert_eq!(
        state.toast_center.active_toasts()[1].severity,
        crate::toast::ToastSeverity::Error
    );
}

#[test]
fn periodic_tasks_status_clear_resets_toast_dedupe() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();

    state.current_status = Some("Capture stopped".to_string());
    state.status_state.message = "Capture stopped".to_string();
    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(state.toast_center.active_count(), 1);

    timers.status_clear_deadline = Some(now - Duration::from_millis(1));
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_millis(2),
    );
    assert!(state.current_status.is_none());

    state.current_status = Some("Capture stopped".to_string());
    state.status_state.message = "Capture stopped".to_string();
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_millis(4),
    );
    assert_eq!(state.toast_center.active_count(), 2);
}

// ---------------------------------------------------------------------------
