use super::*;

#[test]
fn run_periodic_tasks_sigwinch_no_size_change_skips_resize_messages() {
    let _host = install_terminal_host_override(TerminalHost::Other);
    let _hooks = install_sigwinch_hooks(hook_take_sigwinch_true, hook_terminal_size_80x24);
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.terminal_cols = 80;
    state.ui.terminal_rows = 24;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());
    assert!(
        writer_rx.recv_timeout(Duration::from_millis(100)).is_err(),
        "no resize event expected when geometry is unchanged"
    );
}

#[test]
fn run_periodic_tasks_sigwinch_single_dimension_change_triggers_resize() {
    let _host = install_terminal_host_override(TerminalHost::Other);
    let _hooks = install_sigwinch_hooks(hook_take_sigwinch_true, hook_terminal_size_80x24);
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.terminal_cols = 80;
    state.ui.terminal_rows = 1;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());
    let msg = writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("resize message");
    match msg {
        WriterMessage::Resize { rows, cols } => {
            assert_eq!(rows, 24);
            assert_eq!(cols, 80);
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
    assert_eq!(state.ui.terminal_cols, 80);
    assert_eq!(state.ui.terminal_rows, 24);
}

#[test]
fn run_periodic_tasks_cursor_sigwinch_is_debounced_before_resize_apply() {
    let _host = install_terminal_host_override(TerminalHost::Cursor);
    let _hooks = install_sigwinch_hooks(hook_take_sigwinch_true, hook_terminal_size_100x30);
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.terminal_cols = 80;
    state.ui.terminal_rows = 24;

    let first_tick = Instant::now();
    timers.last_terminal_geometry_poll = first_tick;
    run_periodic_tasks(&mut state, &mut timers, &mut deps, first_tick);
    assert!(
        writer_rx.recv_timeout(Duration::from_millis(100)).is_err(),
        "first Cursor SIGWINCH sample inside debounce window should not resize immediately"
    );
    assert_eq!(state.ui.terminal_cols, 80);
    assert_eq!(state.ui.terminal_rows, 24);

    let second_tick = first_tick + Duration::from_millis(200);
    run_periodic_tasks(&mut state, &mut timers, &mut deps, second_tick);
    let msg = writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("debounced Cursor SIGWINCH should apply resize on next eligible tick");
    match msg {
        WriterMessage::Resize { rows, cols } => {
            assert_eq!(rows, 30);
            assert_eq!(cols, 100);
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
    assert_eq!(state.ui.terminal_cols, 100);
    assert_eq!(state.ui.terminal_rows, 30);
}

#[test]
fn run_periodic_tasks_geometry_poll_without_sigwinch_triggers_resize() {
    let _hooks = install_sigwinch_hooks(hook_take_sigwinch_false, hook_terminal_size_100x30);
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.terminal_cols = 80;
    state.ui.terminal_rows = 24;
    timers.last_terminal_geometry_poll = Instant::now() - Duration::from_millis(1000);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());
    let msg = writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("resize message");
    match msg {
        WriterMessage::Resize { rows, cols } => {
            assert_eq!(rows, 30);
            assert_eq!(cols, 100);
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
    assert_eq!(state.ui.terminal_cols, 100);
    assert_eq!(state.ui.terminal_rows, 30);
}

#[test]
fn run_periodic_tasks_geometry_poll_ignores_zero_size_probe() {
    let _hooks = install_sigwinch_hooks(hook_take_sigwinch_false, hook_terminal_size_0x0);
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.terminal_cols = 80;
    state.ui.terminal_rows = 24;
    timers.last_terminal_geometry_poll = Instant::now() - Duration::from_millis(1000);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());
    assert!(
        writer_rx.recv_timeout(Duration::from_millis(100)).is_err(),
        "zero-size probes should not emit resize events when cached geometry is valid"
    );
    assert_eq!(state.ui.terminal_cols, 80);
    assert_eq!(state.ui.terminal_rows, 24);
}

#[test]
fn run_periodic_tasks_geometry_poll_debounces_single_claude_row_collapse_probe() {
    let _hooks =
        install_sigwinch_hooks(hook_take_sigwinch_false, hook_terminal_size_80x2_then_80x24);
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "claude".to_string();
    state.ui.terminal_cols = 80;
    state.ui.terminal_rows = 24;

    let first_tick = Instant::now();
    timers.last_terminal_geometry_poll = first_tick - Duration::from_millis(1000);
    run_periodic_tasks(&mut state, &mut timers, &mut deps, first_tick);
    assert!(
        writer_rx.recv_timeout(Duration::from_millis(100)).is_err(),
        "single collapse probe should not emit resize"
    );
    assert_eq!(state.ui.terminal_cols, 80);
    assert_eq!(state.ui.terminal_rows, 24);
    assert!(
        timers.pending_terminal_geometry_sample.is_some(),
        "first collapse probe should arm stabilization sample"
    );

    let second_tick = first_tick + Duration::from_millis(1000);
    timers.last_terminal_geometry_poll = second_tick - Duration::from_millis(1000);
    run_periodic_tasks(&mut state, &mut timers, &mut deps, second_tick);
    assert!(
        writer_rx.recv_timeout(Duration::from_millis(100)).is_err(),
        "returning to stable geometry should clear sample without resize"
    );
    assert_eq!(state.ui.terminal_cols, 80);
    assert_eq!(state.ui.terminal_rows, 24);
    assert!(
        timers.pending_terminal_geometry_sample.is_none(),
        "stable sample should clear collapse debounce state"
    );
}

#[test]
fn run_periodic_tasks_geometry_poll_accepts_persistent_claude_row_collapse() {
    let _hooks = install_sigwinch_hooks(hook_take_sigwinch_false, hook_terminal_size_80x2);
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.backend_label = "claude".to_string();
    state.ui.terminal_cols = 80;
    state.ui.terminal_rows = 24;

    let first_tick = Instant::now();
    timers.last_terminal_geometry_poll = first_tick - Duration::from_millis(1000);
    run_periodic_tasks(&mut state, &mut timers, &mut deps, first_tick);
    assert!(
        writer_rx.recv_timeout(Duration::from_millis(100)).is_err(),
        "first collapse sample should be held for stabilization"
    );
    assert_eq!(state.ui.terminal_rows, 24);

    let second_tick = first_tick + Duration::from_millis(1000);
    timers.last_terminal_geometry_poll = second_tick - Duration::from_millis(1000);
    run_periodic_tasks(&mut state, &mut timers, &mut deps, second_tick);
    let msg = writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("persistent collapse should emit resize after debounce");
    match msg {
        WriterMessage::Resize { rows, cols } => {
            assert_eq!(rows, 2);
            assert_eq!(cols, 80);
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
    assert_eq!(state.ui.terminal_rows, 2);
    assert_eq!(state.ui.terminal_cols, 80);
}

#[test]
fn run_periodic_tasks_updates_recording_duration() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Recording;
    timers.recording_started_at = Some(now - Duration::from_secs(2));
    timers.last_recording_update = now - Duration::from_millis(RECORDING_DURATION_UPDATE_MS + 5);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert!(state.status_state.recording_duration.is_some());
    assert!(state.last_recording_duration > 1.0);
    assert_eq!(timers.last_recording_update, now);
}

#[test]
fn run_periodic_tasks_keeps_theme_digits_when_picker_deadline_not_reached() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.ui.overlay_mode = OverlayMode::ThemePicker;
    state.theme_studio.picker_digits = "12".to_string();
    timers.theme_picker_digit_deadline = Some(now + Duration::from_secs(1));

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(state.theme_studio.picker_digits, "12");
    assert_eq!(
        timers.theme_picker_digit_deadline,
        Some(now + Duration::from_secs(1))
    );
}

#[test]
fn run_periodic_tasks_skips_recording_update_when_delta_is_too_small() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Recording;
    timers.recording_started_at = Some(now - Duration::from_secs(2));
    timers.last_recording_update = now - Duration::from_millis(RECORDING_DURATION_UPDATE_MS + 5);
    state.last_recording_duration = 2.05;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert!(state.status_state.recording_duration.is_none());
    assert_eq!(state.last_recording_duration, 2.05);
    assert_eq!(timers.last_recording_update, now);
}

#[test]
fn run_periodic_tasks_does_not_update_meter_when_not_recording() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Idle;
    state.meter_floor_started_at = Some(now - Duration::from_secs(2));
    timers.last_meter_update = now - Duration::from_secs(1);
    let prior_update = timers.last_meter_update;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert!(state.status_state.meter_db.is_none());
    assert!(state.meter_floor_started_at.is_none());
    assert_eq!(timers.last_meter_update, prior_update);
}

#[test]
fn run_periodic_tasks_keeps_meter_history_at_cap_when_prefill_is_one_under() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Recording;
    state.meter_levels = VecDeque::from(vec![-30.0; METER_HISTORY_MAX - 1]);
    timers.last_meter_update = now - Duration::from_millis(500);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(state.meter_levels.len(), METER_HISTORY_MAX);
}

