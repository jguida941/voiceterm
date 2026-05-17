//! VoiceTerm overlay entrypoint so PTY, HUD, and voice control start as one runtime.
//!
//! Runs the selected CLI in a PTY and intercepts hotkeys for voice capture. Transcripts
//! are injected as keystrokes, preserving the native TUI.
//!
//! # Architecture
//!
//! - Input thread: reads stdin, intercepts overlay shortcut keys
//! - PTY reader: forwards CLI output to terminal
//! - Writer thread: serializes output to avoid interleaving
//! - Voice worker: background audio capture and STT

mod action_center;
mod ansi;
mod arrow_keys;
mod audio_meter;
mod banner;
mod button_handlers;
mod buttons;
mod capture_once;
mod cli_utils;
mod color_mode;
mod config;
mod custom_help;
mod cycle_index;
mod daemon;
mod dev_command;
mod dev_panel;
mod event_loop;
mod event_state;
mod help;
mod hud;
mod hud_debug;
mod icons;
mod image_mode;
mod input;
mod memory;
mod memory_browser;
mod onboarding;
mod overlay_frame;
mod overlay_list;
mod overlays;
mod persistence_io;
mod persistent_config;
mod prompt;
mod provider_adapter;
mod runtime_compat;
mod scrollable;
mod session_memory;
mod session_stats;
mod settings;
mod settings_handlers;
mod status_line;
mod status_messages;
mod status_style;
mod stream_line_buffer;
mod terminal;
#[cfg(test)]
mod test_env;
mod theme;
mod theme_ops;
mod theme_picker;
mod theme_studio;
mod toast;
mod transcript;
mod transcript_history;
mod voice_control;
mod voice_macros;
mod wake_word;
mod writer;

pub(crate) use overlays::OverlayMode;

use anyhow::{bail, Result};
use clap::Parser;
use crossbeam_channel::{bounded, Receiver, Sender};
use std::collections::VecDeque;
use std::env;
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::thread;
use std::time::{Duration, Instant};
use voiceterm::pty_session::PtyOverlaySession;
use voiceterm::{
    auth::run_login_command,
    devtools::{default_dev_root_dir, DevEventJsonlWriter, DevModeStats},
    doctor::base_doctor_report,
    init_logging, log_debug, log_file_path,
    terminal_restore::TerminalRestoreGuard,
    VoiceCaptureTrigger,
};

use crate::banner::{should_skip_banner, show_startup_splash, BannerConfig};
use crate::button_handlers::send_enhanced_status_with_buttons;
use crate::buttons::ButtonRegistry;
use crate::cli_utils::{list_input_devices, resolve_sound_flag, should_print_stats};
use crate::config::{HudStyle, OverlayConfig};
use crate::dev_command::{DevCommandBroker, DevPanelState};
use crate::event_loop::run_event_loop;
use crate::event_state::{
    EventLoopDeps, EventLoopState, EventLoopTimers, PromptRuntimeState, PtyBufferState,
    SettingsRuntimeState, ThemeStudioRuntimeState, UiRuntimeState,
};
use crate::hud::HudRegistry;
use crate::input::{spawn_input_thread, InputEvent};
use crate::prompt::{resolve_prompt_log, resolve_prompt_regex, PromptLogger, PromptTracker};
use crate::provider_adapter::build_prompt_occlusion_detector;
use crate::session_memory::SessionMemoryLogger;
use crate::session_stats::{format_session_stats, SessionStats};
use crate::settings::SettingsMenuState;
use crate::status_line::{
    Pipeline, StatusLineState, VoiceMode, WakeWordHudState, METER_HISTORY_MAX,
};
use crate::terminal::{apply_pty_winsize, install_sigwinch_handler, startup_pty_geometry};
use crate::theme::{set_runtime_theme_file_override, style_pack_theme_lock};
use crate::theme_ops::theme_index_from_theme;
use crate::voice_control::{reset_capture_visuals, start_voice_capture, VoiceManager};
use crate::voice_macros::VoiceMacros;
use crate::wake_word::WakeWordRuntime;
use crate::writer::{send_message_blocking, set_status, spawn_writer_thread, WriterMessage};

/// Max pending messages for the output writer thread.
const WRITER_CHANNEL_CAPACITY: usize = 512;

/// Max pending input events before backpressure.
const INPUT_CHANNEL_CAPACITY: usize = 256;

