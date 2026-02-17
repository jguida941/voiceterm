use super::*;
use clap::Parser;
use crossbeam_channel::{bounded, Receiver, Sender};
use std::cell::Cell;
use std::collections::VecDeque;
use std::io;
use voiceterm::pty_session::PtyOverlaySession;

use crate::buttons::ButtonRegistry;
use crate::config::HudStyle;
use crate::config::OverlayConfig;
use crate::prompt::{PromptLogger, PromptTracker};
use crate::session_stats::SessionStats;
use crate::settings::SettingsMenuState;
use crate::status_line::{Pipeline, StatusLineState, VoiceMode, WakeWordHudState};
use crate::theme::Theme;
use crate::theme_ops::theme_index_from_theme;
use crate::voice_control::VoiceManager;
use crate::voice_macros::VoiceMacros;
use crate::wake_word::WakeWordRuntime;

thread_local! {
    static HOOK_CALLS: Cell<usize> = const { Cell::new(0) };
    static START_CAPTURE_CALLS: Cell<usize> = const { Cell::new(0) };
    static EARLY_STOP_CALLS: Cell<usize> = const { Cell::new(0) };
}

struct TrySendHookGuard;

impl Drop for TrySendHookGuard {
    fn drop(&mut self) {
        set_try_send_hook(None);
        HOOK_CALLS.with(|calls| calls.set(0));
    }
}

fn install_try_send_hook(hook: TrySendHook) -> TrySendHookGuard {
    set_try_send_hook(Some(hook));
    HOOK_CALLS.with(|calls| calls.set(0));
    TrySendHookGuard
}

struct SigwinchHookGuard;

impl Drop for SigwinchHookGuard {
    fn drop(&mut self) {
        set_take_sigwinch_hook(None);
        set_terminal_size_hook(None);
    }
}

fn install_sigwinch_hooks(
    take_hook: TakeSigwinchHook,
    size_hook: TerminalSizeHook,
) -> SigwinchHookGuard {
    set_take_sigwinch_hook(Some(take_hook));
    set_terminal_size_hook(Some(size_hook));
    SigwinchHookGuard
}

struct StartCaptureHookGuard;

impl Drop for StartCaptureHookGuard {
    fn drop(&mut self) {
        set_start_capture_hook(None);
        START_CAPTURE_CALLS.with(|calls| calls.set(0));
    }
}

fn install_start_capture_hook(hook: StartCaptureHook) -> StartCaptureHookGuard {
    set_start_capture_hook(Some(hook));
    START_CAPTURE_CALLS.with(|calls| calls.set(0));
    StartCaptureHookGuard
}

struct EarlyStopHookGuard;

impl Drop for EarlyStopHookGuard {
    fn drop(&mut self) {
        set_request_early_stop_hook(None);
        EARLY_STOP_CALLS.with(|calls| calls.set(0));
    }
}

fn install_request_early_stop_hook(hook: RequestEarlyStopHook) -> EarlyStopHookGuard {
    set_request_early_stop_hook(Some(hook));
    EARLY_STOP_CALLS.with(|calls| calls.set(0));
    EarlyStopHookGuard
}

fn hook_would_block(_: &[u8]) -> io::Result<usize> {
    Err(io::Error::new(ErrorKind::WouldBlock, "hook would block"))
}

fn hook_interrupted(_: &[u8]) -> io::Result<usize> {
    Err(io::Error::new(ErrorKind::Interrupted, "hook interrupted"))
}

fn hook_broken_pipe(_: &[u8]) -> io::Result<usize> {
    Err(io::Error::new(ErrorKind::BrokenPipe, "hook broken pipe"))
}

fn hook_non_empty_full_write(bytes: &[u8]) -> io::Result<usize> {
    if bytes.is_empty() {
        Err(io::Error::new(
            ErrorKind::BrokenPipe,
            "unexpected empty write",
        ))
    } else {
        Ok(bytes.len())
    }
}

fn hook_one_byte(bytes: &[u8]) -> io::Result<usize> {
    if bytes.is_empty() {
        Ok(0)
    } else {
        Ok(1)
    }
}

