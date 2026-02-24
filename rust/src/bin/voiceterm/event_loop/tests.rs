use super::*;
use clap::Parser;
use crossbeam_channel::{bounded, Receiver, Sender};
use std::cell::Cell;
use std::collections::VecDeque;
use std::io;
use voiceterm::pty_session::PtyOverlaySession;

use crate::buttons::{ButtonAction, ButtonRegistry};
use crate::config::OverlayConfig;
use crate::config::{HudStyle, LatencyDisplayMode};
use crate::dev_command::{
    DevCommandCompletion, DevCommandKind, DevCommandStatus, DevPanelCommandState, DevTerminalPacket,
};
use crate::dev_panel::dev_panel_height;
use crate::memory::{MemoryIngestor, MemoryMode};
use crate::prompt::{PromptLogger, PromptTracker};
use crate::session_stats::SessionStats;
use crate::settings::SettingsMenuState;
use crate::status_line::{
    status_banner_height, Pipeline, StatusLineState, VoiceMode, WakeWordHudState,
};
use crate::theme::{
    RuntimeBannerStyleOverride, RuntimeBorderStyleOverride, RuntimeGlyphSetOverride,
    RuntimeIndicatorSetOverride, RuntimeProgressBarFamilyOverride, RuntimeProgressStyleOverride,
    RuntimeStartupStyleOverride, RuntimeStylePackOverrides, RuntimeToastPositionOverride,
    RuntimeToastSeverityModeOverride, RuntimeVoiceSceneStyleOverride, Theme,
};
use crate::theme_ops::theme_index_from_theme;
use crate::voice_control::VoiceManager;
use crate::voice_macros::VoiceMacros;
use crate::wake_word::{WakeWordEvent, WakeWordRuntime};

thread_local! {
    static HOOK_CALLS: Cell<usize> = const { Cell::new(0) };
    static START_CAPTURE_CALLS: Cell<usize> = const { Cell::new(0) };
    static LAST_CAPTURE_TRIGGER: Cell<Option<VoiceCaptureTrigger>> = const { Cell::new(None) };
    static EARLY_STOP_CALLS: Cell<usize> = const { Cell::new(0) };
    static CANCEL_CAPTURE_CALLS: Cell<usize> = const { Cell::new(0) };
    static WAKE_CAPTURE_LOG_CALLS: Cell<usize> = const { Cell::new(0) };
    static DRAIN_CALLS: Cell<usize> = const { Cell::new(0) };
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
        LAST_CAPTURE_TRIGGER.with(|trigger| trigger.set(None));
    }
}