const METER_UPDATE_MS: u64 = 80;
const JETBRAINS_METER_UPDATE_MS: u64 = 90;
const THREAD_JOIN_POLL_MS: u64 = 10;
const WRITER_SHUTDOWN_JOIN_TIMEOUT_MS: u64 = 500;
const INPUT_SHUTDOWN_JOIN_TIMEOUT_MS: u64 = 100;

#[derive(Debug, Clone)]
struct BackendLaunchConfig {
    label: String,
    command: String,
    args: Vec<String>,
    prompt_pattern: Option<String>,
}

struct LoadedConfigPhase {
    config: OverlayConfig,
    user_config: persistent_config::UserConfig,
    backend: BackendLaunchConfig,
    theme: theme::Theme,
    sound_on_complete: bool,
    sound_on_error: bool,
}

struct RuntimeBuildInputs {
    loaded: LoadedConfigPhase,
    working_dir: String,
    voice_macros: VoiceMacros,
    session_memory_path: PathBuf,
    session_memory_enabled: bool,
    dev_event_logger: Option<DevEventJsonlWriter>,
    prompt_tracker: PromptTracker,
    terminal_guard: TerminalRestoreGuard,
    writer_handle: thread::JoinHandle<()>,
    input_handle: thread::JoinHandle<()>,
    session: PtyOverlaySession,
    writer_tx: Sender<WriterMessage>,
    input_rx: Receiver<InputEvent>,
    button_registry: ButtonRegistry,
    terminal_rows: u16,
    terminal_cols: u16,
    initial_hud_style: HudStyle,
}

struct RuntimeExecutionPhase {
    state: EventLoopState,
    timers: EventLoopTimers,
    deps: EventLoopDeps,
    terminal_guard: TerminalRestoreGuard,
    writer_handle: thread::JoinHandle<()>,
    input_handle: thread::JoinHandle<()>,
}

fn apply_jetbrains_meter_floor(base_ms: u64, is_jetbrains: bool) -> u64 {
    if is_jetbrains {
        base_ms.max(JETBRAINS_METER_UPDATE_MS)
    } else {
        base_ms
    }
}

fn default_session_memory_path(working_dir: &str) -> PathBuf {
    PathBuf::from(working_dir)
        .join(".voiceterm")
        .join("session-memory.md")
}

fn validate_dev_mode_flags(config: &OverlayConfig) -> Result<()> {
    if !config.dev_mode {
        if config.dev_log {
            bail!(
                "--dev-log requires --dev (got dev_mode={}, dev_log={})",
                config.dev_mode,
                config.dev_log
            );
        }
        if config.dev_path.is_some() {
            bail!(
                "--dev-path requires --dev (got dev_mode={}, dev_path={:?})",
                config.dev_mode,
                config.dev_path
            );
        }
    }

    if config.dev_path.is_some() && !config.dev_log {
        bail!(
            "--dev-path requires --dev-log (got dev_log={}, dev_path={:?})",
            config.dev_log,
            config.dev_path
        );
    }
    Ok(())
}

fn resolve_dev_root_path(config: &OverlayConfig, working_dir: &str) -> PathBuf {
    config
        .dev_path
        .clone()
        .unwrap_or_else(|| default_dev_root_dir(Path::new(working_dir)))
}

fn resolved_meter_update_ms(hud_registry: &HudRegistry) -> u64 {
    let base_ms = hud_registry
        .min_tick_interval()
        .map(|duration| duration.as_millis() as u64)
        .unwrap_or(METER_UPDATE_MS);
    apply_jetbrains_meter_floor(base_ms, runtime_compat::is_jetbrains_terminal())
}

fn join_thread_with_timeout(name: &str, handle: thread::JoinHandle<()>, timeout: Duration) {
    let deadline = Instant::now() + timeout;
    loop {
        if handle.is_finished() || Instant::now() >= deadline {
            break;
        }
        thread::sleep(Duration::from_millis(THREAD_JOIN_POLL_MS));
    }

    if handle.is_finished() {
        if let Err(err) = handle.join() {
            log_debug(&format!("{name} thread panicked during shutdown: {err:?}"));
        }
    } else {
        log_debug(&format!(
            "{name} thread did not exit within {}ms; detaching",
            timeout.as_millis()
        ));
    }
}