fn hook_partial_then_would_block(bytes: &[u8]) -> io::Result<usize> {
    HOOK_CALLS.with(|calls| {
        let call_index = calls.get();
        calls.set(call_index + 1);
        if call_index == 0 {
            if bytes.is_empty() {
                Ok(0)
            } else {
                Ok(1)
            }
        } else {
            Err(io::Error::new(ErrorKind::WouldBlock, "hook would block"))
        }
    })
}

fn hook_count_writes(bytes: &[u8]) -> io::Result<usize> {
    HOOK_CALLS.with(|calls| calls.set(calls.get() + 1));
    Ok(bytes.len())
}

fn hook_take_sigwinch_true() -> bool {
    true
}

fn hook_take_sigwinch_false() -> bool {
    false
}

fn hook_terminal_size_80x24() -> io::Result<(u16, u16)> {
    Ok((80, 24))
}

fn hook_start_capture_count(
    _: &mut crate::voice_control::VoiceManager,
    _: VoiceCaptureTrigger,
    _: &crossbeam_channel::Sender<WriterMessage>,
    _: &mut Option<Instant>,
    _: &mut Option<String>,
    _: &mut crate::status_line::StatusLineState,
) -> anyhow::Result<()> {
    START_CAPTURE_CALLS.with(|calls| calls.set(calls.get() + 1));
    Ok(())
}

fn hook_start_capture_err(
    _: &mut crate::voice_control::VoiceManager,
    _: VoiceCaptureTrigger,
    _: &crossbeam_channel::Sender<WriterMessage>,
    _: &mut Option<Instant>,
    _: &mut Option<String>,
    _: &mut crate::status_line::StatusLineState,
) -> anyhow::Result<()> {
    Err(anyhow::anyhow!("forced start capture failure"))
}

fn hook_request_early_stop_true(_: &mut crate::voice_control::VoiceManager) -> bool {
    EARLY_STOP_CALLS.with(|calls| calls.set(calls.get() + 1));
    true
}

fn build_harness(
    cmd: &str,
    args: &[&str],
    writer_capacity: usize,
) -> (
    EventLoopState,
    EventLoopTimers,
    EventLoopDeps,
    Receiver<WriterMessage>,
    Sender<InputEvent>,
) {
    let config = OverlayConfig::parse_from(["voiceterm"]);
    let mut status_state = StatusLineState::new();
    let auto_voice_enabled = config.auto_voice;
    status_state.sensitivity_db = config.app.voice_vad_threshold_db;
    status_state.auto_voice_enabled = auto_voice_enabled;
    status_state.send_mode = config.voice_send_mode;
    status_state.latency_display = config.latency_display;
    status_state.macros_enabled = false;
    status_state.hud_right_panel = config.hud_right_panel;
    status_state.hud_border_style = config.hud_border_style;
    status_state.hud_right_panel_recording_only = config.hud_right_panel_recording_only;
    status_state.hud_style = config.hud_style;
    status_state.voice_mode = if auto_voice_enabled {
        VoiceMode::Auto
    } else {
        VoiceMode::Manual
    };
    status_state.pipeline = Pipeline::Rust;
    status_state.mouse_enabled = true;

    let theme = Theme::Codex;
    let prompt_tracker = PromptTracker::new(None, true, PromptLogger::new(None));
    let voice_manager = VoiceManager::new(config.app.clone());
    let wake_word_runtime = WakeWordRuntime::new(config.app.clone());
    let wake_word_rx = wake_word_runtime.receiver();
    let live_meter = voice_manager.meter();
    let arg_vec: Vec<String> = args.iter().map(|arg| (*arg).to_string()).collect();
    let session =
        PtyOverlaySession::new(cmd, ".", &arg_vec, "xterm-256color").expect("start pty session");

    let (writer_tx, writer_rx) = bounded(writer_capacity);
    let (input_tx, input_rx) = bounded(16);

    let state = EventLoopState {
        config,
        status_state,
        auto_voice_enabled,
        theme,
        overlay_mode: OverlayMode::None,
        settings_menu: SettingsMenuState::new(),
        meter_levels: VecDeque::with_capacity(METER_HISTORY_MAX),
        theme_picker_selected: theme_index_from_theme(theme),
        theme_picker_digits: String::new(),
        current_status: None,
        pending_transcripts: VecDeque::new(),
        session_stats: SessionStats::new(),
        prompt_tracker,
        terminal_rows: 24,
        terminal_cols: 80,
        last_recording_duration: 0.0,
        meter_floor_started_at: None,
        processing_spinner_index: 0,
        pending_pty_output: None,
        pending_pty_input: VecDeque::new(),
        pending_pty_input_offset: 0,
        pending_pty_input_bytes: 0,
        suppress_startup_escape_input: false,
        force_send_on_next_transcript: false,
    };

    let now = Instant::now();
    let timers = EventLoopTimers {
        theme_picker_digit_deadline: None,
        status_clear_deadline: None,
        preview_clear_deadline: None,
        last_auto_trigger_at: None,
        last_enter_at: None,
        recording_started_at: None,
        last_recording_update: now,
        last_processing_tick: now,
        last_heartbeat_tick: now,
        last_meter_update: now,
        last_wake_hud_tick: now,
    };

    let deps = EventLoopDeps {
        session,
        voice_manager,
        wake_word_runtime,
        wake_word_rx,
        writer_tx,
        input_rx,
        button_registry: ButtonRegistry::new(),
        backend_label: "test".to_string(),
        sound_on_complete: false,
        sound_on_error: false,
        live_meter,
        meter_update_ms: 50,
        auto_idle_timeout: Duration::from_millis(300),
        transcript_idle_timeout: Duration::from_millis(100),
        voice_macros: VoiceMacros::default(),
    };

    (state, timers, deps, writer_rx, input_tx)
}

