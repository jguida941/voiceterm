//! Core runtime loop that coordinates PTY output, input events, and voice jobs.

mod input_dispatch;
mod output_dispatch;
mod overlay_dispatch;
mod periodic_tasks;

#[cfg(test)]
use std::cell::Cell;
use std::io::{self, ErrorKind};
use std::time::{Duration, Instant};

use crossbeam_channel::{never, select, TryRecvError, TrySendError};
use crossterm::terminal::size as terminal_size;
use voiceterm::{log_debug, VoiceCaptureTrigger};

use crate::arrow_keys::{is_arrow_escape_noise, parse_arrow_keys, parse_arrow_keys_only, ArrowKey};
use crate::button_handlers::{
    advance_hud_button_focus, send_enhanced_status_with_buttons, update_button_registry,
    ButtonActionContext,
};
use crate::buttons::ButtonAction;
use crate::config::{HudRightPanel, VoiceSendMode};
use crate::event_state::{EventLoopDeps, EventLoopState, EventLoopTimers};
use crate::help::{
    help_overlay_height, help_overlay_inner_width_for_terminal, help_overlay_width_for_terminal,
    HELP_OVERLAY_FOOTER,
};
use crate::input::InputEvent;
use crate::overlays::{
    show_help_overlay, show_settings_overlay, show_theme_picker_overlay, OverlayMode,
};
use crate::progress;
use crate::prompt::should_auto_trigger;
use crate::settings::{
    settings_overlay_height, settings_overlay_inner_width_for_terminal,
    settings_overlay_width_for_terminal, SettingsItem, SETTINGS_OVERLAY_FOOTER,
};
use crate::settings_handlers::{
    SettingsActionContext, SettingsHudContext, SettingsStatusContext, SettingsVoiceContext,
};
use crate::status_line::{RecordingState, METER_HISTORY_MAX};
use crate::terminal::{apply_pty_winsize, resolved_cols, take_sigwinch, update_pty_winsize};
use crate::theme_ops::{
    apply_theme_picker_index, theme_index_from_theme, theme_picker_has_longer_match,
    theme_picker_parse_index,
};
use crate::theme_picker::{
    theme_picker_height, theme_picker_inner_width_for_terminal,
    theme_picker_total_width_for_terminal, THEME_OPTIONS, THEME_PICKER_FOOTER,
    THEME_PICKER_OPTION_START_ROW,
};
use crate::transcript::{try_flush_pending, TranscriptIo};
use crate::voice_control::{
    clear_capture_metrics, drain_voice_messages, reset_capture_visuals, start_voice_capture,
    VoiceDrainContext,
};
use crate::writer::{set_status, WriterMessage};
use input_dispatch::handle_input_event;
use output_dispatch::handle_output_chunk;
use overlay_dispatch::{
    close_overlay, open_help_overlay, open_settings_overlay, open_theme_picker_overlay,
};
use periodic_tasks::run_periodic_tasks;

const EVENT_LOOP_IDLE_MS: u64 = 20;
const THEME_PICKER_NUMERIC_TIMEOUT_MS: u64 = 350;
const RECORDING_DURATION_UPDATE_MS: u64 = 200;
const PROCESSING_SPINNER_TICK_MS: u64 = 120;
const METER_DB_FLOOR: f32 = -60.0;
const PTY_OUTPUT_BATCH_CHUNKS: usize = 16;
const PENDING_OUTPUT_RETRY_MS: u64 = 5;
const PTY_INPUT_FLUSH_ATTEMPTS: usize = 16;
const PTY_INPUT_MAX_BUFFER_BYTES: usize = 256 * 1024;

