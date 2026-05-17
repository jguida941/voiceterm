use super::*;

#[test]
fn run_event_loop_does_not_run_periodic_before_first_tick() {
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::None;
    state.theme_studio.picker_digits = "12".to_string();
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);
    assert_eq!(state.theme_studio.picker_digits, "12");
}

#[test]
fn handle_input_event_bytes_marks_insert_mode_pending_send() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"status".to_vec()),
        &mut running,
    );

    assert!(running);
    assert!(state.status_state.insert_pending_send);
}

#[test]
fn suppress_startup_escape_only_blocks_arrow_noise_when_enabled() {
    {
        let _hook = install_try_send_hook(hook_count_writes);
        let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
        state.ui.suppress_startup_escape_input = true;
        let mut running = true;
        handle_input_event(
            &mut state,
            &mut timers,
            &mut deps,
            InputEvent::Bytes(b"\x1b[A".to_vec()),
            &mut running,
        );
        assert!(running);
        HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 0));
    }

    {
        let _hook = install_try_send_hook(hook_count_writes);
        let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
        state.ui.suppress_startup_escape_input = false;
        state.status_state.hud_button_focus = None;
        let mut running = true;
        handle_input_event(
            &mut state,
            &mut timers,
            &mut deps,
            InputEvent::Bytes(b"\x1b[A".to_vec()),
            &mut running,
        );
        assert!(running);
        assert!(state.status_state.hud_button_focus.is_none());
        HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 1));
    }
}

#[test]
fn arrow_left_and_right_focus_different_buttons_from_none() {
    let (mut left_state, mut left_timers, mut left_deps, _left_writer_rx, _left_input_tx) =
        build_harness("cat", &[], 8);
    left_state.status_state.hud_button_focus = None;
    let mut running = true;
    handle_input_event(
        &mut left_state,
        &mut left_timers,
        &mut left_deps,
        InputEvent::Bytes(b"\x1b[D".to_vec()),
        &mut running,
    );
    assert!(running);
    let left_focus = left_state.status_state.hud_button_focus;
    assert!(left_focus.is_some(), "left arrow should set focus");

    let (mut right_state, mut right_timers, mut right_deps, _right_writer_rx, _right_input_tx) =
        build_harness("cat", &[], 8);
    right_state.status_state.hud_button_focus = None;
    let mut running = true;
    handle_input_event(
        &mut right_state,
        &mut right_timers,
        &mut right_deps,
        InputEvent::Bytes(b"\x1b[C".to_vec()),
        &mut running,
    );
    assert!(running);
    let right_focus = right_state.status_state.hud_button_focus;
    assert!(right_focus.is_some(), "right arrow should set focus");
    assert_ne!(left_focus, right_focus);
}

#[test]
fn insert_mode_with_pending_text_forwards_left_and_right_arrows_to_pty() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.insert_pending_send = true;
    state.status_state.hud_button_focus = Some(ButtonAction::ToggleSendMode);
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[D".to_vec()),
        &mut running,
    );
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[C".to_vec()),
        &mut running,
    );

    assert!(running);
    assert!(state.status_state.hud_button_focus.is_none());
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 2));
}

#[test]
fn insert_mode_without_pending_text_keeps_hud_arrow_focus_navigation() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.insert_pending_send = false;
    state.status_state.hud_button_focus = None;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[D".to_vec()),
        &mut running,
    );

    assert!(running);
    assert!(state.status_state.hud_button_focus.is_some());
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn up_arrow_without_hud_focus_is_forwarded_to_pty() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.hud_button_focus = None;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[A".to_vec()),
        &mut running,
    );

    assert!(running);
    assert!(state.status_state.hud_button_focus.is_none());
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 1));
}

#[test]
fn insert_mode_with_pending_text_forwards_up_and_down_to_pty() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.insert_pending_send = true;
    state.status_state.hud_button_focus = None;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[A".to_vec()),
        &mut running,
    );
    let focus_after_up = state.status_state.hud_button_focus;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[B".to_vec()),
        &mut running,
    );

    assert!(running);
    assert!(focus_after_up.is_none());
    assert!(state.status_state.hud_button_focus.is_none());
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 2));
}

