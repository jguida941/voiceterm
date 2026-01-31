//! Codex Voice overlay - voice input for the Codex CLI.
//!
//! Runs Codex in a PTY and intercepts hotkeys for voice capture. Transcripts
//! are injected as keystrokes, preserving Codex's native TUI.
//!
//! # Architecture
//!
//! - Input thread: reads stdin, intercepts Ctrl+R/V/Q
//! - PTY reader: forwards Codex output to terminal
//! - Writer thread: serializes output to avoid interleaving
//! - Voice worker: background audio capture and STT

mod audio_meter;
mod banner;
mod color_mode;
mod config;
mod help;
mod input;
mod progress;
mod prompt;
mod session_stats;
mod status_line;
mod status_style;
mod theme;
mod transcript;
mod voice_control;
mod writer;

use anyhow::{anyhow, Result};
use clap::Parser;
use crossbeam_channel::{bounded, select};
use crossterm::terminal::{disable_raw_mode, enable_raw_mode, size as terminal_size};
use rust_tui::pty_session::PtyOverlaySession;
use rust_tui::{
    audio, init_logging, log_debug, log_file_path, VoiceCaptureSource, VoiceCaptureTrigger,
    VoiceJobMessage,
};
use std::collections::VecDeque;
use std::env;
use std::io::{self, Write};
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::{Duration, Instant};

use crate::banner::{format_minimal_banner, format_startup_banner, BannerConfig};
use crate::config::{OverlayConfig, VoiceSendMode};
use crate::help::{format_help_overlay, help_overlay_height};
use crate::input::{spawn_input_thread, InputEvent};
use crate::prompt::{
    resolve_prompt_log, resolve_prompt_regex, should_auto_trigger, PromptLogger, PromptTracker,
};
use crate::session_stats::{format_session_stats, SessionStats};
use crate::status_line::{Pipeline, RecordingState, StatusLineState, VoiceMode};
use crate::transcript::{
    deliver_transcript, push_pending_transcript, transcript_ready, try_flush_pending,
    PendingTranscript, TranscriptIo,
};
use crate::voice_control::{handle_voice_message, start_voice_capture, VoiceManager};
use crate::writer::{send_enhanced_status, set_status, spawn_writer_thread, WriterMessage};

/// Flag set by SIGWINCH handler to trigger terminal resize.
static SIGWINCH_RECEIVED: AtomicBool = AtomicBool::new(false);

/// Max pending messages for the output writer thread.
const WRITER_CHANNEL_CAPACITY: usize = 512;

/// Max pending input events before backpressure.
const INPUT_CHANNEL_CAPACITY: usize = 256;

/// Signal handler for terminal resize events.
///
/// Sets a flag that the main loop checks to update PTY dimensions.
/// Only uses atomic operations (async-signal-safe).
extern "C" fn handle_sigwinch(_: libc::c_int) {
    SIGWINCH_RECEIVED.store(true, Ordering::SeqCst);
}

