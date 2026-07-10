use super::*;
use clap::Parser;
use crossbeam_channel::{bounded, Receiver, Sender};
use regex::Regex;
use std::cell::Cell;
use std::collections::VecDeque;
use std::io;
use voiceterm::pty_session::PtyOverlaySession;

use crate::buttons::{ButtonAction, ButtonRegistry};
use crate::config::OverlayConfig;
use crate::config::{HudStyle, LatencyDisplayMode};
use crate::dev_command::{
    DevCommandCompletion, DevCommandKind, DevCommandStatus, DevPanelState, DevTerminalPacket,
};
use crate::dev_panel::{dev_panel_active_footer, dev_panel_height, panel_inner_width, panel_width};
use crate::event_state::{
    PromptRuntimeState, PtyBufferState, SettingsRuntimeState, ThemeStudioRuntimeState,
    UiRuntimeState,
};
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

mod dev_panel_overlay;
mod input_navigation;
mod non_interference;
mod overlay_replay;
mod periodic_runtime;
mod prompt_suppression;
mod recording_finalize;
mod settings_overlay;
mod theme_picker_mouse;
mod theme_studio;
mod voice_capture;
thread_local! {
    static HOOK_CALLS: Cell<usize> = const { Cell::new(0) };
    static TERMINAL_SIZE_HOOK_CALLS: Cell<usize> = const { Cell::new(0) };
    static START_CAPTURE_CALLS: Cell<usize> = const { Cell::new(0) };
    static LAST_CAPTURE_TRIGGER: Cell<Option<VoiceCaptureTrigger>> = const { Cell::new(None) };
    static EARLY_STOP_CALLS: Cell<usize> = const { Cell::new(0) };
    static CANCEL_CAPTURE_CALLS: Cell<usize> = const { Cell::new(0) };
    static WAKE_CAPTURE_LOG_CALLS: Cell<usize> = const { Cell::new(0) };
    static DRAIN_CALLS: Cell<usize> = const { Cell::new(0) };
}

struct PromptRollingOverrideGuard;

impl Drop for PromptRollingOverrideGuard {
    fn drop(&mut self) {
        super::prompt_occlusion::set_test_rolling_detector_override(None);
    }
}