#[test]
fn up_and_down_forward_to_pty_even_when_hud_focus_is_active() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.hud_button_focus = Some(ButtonAction::ToggleSendMode);
    let mut running = true;

    // Up arrow with active HUD focus should pass through to PTY, not navigate HUD.
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[A".to_vec()),
        &mut running,
    );
    assert!(running);
    assert!(
        state.status_state.hud_button_focus.is_none(),
        "Up must clear HUD focus and forward to PTY"
    );
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 1, "Up must write to PTY"));

    // Set focus again to test Down arrow.
    state.status_state.hud_button_focus = Some(ButtonAction::ToggleSendMode);
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[B".to_vec()),
        &mut running,
    );
    assert!(running);
    assert!(
        state.status_state.hud_button_focus.is_none(),
        "Down must clear HUD focus and forward to PTY"
    );
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 2, "Down must write to PTY"));
}

#[test]
fn settings_overlay_up_down_navigates_menu_locally() {
    // Proves open vertical overlays still consume Up/Down locally after the
    // closed-HUD input ownership change that reserves Up/Down for the PTY.
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::Settings;
    let initial_selected = state.settings.menu.selected;
    while writer_rx.try_recv().is_ok() {}

    let mut running = true;

    // Down arrow should move selection within Settings, not forward to PTY.
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[B".to_vec()),
        &mut running,
    );
    assert!(running);
    assert_eq!(
        state.ui.overlay_mode,
        OverlayMode::Settings,
        "overlay must stay open"
    );
    assert_ne!(
        state.settings.menu.selected, initial_selected,
        "Down arrow must navigate Settings menu"
    );
    let after_down = state.settings.menu.selected;

    // Up arrow should move back.
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[A".to_vec()),
        &mut running,
    );
    assert!(running);
    assert_eq!(
        state.ui.overlay_mode,
        OverlayMode::Settings,
        "overlay must stay open"
    );
    assert_ne!(
        state.settings.menu.selected, after_down,
        "Up arrow must navigate Settings menu"
    );
    // No PTY writes: overlay consumed the arrows.
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 0, "overlay must not forward arrows to PTY"));
}

#[test]
fn insert_mode_empty_bytes_do_not_mark_pending_send() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.insert_pending_send = false;
    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(Vec::new()),
        &mut running,
    );
    assert!(running);
    assert!(!state.status_state.insert_pending_send);
}

#[test]
fn empty_bytes_keep_claude_prompt_suppression_enabled() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let mut running = true;

    super::prompt_occlusion::apply_prompt_suppression(&mut state, &mut deps, true);
    assert!(state.status_state.prompt_suppressed);
    timers.prompt_suppression_release_not_before = Some(Instant::now() + Duration::from_secs(3));

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(Vec::new()),
        &mut running,
    );

    assert!(running);
    assert!(state.status_state.prompt_suppressed);
}

#[test]
fn non_confirmation_bytes_keep_claude_prompt_suppression() {
    for bytes in [
        b"x".as_slice(),
        b"a".as_slice(),
        b"d".as_slice(),
        b"q".as_slice(),
    ] {
        let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
        state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
        let mut running = true;

        let detected = state
            .prompt
            .occlusion_detector
            .feed_output(b"Do you want to proceed? (y/n)\n");
        assert!(detected);
        super::prompt_occlusion::apply_prompt_suppression(&mut state, &mut deps, true);
        assert!(state.status_state.prompt_suppressed);
        timers.prompt_suppression_release_not_before =
            Some(Instant::now() + Duration::from_secs(3));

        handle_input_event(
            &mut state,
            &mut timers,
            &mut deps,
            InputEvent::Bytes(bytes.to_vec()),
            &mut running,
        );

        assert!(running);
        assert!(state.status_state.prompt_suppressed);
    }
}