fn main() -> Result<()> {
    let mut config = OverlayConfig::parse();
    let theme = config.theme();
    if config.app.list_input_devices {
        list_input_devices()?;
        return Ok(());
    }

    if config.app.mic_meter {
        audio_meter::run_mic_meter(&config.app, theme)?;
        return Ok(());
    }

    config.app.validate()?;
    init_logging(&config.app);
    let log_path = log_file_path();
    log_debug("=== Codex Voice Overlay Started ===");
    log_debug(&format!("Log file: {log_path:?}"));

    install_sigwinch_handler()?;

    let working_dir = env::var("CODEX_VOICE_CWD")
        .ok()
        .or_else(|| {
            env::current_dir()
                .ok()
                .map(|dir| dir.to_string_lossy().to_string())
        })
        .unwrap_or_else(|| ".".to_string());

    let prompt_log_path = if config.app.no_logs {
        None
    } else {
        resolve_prompt_log(&config)
    };
    let prompt_logger = PromptLogger::new(prompt_log_path);
    let prompt_regex = resolve_prompt_regex(&config)?;
    let mut prompt_tracker = PromptTracker::new(prompt_regex, prompt_logger);

    let banner_config = BannerConfig {
        auto_voice: config.auto_voice,
        theme: theme.to_string(),
        pipeline: "Rust".to_string(),
        sensitivity_db: config.app.voice_vad_threshold_db,
    };
    let banner = match terminal_size() {
        Ok((cols, _)) if cols < 60 => format_minimal_banner(theme),
        _ => format_startup_banner(&banner_config, theme),
    };
    print!("{banner}");
    let _ = io::stdout().flush();

    let mut session = PtyOverlaySession::new(
        &config.app.codex_cmd,
        &working_dir,
        &config.app.codex_args,
        &config.app.term_value,
    )?;

    enable_raw_mode()?;

    let (writer_tx, writer_rx) = bounded(WRITER_CHANNEL_CAPACITY);
    let _writer_handle = spawn_writer_thread(writer_rx);

    // Set the color theme for the status line
    let _ = writer_tx.send(WriterMessage::SetTheme(theme));

    let mut terminal_cols = 0u16;
    if let Ok((cols, rows)) = terminal_size() {
        terminal_cols = cols;
        let _ = session.set_winsize(rows, cols);
        let _ = writer_tx.send(WriterMessage::Resize { rows, cols });
    }

    let (input_tx, input_rx) = bounded(INPUT_CHANNEL_CAPACITY);
    let _input_handle = spawn_input_thread(input_tx);

    let auto_idle_timeout = Duration::from_millis(config.auto_voice_idle_ms.max(100));
    let transcript_idle_timeout = Duration::from_millis(config.transcript_idle_ms.max(50));
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let mut auto_voice_enabled = config.auto_voice;
    let mut status_state = StatusLineState::new();
    status_state.sensitivity_db = config.app.voice_vad_threshold_db;
    status_state.auto_voice_enabled = auto_voice_enabled;
    status_state.voice_mode = if auto_voice_enabled {
        VoiceMode::Auto
    } else {
        VoiceMode::Manual
    };
    status_state.pipeline = Pipeline::Rust;
    let mut last_auto_trigger_at: Option<Instant> = None;
    let mut last_enter_at: Option<Instant> = None;
    let mut pending_transcripts: VecDeque<PendingTranscript> = VecDeque::new();
    let mut status_clear_deadline: Option<Instant> = None;
    let mut current_status: Option<String> = None;
    let mut recording_started_at: Option<Instant> = None;
    let mut last_recording_update = Instant::now();
    let mut last_recording_duration = 0.0_f32;
    let mut processing_spinner_index = 0usize;
    let mut last_processing_tick = Instant::now();
    let mut help_visible = false;
    let mut session_stats = SessionStats::new();

    if auto_voice_enabled {
        set_status(
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            "Auto-voice enabled",
            None,
        );
        if voice_manager.is_idle() {
            if let Err(err) = start_voice_capture(
                &mut voice_manager,
                VoiceCaptureTrigger::Auto,
                &writer_tx,
                &mut status_clear_deadline,
                &mut current_status,
                &mut status_state,
            ) {
                log_debug(&format!("auto voice capture failed: {err:#}"));
            } else {
                last_auto_trigger_at = Some(Instant::now());
                recording_started_at = Some(Instant::now());
            }
        }
    }

    let mut running = true;
    while running {
        select! {
            recv(input_rx) -> event => {
                match event {
                    Ok(evt) => {
                        if help_visible {
                            match evt {
                                InputEvent::Exit => running = false,
                                _ => {
                                    help_visible = false;
                                    let _ = writer_tx.send(WriterMessage::ClearHelp);
                                }
                            }
                            continue;
                        }
                        match evt {
                            InputEvent::HelpToggle => {
                                let cols = if terminal_cols == 0 {
                                    terminal_size().map(|(c, _)| c).unwrap_or(80)
                                } else {
                                    terminal_cols
                                };
                                let content = format_help_overlay(theme, cols as usize);
                                let height = help_overlay_height();
                                let _ = writer_tx.send(WriterMessage::HelpOverlay { content, height });
                                help_visible = true;
                            }
                            InputEvent::Bytes(bytes) => {
                                if let Err(err) = session.send_bytes(&bytes) {
                                    log_debug(&format!("failed to write to PTY: {err:#}"));
                                    running = false;
                                }
                            }
                            InputEvent::VoiceTrigger => {
                                if let Err(err) = start_voice_capture(
                                    &mut voice_manager,
                                    VoiceCaptureTrigger::Manual,
                                    &writer_tx,
                                    &mut status_clear_deadline,
                                    &mut current_status,
                                    &mut status_state,
                                ) {
                                    set_status(
                                        &writer_tx,
                                        &mut status_clear_deadline,
                                        &mut current_status,
                                        &mut status_state,
                                        "Voice capture failed (see log)",
                                        Some(Duration::from_secs(2)),
                                    );
                                    log_debug(&format!("voice capture failed: {err:#}"));
                                } else {
                                    recording_started_at = Some(Instant::now());
                                }
                            }
                            InputEvent::ToggleAutoVoice => {
                                auto_voice_enabled = !auto_voice_enabled;
                                status_state.auto_voice_enabled = auto_voice_enabled;
                                status_state.voice_mode = if auto_voice_enabled {
                                    VoiceMode::Auto
                                } else {
                                    VoiceMode::Manual
                                };
                                let msg = if auto_voice_enabled {
                                    "Auto-voice enabled"
                                } else {
                                    // Cancel any running capture when disabling auto-voice
                                    if voice_manager.cancel_capture() {
                                        status_state.recording_state = RecordingState::Idle;
                                        recording_started_at = None;
                                        "Auto-voice disabled (capture cancelled)"
                                    } else {
                                        "Auto-voice disabled"
                                    }
                                };
                                set_status(
                                    &writer_tx,
                                    &mut status_clear_deadline,
                                    &mut current_status,
                                    &mut status_state,
                                    msg,
                                    if auto_voice_enabled {
                                        None
                                    } else {
                                        Some(Duration::from_secs(2))
                                    },
                                );
                                if auto_voice_enabled && voice_manager.is_idle() {
                                    if let Err(err) = start_voice_capture(
                                        &mut voice_manager,
                                        VoiceCaptureTrigger::Auto,
                                        &writer_tx,
                                        &mut status_clear_deadline,
                                        &mut current_status,
                                        &mut status_state,
                                    ) {
                                        log_debug(&format!("auto voice capture failed: {err:#}"));
                                    } else {
                                        last_auto_trigger_at = Some(Instant::now());
                                        recording_started_at = Some(Instant::now());
                                    }
                                }
                            }
                            InputEvent::ToggleSendMode => {
                                config.voice_send_mode = match config.voice_send_mode {
                                    VoiceSendMode::Auto => VoiceSendMode::Insert,
                                    VoiceSendMode::Insert => VoiceSendMode::Auto,
                                };
                                let msg = match config.voice_send_mode {
                                    VoiceSendMode::Auto => "Send mode: auto (sends Enter)",
                                    VoiceSendMode::Insert => "Send mode: insert (press Enter to send)",
                                };
                                set_status(
                                    &writer_tx,
                                    &mut status_clear_deadline,
                                    &mut current_status,
                                    &mut status_state,
                                    msg,
                                    Some(Duration::from_secs(3)),
                                );
                            }
                            InputEvent::IncreaseSensitivity => {
                                let threshold_db = voice_manager.adjust_sensitivity(5.0);
                                status_state.sensitivity_db = threshold_db;
                                let msg = format!("Mic sensitivity: {threshold_db:.0} dB (less sensitive)");
                                set_status(
                                    &writer_tx,
                                    &mut status_clear_deadline,
                                    &mut current_status,
                                    &mut status_state,
                                    &msg,
                                    Some(Duration::from_secs(3)),
                                );
                            }
                            InputEvent::DecreaseSensitivity => {
                                let threshold_db = voice_manager.adjust_sensitivity(-5.0);
                                status_state.sensitivity_db = threshold_db;
                                let msg = format!("Mic sensitivity: {threshold_db:.0} dB (more sensitive)");
                                set_status(
                                    &writer_tx,
                                    &mut status_clear_deadline,
                                    &mut current_status,
                                    &mut status_state,
                                    &msg,
                                    Some(Duration::from_secs(3)),
                                );
                            }
                            InputEvent::EnterKey => {
                                // In insert mode, Enter stops capture early and sends what was recorded
                                if config.voice_send_mode == VoiceSendMode::Insert && !voice_manager.is_idle() {
                                    if voice_manager.active_source() == Some(VoiceCaptureSource::Python) {
                                        let _ = voice_manager.cancel_capture();
                                        status_state.recording_state = RecordingState::Idle;
                                        recording_started_at = None;
                                        set_status(
                                            &writer_tx,
                                            &mut status_clear_deadline,
                                            &mut current_status,
                                            &mut status_state,
                                            "Capture cancelled (python fallback cannot stop early)",
                                            Some(Duration::from_secs(3)),
                                        );
                                    } else {
                                        voice_manager.request_early_stop();
                                        status_state.recording_state = RecordingState::Processing;
                                        status_state.recording_duration = None;
                                        processing_spinner_index = 0;
                                        last_processing_tick = Instant::now();
                                        set_status(
                                            &writer_tx,
                                            &mut status_clear_deadline,
                                            &mut current_status,
                                            &mut status_state,
                                            "Processing",
                                            None,
                                        );
                                    }
                                } else {
                                    // Forward Enter to PTY
                                    if let Err(err) = session.send_bytes(&[0x0d]) {
                                        log_debug(&format!("failed to write Enter to PTY: {err:#}"));
                                        running = false;
                                    } else {
                                        last_enter_at = Some(Instant::now());
                                    }
                                }
                            }
                            InputEvent::Exit => {
                                running = false;
                            }
                        }
                    }
                    Err(_) => {
                        running = false;
                    }
                }
            }
            recv(session.output_rx) -> chunk => {
                match chunk {
                    Ok(data) => {
                        prompt_tracker.feed_output(&data);
                        {
                            let mut io = TranscriptIo {
                                session: &mut session,
                                writer_tx: &writer_tx,
                                status_clear_deadline: &mut status_clear_deadline,
                                current_status: &mut current_status,
                                status_state: &mut status_state,
                            };
                            try_flush_pending(
                                &mut pending_transcripts,
                                &prompt_tracker,
                                &mut last_enter_at,
                                &mut io,
                                Instant::now(),
                                transcript_idle_timeout,
                            );
                        }
                        if writer_tx.send(WriterMessage::PtyOutput(data)).is_err() {
                            running = false;
                        }
                    }
                    Err(_) => {
                        running = false;
                    }
                }
            }
            default(Duration::from_millis(50)) => {
                if SIGWINCH_RECEIVED.swap(false, Ordering::SeqCst) {
                    if let Ok((cols, rows)) = terminal_size() {
                        terminal_cols = cols;
                        let _ = session.set_winsize(rows, cols);
                        let _ = writer_tx.send(WriterMessage::Resize { rows, cols });
                        if help_visible {
                            let content = format_help_overlay(theme, cols as usize);
                            let height = help_overlay_height();
                            let _ = writer_tx.send(WriterMessage::HelpOverlay { content, height });
                        }
                    }
                }

                let now = Instant::now();
                if status_state.recording_state == RecordingState::Recording {
                    if let Some(start) = recording_started_at {
                        if now.duration_since(last_recording_update) >= Duration::from_millis(200) {
                            let duration = now.duration_since(start).as_secs_f32();
                            if (duration - last_recording_duration).abs() >= 0.1 {
                                status_state.recording_duration = Some(duration);
                                last_recording_duration = duration;
                                send_enhanced_status(&writer_tx, &status_state);
                            }
                            last_recording_update = now;
                        }
                    }
                } else if status_state.recording_duration.is_some() {
                    status_state.recording_duration = None;
                    last_recording_duration = 0.0;
                    send_enhanced_status(&writer_tx, &status_state);
                }

                if status_state.recording_state == RecordingState::Processing
                    && now.duration_since(last_processing_tick) >= Duration::from_millis(120)
                {
                    let spinner = progress::SPINNER_BRAILLE
                        [processing_spinner_index % progress::SPINNER_BRAILLE.len()];
                    status_state.message = format!("Processing {spinner}");
                    processing_spinner_index = processing_spinner_index.wrapping_add(1);
                    last_processing_tick = now;
                    send_enhanced_status(&writer_tx, &status_state);
                }
                prompt_tracker.on_idle(now, auto_idle_timeout);

                if let Some(message) = voice_manager.poll_message() {
                    let rearm_auto = matches!(
                        message,
                        VoiceJobMessage::Empty { .. } | VoiceJobMessage::Error(_)
                    );
                    match message {
                        VoiceJobMessage::Transcript {
                            text,
                            source,
                            metrics,
                        } => {
                            let ready = transcript_ready(
                                &prompt_tracker,
                                last_enter_at,
                                now,
                                transcript_idle_timeout,
                            );
                            if auto_voice_enabled {
                                prompt_tracker.note_activity(now);
                            }
                            status_state.recording_state = RecordingState::Idle;
                            status_state.recording_duration = None;
                            status_state.pipeline = match source {
                                VoiceCaptureSource::Native => Pipeline::Rust,
                                VoiceCaptureSource::Python => Pipeline::Python,
                            };
                            let drop_note = metrics
                                .as_ref()
                                .filter(|metrics| metrics.frames_dropped > 0)
                                .map(|metrics| format!("dropped {} frames", metrics.frames_dropped));
                            let duration_secs = metrics
                                .as_ref()
                                .map(|metrics| metrics.speech_ms as f32 / 1000.0)
                                .unwrap_or(0.0);
                            session_stats.record_transcript(duration_secs);
                            let drop_suffix = drop_note
                                .as_ref()
                                .map(|note| format!(", {note}"))
                                .unwrap_or_default();
                            if ready && pending_transcripts.is_empty() {
                                let mut io = TranscriptIo {
                                    session: &mut session,
                                    writer_tx: &writer_tx,
                                    status_clear_deadline: &mut status_clear_deadline,
                                    current_status: &mut current_status,
                                    status_state: &mut status_state,
                                };
                                let sent_newline = deliver_transcript(
                                    &text,
                                    source.label(),
                                    config.voice_send_mode,
                                    &mut io,
                                    0,
                                    drop_note.as_deref(),
                                );
                                if sent_newline {
                                    last_enter_at = Some(now);
                                }
                            } else {
                                let dropped = push_pending_transcript(
                                    &mut pending_transcripts,
                                    PendingTranscript {
                                        text,
                                        source,
                                        mode: config.voice_send_mode,
                                    },
                                );
                                if dropped {
                                    set_status(
                                        &writer_tx,
                                        &mut status_clear_deadline,
                                        &mut current_status,
                                        &mut status_state,
                                        "Transcript queue full (oldest dropped)",
                                        Some(Duration::from_secs(2)),
                                    );
                                }
                                if ready {
                                    let mut io = TranscriptIo {
                                        session: &mut session,
                                        writer_tx: &writer_tx,
                                        status_clear_deadline: &mut status_clear_deadline,
                                        current_status: &mut current_status,
                                        status_state: &mut status_state,
                                    };
                                    try_flush_pending(
                                        &mut pending_transcripts,
                                        &prompt_tracker,
                                        &mut last_enter_at,
                                        &mut io,
                                        now,
                                        transcript_idle_timeout,
                                    );
                                } else if !dropped {
                                    let status =
                                        format!("Transcript queued ({}{})", pending_transcripts.len(), drop_suffix);
                                    set_status(
                                        &writer_tx,
                                        &mut status_clear_deadline,
                                        &mut current_status,
                                        &mut status_state,
                                        &status,
                                        None,
                                    );
                                }
                            }
                            if auto_voice_enabled
                                && config.voice_send_mode == VoiceSendMode::Insert
                                && pending_transcripts.is_empty()
                                && voice_manager.is_idle()
                            {
                                if let Err(err) = start_voice_capture(
                                    &mut voice_manager,
                                    VoiceCaptureTrigger::Auto,
                                    &writer_tx,
                                    &mut status_clear_deadline,
                                    &mut current_status,
                                    &mut status_state,
                                ) {
                                    log_debug(&format!("auto voice capture failed: {err:#}"));
                                } else {
                                    last_auto_trigger_at = Some(now);
                                    recording_started_at = Some(now);
                                }
                            }
                        }
                        other => {
                            handle_voice_message(
                                other,
                                &config,
                                &mut session,
                                &writer_tx,
                                &mut status_clear_deadline,
                                &mut current_status,
                                &mut status_state,
                                &mut session_stats,
                                auto_voice_enabled,
                            );
                        }
                    }
                    if auto_voice_enabled && rearm_auto {
                        // Treat empty/error captures as activity so auto-voice can re-arm after idle.
                        prompt_tracker.note_activity(now);
                    }
                    if status_state.recording_state != RecordingState::Recording {
                        recording_started_at = None;
                    }
                }

                {
                    let mut io = TranscriptIo {
                        session: &mut session,
                        writer_tx: &writer_tx,
                        status_clear_deadline: &mut status_clear_deadline,
                        current_status: &mut current_status,
                        status_state: &mut status_state,
                    };
                    try_flush_pending(
                        &mut pending_transcripts,
                        &prompt_tracker,
                        &mut last_enter_at,
                        &mut io,
                        now,
                        transcript_idle_timeout,
                    );
                }

                if auto_voice_enabled
                    && voice_manager.is_idle()
                    && should_auto_trigger(
                        &prompt_tracker,
                        now,
                        auto_idle_timeout,
                        last_auto_trigger_at,
                    )
                {
                    if let Err(err) = start_voice_capture(
                        &mut voice_manager,
                        VoiceCaptureTrigger::Auto,
                        &writer_tx,
                        &mut status_clear_deadline,
                        &mut current_status,
                        &mut status_state,
                    ) {
                        log_debug(&format!("auto voice capture failed: {err:#}"));
                    } else {
                        last_auto_trigger_at = Some(now);
                        recording_started_at = Some(now);
                    }
                }

                if let Some(deadline) = status_clear_deadline {
                    if now >= deadline {
                        status_clear_deadline = None;
                        current_status = None;
                        status_state.message.clear();
                        if auto_voice_enabled && voice_manager.is_idle() {
                            status_state.message = "Auto-voice enabled".to_string();
                        }
                        send_enhanced_status(&writer_tx, &status_state);
                    }
                }
            }
        }
    }

    let _ = writer_tx.send(WriterMessage::ClearStatus);
    let _ = writer_tx.send(WriterMessage::Shutdown);
    disable_raw_mode()?;
    let stats_output = format_session_stats(&session_stats, theme);
    if !stats_output.is_empty() {
        print!("{stats_output}");
        let _ = io::stdout().flush();
    }
    log_debug("=== Codex Voice Overlay Exiting ===");
    Ok(())
}