fn install_prompt_rolling_override(enabled: bool) -> PromptRollingOverrideGuard {
    super::prompt_occlusion::set_test_rolling_detector_override(Some(enabled));
    PromptRollingOverrideGuard
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
        TERMINAL_SIZE_HOOK_CALLS.with(|calls| calls.set(0));
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

struct TerminalHostOverrideGuard {
    previous: Option<TerminalHost>,
}

impl Drop for TerminalHostOverrideGuard {
    fn drop(&mut self) {
        crate::runtime_compat::set_terminal_host_override(self.previous);
    }
}

fn install_terminal_host_override(host: TerminalHost) -> TerminalHostOverrideGuard {
    let previous = Some(crate::runtime_compat::detect_terminal_host());
    crate::runtime_compat::set_terminal_host_override(Some(host));
    TerminalHostOverrideGuard { previous }
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

fn hook_terminal_size_100x30() -> io::Result<(u16, u16)> {
    Ok((100, 30))
}

fn hook_terminal_size_0x0() -> io::Result<(u16, u16)> {
    Ok((0, 0))
}

fn hook_terminal_size_80x2_then_80x24() -> io::Result<(u16, u16)> {
    TERMINAL_SIZE_HOOK_CALLS.with(|calls| {
        let call = calls.get();
        calls.set(call + 1);
        if call == 0 {
            Ok((80, 2))
        } else {
            Ok((80, 24))
        }
    })
}

fn hook_terminal_size_80x2() -> io::Result<(u16, u16)> {
    Ok((80, 2))
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
    let session = PtyOverlaySession::new(cmd, ".", &arg_vec, "xterm-256color", 24, 80)
        .expect("start pty session");

    let (writer_tx, writer_rx) = bounded(writer_capacity);
    let (input_tx, input_rx) = bounded(16);

    let state = EventLoopState {
        config,
        working_dir: ".".to_string(),
        status_state,
        auto_voice_enabled,
        auto_voice_paused_by_user: false,
        theme,
        ui: UiRuntimeState {
            overlay_mode: OverlayMode::None,
            terminal_rows: 24,
            terminal_cols: 80,
            suppress_startup_escape_input: false,
        },
        settings: SettingsRuntimeState {
            menu: SettingsMenuState::new(),
        },
        meter_levels: VecDeque::with_capacity(METER_HISTORY_MAX),
        theme_studio: ThemeStudioRuntimeState {
            selected: 0,
            page: crate::theme_studio::StudioPage::Home,
            colors_editor: None,
            borders_page: crate::theme_studio::BordersPageState::new(),
            components_editor: crate::theme_studio::ComponentsEditorState::new(),
            preview_page: crate::theme_studio::PreviewPageState::new(),
            export_page: crate::theme_studio::ExportPageState::new(),
            undo_history: Vec::new(),
            redo_history: Vec::new(),
            picker_selected: theme_index_from_theme(theme),
            picker_digits: String::new(),
        },
        current_status: None,
        pending_transcripts: VecDeque::new(),
        session_stats: SessionStats::new(),
        dev_mode_stats: None,
        dev_event_logger: None,
        dev_panel_commands: DevPanelState::default(),
        prompt: PromptRuntimeState {
            tracker: prompt_tracker,
            occlusion_detector: crate::prompt::PromptOcclusionDetector::new(false),
            non_rolling_approval_window: VecDeque::with_capacity(1024),
            non_rolling_approval_window_last_update: None,
            non_rolling_release_armed: false,
            non_rolling_sticky_hold_until: None,
        },
        last_recording_duration: 0.0,
        meter_floor_started_at: None,
        processing_spinner_index: 0,
        pty_buffer: PtyBufferState {
            pending_output: None,
            pending_input: VecDeque::new(),
            pending_input_offset: 0,
            pending_input_bytes: 0,
        },
        force_send_on_next_transcript: false,
        transcript_history: crate::transcript_history::TranscriptHistory::new(),
        transcript_history_state: crate::transcript_history::TranscriptHistoryState::new(),
        session_memory_logger: None,
        last_toast_status: None,
        toast_center: crate::toast::ToastCenter::new(),
        memory_ingestor: None,
        memory_browser_state: crate::memory_browser::MemoryBrowserState::new(),
        theme_file_watcher: None,
    };

    let now = Instant::now();
    let timers = EventLoopTimers {
        theme_picker_digit_deadline: None,
        status_clear_deadline: None,
        preview_clear_deadline: None,
        prompt_suppression_release_not_before: None,
        last_auto_trigger_at: None,
        last_user_input_at: None,
        last_enter_at: None,
        recording_started_at: None,
        last_recording_update: now,
        last_processing_tick: now,
        last_heartbeat_tick: now,
        last_meter_update: now,
        last_wake_hud_tick: now,
        last_toast_tick: now,
        last_theme_file_poll: now,
        last_terminal_geometry_poll: now,
        last_review_poll: now,
        pending_terminal_geometry_sample: None,
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
        .ui
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
    // Panels are left-anchored at column 1; a click a couple of columns in
    // lands inside the frame.
    let _ = state;
    3
}

fn centered_settings_overlay_rel_x_to_screen_x(state: &EventLoopState, rel_x: usize) -> u16 {
    // Left-anchored panels: panel-relative columns ARE screen columns.
    let _ = state;
    u16::try_from(rel_x).expect("overlay x fits in u16")
}

fn centered_overlay_left_gutter_x(terminal_cols: u16, overlay_width: usize) -> u16 {
    // Left-anchored panels have no left gutter; the gutter sits just past the
    // panel's right edge.
    let cols = resolved_cols(terminal_cols) as usize;
    assert!(
        cols > overlay_width,
        "test requires a terminal wider than the overlay"
    );
    u16::try_from(overlay_width.saturating_add(1)).expect("overlay gutter x fits in u16")
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
        .ui
        .terminal_rows
        .saturating_sub(overlay_height)
        .saturating_add(1);
    let footer_y = overlay_top_y
        .saturating_add(overlay_height.saturating_sub(1))
        .saturating_sub(1);

    let cols = resolved_cols(state.ui.terminal_cols) as usize;
    let _overlay_width = settings_overlay_width_for_terminal(cols);
    let inner_width = settings_overlay_inner_width_for_terminal(cols);
    // Panels render left-anchored at column 1.
    let centered_left = 1usize;

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

fn dev_panel_footer_close_click(state: &EventLoopState) -> (u16, u16) {
    let overlay_height = dev_panel_height() as u16;
    let overlay_top_y = state
        .ui
        .terminal_rows
        .saturating_sub(overlay_height)
        .saturating_add(1);
    let footer_y = overlay_top_y
        .saturating_add(overlay_height.saturating_sub(1))
        .saturating_sub(1);

    let cols = resolved_cols(state.ui.terminal_cols) as usize;
    let _overlay_width = panel_width(cols);
    let inner_width = panel_inner_width(cols);
    // Panels render left-anchored at column 1.
    let centered_left = 1usize;

    let footer_title =
        dev_panel_active_footer(&state.theme.colors(), &state.dev_panel_commands, cols);
    let title_len = crate::overlay_frame::display_width(&footer_title);
    let left_pad = inner_width.saturating_sub(title_len) / 2;
    let close_prefix = if let Some(prefix_end) = footer_title.find(" close") {
        &footer_title[..prefix_end + " close".len()]
    } else {
        footer_title.as_str()
    };
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
        .ui
        .terminal_rows
        .saturating_sub(theme_picker_height() as u16)
        .saturating_add(1);
    overlay_top_y
        .saturating_add(THEME_PICKER_OPTION_START_ROW as u16)
        .saturating_add(u16::try_from(option_index).expect("option index fits in u16"))
        .saturating_sub(1)
}

fn centered_theme_picker_rel_x_to_screen_x(state: &EventLoopState, rel_x: usize) -> u16 {
    // Panels render left-anchored: panel-relative columns ARE screen columns.
    let _ = state;
    u16::try_from(rel_x).expect("overlay x fits in u16")
}

fn theme_studio_overlay_row_y(state: &EventLoopState, option_index: usize) -> u16 {
    let overlay_top_y = state
        .ui
        .terminal_rows
        .saturating_sub(theme_studio_height() as u16)
        .saturating_add(1);
    overlay_top_y
        .saturating_add(THEME_STUDIO_OPTION_START_ROW as u16)
        .saturating_add(u16::try_from(option_index).expect("option index fits in u16"))
        .saturating_sub(1)
}

fn centered_theme_studio_rel_x_to_screen_x(state: &EventLoopState, rel_x: usize) -> u16 {
    // Panels render left-anchored: panel-relative columns ARE screen columns.
    let _ = state;
    u16::try_from(rel_x).expect("overlay x fits in u16")
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
        .ui
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
    state.pty_buffer.pending_output = Some(vec![1, 2, 3]);

    assert!(!flush_pending_pty_output(&mut state, &deps));
    assert_eq!(state.pty_buffer.pending_output, Some(vec![1, 2, 3]));
}

#[test]
fn flush_pending_pty_output_returns_false_when_writer_is_disconnected() {
    let (mut state, _timers, deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    drop(writer_rx);
    state.pty_buffer.pending_output = Some(vec![9, 8, 7]);

    assert!(!flush_pending_pty_output(&mut state, &deps));
    assert!(
        state.pty_buffer.pending_output.is_none(),
        "disconnected writes should not keep stale pending output"
    );
}

#[test]
fn flush_pending_pty_input_empty_queue_resets_counters() {
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pty_buffer.pending_input_offset = 3;
    state.pty_buffer.pending_input_bytes = 9;

    assert!(flush_pending_pty_input(&mut state, &mut deps));
    assert_eq!(state.pty_buffer.pending_input_offset, 0);
    assert_eq!(state.pty_buffer.pending_input_bytes, 0);
}

#[test]
fn flush_pending_pty_input_pops_front_when_offset_reaches_chunk_end() {
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pty_buffer.pending_input.push_back(vec![1, 2]);
    state.pty_buffer.pending_input.push_back(vec![3]);
    state.pty_buffer.pending_input_offset = 2;
    state.pty_buffer.pending_input_bytes = 1;

    assert!(flush_pending_pty_input(&mut state, &mut deps));
    assert!(state.pty_buffer.pending_input.is_empty());
    assert_eq!(state.pty_buffer.pending_input_offset, 0);
    assert_eq!(state.pty_buffer.pending_input_bytes, 0);
}

#[test]
fn event_loop_constants_match_expected_limits() {
    assert_eq!(METER_DB_FLOOR, -60.0);
    assert_eq!(PTY_INPUT_MAX_BUFFER_BYTES, 256 * 1024);
}

#[test]
fn should_emit_user_input_activity_for_claude_in_cursor_and_jetbrains_hosts() {
    assert!(should_emit_user_input_activity_for_host(
        "claude",
        TerminalHost::Cursor
    ));
    assert!(should_emit_user_input_activity_for_host(
        "claude",
        TerminalHost::JetBrains
    ));
}

#[test]
fn should_not_emit_user_input_activity_for_non_claude_or_other_hosts() {
    assert!(!should_emit_user_input_activity_for_host(
        "codex",
        TerminalHost::Cursor
    ));
    assert!(!should_emit_user_input_activity_for_host(
        "claude",
        TerminalHost::Other
    ));
}

#[test]
fn flush_pending_pty_input_treats_would_block_as_retryable() {
    let _hook = install_try_send_hook(hook_would_block);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pty_buffer.pending_input.push_back(vec![1, 2, 3]);
    state.pty_buffer.pending_input_bytes = 3;

    assert!(flush_pending_pty_input(&mut state, &mut deps));
    assert_eq!(state.pty_buffer.pending_input_offset, 0);
    assert_eq!(state.pty_buffer.pending_input_bytes, 3);
    assert_eq!(state.pty_buffer.pending_input.len(), 1);
}

#[test]
fn flush_pending_pty_input_treats_interrupted_as_retryable() {
    let _hook = install_try_send_hook(hook_interrupted);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pty_buffer.pending_input.push_back(vec![7, 8]);
    state.pty_buffer.pending_input_bytes = 2;

    assert!(flush_pending_pty_input(&mut state, &mut deps));
    assert_eq!(state.pty_buffer.pending_input_offset, 0);
    assert_eq!(state.pty_buffer.pending_input_bytes, 2);
    assert_eq!(state.pty_buffer.pending_input.len(), 1);
}

#[test]
fn flush_pending_pty_input_returns_false_for_non_retry_errors() {
    let _hook = install_try_send_hook(hook_broken_pipe);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pty_buffer.pending_input.push_back(vec![7, 8]);
    state.pty_buffer.pending_input_bytes = 2;

    assert!(!flush_pending_pty_input(&mut state, &mut deps));
}

#[test]
fn flush_pending_pty_input_does_not_write_empty_slice_when_offset_is_at_chunk_end() {
    let _hook = install_try_send_hook(hook_non_empty_full_write);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.pty_buffer.pending_input.push_back(vec![1, 2]);
    state.pty_buffer.pending_input_offset = 2;
    state.pty_buffer.pending_input_bytes = 0;

    assert!(flush_pending_pty_input(&mut state, &mut deps));
    assert!(state.pty_buffer.pending_input.is_empty());
}

#[test]
fn flush_pending_pty_input_drains_many_single_byte_chunks_within_attempt_budget() {
    let _hook = install_try_send_hook(hook_one_byte);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    for _ in 0..12 {
        state.pty_buffer.pending_input.push_back(vec![b'x']);
    }
    state.pty_buffer.pending_input_bytes = 12;

    assert!(flush_pending_pty_input(&mut state, &mut deps));
    assert!(
        state.pty_buffer.pending_input.is_empty(),
        "single-byte writes should clear this queue within 16 attempts"
    );
    assert_eq!(state.pty_buffer.pending_input_bytes, 0);
}

#[test]
fn write_or_queue_pty_input_queues_remainder_after_partial_write() {
    let _hook = install_try_send_hook(hook_partial_then_would_block);
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let bytes = vec![1, 2, 3, 4];

    assert!(write_or_queue_pty_input(&mut state, &mut deps, bytes));
    assert_eq!(state.pty_buffer.pending_input_bytes, 3);
    assert_eq!(state.pty_buffer.pending_input.len(), 1);
    assert_eq!(state.pty_buffer.pending_input.front(), Some(&vec![2, 3, 4]));
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
    assert_eq!(state.pty_buffer.pending_input_bytes, bytes.len());
    assert_eq!(state.pty_buffer.pending_input.front(), Some(&bytes));
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
        state.pty_buffer.pending_input.is_empty(),
        "non-retry errors should not queue bytes"
    );
    assert_eq!(state.pty_buffer.pending_input_bytes, 0);
}

#[test]
fn write_or_queue_pty_input_returns_true_for_live_session() {
    let (mut state, _timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    let bytes = b"hello".to_vec();

    assert!(write_or_queue_pty_input(&mut state, &mut deps, bytes));
    assert_eq!(state.pty_buffer.pending_input_offset, 0);
    assert!(
        state.pty_buffer.pending_input_bytes <= 5,
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
    state.ui.overlay_mode = OverlayMode::None;
    state.theme_studio.picker_digits = "12".to_string();
    timers.theme_picker_digit_deadline = Some(Instant::now() + Duration::from_secs(1));

    run_periodic_tasks(&mut state, &mut timers, &mut deps, Instant::now());
    assert!(state.theme_studio.picker_digits.is_empty());
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
    state.ui.terminal_rows = 0;
    state.ui.terminal_cols = 0;

    sync_overlay_winsize(&mut state, &mut deps);

    assert!(state.ui.terminal_rows > 0);
    assert!(state.ui.terminal_cols > 0);
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
    state.ui.overlay_mode = OverlayMode::Settings;
    while writer_rx.try_recv().is_ok() {}

    close_overlay(&mut state, &mut deps, false);

    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
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
    state.ui.overlay_mode = OverlayMode::None;
    while writer_rx.try_recv().is_ok() {}

    open_help_overlay(&mut state, &mut deps);

    assert_eq!(state.ui.overlay_mode, OverlayMode::Help);
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
    state.ui.overlay_mode = OverlayMode::None;
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
    assert_eq!(state.ui.overlay_mode, OverlayMode::DevPanel);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("dev panel render")
    {
        WriterMessage::ShowOverlay { content, height } => {
            assert_eq!(height, dev_panel_height());
            assert!(content.contains("Actions"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn dev_panel_toggle_closes_overlay_when_open() {
    let (mut state, mut timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.config.dev_mode = true;
    state.ui.overlay_mode = OverlayMode::DevPanel;
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
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
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
    state.ui.overlay_mode = OverlayMode::None;
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
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);
    assert_eq!(state.pty_buffer.pending_input_bytes, 1);
    assert_eq!(state.pty_buffer.pending_input.front(), Some(&vec![0x04]));
}

#[test]
fn open_settings_overlay_sets_mode_and_renders_overlay() {
    let (mut state, _timers, mut deps, writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::None;
    while writer_rx.try_recv().is_ok() {}

    open_settings_overlay(&mut state, &mut deps);

    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
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
    state.ui.overlay_mode = OverlayMode::None;
    state.theme_studio.picker_digits = "12".to_string();
    timers.theme_picker_digit_deadline = Some(Instant::now() + Duration::from_secs(1));
    while writer_rx.try_recv().is_ok() {}

    open_theme_picker_overlay(&mut state, &mut timers, &mut deps);

    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemePicker);
    assert!(state.theme_studio.picker_digits.is_empty());
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
    state.ui.overlay_mode = OverlayMode::None;
    state.theme_studio.selected = 1;
    state.status_state.hud_style = HudStyle::Hidden;
    state.config.hud_border_style = crate::config::HudBorderStyle::Double;
    state.config.hud_right_panel = crate::config::HudRightPanel::Dots;
    state.config.hud_right_panel_recording_only = false;
    while writer_rx.try_recv().is_ok() {}

    open_theme_studio_overlay(&mut state, &mut deps);

    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
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