#[test]
fn confirmation_bytes_defer_claude_prompt_clear_until_periodic_tick() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    let mut running = true;

    let detected = state
        .prompt
        .occlusion_detector
        .feed_output(b"Do you want to proceed? (y/n)\n");
    assert!(detected);
    super::prompt_occlusion::apply_prompt_suppression(&mut state, &mut deps, true);
    assert!(state.status_state.prompt_suppressed);
    timers.prompt_suppression_release_not_before = Some(Instant::now() + Duration::from_secs(3));

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"y".to_vec()),
        &mut running,
    );

    assert!(running);
    // Input marks detector resolved, but suppression is cleared on the next loop tick
    // to avoid same-frame redraw collisions with backend approval UI repaint.
    assert!(state.status_state.prompt_suppressed);
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
}

#[test]
fn startup_ready_marker_release_is_debounced_before_unsuppress() {
    let _rolling = install_prompt_rolling_override(true);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);

    state.prompt.occlusion_detector.activate_startup_guard();
    super::prompt_occlusion::apply_prompt_suppression(&mut state, &mut deps, true);
    assert!(state.status_state.prompt_suppressed);

    let mut running = true;
    // Startup-ready markers should arm release, not clear suppression
    // immediately, so JetBrains startup redraw bursts cannot flap state.
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        "❯ Try \"fix typecheck errors\"\n? for shortcuts\n"
            .as_bytes()
            .to_vec(),
        &mut running,
    );
    assert!(running);
    assert!(state.status_state.prompt_suppressed);
    assert!(timers.prompt_suppression_release_not_before.is_some());

    let now = Instant::now();
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_millis(300),
    );
    assert!(state.status_state.prompt_suppressed);

    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_millis(1200),
    );
    assert!(!state.status_state.prompt_suppressed);
}

#[test]
fn numeric_approval_choice_defer_claude_prompt_clear_until_periodic_tick() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    let mut running = true;

    let detected = state
        .prompt
        .occlusion_detector
        .feed_output(
            b"This command requires approval\nDo you want to proceed?\n1. Yes\n2. Yes, and don't ask again for: test:*\n3. No\n",
        );
    assert!(detected);
    super::prompt_occlusion::apply_prompt_suppression(&mut state, &mut deps, true);
    assert!(state.status_state.prompt_suppressed);
    timers.prompt_suppression_release_not_before = Some(Instant::now() + Duration::from_secs(3));

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"2".to_vec()),
        &mut running,
    );

    assert!(running);
    assert!(state.status_state.prompt_suppressed);
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
}

#[test]
fn enter_key_defer_claude_prompt_clear_until_periodic_tick() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    let mut running = true;

    let detected = state
        .prompt
        .occlusion_detector
        .feed_output(b"Do you want to proceed? (y/n)\n");
    assert!(detected);
    super::prompt_occlusion::apply_prompt_suppression(&mut state, &mut deps, true);
    assert!(state.status_state.prompt_suppressed);
    timers.prompt_suppression_release_not_before = Some(Instant::now() + Duration::from_secs(3));

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert!(state.status_state.prompt_suppressed);
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
}

#[test]
fn enter_key_resolution_does_not_re_suppress_on_empty_output() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.ui.terminal_rows = 24;
    state.ui.terminal_cols = 80;
    let mut running = true;

    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"Do you want to proceed? (y/n)\n".to_vec(),
        &mut running,
    );
    assert!(running);
    assert!(state.status_state.prompt_suppressed);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    assert!(running);

    let now = Instant::now();
    run_periodic_tasks(
        &mut state,
        &mut timers,
        &mut deps,
        now + Duration::from_secs(4),
    );
    assert!(!state.status_state.prompt_suppressed);

    // Empty output should not re-trigger suppression from stale detector buffers.
    handle_output_chunk(&mut state, &mut timers, &mut deps, Vec::new(), &mut running);
    assert!(running);
    assert!(!state.status_state.prompt_suppressed);
}