#[test]
fn flush_pending_pty_output_returns_true_when_empty() {
    let (mut state, _timers, deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    assert!(flush_pending_pty_output(&mut state, &deps));
}

#[test]
fn flush_pending_pty_output_requeues_when_writer_is_full() {
    let (mut state, _timers, deps, _writer_rx, _input_tx) = build_harness("cat", &[], 1);
    deps.writer_tx
        .try_send(WriterMessage::ClearStatus)
        .expect("fill bounded writer channel");
    state.pending_pty_output = Some(vec![1, 2, 3]);

    assert!(!flush_pending_pty_output(&mut state, &deps));
    assert_eq!(state.pending_pty_output, Some(vec![1, 2, 3]));
}

#[test]
fn flush_pending_pty_output_returns_false_when_writer_is_disconnected() {
    let (mut state, _timers, deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    drop(writer_rx);
    state.pending_pty_output = Some(vec![9, 8, 7]);

    assert!(!flush_pending_pty_output(&mut state, &deps));
    assert!(
        state.pending_pty_output.is_none(),
        "disconnected writes should not keep stale pending output"
    );
}

#[test]
fn flush_pending_pty_input_empty_queue_resets_counters() {
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pending_pty_input_offset = 3;
    state.pending_pty_input_bytes = 9;

    assert!(flush_pending_pty_input(&mut state, &mut deps));
    assert_eq!(state.pending_pty_input_offset, 0);
    assert_eq!(state.pending_pty_input_bytes, 0);
}

#[test]
fn flush_pending_pty_input_pops_front_when_offset_reaches_chunk_end() {
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pending_pty_input.push_back(vec![1, 2]);
    state.pending_pty_input.push_back(vec![3]);
    state.pending_pty_input_offset = 2;
    state.pending_pty_input_bytes = 1;

    assert!(flush_pending_pty_input(&mut state, &mut deps));
    assert!(state.pending_pty_input.is_empty());
    assert_eq!(state.pending_pty_input_offset, 0);
    assert_eq!(state.pending_pty_input_bytes, 0);
}

#[test]
fn event_loop_constants_match_expected_limits() {
    assert_eq!(METER_DB_FLOOR, -60.0);
    assert_eq!(PTY_INPUT_MAX_BUFFER_BYTES, 256 * 1024);
}

#[test]
fn flush_pending_pty_input_treats_would_block_as_retryable() {
    let _hook = install_try_send_hook(hook_would_block);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pending_pty_input.push_back(vec![1, 2, 3]);
    state.pending_pty_input_bytes = 3;

    assert!(flush_pending_pty_input(&mut state, &mut deps));
    assert_eq!(state.pending_pty_input_offset, 0);
    assert_eq!(state.pending_pty_input_bytes, 3);
    assert_eq!(state.pending_pty_input.len(), 1);
}

#[test]
fn flush_pending_pty_input_treats_interrupted_as_retryable() {
    let _hook = install_try_send_hook(hook_interrupted);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pending_pty_input.push_back(vec![7, 8]);
    state.pending_pty_input_bytes = 2;

    assert!(flush_pending_pty_input(&mut state, &mut deps));
    assert_eq!(state.pending_pty_input_offset, 0);
    assert_eq!(state.pending_pty_input_bytes, 2);
    assert_eq!(state.pending_pty_input.len(), 1);
}

#[test]
fn flush_pending_pty_input_returns_false_for_non_retry_errors() {
    let _hook = install_try_send_hook(hook_broken_pipe);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pending_pty_input.push_back(vec![7, 8]);
    state.pending_pty_input_bytes = 2;

    assert!(!flush_pending_pty_input(&mut state, &mut deps));
}

#[test]
fn flush_pending_pty_input_does_not_write_empty_slice_when_offset_is_at_chunk_end() {
    let _hook = install_try_send_hook(hook_non_empty_full_write);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pending_pty_input.push_back(vec![1, 2]);
    state.pending_pty_input_offset = 2;
    state.pending_pty_input_bytes = 0;

    assert!(flush_pending_pty_input(&mut state, &mut deps));
    assert!(state.pending_pty_input.is_empty());
}

#[test]
fn flush_pending_pty_input_drains_many_single_byte_chunks_within_attempt_budget() {
    let _hook = install_try_send_hook(hook_one_byte);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    for _ in 0..12 {
        state.pending_pty_input.push_back(vec![b'x']);
    }
    state.pending_pty_input_bytes = 12;

    assert!(flush_pending_pty_input(&mut state, &mut deps));
    assert!(
        state.pending_pty_input.is_empty(),
        "single-byte writes should clear this queue within 16 attempts"
    );
    assert_eq!(state.pending_pty_input_bytes, 0);
}

#[test]
fn write_or_queue_pty_input_queues_remainder_after_partial_write() {
    let _hook = install_try_send_hook(hook_partial_then_would_block);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let bytes = vec![1, 2, 3, 4];

    assert!(write_or_queue_pty_input(&mut state, &mut deps, bytes));
    assert_eq!(state.pending_pty_input_bytes, 3);
    assert_eq!(state.pending_pty_input.len(), 1);
    assert_eq!(state.pending_pty_input.front(), Some(&vec![2, 3, 4]));
}

#[test]
fn write_or_queue_pty_input_queues_all_bytes_on_would_block() {
    let _hook = install_try_send_hook(hook_would_block);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let bytes = vec![1, 2, 3];

    assert!(write_or_queue_pty_input(
        &mut state,
        &mut deps,
        bytes.clone()
    ));
    assert_eq!(state.pending_pty_input_bytes, bytes.len());
    assert_eq!(state.pending_pty_input.front(), Some(&bytes));
}

#[test]
fn write_or_queue_pty_input_returns_false_on_non_retryable_error() {
    let _hook = install_try_send_hook(hook_broken_pipe);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);

    assert!(!write_or_queue_pty_input(
        &mut state,
        &mut deps,
        vec![1, 2, 3]
    ));
    assert!(
        state.pending_pty_input.is_empty(),
        "non-retry errors should not queue bytes"
    );
    assert_eq!(state.pending_pty_input_bytes, 0);
}

#[test]
fn write_or_queue_pty_input_returns_true_for_live_session() {
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let bytes = b"hello".to_vec();

    assert!(write_or_queue_pty_input(&mut state, &mut deps, bytes));
    assert_eq!(state.pending_pty_input_offset, 0);
    assert!(
        state.pending_pty_input_bytes <= 5,
        "live writes may flush immediately but should not overcount pending bytes"
    );
}

#[test]
fn run_periodic_tasks_clears_theme_digits_outside_picker_mode() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::None;
    state.theme_picker_digits = "12".to_string();
    timers.theme_picker_digit_deadline = Some(Instant::now() + Duration::from_secs(1));

    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());
    assert!(state.theme_picker_digits.is_empty());
    assert!(timers.theme_picker_digit_deadline.is_none());
}