fn install_start_capture_hook(hook: StartCaptureHook) -> StartCaptureHookGuard {
    set_start_capture_hook(Some(hook));
    START_CAPTURE_CALLS.with(|calls| calls.set(0));
    LAST_CAPTURE_TRIGGER.with(|trigger| trigger.set(None));
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

struct CancelCaptureHookGuard;

impl Drop for CancelCaptureHookGuard {
    fn drop(&mut self) {
        set_cancel_capture_hook(None);
        CANCEL_CAPTURE_CALLS.with(|calls| calls.set(0));
    }
}

fn install_cancel_capture_hook(hook: CancelCaptureHook) -> CancelCaptureHookGuard {
    set_cancel_capture_hook(Some(hook));
    CANCEL_CAPTURE_CALLS.with(|calls| calls.set(0));
    CancelCaptureHookGuard
}

struct WakeCaptureLogHookGuard;

impl Drop for WakeCaptureLogHookGuard {
    fn drop(&mut self) {
        set_wake_capture_log_hook(None);
        WAKE_CAPTURE_LOG_CALLS.with(|calls| calls.set(0));
    }
}

fn install_wake_capture_log_hook(hook: WakeCaptureLogHook) -> WakeCaptureLogHookGuard {
    set_wake_capture_log_hook(Some(hook));
    WAKE_CAPTURE_LOG_CALLS.with(|calls| calls.set(0));
    WakeCaptureLogHookGuard
}

struct DrainHookGuard;

impl Drop for DrainHookGuard {
    fn drop(&mut self) {
        set_drain_voice_messages_hook(None);
        DRAIN_CALLS.with(|calls| calls.set(0));
    }
}

fn install_drain_hook(hook: DrainVoiceMessagesHook) -> DrainHookGuard {
    set_drain_voice_messages_hook(Some(hook));
    DRAIN_CALLS.with(|calls| calls.set(0));
    DrainHookGuard
}

struct RuntimeStylePackOverrideGuard {
    previous: RuntimeStylePackOverrides,
}

impl Drop for RuntimeStylePackOverrideGuard {
    fn drop(&mut self) {
        crate::theme::set_runtime_style_pack_overrides(self.previous);
    }
}

fn install_runtime_style_pack_overrides(
    overrides: RuntimeStylePackOverrides,
) -> RuntimeStylePackOverrideGuard {
    let previous = crate::theme::runtime_style_pack_overrides();
    crate::theme::set_runtime_style_pack_overrides(overrides);
    RuntimeStylePackOverrideGuard { previous }
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
    trigger: VoiceCaptureTrigger,
    _: &crossbeam_channel::Sender<WriterMessage>,
    _: &mut Option<Instant>,
    _: &mut Option<String>,
    _: &mut crate::status_line::StatusLineState,
) -> anyhow::Result<()> {
    START_CAPTURE_CALLS.with(|calls| calls.set(calls.get() + 1));
    LAST_CAPTURE_TRIGGER.with(|last| last.set(Some(trigger)));
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

fn hook_cancel_capture_true(_: &mut crate::voice_control::VoiceManager) -> bool {
    CANCEL_CAPTURE_CALLS.with(|calls| calls.set(calls.get() + 1));
    true
}

fn hook_cancel_capture_false(_: &mut crate::voice_control::VoiceManager) -> bool {
    CANCEL_CAPTURE_CALLS.with(|calls| calls.set(calls.get() + 1));
    false
}

fn hook_wake_capture_log_count() {
    WAKE_CAPTURE_LOG_CALLS.with(|calls| calls.set(calls.get() + 1));
}

fn hook_drain_count(
    _: &mut crate::voice_control::VoiceDrainContext<'_, voiceterm::pty_session::PtyOverlaySession>,
) {
    DRAIN_CALLS.with(|calls| calls.set(calls.get() + 1));
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
        auto_voice_paused_by_user: false,
        theme,
        overlay_mode: OverlayMode::None,
        settings_menu: SettingsMenuState::new(),
        meter_levels: VecDeque::with_capacity(METER_HISTORY_MAX),
        theme_studio_selected: 0,
        theme_studio_page: crate::theme_studio::StudioPage::Home,
        theme_studio_colors_editor: None,
        theme_studio_borders_page: crate::theme_studio::BordersPageState::new(),
        theme_studio_components_editor: crate::theme_studio::ComponentsEditorState::new(),
        theme_studio_preview_page: crate::theme_studio::PreviewPageState::new(),
        theme_studio_export_page: crate::theme_studio::ExportPageState::new(),
        theme_studio_undo_history: Vec::new(),
        theme_studio_redo_history: Vec::new(),
        theme_picker_selected: theme_index_from_theme(theme),
        theme_picker_digits: String::new(),
        current_status: None,
        pending_transcripts: VecDeque::new(),
        session_stats: SessionStats::new(),
        dev_mode_stats: None,
        dev_event_logger: None,
        dev_panel_commands: DevPanelCommandState::default(),
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
        transcript_history: crate::transcript_history::TranscriptHistory::new(),
        transcript_history_state: crate::transcript_history::TranscriptHistoryState::new(),
        session_memory_logger: None,
        claude_prompt_detector: crate::prompt::ClaudePromptDetector::new(false),
        last_toast_status: None,
        toast_center: crate::toast::ToastCenter::new(),
        memory_ingestor: None,
        theme_file_watcher: None,
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
        last_toast_tick: now,
        last_theme_file_poll: now,
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
        dev_command_broker: None,
    };

    (state, timers, deps, writer_rx, input_tx)
}

fn settings_overlay_row_y(state: &EventLoopState, item: SettingsItem) -> u16 {
    let overlay_top_y = state
        .terminal_rows
        .saturating_sub(settings_overlay_height() as u16)
        .saturating_add(1);
    let item_index = SETTINGS_ITEMS
        .iter()
        .position(|candidate| *candidate == item)
        .expect("settings item index");
    let item_index_u16 = u16::try_from(item_index).expect("settings index fits in u16");
    overlay_top_y
        .saturating_add(SETTINGS_OPTION_START_ROW as u16)
        .saturating_add(item_index_u16)
        .saturating_sub(1)
}

fn centered_overlay_click_x(state: &EventLoopState) -> u16 {
    let cols = resolved_cols(state.terminal_cols) as usize;
    let overlay_width = settings_overlay_width_for_terminal(cols);
    let centered_left = cols.saturating_sub(overlay_width) / 2 + 1;
    u16::try_from(centered_left.saturating_add(2)).expect("overlay x fits in u16")
}

fn centered_settings_overlay_rel_x_to_screen_x(state: &EventLoopState, rel_x: usize) -> u16 {
    let cols = resolved_cols(state.terminal_cols) as usize;
    let overlay_width = settings_overlay_width_for_terminal(cols);
    let centered_left = cols.saturating_sub(overlay_width) / 2 + 1;
    let x = centered_left.saturating_add(rel_x).saturating_sub(1);
    u16::try_from(x).expect("overlay x fits in u16")
}

fn settings_slider_click_x(state: &EventLoopState, slider_offset: usize) -> u16 {
    const SETTINGS_SLIDER_START_REL_X: usize = 2 + 1 + 1 + 15 + 1;
    centered_settings_overlay_rel_x_to_screen_x(
        state,
        SETTINGS_SLIDER_START_REL_X.saturating_add(slider_offset),
    )
}

fn settings_overlay_footer_close_click(state: &EventLoopState) -> (u16, u16) {
    let overlay_height = settings_overlay_height() as u16;
    let overlay_top_y = state
        .terminal_rows
        .saturating_sub(overlay_height)
        .saturating_add(1);
    let footer_y = overlay_top_y
        .saturating_add(overlay_height.saturating_sub(1))
        .saturating_sub(1);

    let cols = resolved_cols(state.terminal_cols) as usize;
    let overlay_width = settings_overlay_width_for_terminal(cols);
    let inner_width = settings_overlay_inner_width_for_terminal(cols);
    let centered_left = cols.saturating_sub(overlay_width) / 2 + 1;

    let footer_title = settings_overlay_footer(&state.theme.colors());
    let title_len = crate::overlay_frame::display_width(&footer_title);
    let left_pad = inner_width.saturating_sub(title_len) / 2;
    let close_prefix = footer_title
        .split('·')
        .next()
        .unwrap_or(&footer_title)
        .split('|')
        .next()
        .unwrap_or(&footer_title)
        .trim_end();
    let close_len = crate::overlay_frame::display_width(close_prefix);
    let close_start = 2usize.saturating_add(left_pad);
    let rel_x = close_start.saturating_add(close_len.saturating_sub(1) / 2);
    let x = centered_left.saturating_add(rel_x).saturating_sub(1);

    (
        u16::try_from(x).expect("footer close x fits in u16"),
        footer_y,
    )
}

fn theme_picker_overlay_row_y(state: &EventLoopState, option_index: usize) -> u16 {
    let overlay_top_y = state
        .terminal_rows
        .saturating_sub(theme_picker_height() as u16)
        .saturating_add(1);
    overlay_top_y
        .saturating_add(THEME_PICKER_OPTION_START_ROW as u16)
        .saturating_add(u16::try_from(option_index).expect("option index fits in u16"))
        .saturating_sub(1)
}

fn centered_theme_picker_rel_x_to_screen_x(state: &EventLoopState, rel_x: usize) -> u16 {
    let cols = resolved_cols(state.terminal_cols) as usize;
    let overlay_width = theme_picker_total_width_for_terminal(cols);
    let centered_left = cols.saturating_sub(overlay_width) / 2 + 1;
    let x = centered_left.saturating_add(rel_x).saturating_sub(1);
    u16::try_from(x).expect("overlay x fits in u16")
}

fn theme_studio_overlay_row_y(state: &EventLoopState, option_index: usize) -> u16 {
    let overlay_top_y = state
        .terminal_rows
        .saturating_sub(theme_studio_height() as u16)
        .saturating_add(1);
    overlay_top_y
        .saturating_add(THEME_STUDIO_OPTION_START_ROW as u16)
        .saturating_add(u16::try_from(option_index).expect("option index fits in u16"))
        .saturating_sub(1)
}

fn centered_theme_studio_rel_x_to_screen_x(state: &EventLoopState, rel_x: usize) -> u16 {
    let cols = resolved_cols(state.terminal_cols) as usize;
    let overlay_width = theme_studio_total_width_for_terminal(cols);
    let centered_left = cols.saturating_sub(overlay_width) / 2 + 1;
    let x = centered_left.saturating_add(rel_x).saturating_sub(1);
    u16::try_from(x).expect("overlay x fits in u16")
}

fn hud_button_click_coords(
    state: &EventLoopState,
    deps: &EventLoopDeps,
    action: ButtonAction,
) -> (u16, u16) {
    let button = deps
        .button_registry
        .all_buttons()
        .into_iter()
        .find(|button| button.event == action)
        .expect("button should be registered");
    let x = button.start_x + (button.end_x.saturating_sub(button.start_x) / 2);
    let y = state
        .terminal_rows
        .saturating_sub(button.y)
        .saturating_add(1);
    (x, y)
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
fn write_or_queue_pty_input_ingests_lossy_text_for_invalid_utf8_bytes() {
    let _hook = install_try_send_hook(hook_would_block);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.memory_ingestor = Some(
        MemoryIngestor::new(
            "sess_evt_loop_input".to_string(),
            "proj_evt_loop_input".to_string(),
            None,
            MemoryMode::Assist,
        )
        .expect("memory ingestor should initialize"),
    );

    assert!(write_or_queue_pty_input(
        &mut state,
        &mut deps,
        vec![0xff, 0xfe, b'a']
    ));

    let ingestor = state
        .memory_ingestor
        .as_ref()
        .expect("memory ingestor should be present");
    let recent = ingestor.index().recent(1);
    assert_eq!(recent.len(), 1);
    assert_eq!(
        recent[0].source,
        crate::memory::types::EventSource::PtyInput
    );
    assert!(
        recent[0].text.contains('\u{FFFD}') || recent[0].text.contains('a'),
        "lossy decode should retain a persisted representation for invalid utf-8 bytes"
    );
}

#[test]
fn handle_output_chunk_ingests_lossy_text_for_invalid_utf8_bytes() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.memory_ingestor = Some(
        MemoryIngestor::new(
            "sess_evt_loop_output".to_string(),
            "proj_evt_loop_output".to_string(),
            None,
            MemoryMode::Assist,
        )
        .expect("memory ingestor should initialize"),
    );
    let mut running = true;

    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        vec![0xff, b'o', b'k'],
        &mut running,
    );

    assert!(running);
    let ingestor = state
        .memory_ingestor
        .as_ref()
        .expect("memory ingestor should be present");
    let recent = ingestor.index().recent(1);
    assert_eq!(recent.len(), 1);
    assert_eq!(
        recent[0].source,
        crate::memory::types::EventSource::PtyOutput
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
fn drain_voice_messages_once_invokes_installed_hook() {
    let _drain = install_drain_hook(hook_drain_count);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);

    drain_voice_messages_once(&mut state, &mut timers, &mut deps, Instant::now());

    DRAIN_CALLS.with(|calls| assert_eq!(calls.get(), 1));
}

#[test]
fn sync_overlay_winsize_updates_cached_terminal_dimensions() {
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.terminal_rows = 0;
    state.terminal_cols = 0;

    sync_overlay_winsize(&mut state, &mut deps);

    assert!(state.terminal_rows > 0);
    assert!(state.terminal_cols > 0);
}

#[test]
fn refresh_button_registry_if_mouse_only_updates_when_enabled() {
    let (mut state, _timers, deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    deps.button_registry.clear();
    state.status_state.mouse_enabled = false;

    refresh_button_registry_if_mouse(&state, &deps);
    assert!(deps.button_registry.all_buttons().is_empty());

    state.status_state.mouse_enabled = true;
    refresh_button_registry_if_mouse(&state, &deps);
    assert!(!deps.button_registry.all_buttons().is_empty());
}

#[test]
fn render_help_overlay_for_state_sends_show_overlay_message() {
    let (state, _timers, deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);

    render_help_overlay_for_state(&state, &deps);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("help overlay message")
    {
        WriterMessage::ShowOverlay { height, .. } => assert_eq!(height, help_overlay_height()),
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn render_theme_picker_overlay_for_state_sends_show_overlay_message() {
    let (state, _timers, deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);

    render_theme_picker_overlay_for_state(&state, &deps);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("theme picker overlay message")
    {
        WriterMessage::ShowOverlay { height, .. } => assert_eq!(height, theme_picker_height()),
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn render_settings_overlay_for_state_sends_show_overlay_message() {
    let (state, _timers, deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);

    render_settings_overlay_for_state(&state, &deps);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("settings overlay message")
    {
        WriterMessage::ShowOverlay { height, .. } => assert_eq!(height, settings_overlay_height()),
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn close_overlay_sets_none_and_sends_clear_overlay() {
    let (mut state, _timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    while writer_rx.try_recv().is_ok() {}

    close_overlay(&mut state, &mut deps, false);

    assert_eq!(state.overlay_mode, OverlayMode::None);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("clear overlay message")
    {
        WriterMessage::ClearOverlay => {}
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn open_help_overlay_sets_mode_and_renders_overlay() {
    let (mut state, _timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::None;
    while writer_rx.try_recv().is_ok() {}

    open_help_overlay(&mut state, &mut deps);

    assert_eq!(state.overlay_mode, OverlayMode::Help);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("help overlay render")
    {
        WriterMessage::ShowOverlay { .. } => {}
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn dev_panel_toggle_opens_overlay_when_dev_mode_enabled() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::None;
    state.config.dev_mode = true;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::DevPanelToggle,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::DevPanel);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("dev panel render")
    {
        WriterMessage::ShowOverlay { content, height } => {
            assert_eq!(height, dev_panel_height());
            assert!(content.contains("Dev Tools"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn dev_panel_toggle_closes_overlay_when_open() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.overlay_mode = OverlayMode::DevPanel;
    while writer_rx.try_recv().is_ok() {}
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::DevPanelToggle,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::None);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("clear overlay message")
    {
        WriterMessage::ClearOverlay => {}
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn dev_panel_toggle_forwards_ctrl_d_when_dev_mode_disabled() {
    let _guard = install_try_send_hook(hook_would_block);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::None;
    state.config.dev_mode = false;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::DevPanelToggle,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::None);
    assert_eq!(state.pending_pty_input_bytes, 1);
    assert_eq!(state.pending_pty_input.front(), Some(&vec![0x04]));
}

#[test]
fn dev_panel_arrow_navigation_moves_command_selection() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.overlay_mode = OverlayMode::DevPanel;
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
    state.overlay_mode = OverlayMode::DevPanel;
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
    state.overlay_mode = OverlayMode::DevPanel;
    state.dev_panel_commands.select_index(5);
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
        state.dev_panel_commands.pending_confirmation(),
        Some(DevCommandKind::Sync)
    );
    assert!(state.dev_panel_commands.running_request_id().is_none());
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
        state.pending_pty_input_bytes,
        "propose bounded remediation".len()
    );
}

#[test]
fn apply_terminal_packet_completion_auto_send_requires_runtime_guard() {
    let _guard = install_try_send_hook(hook_would_block);
    std::env::set_var("VOICETERM_DEV_PACKET_AUTOSEND", "1");

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
    std::env::remove_var("VOICETERM_DEV_PACKET_AUTOSEND");

    assert!(message.contains("auto-sent"));
    assert!(!state.status_state.insert_pending_send);
    assert_eq!(
        state.pending_pty_input_bytes,
        "all clear, continue".len() + 1
    );
    assert!(timers.last_enter_at.is_some());
}

#[test]
fn dev_panel_second_sync_enter_without_broker_reports_unavailable() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.overlay_mode = OverlayMode::DevPanel;
    state.dev_panel_commands.select_index(5);
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
    assert_eq!(state.dev_panel_commands.pending_confirmation(), None);
    assert_eq!(state.dev_panel_commands.running_request_id(), None);
    assert!(state
        .current_status
        .as_deref()
        .is_some_and(|status| status.contains("broker unavailable")));
}

#[test]
fn open_settings_overlay_sets_mode_and_renders_overlay() {
    let (mut state, _timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::None;
    while writer_rx.try_recv().is_ok() {}

    open_settings_overlay(&mut state, &mut deps);

    assert_eq!(state.overlay_mode, OverlayMode::Settings);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("settings overlay render")
    {
        WriterMessage::ShowOverlay { .. } => {}
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn open_theme_picker_overlay_sets_mode_resets_picker_and_renders_overlay() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::None;
    state.theme_picker_digits = "12".to_string();
    timers.theme_picker_digit_deadline = Some(Instant::now() + Duration::from_secs(1));
    while writer_rx.try_recv().is_ok() {}

    open_theme_picker_overlay(&mut state, &mut timers, &mut deps);

    assert_eq!(state.overlay_mode, OverlayMode::ThemePicker);
    assert!(state.theme_picker_digits.is_empty());
    assert!(timers.theme_picker_digit_deadline.is_none());
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("theme picker overlay render")
    {
        WriterMessage::ShowOverlay { .. } => {}
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn open_theme_studio_overlay_sets_mode_and_renders_overlay() {
    let (mut state, _timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::None;
    state.theme_studio_selected = 1;
    state.status_state.hud_style = HudStyle::Hidden;
    state.config.hud_border_style = crate::config::HudBorderStyle::Double;
    state.config.hud_right_panel = crate::config::HudRightPanel::Dots;
    state.config.hud_right_panel_recording_only = false;
    while writer_rx.try_recv().is_ok() {}

    open_theme_studio_overlay(&mut state, &mut deps);

    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("theme studio overlay render")
    {
        WriterMessage::ShowOverlay { height, content } => {
            assert_eq!(height, theme_studio_height());
            assert!(content.contains("Theme Studio"));
            assert!(content.contains("[ Hidden ]"));
            assert!(content.contains("[ Double ]"));
            assert!(content.contains("[ Dots ]"));
            assert!(content.contains("[ Always ]"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn theme_picker_hotkey_opens_theme_studio_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::None;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::ThemePicker,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
}

#[test]
fn theme_studio_enter_on_theme_picker_row_opens_theme_picker_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 0;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemePicker);
}

#[test]
fn theme_studio_enter_on_hud_style_row_cycles_style_and_stays_open() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 1; // HUD style
    state.status_state.hud_style = HudStyle::Full;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(state.status_state.hud_style, HudStyle::Minimal);
}

#[test]
fn theme_studio_arrow_left_on_hud_style_row_cycles_backward() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 1; // HUD style
    state.status_state.hud_style = HudStyle::Minimal;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[D".to_vec()),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(state.status_state.hud_style, HudStyle::Full);
}

#[test]
fn theme_studio_enter_on_glyph_profile_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 5; // Glyph profile
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.glyph_set_override,
        Some(RuntimeGlyphSetOverride::Unicode)
    );
}

#[test]
fn theme_studio_arrow_right_on_indicator_set_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 6; // Indicator set
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[C".to_vec()),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.indicator_set_override,
        Some(RuntimeIndicatorSetOverride::Ascii)
    );
}

#[test]
fn theme_studio_enter_on_progress_spinner_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 7; // Progress spinner
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.progress_style_override,
        Some(RuntimeProgressStyleOverride::Braille)
    );
}

#[test]
fn theme_studio_enter_on_progress_bars_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 8; // Progress bars
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.progress_bar_family_override,
        Some(RuntimeProgressBarFamilyOverride::Bar)
    );
}

#[test]
fn theme_studio_enter_on_theme_borders_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 9; // Theme borders
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.border_style_override,
        Some(RuntimeBorderStyleOverride::Single)
    );
}

#[test]
fn theme_studio_enter_on_voice_scene_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 10; // Voice scene
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.voice_scene_style_override,
        Some(RuntimeVoiceSceneStyleOverride::Pulse)
    );
}

#[test]
fn theme_studio_enter_on_toast_position_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 11; // Toast position
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.toast_position_override,
        Some(RuntimeToastPositionOverride::TopRight)
    );
}

#[test]
fn theme_studio_enter_on_startup_splash_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 12; // Startup splash
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.startup_style_override,
        Some(RuntimeStartupStyleOverride::Full)
    );
}

#[test]
fn theme_studio_enter_on_toast_severity_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 13; // Toast severity
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.toast_severity_mode_override,
        Some(RuntimeToastSeverityModeOverride::Icon)
    );
}

#[test]
fn theme_studio_enter_on_banner_style_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 14; // Banner style
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.banner_style_override,
        Some(RuntimeBannerStyleOverride::Full)
    );
}

