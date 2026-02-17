//! IPC session lifecycle orchestration for long-lived backend command execution.

use crate::auth;
use crate::codex::{sanitize_pty_output, CodexCliBackend, CodexEvent, CodexEventKind, CodexJob};
use crate::config::AppConfig;
use crate::process_signal::signal_process_group_or_pid;
use crate::pty_session::PtyCliSession;
use crate::voice::VoiceJob;
use crate::{audio, log_debug, log_debug_content, stt};
use anyhow::Result;
#[cfg(any(test, feature = "mutants"))]
use std::collections::HashMap;
use std::env;
use std::io::{self, BufRead, Write};
#[cfg(any(test, feature = "mutants"))]
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::mpsc::{self, Receiver, RecvTimeoutError, Sender};
#[cfg(any(test, feature = "mutants"))]
use std::sync::OnceLock;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use super::protocol::{IpcCommand, IpcEvent, Provider};
mod event_processing;
mod loop_runtime;

// ============================================================================
// PTY toggle for tests/mutants so IPC paths can run without PTY dependencies.
// ============================================================================
#[cfg(any(test, feature = "mutants"))]
const USE_PTY: bool = false;
#[cfg(not(any(test, feature = "mutants")))]
const USE_PTY: bool = true;
const IPC_LOOP_WAIT_MS: u64 = 5;
#[cfg(any(test, feature = "mutants"))]
const AUTH_TIMEOUT: Duration = Duration::from_millis(50);
#[cfg(not(any(test, feature = "mutants")))]
const AUTH_TIMEOUT: Duration = Duration::from_secs(120);

// ============================================================================
// IPC state owned by the event loop.
// ============================================================================

pub(super) struct IpcState {
    pub(super) config: AppConfig,
    pub(super) active_provider: Provider,
    pub(super) codex_cli_backend: Arc<CodexCliBackend>,
    pub(super) claude_cmd: String,
    pub(super) recorder: Option<Arc<Mutex<audio::Recorder>>>,
    pub(super) transcriber: Option<Arc<Mutex<stt::Transcriber>>>,
    pub(super) current_job: Option<ActiveJob>,
    pub(super) current_voice_job: Option<VoiceJob>,
    pub(super) current_auth_job: Option<AuthJob>,
    pub(super) session_id: String,
    pub(super) cancelled: bool,
    pub(super) exit_requested: bool,
}

pub(super) enum ActiveJob {
    Codex(CodexJob),
    Claude(ClaudeJob),
}

pub(super) enum ClaudeJobOutput {
    Piped {
        child: std::process::Child,
        stdout_rx: Receiver<String>,
    },
    Pty {
        session: PtyCliSession,
    },
}

pub(super) struct ClaudeJob {
    pub(super) output: ClaudeJobOutput,
    #[allow(dead_code)]
    pub(super) started_at: Instant,
    pub(super) pending_exit: Option<std::process::ExitStatus>,
}

pub(super) type AuthResult = auth::AuthResult;

pub(super) struct AuthJob {
    pub(super) provider: Provider,
    pub(super) receiver: Receiver<AuthResult>,
    #[allow(dead_code)]
    pub(super) started_at: Instant,
}

impl IpcState {
    pub(super) fn new(mut config: AppConfig) -> Self {
        // Keep test/mutant runs deterministic by disabling PTY when toggled off.
        if !USE_PTY {
            config.persistent_codex = false;
            log_debug("PTY disabled via USE_PTY toggle");
        }

        // Session id is emitted in capabilities so clients can correlate events.
        let session_id = format!(
            "{:x}",
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_millis()
        );

        // Use already validated command values from config parsing.
        let claude_cmd = config.claude_cmd.clone();

        // Backend is shared so concurrent jobs can be cancelled from multiple paths.
        let codex_cli_backend = Arc::new(CodexCliBackend::new(config.clone()));

        // Allow env override so wrappers can pin provider without extra flags.
        let default_provider = env::var("VOICETERM_PROVIDER")
            .ok()
            .and_then(|s| Provider::from_str(&s))
            .unwrap_or(Provider::Codex);

        // Recorder/transcriber are optional so IPC still works without voice dependencies.
        let recorder = match audio::Recorder::new(config.input_device.as_deref()) {
            Ok(r) => {
                log_debug("Audio recorder initialized");
                Some(Arc::new(Mutex::new(r)))
            }
            Err(e) => {
                log_debug(&format!("Audio recorder not available: {e}"));
                None
            }
        };

        // Load STT lazily from config path; failures remain recoverable.
        let transcriber = if let Some(model_path) = &config.whisper_model_path {
            match stt::Transcriber::new(model_path) {
                Ok(t) => {
                    log_debug("Whisper transcriber initialized");
                    Some(Arc::new(Mutex::new(t)))
                }
                Err(e) => {
                    log_debug(&format!("Whisper not available: {e}"));
                    None
                }
            }
        } else {
            log_debug("No whisper model path configured");
            None
        };

        Self {
            config,
            active_provider: default_provider,
            codex_cli_backend,
            claude_cmd,
            recorder,
            transcriber,
            current_job: None,
            current_voice_job: None,
            current_auth_job: None,
            session_id,
            cancelled: false,
            exit_requested: false,
        }
    }