#[test]
fn run_periodic_tasks_updates_meter_and_caps_history() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Recording;
    state.meter_levels = VecDeque::from(vec![-30.0; METER_HISTORY_MAX]);
    timers.last_meter_update = now - Duration::from_millis(500);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(state.meter_levels.len(), METER_HISTORY_MAX);
    assert!(state.status_state.meter_db.is_some());
    assert_eq!(timers.last_meter_update, now);
}

#[test]
fn run_periodic_tasks_keeps_floor_db_before_silence_placeholder_timeout() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Recording;
    state.meter_floor_started_at =
        Some(now - Duration::from_millis(METER_NO_SIGNAL_PLACEHOLDER_MS.saturating_sub(100)));
    timers.last_meter_update = now - Duration::from_millis(500);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert!(matches!(
        state.status_state.meter_db,
        Some(db) if db <= METER_DB_FLOOR + METER_FLOOR_EPSILON_DB
    ));
}

#[test]
fn run_periodic_tasks_keeps_last_db_after_sustained_floor_level() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Recording;
    state.status_state.meter_db = Some(-42.0);
    state.meter_floor_started_at =
        Some(now - Duration::from_millis(METER_NO_SIGNAL_PLACEHOLDER_MS + 1));
    timers.last_meter_update = now - Duration::from_millis(500);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(state.status_state.meter_db, Some(-42.0));
}