#[cfg(test)]
type TrySendHook = fn(&[u8]) -> io::Result<usize>;
#[cfg(test)]
type TakeSigwinchHook = fn() -> bool;
#[cfg(test)]
type TerminalSizeHook = fn() -> io::Result<(u16, u16)>;
#[cfg(test)]
type StartCaptureHook = fn(
    &mut crate::voice_control::VoiceManager,
    VoiceCaptureTrigger,
    &crossbeam_channel::Sender<WriterMessage>,
    &mut Option<Instant>,
    &mut Option<String>,
    &mut crate::status_line::StatusLineState,
) -> anyhow::Result<()>;
#[cfg(test)]
type RequestEarlyStopHook = fn(&mut crate::voice_control::VoiceManager) -> bool;
#[cfg(test)]
thread_local! {
    static TRY_SEND_HOOK: Cell<Option<TrySendHook>> = const { Cell::new(None) };
    static TAKE_SIGWINCH_HOOK: Cell<Option<TakeSigwinchHook>> = const { Cell::new(None) };
    static TERMINAL_SIZE_HOOK: Cell<Option<TerminalSizeHook>> = const { Cell::new(None) };
    static START_CAPTURE_HOOK: Cell<Option<StartCaptureHook>> = const { Cell::new(None) };
    static REQUEST_EARLY_STOP_HOOK: Cell<Option<RequestEarlyStopHook>> = const { Cell::new(None) };
}

#[cfg(test)]
fn set_try_send_hook(hook: Option<TrySendHook>) {
    TRY_SEND_HOOK.with(|slot| slot.set(hook));
}

#[cfg(test)]
fn set_take_sigwinch_hook(hook: Option<TakeSigwinchHook>) {
    TAKE_SIGWINCH_HOOK.with(|slot| slot.set(hook));
}

#[cfg(test)]
fn set_terminal_size_hook(hook: Option<TerminalSizeHook>) {
    TERMINAL_SIZE_HOOK.with(|slot| slot.set(hook));
}

#[cfg(test)]
fn set_start_capture_hook(hook: Option<StartCaptureHook>) {
    START_CAPTURE_HOOK.with(|slot| slot.set(hook));
}

#[cfg(test)]
fn set_request_early_stop_hook(hook: Option<RequestEarlyStopHook>) {
    REQUEST_EARLY_STOP_HOOK.with(|slot| slot.set(hook));
}

fn try_send_pty_bytes(
    session: &mut voiceterm::pty_session::PtyOverlaySession,
    bytes: &[u8],
) -> io::Result<usize> {
    #[cfg(test)]
    {
        if let Some(hook) = TRY_SEND_HOOK.with(|slot| slot.get()) {
            return hook(bytes);
        }
    }
    session.try_send_bytes(bytes)
}

fn take_sigwinch_flag() -> bool {
    #[cfg(test)]
    {
        if let Some(hook) = TAKE_SIGWINCH_HOOK.with(|slot| slot.get()) {
            return hook();
        }
    }
    take_sigwinch()
}

fn read_terminal_size() -> io::Result<(u16, u16)> {
    #[cfg(test)]
    {
        if let Some(hook) = TERMINAL_SIZE_HOOK.with(|slot| slot.get()) {
            return hook();
        }
    }
    terminal_size()
}

fn start_voice_capture_with_hook(
    voice_manager: &mut crate::voice_control::VoiceManager,
    trigger: VoiceCaptureTrigger,
    writer_tx: &crossbeam_channel::Sender<WriterMessage>,
    status_clear_deadline: &mut Option<Instant>,
    current_status: &mut Option<String>,
    status_state: &mut crate::status_line::StatusLineState,
) -> anyhow::Result<()> {
    #[cfg(test)]
    {
        if let Some(hook) = START_CAPTURE_HOOK.with(|slot| slot.get()) {
            return hook(
                voice_manager,
                trigger,
                writer_tx,
                status_clear_deadline,
                current_status,
                status_state,
            );
        }
    }
    start_voice_capture(
        voice_manager,
        trigger,
        writer_tx,
        status_clear_deadline,
        current_status,
        status_state,
    )
}

fn request_early_stop_with_hook(voice_manager: &mut crate::voice_control::VoiceManager) -> bool {
    #[cfg(test)]
    {
        if let Some(hook) = REQUEST_EARLY_STOP_HOOK.with(|slot| slot.get()) {
            return hook(voice_manager);
        }
    }
    voice_manager.request_early_stop()
}