fn main() -> Result<()> {
    let Some(mut loaded) = load_config_phase()? else {
        return Ok(());
    };
    if loaded.config.capture_once {
        validate_dev_mode_flags(&loaded.config)?;
        loaded.config.app.validate()?;
        init_logging(&loaded.config.app);
        return capture_once::run_capture_once(&loaded.config);
    }
    if loaded.config.daemon {
        return run_daemon_mode(&loaded.config);
    }
    let runtime_inputs = prepare_runtime_phase(loaded)?;
    let mut runtime = build_state_phase(runtime_inputs);
    run_runtime_phase(&mut runtime);
    shutdown_runtime_phase(runtime);
    Ok(())
}

fn run_daemon_mode(config: &config::OverlayConfig) -> Result<()> {
    init_logging(&config.app);
    let working_dir = env::var("VOICETERM_CWD")
        .ok()
        .or_else(|| {
            env::current_dir()
                .ok()
                .map(|d| d.to_string_lossy().to_string())
        })
        .unwrap_or_else(|| ".".to_string());

    let daemon_config = daemon::DaemonConfig {
        socket_path: config
            .socket_path
            .clone()
            .unwrap_or_else(daemon::DaemonConfig::default_socket_path),
        ws_port: config.ws_port,
        ws_enabled: !config.no_ws,
        working_dir,
        memory_mode: memory::MemoryMode::CaptureOnly,
    };

    let rt = tokio::runtime::Runtime::new()?;
    rt.block_on(daemon::run_daemon(daemon_config))
}

fn load_config_phase() -> Result<Option<LoadedConfigPhase>> {
    let mut config = OverlayConfig::parse();
    if config.help {
        let backend = config.resolve_backend();
        let theme = config.theme_for_backend(&backend.label);
        custom_help::print_themed_help(theme);
        return Ok(None);
    }

    if let Some(ref theme_name) = config.export_theme {
        match theme::Theme::from_name(theme_name) {
            Some(t) => {
                let colors = theme::palette_to_resolved(&t.colors());
                let toml = theme::theme_file::export_theme_file(
                    &colors,
                    Some(theme_name.as_str()),
                    Some(theme_name.as_str()),
                );
                print!("{toml}");
                return Ok(None);
            }
            None => {
                bail!(
                    "unknown theme '{}'. Available: chatgpt, claude, codex, coral, catppuccin, dracula, gruvbox, nord, tokyonight, ansi, none",
                    theme_name
                );
            }
        }
    }

    let cli_explicit = persistent_config::detect_explicit_flags(&config);
    let user_config = persistent_config::load_user_config();
    persistent_config::apply_user_config_to_overlay(&user_config, &mut config, &cli_explicit);

    set_runtime_theme_file_override(
        config
            .theme_file
            .as_ref()
            .map(|path| path.to_string_lossy().into_owned()),
    );

    let sound_on_complete = resolve_sound_flag(config.app.sounds, config.app.sound_on_complete);
    let sound_on_error = resolve_sound_flag(config.app.sounds, config.app.sound_on_error);
    let resolved_backend = config.resolve_backend();
    runtime_compat::set_runtime_backend_label(resolved_backend.label.as_str());
    let backend = BackendLaunchConfig {
        label: resolved_backend.label,
        command: resolved_backend.command,
        args: resolved_backend.args,
        prompt_pattern: resolved_backend.prompt_pattern,
    };
    let theme = style_pack_theme_lock().unwrap_or_else(|| config.theme_for_backend(&backend.label));

    if config.app.doctor {
        let mut report = base_doctor_report(&config.app, "voiceterm");
        report.section("Overlay");
        report.push_kv("backend", backend.label.as_str());
        let mut command = vec![backend.command.clone()];
        command.extend(backend.args.iter().cloned());
        report.push_kv("backend_command", command.join(" "));
        report.push_kv(
            "prompt_regex",
            config.prompt_regex.as_deref().unwrap_or("auto"),
        );
        report.push_kv(
            "prompt_log",
            config
                .prompt_log
                .as_ref()
                .map(|path| path.display().to_string())
                .unwrap_or_else(|| "disabled".to_string()),
        );
        report.push_kv("theme", config.theme_name.as_deref().unwrap_or("coral"));
        report.push_kv("no_color", config.no_color);
        report.push_kv("auto_voice", config.auto_voice);
        report.push_kv(
            "voice_send_mode",
            format!("{:?}", config.voice_send_mode).to_lowercase(),
        );
        report.push_kv(
            "latency_display",
            format!("{:?}", config.latency_display).to_lowercase(),
        );
        println!("{}", report.render());
        return Ok(None);
    }

    if config.app.list_input_devices {
        list_input_devices()?;
        return Ok(None);
    }

    if config.app.mic_meter {
        audio_meter::run_mic_meter(&config.app, theme)?;
        return Ok(None);
    }

    Ok(Some(LoadedConfigPhase {
        config,
        user_config,
        backend,
        theme,
        sound_on_complete,
        sound_on_error,
    }))
}