#[test]
fn theme_studio_enter_on_undo_row_reverts_latest_runtime_override_edit() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 5; // Glyph profile
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    assert_eq!(
        crate::theme::runtime_style_pack_overrides().glyph_set_override,
        Some(RuntimeGlyphSetOverride::Unicode)
    );
    assert_eq!(state.theme_studio_undo_history.len(), 1);
    assert!(state.theme_studio_redo_history.is_empty());

    state.theme_studio_selected = 15; // Undo edit
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(
        crate::theme::runtime_style_pack_overrides().glyph_set_override,
        None
    );
    assert!(state.theme_studio_undo_history.is_empty());
    assert_eq!(state.theme_studio_redo_history.len(), 1);
}

#[test]
fn theme_studio_enter_on_redo_row_reapplies_runtime_override_edit() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    let mut running = true;

    state.theme_studio_selected = 5; // Glyph profile
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    state.theme_studio_selected = 15; // Undo edit
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    state.theme_studio_selected = 16; // Redo edit
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(
        crate::theme::runtime_style_pack_overrides().glyph_set_override,
        Some(RuntimeGlyphSetOverride::Unicode)
    );
    assert_eq!(state.theme_studio_undo_history.len(), 1);
    assert!(state.theme_studio_redo_history.is_empty());
}