fn drain_voice_messages_once(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    now: Instant,
) {
    let mut ctx = VoiceDrainContext {
        voice_manager: &mut deps.voice_manager,
        config: &state.config,
        voice_macros: &deps.voice_macros,
        session: &mut deps.session,
        writer_tx: &deps.writer_tx,
        status_clear_deadline: &mut timers.status_clear_deadline,
        current_status: &mut state.current_status,
        status_state: &mut state.status_state,
        session_stats: &mut state.session_stats,
        pending_transcripts: &mut state.pending_transcripts,
        prompt_tracker: &mut state.prompt_tracker,
        last_enter_at: &mut timers.last_enter_at,
        now,
        transcript_idle_timeout: deps.transcript_idle_timeout,
        recording_started_at: &mut timers.recording_started_at,
        preview_clear_deadline: &mut timers.preview_clear_deadline,
        last_meter_update: &mut timers.last_meter_update,
        last_auto_trigger_at: &mut timers.last_auto_trigger_at,
        force_send_on_next_transcript: &mut state.force_send_on_next_transcript,
        auto_voice_enabled: state.auto_voice_enabled,
        sound_on_complete: deps.sound_on_complete,
        sound_on_error: deps.sound_on_error,
    };
    drain_voice_messages(&mut ctx);
}

fn sync_overlay_winsize(state: &mut EventLoopState, deps: &mut EventLoopDeps) {
    update_pty_winsize(
        &mut deps.session,
        &mut state.terminal_rows,
        &mut state.terminal_cols,
        state.overlay_mode,
        state.status_state.hud_style,
    );
}

fn refresh_button_registry_if_mouse(state: &EventLoopState, deps: &EventLoopDeps) {
    if !state.status_state.mouse_enabled {
        return;
    }
    update_button_registry(
        &deps.button_registry,
        &state.status_state,
        state.overlay_mode,
        state.terminal_cols,
        state.theme,
    );
}

fn render_help_overlay_for_state(state: &EventLoopState, deps: &EventLoopDeps) {
    let cols = resolved_cols(state.terminal_cols);
    show_help_overlay(&deps.writer_tx, state.theme, cols);
}

fn render_theme_picker_overlay_for_state(state: &EventLoopState, deps: &EventLoopDeps) {
    let cols = resolved_cols(state.terminal_cols);
    show_theme_picker_overlay(
        &deps.writer_tx,
        state.theme,
        state.theme_picker_selected,
        cols,
    );
}

fn render_settings_overlay_for_state(state: &EventLoopState, deps: &EventLoopDeps) {
    let cols = resolved_cols(state.terminal_cols);
    show_settings_overlay(
        &deps.writer_tx,
        state.theme,
        cols,
        &state.settings_menu,
        &state.config,
        &state.status_state,
        &deps.backend_label,
    );
}

fn reset_theme_picker_digits(state: &mut EventLoopState, timers: &mut EventLoopTimers) {
    state.theme_picker_digits.clear();
    timers.theme_picker_digit_deadline = None;
}

fn reset_theme_picker_selection(state: &mut EventLoopState, timers: &mut EventLoopTimers) {
    state.theme_picker_selected = theme_index_from_theme(state.theme);
    reset_theme_picker_digits(state, timers);
}

fn settings_action_context<'a>(
    state: &'a mut EventLoopState,
    timers: &'a mut EventLoopTimers,
    deps: &'a mut EventLoopDeps,
    overlay_mode: OverlayMode,
) -> SettingsActionContext<'a> {
    SettingsActionContext {
        config: &mut state.config,
        status: SettingsStatusContext {
            status_state: &mut state.status_state,
            writer_tx: &deps.writer_tx,
            status_clear_deadline: &mut timers.status_clear_deadline,
            current_status: &mut state.current_status,
            preview_clear_deadline: &mut timers.preview_clear_deadline,
            last_meter_update: &mut timers.last_meter_update,
        },
        voice: SettingsVoiceContext {
            auto_voice_enabled: &mut state.auto_voice_enabled,
            voice_manager: &mut deps.voice_manager,
            last_auto_trigger_at: &mut timers.last_auto_trigger_at,
            recording_started_at: &mut timers.recording_started_at,
        },
        hud: SettingsHudContext {
            button_registry: &deps.button_registry,
            overlay_mode,
            terminal_rows: &mut state.terminal_rows,
            terminal_cols: &mut state.terminal_cols,
            theme: &mut state.theme,
            pty_session: Some(&mut deps.session),
        },
    }
}