    pub(super) fn emit_capabilities(&self) {
        let providers = vec!["codex".to_string(), "claude".to_string()];

        // Device name is included in capabilities for client-side diagnostics.
        let input_device = self.recorder.as_ref().map(|r| {
            r.lock()
                .map(|recorder| recorder.device_name())
                .unwrap_or_else(|_| "Unknown Device".to_string())
        });

        send_event(&IpcEvent::Capabilities {
            session_id: self.session_id.clone(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            mic_available: self.recorder.is_some(),
            input_device,
            whisper_model_loaded: self.transcriber.is_some(),
            whisper_model_path: self.config.whisper_model_path.clone(),
            python_fallback_allowed: !self.config.no_python_fallback,
            providers_available: providers,
            active_provider: self.active_provider.as_str().to_string(),
            working_dir: env::current_dir()
                .map(|p| p.display().to_string())
                .unwrap_or_else(|_| ".".to_string()),
            codex_cmd: self.config.codex_cmd.clone(),
            claude_cmd: self.claude_cmd.clone(),
        });
    }
}

// ============================================================================
// Event sending
// ============================================================================

pub(super) fn send_event(event: &IpcEvent) {
    #[cfg(any(test, feature = "mutants"))]
    if capture_test_event(event) {
        return;
    }
    if let Ok(json) = serde_json::to_string(event) {
        let mut stdout = io::stdout().lock();
        let _ = writeln!(stdout, "{json}");
        let _ = stdout.flush();
    }
}

#[cfg(any(test, feature = "mutants"))]
#[derive(Default)]
struct EventSink {
    per_thread: HashMap<std::thread::ThreadId, Vec<IpcEvent>>,
}

#[cfg(any(test, feature = "mutants"))]
static EVENT_SINK: OnceLock<Mutex<EventSink>> = OnceLock::new();
#[cfg(any(test, feature = "mutants"))]
pub(super) static IPC_LOOP_COUNT: AtomicU64 = AtomicU64::new(0);

#[cfg(any(test, feature = "mutants"))]
fn capture_test_event(event: &IpcEvent) -> bool {
    if let Some(sink) = EVENT_SINK.get() {
        if let Ok(mut events) = sink.lock() {
            events
                .per_thread
                .entry(std::thread::current().id())
                .or_default()
                .push(event.clone());
            return true;
        }
    }
    false
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn init_event_sink() {
    let _ = EVENT_SINK.get_or_init(|| Mutex::new(EventSink::default()));
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn ipc_loop_count_reset() {
    IPC_LOOP_COUNT.store(0, Ordering::SeqCst);
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn ipc_loop_count() -> u64 {
    IPC_LOOP_COUNT.load(Ordering::SeqCst)
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn event_snapshot() -> usize {
    init_event_sink();
    let current = std::thread::current().id();
    EVENT_SINK
        .get()
        .and_then(|sink| {
            sink.lock()
                .ok()
                .and_then(|events| events.per_thread.get(&current).map(Vec::len))
        })
        .unwrap_or(0)
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn events_since(start: usize) -> Vec<IpcEvent> {
    let current = std::thread::current().id();
    EVENT_SINK
        .get()
        .and_then(|sink| {
            sink.lock().ok().and_then(|events| {
                events
                    .per_thread
                    .get(&current)
                    .map(|thread_events| thread_events.iter().skip(start).cloned().collect())
            })
        })
        .unwrap_or_default()
}

impl ClaudeJob {
    pub(super) fn cancel(&mut self) {
        match &mut self.output {
            ClaudeJobOutput::Piped { child, .. } => {
                terminate_piped_child(child);
            }
            ClaudeJobOutput::Pty { session } => {
                let _ = session.send("\u{3}");
            }
        }
    }
}

// ============================================================================
// Stdin Reader Thread
// ============================================================================

#[cfg_attr(any(test, feature = "mutants"), allow(dead_code))]
fn spawn_stdin_reader(tx: Sender<IpcCommand>) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        let stdin = io::stdin();
        let stdin_lock = stdin.lock();

        for line in stdin_lock.lines() {
            let line = match line {
                Ok(l) => l,
                Err(_) => break,
            };

            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }

            match serde_json::from_str::<IpcCommand>(trimmed) {
                Ok(cmd) => {
                    if tx.send(cmd).is_err() {
                        break; // Main thread has exited
                    }
                }
                Err(e) => {
                    send_event(&IpcEvent::Error {
                        message: format!("Invalid command: {e}"),
                        recoverable: true,
                    });
                }
            }
        }

        log_debug("Stdin reader thread exiting");
    })
}

// ============================================================================
// Claude Backend
// ============================================================================

fn terminate_piped_child(child: &mut std::process::Child) {
    #[cfg(unix)]
    {
        let pid = child.id() as i32;

        let _ = signal_process_group_or_pid(pid, libc::SIGTERM, true);
        let deadline = Instant::now() + Duration::from_millis(150);
        while Instant::now() < deadline {
            match child.try_wait() {
                Ok(Some(_)) => return,
                Ok(None) => thread::sleep(Duration::from_millis(10)),
                Err(_) => break,
            }
        }
        let _ = signal_process_group_or_pid(pid, libc::SIGKILL, true);
    }

    #[cfg(not(unix))]
    {
        let _ = child.kill();
    }

    let _ = child.wait();
}

fn start_claude_job_with_mode(
    claude_cmd: &str,
    prompt: &str,
    skip_permissions: bool,
    term_value: &str,
    use_pty: bool,
) -> Result<ClaudeJob, String> {
    use std::process::{Command, Stdio};

    log_debug_content(&format!(
        "Starting Claude job with prompt: {}...",
        &prompt[..prompt.len().min(30)]
    ));

    // Use --print with --dangerously-skip-permissions for non-interactive operation.
    // Prefer PTY when enabled so thinking/tool call output streams in real time.
    let mut args = vec!["--print".to_string()];
    if skip_permissions {
        args.push("--dangerously-skip-permissions".to_string());
    }
    args.push(prompt.to_string());

    if use_pty {
        let working_dir = env::current_dir()
            .map(|path| path.display().to_string())
            .unwrap_or_else(|_| ".".to_string());
        match PtyCliSession::new(claude_cmd, &working_dir, &args, term_value) {
            Ok(session) => {
                log_debug("Claude job started (PTY)");
                return Ok(ClaudeJob {
                    output: ClaudeJobOutput::Pty { session },
                    started_at: Instant::now(),
                    pending_exit: None,
                });
            }
            Err(err) => {
                log_debug(&format!(
                    "Claude PTY failed, falling back to pipes: {err:#}"
                ));
            }
        }
    }

    let mut command = Command::new(claude_cmd);
    command.args(&args);
    let mut child = command
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to start claude: {e}"))?;

    let stdout = child.stdout.take().ok_or("Failed to capture stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to capture stderr")?;

    let (tx, rx) = mpsc::channel();
    let tx_err = tx.clone();

    // Read stdout
    thread::spawn(move || {
        let reader = io::BufReader::new(stdout);
        for line in reader.lines().map_while(Result::ok) {
            if tx.send(line).is_err() {
                break;
            }
        }
    });

    // Read stderr
    thread::spawn(move || {
        let reader = io::BufReader::new(stderr);
        for line in reader.lines().map_while(Result::ok) {
            // Only show non-empty stderr lines
            if !line.trim().is_empty() && tx_err.send(format!("[info] {line}")).is_err() {
                break;
            }
        }
    });

    log_debug("Claude job started");
    Ok(ClaudeJob {
        output: ClaudeJobOutput::Piped {
            child,
            stdout_rx: rx,
        },
        started_at: Instant::now(),
        pending_exit: None,
    })
}

pub(super) fn start_claude_job(
    claude_cmd: &str,
    prompt: &str,
    skip_permissions: bool,
    term_value: &str,
) -> Result<ClaudeJob, String> {
    start_claude_job_with_mode(claude_cmd, prompt, skip_permissions, term_value, USE_PTY)
}

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn start_claude_job_with_pty(
    claude_cmd: &str,
    prompt: &str,
    skip_permissions: bool,
    term_value: &str,
) -> Result<ClaudeJob, String> {
    start_claude_job_with_mode(claude_cmd, prompt, skip_permissions, term_value, true)
}

// ============================================================================
// Auth Backend
// ============================================================================

#[cfg(any(test, feature = "mutants"))]
pub(super) type AuthFlowHook =
    Box<dyn Fn(Provider, &str, &str) -> AuthResult + Send + Sync + 'static>;

#[cfg(any(test, feature = "mutants"))]
static AUTH_FLOW_HOOK: OnceLock<Mutex<Option<AuthFlowHook>>> = OnceLock::new();

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn set_auth_flow_hook(hook: Option<AuthFlowHook>) {
    let storage = AUTH_FLOW_HOOK.get_or_init(|| Mutex::new(None));
    *storage.lock().unwrap_or_else(|e| e.into_inner()) = hook;
}

pub(super) fn run_auth_flow(provider: Provider, codex_cmd: &str, claude_cmd: &str) -> AuthResult {
    #[cfg(any(test, feature = "mutants"))]
    if let Some(storage) = AUTH_FLOW_HOOK.get() {
        if let Ok(guard) = storage.lock() {
            if let Some(hook) = guard.as_ref() {
                return hook(provider, codex_cmd, claude_cmd);
            }
        }
    }
    let command = match provider {
        Provider::Codex => codex_cmd,
        Provider::Claude => claude_cmd,
    };
    auth::run_login_command(command)
        .map_err(|err| format!("{} auth failed: {}", provider.as_str(), err))
}

// ============================================================================
// Main Event Loop
// ============================================================================

/// Run newline-delimited JSON IPC mode until stdin closes or loop exits.
pub fn run_ipc_mode(config: AppConfig) -> Result<()> {
    log_debug("Starting JSON IPC mode (non-blocking)");

    let mut state = IpcState::new(config);

    // Emit capabilities on startup
    state.emit_capabilities();

    // Start stdin reader thread
    let (cmd_tx, cmd_rx) = mpsc::channel();
    #[cfg(any(test, feature = "mutants"))]
    {
        drop(cmd_tx);
        run_ipc_loop(&mut state, &cmd_rx, Some(10))
    }
    #[cfg(not(any(test, feature = "mutants")))]
    {
        let _stdin_handle = spawn_stdin_reader(cmd_tx);
        run_ipc_loop(&mut state, &cmd_rx, None)
    }
}

#[cfg(any(test, feature = "mutants"))]
pub(super) fn ipc_guard_tripped(elapsed: Duration) -> bool {
    elapsed > Duration::from_secs(2)
}

pub(super) fn run_ipc_loop(
    state: &mut IpcState,
    cmd_rx: &Receiver<IpcCommand>,
    max_loops: Option<u64>,
) -> Result<()> {
    #[cfg(any(test, feature = "mutants"))]
    let guard_start = Instant::now();
    let mut loop_count: u64 = 0;
    loop {
        #[cfg(any(test, feature = "mutants"))]
        if ipc_guard_tripped(guard_start.elapsed()) {
            panic!("IPC loop guard exceeded");
        }
        loop_count += 1;
        #[cfg(any(test, feature = "mutants"))]
        IPC_LOOP_COUNT.store(loop_count, Ordering::SeqCst);
        if loop_count.is_multiple_of(1000) {
            log_debug(&format!(
                "IPC loop iteration {}, job active: {}",
                loop_count,
                state.current_job.is_some()
            ));
        }

        if let Some(limit) = max_loops {
            if loop_count >= limit {
                log_debug("IPC loop reached test limit, exiting");
                break;
            }
        }

        // Wait briefly for commands so idle IPC loops don't spin.
        match cmd_rx.recv_timeout(Duration::from_millis(IPC_LOOP_WAIT_MS)) {
            Ok(cmd) => {
                log_debug_content(&format!("IPC command received: {cmd:?}"));
                loop_runtime::handle_command(state, cmd);
            }
            Err(RecvTimeoutError::Timeout) => {}
            Err(RecvTimeoutError::Disconnected) => {
                log_debug("Command channel disconnected, exiting");
                break;
            }
        }

        loop_runtime::drain_active_jobs(state);

        if loop_runtime::should_exit(state) {
            log_debug("IPC graceful exit requested; no active work remains");
            break;
        }
    }

    log_debug("IPC mode exiting");
    Ok(())
}

pub(super) fn process_codex_events(job: &mut CodexJob, cancelled: bool) -> bool {
    event_processing::process_codex_events(job, cancelled)
}

pub(super) fn process_claude_events(job: &mut ClaudeJob, cancelled: bool) -> bool {
    event_processing::process_claude_events(job, cancelled)
}

pub(super) fn process_voice_events(job: &VoiceJob, cancelled: bool) -> bool {
    event_processing::process_voice_events(job, cancelled)
}

pub(super) fn process_auth_events(state: &mut IpcState) -> bool {
    event_processing::process_auth_events(state)
}