fn prepare_runtime_phase(mut loaded: LoadedConfigPhase) -> Result<RuntimeBuildInputs> {
    validate_dev_mode_flags(&loaded.config)?;
    loaded.config.app.validate()?;
    init_logging(&loaded.config.app);
    let log_path = log_file_path();
    log_debug("=== VoiceTerm Overlay Started ===");
    log_debug(&format!("Log file: {log_path:?}"));

    if loaded.config.login {
        log_debug(&format!(
            "Running login for backend: {}",
            loaded.backend.label
        ));
        run_login_command(&loaded.backend.command)
            .map_err(|err| anyhow::anyhow!("{} login failed: {err}", loaded.backend.label))?;
    }

    install_sigwinch_handler()?;

    let working_dir = env::var("VOICETERM_CWD")
        .ok()
        .or_else(|| {
            env::current_dir()
                .ok()
                .map(|dir| dir.to_string_lossy().to_string())
        })
        .unwrap_or_else(|| ".".to_string());
    log_debug(&format!("resolved working directory: {working_dir}"));
    let voice_macros = VoiceMacros::load_for_project(Path::new(&working_dir));
    if let Some(path) = voice_macros.source_path() {
        log_debug(&format!(
            "voice macros path: {} (loaded {})",
            path.display(),
            voice_macros.len()
        ));
    }

    let session_memory_path = loaded
        .config
        .app
        .session_memory_path
        .clone()
        .unwrap_or_else(|| default_session_memory_path(&working_dir));
    let session_memory_enabled = loaded.config.app.session_memory;
    let dev_event_logger = if loaded.config.dev_mode && loaded.config.dev_log {
        let dev_root = resolve_dev_root_path(&loaded.config, &working_dir);
        let logger = DevEventJsonlWriter::open_session(&dev_root)?;
        log_debug(&format!(
            "dev mode event logging enabled at {}",
            logger.path().display()
        ));
        Some(logger)
    } else {
        None
    };

    let prompt_log_path = if loaded.config.app.no_logs {
        None
    } else {
        resolve_prompt_log(&loaded.config)
    };
    let prompt_logger = PromptLogger::new(prompt_log_path);
    let prompt_regex =
        resolve_prompt_regex(&loaded.config, loaded.backend.prompt_pattern.as_deref())?;
    let prompt_tracker = PromptTracker::new(
        prompt_regex.regex,
        prompt_regex.allow_auto_learn,
        prompt_logger,
    );

    let banner_config = BannerConfig {
        auto_voice: loaded.config.auto_voice,
        theme: loaded.theme,
        pipeline: Pipeline::Rust,
        sensitivity_db: loaded.config.app.voice_vad_threshold_db,
        backend: loaded.backend.label.clone(),
    };
    if !should_skip_banner(env::var("VOICETERM_NO_STARTUP_BANNER").is_ok()) {
        show_startup_splash(&banner_config, loaded.theme)?;
    }

    let terminal_guard = TerminalRestoreGuard::new();
    terminal_guard.enable_raw_mode()?;

    let initial_hud_style = if loaded.config.minimal_hud {
        HudStyle::Minimal
    } else {
        loaded.config.hud_style
    };
    let (terminal_rows, terminal_cols, initial_pty_rows, initial_pty_cols) =
        startup_pty_geometry(initial_hud_style);

    let mut session = PtyOverlaySession::new(
        &loaded.backend.command,
        &working_dir,
        &loaded.backend.args,
        &loaded.config.app.term_value,
        initial_pty_rows,
        initial_pty_cols,
    )?;

    let (writer_tx, writer_rx) = bounded(WRITER_CHANNEL_CAPACITY);
    let writer_handle = spawn_writer_thread(writer_rx);
    send_message_blocking(
        &writer_tx,
        WriterMessage::SetTheme(loaded.theme),
        "runtime build: initial theme sync",
    );

    let button_registry = ButtonRegistry::new();
    if terminal_rows > 0 && terminal_cols > 0 {
        apply_pty_winsize(
            &mut session,
            terminal_rows,
            terminal_cols,
            OverlayMode::None,
            initial_hud_style,
            false,
        );
        send_message_blocking(
            &writer_tx,
            WriterMessage::Resize {
                rows: terminal_rows,
                cols: terminal_cols,
            },
            "runtime build: initial resize sync",
        );
    }

    let (input_tx, input_rx) = bounded(INPUT_CHANNEL_CAPACITY);
    let input_handle = spawn_input_thread(input_tx);

    Ok(RuntimeBuildInputs {
        loaded,
        working_dir,
        voice_macros,
        session_memory_path,
        session_memory_enabled,
        dev_event_logger,
        prompt_tracker,
        terminal_guard,
        writer_handle,
        input_handle,
        session,
        writer_tx,
        input_rx,
        button_registry,
        terminal_rows,
        terminal_cols,
        initial_hud_style,
    })
}