#[test]
fn run_periodic_tasks_sets_floor_db_after_sustained_floor_level_when_unset() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Recording;
    state.status_state.meter_db = None;
    state.meter_floor_started_at =
        Some(now - Duration::from_millis(METER_NO_SIGNAL_PLACEHOLDER_MS + 1));
    timers.last_meter_update = now - Duration::from_millis(500);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert!(matches!(
        state.status_state.meter_db,
        Some(db) if db <= METER_DB_FLOOR + METER_FLOOR_EPSILON_DB
    ));
}

#[test]
fn run_periodic_tasks_non_floor_level_clears_floor_tracking_state() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    let non_floor_level = METER_DB_FLOOR + METER_FLOOR_EPSILON_DB + 1.0;
    state.status_state.recording_state = RecordingState::Recording;
    state.meter_floor_started_at =
        Some(now - Duration::from_millis(METER_NO_SIGNAL_PLACEHOLDER_MS + 1));
    timers.last_meter_update = now - Duration::from_millis(500);
    deps.live_meter.set_db(non_floor_level);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    assert_eq!(state.status_state.meter_db, Some(non_floor_level));
    assert!(
        state.meter_floor_started_at.is_none(),
        "non-floor levels should clear floor tracking"
    );
}

#[test]
fn run_periodic_tasks_does_not_advance_spinner_when_not_processing() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Idle;
    timers.last_processing_tick = now - Duration::from_secs(1);
    let prior_tick = timers.last_processing_tick;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(state.processing_spinner_index, 0);
    assert_eq!(timers.last_processing_tick, prior_tick);
}