fn apply_settings_item_action(
    selected: SettingsItem,
    direction: i32,
    settings_ctx: &mut SettingsActionContext<'_>,
) -> bool {
    let step = if direction < 0 { -1 } else { 1 };
    match selected {
        SettingsItem::AutoVoice => {
            settings_ctx.toggle_auto_voice();
            true
        }
        SettingsItem::SendMode => {
            settings_ctx.toggle_send_mode();
            true
        }
        SettingsItem::Macros => {
            settings_ctx.toggle_macros_enabled();
            true
        }
        SettingsItem::Sensitivity => {
            if direction == 0 {
                false
            } else {
                let delta_db = if direction < 0 { -5.0 } else { 5.0 };
                settings_ctx.adjust_sensitivity(delta_db);
                true
            }
        }
        SettingsItem::Theme => {
            settings_ctx.cycle_theme(step);
            true
        }
        SettingsItem::HudStyle => {
            settings_ctx.cycle_hud_style(step);
            true
        }
        SettingsItem::HudBorders => {
            settings_ctx.cycle_hud_border_style(step);
            true
        }
        SettingsItem::HudPanel => {
            settings_ctx.cycle_hud_panel(step);
            true
        }
        SettingsItem::HudAnimate => {
            settings_ctx.toggle_hud_panel_recording_only();
            true
        }
        SettingsItem::Latency => {
            settings_ctx.cycle_latency_display(step);
            true
        }
        SettingsItem::Mouse => {
            settings_ctx.toggle_mouse();
            true
        }
        SettingsItem::Backend
        | SettingsItem::Pipeline
        | SettingsItem::Close
        | SettingsItem::Quit => false,
    }
}

fn button_action_context<'a>(
    state: &'a mut EventLoopState,
    timers: &'a mut EventLoopTimers,
    deps: &'a mut EventLoopDeps,
) -> ButtonActionContext<'a> {
    ButtonActionContext {
        overlay_mode: &mut state.overlay_mode,
        settings_menu: &mut state.settings_menu,
        config: &mut state.config,
        status_state: &mut state.status_state,
        auto_voice_enabled: &mut state.auto_voice_enabled,
        voice_manager: &mut deps.voice_manager,
        session: &mut deps.session,
        writer_tx: &deps.writer_tx,
        status_clear_deadline: &mut timers.status_clear_deadline,
        current_status: &mut state.current_status,
        recording_started_at: &mut timers.recording_started_at,
        preview_clear_deadline: &mut timers.preview_clear_deadline,
        last_meter_update: &mut timers.last_meter_update,
        last_auto_trigger_at: &mut timers.last_auto_trigger_at,
        terminal_rows: &mut state.terminal_rows,
        terminal_cols: &mut state.terminal_cols,
        backend_label: &deps.backend_label,
        theme: &mut state.theme,
        button_registry: &deps.button_registry,
    }
}

fn flush_pending_pty_output(state: &mut EventLoopState, deps: &EventLoopDeps) -> bool {
    let Some(pending) = state.pending_pty_output.take() else {
        return true;
    };
    match deps.writer_tx.try_send(WriterMessage::PtyOutput(pending)) {
        Ok(()) => true,
        Err(TrySendError::Full(WriterMessage::PtyOutput(bytes))) => {
            state.pending_pty_output = Some(bytes);
            false
        }
        Err(TrySendError::Full(_)) => false,
        Err(TrySendError::Disconnected(_)) => false,
    }
}

fn flush_pending_pty_input(state: &mut EventLoopState, deps: &mut EventLoopDeps) -> bool {
    for _ in 0..PTY_INPUT_FLUSH_ATTEMPTS {
        let Some(front_len) = state.pending_pty_input.front().map(Vec::len) else {
            state.pending_pty_input_offset = 0;
            state.pending_pty_input_bytes = 0;
            return true;
        };
        if state.pending_pty_input_offset >= front_len {
            state.pending_pty_input.pop_front();
            state.pending_pty_input_offset = 0;
            continue;
        }
        let write_result = {
            let Some(front) = state.pending_pty_input.front() else {
                state.pending_pty_input_offset = 0;
                state.pending_pty_input_bytes = 0;
                return true;
            };
            try_send_pty_bytes(&mut deps.session, &front[state.pending_pty_input_offset..])
                .map(|written| (written, front.len()))
        };
        match write_result {
            Ok((written, front_len)) => {
                state.pending_pty_input_bytes =
                    state.pending_pty_input_bytes.saturating_sub(written);
                state.pending_pty_input_offset += written;
                if state.pending_pty_input_offset >= front_len {
                    state.pending_pty_input.pop_front();
                    state.pending_pty_input_offset = 0;
                }
            }
            Err(err) => {
                if err.kind() == ErrorKind::WouldBlock || err.kind() == ErrorKind::Interrupted {
                    break;
                }
                log_debug(&format!("failed to flush PTY input queue: {err}"));
                return false;
            }
        }
    }
    true
}