fn build_state_phase(inputs: RuntimeBuildInputs) -> RuntimeExecutionPhase {
    let RuntimeBuildInputs {
        loaded,
        working_dir,
        voice_macros,
        session_memory_path,
        session_memory_enabled,
        dev_event_logger,
        prompt_tracker,
        terminal_guard,
        writer_handle,
        input_handle,
        session,
        writer_tx,
        input_rx,
        button_registry,
        terminal_rows,
        terminal_cols,
        initial_hud_style,
    } = inputs;
    let LoadedConfigPhase {
        config,
        user_config,
        backend,
        theme,
        sound_on_complete,
        sound_on_error,
    } = loaded;
    let backend_label = backend.label;

    let auto_idle_timeout = Duration::from_millis(config.auto_voice_idle_ms.max(100));
    let transcript_idle_timeout = Duration::from_millis(config.transcript_idle_ms.max(50));
    let hud_registry = HudRegistry::with_defaults();
    let meter_update_ms = resolved_meter_update_ms(&hud_registry);
    let voice_manager = VoiceManager::new(config.app.clone());
    let wake_word_runtime = WakeWordRuntime::new(config.app.clone());
    let wake_word_rx = wake_word_runtime.receiver();
    let live_meter = voice_manager.meter();
    let auto_voice_enabled = config.auto_voice;
    let persisted_memory_mode = persistent_config::resolved_memory_mode(&user_config);

    let mut status_state = StatusLineState::new();
    status_state.sensitivity_db = config.app.voice_vad_threshold_db;
    status_state.auto_voice_enabled = auto_voice_enabled;
    status_state.wake_word_state = WakeWordHudState::Off;
    status_state.send_mode = config.voice_send_mode;
    status_state.image_mode_enabled = config.image_mode;
    status_state.dev_mode_enabled = config.dev_mode;
    status_state.latency_display = config.latency_display;
    status_state.macros_enabled = false;
    persistent_config::apply_user_config_to_status_state(&user_config, &mut status_state);
    status_state.hud_right_panel = config.hud_right_panel;
    status_state.hud_border_style = config.hud_border_style;
    status_state.hud_right_panel_recording_only = config.hud_right_panel_recording_only;
    status_state.hud_style = initial_hud_style;
    status_state.voice_mode = if auto_voice_enabled {
        VoiceMode::Auto
    } else {
        VoiceMode::Manual
    };
    status_state.pipeline = Pipeline::Rust;
    status_state.mouse_enabled = true;
    send_message_blocking(
        &writer_tx,
        WriterMessage::EnableMouse,
        "runtime build: enable mouse",
    );

    let dev_mode_stats = config.dev_mode.then(DevModeStats::default);
    let session_memory_logger = if session_memory_enabled {
        match SessionMemoryLogger::new(&session_memory_path, &backend_label, &working_dir) {
            Ok(logger) => {
                log_debug(&format!(
                    "session memory enabled at {}",
                    logger.path().display()
                ));
                Some(logger)
            }
            Err(err) => {
                log_debug(&format!(
                    "failed to initialize session memory log {}: {err}",
                    session_memory_path.display()
                ));
                None
            }
        }
    } else {
        None
    };

    let mut memory_ingestor = {
        let project_root = std::path::Path::new(&working_dir);
        let jsonl_path = crate::memory::governance::events_jsonl_path(project_root);
        let session_id = crate::memory::types::generate_session_id();
        let project_id = working_dir.clone();
        match crate::memory::MemoryIngestor::new(
            session_id,
            project_id,
            Some(&jsonl_path),
            persisted_memory_mode,
        ) {
            Ok(ingestor) => {
                log_debug(&format!("memory ingestor ready: {}", jsonl_path.display()));
                Some(ingestor)
            }
            Err(err) => {
                log_debug(&format!("memory ingestor disabled: {err}"));
                None
            }
        }
    };
    if let Some(ref mut ingestor) = memory_ingestor {
        let jsonl_path =
            crate::memory::governance::events_jsonl_path(std::path::Path::new(&working_dir));
        let recovered = ingestor.recover_from_jsonl(&jsonl_path);
        if recovered > 0 {
            log_debug(&format!(
                "memory: recovered {recovered} events from prior sessions"
            ));
        }
    }

    let dev_command_broker = config
        .dev_mode
        .then(|| DevCommandBroker::spawn(PathBuf::from(&working_dir)));
    let mut state = EventLoopState {
        config,
        working_dir,
        status_state,
        auto_voice_enabled,
        auto_voice_paused_by_user: false,
        theme,
        ui: UiRuntimeState {
            overlay_mode: OverlayMode::None,
            terminal_rows,
            terminal_cols,
            suppress_startup_escape_input: true,
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
        dev_mode_stats,
        dev_event_logger,
        dev_panel_commands: DevPanelState::default(),
        prompt: PromptRuntimeState {
            tracker: prompt_tracker,
            occlusion_detector: build_prompt_occlusion_detector(&backend_label),
            non_rolling_approval_window: VecDeque::with_capacity(1024),
            non_rolling_approval_window_last_update: None,
            non_rolling_release_armed: false,
            non_rolling_sticky_hold_until: None,
        },
        last_recording_duration: 0.0_f32,
        meter_floor_started_at: None,
        processing_spinner_index: 0,
        pty_buffer: PtyBufferState {
            pending_output: None,
            pending_input: VecDeque::new(),
            pending_input_offset: 0,
            pending_input_bytes: 0,
        },
        force_send_on_next_transcript: false,
        transcript_history: transcript_history::TranscriptHistory::new(),
        transcript_history_state: transcript_history::TranscriptHistoryState::new(),
        session_memory_logger,
        last_toast_status: None,
        toast_center: crate::toast::ToastCenter::new(),
        memory_ingestor,
        memory_browser_state: crate::memory_browser::MemoryBrowserState::new(),
        theme_file_watcher: std::env::var("VOICETERM_THEME_FILE").ok().and_then(|p| {
            let path = std::path::PathBuf::from(p.trim());
            if path.exists() {
                Some(crate::theme::file_watcher::ThemeFileWatcher::new(path))
            } else {
                None
            }
        }),
    };
    let mut timers = EventLoopTimers {
        theme_picker_digit_deadline: None,
        status_clear_deadline: None,
        preview_clear_deadline: None,
        prompt_suppression_release_not_before: None,
        last_auto_trigger_at: None,
        last_user_input_at: None,
        last_enter_at: None,
        recording_started_at: None,
        last_recording_update: Instant::now(),
        last_processing_tick: Instant::now(),
        last_heartbeat_tick: Instant::now(),
        last_meter_update: Instant::now(),
        last_wake_hud_tick: Instant::now(),
        last_toast_tick: Instant::now(),
        last_theme_file_poll: Instant::now(),
        last_terminal_geometry_poll: Instant::now(),
        last_review_poll: Instant::now(),
        pending_terminal_geometry_sample: None,
    };
    let mut deps = EventLoopDeps {
        session,
        voice_manager,
        wake_word_runtime,
        wake_word_rx,
        writer_tx,
        input_rx,
        button_registry,
        backend_label,
        sound_on_complete,
        sound_on_error,
        live_meter,
        meter_update_ms,
        auto_idle_timeout,
        transcript_idle_timeout,
        voice_macros,
        dev_command_broker,
    };

    let claude_jetbrains_startup_guard =
        runtime_compat::should_enable_claude_startup_guard(&deps.backend_label);
    if claude_jetbrains_startup_guard {
        state.prompt.occlusion_detector.activate_startup_guard();
        state.status_state.prompt_suppressed = true;
        apply_pty_winsize(
            &mut deps.session,
            state.ui.terminal_rows,
            state.ui.terminal_cols,
            state.ui.overlay_mode,
            state.status_state.hud_style,
            true,
        );
    }

    deps.wake_word_runtime.sync(
        state.config.wake_word,
        state.config.wake_word_sensitivity,
        state.config.wake_word_cooldown_ms,
        state.status_state.sensitivity_db,
        false,
        false,
    );
    let wake_listener_active = deps.wake_word_runtime.is_listener_active();
    state.status_state.wake_word_state = if !state.config.wake_word {
        WakeWordHudState::Off
    } else if wake_listener_active {
        WakeWordHudState::Listening
    } else {
        WakeWordHudState::Unavailable
    };
    let wake_mode_owns_mic = state.config.wake_word && wake_listener_active;

    if state.auto_voice_enabled {
        let auto_status_msg = if wake_mode_owns_mic {
            "Auto-voice enabled (wake-word active; idle capture paused)"
        } else {
            "Auto-voice enabled"
        };
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            auto_status_msg,
            Some(Duration::from_secs(2)),
        );
        if !wake_mode_owns_mic && deps.voice_manager.is_idle() {
            if let Err(err) = start_voice_capture(
                &mut deps.voice_manager,
                VoiceCaptureTrigger::Auto,
                &deps.writer_tx,
                &mut timers.status_clear_deadline,
                &mut state.current_status,
                &mut state.status_state,
            ) {
                log_debug(&format!("auto voice capture failed: {err:#}"));
            } else {
                let now = Instant::now();
                timers.last_auto_trigger_at = Some(now);
                timers.recording_started_at = Some(now);
                reset_capture_visuals(
                    &mut state.status_state,
                    &mut timers.preview_clear_deadline,
                    &mut timers.last_meter_update,
                );
            }
        }
    }

    if onboarding::should_show_hint() {
        set_status(
            &deps.writer_tx,
            &mut timers.status_clear_deadline,
            &mut state.current_status,
            &mut state.status_state,
            "Getting started: Ctrl+R record · ? help · Ctrl+O settings",
            None,
        );
    }

    send_enhanced_status_with_buttons(
        &deps.writer_tx,
        &deps.button_registry,
        &state.status_state,
        state.ui.overlay_mode,
        state.ui.terminal_cols,
        state.theme,
    );

    RuntimeExecutionPhase {
        state,
        timers,
        deps,
        terminal_guard,
        writer_handle,
        input_handle,
    }
}