fn list_input_devices() -> Result<()> {
    match audio::Recorder::list_devices() {
        Ok(devices) => {
            if devices.is_empty() {
                println!("No audio input devices detected.");
            } else {
                println!("Available audio input devices:");
                for name in devices {
                    println!("  - {name}");
                }
            }
        }
        Err(err) => {
            eprintln!("Failed to list audio input devices: {err}");
        }
    }
    Ok(())
}

fn install_sigwinch_handler() -> Result<()> {
    unsafe {
        let handler = handle_sigwinch as *const () as libc::sighandler_t;
        if libc::signal(libc::SIGWINCH, handler) == libc::SIG_ERR {
            log_debug("failed to install SIGWINCH handler");
            return Err(anyhow!("failed to install SIGWINCH handler"));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::Ordering;
    use std::thread;
    use std::time::Duration;

    #[test]
    fn sigwinch_handler_sets_flag() {
        SIGWINCH_RECEIVED.store(false, Ordering::SeqCst);
        handle_sigwinch(0);
        assert!(SIGWINCH_RECEIVED.swap(false, Ordering::SeqCst));
    }

    #[test]
    fn install_sigwinch_handler_installs_handler() {
        SIGWINCH_RECEIVED.store(false, Ordering::SeqCst);
        install_sigwinch_handler().expect("install sigwinch handler");
        unsafe {
            libc::raise(libc::SIGWINCH);
        }
        for _ in 0..20 {
            if SIGWINCH_RECEIVED.swap(false, Ordering::SeqCst) {
                return;
            }
            thread::sleep(Duration::from_millis(5));
        }
        panic!("SIGWINCH was not received");
    }
}