#[test]
fn theme_studio_enter_on_rollback_row_clears_runtime_overrides() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    let mut running = true;

    state.theme_studio_selected = 5; // Glyph profile
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    state.theme_studio_selected = 6; // Indicator set
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    assert_eq!(
        crate::theme::runtime_style_pack_overrides().glyph_set_override,
        Some(RuntimeGlyphSetOverride::Unicode)
    );
    assert_eq!(
        crate::theme::runtime_style_pack_overrides().indicator_set_override,
        Some(RuntimeIndicatorSetOverride::Ascii)
    );

    state.theme_studio_selected = 17; // Rollback edits
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(
        crate::theme::runtime_style_pack_overrides(),
        RuntimeStylePackOverrides::default()
    );
    assert!(state.theme_studio_undo_history.len() >= 2);
    assert!(state.theme_studio_redo_history.is_empty());
}

#[test]
fn reset_theme_picker_selection_resets_index_and_digits() {
    let (mut state, mut timers, _deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.theme = Theme::Codex;
    state.theme_picker_selected = theme_index_from_theme(Theme::Claude);
    state.theme_picker_digits = "12".to_string();
    timers.theme_picker_digit_deadline = Some(Instant::now() + Duration::from_millis(300));

    reset_theme_picker_selection(&mut state, &mut timers);

    let expected_theme = style_pack_theme_lock().unwrap_or(state.theme);
    assert_eq!(
        state.theme_picker_selected,
        theme_index_from_theme(expected_theme)
    );
    assert!(state.theme_picker_digits.is_empty());
    assert!(timers.theme_picker_digit_deadline.is_none());
}

#[test]
fn apply_settings_item_action_theme_zero_direction_matches_positive_step() {
    let (mut zero_state, mut zero_timers, mut zero_deps, _zero_writer_rx, _zero_input_tx) =
        build_harness("cat", &[], 8);
    let (mut plus_state, mut plus_timers, mut plus_deps, _plus_writer_rx, _plus_input_tx) =
        build_harness("cat", &[], 8);
    zero_state.status_state.hud_style = HudStyle::Full;
    plus_state.status_state.hud_style = HudStyle::Full;

    let zero_overlay = zero_state.overlay_mode;
    {
        let mut zero_ctx = settings_action_context(
            &mut zero_state,
            &mut zero_timers,
            &mut zero_deps,
            zero_overlay,
        );
        assert!(apply_settings_item_action(
            SettingsItem::HudStyle,
            0,
            &mut zero_ctx
        ));
    }

    let plus_overlay = plus_state.overlay_mode;
    {
        let mut plus_ctx = settings_action_context(
            &mut plus_state,
            &mut plus_timers,
            &mut plus_deps,
            plus_overlay,
        );
        assert!(apply_settings_item_action(
            SettingsItem::HudStyle,
            1,
            &mut plus_ctx
        ));
    }

    assert_eq!(
        zero_state.status_state.hud_style,
        plus_state.status_state.hud_style
    );
}

#[test]
fn apply_settings_item_action_theme_negative_direction_differs_from_positive_step() {
    let (mut minus_state, mut minus_timers, mut minus_deps, _minus_writer_rx, _minus_input_tx) =
        build_harness("cat", &[], 8);
    let (mut plus_state, mut plus_timers, mut plus_deps, _plus_writer_rx, _plus_input_tx) =
        build_harness("cat", &[], 8);
    minus_state.status_state.hud_style = HudStyle::Full;
    plus_state.status_state.hud_style = HudStyle::Full;

    let minus_overlay = minus_state.overlay_mode;
    {
        let mut minus_ctx = settings_action_context(
            &mut minus_state,
            &mut minus_timers,
            &mut minus_deps,
            minus_overlay,
        );
        assert!(apply_settings_item_action(
            SettingsItem::HudStyle,
            -1,
            &mut minus_ctx
        ));
    }

    let plus_overlay = plus_state.overlay_mode;
    {
        let mut plus_ctx = settings_action_context(
            &mut plus_state,
            &mut plus_timers,
            &mut plus_deps,
            plus_overlay,
        );
        assert!(apply_settings_item_action(
            SettingsItem::HudStyle,
            1,
            &mut plus_ctx
        ));
    }

    assert_ne!(
        minus_state.status_state.hud_style,
        plus_state.status_state.hud_style
    );
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
    state.overlay_mode = OverlayMode::Settings;

    input_dispatch::handle_wake_word_detection(
        &mut state,
        &mut timers,
        &mut deps,
        WakeWordEvent::Detected,
    );

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
    state.overlay_mode = OverlayMode::None;
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
fn help_overlay_unhandled_bytes_close_overlay_and_replay_input() {
    let _hook = install_try_send_hook(hook_count_writes);
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Help;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"status".to_vec()),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::None);
    HOOK_CALLS.with(|calls| assert_eq!(calls.get(), 1));
}