#[test]
fn take_sigwinch_flag_uses_installed_hook_value() {
    let _hooks = install_sigwinch_hooks(hook_take_sigwinch_false, hook_terminal_size_80x24);
    assert!(!take_sigwinch_flag());
}

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

    input_dispatch::handle_wake_word_detection(&mut state, &mut timers, &mut deps);

    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 1));
}

#[test]
fn wake_word_detection_is_ignored_while_recording() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = true;
    state.status_state.recording_state = RecordingState::Recording;

    input_dispatch::handle_wake_word_detection(&mut state, &mut timers, &mut deps);

    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn wake_word_detection_is_ignored_when_disabled() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = false;

    input_dispatch::handle_wake_word_detection(&mut state, &mut timers, &mut deps);

    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn wake_word_detection_is_ignored_when_overlay_is_open() {
    let _capture = install_start_capture_hook(hook_start_capture_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.wake_word = true;
    state.overlay_mode = OverlayMode::Settings;

    input_dispatch::handle_wake_word_detection(&mut state, &mut timers, &mut deps);

    START_CAPTURE_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}

#[test]
fn run_periodic_tasks_sigwinch_no_size_change_skips_resize_messages() {
    let _hooks = install_sigwinch_hooks(hook_take_sigwinch_true, hook_terminal_size_80x24);
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.terminal_cols = 80;
    state.terminal_rows = 24;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());
    assert!(
        writer_rx.recv_timeout(Duration::from_millis(100)).is_err(),
        "no resize event expected when geometry is unchanged"
    );
}