#[test]
fn run_periodic_tasks_advances_processing_spinner() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Processing;
    timers.last_processing_tick = now - Duration::from_millis(PROCESSING_SPINNER_TICK_MS + 5);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert!(state.status_state.message.starts_with("Processing "));
    assert_eq!(state.processing_spinner_index, 1);
    assert_eq!(timers.last_processing_tick, now);
}

#[test]
fn run_periodic_tasks_spinner_uses_modulo_for_frame_selection() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    let start_index = 5;
    let expected = crate::theme::processing_spinner_symbol(&state.theme.colors(), start_index);
    state.status_state.recording_state = RecordingState::Processing;
    state.processing_spinner_index = start_index;
    timers.last_processing_tick = now - Duration::from_secs(1);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(state.status_state.message, format!("Processing {expected}"));
}

#[test]
fn run_periodic_tasks_heartbeat_respects_recording_only_gate() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.hud_right_panel = HudRightPanel::Heartbeat;
    state.status_state.hud_right_panel_recording_only = true;
    state.status_state.recording_state = RecordingState::Idle;
    timers.last_heartbeat_tick = now - Duration::from_secs(2);
    let prior_tick = timers.last_heartbeat_tick;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(timers.last_heartbeat_tick, prior_tick);
}

#[test]
fn run_periodic_tasks_heartbeat_animates_when_recording_only_is_disabled() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.hud_right_panel = HudRightPanel::Heartbeat;
    state.status_state.hud_right_panel_recording_only = false;
    state.status_state.recording_state = RecordingState::Idle;
    timers.last_heartbeat_tick = now - Duration::from_secs(2);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(timers.last_heartbeat_tick, now);
}

#[test]
fn run_periodic_tasks_heartbeat_requires_full_interval() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.hud_right_panel = HudRightPanel::Heartbeat;
    state.status_state.hud_right_panel_recording_only = false;
    state.status_state.recording_state = RecordingState::Recording;
    timers.last_heartbeat_tick = now - Duration::from_millis(500);
    let prior_tick = timers.last_heartbeat_tick;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(timers.last_heartbeat_tick, prior_tick);
}

#[test]
fn run_periodic_tasks_heartbeat_only_runs_for_heartbeat_panel() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.hud_right_panel = HudRightPanel::Ribbon;
    state.status_state.hud_right_panel_recording_only = false;
    state.status_state.recording_state = RecordingState::Recording;
    timers.last_heartbeat_tick = now - Duration::from_secs(2);
    let prior_tick = timers.last_heartbeat_tick;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(timers.last_heartbeat_tick, prior_tick);
}

#[test]
fn run_periodic_tasks_wake_badge_does_not_pulse_redraw_while_listening() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}
    deps.wake_word_runtime
        .set_listener_active_override_for_tests(Some(true));

    let now = Instant::now();
    state.config.wake_word = true;
    state.ui.overlay_mode = OverlayMode::None;
    state.status_state.hud_style = HudStyle::Full;
    state.status_state.wake_word_state = WakeWordHudState::Listening;
    timers.last_wake_hud_tick = now - Duration::from_secs(1);
    let prior_tick = timers.last_wake_hud_tick;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    assert_eq!(timers.last_wake_hud_tick, prior_tick);
    assert!(
        writer_rx.try_recv().is_err(),
        "listening badge should stay steady without periodic pulse redraw"
    );
}

#[test]
fn run_periodic_tasks_clears_preview_and_status_at_deadline() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.transcript_preview = Some("preview".to_string());
    state.current_status = Some("busy".to_string());
    state.status_state.message = "busy".to_string();
    state.status_state.recording_state = RecordingState::Responding;
    timers.preview_clear_deadline = Some(now);
    timers.status_clear_deadline = Some(now);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert!(timers.preview_clear_deadline.is_none());
    assert!(state.status_state.transcript_preview.is_none());
    assert!(timers.status_clear_deadline.is_none());
    assert!(state.current_status.is_none());
    assert!(state.status_state.message.is_empty());
    assert_eq!(state.status_state.recording_state, RecordingState::Idle);
}