#[test]
fn help_overlay_unhandled_ctrl_e_closes_overlay_and_replays_action() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Help;
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
    assert_eq!(state.overlay_mode, OverlayMode::None);
    assert_eq!(state.current_status.as_deref(), Some("Nothing to finalize"));
}

#[test]
fn transcript_history_overlay_ignores_escape_noise_in_search() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::TranscriptHistory;
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
    state.overlay_mode = OverlayMode::TranscriptHistory;
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
    assert_eq!(state.overlay_mode, OverlayMode::TranscriptHistory);
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
    state.overlay_mode = OverlayMode::Help;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::ToggleHudStyle,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::Help);
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
fn theme_picker_enter_with_invalid_selection_keeps_overlay_open_and_rerenders() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    state.overlay_mode = OverlayMode::ThemePicker;
    state.theme_picker_selected = THEME_OPTIONS.len() + 10;
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
    assert_eq!(state.overlay_mode, OverlayMode::ThemePicker);
    assert_eq!(state.theme, original_theme);
    assert!(state.theme_picker_digits.is_empty());
    let rendered = writer_rx
        .try_iter()
        .any(|message| matches!(message, WriterMessage::ShowOverlay { .. }));
    assert!(
        rendered,
        "invalid index should re-render theme picker overlay"
    );
}

#[test]
fn handle_output_chunk_empty_data_keeps_responding_state_and_suppress_flag() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    state.suppress_startup_escape_input = true;
    state.status_state.recording_state = RecordingState::Responding;
    let mut running = true;

    handle_output_chunk(&mut state, &mut timers, &mut deps, Vec::new(), &mut running);

    assert!(running);
    assert!(state.suppress_startup_escape_input);
    assert_eq!(
        state.status_state.recording_state,
        RecordingState::Responding
    );
}

#[test]
fn handle_output_chunk_non_empty_idle_emits_only_pty_output() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    state.suppress_startup_escape_input = true;
    state.status_state.recording_state = RecordingState::Idle;
    let mut running = true;

    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"ok".to_vec(),
        &mut running,
    );

    assert!(running);
    assert!(!state.suppress_startup_escape_input);
    assert_eq!(state.status_state.recording_state, RecordingState::Idle);
    let messages: Vec<_> = writer_rx.try_iter().collect();
    assert_eq!(
        messages.len(),
        1,
        "idle non-empty output should not emit an extra status redraw"
    );
    match &messages[0] {
        WriterMessage::PtyOutput(bytes) => assert_eq!(bytes, b"ok"),
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn handle_output_chunk_non_empty_responding_transitions_to_idle() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}

    state.status_state.recording_state = RecordingState::Responding;
    let mut running = true;
    handle_output_chunk(
        &mut state,
        &mut timers,
        &mut deps,
        b"done".to_vec(),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.status_state.recording_state, RecordingState::Idle);
    let has_output = writer_rx
        .try_iter()
        .any(|message| matches!(message, WriterMessage::PtyOutput(_)));
    assert!(has_output, "PTY output should always be forwarded");
}

#[test]
fn settings_overlay_mouse_click_cycles_setting_value() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    state.config.latency_display = LatencyDisplayMode::Short;
    state.status_state.latency_display = LatencyDisplayMode::Short;
    let latency_row = settings_overlay_row_y(&state, SettingsItem::Latency);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: 3,
            y: latency_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::Settings);
    assert_eq!(
        state.status_state.latency_display,
        LatencyDisplayMode::Label
    );
    let latency_index = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Latency)
        .expect("latency index");
    assert_eq!(state.settings_menu.selected, latency_index);
}

#[test]
fn settings_overlay_mouse_click_cycles_setting_value_with_centered_offset_x() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    state.config.latency_display = LatencyDisplayMode::Short;
    state.status_state.latency_display = LatencyDisplayMode::Short;
    let latency_row = settings_overlay_row_y(&state, SettingsItem::Latency);
    let click_x = centered_overlay_click_x(&state);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: click_x,
            y: latency_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::Settings);
    assert_eq!(
        state.status_state.latency_display,
        LatencyDisplayMode::Label
    );
}

#[test]
fn settings_overlay_mouse_click_adjusts_sensitivity_with_centered_offset_x() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    state.status_state.sensitivity_db = -55.0;
    let sensitivity_row = settings_overlay_row_y(&state, SettingsItem::Sensitivity);
    let click_x = centered_overlay_click_x(&state);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: click_x,
            y: sensitivity_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::Settings);
    assert_eq!(state.status_state.sensitivity_db, -50.0);
}