#[test]
fn run_periodic_tasks_sigwinch_single_dimension_change_triggers_resize() {
    let _hooks = install_sigwinch_hooks(hook_take_sigwinch_true, hook_terminal_size_80x24);
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.terminal_cols = 80;
    state.terminal_rows = 1;

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
    assert_eq!(state.terminal_cols, 80);
    assert_eq!(state.terminal_rows, 24);
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
    state.overlay_mode = OverlayMode::ThemePicker;
    state.theme_picker_digits = "12".to_string();
    timers.theme_picker_digit_deadline = Some(now + Duration::from_secs(1));

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(state.theme_picker_digits, "12");
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
    let expected = progress::SPINNER_BRAILLE[start_index % progress::SPINNER_BRAILLE.len()];
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
fn run_periodic_tasks_wake_badge_pulse_refreshes_full_hud_when_interval_elapsed() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    let now = Instant::now();
    state.config.wake_word = true;
    state.status_state.hud_style = HudStyle::Full;
    state.status_state.wake_word_state = WakeWordHudState::Listening;
    timers.last_wake_hud_tick = now - Duration::from_secs(1);

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(timers.last_wake_hud_tick, now);
    assert!(
        writer_rx.try_recv().is_ok(),
        "expected wake-badge pulse redraw when interval elapsed"
    );
}

#[test]
fn run_periodic_tasks_wake_badge_pulse_waits_for_interval() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    let now = Instant::now();
    state.config.wake_word = true;
    state.status_state.hud_style = HudStyle::Full;
    state.status_state.wake_word_state = WakeWordHudState::Listening;
    timers.last_wake_hud_tick = now - Duration::from_millis(100);
    let prior_tick = timers.last_wake_hud_tick;

    run_periodic_tasks(&mut state, &mut timers, &mut deps, now);
    assert_eq!(timers.last_wake_hud_tick, prior_tick);
    assert!(
        writer_rx.try_recv().is_err(),
        "no wake-badge redraw expected before pulse interval"
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
    state.pending_pty_output = Some(b"abc".to_vec());

    assert!(flush_pending_output_or_continue(&mut state, &deps));
    assert_eq!(state.pending_pty_output, Some(b"abc".to_vec()));
}