#[test]
fn reply_composer_marker_does_not_enable_prompt_suppression() {
    let (mut state, _timers, _deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    let detected = state.prompt.occlusion_detector.feed_output("❯ ".as_bytes());
    assert!(!detected);
    assert!(!state.prompt.occlusion_detector.should_suppress_hud());
}

#[test]
fn codex_generate_command_hint_does_not_enable_prompt_suppression() {
    let (mut state, _timers, _deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.prompt.occlusion_detector = crate::prompt::PromptOcclusionDetector::new(true);
    let detected = state
        .prompt
        .occlusion_detector
        .feed_output("⌘K to generate command".as_bytes());
    assert!(!detected);
    assert!(!state.prompt.occlusion_detector.should_suppress_hud());
}

#[test]
fn send_staged_text_processing_insert_mode_consumes_without_status_or_write() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.recording_state = RecordingState::Processing;
    state.status_state.insert_pending_send = false;
    state.current_status = None;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::SendStagedText,
        &mut running,
    );

    assert!(running);
    assert!(state.current_status.is_none());
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn send_staged_text_outside_insert_mode_stops_on_pty_error() {
    let _hook = install_try_send_hook(hook_broken_pipe);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.voice_send_mode = crate::config::VoiceSendMode::Auto;
    state.status_state.send_mode = crate::config::VoiceSendMode::Auto;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::SendStagedText,
        &mut running,
    );
    assert!(!running);
}

#[test]
fn decrease_sensitivity_event_moves_threshold_down() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.sensitivity_db = -50.0;
    state.config.app.voice_vad_threshold_db = -50.0;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::DecreaseSensitivity,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.status_state.sensitivity_db, -60.0);
}

#[test]
fn enter_key_non_theme_focus_keeps_theme_picker_digits() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.hud_button_focus = Some(ButtonAction::ToggleSendMode);
    state.theme_studio.picker_digits = "12".to_string();
    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    assert!(running);
    assert_eq!(state.theme_studio.picker_digits, "12");
}

#[test]
fn enter_key_with_auto_focus_submits_terminal_input_without_toggling_auto_mode() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.auto_voice_enabled = false;
    state.status_state.auto_voice_enabled = false;
    state.status_state.voice_mode = VoiceMode::Manual;
    state.status_state.hud_button_focus = Some(ButtonAction::ToggleAutoVoice);
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert!(!state.auto_voice_enabled);
    assert!(!state.status_state.auto_voice_enabled);
    assert_eq!(state.status_state.voice_mode, VoiceMode::Manual);
    assert!(state.status_state.hud_button_focus.is_none());
    assert!(timers.last_enter_at.is_some());
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 1));
}

#[test]
fn mouse_click_non_theme_button_keeps_theme_picker_digits() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    update_button_registry(
        &deps.button_registry,
        &state.status_state,
        state.ui.overlay_mode,
        state.ui.terminal_cols,
        state.theme,
    );
    let (x, y) = hud_button_click_coords(&state, &deps, ButtonAction::ToggleSendMode);
    state.theme_studio.picker_digits = "12".to_string();

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x, y },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.theme_studio.picker_digits, "12");
}

#[test]
fn full_hud_single_line_mouse_click_bottom_row_triggers_button_action() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.hud_style = HudStyle::Full;
    state.status_state.full_hud_single_line = true;
    state.status_state.send_mode = crate::config::VoiceSendMode::Auto;
    state.config.voice_send_mode = crate::config::VoiceSendMode::Auto;

    update_button_registry(
        &deps.button_registry,
        &state.status_state,
        state.ui.overlay_mode,
        state.ui.terminal_cols,
        state.theme,
    );
    let button = deps
        .button_registry
        .all_buttons()
        .into_iter()
        .find(|button| button.event == ButtonAction::ToggleSendMode)
        .expect("toggle-send button should be registered");
    let x = button.start_x + (button.end_x.saturating_sub(button.start_x) / 2);
    let y = state.ui.terminal_rows;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x, y },
        &mut running,
    );

    assert!(running);
    assert_eq!(
        state.status_state.send_mode,
        crate::config::VoiceSendMode::Insert
    );
    assert_eq!(
        state.config.voice_send_mode,
        crate::config::VoiceSendMode::Insert
    );
}