#[test]
fn settings_overlay_mouse_click_sensitivity_slider_left_moves_more_sensitive() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    state.status_state.sensitivity_db = -55.0;
    state.config.app.voice_vad_threshold_db = -55.0;
    let sensitivity_row = settings_overlay_row_y(&state, SettingsItem::Sensitivity);
    let click_x = settings_slider_click_x(&state, 1);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: click_x,
            y: sensitivity_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::Settings);
    assert_eq!(state.status_state.sensitivity_db, -60.0);
    assert_eq!(
        state.current_status.as_deref(),
        Some("Mic sensitivity: -60 dB (more sensitive)")
    );
}

#[test]
fn settings_overlay_mouse_click_wake_sensitivity_slider_left_moves_less_sensitive() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    state.config.wake_word_sensitivity = 0.55;
    let sensitivity_row = settings_overlay_row_y(&state, SettingsItem::WakeSensitivity);
    let click_x = settings_slider_click_x(&state, 1);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: click_x,
            y: sensitivity_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::Settings);
    assert!((state.config.wake_word_sensitivity - 0.50).abs() < f32::EPSILON);
}

#[test]
fn settings_overlay_mouse_click_selects_read_only_row_without_state_change() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    let initial_auto_voice = state.auto_voice_enabled;
    let backend_row = settings_overlay_row_y(&state, SettingsItem::Backend);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: 3,
            y: backend_row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::Settings);
    assert_eq!(state.auto_voice_enabled, initial_auto_voice);
    let backend_index = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Backend)
        .expect("backend index");
    assert_eq!(state.settings_menu.selected, backend_index);
}

#[test]
fn settings_overlay_mouse_click_close_row_closes_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    let close_row = settings_overlay_row_y(&state, SettingsItem::Close);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x: 3, y: close_row },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::None);
}

#[test]
fn settings_overlay_mouse_click_quit_row_stops_event_loop() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    let quit_row = settings_overlay_row_y(&state, SettingsItem::Quit);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x: 3, y: quit_row },
        &mut running,
    );

    assert!(!running);
}

#[test]
fn settings_overlay_mouse_click_footer_close_prefix_closes_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    let (x, y) = settings_overlay_footer_close_click(&state);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x, y },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::None);
}

#[test]
fn settings_overlay_mouse_click_footer_outside_close_prefix_keeps_overlay_open() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;

    let overlay_height = settings_overlay_height() as u16;
    let overlay_top_y = state
        .terminal_rows
        .saturating_sub(overlay_height)
        .saturating_add(1);
    let footer_y = overlay_top_y
        .saturating_add(overlay_height.saturating_sub(1))
        .saturating_sub(1);
    let cols = resolved_cols(state.terminal_cols) as usize;
    let overlay_width = settings_overlay_width_for_terminal(cols);
    let x = centered_settings_overlay_rel_x_to_screen_x(&state, overlay_width.saturating_sub(2));

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x, y: footer_y },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::Settings);
}

#[test]
fn settings_overlay_enter_backend_row_keeps_overlay_open() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    state.settings_menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Backend)
        .expect("backend index");

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::Settings);
}

#[test]
fn settings_overlay_enter_backend_row_does_not_redraw() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}
    state.overlay_mode = OverlayMode::Settings;
    state.settings_menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Backend)
        .expect("backend index");

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    let rendered = writer_rx
        .try_iter()
        .any(|msg| matches!(msg, WriterMessage::ShowOverlay { .. }));
    assert!(
        !rendered,
        "read-only backend selection should not redraw settings overlay"
    );
}

#[test]
fn settings_overlay_enter_actionable_row_redraws_overlay() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    while writer_rx.try_recv().is_ok() {}
    state.overlay_mode = OverlayMode::Settings;
    state.settings_menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Latency)
        .expect("latency index");
    state.config.latency_display = LatencyDisplayMode::Short;
    state.status_state.latency_display = LatencyDisplayMode::Short;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    let rendered = writer_rx
        .try_iter()
        .any(|msg| matches!(msg, WriterMessage::ShowOverlay { .. }));
    assert!(rendered, "actionable row should redraw settings overlay");
}

#[test]
fn settings_overlay_enter_close_row_closes_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    state.settings_menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Close)
        .expect("close index");

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::None);
}

#[test]
fn settings_overlay_enter_quit_row_stops_event_loop() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    state.settings_menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Quit)
        .expect("quit index");

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(!running);
}

#[test]
fn settings_overlay_escape_bytes_close_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![0x1b]),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::None);
}

#[test]
fn settings_overlay_arrow_left_and_right_take_different_paths_and_redraw() {
    let (mut left_state, mut left_timers, mut left_deps, left_writer_rx, _left_input_tx) =
        build_harness("cat", &[], 8);
    left_state.overlay_mode = OverlayMode::Settings;
    left_state.config.latency_display = LatencyDisplayMode::Short;
    left_state.status_state.latency_display = LatencyDisplayMode::Short;
    left_state.settings_menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Latency)
        .expect("latency index");
    while left_writer_rx.try_recv().is_ok() {}

    let mut running = true;
    handle_input_event(
        &mut left_state,
        &mut left_timers,
        &mut left_deps,
        InputEvent::Bytes(b"\x1b[D".to_vec()),
        &mut running,
    );
    assert!(running);
    let left_latency = left_state.status_state.latency_display;
    let left_redraw = left_writer_rx
        .try_iter()
        .any(|msg| matches!(msg, WriterMessage::ShowOverlay { .. }));
    assert!(left_redraw, "left-arrow setting changes should redraw");

    let (mut right_state, mut right_timers, mut right_deps, right_writer_rx, _right_input_tx) =
        build_harness("cat", &[], 8);
    right_state.overlay_mode = OverlayMode::Settings;
    right_state.config.latency_display = LatencyDisplayMode::Short;
    right_state.status_state.latency_display = LatencyDisplayMode::Short;
    right_state.settings_menu.selected = SETTINGS_ITEMS
        .iter()
        .position(|item| *item == SettingsItem::Latency)
        .expect("latency index");
    while right_writer_rx.try_recv().is_ok() {}

    let mut running = true;
    handle_input_event(
        &mut right_state,
        &mut right_timers,
        &mut right_deps,
        InputEvent::Bytes(b"\x1b[C".to_vec()),
        &mut running,
    );
    assert!(running);
    let right_latency = right_state.status_state.latency_display;
    let right_redraw = right_writer_rx
        .try_iter()
        .any(|msg| matches!(msg, WriterMessage::ShowOverlay { .. }));
    assert!(right_redraw, "right-arrow setting changes should redraw");
    assert_ne!(left_latency, right_latency);
}

#[test]
fn theme_picker_escape_bytes_close_and_clear_digits() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemePicker;
    state.theme_picker_digits = "12".to_string();

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![0x1b]),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::None);
    assert!(state.theme_picker_digits.is_empty());
}