#[test]
fn flush_pending_output_or_continue_stops_when_writer_disconnected_and_output_drained() {
    let (mut state, _timers, deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    drop(writer_rx);
    state.pending_pty_output = Some(b"abc".to_vec());

    assert!(!flush_pending_output_or_continue(&mut state, &deps));
    assert!(state.pending_pty_output.is_none());
}

#[test]
fn flush_pending_output_or_continue_keeps_running_when_flush_succeeds() {
    let (mut state, _timers, deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pending_pty_output = Some(b"ok".to_vec());

    assert!(flush_pending_output_or_continue(&mut state, &deps));
    assert!(state.pending_pty_output.is_none());
}

#[test]
fn run_event_loop_flushes_pending_input_before_exit() {
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.pending_pty_input.push_back(b"hello".to_vec());
    state.pending_pty_input_bytes = 5;
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);
    assert!(state.pending_pty_input.is_empty());
    assert_eq!(state.pending_pty_input_offset, 0);
    assert_eq!(state.pending_pty_input_bytes, 0);
}

#[test]
fn run_event_loop_flushes_pending_output_even_when_writer_is_disconnected() {
    let (mut state, mut timers, mut deps, writer_rx, input_tx) = build_harness("cat", &[], 8);
    drop(writer_rx);
    state.pending_pty_output = Some(b"leftover".to_vec());
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);
    assert!(
        state.pending_pty_output.is_none(),
        "pending output should be consumed even when writer is disconnected"
    );
}

#[test]
fn run_event_loop_flushes_pending_output_on_success_path() {
    let (mut state, mut timers, mut deps, writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.pending_pty_output = Some(b"ok".to_vec());
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);
    assert!(state.pending_pty_output.is_none());
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

#[test]
fn run_event_loop_help_overlay_mouse_body_click_keeps_overlay_open() {
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Help;
    let overlay_top_y = state
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
    assert_eq!(state.overlay_mode, OverlayMode::Help);
}

#[test]
fn run_event_loop_theme_picker_click_selects_theme_and_closes_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemePicker;
    let overlay_top_y = state
        .terminal_rows
        .saturating_sub(theme_picker_height() as u16)
        .saturating_add(1);
    input_tx
        .send(InputEvent::MouseClick {
            x: 3,
            y: overlay_top_y + THEME_PICKER_OPTION_START_ROW as u16 - 1,
        })
        .expect("queue theme option click");
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);
    assert_eq!(state.overlay_mode, OverlayMode::None);
    assert_ne!(state.theme, Theme::Codex);
}

#[test]
fn run_event_loop_does_not_run_periodic_before_first_tick() {
    let (mut state, mut timers, mut deps, _writer_rx, input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::None;
    state.theme_picker_digits = "12".to_string();
    input_tx.send(InputEvent::Exit).expect("queue exit event");

    run_event_loop(&mut state, &mut timers, &mut deps);
    assert_eq!(state.theme_picker_digits, "12");
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
fn run_event_loop_ctrl_e_with_pending_insert_text_sends_immediately_while_recording() {
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

    EARLY_STOP_CALLS.with(|calls| assert_eq!(calls.get(), 0));
    assert!(timers.last_enter_at.is_some());
    assert!(!state.status_state.insert_pending_send);
    assert_eq!(
        state.status_state.recording_state,
        RecordingState::Recording
    );
    assert!(!state.force_send_on_next_transcript);
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 1));
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
    assert!(state.force_send_on_next_transcript);
}

#[test]
fn run_event_loop_ctrl_e_with_pending_insert_text_sends_immediately_outside_recording() {
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

    assert!(timers.last_enter_at.is_some());
    assert!(!state.status_state.insert_pending_send);
    assert_eq!(state.status_state.recording_state, RecordingState::Idle);
    assert!(!state.force_send_on_next_transcript);
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 1));
}

#[test]
fn run_event_loop_ctrl_e_without_pending_insert_text_is_consumed_outside_recording() {
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
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 0));
}