#[test]
fn run_periodic_tasks_expires_stale_latency_badge() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Idle;
    state.status_state.last_latency_ms = Some(1256);
    state.status_state.last_latency_speech_ms = Some(5200);
    state.status_state.last_latency_rtf_x1000 = Some(241);
    state.status_state.last_latency_updated_at = Some(now - Duration::from_secs(9));

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    assert!(state.status_state.last_latency_ms.is_none());
    assert!(state.status_state.last_latency_speech_ms.is_none());
    assert!(state.status_state.last_latency_rtf_x1000.is_none());
    assert!(state.status_state.last_latency_updated_at.is_none());
}

#[test]
fn run_periodic_tasks_keeps_fresh_latency_badge() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Idle;
    state.status_state.last_latency_ms = Some(320);
    state.status_state.last_latency_speech_ms = Some(1200);
    state.status_state.last_latency_rtf_x1000 = Some(266);
    state.status_state.last_latency_updated_at = Some(now - Duration::from_secs(2));

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    assert_eq!(state.status_state.last_latency_ms, Some(320));
    assert_eq!(state.status_state.last_latency_speech_ms, Some(1200));
    assert_eq!(state.status_state.last_latency_rtf_x1000, Some(266));
    assert_eq!(
        state.status_state.last_latency_updated_at,
        Some(now - Duration::from_secs(2))
    );
}

#[test]
fn run_periodic_tasks_expires_stale_latency_badge_at_exact_boundary() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    let now = Instant::now();
    state.status_state.recording_state = RecordingState::Idle;
    state.status_state.last_latency_ms = Some(444);
    state.status_state.last_latency_speech_ms = Some(1337);
    state.status_state.last_latency_rtf_x1000 = Some(333);
    state.status_state.last_latency_updated_at = Some(now - Duration::from_secs(8));

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    assert!(state.status_state.last_latency_ms.is_none());
    assert!(state.status_state.last_latency_speech_ms.is_none());
    assert!(state.status_state.last_latency_rtf_x1000.is_none());
    assert!(state.status_state.last_latency_updated_at.is_none());
}

#[test]
fn run_periodic_tasks_marks_wake_hud_unavailable_when_listener_is_not_active() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    let now = Instant::now();
    state.config.wake_word = true;
    state.status_state.wake_word_state = WakeWordHudState::Off;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);

    assert_eq!(
        state.status_state.wake_word_state,
        WakeWordHudState::Unavailable
    );
    assert!(
        state
            .current_status
            .as_deref()
            .is_some_and(|msg| msg.contains("Wake listener unavailable")),
        "wake listener startup failures should surface a user-visible status"
    );
    assert_eq!(timers.last_wake_hud_tick, now);
}

#[test]
fn run_periodic_tasks_does_not_start_auto_voice_when_disabled() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let _sigwinch = install_sigwinch_hooks(hook_take_sigwinch_false, hook_terminal_size_80x24);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.auto_voice_enabled = false;
    deps.auto_idle_timeout = Duration::ZERO;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());
    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));
    assert!(timers.last_auto_trigger_at.is_none());
}

#[test]
fn run_periodic_tasks_does_not_start_auto_voice_when_paused_by_user() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let _sigwinch = install_sigwinch_hooks(hook_take_sigwinch_false, hook_terminal_size_80x24);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.auto_voice_enabled = true;
    state.auto_voice_paused_by_user = true;
    deps.auto_idle_timeout = Duration::ZERO;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());
    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));
    assert!(timers.last_auto_trigger_at.is_none());
}

#[test]
fn run_periodic_tasks_does_not_start_auto_voice_while_wake_listener_is_active() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let _sigwinch = install_sigwinch_hooks(hook_take_sigwinch_false, hook_terminal_size_80x24);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.auto_voice_enabled = true;
    state.config.wake_word = true;
    deps.wake_word_runtime
        .set_listener_active_override_for_tests(Some(true));
    deps.auto_idle_timeout = Duration::ZERO;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());

    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));
    assert!(timers.last_auto_trigger_at.is_none());
}