fn write_or_queue_pty_input(
    state: &mut EventLoopState,
    deps: &mut EventLoopDeps,
    bytes: Vec<u8>,
) -> bool {
    if bytes.is_empty() {
        return true;
    }
    if state.pending_pty_input.is_empty() {
        match try_send_pty_bytes(&mut deps.session, &bytes) {
            Ok(written) => {
                let Some(remaining) = bytes.get(written..) else {
                    log_debug("PTY write returned an out-of-range byte count");
                    return false;
                };
                if !remaining.is_empty() {
                    state.pending_pty_input.push_back(remaining.to_vec());
                    state.pending_pty_input_bytes = state
                        .pending_pty_input_bytes
                        .saturating_add(remaining.len());
                }
            }
            Err(err) => {
                if err.kind() == ErrorKind::WouldBlock || err.kind() == ErrorKind::Interrupted {
                    state.pending_pty_input_bytes =
                        state.pending_pty_input_bytes.saturating_add(bytes.len());
                    state.pending_pty_input.push_back(bytes);
                } else {
                    log_debug(&format!("failed to write to PTY: {err}"));
                    return false;
                }
            }
        }
    } else {
        state.pending_pty_input_bytes = state.pending_pty_input_bytes.saturating_add(bytes.len());
        state.pending_pty_input.push_back(bytes);
    }
    flush_pending_pty_input(state, deps)
}

fn flush_pending_output_or_continue(state: &mut EventLoopState, deps: &EventLoopDeps) -> bool {
    if state.pending_pty_output.is_none() {
        return true;
    }
    let flush_ok = flush_pending_pty_output(state, deps);
    flush_ok || state.pending_pty_output.is_some()
}

pub(crate) fn run_event_loop(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    let mut running = true;
    let tick_interval = Duration::from_millis(EVENT_LOOP_IDLE_MS);
    let mut last_periodic_tick = Instant::now();
    while running {
        if !flush_pending_pty_input(state, deps) {
            running = false;
            continue;
        }
        let now = Instant::now();
        if now.duration_since(last_periodic_tick) >= tick_interval {
            run_periodic_tasks(state, timers, deps, now);
            last_periodic_tick = now;
        }
        if !flush_pending_output_or_continue(state, deps) {
            running = false;
            continue;
        }
        let select_timeout = if state.pending_pty_output.is_some() {
            Duration::from_millis(PENDING_OUTPUT_RETRY_MS)
        } else {
            tick_interval
        };
        let output_guard = if state.pending_pty_output.is_some() {
            Some(never::<Vec<u8>>())
        } else {
            None
        };
        let input_guard = if state.pending_pty_input_bytes >= PTY_INPUT_MAX_BUFFER_BYTES {
            Some(never::<InputEvent>())
        } else {
            None
        };
        let input_rx = input_guard.as_ref().unwrap_or(&deps.input_rx);
        let output_rx = output_guard.as_ref().unwrap_or(&deps.session.output_rx);
        select! {
            recv(input_rx) -> event => {
                match event {
                    Ok(evt) => handle_input_event(state, timers, deps, evt, &mut running),
                    Err(_) => {
                        running = false;
                    }
                }
            }
            recv(output_rx) -> chunk => {
                match chunk {
                    Ok(data) => handle_output_chunk(state, timers, deps, data, &mut running),
                    Err(_) => {
                        running = false;
                    }
                }
            }
            default(select_timeout) => {}
        }
    }
}

#[cfg(test)]
mod tests;