fn run_runtime_phase(runtime: &mut RuntimeExecutionPhase) {
    run_event_loop(&mut runtime.state, &mut runtime.timers, &mut runtime.deps);
    runtime
        .state
        .transcript_history
        .flush_pending_stream_lines();
    if let Some(logger) = runtime.state.session_memory_logger.as_mut() {
        logger.flush_pending();
    }
    if let Some(logger) = runtime.state.dev_event_logger.as_mut() {
        let _ = logger.flush();
    }
}

fn shutdown_runtime_phase(runtime: RuntimeExecutionPhase) {
    send_message_blocking(
        &runtime.deps.writer_tx,
        WriterMessage::ClearStatus,
        "runtime shutdown: clear status",
    );
    send_message_blocking(
        &runtime.deps.writer_tx,
        WriterMessage::Shutdown,
        "runtime shutdown: writer shutdown",
    );
    runtime.terminal_guard.restore();
    drop(runtime.deps);
    join_thread_with_timeout(
        "writer",
        runtime.writer_handle,
        Duration::from_millis(WRITER_SHUTDOWN_JOIN_TIMEOUT_MS),
    );
    join_thread_with_timeout(
        "input",
        runtime.input_handle,
        Duration::from_millis(INPUT_SHUTDOWN_JOIN_TIMEOUT_MS),
    );
    let stats_output = format_session_stats(&runtime.state.session_stats, runtime.state.theme);
    if should_print_stats(&stats_output) {
        print!("{stats_output}");
        let _ = io::stdout().flush();
    }
    log_debug("=== VoiceTerm Overlay Exiting ===");
}

#[cfg(test)]
mod main_tests;