#[test]
fn theme_picker_arrow_left_and_right_move_selection_in_opposite_directions() {
    let total = THEME_OPTIONS.len();
    assert!(total >= 3, "theme picker should expose multiple options");

    let (mut left_state, mut left_timers, mut left_deps, _left_writer_rx, _left_input_tx) =
        build_harness("cat", &[], 8);
    left_state.overlay_mode = OverlayMode::ThemePicker;
    left_state.theme_picker_selected = 1;
    let mut running = true;
    handle_input_event(
        &mut left_state,
        &mut left_timers,
        &mut left_deps,
        InputEvent::Bytes(b"\x1b[D".to_vec()),
        &mut running,
    );
    assert!(running);
    let left_selected = left_state.theme_picker_selected;

    let (mut right_state, mut right_timers, mut right_deps, _right_writer_rx, _right_input_tx) =
        build_harness("cat", &[], 8);
    right_state.overlay_mode = OverlayMode::ThemePicker;
    right_state.theme_picker_selected = 1;
    let mut running = true;
    handle_input_event(
        &mut right_state,
        &mut right_timers,
        &mut right_deps,
        InputEvent::Bytes(b"\x1b[C".to_vec()),
        &mut running,
    );
    assert!(running);
    let right_selected = right_state.theme_picker_selected;

    assert_ne!(left_selected, right_selected);
    assert_eq!(left_selected, 0);
    assert_eq!(right_selected, 2);
}

#[test]
fn theme_picker_numeric_input_keeps_three_digits_and_clears_after_fourth() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemePicker;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"123".to_vec()),
        &mut running,
    );
    assert!(running);
    assert_eq!(state.theme_picker_digits, "123");

    let before = Instant::now();
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"4".to_vec()),
        &mut running,
    );
    assert!(running);
    assert!(state.theme_picker_digits.is_empty());
    let deadline = timers
        .theme_picker_digit_deadline
        .expect("digit deadline should still be refreshed");
    assert!(
        deadline >= before,
        "digit timeout should not be scheduled in the past"
    );
}

#[test]
fn theme_picker_single_digit_waits_when_longer_match_exists() {
    if THEME_OPTIONS.len() < 10 {
        return;
    }
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemePicker;
    state.theme_picker_selected = 5;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"1".to_vec()),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemePicker);
    assert_eq!(state.theme_picker_selected, 5);
    assert_eq!(state.theme_picker_digits, "1");
}

#[test]
fn overlay_mouse_click_outside_vertical_bounds_is_ignored() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    state.settings_menu.selected = 0;
    let overlay_top_y = state
        .terminal_rows
        .saturating_sub(settings_overlay_height() as u16)
        .saturating_add(1);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: 3,
            y: overlay_top_y.saturating_sub(1),
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.settings_menu.selected, 0);
    assert_eq!(state.overlay_mode, OverlayMode::Settings);
}

#[test]
fn overlay_mouse_click_outside_horizontal_bounds_is_ignored() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    state.settings_menu.selected = 0;
    let row = settings_overlay_row_y(&state, SettingsItem::Latency);
    let click_x = state.terminal_cols;

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x: click_x, y: row },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.settings_menu.selected, 0);
    assert_eq!(state.overlay_mode, OverlayMode::Settings);
}

#[test]
fn theme_picker_mouse_click_on_border_columns_does_not_select_option() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemePicker;
    state.theme_picker_selected = 2;
    let row = theme_picker_overlay_row_y(&state, 0);
    let left_border_x = centered_theme_picker_rel_x_to_screen_x(&state, 1);
    let cols = resolved_cols(state.terminal_cols) as usize;
    let overlay_width = theme_picker_total_width_for_terminal(cols);
    let right_border_x = centered_theme_picker_rel_x_to_screen_x(&state, overlay_width);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: left_border_x,
            y: row,
        },
        &mut running,
    );
    assert!(running);
    assert_eq!(state.theme_picker_selected, 2);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: right_border_x,
            y: row,
        },
        &mut running,
    );
    assert!(running);
    assert_eq!(state.theme_picker_selected, 2);
}

#[test]
fn theme_studio_mouse_click_on_border_columns_does_not_select_option() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 4;
    let row = theme_studio_overlay_row_y(&state, 0);
    let left_border_x = centered_theme_studio_rel_x_to_screen_x(&state, 1);
    let cols = resolved_cols(state.terminal_cols) as usize;
    let overlay_width = theme_studio_total_width_for_terminal(cols);
    let right_border_x = centered_theme_studio_rel_x_to_screen_x(&state, overlay_width);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: left_border_x,
            y: row,
        },
        &mut running,
    );
    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(state.theme_studio_selected, 4);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: right_border_x,
            y: row,
        },
        &mut running,
    );
    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(state.theme_studio_selected, 4);
}

#[test]
fn theme_studio_mouse_click_on_theme_picker_row_opens_theme_picker_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 6;
    let row = theme_studio_overlay_row_y(&state, 0);
    let interior_x = centered_theme_studio_rel_x_to_screen_x(&state, 3);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: interior_x,
            y: row,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemePicker);
    assert_eq!(state.theme_studio_selected, 0);
}

#[test]
fn theme_studio_mouse_click_above_option_rows_does_not_activate_selection() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio_selected = 6;
    let overlay_top_y = state
        .terminal_rows
        .saturating_sub(theme_studio_height() as u16)
        .saturating_add(1);
    let row_above_options = overlay_top_y
        .saturating_add(THEME_STUDIO_OPTION_START_ROW as u16)
        .saturating_sub(2);
    let interior_x = centered_theme_studio_rel_x_to_screen_x(&state, 3);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: interior_x,
            y: row_above_options,
        },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(state.theme_studio_selected, 6);
}

#[test]
fn settings_mouse_click_on_border_columns_does_not_select_option() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    state.settings_menu.selected = 0;
    let row = settings_overlay_row_y(&state, SettingsItem::Latency);
    let left_border_x = centered_settings_overlay_rel_x_to_screen_x(&state, 1);
    let cols = resolved_cols(state.terminal_cols) as usize;
    let overlay_width = settings_overlay_width_for_terminal(cols);
    let right_border_x = centered_settings_overlay_rel_x_to_screen_x(&state, overlay_width);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: left_border_x,
            y: row,
        },
        &mut running,
    );
    assert!(running);
    assert_eq!(state.settings_menu.selected, 0);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick {
            x: right_border_x,
            y: row,
        },
        &mut running,
    );
    assert!(running);
    assert_eq!(state.settings_menu.selected, 0);
}

#[test]
fn settings_mouse_click_zero_column_is_ignored() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.overlay_mode = OverlayMode::Settings;
    state.settings_menu.selected = 0;
    let row = settings_overlay_row_y(&state, SettingsItem::Latency);

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x: 0, y: row },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::Settings);
    assert_eq!(state.settings_menu.selected, 0);
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
fn suppress_startup_escape_only_blocks_arrow_noise_when_enabled() {
    {
        let _hook = install_try_send_hook(hook_count_writes);
        let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
        state.suppress_startup_escape_input = true;
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
        state.suppress_startup_escape_input = false;
        let mut running = true;
        handle_input_event(
            &mut state,
            &mut timers,
            &mut deps,
            InputEvent::Bytes(b"\x1b[A".to_vec()),
            &mut running,
        );
        assert!(running);
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
fn up_arrow_does_not_move_focus_and_is_forwarded_to_pty() {
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

    set_claude_prompt_suppression(&mut state, &mut deps, true);
    assert!(state.status_state.claude_prompt_suppressed);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(Vec::new()),
        &mut running,
    );

    assert!(running);
    assert!(state.status_state.claude_prompt_suppressed);
}

#[test]
fn non_empty_bytes_clear_claude_prompt_suppression() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.claude_prompt_detector = crate::prompt::ClaudePromptDetector::new(true);
    let mut running = true;

    let detected = state
        .claude_prompt_detector
        .feed_output(b"Do you want to proceed? (y/n)\n");
    assert!(detected);
    set_claude_prompt_suppression(&mut state, &mut deps, true);
    assert!(state.status_state.claude_prompt_suppressed);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"x".to_vec()),
        &mut running,
    );

    assert!(running);
    assert!(!state.status_state.claude_prompt_suppressed);
}

