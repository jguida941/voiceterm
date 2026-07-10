use super::*;

#[test]
fn start_voice_capture_with_hook_propagates_hook_error() {
    let _capture = install_start_capture_hook(hook_start_capture_err);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let mut status_clear_deadline = None;
    let mut current_status = None;

    let result = start_voice_capture_with_hook(
        &mut deps.voice_manager,
        VoiceCaptureTrigger::Auto,
        &deps.writer_tx,
        &mut status_clear_deadline,
        &mut current_status,
        &mut state.status_state,
    );
    assert!(result.is_err());
}

#[test]
fn wake_word_detection_starts_capture_via_shared_trigger_path() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = true;

    input_dispatch::handle_wake_word_detection(
        &mut state,
        &mut timers,
        &mut deps,
        WakeWordEvent::Detected,
    );

    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 1));
    LAST_CAPTURE_TRIGGER.with(|last| {
        assert_eq!(last.get(), Some(VoiceCaptureTrigger::WakeWord));
    });
}

#[test]
fn wake_word_detection_logs_wake_capture_marker() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let _wake_log = install_wake_capture_log_hook(hook_wake_capture_log_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = true;

    input_dispatch::handle_wake_word_detection(
        &mut state,
        &mut timers,
        &mut deps,
        WakeWordEvent::Detected,
    );

    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 1));
    WAKE_CAPTURE_LOG_CALLS.with(|calls| assert_eq!(calls.get(), 1));
}

#[test]
fn manual_voice_trigger_does_not_log_wake_capture_marker() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let _wake_log = install_wake_capture_log_hook(hook_wake_capture_log_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::VoiceTrigger,
        &mut running,
    );

    assert!(running);
    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 1));
    WAKE_CAPTURE_LOG_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn manual_voice_trigger_starts_voice_capture_even_when_image_mode_enabled() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.image_mode = true;
    state.status_state.image_mode_enabled = true;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::VoiceTrigger,
        &mut running,
    );

    assert!(running);
    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 1));
    LAST_CAPTURE_TRIGGER.with(|last| {
        assert_eq!(last.get(), Some(VoiceCaptureTrigger::Manual));
    });
    assert!(state.current_status.is_none());
}

#[test]
fn image_capture_trigger_while_recording_sets_guard_status() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.recording_state = RecordingState::Recording;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::ImageCaptureTrigger,
        &mut running,
    );

    assert!(running);
    assert_eq!(
        state.current_status.as_deref(),
        Some("Finish voice capture first")
    );
}

#[test]
fn wake_word_detection_is_ignored_while_recording() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = true;
    state.status_state.recording_state = RecordingState::Recording;

    input_dispatch::handle_wake_word_detection(
        &mut state,
        &mut timers,
        &mut deps,
        WakeWordEvent::Detected,
    );

    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn wake_word_detection_still_triggers_when_auto_voice_is_paused_by_user() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = true;
    state.auto_voice_enabled = true;
    state.status_state.auto_voice_enabled = true;
    state.status_state.voice_mode = VoiceMode::Auto;
    state.auto_voice_paused_by_user = true;

    input_dispatch::handle_wake_word_detection(
        &mut state,
        &mut timers,
        &mut deps,
        WakeWordEvent::Detected,
    );

    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 1));
    assert!(
        !state.auto_voice_paused_by_user,
        "wake trigger should resume auto mode after manual pause"
    );
}

#[test]
fn wake_word_send_intent_submits_staged_insert_text() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = true;
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.insert_pending_send = true;

    input_dispatch::handle_wake_word_detection(
        &mut state,
        &mut timers,
        &mut deps,
        WakeWordEvent::SendStagedInput,
    );

    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 1));
    assert!(!state.status_state.insert_pending_send);
}

#[test]
fn wake_word_send_intent_without_staged_text_sets_status() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = true;
    state.config.voice_send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.send_mode = crate::config::VoiceSendMode::Insert;
    state.status_state.insert_pending_send = false;

    input_dispatch::handle_wake_word_detection(
        &mut state,
        &mut timers,
        &mut deps,
        WakeWordEvent::SendStagedInput,
    );

    assert_eq!(state.current_status.as_deref(), Some("Nothing to send"));
}

#[test]
fn wake_word_send_intent_in_auto_mode_submits_enter_without_pending_flag() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = true;
    state.config.voice_send_mode = crate::config::VoiceSendMode::Auto;
    state.status_state.send_mode = crate::config::VoiceSendMode::Auto;
    state.status_state.insert_pending_send = false;

    input_dispatch::handle_wake_word_detection(
        &mut state,
        &mut timers,
        &mut deps,
        WakeWordEvent::SendStagedInput,
    );

    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 1));
    assert!(state.current_status.is_none());
    assert!(!state.status_state.insert_pending_send);
}

#[test]
fn manual_voice_trigger_while_recording_uses_cancel_capture_path() {
    let _cancel = install_cancel_capture_hook(hook_cancel_capture_true);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.recording_state = RecordingState::Recording;
    state.current_status = None;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::VoiceTrigger,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.status_state.recording_state, RecordingState::Idle);
    assert_eq!(state.current_status.as_deref(), Some("Capture stopped"));
    CANCEL_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 1));
}

#[test]
fn manual_voice_trigger_in_auto_mode_pauses_then_resumes_with_explicit_restart() {
    let _cancel = install_cancel_capture_hook(hook_cancel_capture_true);
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let _sigwinch = install_sigwinch_hooks(hook_take_sigwinch_false, hook_terminal_size_80x24);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.auto_voice_enabled = true;
    state.status_state.auto_voice_enabled = true;
    state.status_state.voice_mode = VoiceMode::Auto;
    state.status_state.recording_state = RecordingState::Recording;
    deps.auto_idle_timeout = Duration::ZERO;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::VoiceTrigger,
        &mut running,
    );
    assert!(running);
    assert!(state.auto_voice_paused_by_user);
    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));

    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());
    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::VoiceTrigger,
        &mut running,
    );
    assert!(running);
    assert!(!state.auto_voice_paused_by_user);
    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 1));
}

#[test]
fn manual_voice_trigger_cancel_failure_keeps_recording() {
    let _cancel = install_cancel_capture_hook(hook_cancel_capture_false);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.recording_state = RecordingState::Recording;
    state.current_status = None;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::VoiceTrigger,
        &mut running,
    );

    assert!(running);
    assert_eq!(
        state.status_state.recording_state,
        RecordingState::Recording,
        "failed cancel should keep recording state"
    );
    assert!(state.current_status.is_none());
    CANCEL_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 1));
}

#[test]
fn wake_word_detection_while_recording_does_not_use_cancel_capture_path() {
    let _cancel = install_cancel_capture_hook(hook_cancel_capture_true);
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = true;
    state.status_state.recording_state = RecordingState::Recording;

    input_dispatch::handle_wake_word_detection(
        &mut state,
        &mut timers,
        &mut deps,
        WakeWordEvent::Detected,
    );

    assert_eq!(
        state.status_state.recording_state,
        RecordingState::Recording
    );
    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));
    CANCEL_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn wake_word_detection_is_ignored_when_disabled() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = false;

    input_dispatch::handle_wake_word_detection(
        &mut state,
        &mut timers,
        &mut deps,
        WakeWordEvent::Detected,
    );

    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn wake_word_detection_is_ignored_when_overlay_is_open() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = true;
    state.ui.overlay_mode = OverlayMode::Settings;

    input_dispatch::handle_wake_word_detection(
        &mut state,
        &mut timers,
        &mut deps,
        WakeWordEvent::Detected,
    );

    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}