#[test]
fn run_periodic_tasks_does_not_start_auto_voice_when_trigger_not_ready() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let _sigwinch = install_sigwinch_hooks(hook_take_sigwinch_false, hook_terminal_size_80x24);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.auto_voice_enabled = true;
    deps.auto_idle_timeout = Duration::from_secs(60);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());
    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));
    assert!(timers.last_auto_trigger_at.is_none());
}

#[test]
fn flush_pending_output_or_continue_handles_no_pending_output() {
    let (mut state, _timers, deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    assert!(flush_pending_output_or_continue(&mut state, &deps));
}

#[test]
fn flush_pending_output_or_continue_keeps_running_when_output_requeues() {
    let (mut state, _timers, deps, _writer_rx, _input_tx) = build_harness("cat", &[], 1);
    deps.writer_tx
        .try_send(WriterMessage::ClearStatus)
        .expect("fill bounded writer channel");
    state.pty_buffer.pending_output = Some(b"abc".to_vec());

    assert!(flush_pending_output_or_continue(&mut state, &deps));
    assert_eq!(state.pty_buffer.pending_output, Some(b"abc".to_vec()));
}

#[test]
fn flush_pending_output_or_continue_stops_when_writer_disconnected_and_output_drained() {
    let (mut state, _timers, deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    drop(writer_rx);
    state.pty_buffer.pending_output = Some(b"abc".to_vec());

    assert!(!flush_pending_output_or_continue(&mut state, &deps));
    assert!(state.pty_buffer.pending_output.is_none());
}

#[test]
fn flush_pending_output_or_continue_keeps_running_when_flush_succeeds() {
    let (mut state, _timers, deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pty_buffer.pending_output = Some(b"ok".to_vec());

    assert!(flush_pending_output_or_continue(&mut state, &deps));
    assert!(state.pty_buffer.pending_output.is_none());
}

#[test]
fn run_event_loop_flushes_pending_input_before_exit() {
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.pty_buffer.pending_input.push_back(b"hello".to_vec());
    state.pty_buffer.pending_input_bytes = 5;
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);
    assert!(state.pty_buffer.pending_input.is_empty());
    assert_eq!(state.pty_buffer.pending_input_offset, 0);
    assert_eq!(state.pty_buffer.pending_input_bytes, 0);
}

#[test]
fn run_event_loop_flushes_pending_output_even_when_writer_is_disconnected() {
    let (mut state, mut timers, mut deps, writer_rx, input_tx) = build_harness("cat", &[], 8);
    drop(writer_rx);
    state.pty_buffer.pending_output = Some(b"leftover".to_vec());
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);
    assert!(
        state.pty_buffer.pending_output.is_none(),
        "pending output should be consumed even when writer is disconnected"
    );
}

#[test]
fn run_event_loop_flushes_pending_output_on_success_path() {
    let (mut state, mut timers, mut deps, writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.pty_buffer.pending_output = Some(b"ok".to_vec());
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);
    assert!(state.pty_buffer.pending_output.is_none());
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("writer output")
    {
        WriterMessage::PtyOutput(bytes) => assert_eq!(bytes, b"ok".to_vec()),
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn run_event_loop_processes_multiple_input_events_before_exit() {
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    let initial_auto_voice = state.auto_voice_enabled;
    input_tx
        .send(InputEvent::ToggleAutoVoice)
        .expect("queue first auto-voice toggle");
    input_tx
        .send(InputEvent::ToggleAutoVoice)
        .expect("queue second auto-voice toggle");
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);
    assert!(
        state.auto_voice_enabled == initial_auto_voice,
        "both toggles should run before exit so auto-voice returns to its initial value"
    );
    assert!(
        state.status_state.auto_voice_enabled == initial_auto_voice,
        "status and runtime auto-voice state should stay aligned"
    );
}