#[test]
fn reply_composer_typing_keeps_claude_prompt_suppression() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.claude_prompt_detector = crate::prompt::ClaudePromptDetector::new(true);
    let mut running = true;

    let detected = state.claude_prompt_detector.feed_output("❯ ".as_bytes());
    assert!(detected);
    set_claude_prompt_suppression(&mut state, &mut deps, true);
    assert!(state.status_state.claude_prompt_suppressed);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"hello".to_vec()),
        &mut running,
    );

    assert!(running);
    assert!(state.status_state.claude_prompt_suppressed);
}

#[test]
fn reply_composer_cancel_key_clears_claude_prompt_suppression() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.claude_prompt_detector = crate::prompt::ClaudePromptDetector::new(true);
    let mut running = true;

    let detected = state.claude_prompt_detector.feed_output("❯ ".as_bytes());
    assert!(detected);
    set_claude_prompt_suppression(&mut state, &mut deps, true);
    assert!(state.status_state.claude_prompt_suppressed);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(vec![0x1b]),
        &mut running,
    );

    assert!(running);
    assert!(!state.status_state.claude_prompt_suppressed);
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
    state.theme_picker_digits = "12".to_string();
    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    assert!(running);
    assert_eq!(state.theme_picker_digits, "12");
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
        state.overlay_mode,
        state.terminal_cols,
        state.theme,
    );
    let (x, y) = hud_button_click_coords(&state, &deps, ButtonAction::ToggleSendMode);
    state.theme_picker_digits = "12".to_string();

    let mut running = true;
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::MouseClick { x, y },
        &mut running,
    );

    assert!(running);
    assert_eq!(state.theme_picker_digits, "12");
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
        state.overlay_mode,
        state.terminal_cols,
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
        state.overlay_mode,
        state.terminal_cols,
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
fn set_claude_prompt_suppression_updates_pty_row_budget() {
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.status_state.hud_style = HudStyle::Full;
    state.terminal_rows = 24;
    state.terminal_cols = 80;

    set_claude_prompt_suppression(&mut state, &mut deps, true);
    assert!(state.status_state.claude_prompt_suppressed);
    let (suppressed_rows, _) = deps.session.current_winsize();
    assert_eq!(suppressed_rows, 24);

    set_claude_prompt_suppression(&mut state, &mut deps, false);
    assert!(!state.status_state.claude_prompt_suppressed);
    let (restored_rows, _) = deps.session.current_winsize();
    let expected_rows = 24u16
        .saturating_sub(status_banner_height(80, HudStyle::Full) as u16)
        .max(1);
    assert_eq!(restored_rows, expected_rows);
}

#[test]
fn periodic_tasks_clear_stale_prompt_suppression_without_new_output() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.claude_prompt_detector = crate::prompt::ClaudePromptDetector::new(true);
    state.status_state.hud_style = HudStyle::Full;
    state.terminal_rows = 24;
    state.terminal_cols = 80;

    // Activate suppression and row-budget expansion.
    let detected = state
        .claude_prompt_detector
        .feed_output(b"Do you want to proceed? (y/n)\n");
    assert!(detected);
    set_claude_prompt_suppression(&mut state, &mut deps, true);
    let (suppressed_rows, _) = deps.session.current_winsize();
    assert_eq!(suppressed_rows, 24);

    // Detector resolved via user input path, but no fresh output chunk arrives.
    state.claude_prompt_detector.on_user_input();
    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());

    assert!(!state.status_state.claude_prompt_suppressed);
    let (restored_rows, _) = deps.session.current_winsize();
    let expected_rows = 24u16
        .saturating_sub(status_banner_height(80, HudStyle::Full) as u16)
        .max(1);
    assert_eq!(restored_rows, expected_rows);
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
    assert_eq!(state.overlay_mode, OverlayMode::ToastHistory);

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::ToastHistoryToggle,
        &mut running,
    );
    assert!(running);
    assert_eq!(state.overlay_mode, OverlayMode::None);
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
    state.overlay_mode = OverlayMode::None;
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
        state.overlay_mode,
        OverlayMode::None,
        "overlay must stay None when dev_mode is off"
    );
    assert_eq!(
        state.pending_pty_input.front(),
        Some(&vec![0x04]),
        "Ctrl+D must queue the EOF byte (0x04) to the PTY"
    );
    assert_eq!(
        state.pending_pty_input_bytes, 1,
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
            state.overlay_mode,
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
    state.overlay_mode = OverlayMode::None;
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
        state.overlay_mode,
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
                content.contains("Dev Tools"),
                "overlay content should contain the Dev Tools header"
            );
        }
        other => panic!("expected ShowOverlay, got: {other:?}"),
    }
    // Confirm PTY did NOT receive the EOF byte.
    assert!(
        state.pending_pty_input.is_empty(),
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
    let overlay_before = state.overlay_mode;

    assert!(deps.dev_command_broker.is_none());
    poll_dev_command_updates(&mut state, &mut timers, &mut deps);

    assert_eq!(
        state.current_status, status_before,
        "status must not change when broker is absent"
    );
    assert_eq!(
        state.overlay_mode, overlay_before,
        "overlay must not change when broker is absent"
    );
}

#[test]
fn non_interference_request_dev_command_rejected_when_dev_mode_off() {
    // request_selected_dev_panel_command must short-circuit when dev_mode is off,
    // leaving all command state untouched.
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = false;
    state.overlay_mode = OverlayMode::DevPanel; // force overlay open
    state.dev_panel_commands.select_index(0);

    request_selected_dev_panel_command(&mut state, &mut timers, &mut deps);

    assert!(
        state.dev_panel_commands.running_request_id().is_none(),
        "no dev command should be launched when dev_mode is off"
    );
    assert!(
        state.current_status.is_none(),
        "no status message should appear; the function should return immediately"
    );
}

#[test]
fn non_interference_default_harness_mirrors_non_dev_session() {
    // Comprehensive invariant check: the default harness (no --dev flag)
    // must mirror the production default where all dev surfaces are inert.
    let (state, _timers, deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);

    assert!(!state.config.dev_mode, "dev_mode must default to false");
    assert!(!state.config.dev_log, "dev_log must default to false");
    assert!(
        state.config.dev_path.is_none(),
        "dev_path must default to None"
    );
    assert!(
        state.dev_mode_stats.is_none(),
        "dev_mode_stats must be None"
    );
    assert!(
        state.dev_event_logger.is_none(),
        "dev_event_logger must be None"
    );
    assert!(
        deps.dev_command_broker.is_none(),
        "dev_command_broker must be None"
    );
    assert_eq!(
        state.overlay_mode,
        OverlayMode::None,
        "overlay must start as None"
    );
    assert!(
        !state.status_state.dev_mode_enabled,
        "status_state.dev_mode_enabled must be false"
    );
}
